"""Management Consulting Manager Agent: intent detection -> routing -> (parallel) specialist
agents -> cross-domain synthesis into one consulting recommendation.

Run: .venv/bin/python -m app.agents.manager "your question"
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from app import config, llm
from app.agents.base import DomainAgent, load_prompt

ROUTES = config.DOMAINS + ["out_of_scope"]

ROUTE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["routes", "cross_domain", "sub_questions", "reason", "confidence"],
    "properties": {
        "routes": {"type": "array", "items": {"type": "string", "enum": ROUTES}},
        "cross_domain": {"type": "boolean"},
        "sub_questions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["route", "question"],
            "properties": {"route": {"type": "string", "enum": ROUTES}, "question": {"type": "string"}}}},
        "reason": {"type": "string"},
        "confidence": {"type": "number"},
    },
}

SYNTH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["executive_summary", "integrated_recommendations", "cross_domain_links",
                 "conflicts_or_gaps", "next_steps", "kpis", "confidence"],
    "properties": {
        "executive_summary": {"type": "string"},
        "integrated_recommendations": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["action", "priority", "why", "sources"],
            "properties": {
                "action": {"type": "string"},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "why": {"type": "string"},
                "sources": {"type": "array", "items": {"type": "string"}, "description": "Ids like SEC-S3."},
            }}},
        "cross_domain_links": {"type": "array", "items": {"type": "string"},
                               "description": "How one specialist's findings change another's recommendation."},
        "conflicts_or_gaps": {"type": "array", "items": {"type": "string"}},
        "next_steps": {"type": "array", "items": {"type": "string"}},
        "kpis": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["metric", "how_to_measure"],
            "properties": {"metric": {"type": "string"}, "how_to_measure": {"type": "string"}}}},
        "confidence": {
            "type": "object", "additionalProperties": False, "required": ["level", "reason"],
            "properties": {"level": {"type": "string", "enum": ["high", "medium", "low"]}, "reason": {"type": "string"}}},
    },
}

PREFIX = {"technology": "TECH", "clinical": "CLIN", "sec": "SEC", "csr": "CSR"}


class ManagerAgent:
    def __init__(self):
        self.prompt = load_prompt("manager")
        self.agents = {d: DomainAgent(d) for d in config.DOMAINS}

    def route(self, query: str) -> dict:
        """Small, fast model classifies intent and writes one sub-question per specialist."""
        t0 = time.time()
        decision = llm.chat_json(
            [{"role": "system", "content": self.prompt + "\n\nReturn only the routing decision."},
             {"role": "user", "content": query}],
            config.ROUTER_MODEL, ROUTE_SCHEMA, "routing_decision", effort="low",
        )
        routes = [r for r in dict.fromkeys(decision["routes"]) if r in config.DOMAINS]
        if not routes:
            decision["routes"] = ["out_of_scope"]
        else:
            decision["routes"] = routes
            asked = {s["route"]: s["question"] for s in decision["sub_questions"]}
            decision["sub_questions"] = [{"route": r, "question": asked.get(r, query)} for r in routes]
        decision["cross_domain"] = len(routes) > 1
        decision["model"] = config.ROUTER_MODEL
        decision["seconds"] = round(time.time() - t0, 1)
        return decision

    def synthesize(self, query: str, results: dict) -> dict:
        """Full model merges the specialists' cited findings into one consulting recommendation."""
        briefs = []
        for domain, res in results.items():
            p = PREFIX[domain]
            src = {s["id"]: f"{p}-{s['id']}" for s in res["sources"]}
            ans = json.loads(json.dumps(res["answer"]))
            for item in ans.get("findings", []) + ans.get("recommendations", []):
                item["sources"] = [src.get(s, s) for s in item.get("sources", [])]
            briefs.append(f"### {res['agent']} (source ids prefixed {p}-)\nSub-question: {res['question']}\n"
                          f"{json.dumps(ans, indent=1)}")
        messages = [
            {"role": "system", "content": self.prompt + "\n\nWrite the consolidated consulting recommendation. Be concise: an executive summary of at most "
                                       "5 sentences, at most 5 integrated recommendations, 4 cross-domain links, 6 next steps "
                                       "and 5 KPIs."},
            {"role": "user", "content": f"Client request: {query}\n\nSpecialist reports:\n\n" + "\n\n".join(briefs)},
        ]
        return llm.chat_json(messages, config.AGENT_MODEL, SYNTH_SCHEMA, "consulting_recommendation", config.AGENT_EFFORT)

    def run(self, query: str, on_event: Callable | None = None) -> dict:
        t0 = time.time()
        emit = on_event or (lambda *a: None)
        decision = self.route(query)
        emit("route", decision)
        out = {"query": query, "route": decision, "agents": {}, "synthesis": None}
        if decision["routes"] == ["out_of_scope"]:
            out["seconds"] = round(time.time() - t0, 1)
            return out

        def work(sub):
            emit("agent_start", sub["route"])
            res = self.agents[sub["route"]].run(sub["question"], on_event)
            emit("agent_done", sub["route"])
            return sub["route"], res

        # Concurrent fan-out: specialists work in parallel, then the manager aggregates.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for domain, res in pool.map(work, decision["sub_questions"]):
                out["agents"][domain] = res
        if decision["cross_domain"]:
            emit("synthesis_start")
            out["synthesis"] = self.synthesize(query, out["agents"])
        out["seconds"] = round(time.time() - t0, 1)
        return out


if __name__ == "__main__":
    from app.agents.render import to_markdown

    question = " ".join(sys.argv[1:]) or "Which replacement components should we order to resolve a Cisco router failure?"
    result = ManagerAgent().run(question, on_event=lambda *a: print("  ..", *a[:2], file=sys.stderr))
    print(to_markdown(result))

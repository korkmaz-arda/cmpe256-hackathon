"""Management Consulting Manager Agent: intent detection -> routing -> (parallel) specialist
agents -> cross-domain synthesis into one consulting recommendation.

Run: .venv/bin/python -m app.agents.manager "your question"
"""
from __future__ import annotations

import json
import re
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
            # One sub-question per specialist: merge if the router split a route into several parts.
            asked: dict = {}
            for s in decision["sub_questions"]:
                asked.setdefault(s["route"], []).append(s["question"])
            merged = []
            for r in routes:
                parts = asked.get(r) or [query]
                question = parts[0] if len(parts) == 1 else "Answer all of the following:\n" + "\n".join(
                    f"{i}. {p}" for i, p in enumerate(parts, 1))
                merged.append({"route": r, "question": question})
            decision["sub_questions"] = merged
        decision["cross_domain"] = len(routes) > 1
        decision["model"] = config.ROUTER_MODEL
        decision["seconds"] = round(time.time() - t0, 1)
        return decision

    def synthesize(self, query: str, results: dict) -> dict:
        """Full model merges the specialists' cited findings into one consulting recommendation.
        Source ids are already namespaced per specialist (TECH-S1, SEC-S4, ...) by `namespace_sources`."""
        briefs = [f"### {res['agent']}\nSub-question: {res['question']}\n{json.dumps(res['answer'], indent=1)}"
                  for res in results.values()]
        messages = [
            {"role": "system", "content": self.prompt + "\n\nWrite the consolidated consulting recommendation. Be concise: "
                                       "an executive summary of at most 5 sentences, at most 5 integrated recommendations, "
                                       "4 cross-domain links, 6 next steps and 5 KPIs. Cite only the source ids that appear "
                                       "in the specialist reports."},
            {"role": "user", "content": f"Client request: {query}\n\nSpecialist reports:\n\n" + "\n\n".join(briefs)},
        ]
        return llm.chat_json(messages, config.AGENT_MODEL, SYNTH_SCHEMA, "consulting_recommendation", config.AGENT_EFFORT)

    def run(self, query: str, on_event: Callable | None = None) -> dict:
        t0 = time.time()
        emit = on_event or (lambda *a: None)
        decision = self.route(query)
        emit("route", decision)
        out = {"query": query, "route": decision, "agents": {}, "errors": {}, "synthesis": None}
        if decision["routes"] == ["out_of_scope"]:
            out["seconds"] = round(time.time() - t0, 1)
            return out

        def work(sub):
            emit("agent_start", sub["route"])
            res = self.agents[sub["route"]].run(sub["question"], on_event)
            emit("agent_done", sub["route"])
            return res

        # Concurrent fan-out: specialists work in parallel, then the manager aggregates.
        # A failing specialist is reported but doesn't discard the others' work.
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {sub["route"]: pool.submit(work, sub) for sub in decision["sub_questions"]}
            for domain, future in futures.items():
                try:
                    out["agents"][domain] = future.result()
                except Exception as exc:
                    out["errors"][domain] = f"{type(exc).__name__}: {exc}"
                    emit("agent_error", domain, str(exc))

        if decision["cross_domain"]:
            for domain, res in out["agents"].items():
                namespace_sources(res, PREFIX[domain])
            if len(out["agents"]) > 1:
                emit("synthesis_start")
                try:
                    out["synthesis"] = self.synthesize(query, out["agents"])
                except Exception as exc:
                    out["errors"]["synthesis"] = f"{type(exc).__name__}: {exc}"
        out["seconds"] = round(time.time() - t0, 1)
        return out


_INLINE = re.compile(r"\bS(\d+)\b")


def namespace_sources(res: dict, prefix: str) -> None:
    """Rename a specialist's source ids S1, S2, ... to PREFIX-S1, ... everywhere (source list,
    `sources` fields and inline [S3] mentions) so ids stay unique across specialists."""
    def fix_text(text: str) -> str:
        return re.sub(r"\[([^\]]*)\]", lambda m: "[" + _INLINE.sub(rf"{prefix}-S\1", m.group(1)) + "]", text)

    def walk(obj):
        if isinstance(obj, dict):
            return {k: ([f"{prefix}-{s}" if not str(s).startswith(prefix) else s for s in v] if k == "sources" and isinstance(v, list)
                        else walk(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        return fix_text(obj) if isinstance(obj, str) else obj

    res["answer"] = walk(res["answer"])
    for s in res["sources"]:
        s["id"] = f"{prefix}-{s['id']}"
    res["grounding"]["invalid_citations"] = [f"{prefix}-{s}" for s in res["grounding"].get("invalid_citations", [])]


if __name__ == "__main__":
    from app.agents.render import to_markdown

    question = " ".join(sys.argv[1:]) or "Which replacement components should we order to resolve a Cisco router failure?"
    result = ManagerAgent().run(question, on_event=lambda *a: print("  ..", *a[:2], file=sys.stderr))
    print(to_markdown(result))

"""A grounded domain agent: persona prompt + tools (RAG search, domain recommenders) + a
structured, cited answer with an explicit confirmed/hypothesis split and a confidence estimate."""
from __future__ import annotations

import json
import time
from typing import Callable

from app import config, llm
from app.rag.store import get_store

MAX_TOOL_ROUNDS = 6
SNIPPET_CHARS = 900

# Metadata filters each agent may apply to its own knowledge base.
FILTERS = {
    "technology": {"company": ["Cisco", "Google"]},
    "clinical": {"topic": ["Covid", "Diabetes", "Heart_attack", "KneeInjuries"]},
    "sec": {"company": ["Cisco", "Agilent", "Alphabet"], "year": ["FY2024", "FY2025", "FY2026"]},
    "csr": {"year": ["2023", "2024"]},
}

ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "findings", "recommendations", "next_steps", "kpis",
                 "missing_information", "risks_assumptions", "confidence"],
    "properties": {
        "summary": {"type": "string", "description": "2-4 sentence direct answer to the question."},
        "findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["claim", "status", "sources"],
            "properties": {
                "claim": {"type": "string"},
                "status": {"type": "string", "enum": ["confirmed", "hypothesis"]},
                "sources": {"type": "array", "items": {"type": "string"}, "description": "Source ids like S3."},
            }}},
        "recommendations": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["action", "priority", "why", "sources"],
            "properties": {
                "action": {"type": "string"},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "why": {"type": "string"},
                "sources": {"type": "array", "items": {"type": "string"}},
            }}},
        "next_steps": {"type": "array", "items": {"type": "string"}},
        "kpis": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["metric", "how_to_measure"],
            "properties": {"metric": {"type": "string"}, "how_to_measure": {"type": "string"}}}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "risks_assumptions": {"type": "array", "items": {"type": "string"}},
        "confidence": {
            "type": "object", "additionalProperties": False, "required": ["level", "reason"],
            "properties": {"level": {"type": "string", "enum": ["high", "medium", "low"]}, "reason": {"type": "string"}}},
    },
}

OUTPUT_RULES = """
## Output rules (all agents)
- Ground every finding in the tool results. Each result carries a source id such as S3; put the ids
  in the `sources` field and you may also cite them inline like [S3]. Use only ids you were given.
- `status` is "confirmed" only when a cited source states it; otherwise "hypothesis".
- `recommendations` say what the client should do; `why` explains why it is appropriate.
- `kpis` say how the client can measure the impact of acting on the recommendations.
- `missing_information` lists what you would need from the client to be more certain.
- Be concise and specific: at most 8 findings, 6 recommendations, 6 next steps, 5 KPIs and
  6 missing-information items. Prefer the most decision-relevant points.
- `confidence.level`: high = directly supported by several sources; medium = partly supported or
  needs client confirmation; low = little evidence.
"""


def load_prompt(name: str) -> str:
    return (config.PROMPTS / f"{name}.md").read_text()


def search_tool_spec(domain: str) -> dict:
    props: dict = {
        "query": {"type": "string", "description": "What to look for, in natural language."},
        "k": {"type": "integer", "description": "Number of passages (default 6, max 10)."},
    }
    for key, values in FILTERS[domain].items():
        props[key] = {"type": "string", "enum": values, "description": f"Optional filter on {key}."}
    return {"type": "function", "function": {
        "name": "search_knowledge",
        "description": f"Hybrid semantic + keyword search over the {config.DOMAIN_LABELS[domain]} knowledge base. "
                       "Returns passages with source ids, titles and page numbers.",
        "parameters": {"type": "object", "properties": props, "required": ["query"]},
    }}


class DomainAgent:
    def __init__(self, domain: str):
        self.domain = domain
        self.name = config.DOMAIN_LABELS[domain]
        self.prompt = load_prompt(domain)
        self.tools = [search_tool_spec(domain)]
        if domain in ("technology", "clinical"):
            from app.tools import product_recommender
            self.tools.append(product_recommender.TOOL_SPEC)
        if domain == "clinical":
            from app.tools import trials
            self.tools.extend(trials.TOOL_SPECS)

    # ------------------------------------------------------------------ tools
    def _register(self, sources: list[dict], **src) -> str:
        sid = f"S{len(sources) + 1}"
        sources.append({"id": sid, **src})
        return sid

    def _call_tool(self, name: str, args: dict, sources: list[dict]) -> str:
        if name == "search_knowledge":
            filters = {k: args[k] for k in FILTERS[self.domain] if args.get(k)}
            k = max(1, min(int(args.get("k") or 6), 10))
            hits = get_store(self.domain).search(args["query"], k=k, filters=filters)
            lines = []
            for h in hits:
                sid = self._register(sources, kind="document", title=h["title"], page=h.get("page"),
                                     url=h.get("url"), path=h.get("path"), source=h.get("source"),
                                     text=h["text"], cosine=h["cosine"])
                page = f", p.{h['page']}" if h.get("page") else ""
                lines.append(f"[{sid}] {h['title']}{page} ({h.get('source')}): {h['text'][:SNIPPET_CHARS]}")
            return "\n\n".join(lines) or "No passages matched. Try a broader query or remove filters."

        if name == "recommend_products":
            from app.tools import product_recommender
            results = product_recommender.recommend_products(**args)
            catalog = _catalog(args.get("catalog", "cisco"))
            for r in results:
                entry = catalog.get(r["id"], {})
                # Give the agent the facts it needs for compatibility / parts questions.
                for key in ("family", "deployment", "power_supply_redundancy", "field_replaceable_parts",
                            "max_throughput_text", "best_for", "source_pages", "regulatory", "measures_or_does"):
                    if key in entry:
                        r[key] = entry[key]
                r["source_id"] = self._register(sources, kind="product", title=f"Catalog: {r.get('name')}",
                                                url=r.get("source_url"), page=None, text=json.dumps(r)[:1500],
                                                source="Product catalog (from datasheets)")
            return json.dumps(results)

        if name in ("search_trials", "instrument_usage"):
            from app.tools import trials
            out = trials.call_tool(name, args)
            rows = out if isinstance(out, list) else out.get("trials", [])
            for row in rows[:15]:
                row["source_id"] = self._register(sources, kind="trial", title=f"{row.get('nct_id')}: {row.get('title')}",
                                                  url=row.get("url"), page=None, source="ClinicalTrials.gov record",
                                                  text=json.dumps(row)[:1500])
            if isinstance(out, dict) and "trials" in out:
                out = {**out, "trials": rows[:15]}
            return json.dumps(out, default=str)[:12000]

        return f"Unknown tool {name}"

    # ------------------------------------------------------------------ run
    def run(self, question: str, on_event: Callable | None = None) -> dict:
        t0 = time.time()
        emit = on_event or (lambda *a: None)
        sources: list[dict] = []
        tool_calls: list[dict] = []
        messages = [
            {"role": "system", "content": self.prompt + "\n" + OUTPUT_RULES},
            {"role": "user", "content": question},
        ]
        answer = None
        for _ in range(MAX_TOOL_ROUNDS):
            msg = llm.chat(messages, config.AGENT_MODEL, tools=self.tools, schema=ANSWER_SCHEMA,
                           schema_name="domain_answer", effort="none")  # tools require effort "none" on chat completions
            if not msg.tool_calls:
                answer = json.loads(msg.content)
                break
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls]})
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                emit("tool", self.domain, tc.function.name, args)
                try:
                    result = self._call_tool(tc.function.name, args, sources)
                except Exception as exc:  # report tool errors to the model instead of crashing
                    result = f"Tool error: {exc}"
                tool_calls.append({"tool": tc.function.name, "args": args})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        if answer is None:  # ran out of tool rounds: force a final answer
            messages.append({"role": "user", "content": "Answer now using the evidence gathered so far."})
            answer = llm.chat_json(messages, config.AGENT_MODEL, ANSWER_SCHEMA, "domain_answer", "none")

        return {
            "domain": self.domain,
            "agent": self.name,
            "question": question,
            "answer": answer,
            "sources": sources,
            "tool_calls": tool_calls,
            "grounding": grounding_report(answer, sources),
            "seconds": round(time.time() - t0, 1),
        }


def grounding_report(answer: dict, sources: list[dict]) -> dict:
    """Measurable explainability: how much of the answer is backed by retrieved evidence."""
    valid = {s["id"] for s in sources}
    findings = answer.get("findings", [])
    cited = [f for f in findings if any(s in valid for s in f.get("sources", []))]
    invalid = sorted({s for f in findings for s in f.get("sources", []) if s not in valid})
    confirmed = [f for f in findings if f.get("status") == "confirmed"]
    cosines = sorted((s["cosine"] for s in sources if s.get("cosine") is not None), reverse=True)[:3]
    retrieval = sum(cosines) / len(cosines) if cosines else None
    coverage = len(cited) / len(findings) if findings else 0.0
    # Grounding score: half citation coverage, half retrieval strength (cosine 0.3 -> 0, 0.7 -> 1).
    strength = min(1.0, max(0.0, (retrieval - 0.3) / 0.4)) if retrieval is not None else (1.0 if sources else 0.0)
    return {
        "findings": len(findings),
        "confirmed": len(confirmed),
        "hypotheses": len(findings) - len(confirmed),
        "citation_coverage": round(coverage, 2),
        "invalid_citations": invalid,
        "top3_retrieval_cosine": round(retrieval, 3) if retrieval is not None else None,
        "grounding_score": round(0.5 * coverage + 0.5 * strength, 2),
        "sources_retrieved": len(sources),
    }


_CATALOGS: dict = {}


def _catalog(name: str) -> dict:
    if name not in _CATALOGS:
        file = config.ROOT / "app" / "catalog" / ("cisco_routers.json" if name == "cisco" else "agilent_products.json")
        _CATALOGS[name] = {e["id"]: e for e in json.loads(file.read_text())}
    return _CATALOGS[name]

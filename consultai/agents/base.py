"""Specialist agent base: prompt rendering, tool plumbing, evidence registry, report validation.

A specialist is (1) a persona prompt in agents/<name>/prompt.md, (2) a set of retrieval / recommender
tools over its own sources, and (3) the shared `submit_report` tool whose input schema IS the
ReportBody contract. Tools create Evidence records (with ids such as TECH-3) in code; the agent can
only cite ids that its own tools returned, and `submit_report` rejects anything else.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from claude_agent_sdk import SdkMcpTool, tool
from pydantic import ValidationError

from consultai.config import INDEX_DIR, settings
from consultai.contracts import (EVIDENCE_PREFIX, Evidence, ReportBody, SpecialistReport, SpecialistTask,
                                 inline_schema)
from consultai.ingest.sources import KNOWN_GAPS, SOURCES_BY_ID, Source, sources_for
from consultai.llm.claude_runner import run_agent
from consultai.orchestrator.trace import TraceBus
from consultai.retrieval.store import Hit

AGENTS_DIR = Path(__file__).parent
COMMON_POLICY = AGENTS_DIR / "common_policy.md"


# ----------------------------------------------------------------------------- evidence
class EvidenceRegistry:
    """Run-wide store of every evidence record any tool produced. Ids are agent-prefixed counters."""

    def __init__(self):
        self.items: dict[str, Evidence] = {}
        self._counters: dict[str, int] = {}

    def add(self, agent: str, **fields) -> Evidence:
        prefix = EVIDENCE_PREFIX[agent]
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        ev = Evidence(evidence_id=f"{prefix}-{self._counters[prefix]}", agent=agent, **fields)
        self.items[ev.evidence_id] = ev
        return ev

    def add_hit(self, agent: str, tool_name: str, query: str | None, hit: Hit, snippet_chars: int) -> Evidence:
        c = hit.chunk
        src = SOURCES_BY_ID.get(c["source_id"])
        page, section = c.get("page"), c.get("section")
        locator = ", ".join(x for x in (section, f"p. {page}" if page else None) if x) or "web page"
        url = (src.citation_url if src else None) or c["meta"].get("url")
        if url and page and str(url).endswith(".pdf"):
            url = f"{url}#page={page}"
        return self.add(agent, tool=tool_name, query=query, source_id=c["source_id"],
                        title=src.title if src else c["meta"].get("doc_title", c["source_id"]),
                        locator=locator, page=page, section=section, citation_url=url,
                        local_path=str(src.local_path) if src else None,
                        snippet=c["text"][:snippet_chars], scores=hit.scores)

    def for_agent(self, agent: str) -> dict[str, Evidence]:
        prefix = EVIDENCE_PREFIX[agent] + "-"
        return {k: v for k, v in self.items.items() if k.startswith(prefix)}


def format_evidence(ev: Evidence, extra: str = "") -> str:
    score = ", ".join(f"{k} {v}" for k, v in ev.scores.items())
    head = f"[{ev.evidence_id}] {ev.title} | {ev.locator}" + (f" | scores: {score}" if score else "")
    return f"{head}{extra}\n{ev.snippet}"


# ----------------------------------------------------------------------------- tool context
@dataclass
class ToolContext:
    run_id: str
    task: SpecialistTask
    agent: str
    registry: EvidenceRegistry
    trace: TraceBus
    budget: int
    calls: int = 0
    report: ReportBody | None = None
    submit_attempts: int = 0
    retrieved_ids: list[str] = field(default_factory=list)


def make_tool(ctx: ToolContext, name: str, description: str, schema: dict,
              fn: Callable[[dict], str], counts_against_budget: bool = True) -> SdkMcpTool:
    """Wrap a synchronous tool function: budget check, tracing, error containment, thread offload."""

    @tool(name, description, schema)
    async def _handler(args: dict) -> dict:
        if counts_against_budget:
            ctx.calls += 1
            if ctx.calls > ctx.budget:
                msg = (f"Tool budget of {ctx.budget} calls is used up. Do not search further: "
                       f"call submit_report now with what you have and list remaining gaps.")
                ctx.trace.emit("tool_result", ctx.agent, {"tool": name, "budget_exhausted": True}, ctx.task.task_id)
                return {"content": [{"type": "text", "text": msg}]}
        ctx.trace.emit("tool_called", ctx.agent, {"tool": name, "args": args}, ctx.task.task_id)
        before = set(ctx.registry.for_agent(ctx.agent))
        t0 = time.time()
        try:
            text = await asyncio.to_thread(fn, args)
            is_error = False
        except Exception as e:  # tool errors go back to the agent, they never crash the run
            text, is_error = f"Tool error: {type(e).__name__}: {e}", True
        new_ids = [i for i in ctx.registry.for_agent(ctx.agent) if i not in before]
        ctx.retrieved_ids += new_ids
        ctx.trace.emit("tool_result", ctx.agent, {
            "tool": name, "evidence_ids": new_ids, "error": is_error, "seconds": round(time.time() - t0, 2),
            "evidence": [{"id": i, "title": ctx.registry.items[i].title, "locator": ctx.registry.items[i].locator,
                          "scores": ctx.registry.items[i].scores} for i in new_ids],
            "preview": text[:600]}, ctx.task.task_id)
        return {"content": [{"type": "text", "text": text}], **({"is_error": True} if is_error else {})}

    return _handler


# ----------------------------------------------------------------------------- report validation
def validate_report(body: ReportBody, own_ids: set[str]) -> list[str]:
    """Contract checks beyond the JSON schema. Returned problems are sent back to the agent."""
    problems = []

    def check_ids(ids: list[str], where: str) -> None:
        for i in ids:
            if i not in own_ids:
                problems.append(f"{where}: evidence id {i!r} was not returned by your tools in this task.")

    for n, f in enumerate(body.findings, 1):
        check_ids(f.evidence_ids, f"finding {n}")
        if f.basis in ("confirmed", "inferred") and not f.evidence_ids:
            problems.append(f"finding {n} has basis '{f.basis}' but cites no evidence id; cite evidence "
                            f"or mark it general_knowledge.")
        if f.basis == "general_knowledge" and f.confidence == "high":
            problems.append(f"finding {n} is general_knowledge (not from the knowledge base); its confidence cannot be 'high'.")
    for n, r in enumerate(body.recommendations, 1):
        check_ids(r.evidence_ids, f"recommendation {n}")
        for item in r.ranked_items:
            check_ids(item.evidence_ids, f"recommendation {n} ranked item {item.item!r}")
    if body.status == "ok" and not body.findings:
        problems.append("status 'ok' requires at least one finding.")
    for i in set(re.findall(r"\[([A-Z]+-\d+)\]", body.answer_summary)):
        if i not in own_ids:
            problems.append(f"answer_summary cites [{i}], which your tools did not return.")
    return problems


# ----------------------------------------------------------------------------- specialist
class Specialist:
    name: str = ""
    display_name: str = ""
    persona: str = ""                      # one-line persona title (shown on agent cards)
    capability: str = ""                   # one paragraph used in the router's capability cards
    routing_examples: list[str] = []       # example customer questions for this specialist

    def __init__(self):
        self.prompt_path = AGENTS_DIR / self.name / "prompt.md"

    # -- tools ---------------------------------------------------------------
    def domain_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        raise NotImplementedError

    def tool_specs(self) -> list[tuple[str, str]]:
        """(name, description) of every tool, for the prompt and the agent card."""
        dummy = ToolContext("-", SpecialistTask(task_id="-", run_id="-", agent=self.name, customer_request="-",
                                                objective="-"), self.name, EvidenceRegistry(),
                            TraceBus("-", persist=False), budget=0)
        return [(t.name, t.description) for t in self.all_tools(dummy)]

    def all_tools(self, ctx: ToolContext) -> list[SdkMcpTool]:
        return self.domain_tools(ctx) + [self._read_page_tool(ctx), self._submit_tool(ctx)]

    def _read_page_tool(self, ctx: ToolContext) -> SdkMcpTool:
        own = {s.source_id: s for s in sources_for(self.name) if s.collection != "trials"}
        pages: dict[tuple[str, int], str] = {}

        def load() -> None:
            if pages:
                return
            for col in {s.collection for s in own.values()}:
                for line in (INDEX_DIR / col / "pages.jsonl").open():
                    d = json.loads(line)
                    pages[(d["source_id"], d["page"])] = d["text"]

        def read_page(args: dict) -> str:
            load()
            sid, page = args["source_id"], int(args.get("page") or 1)
            if sid not in own:
                return f"Unknown source_id {sid!r}. Your sources: {', '.join(sorted(own))}"
            text = pages.get((sid, page))
            if text is None:
                return f"{sid} has no page {page}."
            src = own[sid]
            ev = ctx.registry.add(self.name, tool="read_page", query=None, source_id=sid, title=src.title,
                                  locator=f"p. {page}" if src.kind == "pdf" else "web page", page=page if src.kind == "pdf" else None,
                                  section=None, citation_url=(f"{src.citation_url}#page={page}" if src.citation_url and src.kind == "pdf"
                                                              else src.citation_url),
                                  local_path=str(src.local_path), snippet=text[:6000])
            return format_evidence(ev)

        return make_tool(ctx, "read_page",
                         "Read the full text of one page of one of your sources (to see a table or the context around a "
                         "search hit). Returns a new evidence id for that page. Args: source_id, page (1-based; web pages "
                         "have a single page 1).",
                         {"type": "object", "properties": {"source_id": {"type": "string"}, "page": {"type": "integer"}},
                          "required": ["source_id"]}, read_page)

    def _submit_tool(self, ctx: ToolContext) -> SdkMcpTool:
        def submit(args: dict) -> str:
            ctx.submit_attempts += 1
            try:
                body = ReportBody.model_validate(args)
            except ValidationError as e:
                return f"REJECTED: the report does not match the contract:\n{e}\nFix it and call submit_report again."
            problems = validate_report(body, set(ctx.registry.for_agent(self.name)))
            if problems and ctx.submit_attempts < 3:
                ctx.trace.emit("tool_result", self.name, {"tool": "submit_report", "rejected": problems}, ctx.task.task_id)
                return "REJECTED:\n- " + "\n- ".join(problems) + "\nFix these and call submit_report again."
            ctx.report = body
            return "ACCEPTED. Your report was delivered to the manager. Reply with the single word DONE."

        return make_tool(ctx, "submit_report",
                         "Deliver your final report to the manager. Call exactly once, at the end. The input must follow "
                         "the report contract; every evidence id you cite must come from your own tool results.",
                         inline_schema(ReportBody), submit, counts_against_budget=False)

    # -- prompt --------------------------------------------------------------
    def grounding_section(self) -> str:
        lines = []
        by_collection: dict[str, list[Source]] = {}
        for s in sources_for(self.name):
            by_collection.setdefault(s.collection, []).append(s)
        for col, srcs in by_collection.items():
            lines.append(f"\nCollection `{col}`:")
            for s in srcs:
                url = f" <{s.citation_url}>" if s.citation_url else ""
                lines.append(f"- `{s.source_id}`: {s.title}{url}")
        lines.append("\nKnown gaps (say so when a question needs them; never fill them from memory):")
        lines += [f"- {g}" for g in KNOWN_GAPS[self.name]]
        return "\n".join(lines)

    def system_prompt(self) -> str:
        tools = "\n".join(f"- `{n}`: {d}" for n, d in self.tool_specs())
        body = self.prompt_path.read_text()
        policy = COMMON_POLICY.read_text().replace("{{PREFIX}}", EVIDENCE_PREFIX[self.name])
        return (body.replace("{{SOURCES}}", self.grounding_section())
                    .replace("{{TOOLS}}", tools)
                    .replace("{{COMMON_POLICY}}", policy))

    # -- run -----------------------------------------------------------------
    @staticmethod
    def task_prompt(task: SpecialistTask) -> str:
        payload = task.model_dump(mode="json", exclude_none=True)
        return ("You have been assigned the following task by the Engagement Manager. The JSON below is your "
                "complete input (SpecialistTask contract).\n\n```json\n" + json.dumps(payload, indent=2, ensure_ascii=False)
                + "\n```\n\nWork the task with your tools, then call `submit_report`.")

    async def run(self, task: SpecialistTask, registry: EvidenceRegistry, trace: TraceBus, model: str) -> SpecialistReport:
        cfg = settings()["orchestration"]
        ctx = ToolContext(task.run_id, task, self.name, registry, trace, budget=task.budget_tool_calls)
        t0 = time.time()

        def on_message(kind: str, text: Any) -> None:
            trace.emit("agent_message", self.name, {"kind": kind, "text": str(text)[:2000]}, task.task_id)

        run = await run_agent(
            prompt=self.task_prompt(task), system_prompt=self.system_prompt(),
            server_name=f"{self.name}_kb", tools=self.all_tools(ctx), model=model,
            max_turns=cfg["specialist_max_turns"], is_done=lambda: ctx.report is not None,
            nudge="You stopped without delivering your report. Call `submit_report` now with your findings so far; "
                  "use status 'partial' or 'insufficient_evidence' if appropriate and list the gaps.",
            on_message=on_message)
        own = registry.for_agent(self.name)
        if ctx.report is None:
            return SpecialistReport(status="failed", task_id=task.task_id, agent=self.name, round=task.round,
                                    answer_summary="The specialist did not deliver a report.",
                                    error="no submit_report call", raw_text=run.text[-4000:],
                                    retrieved_evidence_count=len(ctx.retrieved_ids), tool_calls=ctx.calls,
                                    model=model, duration_s=round(time.time() - t0, 2), usage=run.meta.as_dict())
        body = ctx.report
        cited = _cited_ids(body)
        return SpecialistReport(**body.model_dump(), task_id=task.task_id, agent=self.name, round=task.round,
                                evidence=[own[i] for i in cited if i in own],
                                retrieved_evidence_count=len(ctx.retrieved_ids), tool_calls=ctx.calls,
                                model=model, duration_s=round(time.time() - t0, 2), usage=run.meta.as_dict())


def _cited_ids(body: ReportBody) -> list[str]:
    ids: list[str] = []
    for f in body.findings:
        ids += f.evidence_ids
    for r in body.recommendations:
        ids += r.evidence_ids
        for it in r.ranked_items:
            ids += it.evidence_ids
    ids += re.findall(r"\[([A-Z]+-\d+)\]", body.answer_summary)
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


# ----------------------------------------------------------------------------- shared search tool helper
def search_and_register(ctx: ToolContext, tool_name: str, collection_name: str, query: str, k: int,
                        where: Callable[[dict], bool] | None = None, extra: Callable[[dict], str] | None = None) -> str:
    """Run a retrieval query, register each hit as evidence, and format the result for the agent."""
    from consultai.retrieval.store import collection

    snippet_chars = settings()["retrieval"]["snippet_chars"]
    hits = collection(collection_name).search(query, k=max(1, min(int(k), 10)), where=where)
    if not hits:
        return f"No results in `{collection_name}` for {query!r} with these filters. Try broader terms or fewer filters."
    blocks = []
    for h in hits:
        ev = ctx.registry.add_hit(ctx.agent, tool_name, query, h, snippet_chars)
        blocks.append(format_evidence(ev, extra(h.chunk) if extra else ""))
    return f"{len(hits)} results for {query!r} (ranked by hybrid BM25+dense retrieval with cross-encoder rerank):\n\n" \
           + "\n\n".join(blocks)

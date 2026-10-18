"""The Management Consulting Manager Agent: intake -> route -> dispatch -> review -> synthesize.

    result = await Orchestrator(profile="demo").consult("Our Cisco router ...")

1. Route & plan   small model fills a RoutingDecision (which specialists, sub-questions, dependencies);
                  code enforces the contract; kNN router is the fallback.
2. Dispatch       one SpecialistTask per assignment, run as a DAG (parallel where independent),
                  each with a timeout; failures become `failed` reports instead of crashing the run.
3. Review         the manager's progress ledger: goal met? gaps? conflicts? -> at most N follow-up tasks
                  in one extra round (possibly to a specialist that was not routed at first).
4. Synthesize     the manager writes the ConsultingResponse from the full reports.
5. Verify         every cited evidence id is resolved against the specialists' evidence.
Every step is emitted to the TraceBus (runs/<run_id>/trace.jsonl) and the whole run is saved as run.json.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Callable

from claude_agent_sdk import ClaudeSDKError
from pydantic import BaseModel, Field

from consultai.agents.base import EvidenceRegistry
from consultai.agents.registry import get as get_specialist
from consultai.config import model_profile, settings
from consultai.contracts import (ConsultingResponse, ReviewDecision, RoutingDecision, SpecialistReport,
                                 SpecialistTask)
from consultai.llm.claude_runner import CallMeta, ClaudeRunnerError, run_structured
from consultai.orchestrator import router
from consultai.orchestrator.citations import validate_response
from consultai.orchestrator.ledger import Ledger
from consultai.orchestrator.scheduler import run_dag
from consultai.orchestrator.trace import TraceBus

MANAGER_DIR = Path(__file__).resolve().parents[1] / "agents" / "manager"


class Turn(BaseModel):
    request: str
    executive_summary: str = ""
    questions_for_customer: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: str
    request: str
    profile: str
    models: dict
    routing: RoutingDecision
    ledger: Ledger
    tasks: list[SpecialistTask] = Field(default_factory=list)
    reports: list[SpecialistReport] = Field(default_factory=list)
    reviews: list[ReviewDecision] = Field(default_factory=list)
    response: ConsultingResponse
    citation_check: dict = Field(default_factory=dict)
    timings: dict = Field(default_factory=dict)
    usage: dict = Field(default_factory=dict)
    run_dir: str | None = None


def _history_text(history: list[Turn] | None) -> str | None:
    if not history:
        return None
    lines = []
    for i, t in enumerate(history[-3:], 1):
        lines.append(f"Turn {i} request: {t.request}\nTurn {i} our summary: {t.executive_summary}")
        if t.questions_for_customer:
            lines.append(f"Turn {i} we asked: " + " | ".join(t.questions_for_customer))
    return "\n".join(lines)


class Orchestrator:
    def __init__(self, profile: str | None = None, persist: bool = True,
                 review_enabled: bool | None = None, inject_failure: str | None = None):
        self.profile = model_profile(profile)
        self.cfg = settings()["orchestration"]
        self.persist = persist
        self.review_enabled = self.cfg["review_enabled"] if review_enabled is None else review_enabled
        self.inject_failure = inject_failure  # test hook: make this agent time out (demonstrates containment)

    # ------------------------------------------------------------------ public
    async def consult(self, request: str, history: list[Turn] | None = None,
                      on_event: Callable[[dict], None] | None = None) -> RunResult:
        run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        trace = TraceBus(run_id, persist=self.persist)
        if on_event:
            trace.subscribe(on_event)
        usage: dict[str, CallMeta] = {}
        timings: dict[str, float] = {}
        t0 = time.time()
        hist = _history_text(history)
        trace.emit("run_started", "manager", {"request": request, "profile": self.profile.name,
                                              "models": self.profile.__dict__, "history": hist})

        # 1. route
        routing = await self._route(request, hist, trace, usage)
        timings["routing_s"] = round(time.time() - t0, 2)
        ledger = Ledger.from_routing(request, routing)
        registry = EvidenceRegistry()

        if routing.blocking or not routing.assignments:
            response = self._no_dispatch_response(routing)
            trace.emit("clarification_requested", "manager", response)
            return self._finish(run_id, request, routing, ledger, [], [], [], response, {}, timings, usage, trace, t0)

        # 2. dispatch round 1
        tasks, deps = self._tasks_from_routing(run_id, request, hist, routing)
        ledger.add_plan(tasks, deps)
        t1 = time.time()
        results = await run_dag(tasks, deps, lambda t: self._run_specialist(t, registry, trace, usage),
                                trace, self.cfg["max_parallel_specialists"])
        reports = [results[t.task_id] for t in tasks]
        timings["round1_s"] = round(time.time() - t1, 2)
        all_tasks, reviews = list(tasks), []

        # 3. review -> optional follow-up round
        if self.review_enabled:
            review = await self._review(request, routing, all_tasks, reports, trace, usage)
            if review:
                reviews.append(review)
            ledger.record_round(1, reports, review)
            if review and review.follow_ups and not review.goal_met and self.cfg["max_follow_up_rounds"] > 0:
                fu_tasks = self._follow_up_tasks(run_id, request, hist, review, reports)
                ledger.add_plan(fu_tasks, {})
                t2 = time.time()
                fu_results = await run_dag(fu_tasks, {}, lambda t: self._run_specialist(t, registry, trace, usage),
                                           trace, self.cfg["max_parallel_specialists"])
                fu_reports = [fu_results[t.task_id] for t in fu_tasks]
                timings["round2_s"] = round(time.time() - t2, 2)
                all_tasks += fu_tasks
                reports += fu_reports
                ledger.record_round(2, fu_reports, None)
        else:
            ledger.record_round(1, reports, None)

        # 4. synthesize + 5. verify citations
        t3 = time.time()
        response = await self._synthesize(request, hist, routing, reports, reviews, trace, usage)
        response, check = validate_response(response, reports)
        timings["synthesis_s"] = round(time.time() - t3, 2)
        trace.emit("citation_check", "manager", check)
        return self._finish(run_id, request, routing, ledger, all_tasks, reports, reviews, response, check,
                            timings, usage, trace, t0)

    # ------------------------------------------------------------------ steps
    async def _route(self, request: str, hist: str | None, trace: TraceBus, usage: dict) -> RoutingDecision:
        try:
            decision, meta = await router.llm_route(request, hist, self.profile.router, self.cfg["llm_call_timeout_s"])
            usage["router"] = meta
        except (ClaudeRunnerError, ClaudeSDKError, asyncio.TimeoutError) as e:
            trace.emit("error", "router", {"stage": "routing", "error": repr(e), "fallback": "knn"})
            decision = await asyncio.to_thread(router.knn_route, request)
        decision = router.enforce_contract(decision)
        trace.emit("routing_decided", "router", decision)
        return decision

    def _tasks_from_routing(self, run_id: str, request: str, hist: str | None,
                            routing: RoutingDecision) -> tuple[list[SpecialistTask], dict[str, list[str]]]:
        tasks, by_agent = [], {}
        for n, a in enumerate(routing.assignments, 1):
            t = SpecialistTask(task_id=f"T{n}", run_id=run_id, agent=a.agent, customer_request=request,
                               conversation_context=hist, objective=a.sub_question, entities=a.entities,
                               expected_outputs=a.expected_outputs,
                               constraints=[f"Out of scope for the platform (do not attempt): {x}" for x in routing.out_of_scope],
                               budget_tool_calls=self.cfg["specialist_max_tool_calls"])
            tasks.append(t)
            by_agent[a.agent] = t.task_id
        deps = {by_agent[a.agent]: [by_agent[d] for d in a.depends_on] for a in routing.assignments}
        return tasks, deps

    def _follow_up_tasks(self, run_id: str, request: str, hist: str | None, review: ReviewDecision,
                         reports: list[SpecialistReport]) -> list[SpecialistTask]:
        from consultai.orchestrator.scheduler import upstream_context

        out = []
        for n, f in enumerate(review.follow_ups[: self.cfg["max_follow_up_tasks"]], 1):
            out.append(SpecialistTask(
                task_id=f"R2-T{n}", run_id=run_id, agent=f.agent, round=2, customer_request=request,
                conversation_context=hist, objective=f.objective, follow_up_reason=f.reason,
                upstream=[upstream_context(r) for r in reports if r.status != "failed"],
                budget_tool_calls=max(4, self.cfg["specialist_max_tool_calls"] // 2)))
        return out

    async def _run_specialist(self, task: SpecialistTask, registry: EvidenceRegistry, trace: TraceBus,
                              usage: dict) -> SpecialistReport:
        agent = get_specialist(task.agent)
        timeout = 1 if self.inject_failure == task.agent else self.cfg["specialist_timeout_s"]
        t0 = time.time()
        for attempt in range(self.cfg["transport_retries"] + 1):
            try:
                report = await asyncio.wait_for(agent.run(task, registry, trace, self.profile.specialist), timeout)
                break
            except asyncio.TimeoutError:
                report = self._failed(task, f"timed out after {timeout}s", registry, t0)
                break
            except (ClaudeSDKError, ClaudeRunnerError, OSError) as e:
                trace.emit("error", task.agent, {"stage": "specialist", "attempt": attempt + 1, "error": repr(e)}, task.task_id)
                report = self._failed(task, f"{type(e).__name__}: {e}", registry, t0)
            except Exception as e:  # unexpected bug in a tool or agent: contain it, never crash the run
                trace.emit("error", task.agent, {"stage": "specialist", "error": repr(e)}, task.task_id)
                report = self._failed(task, f"{type(e).__name__}: {e}", registry, t0)
                break
        usage[f"{task.task_id}:{task.agent}"] = report.usage
        trace.emit("report_received", task.agent, report, task.task_id)
        return report

    @staticmethod
    def _failed(task: SpecialistTask, error: str, registry: EvidenceRegistry, t0: float) -> SpecialistReport:
        return SpecialistReport(status="failed", task_id=task.task_id, agent=task.agent, round=task.round,
                                answer_summary=f"The {task.agent} specialist did not complete: {error}.",
                                error=error, retrieved_evidence_count=len(registry.for_agent(task.agent)),
                                duration_s=round(time.time() - t0, 2))

    async def _review(self, request, routing, tasks, reports, trace, usage) -> ReviewDecision | None:
        system = (MANAGER_DIR / "review_prompt.md").read_text().replace("{{MAX_FOLLOW_UPS}}",
                                                                         str(self.cfg["max_follow_up_tasks"]))
        payload = {"customer_request": request, "routing": routing.model_dump(mode="json"),
                   "tasks": [t.model_dump(mode="json", exclude={"upstream"}) for t in tasks],
                   "reports": [r.model_dump(mode="json", exclude={"raw_text", "usage"}) for r in reports]}
        try:
            review, meta = await run_structured(json.dumps(payload, ensure_ascii=False), system, ReviewDecision,
                                                self.profile.review, timeout_s=self.cfg["llm_call_timeout_s"])
            usage["review"] = meta
        except (ClaudeRunnerError, ClaudeSDKError) as e:
            trace.emit("error", "manager", {"stage": "review", "error": repr(e)})
            return None
        trace.emit("review_decision", "manager", review)
        return review

    async def _synthesize(self, request, hist, routing, reports, reviews, trace, usage) -> ConsultingResponse:
        trace.emit("synthesis_started", "manager", {"reports": [r.task_id for r in reports]})
        system = (MANAGER_DIR / "synthesis_prompt.md").read_text()
        payload = {"customer_request": request, "earlier_turns": hist,
                   "routing": routing.model_dump(mode="json"),
                   "reports": [r.model_dump(mode="json", exclude={"raw_text", "usage"}) for r in reports],
                   "review": [r.model_dump(mode="json") for r in reviews],
                   "failed_specialists": [r.agent for r in reports if r.status == "failed"]}
        try:
            resp, meta = await run_structured(json.dumps(payload, ensure_ascii=False), system, ConsultingResponse,
                                              self.profile.synthesis, timeout_s=self.cfg["llm_call_timeout_s"] * 2)
            usage["synthesis"] = meta
        except (ClaudeRunnerError, ClaudeSDKError) as e:
            trace.emit("error", "manager", {"stage": "synthesis", "error": repr(e)})
            resp = self._fallback_response(reports, repr(e))
        trace.emit("synthesis_done", "manager", resp)
        return resp

    # ------------------------------------------------------------------ deterministic responses
    @staticmethod
    def _no_dispatch_response(routing: RoutingDecision) -> ConsultingResponse:
        if routing.blocking:
            summary = "We need a little more information before our specialists can start."
        else:
            summary = ("This request is outside what our specialists can answer from their grounded sources, so no "
                       "specialist was assigned.")
        return ConsultingResponse(executive_summary=summary, answer=summary,
                                  questions_for_customer=routing.clarifying_questions,
                                  limitations=routing.out_of_scope or ["No specialist domain matched the request."])

    @staticmethod
    def _fallback_response(reports: list[SpecialistReport], error: str) -> ConsultingResponse:
        """If synthesis itself fails, return the specialists' own summaries verbatim (clearly labelled)."""
        parts = [f"**{r.agent}** ({r.status}): {r.answer_summary}" for r in reports]
        return ConsultingResponse(executive_summary="Synthesis failed; the specialists' own summaries follow.",
                                  answer="\n\n".join(parts),
                                  limitations=[f"Manager synthesis failed: {error}"])

    def _finish(self, run_id, request, routing, ledger, tasks, reports, reviews, response, check,
                timings, usage, trace, t0) -> RunResult:
        timings["total_s"] = round(time.time() - t0, 2)
        flat = {k: (v.as_dict() if isinstance(v, CallMeta) else v) for k, v in usage.items()}
        totals = {"cost_usd_api_equivalent": round(sum((v or {}).get("cost_usd", 0) or 0 for v in flat.values()), 4),
                  "output_tokens": sum((v or {}).get("output_tokens", 0) or 0 for v in flat.values())}
        result = RunResult(run_id=run_id, request=request, profile=self.profile.name, models=self.profile.__dict__,
                           routing=routing, ledger=ledger, tasks=tasks, reports=reports, reviews=reviews,
                           response=response, citation_check=check, timings=timings,
                           usage={"calls": flat, "totals": totals},
                           run_dir=str(trace.dir) if trace.dir else None)
        trace.emit("run_finished", "manager", {"timings": timings, "usage": totals,
                                               "agents": [t.agent for t in tasks]})
        trace.save_json("run.json", result)
        return result

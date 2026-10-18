"""Offline tests of the inter-agent contracts and the orchestration machinery (no Claude calls)."""
from __future__ import annotations

import asyncio
import time

from consultai.agents.base import EvidenceRegistry, validate_report
from consultai.contracts import (Assignment, ConsultingRecommendation, ConsultingResponse, Entities, Evidence,
                                 Finding, ReportBody, RoutingDecision, SpecialistReport, SpecialistTask,
                                 inline_schema)
from consultai.orchestrator.citations import validate_response
from consultai.orchestrator.router import enforce_contract
from consultai.orchestrator.scheduler import run_dag
from consultai.orchestrator.trace import TraceBus
from consultai.agents.sec.agent import safe_eval


def _task(tid: str, agent: str) -> SpecialistTask:
    return SpecialistTask(task_id=tid, run_id="test", agent=agent, customer_request="r", objective="o")


def _report(task: SpecialistTask, status: str = "ok") -> SpecialistReport:
    return SpecialistReport(status=status, task_id=task.task_id, agent=task.agent, answer_summary=f"{task.agent} done")


def test_contract_round_trip():
    task = _task("T1", "technology")
    task.entities = Entities(products=["ISR4331"], fiscal_years=[2025])
    assert SpecialistTask.model_validate_json(task.model_dump_json()) == task
    schema = inline_schema(ReportBody)
    assert "$defs" not in str(schema) and "$ref" not in str(schema)
    assert "findings" in schema["properties"]


def test_evidence_ids_are_agent_prefixed_and_unique():
    reg = EvidenceRegistry()
    a = reg.add("technology", tool="t", source_id="s", title="x", locator="p. 1", snippet="...")
    b = reg.add("sec", tool="t", source_id="s", title="x", locator="p. 1", snippet="...")
    c = reg.add("technology", tool="t", source_id="s", title="x", locator="p. 2", snippet="...")
    assert (a.evidence_id, b.evidence_id, c.evidence_id) == ("TECH-1", "SEC-1", "TECH-2")
    assert set(reg.for_agent("technology")) == {"TECH-1", "TECH-2"}


def test_submit_report_validation_rejects_unknown_and_uncited():
    body = ReportBody(status="ok", answer_summary="Revenue rose [SEC-9].", findings=[
        Finding(claim="a", basis="confirmed", evidence_ids=["SEC-1"], confidence="high", confidence_reason="x"),
        Finding(claim="b", basis="confirmed", evidence_ids=[], confidence="medium", confidence_reason="x"),
        Finding(claim="c", basis="general_knowledge", evidence_ids=[], confidence="high", confidence_reason="x"),
        Finding(claim="d", basis="inferred", evidence_ids=["TECH-1"], confidence="low", confidence_reason="x"),
    ])
    problems = " ".join(validate_report(body, own_ids={"SEC-1"}))
    assert "SEC-9" in problems            # cited in text but never retrieved
    assert "finding 2" in problems         # confirmed without evidence
    assert "finding 3" in problems         # general knowledge cannot be high confidence
    assert "TECH-1" in problems            # another agent's evidence
    assert validate_report(ReportBody(status="ok", answer_summary="ok [SEC-1]", findings=[
        Finding(claim="a", basis="confirmed", evidence_ids=["SEC-1"], confidence="high", confidence_reason="x")]),
        own_ids={"SEC-1"}) == []


def test_router_contract_threshold_dedupe_and_cycles():
    a = lambda agent, rel, deps=(): Assignment(agent=agent, relevance=rel, rationale="", sub_question="q",  # noqa: E731
                                               depends_on=list(deps))
    d = RoutingDecision(intents=["x"], assignments=[
        a("technology", 0.9, ["csr"]), a("csr", 0.8, ["technology"]),   # cycle
        a("sec", 0.7, ["sec", "clinical"]),                               # self + not-assigned dependency
        a("clinical", 0.2), a("technology", 0.6)])                        # below threshold, duplicate
    out = enforce_contract(d, threshold=0.5)
    agents = [x.agent for x in out.assignments]
    assert agents == ["technology", "csr", "sec"]
    deps = {x.agent: x.depends_on for x in out.assignments}
    assert deps["sec"] == []
    assert not (deps["technology"] == ["csr"] and deps["csr"] == ["technology"])  # cycle broken


def test_scheduler_runs_dependencies_in_order_and_in_parallel():
    t1, t2, t3 = _task("T1", "csr"), _task("T2", "technology"), _task("T3", "sec")
    started, finished = {}, {}

    async def runner(task):
        started[task.task_id] = time.time()
        await asyncio.sleep(0.2)
        finished[task.task_id] = time.time()
        return _report(task)

    res = asyncio.run(run_dag([t1, t2, t3], {"T2": ["T1"]}, runner, TraceBus("t", persist=False), 4))
    assert set(res) == {"T1", "T2", "T3"}
    assert started["T2"] >= finished["T1"]              # dependent waits for upstream
    assert abs(started["T1"] - started["T3"]) < 0.1      # independent tasks start together
    assert [u.agent for u in t2.upstream] == ["csr"]     # upstream findings attached losslessly


def test_scheduler_contains_failures():
    t1, t2 = _task("T1", "csr"), _task("T2", "technology")

    async def runner(task):
        if task.agent == "csr":
            return _report(task, status="failed")
        return _report(task)

    res = asyncio.run(run_dag([t1, t2], {"T2": ["T1"]}, runner, TraceBus("t", persist=False), 4))
    assert res["T1"].status == "failed" and res["T2"].status == "ok"
    assert any("failed" in c for c in t2.constraints)    # dependent is told its upstream failed


def test_citation_validator_strips_unknown_ids():
    ev = Evidence(evidence_id="TECH-1", agent="technology", tool="t", source_id="s", title="x", locator="p. 1", snippet="s")
    rep = SpecialistReport(status="ok", task_id="T1", agent="technology", answer_summary="a", evidence=[ev])
    resp = ConsultingResponse(executive_summary="See [TECH-1] and [SEC-4].", answer="Do X [TECH-1].",
                              recommendations=[ConsultingRecommendation(action="a", why="w", priority="high",
                                                                        owner_agents=["technology"],
                                                                        evidence_ids=["TECH-1", "TECH-77"],
                                                                        basis="general_knowledge", confidence="high")])
    resp, check = validate_response(resp, [rep])
    assert check["invalid"] == ["SEC-4", "TECH-77"]
    assert resp.recommendations[0].evidence_ids == ["TECH-1"]
    assert resp.recommendations[0].confidence == "medium"
    assert "unverified citation removed" in resp.executive_summary


def test_safe_eval_is_arithmetic_only():
    assert abs(safe_eval("(56,654-53,803)/53,803*100") - 5.2989) < 1e-3
    for bad in ["__import__('os')", "a+1", "open('x')"]:
        try:
            safe_eval(bad)
            raise AssertionError(bad)
        except ValueError:
            pass
        except SyntaxError:
            pass

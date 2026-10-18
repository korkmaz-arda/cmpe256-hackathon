"""End-to-end response quality on the scenario set (datasets/scenarios.json).

    python -m consultai.eval.response_quality --profile dev [--reuse] [--only id1,id2]

For each scenario the full orchestrator runs (or, with --reuse, the latest saved run of the same request and
profile is loaded from runs/). Measured:
  deterministic  routing correct (exact agent set), citation valid rate, share of specialist findings that cite
                 evidence (confirmed/inferred), required sections present, latency
  LLM judge      (a) claim faithfulness: up to 8 claims from the answer, each shown WITH the evidence snippets it
                 cites -> supported / partial / unsupported;  (b) rubric 1-5: actionability, completeness,
                 uncertainty handling, cross-domain integration (multi-agent scenarios only)
The judge is the profile's `judge` model (a Claude model judging Claude output: possible self-preference bias,
reported as a limitation).
"""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Literal

from pydantic import BaseModel, Field

from consultai.config import RUNS_DIR, model_profile
from consultai.eval.common import DATASETS, md_table, save_result
from consultai.llm.claude_runner import run_structured
from consultai.orchestrator.citations import evidence_index
from consultai.orchestrator.manager import Orchestrator, RunResult

JUDGE_SYSTEM = """You are a strict evaluator of consulting answers produced by an AI system that must be grounded in
retrieved evidence. For each claim you get the evidence snippets the claim cites. Judge ONLY against those snippets:
supported = the snippets state it; partial = some of it is supported, or it overstates/generalises; unsupported = the
snippets do not support it. Then rate the whole answer 1-5 on: actionability (clear next steps, owners, KPIs),
completeness (covers every part of the request that the sources allow), uncertainty_handling (separates confirmed facts
from hypotheses, admits gaps, asks for missing information), and cross_domain_integration (only if several specialists
contributed: are their findings connected and reconciled rather than listed? otherwise null). Be terse."""


class ClaimVerdict(BaseModel):
    claim_index: int
    verdict: Literal["supported", "partial", "unsupported"]
    reason: str


class Judgement(BaseModel):
    claims: list[ClaimVerdict] = Field(default_factory=list)
    actionability: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    uncertainty_handling: int = Field(ge=1, le=5)
    cross_domain_integration: int | None = Field(default=None, ge=1, le=5)
    comment: str


def _latest_saved(request: str, profile: str) -> RunResult | None:
    if not RUNS_DIR.exists():
        return None
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        f = d / "run.json"
        if f.exists():
            data = json.loads(f.read_text())
            if data.get("request") == request and data.get("profile") == profile:
                return RunResult.model_validate(data)
    return None


def _claims(run: RunResult, limit: int = 8) -> list[dict]:
    idx = evidence_index(run.reports)
    items = [(c.statement, c.evidence_ids) for c in run.response.confirmed]
    items += [(f"{r.action} - because {r.why}", r.evidence_ids) for r in run.response.recommendations]
    items += [(i.insight, i.evidence_ids) for i in run.response.cross_domain_insights]
    out = []
    for text, ids in items:
        ids = [i for i in ids if i in idx][:4]
        if ids:
            out.append({"claim": text, "evidence": [{"id": i, "source": idx[i].title, "where": idx[i].locator,
                                                      "snippet": idx[i].snippet[:1200]} for i in ids]})
        if len(out) >= limit:
            break
    return out


def deterministic(run: RunResult, expected: list[str]) -> dict:
    findings = [f for r in run.reports for f in r.findings]
    grounded = [f for f in findings if f.basis in ("confirmed", "inferred")]
    resp = run.response
    oos = not expected
    sections_ok = bool(resp.executive_summary) and (oos or (bool(resp.recommendations) and bool(resp.next_steps)
                                                           and bool(resp.impact_metrics)))
    return {
        "routing_correct": sorted(t.agent for t in run.tasks if t.round == 1) == sorted(expected),
        "agents": sorted({t.agent for t in run.tasks}),
        "follow_up_round": any(t.round > 1 for t in run.tasks),
        "citation_valid_rate": run.citation_check.get("valid_rate"),
        "unique_citations": run.citation_check.get("unique_cited", 0),
        "findings_with_evidence": round(sum(bool(f.evidence_ids) for f in grounded) / len(grounded), 3) if grounded else None,
        "uncertainty_labeled": oos or bool(resp.hypotheses or resp.questions_for_customer or resp.limitations),
        "sections_complete": sections_ok,
        "failed_specialists": [r.agent for r in run.reports if r.status == "failed"],
        "seconds": run.timings.get("total_s"),
    }


async def evaluate_one(sc: dict, profile: str, reuse: bool, sem: asyncio.Semaphore) -> dict:
    async with sem:
        run = _latest_saved(sc["request"], profile) if reuse else None
        if run is None:
            run = await Orchestrator(profile=profile).consult(sc["request"])
        det = deterministic(run, sc["expected_agents"])
        claims = _claims(run)
        judge = None
        if run.reports:
            payload = {"customer_request": sc["request"], "answer_markdown": run.response.answer,
                       "executive_summary": run.response.executive_summary,
                       "next_steps": [s.model_dump() for s in run.response.next_steps],
                       "impact_metrics": [m.model_dump() for m in run.response.impact_metrics],
                       "hypotheses": [h.statement for h in run.response.hypotheses],
                       "questions_for_customer": run.response.questions_for_customer,
                       "limitations": run.response.limitations,
                       "specialists": det["agents"],
                       "claims": [{"index": n, **c} for n, c in enumerate(claims)]}
            try:
                judge, _ = await run_structured(json.dumps(payload, ensure_ascii=False), JUDGE_SYSTEM, Judgement,
                                                model_profile(profile).judge, timeout_s=300)
            except Exception as e:
                det["judge_error"] = repr(e)
        res = {"id": sc["id"], "kind": sc["kind"], "run_id": run.run_id, **det}
        if judge:
            v = [c.verdict for c in judge.claims]
            res.update({"claims_judged": len(v),
                        "faithfulness": round((v.count("supported") + 0.5 * v.count("partial")) / len(v), 3) if v else None,
                        "unsupported_claims": [claims[c.claim_index]["claim"][:120] for c in judge.claims
                                               if c.verdict == "unsupported" and c.claim_index < len(claims)],
                        "actionability": judge.actionability, "completeness": judge.completeness,
                        "uncertainty_handling": judge.uncertainty_handling,
                        "cross_domain_integration": judge.cross_domain_integration, "judge_comment": judge.comment})
        print(f"[{sc['id']}] routing_ok={det['routing_correct']} cites={det['unique_citations']} "
              f"valid={det['citation_valid_rate']} faith={res.get('faithfulness')} {det['seconds']}s", flush=True)
        return res


def run(profile: str | None, reuse: bool, only: list[str] | None, concurrency: int = 3) -> dict:
    profile = model_profile(profile).name
    scenarios = [s for s in json.loads((DATASETS / "scenarios.json").read_text()) if not only or s["id"] in only]

    async def main():
        sem = asyncio.Semaphore(concurrency)
        return await asyncio.gather(*(evaluate_one(s, profile, reuse, sem) for s in scenarios))

    results = asyncio.run(main())

    def mean(key):
        vals = [r[key] for r in results if isinstance(r.get(key), (int, float)) and not isinstance(r.get(key), bool)]
        return round(sum(vals) / len(vals), 3) if vals else None

    overall = {"scenarios": len(results),
               "routing_accuracy": round(sum(r["routing_correct"] for r in results) / len(results), 3),
               "citation_valid_rate": mean("citation_valid_rate"), "findings_with_evidence": mean("findings_with_evidence"),
               "claim_faithfulness": mean("faithfulness"), "actionability": mean("actionability"),
               "completeness": mean("completeness"), "uncertainty_handling": mean("uncertainty_handling"),
               "cross_domain_integration": mean("cross_domain_integration"),
               "sections_complete": round(sum(r["sections_complete"] for r in results) / len(results), 3),
               "mean_seconds": mean("seconds")}
    table = md_table([{k: r.get(k, "-") if r.get(k) is not None else "-" for k in
                       ("id", "routing_correct", "unique_citations", "citation_valid_rate", "findings_with_evidence",
                        "faithfulness", "actionability", "completeness", "uncertainty_handling",
                        "cross_domain_integration", "seconds")} for r in results],
                     ["id", "routing_correct", "unique_citations", "citation_valid_rate", "findings_with_evidence",
                      "faithfulness", "actionability", "completeness", "uncertainty_handling", "cross_domain_integration",
                      "seconds"])
    summary = "**Overall:** " + ", ".join(f"{k} = {v}" for k, v in overall.items()) + f"\n\n{table}"
    path = save_result("response_quality", {"profile": profile, "judge": model_profile(profile).judge,
                                            "overall": overall, "results": results, "summary_md": summary})
    print(summary, f"\n-> {path}")
    return overall


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="dev")
    ap.add_argument("--reuse", action="store_true", help="reuse the latest saved run of each scenario if present")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    run(a.profile, a.reuse, a.only.split(",") if a.only else None)

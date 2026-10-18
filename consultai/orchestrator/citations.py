"""Citation validation of the manager's final answer.

Every evidence id the synthesis cites must resolve to evidence that a specialist report actually cited.
Unresolvable ids are removed from structured fields and marked in the text, and every problem is reported
in the run's `citation_check` (shown in the UI and used by the response-quality evaluation).
"""
from __future__ import annotations

import re

from consultai.contracts import ConsultingResponse, Evidence, SpecialistReport, agent_of_evidence

ID_RE = re.compile(r"\[([A-Z]+-\d+)\]")


def evidence_index(reports: list[SpecialistReport]) -> dict[str, Evidence]:
    return {e.evidence_id: e for r in reports for e in r.evidence}


def validate_response(resp: ConsultingResponse, reports: list[SpecialistReport]) -> tuple[ConsultingResponse, dict]:
    index = evidence_index(reports)
    cited: list[str] = []
    invalid: list[str] = []
    attribution_mismatch: list[str] = []
    single_agent_insights: list[str] = []

    def keep(ids: list[str]) -> list[str]:
        good = []
        for i in ids:
            cited.append(i)
            if i in index:
                good.append(i)
            else:
                invalid.append(i)
        return good

    downgraded = []
    for rec in resp.recommendations:
        rec.evidence_ids = keep(rec.evidence_ids)
        if rec.basis == "general_knowledge" and rec.confidence == "high":
            rec.confidence = "medium"  # policy: advice not grounded in the knowledge base is never high confidence
            downgraded.append(rec.action[:80])
    for ins in resp.cross_domain_insights:
        ins.evidence_ids = keep(ins.evidence_ids)
        if len(set(ins.agents)) < 2:
            single_agent_insights.append(ins.insight[:80])
    for claim in resp.confirmed + resp.hypotheses:
        claim.evidence_ids = keep(claim.evidence_ids)
        for i in claim.evidence_ids:
            if agent_of_evidence(i) != claim.agent:
                attribution_mismatch.append(f"{i} attributed to {claim.agent}")

    def fix_text(text: str) -> str:
        def sub(m: re.Match) -> str:
            i = m.group(1)
            cited.append(i)
            if i in index:
                return m.group(0)
            invalid.append(i)
            return f"[{i}: unverified citation removed]"
        return ID_RE.sub(sub, text)

    resp.answer = fix_text(resp.answer)
    resp.executive_summary = fix_text(resp.executive_summary)

    unique = list(dict.fromkeys(cited))
    check = {
        "citations_total": len(cited),
        "unique_cited": len(unique),
        "invalid": sorted(set(invalid)),
        "valid_rate": round(1 - len(invalid) / len(cited), 3) if cited else None,
        "agents_cited": sorted({agent_of_evidence(i) for i in unique if i in index}),
        "attribution_mismatch": attribution_mismatch,
        "single_agent_cross_domain_insights": single_agent_insights,
        "general_knowledge_confidence_downgraded": downgraded,
        "recommendations_without_evidence": [r.action[:80] for r in resp.recommendations
                                             if not r.evidence_ids and r.basis != "general_knowledge"],
    }
    return resp, check

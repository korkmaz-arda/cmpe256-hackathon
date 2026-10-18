"""Render a RunResult as a client-facing markdown report (used by the CLI and the Streamlit app)."""
from __future__ import annotations

from consultai.contracts import agent_of_evidence
from consultai.orchestrator.citations import ID_RE, evidence_index

AGENT_LABEL = {"technology": "Technology", "clinical": "Clinical", "sec": "SEC", "csr": "Corporate Responsibility"}
BADGE = {"confirmed": "✅ confirmed", "inferred": "🟡 inferred", "general_knowledge": "⚪ general knowledge"}


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


def _ids(ids: list[str]) -> str:
    return " ".join(f"[{i}]" for i in ids)


def render_response(result) -> str:
    r = result.response
    idx = evidence_index(result.reports)
    out = [f"## Executive summary\n{r.executive_summary}", f"## Recommendation\n{r.answer}"]
    if r.recommendations:
        rows = ["## Prioritized actions", "| # | Action | Why | Priority | Owner | Basis / confidence | Evidence |",
                "|---|---|---|---|---|---|---|"]
        for n, rec in enumerate(r.recommendations, 1):
            owners = ", ".join(AGENT_LABEL[a] for a in rec.owner_agents)
            rows.append(f"| {n} | {_cell(rec.action)} | {_cell(rec.why)} | {rec.priority} | {owners} | "
                        f"{BADGE[rec.basis]} / {rec.confidence} | {_ids(rec.evidence_ids)} |")
        out.append("\n".join(rows))
    if r.cross_domain_insights:
        out.append("## Cross-domain insights\n" + "\n".join(
            f"- {i.insight} _({' + '.join(AGENT_LABEL[a] for a in i.agents)})_ {_ids(i.evidence_ids)}"
            for i in r.cross_domain_insights))
    if r.conflicts:
        out.append("## Conflicts reconciled\n" + "\n".join(
            f"- **{' vs '.join(AGENT_LABEL[a] for a in c.agents)}**: {c.description} → **Resolution:** {c.resolution} "
            f"_(basis: {c.basis})_" for c in r.conflicts))
    if r.confirmed or r.hypotheses:
        block = ["## What is confirmed vs. hypothesis"]
        block += [f"- ✅ {c.statement} _({AGENT_LABEL[c.agent]})_ {_ids(c.evidence_ids)}" for c in r.confirmed]
        block += [f"- 🟡 {c.statement} _({AGENT_LABEL[c.agent]})_ {_ids(c.evidence_ids)}" for c in r.hypotheses]
        out.append("\n".join(block))
    if r.questions_for_customer:
        out.append("## Information we need from you\n" + "\n".join(f"- {q}" for q in r.questions_for_customer))
    if r.next_steps:
        out.append("## Next steps\n| Step | Owner | When |\n|---|---|---|\n" + "\n".join(
            f"| {_cell(s.step)} | {_cell(s.owner)} | {_cell(s.timeframe)} |" for s in r.next_steps))
    if r.impact_metrics:
        out.append("## How to measure impact\n| KPI | Measurement | Baseline source | Target |\n|---|---|---|---|\n" + "\n".join(
            f"| {_cell(m.kpi)} | {_cell(m.measurement)} | {_cell(m.baseline_source)} | {_cell(m.target)} |"
            for m in r.impact_metrics))
    if r.risks:
        out.append("## Risks\n" + "\n".join(f"- {x}" for x in r.risks))
    if r.limitations:
        out.append("## Limitations\n" + "\n".join(f"- {x}" for x in r.limitations))

    # sources: every id cited anywhere in the response, resolved to agent + document + location
    cited = set(ID_RE.findall(r.answer + " " + r.executive_summary))
    for coll in (r.recommendations, r.cross_domain_insights, r.confirmed, r.hypotheses):
        for item in coll:
            cited.update(item.evidence_ids)
    rows = []
    for i in sorted(cited, key=lambda x: (x.split("-")[0], int(x.split("-")[1]) if x.split("-")[1].isdigit() else 0)):
        e = idx.get(i)
        if not e:
            continue
        link = f"[{e.title}]({e.citation_url})" if e.citation_url else e.title
        rows.append(f"| {i} | {AGENT_LABEL[agent_of_evidence(i)]} | {link} | {e.locator} |")
    if rows:
        out.append("## Sources\n| Id | Agent | Source | Location |\n|---|---|---|---|\n" + "\n".join(rows))
    return "\n\n".join(out)


def render_trace_line(e: dict) -> str:
    d, t, actor = e.get("data") or {}, e["type"], e["actor"]
    tid = f"[{e['task_id']}] " if e.get("task_id") else ""
    if t == "routing_decided":
        parts = [f"{a['agent']}({a['relevance']:.2f}{' ← ' + ','.join(a['depends_on']) if a['depends_on'] else ''})"
                 for a in d.get("assignments", [])]
        return f"ROUTE ({d.get('router')}): {', '.join(parts) or 'no specialist'} | out of scope: {d.get('out_of_scope')}"
    if t == "task_dispatched":
        up = [u["agent"] for u in d.get("upstream", [])]
        return f"DISPATCH {tid}→ {d['agent']}: {d['objective'][:140]}" + (f" (with upstream from {up})" if up else "")
    if t == "tool_called":
        return f"  {tid}{actor} ▸ {d['tool']}({', '.join(f'{k}={v!r}' for k, v in d['args'].items())[:160]})"
    if t == "tool_result":
        if d.get("budget_exhausted"):
            return f"  {tid}{actor} ◂ {d['tool']}: refused (tool budget used up)"
        if d.get("rejected"):
            return f"  {tid}{actor} ◂ submit_report REJECTED: {d['rejected'][:2]}"
        return f"  {tid}{actor} ◂ {d['tool']}: {len(d.get('evidence_ids', []))} evidence {d.get('evidence_ids', [])[:6]}"
    if t == "report_received":
        return (f"REPORT {tid}{actor}: status={d['status']} findings={len(d.get('findings', []))} "
                f"recs={len(d.get('recommendations', []))} cited={len(d.get('evidence', []))} "
                f"tools={d.get('tool_calls')} {d.get('duration_s')}s" + (f" error={d.get('error')}" if d.get("error") else ""))
    if t == "review_decision":
        return f"REVIEW: goal_met={d['goal_met']} conflicts={len(d['conflicts'])} follow_ups={[f['agent'] for f in d['follow_ups']]}"
    if t == "citation_check":
        return f"CITATIONS: {d.get('unique_cited')} unique, valid rate {d.get('valid_rate')}, invalid {d.get('invalid')}"
    if t == "error":
        return f"ERROR {tid}{actor}: {d}"
    if t in ("run_started", "synthesis_started", "synthesis_done", "run_finished", "clarification_requested"):
        return f"{t.upper().replace('_', ' ')}" + (f" {d.get('timings')}" if t == "run_finished" else "")
    return ""

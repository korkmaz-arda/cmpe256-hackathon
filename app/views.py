"""Streamlit rendering of a consulting run: orchestration graph, ledger, per-agent hand-offs, evidence, trace."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from consultai.contracts import EVIDENCE_PREFIX
from consultai.orchestrator.render import AGENT_LABEL, BADGE, render_response, render_trace_line

STATUS_COLOR = {"ok": "#2e7d32", "partial": "#f9a825", "insufficient_evidence": "#ef6c00",
                "out_of_scope": "#757575", "failed": "#c62828"}


def orchestration_graph(run) -> str:
    """DOT graph: request -> router -> specialists (with dependency edges, coloured by status) -> synthesis."""
    lines = ['digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11];',
             'req [label="Customer request", fillcolor="#e3f2fd"];',
             f'router [label="Manager: intent & routing\\n({run.routing.router}, {run.models.get("router")})", fillcolor="#bbdefb"];',
             'req -> router;']
    deps = {p.task_id: p.depends_on for p in run.ledger.task_ledger.plan}
    for rep in run.reports:
        color = STATUS_COLOR.get(rep.status, "#9e9e9e")
        label = (f"{rep.task_id} {AGENT_LABEL[rep.agent]}\\n{rep.status} | {len(rep.findings)} findings | "
                 f"{len(rep.evidence)} cited\\n{rep.tool_calls} tool calls | {rep.duration_s}s")
        lines.append(f'"{rep.task_id}" [label="{label}", fillcolor="white", color="{color}", penwidth=2.5];')
        ups = deps.get(rep.task_id) or []
        if rep.round > 1:
            lines.append(f'review -> "{rep.task_id}" [label="follow-up", style=dashed];')
        elif ups:
            for u in ups:
                lines.append(f'"{u}" -> "{rep.task_id}" [label="upstream findings", color="#6a1b9a"];')
        else:
            lines.append(f'router -> "{rep.task_id}";')
    if run.reviews:
        r = run.reviews[0]
        lines.append(f'review [label="Manager review\\ngoal met: {r.goal_met}\\nconflicts: {len(r.conflicts)}", fillcolor="#fff9c4"];')
        for rep in run.reports:
            if rep.round == 1:
                lines.append(f'"{rep.task_id}" -> review;')
        lines.append("review -> synth;")
    else:
        for rep in run.reports:
            lines.append(f'"{rep.task_id}" -> synth;')
    cc = run.citation_check or {}
    lines.append(f'synth [label="Manager synthesis\\n{cc.get("unique_cited", 0)} citations, valid {cc.get("valid_rate")}", '
                 f'fillcolor="#c8e6c9"];')
    lines.append("}")
    return "\n".join(lines)


def evidence_table(evidence) -> pd.DataFrame:
    return pd.DataFrame([{"id": e.evidence_id, "source": e.title, "location": e.locator, "tool": e.tool,
                          "query": e.query, "scores": ", ".join(f"{k}={v}" for k, v in e.scores.items()),
                          "link": e.citation_url, "snippet": e.snippet[:300]} for e in evidence])


def show_run(run, key: str = "") -> None:
    if run.reports:
        st.graphviz_chart(orchestration_graph(run), width="stretch")
    tabs = st.tabs(["Recommendation", "Routing & ledger", "Agent hand-offs", "Review & citations", "Trace", "Raw JSON"])
    with tabs[0]:
        st.markdown(render_response(run))
    with tabs[1]:
        rd = run.routing
        st.markdown(f"**Router:** `{rd.router}` ({run.models.get('router')}) - **intents:** {', '.join(rd.intents)}")
        if rd.assignments:
            st.dataframe(pd.DataFrame([{"agent": AGENT_LABEL[a.agent], "relevance": a.relevance, "depends on": ", ".join(a.depends_on),
                                        "sub-question": a.sub_question, "rationale": a.rationale} for a in rd.assignments]),
                         width="stretch", hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Task ledger - facts given**\n" + "\n".join(f"- {f}" for f in run.ledger.task_ledger.facts_given))
            st.markdown("**Facts to look up**\n" + "\n".join(f"- {f}" for f in run.ledger.task_ledger.facts_to_look_up))
        with c2:
            st.markdown("**Out of scope**\n" + ("\n".join(f"- {f}" for f in rd.out_of_scope) or "- none"))
            st.markdown("**Clarifying questions**\n" + ("\n".join(f"- {q}" for q in rd.clarifying_questions) or "- none"))
        st.markdown("**Progress ledger**")
        for p in run.ledger.progress:
            st.write(f"Round {p.round}: {p.task_status} | goal met: {p.goal_met} | follow-ups: {p.follow_ups or 'none'}")
    with tabs[2]:
        for task, rep in zip(run.tasks, run.reports):
            color = STATUS_COLOR.get(rep.status, "#9e9e9e")
            with st.expander(f"{task.task_id} · {AGENT_LABEL[task.agent]} · {rep.status} · "
                             f"{len(rep.findings)} findings · {len(rep.evidence)} evidence cited · {rep.duration_s}s"):
                st.markdown(f"<span style='color:{color}'>●</span> **Manager → {AGENT_LABEL[task.agent]} (SpecialistTask)**",
                            unsafe_allow_html=True)
                st.json(task.model_dump(mode="json", exclude={"upstream"}), expanded=False)
                if task.upstream:
                    st.caption(f"Upstream findings attached from: {', '.join(u.agent for u in task.upstream)}")
                st.markdown(f"**{AGENT_LABEL[task.agent]} → Manager (SpecialistReport)**")
                st.markdown(rep.answer_summary)
                if rep.findings:
                    st.dataframe(pd.DataFrame([{"basis": BADGE[f.basis], "confidence": f.confidence, "claim": f.claim,
                                                "evidence": ", ".join(f.evidence_ids), "why this confidence": f.confidence_reason}
                                               for f in rep.findings]), width="stretch", hide_index=True)
                for r in rep.recommendations:
                    st.markdown(f"- **{r.action}** ({r.priority}, {r.confidence}) - {r.rationale} "
                                f"{' '.join('['+i+']' for i in r.evidence_ids)}" + (f"  \n  KPI: {r.kpi}" if r.kpi else ""))
                    if r.ranked_items:
                        st.dataframe(pd.DataFrame([i.model_dump() for i in r.ranked_items]), hide_index=True)
                if rep.missing_information:
                    st.markdown("**Asks the customer:** " + " · ".join(rep.missing_information))
                if rep.error:
                    st.error(rep.error)
                if rep.evidence:
                    st.dataframe(evidence_table(rep.evidence), width="stretch", hide_index=True,
                                 column_config={"link": st.column_config.LinkColumn()})
    with tabs[3]:
        for r in run.reviews:
            st.markdown(f"**Goal met:** {r.goal_met} - {r.rationale}")
            if r.assessments:
                st.dataframe(pd.DataFrame([a.model_dump() for a in r.assessments]), width="stretch", hide_index=True)
            if r.conflicts:
                st.markdown("**Conflicts found**\n" + "\n".join(f"- {', '.join(c.agents)}: {c.description}" for c in r.conflicts))
            if r.follow_ups:
                st.markdown("**Follow-ups issued**\n" + "\n".join(f"- {f.agent}: {f.objective} ({f.reason})" for f in r.follow_ups))
        st.markdown("**Citation check of the final answer**")
        st.json(run.citation_check)
        st.markdown(f"**Timings:** {run.timings}  \n**Usage (API-equivalent, billed to the subscription):** "
                    f"{run.usage.get('totals')}")
    with tabs[4]:
        if run.run_dir:
            from pathlib import Path
            path = Path(run.run_dir) / "trace.jsonl"
            if path.exists():
                events = [json.loads(l) for l in path.read_text().splitlines()]
                st.code("\n".join(f"[{e['t']:7.1f}s] {render_trace_line(e)}" for e in events if render_trace_line(e)),
                        language="text")
                st.caption(f"Full event log: {path}")
    with tabs[5]:
        st.json(run.model_dump(mode="json"), expanded=False)


def agent_prefix(name: str) -> str:
    return EVIDENCE_PREFIX[name]

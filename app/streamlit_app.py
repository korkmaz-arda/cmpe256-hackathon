"""SJSU Management Consulting - multi-agent consulting platform UI.

    streamlit run app/streamlit_app.py

Tabs: Consult (live orchestration) · Run history · Agents & Grounding · Evaluation · Market Basket
"""
from __future__ import annotations

import asyncio
import json
import queue
import sys
import threading
import warnings
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
warnings.filterwarnings("ignore")

from consultai.config import INDEX_DIR, RUNS_DIR, model_profile, profile_names  # noqa: E402
from consultai.eval.common import load_result  # noqa: E402
from consultai.ingest.sources import KNOWN_GAPS, sources_for  # noqa: E402
from consultai.orchestrator.manager import Orchestrator, RunResult, Turn  # noqa: E402
from consultai.orchestrator.render import AGENT_LABEL, render_trace_line  # noqa: E402

import views  # noqa: E402

st.set_page_config(page_title="SJSU Management Consulting", page_icon="🧭", layout="wide")
SCENARIOS = json.loads((ROOT / "consultai" / "eval" / "datasets" / "scenarios.json").read_text())


# ------------------------------------------------------------------------------------------ helpers
def run_live(request: str, profile: str, history: list[Turn]) -> RunResult | None:
    """Run the orchestrator in a worker thread and stream its trace events into the page."""
    events: queue.Queue = queue.Queue()
    box: dict = {}

    def worker() -> None:
        try:
            box["result"] = asyncio.run(Orchestrator(profile=profile).consult(request, history, on_event=events.put))
        except Exception as e:  # surfaced in the UI
            box["error"] = e
        events.put(None)

    threading.Thread(target=worker, daemon=True).start()
    lines: list[str] = []
    with st.status("Engagement Manager is working…", expanded=True) as status:
        log = st.empty()
        while True:
            e = events.get()
            if e is None:
                break
            line = render_trace_line(e)
            if not line:
                continue
            lines.append(f"[{e['t']:6.1f}s] {line}")
            log.code("\n".join(lines[-30:]), language="text")
            if e["type"] == "routing_decided":
                agents = [AGENT_LABEL[a["agent"]] for a in e["data"]["assignments"]]
                status.update(label=f"Routed to: {', '.join(agents) or 'no specialist'} - specialists working…")
            elif e["type"] == "review_decision":
                status.update(label="Manager reviewing the specialists' reports…")
            elif e["type"] == "synthesis_started":
                status.update(label="Manager synthesizing the recommendation…")
        if "error" in box:
            status.update(label="Run failed", state="error")
            st.exception(box["error"])
            return None
        status.update(label=f"Done in {box['result'].timings.get('total_s')}s", state="complete", expanded=False)
    return box["result"]


def list_runs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted([p for p in RUNS_DIR.iterdir() if (p / "run.json").exists()], reverse=True)


# ------------------------------------------------------------------------------------------ layout
st.title("🧭 SJSU Management Consulting · Multi-Agent AI Coworker")
st.caption("Manager agent routes each request to Technology, Clinical, SEC and Corporate Responsibility specialists, "
           "which answer from grounded, cited sources; the manager reviews and synthesizes a consulting recommendation.")

with st.sidebar:
    profile = st.selectbox("Model profile", profile_names(), index=profile_names().index(model_profile().name))
    mp = model_profile(profile)
    st.caption(f"router: **{mp.router}** · specialists: **{mp.specialist}** · review: **{mp.review}** · "
               f"synthesis: **{mp.synthesis}** (Claude via local Claude Code login)")
    if st.button("New engagement (clear conversation)"):
        st.session_state.pop("history", None)
        st.session_state.pop("last_run", None)

tab_consult, tab_runs, tab_agents, tab_eval, tab_basket = st.tabs(
    ["💬 Consult", "🗂️ Run history", "🧑‍💼 Agents & Grounding", "📊 Evaluation", "🛒 Market Basket"])

# ------------------------------------------------------------------------------------------ consult
with tab_consult:
    history: list[Turn] = st.session_state.setdefault("history", [])
    c1, c2 = st.columns([3, 1])
    with c2:
        pick = st.selectbox("Example scenarios", ["(type your own)"] + [f"{s['id']} - {s['kind']}" for s in SCENARIOS])
    default = "" if pick.startswith("(") else next(s["request"] for s in SCENARIOS if pick.startswith(s["id"] + " "))
    with c1:
        request = st.text_area("Customer request", value=default, height=110,
                               placeholder="e.g. Our Cisco enterprise router is experiencing intermittent connectivity failures…")
    if history:
        st.info(f"Follow-up turn {len(history) + 1}: earlier requests and our open questions are passed to the manager.")
    if st.button("Ask the consultants", type="primary", disabled=not request.strip()):
        result = run_live(request.strip(), profile, history)
        if result:
            st.session_state["last_run"] = result
            history.append(Turn(request=request.strip(), executive_summary=result.response.executive_summary,
                                questions_for_customer=result.response.questions_for_customer))
    if "last_run" in st.session_state:
        views.show_run(st.session_state["last_run"])

# ------------------------------------------------------------------------------------------ run history
with tab_runs:
    runs = list_runs()
    if not runs:
        st.info("No saved runs yet.")
    else:
        labels = {}
        for p in runs[:200]:
            meta = json.loads((p / "run.json").read_text())
            agents = ", ".join(AGENT_LABEL[t["agent"]] for t in meta.get("tasks", [])) or "no specialist"
            labels[f"{p.name} · {meta['profile']} · {agents} · {meta['request'][:80]}"] = p
        choice = st.selectbox("Saved runs (runs/<run_id>/run.json + trace.jsonl)", list(labels))
        run = RunResult.model_validate_json((labels[choice] / "run.json").read_text())
        st.markdown(f"**Request:** {run.request}")
        views.show_run(run, key="hist")

# ------------------------------------------------------------------------------------------ agents & grounding
with tab_agents:
    from consultai.agents.registry import specialists
    from consultai.orchestrator.router import router_system_prompt

    st.markdown("Every prompt below is rendered **live from the code**: the grounding list is generated from the "
                "source manifest (`consultai/ingest/sources.py`) and the tool list from the agent's actual tools.")
    pipeline = ("1. **Route & plan** (small model, structured `RoutingDecision`) → 2. **Dispatch** `SpecialistTask`s as a "
                "dependency DAG, independent ones in parallel → 3. Specialists search their own sources and return a "
                "validated `SpecialistReport` via `submit_report` → 4. **Review** (progress ledger, ≤1 follow-up round) → "
                "5. **Synthesis** `ConsultingResponse` → 6. **Citation check** of every evidence id.")
    st.info(pipeline)
    names = ["Manager"] + [a.display_name for a in specialists().values()]
    sel = st.radio("Agent", names, horizontal=True)
    if sel == "Manager":
        md = ROOT / "consultai" / "agents" / "manager"
        st.subheader("Management Consulting Manager Agent - Engagement Manager")
        st.markdown(f"Models: router **{mp.router}**, review **{mp.review}**, synthesis **{mp.synthesis}**.")
        with st.expander("Router prompt (with capability cards generated from the specialist roster)", expanded=True):
            st.markdown(router_system_prompt())
        with st.expander("Review prompt (progress ledger / evaluate-goal loop)"):
            st.markdown((md / "review_prompt.md").read_text())
        with st.expander("Synthesis prompt"):
            st.markdown((md / "synthesis_prompt.md").read_text())
    else:
        agent = next(a for a in specialists().values() if a.display_name == sel)
        st.subheader(f"{agent.display_name} - {agent.persona}")
        st.markdown(agent.capability)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Grounding sources**")
            info = {}
            for col in {s.collection for s in sources_for(agent.name)}:
                p = INDEX_DIR / col / "info.json"
                info[col] = json.loads(p.read_text()) if p.exists() else {}
            st.dataframe(pd.DataFrame([{"source_id": s.source_id, "title": s.title, "collection": s.collection,
                                        "chunks": info.get(s.collection, {}).get("chunks_per_source", {}).get(s.source_id, "-"),
                                        "url": s.citation_url, "provided as": s.origin} for s in sources_for(agent.name)]),
                         width="stretch", hide_index=True, column_config={"url": st.column_config.LinkColumn()})
            st.markdown("**Known gaps**\n" + "\n".join(f"- {g}" for g in KNOWN_GAPS[agent.name]))
        with c2:
            st.markdown("**Tools**")
            for n, d in agent.tool_specs():
                st.markdown(f"- `{n}` - {d}")
        with st.expander("Full system prompt (as sent to Claude)", expanded=True):
            st.markdown(agent.system_prompt())

# ------------------------------------------------------------------------------------------ evaluation
with tab_eval:
    st.markdown("Run `python -m consultai.eval.run_all` to refresh. Results are read from `eval/results/`.")
    for name, title in [("routing", "Routing accuracy"), ("retrieval", "Retrieval accuracy (ablation)"),
                        ("recommendation", "Recommendation relevance"), ("response_quality", "Response quality"),
                        ("basket", "Market-basket recommender")]:
        res = load_result(name)
        st.subheader(title)
        if not res:
            st.caption("not run yet")
            continue
        st.caption(f"generated {res.get('generated_at')}")
        if res.get("summary_md"):
            st.markdown(res["summary_md"])
        if res.get("table_md"):
            st.markdown(res["table_md"])
        with st.expander("details"):
            st.json(res, expanded=False)

# ------------------------------------------------------------------------------------------ market basket
with tab_basket:
    try:
        import basket_view
        basket_view.render()
    except ImportError:
        st.info("Market-basket recommender not built yet.")

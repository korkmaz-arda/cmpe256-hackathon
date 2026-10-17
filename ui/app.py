"""SJSU AI Management Consulting Coworker: Streamlit front end.

Run from the project root:  .venv/bin/streamlit run ui/app.py
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import config  # noqa: E402
from app.agents.render import answer_markdown, source_label, synthesis_markdown  # noqa: E402

st.set_page_config(page_title="SJSU AI Consulting Coworker", page_icon="🧭", layout="wide")

EXAMPLES = {
    "Technology": [
        "Our Cisco enterprise router is experiencing intermittent connectivity failures. Which replacement parts "
        "should we order, and what actions should we take to prevent future outages?",
        "We need a router for 40 branch offices with SD-WAN and redundant power. Which Cisco platform fits best?",
        "How does Google Cloud describe MCP and RAG, and how would they help us build an internal AI assistant?",
    ],
    "Clinical": [
        "Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent "
        "instrument fits and which clinical trials have used it?",
        "Which diagnostic instrument or replacement component best meets our laboratory requirements for "
        "whole-slide imaging in primary diagnosis?",
        "What does the research say about machine learning for predicting heart attacks?",
    ],
    "SEC": [
        "What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet?",
        "How did Cisco's revenue and risk factors change between fiscal 2025 and fiscal 2026?",
    ],
    "Corporate Responsibility": [
        "List major Food insecurity reason in 2023 from within the context of State of Food Security and "
        "Nutrition in the World 2023 report.",
        "Explain malnutrition in war zones from within the context of the State of Food Security and Nutrition in "
        "the World 2023",
        "List major Food insecurity reason in 2024",
        "Explain increase prices impact on food security",
    ],
    "Cross-domain": [
        "We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, "
        "what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024?",
        "Should a diagnostics company invest in Agilent digital pathology, given Agilent's FY2025 10-K and a "
        "hospital lab's needs for primary diagnosis?",
        "Which technology investments could improve food security and sustainability outcomes?",
    ],
}

AGENT_ICONS = {"technology": "💻", "clinical": "🧪", "sec": "📈", "csr": "🌾"}


@st.cache_resource(show_spinner="Loading agents and knowledge bases ...")
def get_manager():
    from app.agents.manager import ManagerAgent
    from app.rag.store import available_domains, get_store

    for domain in available_domains():
        get_store(domain)  # load indexes once
    return ManagerAgent()


def describe_event(event: tuple) -> str:
    kind = event[0]
    if kind == "route":
        d = event[1]
        names = ", ".join(config.DOMAIN_LABELS.get(r, r) for r in d["routes"])
        return f"🧭 **Manager Agent** ({d['model']}) routed to **{names}**: {d['reason']}"
    if kind == "agent_start":
        return f"{AGENT_ICONS.get(event[1], '•')} **{config.DOMAIN_LABELS[event[1]]}** started"
    if kind == "tool":
        args = json.dumps(event[3])[:160]
        return f"&nbsp;&nbsp;&nbsp;🔧 {config.DOMAIN_LABELS[event[1]]} → `{event[2]}` {args}"
    if kind == "agent_done":
        return f"✅ **{config.DOMAIN_LABELS[event[1]]}** finished"
    if kind == "agent_error":
        return f"⚠️ **{config.DOMAIN_LABELS[event[1]]}** failed: {event[2][:200]}"
    if kind == "synthesis_start":
        return "🧩 **Manager Agent** is synthesizing the cross-domain recommendation"
    return str(event)


def run_with_trace(query: str) -> dict:
    """Run the manager in a worker thread and stream its events into a status box."""
    manager = get_manager()
    events: list[tuple] = []
    box: dict = {}

    def worker():
        try:
            box["result"] = manager.run(query, on_event=lambda *e: events.append(e))
        except Exception as exc:  # surfaced in the UI below
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    with st.status("Consulting team at work ...", expanded=True) as status:
        thread.start()
        shown = 0
        while thread.is_alive() or shown < len(events):
            while shown < len(events):
                st.markdown(describe_event(events[shown]))
                shown += 1
            time.sleep(0.25)
        if "error" in box:
            status.update(label="Something went wrong", state="error")
            raise box["error"]
        status.update(label=f"Done in {box['result']['seconds']}s", state="complete", expanded=False)
    box["result"]["events"] = [describe_event(e) for e in events]
    return box["result"]


def render_sources(res: dict) -> None:
    cited = {s for item in res["answer"].get("findings", []) + res["answer"].get("recommendations", [])
             for s in item.get("sources", [])}
    for s in res["sources"]:
        mark = "⭐ " if s["id"] in cited else ""
        with st.expander(f"{mark}{s['id']} · {source_label(s)}"[:220]):
            st.caption(f"{s.get('source') or s.get('kind')}" + (f" · cosine {s['cosine']}" if s.get("cosine") else ""))
            st.write(s.get("text", "")[:1500])


def render_agent(domain: str, res: dict, expanded: bool) -> None:
    g = res["grounding"]
    with st.expander(f"{AGENT_ICONS[domain]} {res['agent']}  ·  {res['seconds']}s  ·  "
                     f"confidence {res['answer']['confidence']['level']}", expanded=expanded):
        st.caption(f"Sub-question from the Manager: {res['question']}")
        cols = st.columns(5)
        cols[0].metric("Sources retrieved", g["sources_retrieved"])
        cols[1].metric("Confirmed / hypotheses", f"{g['confirmed']} / {g['hypotheses']}")
        cols[2].metric("Citation coverage", f"{g['citation_coverage']:.0%}")
        cols[3].metric("Top-3 retrieval cosine", g["top3_retrieval_cosine"] if g["top3_retrieval_cosine"] is not None else "n/a")
        cols[4].metric("Grounding score", f"{g['grounding_score']:.2f}")
        if g.get("invalid_citations"):
            st.warning(f"Cited ids not found in the evidence: {', '.join(g['invalid_citations'])}")
        st.markdown(answer_markdown(res["answer"]))
        t1, t2 = st.tabs(["Evidence (sources)", "Tool calls"])
        with t1:
            render_sources(res)
        with t2:
            st.json(res["tool_calls"])


def consultant_tab() -> None:
    st.subheader("Ask the consulting team")
    left, right = st.columns([2, 1])
    with right:
        group = st.selectbox("Example requests", list(EXAMPLES))
        example = st.radio("Pick one", EXAMPLES[group], label_visibility="collapsed")
        if st.button("Use this example"):
            st.session_state["query"] = example
    with left:
        query = st.text_area("Customer request", key="query", height=140,
                             placeholder="Describe your business problem ...")
        go = st.button("Ask the consulting team", type="primary", disabled=not query.strip())
    if go:
        st.session_state.pop("result", None)  # never leave an old answer under a new request
        st.session_state["result"] = run_with_trace(query.strip())

    result = st.session_state.get("result")
    if not result:
        return
    r = result["route"]
    st.divider()
    st.markdown(f"**Answer for:** {result['query']}")
    if result["query"] != st.session_state.get("query", "").strip():
        st.caption("⚠️ The request box has changed since this answer was produced; press the button to run the new request.")
    cols = st.columns(4)
    cols[0].metric("Routed to", ", ".join(config.DOMAIN_LABELS.get(x, "Out of scope").replace(" Agent", "") for x in r["routes"]))
    cols[1].metric("Cross-domain", "Yes" if r.get("cross_domain") else "No")
    cols[2].metric("Router confidence", f"{r['confidence']:.2f}")
    cols[3].metric("Total time", f"{result['seconds']}s")
    st.caption(f"Router ({r['model']}): {r['reason']}")
    with st.expander("Execution trace"):
        for line in result.get("events", []):
            st.markdown(line)

    if r["routes"] == ["out_of_scope"]:
        st.info("This request is outside our four practice areas (technology, clinical, SEC filings, food security / CSR), "
                "so the Manager did not engage a specialist.")
        return
    for name, err in (result.get("errors") or {}).items():
        st.error(f"{config.DOMAIN_LABELS.get(name, name.title())} failed: {err}")
    if result.get("synthesis"):
        st.subheader("🧩 Consolidated consulting recommendation")
        st.markdown(synthesis_markdown(result["synthesis"]))
        st.caption("Source ids are prefixed by specialist: TECH-, CLIN-, SEC-, CSR-.")
        st.subheader("Specialist reports")
    for domain, res in result["agents"].items():
        render_agent(domain, res, expanded=not result.get("synthesis"))
    st.download_button("Download this answer as JSON", json.dumps(result, indent=2, default=str),
                       file_name="consulting_answer.json")


def agents_tab() -> None:
    from app.rag.store import available_domains, get_store

    st.subheader("Agent personas, instructions and grounding")
    st.write("Each specialist is an LLM with its own persona, instructions (do / don't), tools and a separate "
             "knowledge base. The Manager only routes and synthesizes.")
    names = ["manager"] + config.DOMAINS
    labels = ["Management Consulting Manager Agent"] + [config.DOMAIN_LABELS[d] for d in config.DOMAINS]
    choice = st.radio("Agent", labels, horizontal=True)
    name = names[labels.index(choice)]
    left, right = st.columns([3, 2])
    with left:
        st.markdown((config.PROMPTS / f"{name}.md").read_text())
    with right:
        if name == "manager":
            st.markdown(f"**Model:** `{config.ROUTER_MODEL}` for routing, `{config.AGENT_MODEL}` for synthesis")
            st.markdown("**Pattern:** intent routing → concurrent fan-out to specialists → aggregator")
            return
        st.markdown(f"**Model:** `{config.AGENT_MODEL}`")
        from app.agents.base import DomainAgent

        st.markdown("**Tools:** " + ", ".join(f"`{t['function']['name']}`" for t in DomainAgent(name).tools))
        if name in available_domains():
            stats = get_store(name).stats()
            st.markdown(f"**Knowledge base:** {stats['chunks']:,} chunks")
            st.dataframe(pd.DataFrame([{"document": k, "chunks": v} for k, v in stats["documents"].items()]),
                         hide_index=True, width="stretch")
        if name == "clinical":
            st.markdown("**Structured data:** 32,611 ClinicalTrials.gov studies (COVID-19, diabetes, heart attack, "
                        "knee injuries) searchable with BM25 through `search_trials` and `instrument_usage`.")


def architecture_tab() -> None:
    st.subheader("Multi-agent architecture")
    st.graphviz_chart("""
    digraph G {
      rankdir=TB; node [shape=box, style="rounded,filled", fontname="Helvetica", fillcolor="#eef2ff"];
      user [label="Customer request", fillcolor="#fde68a"];
      router [label="Management Consulting Manager Agent\\n(intent detection + routing, mini model)"];
      tech [label="Technology Agent\\nCisco datasheets · GCP MCP/RAG\\nTools: search_knowledge, recommend_products"];
      clin [label="Clinical Agent\\nIEEE papers · Agilent products · 32k trials\\nTools: search_knowledge, search_trials,\\ninstrument_usage, recommend_products"];
      sec [label="SEC Agent\\n10-Ks: Cisco FY25/26, Agilent FY25,\\nAlphabet FY24/25\\nTool: search_knowledge (company/year filters)"];
      csr [label="Corporate Responsibility Agent\\nFAO SOFI 2023 & 2024\\nTool: search_knowledge (year filter)"];
      synth [label="Manager Agent: synthesis\\n(full reasoning model)"];
      out [label="Consulting recommendation\\nEvidence · confirmed vs hypothesis · next actions · KPIs · confidence", fillcolor="#bbf7d0"];
      user -> router; router -> tech; router -> clin; router -> sec; router -> csr;
      tech -> synth; clin -> synth; sec -> synth; csr -> synth; synth -> out;
    }""", use_container_width=True)
    st.markdown(f"""
- **Model routing:** `{config.ROUTER_MODEL}` classifies intent and writes one sub-question per specialist;
  `{config.AGENT_MODEL}` runs the specialists and the cross-domain synthesis.
- **RAG:** each domain has its own index. PDFs and web pages are chunked page by page (≈1,400 chars, 200 overlap) with
  title / page / URL / company / year metadata, embedded with `{config.EMBED_MODEL}`, and searched with **hybrid
  retrieval** (dense cosine + BM25, fused by reciprocal rank fusion) plus metadata filters.
- **Recommendation:** Cisco and Agilent catalogs built from the datasheets; TF-IDF **similarity matching**, **ranking**,
  and **contextual re-ranking** from the client's constraints. Market basket uses **Apriori** association rules.
- **Explainability:** every claim carries source ids and a confirmed / hypothesis label; each answer reports citation
  coverage, retrieval strength, a grounding score and the agent's own confidence.
""")


def evaluation_tab() -> None:
    st.subheader("Evaluation")
    for name in ("results.md", "basket_results.md"):
        path = ROOT / "eval" / name
        if path.exists():
            st.markdown(path.read_text())
            st.divider()
    if not (ROOT / "eval" / "results.md").exists():
        st.info("Run `.venv/bin/python -m eval.run_eval --all` to produce eval/results.md.")


def basket_tab() -> None:
    from ui.basket_tab import render

    render()


st.title("🧭 SJSU AI Management Consulting Coworker")
st.caption("Multi-agent consulting platform: Technology · Clinical · SEC · Corporate Responsibility · "
           "plus a Market Basket checkout recommender")
tabs = st.tabs(["💬 Consultant", "🤖 Agents & Grounding", "🏗️ Architecture", "🛒 Market Basket", "📊 Evaluation"])
with tabs[0]:
    consultant_tab()
with tabs[1]:
    agents_tab()
with tabs[2]:
    architecture_tab()
with tabs[3]:
    basket_tab()
with tabs[4]:
    evaluation_tab()

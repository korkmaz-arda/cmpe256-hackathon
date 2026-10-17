# Demo video script (target 6:00, hard max 7:00)

The professor asked for: ~1 min intro + architecture, then the demo. About 4 min on the agents (show each agent's
prompt/instructions and grounding, plus a cross-domain query), and about 2 min on the market basket.

**Before recording**
- Start the app: `.venv/bin/streamlit run ui/app.py`, browser at http://localhost:8501, window ~1400px wide.
- Each answer takes 20–60 s. Either cut or speed up the waiting in editing, or pre-run a query and keep it on screen.
  The *Execution trace* expander still shows the routing and tool calls afterwards.
- Zoom the browser to ~110% so the text is readable in the video.

| Time | Screen | What to say |
|---|---|---|
| 0:00–0:20 | App title | "We built an AI management consulting coworker: a Manager Agent routes each customer request to four grounded specialist agents and turns their evidence into a consulting recommendation." |
| 0:20–1:00 | **Architecture** tab | Walk the diagram. Mention: mini model (gpt-5.4-mini) for intent routing, full model (gpt-5.5) for specialists and synthesis; concurrent fan-out; hybrid RAG (dense + BM25, reciprocal rank fusion) with page-level citations; recommenders (TF-IDF similarity, ranking, contextual re-ranking; Apriori for the basket). |
| 1:00–1:45 | **Agents & Grounding** tab | Click through Manager → Technology → Clinical → SEC → CSR. For one agent, scroll the persona, domain expertise, grounding sources, instructions and **Do / Don't**. Point at the knowledge-base table (documents + chunk counts) and the tools list. "This is how each agent is grounded: its own knowledge base, its own tools, and explicit rules such as never presenting a hypothesis as a confirmed fault." |
| 1:45–2:45 | **Consultant** → Technology example 1 (Cisco router intermittent failures) | Show the routing line and router confidence. Scroll the answer: "It doesn't assume a part failed. Confirmed facts are cited to datasheet pages, causes are labelled hypotheses, and it asks for diagnostics (show logging, show environment, interface counters) before ordering parts." Open one source in *Evidence* to show the page text. Point at the grounding metrics (citation coverage, grounding score). |
| 2:45–3:15 | **Consultant** → Corporate Responsibility example 1 (SOFI 2023 reasons) | "The CSR agent filters to the 2023 report only, so figures don't mix years." Show citations with page numbers. *(Optional swap: the Clinical Seahorse example, which shows trial evidence with NCT ids.)* |
| 3:15–4:30 | **Consultant** → Cross-domain example 1 (cold-chain routers + Cisco 10-K + SOFI 2024) | Show the route: Technology + SEC + Corporate Responsibility running in parallel (execution trace). Read the executive summary, one integrated recommendation with TECH-/SEC-/CSR- citations, the *How the domains connect* list, and the KPIs. Expand one specialist report. |
| 4:30–5:00 | **Evaluation** tab | Read the headline numbers: routing accuracy, retrieval Hit@5 / MRR, recommendation NDCG@3, response-quality judge scores. "Every answer is also measured live: citation coverage and a grounding score." |
| 5:00–6:00 | **Market Basket** tab | Click **Demo 1** (Bosch D7050): ranked recommendations with confidence, lift and support from Apriori. Click **Demo 2** (+ DSC PG9914): "These two were bought together only 5 times and nothing else repeats with them, so we show no recommendation instead of an irrelevant one, as you specified." Then add a normal item with **Add Item** to show the list updating. Mention the thresholds expander and the offline HitRate@k validation. |
| 6:00 | Close | "Thanks. Code is in the Canvas zip; the README maps each Section 5 deliverable to the code." |

**Backup prompts** (if a live run misbehaves)
- "We need a router for 40 branch offices with SD-WAN and redundant power. Which Cisco platform fits best?"
- "What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet?"
- "Explain increase prices impact on food security"
- Saved transcripts of every demo prompt are in `eval/transcripts/` and can be shown instead.

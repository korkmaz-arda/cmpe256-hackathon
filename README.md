# CMPE 256 Hackathon: Agentic AI Management Consulting Platform

**SJSU AI Management Consulting Coworker.** A **Management Consulting Manager Agent** detects the intent of a
customer request, routes it to one or more grounded **specialist agents** (Technology, Clinical, SEC, Corporate
Responsibility), and consolidates their cited findings into a consulting recommendation: what to do next, why, and how
to measure the impact. The app also includes the optional **Market Basket** checkout recommender (Apriori).

See [RUBRIC.md](RUBRIC.md) for the requirements confirmed with the professor.

```
Customer request
      │
      ▼
Management Consulting Manager Agent ── intent detection + routing (gpt-5.4-mini)
      │  one focused sub-question per specialist, run concurrently
      ├──► Technology Agent ─────────── Cisco datasheets + product pages, Google Cloud MCP/RAG pages
      ├──► Clinical Agent ───────────── IEEE papers, Agilent products, 32,611 ClinicalTrials.gov studies
      ├──► SEC Agent ────────────────── 10-Ks: Cisco FY2025/FY2026, Agilent FY2025, Alphabet FY2024/FY2025
      └──► Corporate Responsibility ─── FAO SOFI 2023 + 2024
      │
      ▼
Manager synthesis (gpt-5.5) ── consulting recommendation: evidence, confirmed vs hypothesis,
                               next actions, KPIs, confidence
```

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-..." > .env            # never committed
# unzip the Canvas data into data/ (see "Data setup" below), then:
.venv/bin/python -m app.rag.fetch_web            # download the Cisco / Google web sources
.venv/bin/python -m app.rag.ingest               # build the 4 knowledge bases (about 2 min)
.venv/bin/streamlit run ui/app.py                # open http://localhost:8501
```

CLI: `.venv/bin/python -m app.agents.manager "your question"` prints the full answer as Markdown.

- Demo video plan: [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)
- Canvas zip of all tracked source: `./scripts/make_submission.sh`
- Tests: `.venv/bin/python -m tests.test_basket`, `.venv/bin/python tests/test_trials.py`, `.venv/bin/python tests/test_product_recommender.py`

## How each Section 5 deliverable is met

### 1. Multi-agent orchestration
- `app/agents/manager.py`: the **Manager Agent** uses a small, fast model (`gpt-5.4-mini`) with a strict JSON schema
  to classify the request into `technology | clinical | sec | csr | out_of_scope` (one or more), and to write one
  focused sub-question per specialist that keeps the client's constraints.
- Specialists run **concurrently** (fan-out). For cross-domain requests the Manager **synthesizes** their reports with
  the full model (`gpt-5.5`). Out-of-scope requests are declined without calling a specialist.
- This follows the professor's suggestion: a mini model for routing and a full model for the domain work.
- The UI shows the live **execution trace**: route decision, router confidence, every tool call and timing.

### 2. Domain knowledge grounding
Each agent has its own **persona, domain expertise, grounding sources, instructions, and do/don't rules** in
`app/agents/prompts/*.md`. They're also shown in the UI's *Agents & Grounding* tab.

| Agent | Knowledge base | Tools |
|---|---|---|
| Technology | 5 Cisco datasheets + 5 product pages, 3 Google Cloud pages (MCP, RAG): 305 chunks | `search_knowledge`, `recommend_products(cisco)` |
| Clinical | 20 IEEE papers, Agilent product facts: 672 chunks; 32,611 trials (CSV) | `search_knowledge`, `search_trials`, `instrument_usage`, `recommend_products(agilent)` |
| SEC | 5 Form 10-K filings (Cisco, Agilent, Alphabet): 3,049 chunks | `search_knowledge` with company/year filters |
| Corporate Responsibility | FAO SOFI 2023 and 2024: 2,041 chunks | `search_knowledge` with year filter |

Both kinds of supplied source are used: the **.zip** files (local PDFs/CSVs) and the **.txt** link lists (downloaded
by `app/rag/fetch_web.py`).

### 3. Retrieval-augmented generation (RAG) with citations
- `app/rag/ingest.py`: page-level PDF extraction, ~1,400-character chunks with 200 overlap. Each chunk carries
  **title, page, URL/path, company, fiscal year, topic** metadata. Chunks are embedded with `text-embedding-3-small`.
- `app/rag/store.py`: **hybrid retrieval**. Dense cosine and BM25 are fused with reciprocal rank fusion, plus
  metadata filters (for example, SOFI *2023 only*, or *Cisco FY2026*).
- Agents call retrieval as a tool, so they can search several times with different queries and filters.
- Every finding and recommendation carries **source ids** (S1, S2, …). The UI and the Markdown output resolve each id
  to the document, page and URL.

### 4. Intelligent recommendation system
- **Similarity matching + ranking + contextual recommendation**: `app/tools/product_recommender.py` scores
  the Cisco router catalog and Agilent instrument catalog (`app/catalog/*.json`, built from the datasheets with page
  references). It uses TF-IDF cosine similarity, ranks the top-k with a score breakdown, then re-ranks by the client's
  context (deployment, redundancy, throughput, budget, regulatory/IVD).
- **Evidence-based instrument recommendation**: `instrument_usage` finds the trials that actually use an instrument.
  For example, the Seahorse XF analyzer is used in 11 trials, mostly diabetes.
- **Market basket** (`app/basket/apriori.py`): Apriori built from scratch, recommending only from the **whole
  cart**. If the cart's combination has no frequent pattern, it shows nothing, as the professor specified.

### 5. Cross-domain reasoning
Requests that span domains are split into sub-questions, answered in parallel, and merged. The synthesis lists
**how the domains connect**, **conflicts and gaps**, integrated recommendations with prefixed citations
(TECH-S3, SEC-S2, CSR-S5…), next steps and KPIs. Try the *Cross-domain* examples in the UI.

### 6. Explainability and evaluation
- Every answer has: **findings tagged confirmed vs hypothesis**, cited evidence, **missing information** requested
  from the client, risks and assumptions, and the agent's **confidence (high/medium/low + reason)**.
- Each answer also gets a measured **grounding report**: citation coverage, invalid citations, top-3 retrieval cosine,
  and a grounding score.
- `eval/run_eval.py` measures **routing accuracy**, **retrieval Hit@k / MRR**, **recommendation Precision/NDCG@3**
  (and market-basket HitRate@k), and **response quality** (LLM-as-judge faithfulness, relevance and actionability).
  Results are in [eval/results.md](eval/results.md), with full answer transcripts in `eval/transcripts/`.

### 7. Business value
Every specialist answer ends with **prioritised recommendations + why**, **next steps**, and **KPIs to measure
impact**. For example, MTTR and link-flap rate for router outages, or prevalence of undernourishment and food-loss
percentage for food-security investments. The Technology agent never assumes which part failed: it separates
hypotheses from confirmed facts and asks for the diagnostics it needs before recommending replacement parts.

## Market Basket recommender (optional part)

`ui/basket_tab.py` (also the *Market Basket* tab of the app). Pick an item from the full product list → *Add Item*
→ the cart updates → recommended items appear below, with confidence, lift, support and the rule used.
- Recommendations come only from rules whose antecedent is the **entire cart**. There's no fallback to partial carts
  or popularity.
- Default thresholds are min support count 2, min confidence 0.05 and lift > 1. The data is sparse: the most common
  pair appears in 16 of 1,000 baskets, and the maximum pair lift is 2.25. Class-style thresholds (confidence 0.2,
  lift 3) would leave almost every cart without a recommendation.
- Offline validation (`.venv/bin/python -m app.basket.evaluate`) reports leave-one-out HitRate@k and coverage against
  a popularity baseline, plus a threshold sweep: [eval/basket_results.md](eval/basket_results.md).

## Data setup

The course data isn't committed (this repo is public). Unzip the Canvas zips into `data/`:

```
data/Clinical/        <- Clinical.zip
data/SEC/             <- UnitedStatesSecuritiesandExchangeCommission(SEC).zip (rename the folder to SEC)
data/FoodSecurity/    <- FoodSecurity.zip
data/Retail/          <- Retail.zip
```

The web sources (Cisco datasheets, Agilent pages, GCP pages) are listed in `sources/*.txt` and downloaded to
`data/web/` by `app/rag/fetch_web.py`.

## Assumptions and limitations
- **IBM**: no IBM data was supplied, so the Technology agent covers Cisco and Google Cloud only.
- **Agilent**: agilent.com returns HTTP 403 to automated downloads. The Agilent product facts were transcribed from
  the supplied pages into `app/catalog/agilent_products.json` (with source URLs) and ingested from there. The Clinical
  agent also uses the trials that name Agilent instruments.
- **Market basket data** has weak associations (near-uniform item popularity), so hit rates are low by nature. The
  value is in the "no pattern → no recommendation" behaviour and the transparent rules.
- Models are configurable in `.env` (`ROUTER_MODEL`, `AGENT_MODEL`, `EMBED_MODEL`).

## Repository layout

```
app/
  config.py            paths, models, domain sources
  llm.py               OpenAI chat (tools + JSON schema) and embeddings
  rag/                 fetch_web.py, ingest.py, store.py (hybrid retrieval)
  agents/              manager.py, base.py (domain agent), render.py, prompts/*.md
  tools/               product_recommender.py, trials.py
  catalog/             Cisco + Agilent catalogs built from the datasheets
  basket/              apriori.py, evaluate.py
ui/                    app.py (Streamlit), basket_tab.py
eval/                  gold sets, run_eval.py, results.md, transcripts/
tests/                 unit tests for the recommenders and the trials tool
```

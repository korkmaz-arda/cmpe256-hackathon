# SJSU Management Consulting: a multi-agent AI consulting coworker

CMPE 256 (Recommender Systems) hackathon prototype. A **Management Consulting Manager Agent** detects the intent of a
customer request, decides which specialists it needs (as many as the request genuinely spans), delegates precise
tasks to them, reviews their grounded and cited findings, and synthesizes a consulting recommendation. The
recommendation says what to do next, why it fits, and how to measure the impact.

| Agent | Persona | Grounded on (course-provided only) |
|---|---|---|
| **Manager** | Engagement Manager | Routes, plans, reviews, synthesizes; no documents of its own |
| **Technology** | Principal Network & Cloud Solutions Architect | 5 Cisco router data sheets + product pages, 3 Google Cloud pages (MCP, RAG); verified Cisco parts catalog |
| **Clinical** | Clinical & Life-Science Solutions Consultant | 6 Agilent pages, 20 IEEE papers, 32,392 ClinicalTrials.gov studies |
| **SEC** | Equity Research & Regulatory-Risk Analyst | Form 10-Ks: Agilent FY2025, Alphabet FY2024/25, Cisco FY2025/26 |
| **Corporate Responsibility** | Sustainability & Food-Systems Strategy Advisor | FAO SOFI 2023 and SOFI 2024 |

No IBM material was provided, so the platform says so instead of answering from memory. Each agent's full prompt,
sources, gaps and tools: **[docs/AGENTS.md](docs/AGENTS.md)**, which is generated from the code. Design:
**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Quick start

```bash
conda activate cmpe256                      # Python 3.11
pip install -r requirements.txt
claude --version                            # Claude Code must be installed and logged in (subscription; no API key)

python scripts/setup_data.py                # unzip course data into the data root (git-ignored) + verify
python -m consultai.ingest.build            # build the 6 retrieval indexes (~4 min on GPU, first run downloads bge models)
python scripts/extract_catalogs.py          # Cisco parts + Agilent product catalogs (Claude, then verbatim check)

streamlit run app/streamlit_app.py          # UI
python scripts/consult.py --scenario router_outage --trace          # CLI with live orchestration trace
python -m pytest -q tests                   # offline tests (no Claude calls)
python -m consultai.eval.run_all --profile dev                      # all evaluations -> eval/results/
```

**Data locations.** Course material is not in this public repository. Put the course resources folder (the Canvas zips
under `data/`, the link lists under `documents/`, the saved web pages under `web/{cisco,gcp,agilent}`) at
`resources/` in the clone, or point `CONSULTAI_RESOURCES` at it. Unzipped data and indexes go to `data/`, or to
`CONSULTAI_DATA_ROOT`. Both folders are git-ignored. (In the original hackathon workspace the defaults are the sibling
folders `hackathon/resources` and `hackathon/workdata`.)

**Models** (one file, `config/models.yaml`). All calls run through the local Claude Code login via
`claude-agent-sdk`; the code refuses to run if `ANTHROPIC_API_KEY` is set.

| Profile | Router | Specialists | Review + synthesis | Use |
|---|---|---|---|---|
| `demo` (default) | Haiku | **Opus** | Opus | graded / demo runs |
| `dev` | Haiku | Sonnet | Opus | development and bulk evaluation |
| `smoke` | Haiku | Haiku | Haiku | plumbing checks only |

Embeddings are local: `BAAI/bge-base-en-v1.5` for retrieval and `BAAI/bge-reranker-base` for reranking.

## How one request flows

1. **Route & plan.** Haiku fills a `RoutingDecision`: intents, the specialists needed, a self-contained
   sub-question for each, extracted entities, dependencies, out-of-scope parts and clarifying questions. Code then
   enforces the contract (threshold τ = 0.5, valid and acyclic dependencies). An embedding kNN router is the fallback.
2. **Dispatch.** One `SpecialistTask` per specialist, run as a DAG: independent tasks run in parallel, and a
   dependent task (e.g. Technology after CSR in "which technology would address food insecurity") starts when its
   upstream finishes and receives the upstream findings and evidence in structured form.
3. **Specialist work.** Each specialist is a Claude session that can only use its own retrieval and recommender
   tools. Every tool result becomes an `Evidence` record with an id such as `SEC-4`. The specialist returns a
   `SpecialistReport` through `submit_report`, which rejects unknown citations, unsupported "confirmed" claims and
   high-confidence general knowledge.
4. **Review.** This is the manager's progress ledger (slide 3's evaluate-goal loop): is the goal met, what are the
   gaps and cross-agent conflicts? If needed, at most one follow-up round goes out (it may include a specialist the
   router skipped).
5. **Synthesis.** A `ConsultingResponse` with prioritized actions, cross-domain insights, reconciled conflicts,
   confirmed vs hypotheses, questions for the customer, next steps, impact KPIs, risks and limitations.
6. **Citation check.** Every evidence id in the answer is resolved against the specialists' evidence;
   unresolvable ids are stripped and reported.

Every step is traced to `runs/<run_id>/trace.jsonl` and `run.json`, and shown live in the UI (orchestration graph,
hand-offs, tool calls, evidence and scores).

## How the brief's Section 5 capabilities are met

| Capability | Implementation | Evidence |
|---|---|---|
| Multi-agent orchestration | Router → DAG scheduler → review loop → synthesis (`consultai/orchestrator/`) | Routing eval; trace of every run |
| Domain knowledge grounding | Per-agent source manifest, indexes and tools; web/file tools disabled; gaps declared | `tests/test_grounding.py`, `docs/AGENTS.md` |
| RAG with citations | Hybrid BM25 + dense + rerank; evidence ids minted by tools; links with `#page=` | Retrieval ablation; citation check per run |
| Intelligent recommendation | Cisco platform recommender (constraints + requirement fit + similarity + right-sizing + lifecycle), Agilent product recommender (regulatory filter + similarity + application match), trial ranking, market-basket Apriori | Recommendation and basket evals |
| Cross-domain reasoning | Multi-assignment routing, dependencies with upstream findings, review conflicts, ≥2-agent insights | `food_tech_investment`, `all_four` scenarios |
| Explainability & evaluation | Basis + confidence + reason per claim, retrieval scores, full trace; 5 evaluations | `eval/results/*.json`, Evaluation tab |
| Business value | Next steps (owner, timeframe), why, impact metrics (KPI, measurement, baseline source, target) | Every `ConsultingResponse` |

## Evaluation results (`python -m consultai.eval.run_all`)

**Retrieval accuracy** (59 queries; gold labels checkable by phrase-on-page, gold document or SQL predicate; k = 10):

| Mode | hit@1 | hit@5 | MRR | nDCG@10 |
|---|---|---|---|---|
| BM25 | 0.695 | 0.864 | 0.767 | 0.665 |
| Dense (bge) | 0.695 | 0.898 | 0.779 | 0.680 |
| Hybrid (RRF) | 0.763 | 0.915 | 0.821 | 0.700 |
| **Hybrid + rerank (used)** | **0.797** | **0.966** | **0.871** | **0.761** |

The weakest collection is SOFI (nDCG@10 0.55): facts recur across many pages of 600-page reports.

**Routing accuracy** (50 hand-labelled requests: single-domain, 2/3/4-domain and out-of-scope):

| Router | Exact agent set | Micro F1 | Over-routing | Under-routing | Out-of-scope |
|---|---|---|---|---|---|
| LLM router (Haiku, τ = 0.5) | 1.00 | 1.00 | 0.00 | 0.00 | 1.00 |
| kNN embedding baseline | 0.68 | 0.81 | 0.02 | 0.30 | 1.00 |

τ in 0.3–0.5 is a plateau; recall drops above 0.6. We wrote this set ourselves, and its requests are
clearer than real traffic, so treat 50/50 as an upper bound.

**Recommendation relevance** (hand-graded scenarios; ablation vs similarity-only ranking):

| Recommender | Variant | hit@1 | P@3 | nDCG@3 |
|---|---|---|---|---|
| Cisco platforms (6) | full | 1.00 | 0.72 | 0.80 |
| Cisco platforms (6) | similarity only | 0.50 | 0.22 | 0.35 |
| Agilent products (3) | full | 1.00 | 0.78 | 0.84 |
| Agilent products (3) | similarity only | 0.67 | 0.67 | 0.66 |

The right-sizing term was added after this evaluation showed oversized picks for a small branch (nDCG@3 was 0.66
before). The scenario set is small, so these numbers indicate direction, not precision.

**Response quality.** End-to-end runs of the 12 scenarios in `consultai/eval/datasets/scenarios.json`. Deterministic
checks plus an LLM judge of claim faithfulness and rubric scores (`python -m consultai.eval.response_quality`).
The full table is in `eval/results/response_quality.json` and the Evaluation tab. First two scenarios: citation
valid rate 1.00, judge faithfulness 0.94 (`food_tech_investment`, three agents) and 0.81 (`router_outage`).

**Market basket.** See below.

## Market-basket recommender (optional task)

`consultai/basket/apriori.py` is our own level-wise Apriori (join + prune). For the **whole current cart** C it
recommends items x from frequent itemsets C ∪ {x}, ranked by confidence and then lift (lift > 1 required). If the
exact cart combination is not frequent, or no rule clears the thresholds, **nothing is shown**. There is no
fallback to subsets of the cart, per the professor's clarification.

Thresholds come from an 80/20 hold-out replay of checkouts: min support = 6 transactions, min confidence = 0.10.
That is the most conservative setting within 5% of the best harmonic mean of precision@3 and hit-rate@3.

**Honest finding:** this dataset has very little co-purchase structure. Precision@3 is 0.060 against 0.052 for a
popularity baseline, and hit-rate@3 is 0.067 against 0.151 (the baseline always shows 3 items; ours shows
recommendations at 38% of checkout steps). The recommender's value here is restraint: it stays silent rather than
showing weak suggestions.

Demo in the **Market Basket** tab:
- DSC WS4939 Wireless Key → Dahua DH-IPC-HDBW4431R-ZS camera (confidence 0.16, lift 1.62);
- the slide's own cart, Bosch D7050 + DSC PG9914, appears together in fewer than 6 transactions → no recommendation.

## Demo walkthrough (for recording)

1. **Agents & Grounding tab:** the Manager's router prompt with its capability cards, then one specialist's
   persona, sources, gaps, tools and full prompt.
2. **Consult tab:** run `router_outage` (brief section 4). Show routing to Technology only, the live tool calls,
   confirmed facts vs hypotheses, the questions for diagnostics, and the ISR 4000 end-of-sale flag.
3. **Consult tab:** run `food_tech_investment`. Show CSR and SEC running in parallel, Technology waiting for CSR,
   the review triggering an SEC follow-up, cross-domain insights and reconciled conflicts, and the Sources table.
   (Or open a saved run in **Run history** to skip the wait.)
4. **Evaluation tab:** the routing, retrieval, recommendation and response-quality tables.
5. **Market Basket tab:** one cart that gets recommendations and one that blanks out.

## Limitations

- Only course-provided sources are used. Pricing, lead times, troubleshooting guides, Agilent manuals, company
  ESG reports, stock prices and IBM are not covered, and agents say so.
- Claim support is enforced structurally (evidence ids must exist) and measured by an LLM judge; it is not
  guaranteed. The judge is also a Claude model, so self-preference bias is possible.
- Catalog verification checks that each value string is on the cited page, not that it sits in the right table column.
- End-to-end runs take about 2–5 minutes, with more specialists, Opus specialists and a follow-up round adding time.
- The evaluation sets are small and were written by the team.

## Repository layout

```
consultai/
  contracts.py            inter-agent protocol (Pydantic)
  config.py               paths, model profiles, settings
  llm/claude_runner.py    the only Claude access point (claude-agent-sdk, locked down)
  agents/                 base.py, registry.py, common_policy.md, manager/*.md, <agent>/{prompt.md, agent.py, catalog}
  orchestrator/           manager.py, router.py, scheduler.py, ledger.py, citations.py, trace.py, render.py
  ingest/                 sources.py (manifest), extract.py, build.py, trials.py
  retrieval/              chunking.py, models.py, store.py
  basket/apriori.py
  eval/                   datasets/, retrieval.py, routing.py, recommendation.py, response_quality.py, basket.py, run_all.py
app/                      streamlit_app.py, views.py, basket_view.py
scripts/                  setup_data.py, consult.py, extract_catalogs.py, gen_agent_cards.py
config/                   models.yaml, settings.yaml
docs/                     ARCHITECTURE.md, AGENTS.md (generated)
tests/                    offline tests
```

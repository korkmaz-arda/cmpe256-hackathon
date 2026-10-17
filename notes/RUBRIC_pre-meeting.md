# CMPE 256 Hackathon (Oct 17, 2026): Inferred Rubric + Meeting Prep

Built from: the pasted brief ("From Student to Entrepreneur…"), the 11-slide deck `sources/SJSU_CMPE256_Hackathon_20261017_v7_Release.pdf`, and every file in `data/` and `sources/`.

No official rubric exists. The weights below are **my estimate**. The criteria aren't guesses, though: each row comes straight from wording in the brief or the deck.

---

## TL;DR for the 1:30 meeting

1. **The brief's Section 5 ("Expected Deliverables") is almost certainly the grading rubric.** It has 7 named capabilities written as checkable claims. If an AI grader is involved, it's checking your submission against those 7 bullets, more or less word for word.
2. **The deck has a second project that the brief never mentions.** Slides 6–11 (6 of the 11) cover a **Market Basket checkout recommender** (Retail.zip, FastAPI, web portal). Ask whether it's required and how much it counts.
3. **The deck is recycled.** Slide 11's footer still says *"November 01 – 02, 2025"*. The retail and clinical files are dated 11/01/2025 and the SOFI PDFs 11/04/2024. Last year's hackathon was probably the Food-Security RAG plus the Market Basket recommender, and this year's multi-agent "consulting" layer was added on top. That's why it reads like the professor's own project.
4. **The data doesn't fully match the brief.** IBM has no data at all. The "Agilent manuals" the Clinical Agent supposedly uses don't exist in the bundle, though 13 clinical trials do use Agilent instruments (mostly Seahorse XF). The SEC box says "Cisco and Agilent 2025", but the folder also has Cisco FY2026 and two Alphabet 10-Ks. These are your meeting questions.
5. **The one row an automated grader can check most easily is Evaluation.** The brief names four metrics: retrieval accuracy, routing accuracy, recommendation relevance and response quality. Report a number for each.

---

## 1. What's actually in the materials

| Domain (per brief) | What was supplied | Notes / gaps |
|---|---|---|
| **Technology:** Cisco, IBM, Google | `DataSource-Cisco.txt`: 5 router product pages plus 5 datasheet PDF **URLs** (Catalyst 8300, 8200, 8000V, ISR 4000, ASR 1000). `Google GCP.txt`: 3 URLs on GCP **MCP** and **RAG** | Cisco datasheets have to be downloaded. **No IBM source at all.** The Google links are concept pages, not product specs, which hints that MCP and RAG are expected. |
| **Clinical:** Agilent plus clinical PDFs | `Clinical.zip`: 20 IEEE papers (5 each on COVID, Diabetes, Heart attack, Knee injuries) plus 4 **ClinicalTrials.gov exports** (32,611 studies: diabetes 22,860, COVID 4,773, heart attack 3,713, knee 1,265). `Agilent.txt`: 4 product web pages (Seahorse metabolic analysis, Digital Pathology, NanoZoomer IVD scanner, Artisan Link Pro special stains) | **No Agilent equipment manuals.** But the trial CSVs *do* link to Agilent: **13 trials** use Agilent instruments in their outcome measures. 11 use the **Seahorse XF analyzer** (1 heart attack, 1 COVID, 9 diabetes) to measure mitochondrial respiration, and 2 diabetes trials use an Agilent GC or LC-MS. Seahorse is the first link in `Agilent.txt`, so this looks deliberate. A good Clinical demo: "we need to measure mitochondrial function in a diabetes trial" → recommend Seahorse XF, with similar trials as evidence. The 20 IEEE papers never mention Agilent. |
| **SEC:** "Cisco and Agilent 2025" | `SEC.zip`: Agilent 10-K FY2025 (217 pp). Cisco 10-K FY2025 (123 pp) and **FY2026** (285 pp). **Alphabet** 10-K FY2024 (108 pp) and FY2025 (104 pp) | The SEC box lists only "Cisco SEC 2025" and "Agilent SEC 2025". Google *is* in the Technology box, but its only sources there are GCP concept pages, so it's unclear whether Alphabet is in scope for the SEC agent. Cisco has a FY2026 10-K as well as the "2025" one. Two years each of Cisco and Alphabet make year-over-year comparison possible, which is easy extra credit. |
| **Corporate Responsibility:** Food Security | `FoodSecurity.zip`: FAO SOFI 2023 (316 pp, urbanization theme) and SOFI 2024 (286 pp, financing theme) | Slide 4 lists the exact test prompts (see §3). |
| *(not in brief)* **Retail / Market Basket** | `Retail.zip`: 1,000 transactions, 40 security-hardware SKUs (Bosch, Honeywell, GE, DSC, Hikvision, Axis, Dahua, Hanwha, Pelco), 2–5 items per basket | Covered only in slides 6–11. Details in §2-B. |

---

## 2. Inferred rubric (100 pts)

| # | Criterion | Est. pts | Source |
|---|---|---|---|
| A1 | Multi-agent orchestration & routing | 12 | Brief §5, slide 3 |
| A2 | Domain knowledge grounding | 8 | Brief §5 |
| A3 | RAG with citations | 12 | Brief §5, slides 4–5 |
| A4 | Recommendation techniques (similarity, ranking, context) | 10 | Brief §5 (it's a *Recommender Systems* course, so this could be weighted higher) |
| A5 | Cross-domain reasoning | 8 | Brief §5 |
| A6 | Explainability & evaluation (4 metrics + confidence) | 15 | Brief §5 |
| A7 | Business value (what next / why / how measured) | 10 | Brief §4–5 |
| B | Market Basket checkout recommender | 15 | Slides 6–11 (**confirm it's required**) |
| C | Working demo, engineering, presentation | 10 | Implied ("working prototype") |

### A1. Multi-agent orchestration & routing
- **Spec wording:** the Manager Agent "classifies customer requests and routes them to the appropriate specialized agent."
- **Full marks looks like:**
  - A real intent classifier (LLM function-calling, or an embedding/zero-shot classifier) with labels `technology | clinical | sec | csr | (retail) | multi | out_of_scope`.
  - Every response shows a **route trace**: which agent or agents ran, and why.
  - An orchestrator between the agents. Slide 5 says "RabbitMQ or REST", so REST is fine.
  - Use the vocabulary of the Azure agent-orchestration patterns that slide 3 links to: *handoff/routing* for single-domain questions and *concurrent* fan-out plus an aggregator for cross-domain questions. Say which pattern you used.
- **How you lose points:** one giant prompt role-playing four agents, no visible routing, no handling of ambiguous or out-of-scope requests.

### A2. Domain knowledge grounding
- **Spec wording:** knowledge bases built from "authoritative technical PDFs, SEC filings, and corporate responsibility documents."
- **Full marks looks like:**
  - One index (or one namespace) per domain, with metadata on every chunk: document, page, company, fiscal year, domain.
  - A table listing every source ingested, with page and chunk counts.
- **How you lose points:** a single blended index that can't cite pages, or skipping the Cisco datasheets because they weren't in a zip.

### A3. RAG with citations
- **Spec wording:** "Retrieve relevant evidence and provide source-grounded recommendations with citations."
- **Full marks looks like:**
  - Chunk → embed → retrieve → generate. Hybrid BM25+dense retrieval or a reranker earns bonus points.
  - **Every claim cites doc + page.**
  - The system says what evidence is missing instead of filling the gap.
  - The SOFI prompts are scoped by year ("within the context of … 2023"), so the 2023 prompts must not pull 2024 content. Filter by metadata.
- **How you lose points:** uncited claims, mixing up years or companies, made-up part numbers.

### A4. Recommendation techniques
- **Spec wording:** "similarity matching, ranking, and contextual recommendation" to pick "products, components, or business actions."
- **Full marks looks like:** all three, **named and implemented separately**:
  1. **Similarity:** embedding or TF-IDF cosine similarity between the customer's requirements and product specs (for example, Cisco 8200, 8300, 8000V, ISR 4000 and ASR 1000 on throughput, interfaces and cloud vs. on-prem; Agilent instruments for lab needs).
  2. **Ranking:** a top-k list with visible scores.
  3. **Contextual re-ranking:** adjusts by the customer's constraints (budget, scale, deployment, redundancy).
- **How you lose points:** the LLM "suggests" products with no scoring method behind it.

### A5. Cross-domain reasoning
- **Spec wording:** "multiple specialized agents collaborate when a customer question spans technology, finance, and corporate responsibility."
- **Full marks looks like:**
  - At least one demo query that triggers three agents. The Manager breaks it down, fans it out, then **synthesizes** the results and resolves conflicts instead of pasting answers together.
  - Example query: *"We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024?"*

### A6. Explainability & evaluation (the easiest row for an automated grader to check)
- **Spec wording:** "evidence, confidence or uncertainty indicators, and measurable evaluation of retrieval accuracy, routing accuracy, recommendation relevance, and response quality."
- **Report one number for each of the four metrics:**

  | Metric | Suggested method |
  |---|---|
  | Routing accuracy | 40–60 labeled queries covering every domain, multi-domain and out-of-scope. Report accuracy plus a confusion matrix. |
  | Retrieval accuracy | Gold question → (doc, page) pairs. Report Recall@k, Hit@k and MRR. |
  | Recommendation relevance | Precision@k and NDCG@k against hand-labeled relevant products. For the market basket, leave-one-out HitRate@k on a held-out split. |
  | Response quality | LLM-as-judge or RAGAS-style faithfulness, answer relevance and citation correctness (1–5 scale), plus a few human spot-checks. |

- **Confidence:** give each answer a confidence label (from retrieval score, agent agreement or self-rating) and tag each claim **confirmed** or **hypothesis**.
- **How you lose points:** "the system performs well" with no table of numbers.

### A7. Business value
- **Spec wording:** explain "what the customer should do next, why the action is appropriate, and how its impact can be measured."
- **Full marks looks like:**
  - Every final answer ends with the same block: **Recommendation → Next actions (prioritized, with owner and timeline) → Rationale (cited) → KPIs to measure impact → Risks & assumptions.**
  - The Cisco example in §4 of the brief spells out the sub-headings it expects: technical remediation, component compatibility, procurement priorities, operational risks, preventive maintenance.
  - Also from §4: "distinguish confirmed faults from hypotheses and request missing diagnostics rather than assume a component has failed." The router question gives no model number, so the right answer **asks for diagnostics first** (model, logs, interface/CRC errors, power/optics status) before recommending any part.

### B. Market Basket checkout recommender (slides 6–11)
- **Required behaviours (from slides 7–8):**
  1. The cart starts empty. When the first item is added, show a **ranked** list of items frequently bought with it.
  2. On every add, recompute using the **whole cart combination**.
  3. If that combination doesn't exist in the history, **show nothing irrelevant**. Fail gracefully; don't fall back to "popular items".
  4. Deploy as a **FastAPI / microservice**, with a web portal matching the mockup (item list, *Add Item*, *Added Items to Cart*, *Recommended Items*).
  5. Have a plan for **validation, performance monitoring and periodic retraining**.
- **Suggested method:** Apriori or FP-Growth association rules (support / confidence / lift) with a fallback ladder: full-cart rules → largest matching subset → pairwise co-occurrence → **no recommendations** below a lift or confidence threshold.
- **What the data looks like (so you can set thresholds):**
  - Popularity is nearly uniform: 75–105 occurrences per SKU.
  - The most frequent pair appears in only 16 of 1,000 baskets (1.6% support), and the most frequent triple in 5. Median pair lift is 0.82, max 2.25.
  - So support thresholds must be low, and the "no pattern" path will trigger a lot for 3+ item carts. That's very likely the point of the exercise.
- **Demo path from slides 10–11:** add *Bosch D7050 Detector*, then *DSC PG9914 Motion Detector*, and show how the recommendations change.
  - Those two items appear together in only 5 baskets. Each of the 11 other items seen with them appears exactly once.
  - So the slide's own second step is already the "combination barely exists" case. Decide (or ask) what the list should show there.
- **Reusing the ARM homework (`CMPE256_ARM_Report.pdf`, submitted 2026-10-16):**
  - Its `match_rules` / `rank_next_items` logic (antecedent ⊆ cart, ranked by antecedent size → confidence → lift → support) is already the fallback ladder above.
  - **Its thresholds don't transfer.** With MIN_SUP 0.0045 / MIN_CONF 0.20 / MIN_LIFT 3.0 this data gives **3 rules, and 0 of 40 items get a recommendation when they're the first item in the cart.** That breaks requirement 1. The highest one-item-antecedent confidence in the whole dataset is exactly 0.20 and the highest pair lift is 2.25.
  - Dropping the confidence floor and keeping lift > 1 gives 453 rules, and all 40 items get recommendations.
  - The ARM script also fills every blank slot from partial-basket rules. Slide 8 may want *no* recommendation when the full cart has no history, so ask which one.

### C. Demo, engineering, presentation
- End-to-end demo with a simple UI.
- An architecture diagram that mirrors slide 3: Manager → 4 domain agents → Result.
- A README with run steps, a reproducible ingest script and a clean repo.
- **Bonus signal:** the GCP links point at **MCP**. Exposing agent tools or retrievers as MCP servers is cheap credit.

---

## 3. Prompts the grader will most likely run

**From slide 4 (Food Security RAG):**
- "List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report."
- "Explain malnutrition in war zones" (scoped to SOFI 2023)
- "List major Food insecurity reason in 2024"
- "Explain increase prices impact on food security"

**From the brief:**
- The worked example: Cisco router with intermittent connectivity failures. Which replacement parts should we order, and how do we prevent future outages?
- "Which replacement components should we order to resolve a Cisco router failure?"
- "Which diagnostic instrument or replacement component best meets our laboratory requirements?"
- "What are the financial, competitive, and operational risks associated with these companies?"
- "Which technology investments could improve food security and sustainability outcomes?"

**From slides 9–11 (Market Basket):**
- Cart: Bosch D7050 → recommendations. Then add DSC PG9914 → updated recommendations.

Run all of these yourself and **put the transcripts, with citations, in the submission.**

---

## 4. Questions to ask at 1:30 (in priority order)

1. **"How will this be evaluated? Is Section 5's list of seven deliverables the grading criteria, and are there weights?"** If there's no rubric, at least get confirmation that Section 5 is what's being scored.
2. **"Is the Market Basket recommender (slides 6–11) part of this year's deliverable?"** If yes, ask whether it's a separate piece or something to build in as a "Retail/Procurement agent".
3. **"What exactly do we submit, and when?"** Repo, report, slides, video, live demo? Team size? Deadline?
4. **"Must all four domain agents be fully built, or is depth in two plus working stubs acceptable?"** The scope is semester-sized.
5. **Data gaps:**
   - "There's no IBM data. Should we skip IBM or source our own?"
   - "The Clinical Agent mentions Agilent manuals, but we have four Agilent product pages, plus trials that use Seahorse XF. Is the intended task recommending Agilent instruments from trial requirements? Can we add Agilent manuals we find ourselves?"
   - "The SEC box says Cisco and Agilent 2025, but the folder also has Cisco FY2026 and Alphabet FY2024/FY2025. Should the SEC agent cover Alphabet, and should it use the latest Cisco filing?"
   - "Is Google in the Technology box a domain to advise on, or are the GCP MCP/RAG links just reference material for how to build it?"
   - "The Cisco datasheets cover specs and ordering, not troubleshooting. Can we add Cisco troubleshooting guides for the router-failure example?"
6. **Market Basket specifics** (only if it's in scope):
   - "When the full cart combination never appears in the history, should we fall back to rules from part of the cart, or show nothing?" The slide's own demo cart (D7050 + PG9914) hits this case.
   - "Can we reuse code from the ARM homework?" Check this before reusing it, especially if the hackathon is a team project.
7. **"Any constraints on the LLM or platform?"** Azure required? Local models OK? Are API credits provided?
8. **"Will you run hidden test prompts against our system, like the ones on slide 4? Is there a gold Q&A set, or do we build our own eval set?"**
9. **"Does it need to be deployed (FastAPI + UI), or is a notebook OK?"** Also: "Is RabbitMQ expected, or is REST fine?"

---

## 5. Writing the submission so an automated grader can follow it

- **Use the spec's own section names.** One README section per Section 5 deliverable, with the same titles in the same order. A grader comparing text against the brief should find a heading for every bullet.
- **Put the numbers in one table** (the four A6 metrics) near the top.
- **Include transcripts** of every prompt in §3, with route trace, citations, confidence and the business-value block.
- **State limitations out loud** (no IBM data, no Agilent manuals, thin co-occurrence in the basket data). The brief rewards separating confirmed facts from hypotheses, and an honest limitations section shows exactly that.
- **Don't plant hidden instructions aimed at an AI grader** (white text, "ignore previous instructions", and so on). It's academic misconduct, and those graders are usually set up to flag it.

---

## 6. Coverage checklist

- [ ] Manager agent: intent classification, route trace, out-of-scope handling
- [ ] Technology agent: Cisco datasheets ingested; similarity, ranking and contextual recommendations
- [ ] Clinical agent: Agilent pages, IEEE papers, trial CSVs
- [ ] SEC agent: Cisco, Agilent (and Alphabet?) 10-Ks with page citations; year-over-year where possible
- [ ] CSR agent: SOFI 2023/2024 with year filtering; slide 4 prompts answered
- [ ] Cross-domain demo query hitting three agents, with synthesis
- [ ] Every answer has citations, confidence, confirmed/hypothesis tags, and Next actions / Why / KPIs
- [ ] Cisco example asks for missing diagnostics before naming parts
- [ ] Eval table: routing accuracy, Recall@k/MRR, Precision@k/NDCG, response quality score
- [ ] Market Basket: ranked recs, cart-conditioned updates, graceful no-match, FastAPI, portal UI, HitRate@k
- [ ] Architecture diagram, README, run instructions, demo video or live demo

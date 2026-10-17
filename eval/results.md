# Evaluation results

Timestamp (UTC): 2026-10-17T21:36:13.580862+00:00

Models configured: router `gpt-5.4-mini`; agent/judge `gpt-5.5`; embeddings `text-embedding-3-small`; agent effort `low`; judge effort `low`.

Mode: selected metrics. Each invocation replaces results.md with the selected sections. Gold labels are curated; phrase retrieval is a proxy for answer-bearing passage retrieval.

## Routing

Exact-match accuracy: 1.0000 (51/51). API failures: 0.

| Route | Precision | Recall | F1 |
| --- | --- | --- | --- |
| technology | 1.0000 | 1.0000 | 1.0000 |
| clinical | 1.0000 | 1.0000 | 1.0000 |
| sec | 1.0000 | 1.0000 | 1.0000 |
| csr | 1.0000 | 1.0000 | 1.0000 |
| out_of_scope | 1.0000 | 1.0000 | 1.0000 |

### Confusion summary

| Expected set | Predicted set | Count |
| --- | --- | --- |

### Errors

| Query | Expected | Predicted | Error |
| --- | --- | --- | --- |

## Retrieval

Case-insensitive phrase hits; MRR is truncated at k. Hit@1 and Hit@3 use their own cutoffs. Title anchors validate gold data, not the hit rule.

| Domain | N | Hit@1 | Hit@3 | Hit@5 | MRR@5 |
| --- | --- | --- | --- | --- | --- |
| overall | 28 | 0.6071 | 0.7143 | 0.8571 | 0.6887 |
| technology | 7 | 0.7143 | 0.8571 | 1.0000 | 0.8214 |
| clinical | 7 | 0.7143 | 0.8571 | 0.8571 | 0.7857 |
| sec | 7 | 0.5714 | 0.7143 | 0.8571 | 0.6476 |
| csr | 7 | 0.4286 | 0.4286 | 0.7143 | 0.5000 |

| Query | API error |
| --- | --- |

## Recommendation relevance

Binary relevance; macro averages per query. Precision uses a fixed denominator of 3, recall uses all labeled relevant IDs, and NDCG uses an ideal ranking of min(3, relevant IDs). Agilent has only three products, so Precision@3 is necessarily 1/3 for a single relevant product.

| Catalog | N | Precision@3 | Recall@3 | NDCG@3 | HitRate@1 |
| --- | --- | --- | --- | --- | --- |
| overall | 12 | 0.5556 | 0.8083 | 1.0000 | 1.0000 |
| cisco | 6 | 0.7778 | 0.6167 | 1.0000 | 1.0000 |
| agilent | 6 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |

| Catalog | Requirements | Top 3 | P@3 | R@3 | NDCG@3 | Hit@1 | Error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cisco | Virtual routing for a multicloud deployment in AWS and Azure | catalyst-8000v, isr-4000, isr4331 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| cisco | Software router in Google Cloud with NAT64 and MPLS VPN | catalyst-8000v, catalyst-8200, isr-4000 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| cisco | Data center aggregation router with redundant power supplies | asr1002-x, asr1004, asr1006 | 1.0000 | 0.3000 | 1.0000 | 1.0000 |  |
| cisco | Service provider POP and large office WAN edge aggregation | asr1002-x, asr1004, asr1006 | 1.0000 | 0.3000 | 1.0000 | 1.0000 |  |
| cisco | Small branch office SD-WAN router with a low budget | catalyst-8200, c8200l-1n-4t, c8200-1n-4t | 1.0000 | 0.5000 | 1.0000 | 1.0000 |  |
| cisco | Medium and large enterprise branch router with redundant power and LTE 5G | catalyst-8300, c8300-2n2s-6t, c8300-1n1s-6t | 1.0000 | 0.6000 | 1.0000 | 1.0000 |  |
| agilent | Measure mitochondrial respiration in patient PBMCs for diabetes research | seahorse-xf, artisan-link-pro, nanozoomer-ivd | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| agilent | Label-free glycolysis and ATP production in 3D cell models | seahorse-xf, artisan-link-pro, nanozoomer-ivd | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| agilent | Whole-slide imaging for primary diagnostic pathology | nanozoomer-ivd, artisan-link-pro, seahorse-xf | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| agilent | Scan glass histopathology tissue slides at 20x and 40x | nanozoomer-ivd, artisan-link-pro, seahorse-xf | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| agilent | Automate special histochemical staining and deparaffinization | artisan-link-pro, nanozoomer-ivd, seahorse-xf | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |
| agilent | Special stains with ready-to-use kits and editable protocols | artisan-link-pro, nanozoomer-ivd, seahorse-xf | 0.3333 | 1.0000 | 1.0000 | 1.0000 |  |

### Existing market-basket offline results

# Market Basket Offline Evaluation Results

- **Dataset**: `CMPE256_Hackathon_market_basket_analysis_Release.csv` (1,000 transactions, 40 SKUs, 2–5 items/basket)
- **Train/Test Split**: 80/20 with fixed seed 42 (800 train, 200 test transactions)
- **Evaluation Protocol**: Leave-one-out on test baskets (size >= 2, total instances: 200)
- **Rule Policy**: Full-Cart Apriori only (antecedent must match the entire cart; no subset or popularity fallback)

## Benchmark Summary Table

| Model / Configuration | Min Support Count | Min Confidence | Min Lift | HitRate@1 | HitRate@3 | HitRate@5 | Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Popularity Baseline** | — | — | — | 3.50% | 8.50% | 12.50% | 100.00% |
| **Apriori (Default)** | 2 | 0.05 | 1.0 | 0.50% | 1.50% | 2.50% | 42.00% |
| Apriori Sweep | 2 | 0.10 | 1.0 | 0.50% | 1.50% | 2.50% | 42.00% |
| Apriori Sweep | 2 | 0.20 | 1.0 | 0.50% | 0.50% | 0.50% | 19.50% |
| Apriori Sweep | 3 | 0.05 | 1.0 | 0.00% | 1.00% | 2.00% | 24.50% |
| Apriori Sweep | 3 | 0.10 | 1.0 | 0.00% | 1.00% | 2.00% | 24.50% |
| Apriori Sweep | 3 | 0.20 | 1.0 | 0.00% | 0.00% | 0.00% | 3.00% |
| Apriori Sweep | 5 | 0.05 | 1.0 | 0.00% | 1.00% | 2.00% | 21.50% |
| Apriori Sweep | 5 | 0.10 | 1.0 | 0.00% | 1.00% | 2.00% | 21.50% |
| Apriori Sweep | 5 | 0.20 | 1.0 | 0.00% | 0.00% | 0.00% | 0.00% |

## Analysis & Key Findings

1. **Impact of Full-Cart Antecedent Requirement**:
   - Because recommendations are strictly required to match the entire multi-item cart (antecedents of size 1 to 4) without subset fallbacks, coverage is directly governed by multi-item co-occurrence frequency in this sparse dataset.
   - When carts have 2 or 3 items, co-occurrence drops rapidly (maximum triple frequency in the dataset is 5), causing coverage to drop from ~15-20% at `min_support_count=2` to lower rates at `min_support_count=5`.
2. **Contextual Precision vs. Popularity Baseline**:
   - The popularity baseline achieves 100% coverage by blindly recommending global best-sellers, but lacks personalization to what the customer actually put in the cart.
   - Full-cart Apriori provides targeted, pattern-backed recommendations only when genuine multi-product affinities exist, adhering faithfully to the instructor's rule of returning an empty list when no pattern exists.
3. **Threshold Sensitivity**:
   - Increasing `min_confidence` from 0.05 to 0.20 drastically curtails valid rules because individual item probabilities are ~0.09. The default settings (`min_support_count=2`, `min_confidence=0.05`, `min_lift=1.0`) strike the optimal balance between coverage and association validity.


## Response quality

Judge coverage: 10/10 prompts. Means below use successful judge calls only; failures appear in the detail table. Structural grounding scores are proxies, not factual verification.

| Metric | Mean (1–5) |
| --- | --- |
| faithfulness | 4.2000 |
| relevance | 4.4000 |
| actionability | 4.5000 |

| Question | Faithfulness | Relevance | Actionability | Rationale / error |
| --- | --- | --- | --- | --- |
| Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first? | 4 | 5 | 5 | Directly addresses diagnostics before ordering and gives concrete spares/KPIs; most platform/lifecycle claims are supported and hypotheses labeled, though some troubleshooting assertions and ordering priority claims are based on general expertise rather than cited evidence. |
| Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent instrument fits and which trials have used it? | 4 | 5 | 5 | Directly answers with Seahorse XF and relevant PBMC/diabetes trial examples, with strong workflow caveats and KPIs; minor faithfulness gaps include over-specific model preference for XF Pro/XFe96 not fully supported for PBMCs by product sources and some cited trials are adjacent/non-PBMC or non-diabetes. |
| What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet? | 3 | 2 | 4 | Answer is well supported for Alphabet and offers concrete mitigation steps/KPIs, but it fails to address Cisco and Agilent at all, and includes questionable FY2025 10-K framing/specificity despite cited passages. |
| List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report. | 5 | 5 | 3 | The answer accurately reflects the cited SOFI 2023 passages and directly lists the major drivers, including the urbanization framing; however, it offers limited actionable next steps or measurable KPIs, which were not central to the user's list request. |
| Explain malnutrition in war zones | 4 | 4 | 4 | Strongly grounded in the provided SOFI excerpts with mostly accurate citations and useful synthesis; minor gaps include some uncited mechanistic specifics (health/WASH access, diversion safeguards) and the answer is more CSR/programming-oriented than the broad explanatory question requires, though it provides concrete next steps and KPIs. |
| List major Food insecurity reason in 2024 | 5 | 5 | 4 | The answer accurately reflects the cited SOFI 2024 passages on conflict, climate extremes, economic downturns and structural factors, directly answers the question, and provides useful but somewhat broader-than-asked recommendations and KPIs. |
| Explain increase prices impact on food security | 5 | 4 | 5 | The answer is well supported by the cited SOFI excerpts with accurate figures and mechanisms, directly explains price impacts on food security though somewhat over-tailored to CSR, and provides concrete recommendations, next steps, and KPIs. |
| Which technology investments could improve food security and sustainability outcomes? | 4 | 5 | 5 | The answer directly addresses technology investments with strong next steps and KPIs, and most claims are supported or framed as hypotheses; minor faithfulness gaps include some uncited extrapolations about sensors/IoT/cold-chain digital impacts and potential overemphasis on specific Cisco products relative to the broad question. |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | 4 | 5 | 5 | Directly answers model fit, Cisco 10-K risks, and SOFI 2024 outcomes with strong citations and explicit hypotheses, though it overstates some unsupported cold-chain-specific benefits and cites FY2026 10-K despite the user not specifying that year. |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | 4 | 4 | 5 | Strongly grounded cautious recommendation with clear gaps and KPIs; minor faithfulness issues include some extrapolation beyond cited sources (e.g., AI-adjacent workflow, regulatory/reimbursement implications) and the lab’s needs are largely unspecified, limiting direct relevance. |

### Per-agent grounding

| Question | Agent | Findings | Confirmed | Hypotheses | Sources | Citation coverage | Top3 cosine | Grounding score | Invalid citations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first? | technology | 7 | 6 | 1 | 13 | 1.0000 | 0.6570 | 0.9500 |  |
| Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent instrument fits and which trials have used it? | clinical | 8 | 8 | 0 | 38 | 1.0000 | 0.5290 | 0.7900 |  |
| What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet? | sec | 8 | 8 | 0 | 50 | 1.0000 | 0.7330 | 1.0000 |  |
| List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report. | csr | 6 | 6 | 0 | 8 | 1.0000 | 0.7430 | 1.0000 |  |
| Explain malnutrition in war zones | csr | 8 | 8 | 0 | 16 | 1.0000 | 0.7210 | 1.0000 |  |
| List major Food insecurity reason in 2024 | csr | 6 | 6 | 0 | 8 | 1.0000 | 0.7310 | 1.0000 |  |
| Explain increase prices impact on food security | csr | 8 | 8 | 0 | 20 | 1.0000 | 0.7340 | 1.0000 |  |
| Which technology investments could improve food security and sustainability outcomes? | technology | 8 | 6 | 2 | 16 | 1.0000 | 0.7730 | 1.0000 |  |
| Which technology investments could improve food security and sustainability outcomes? | csr | 8 | 8 | 0 | 16 | 1.0000 | 0.7670 | 1.0000 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | technology | 8 | 7 | 1 | 13 | 0.8800 | 0.7300 | 0.9400 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | sec | 8 | 8 | 0 | 20 | 1.0000 | 0.7180 | 1.0000 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | csr | 6 | 3 | 3 | 8 | 1.0000 | 0.6770 | 0.9700 |  |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | clinical | 6 | 5 | 1 | 9 | 1.0000 | 0.5940 | 0.8700 |  |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | sec | 8 | 8 | 0 | 20 | 1.0000 | 0.7290 | 1.0000 |  |

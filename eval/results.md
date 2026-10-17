# Evaluation results

Timestamp (UTC): 2026-10-17T21:39:21.102216+00:00

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
| relevance | 4.8000 |
| actionability | 4.5000 |

| Question | Faithfulness | Relevance | Actionability | Rationale / error |
| --- | --- | --- | --- | --- |
| Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first? | 4 | 5 | 5 | The answer directly addresses diagnostics before ordering and gives concrete spares/KPIs; most Cisco platform claims are supported, though several troubleshooting claims and command specifics are based on general expertise rather than the cited sources, and no exact replacement parts can be provided without model details. |
| Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent instrument fits and which trials have used it? | 4 | 5 | 5 | The answer directly identifies Seahorse XF/XFe96-class instruments and relevant diabetes/metabolic PBMC trials with mostly well-supported citations; minor penalties for over-specific model preference and RUO/throughput claims not fully evidenced by the cited records. |
| What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet? | 4 | 5 | 4 | Directly answers the risk question with well-cited SEC excerpts and useful comparisons/next steps, but some specifics appear unsupported or overstated by excerpts (e.g., FY2025/2026 'most recent' framing, Alphabet lower-margin growth areas, Agilent life-sciences demand cycles/competitive characterization) and recommendations are more diligence-oriented than fully measurable. |
| List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report. | 5 | 5 | 2 | The answer accurately lists the SOFI 2023 drivers with strong source support and appropriate nuance on urbanization, directly addressing the question; however, it provides little in the way of concrete next steps or measurable KPIs, which limits actionability. |
| Explain malnutrition in war zones | 4 | 5 | 5 | Directly answers the question with well-cited SOFI evidence and clear recommendations/KPIs; minor faithfulness gaps include some uncited general mechanisms and intervention specifics extending beyond the provided sources, though hypotheses are partly separated. |
| List major Food insecurity reason in 2024 | 5 | 4 | 4 | The answer accurately reflects the cited SOFI passages on conflict, climate extremes, economic downturns and structural factors, with well-supported citations; it directly answers the question but adds CSR-oriented recommendations beyond the simple ask, and its next steps/KPIs are concrete though somewhat generic. |
| Explain increase prices impact on food security | 4 | 5 | 5 | The answer directly explains price increases' food-security impacts and adds strong practical recommendations/KPIs; most factual claims are well supported by cited SOFI excerpts, though a few mechanisms and CSR-specific interventions are partly inferred beyond the sources. |
| Which technology investments could improve food security and sustainability outcomes? | 4 | 4 | 5 | Strong synthesis with citations and explicit caveats that food-sector impacts are partly inferential; however, it over-specifies vendor/product investments and some use cases beyond direct outcome evidence, while remaining highly relevant and action-oriented with concrete pilots and KPIs. |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | 4 | 5 | 5 | Directly answers model fit, 10-K risks, and SOFI 2024 outcomes with strong citations and clear caveats; minor faithfulness issues include reliance on a questionable 'FY2026 latest' 10-K framing and some inferred cold-chain/impact specifics beyond the sources. |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | 4 | 5 | 5 | The answer directly addresses the invest/pilot decision, uses the cited 10-K and product evidence carefully with explicit gaps and hypotheses, and provides concrete validation steps and KPIs; minor faithfulness gaps include some broad operational/IT recommendations inferred beyond source specifics and reliance on product-page claims without independent performance evidence. |

### Per-agent grounding

| Question | Agent | Findings | Confirmed | Hypotheses | Sources | Citation coverage | Top3 cosine | Grounding score | Invalid citations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first? | technology | 5 | 4 | 1 | 6 | 1.0000 | 0.6110 | 0.8900 |  |
| Our diabetes research lab needs to measure mitochondrial function in patient PBMCs. Which Agilent instrument fits and which trials have used it? | clinical | 8 | 8 | 0 | 25 | 1.0000 | 0.3940 | 0.6200 |  |
| What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet? | sec | 8 | 8 | 0 | 54 | 1.0000 | 0.6290 | 0.9100 |  |
| List major Food insecurity reason in 2023 from within the context of State of Food Security and Nutrition in the World 2023 report. | csr | 5 | 5 | 0 | 8 | 1.0000 | 0.7010 | 1.0000 |  |
| Explain malnutrition in war zones | csr | 8 | 7 | 1 | 26 | 1.0000 | 0.7130 | 1.0000 |  |
| List major Food insecurity reason in 2024 | csr | 6 | 6 | 0 | 8 | 1.0000 | 0.6920 | 0.9900 |  |
| Explain increase prices impact on food security | csr | 8 | 8 | 0 | 16 | 1.0000 | 0.7220 | 1.0000 |  |
| Which technology investments could improve food security and sustainability outcomes? | technology | 8 | 7 | 1 | 20 | 1.0000 | 0.7320 | 1.0000 |  |
| Which technology investments could improve food security and sustainability outcomes? | csr | 8 | 8 | 0 | 16 | 1.0000 | 0.6710 | 0.9600 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | technology | 8 | 7 | 1 | 9 | 1.0000 | 0.7320 | 1.0000 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | sec | 8 | 8 | 0 | 16 | 1.0000 | 0.7020 | 1.0000 |  |
| We're considering Cisco Catalyst edge routers to monitor cold-chain food distribution. Which model fits, what risks does Cisco's 10-K disclose, and how would this support food-security outcomes per SOFI 2024? | csr | 7 | 5 | 2 | 8 | 1.0000 | 0.6690 | 0.9600 |  |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | clinical | 7 | 6 | 1 | 16 | 1.0000 | 0.5720 | 0.8400 |  |
| Should a diagnostics company invest in Agilent digital pathology given Agilent's FY2025 10-K and the lab's needs? | sec | 8 | 8 | 0 | 20 | 1.0000 | 0.7380 | 1.0000 |  |

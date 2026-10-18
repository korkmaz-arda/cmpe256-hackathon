"""Recommendation relevance of the content-based recommenders (Cisco platforms, Agilent products).

    python -m consultai.eval.recommendation

Gold labels are graded by hand from the data sheets / pages (2 = ideal fit, 1 = acceptable, 0 = not appropriate,
including end-of-sale platforms for a new purchase). Metrics: hit@1 (top item is ideal or acceptable),
precision@3, nDCG@3 (graded). Ablation: the full recommender vs similarity-only ranking (cosine of the use case
to the item description, no constraints / requirement fit / lifecycle) to show what the structured scoring adds.
The market-basket recommender is evaluated separately (consultai.eval.basket).
"""
from __future__ import annotations

import math

from consultai.agents.clinical.agilent_catalog import LabRequirements, load_catalog, recommend_agilent_products
from consultai.agents.technology.catalog import PlatformRequirements, platforms, recommend_platforms
from consultai.eval.common import md_table, save_result

CISCO = [
    {"id": "small-branch", "req": {"use_case": "Small branch office with a few dozen users, SD-WAN and about 500 Mbps of IPsec VPN to HQ",
                                   "deployment": "branch", "virtual_required": False, "min_ipsec_gbps": 0.5},
     "gold": {"C8200L-1N-4T": 2, "C8200-1N-4T": 2, "C8300-1N1S-6T": 1}},
    {"id": "large-branch-10g", "req": {"use_case": "Large branch campus needing 10G WAN uplinks, redundant power and about 15 Gbps IPsec",
                                       "deployment": "branch", "virtual_required": False, "need_10g_wan": True,
                                       "need_redundant_power": True, "min_ipsec_gbps": 15},
     "gold": {"C8300-1N1S-4T2X": 2, "C8300-2N2S-4T2X": 2, "ASR 1001-HX": 1, "ASR1002-HX": 1}},
    {"id": "cloud", "req": {"use_case": "Virtual router in our AWS and Azure VPCs to extend SD-WAN to the cloud",
                            "deployment": "cloud", "virtual_required": True},
     "gold": {"Catalyst 8000V": 2}},
    {"id": "replace-isr4331", "req": {"use_case": "Replace end-of-sale ISR 4331 branch routers with a supported platform",
                                      "deployment": "branch", "virtual_required": False, "current_model": "ISR4331"},
     "gold": {"C8200-1N-4T": 2, "C8300-1N1S-6T": 2, "C8200L-1N-4T": 1, "C8300-1N1S-4T2X": 1, "C8300-2N2S-6T": 1}},
    {"id": "headend-100g", "req": {"use_case": "WAN aggregation headend terminating more than 100 Gbps of encrypted branch traffic",
                                   "deployment": "headend", "virtual_required": False, "min_ipsec_gbps": 100},
     "gold": {"ASR1006-X": 2, "ASR1009-X": 2, "ASR1013": 1}},
    {"id": "regional-aggregation", "req": {"use_case": "Regional aggregation router with 10G ports and around 20 Gbps of IPsec",
                                           "deployment": "aggregation", "virtual_required": False, "need_10g_wan": True,
                                           "min_ipsec_gbps": 20},
     "gold": {"ASR1002-HX": 2, "ASR1006-X": 1, "ASR1009-X": 1}},
]

AGILENT = [
    {"id": "primary-dx-scanner", "req": {"need": "Whole-slide scanner for primary histopathology diagnosis in a hospital lab",
                                         "clinical_diagnostic_use": True, "applications": ["primary diagnosis"]},
     "gold": {"NanoZoomer® S360MD Slide Scanner System": 2, "Agilent S540MD Slide Scanner System": 1}},
    {"id": "special-stains", "req": {"need": "Automate special histochemical stains from deparaffinization to finished slides",
                                     "applications": ["special staining"]},
     "gold": {"Artisan Link Pro Special Staining System": 2, "Special Stains Kits": 1, "Special Staining Accessories": 1}},
    {"id": "cell-metabolism", "req": {"need": "Measure mitochondrial respiration and glycolysis of live cells for drug discovery",
                                      "applications": ["cell metabolism", "drug discovery"]},
     "gold": {"Agilent Seahorse XF Pro analyzer": 2, "Agilent Seahorse XF Pro Analyzer": 2, "Agilent Seahorse XF Analyzers": 2,
              "Plate Reader Metabolic Assays": 1, "XF Assay Kits, Reagents & Cell Assay Media": 1}},
]


def _score(ranked: list[str], gold: dict[str, int], k: int = 3) -> dict:
    rels = [gold.get(x, 0) for x in ranked[:k]]
    ideal = sorted(gold.values(), reverse=True)[:k]
    dcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels))
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return {"hit@1": float(bool(rels) and rels[0] > 0), "p@3": sum(r > 0 for r in rels) / k, "ndcg@3": dcg / idcg if idcg else 0.0}


def _similarity_only(texts: dict[str, str], query: str) -> list[str]:
    from consultai.retrieval.models import embed_passages, embed_query
    names = list(texts)
    sims = embed_passages([texts[n] for n in names]) @ embed_query(query)
    return [names[i] for i in sims.argsort()[::-1]]


def run() -> dict:
    rows, details = [], []
    plat_text = {p.model: f"{p.model}: {p.summary} Deployment: {', '.join(p.deployment)}" for p in platforms()}
    prod_text = {p.name: f"{p.name}. {p.summary} Applications: {', '.join(p.applications)}" for p in load_catalog()}
    for kind, cases in (("cisco_platforms", CISCO), ("agilent_products", AGILENT)):
        agg = {"full": [], "similarity_only": []}
        for case in cases:
            if kind == "cisco_platforms":
                full = [r["model"] for r in recommend_platforms(PlatformRequirements(**case["req"], k=5))["ranked"]]
                base = [m for m in _similarity_only(plat_text, case["req"]["use_case"]) if m.upper() != str(case["req"].get("current_model", "")).upper()]
            else:
                full = [r["product"] for r in recommend_agilent_products(LabRequirements(**case["req"], k=5))["ranked"]]
                base = _similarity_only(prod_text, case["req"]["need"])
            sf, sb = _score(full, case["gold"]), _score(base, case["gold"])
            agg["full"].append(sf)
            agg["similarity_only"].append(sb)
            details.append({"kind": kind, "id": case["id"], "full_top3": full[:3], "similarity_top3": base[:3],
                            "full": sf, "similarity_only": sb})
        for variant, scores in agg.items():
            rows.append({"recommender": kind, "variant": variant, "n": len(scores),
                         **{m: sum(s[m] for s in scores) / len(scores) for m in ("hit@1", "p@3", "ndcg@3")}})
    table = md_table(rows, ["recommender", "variant", "n", "hit@1", "p@3", "ndcg@3"])
    path = save_result("recommendation", {"summary": rows, "details": details, "table_md": table})
    print(table)
    for d in details:
        print(d["id"], "| full:", d["full_top3"], "| sim:", d["similarity_top3"])
    print("->", path)
    return {"summary": rows}


if __name__ == "__main__":
    run()

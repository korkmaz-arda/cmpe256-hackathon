"""Measurable evaluation of the platform.

- routing accuracy: 24 hand-labeled queries (single- and multi-domain)
- retrieval accuracy: precision@5 of retrieved chunks against expected domains
- recommendation relevance: hold-one-out hit-rate@5 / MRR@5 on procurement data
- response quality proxies: evidence volume, citation presence, uncertainty flags
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval import KnowledgeBase
from agents import ManagerAgent

RESULTS = Path(__file__).resolve().parent.parent / "results"

ROUTING_TESTS = [
    # technology
    ("Our Cisco Catalyst 8300 router has intermittent connectivity failures; "
     "which replacement parts should we order?", ["technology"]),
    ("What is the IPsec throughput of the Catalyst 8200 series?", ["technology"]),
    ("We bought Hanwha QNV-6010R cameras; which NVR and accessories are "
     "frequently purchased with them?", ["technology"]),
    ("Compare Cisco ASR 1000 and 4000 ISR for WAN aggregation.", ["technology"]),
    ("How do I deploy the Catalyst 8000V virtual router on Google Cloud?", ["technology"]),
    ("Which Bosch control panel is compatible with our existing detectors?", ["technology"]),
    # clinical
    ("Which Agilent instrument is best for real-time cell metabolic analysis?",
     ["clinical"]),
    ("We need whole-slide imaging for our pathology lab; what scanner do you recommend?",
     ["clinical"]),
    ("What special stains automation does Agilent offer for consistent results?",
     ["clinical"]),
    ("Our lab is choosing between Seahorse assay platforms.", ["clinical"]),
    ("Which digital pathology scanner fits a high-volume clinical lab?", ["clinical"]),
    # sec
    ("What financial risks does Cisco disclose in its annual report?", ["sec"]),
    ("Summarize Alphabet's competitive risks from their SEC filing.", ["sec"]),
    ("How did Agilent perform financially according to their latest 10-K?", ["sec"]),
    ("What operational risks does Cisco disclose around supply chain?", ["sec"]),
    ("Compare the risk factors disclosed by Cisco and Alphabet.", ["sec"]),
    # csr
    ("Which technology investments could improve food security outcomes?", ["csr"]),
    ("What does the SOFI 2024 report say about financing to end hunger?", ["csr"]),
    ("How can agrifood systems transformation improve nutrition?", ["csr"]),
    ("What are the latest global hunger statistics?", ["csr"]),
    # cross-domain
    ("We are evaluating Cisco as a strategic vendor: product options, "
     "financial risks, and sustainability alignment.",
     ["technology", "sec", "csr"]),
    ("Should we invest in Agilent diagnostics given their financial health "
     "and our lab needs?", ["clinical", "sec"]),
    ("What are the technology and financial risks of migrating our network "
     "to Cisco cloud solutions?", ["technology", "sec"]),
    ("How do data center investments affect both our IT costs and "
     "sustainability goals?", ["technology", "csr"]),
]


def prf(expected, predicted):
    e, p = set(expected), set(predicted)
    tp = len(e & p)
    prec = tp / len(p) if p else 0.0
    rec = tp / len(e) if e else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def main():
    kb = KnowledgeBase()
    mgr = ManagerAgent(kb)

    # ---- routing ----
    exact, f1s, per_domain = 0, [], {}
    for q, expected in ROUTING_TESTS:
        pred = mgr.classify(q)["domains"]
        if set(pred) == set(expected):
            exact += 1
        _, _, f1 = prf(expected, pred)
        f1s.append(f1)
        for d in expected:
            s = per_domain.setdefault(d, {"n": 0, "hit": 0})
            s["n"] += 1
            s["hit"] += 1 if d in pred else 0

    # ---- retrieval: precision@5 per query against expected domains ----
    # (a) per-domain retrieval (does the right agent find its own evidence?)
    precs = []
    for q, expected in ROUTING_TESTS:
        hits = []
        for d in expected:
            hits += kb.retrieve(q, d, k=5)
        hits = sorted(hits, key=lambda x: -x[1])[:5]
        ok = sum(1 for c, _ in hits if c["domain"] in expected)
        precs.append(ok / max(1, len(hits)))
    # (b) global retrieval: top-5 across ALL domains — a real discrimination test
    from sklearn.metrics.pairwise import cosine_similarity
    gprecs = []
    for q, expected in ROUTING_TESTS:
        qv = kb.vectorizer.transform([q])
        sims = cosine_similarity(qv, kb.matrix).ravel()
        top5 = sorted(range(len(sims)), key=lambda i: -sims[i])[:5]
        ok = sum(1 for i in top5 if kb.chunks[i]["domain"] in expected)
        gprecs.append(ok / 5)

    # ---- recommendation relevance (hold-one-out on procurement data) ----
    rec_eval = mgr.recommender.evaluate(n=200, seed=7, topn=5)

    # ---- response quality proxies over the demo-style queries ----
    ev_counts, cited, unc_flags, n_reports = [], 0, 0, 0
    for q, _ in ROUTING_TESTS:
        res = mgr.handle(q)
        if res.get("clarification_needed"):
            continue
        for rep in res["agent_reports"]:
            n_reports += 1
            ev_counts.append(len(rep["evidence"]))
            cited += sum(1 for f in rep["findings"] if "[" in f and "]" in f)
            unc_flags += len(rep["uncertainties"])

    metrics = {
        "routing": {
            "n": len(ROUTING_TESTS),
            "exact_match_accuracy": round(exact / len(ROUTING_TESTS), 3),
            "mean_f1": round(sum(f1s) / len(f1s), 3),
            "recall_by_domain": {d: round(v["hit"] / v["n"], 3)
                                 for d, v in per_domain.items()},
        },
        "retrieval": {
            "mean_precision@5": round(sum(precs) / len(precs), 3),
            "cross_domain_precision@5": round(sum(gprecs) / len(gprecs), 3),
            "n_queries": len(precs),
        },
        "recommendation": rec_eval,
        "response_quality": {
            "reports": n_reports,
            "avg_evidence_passages_per_report":
                round(sum(ev_counts) / max(1, len(ev_counts)), 1),
            "findings_with_citations": cited,
            "uncertainty_flags_raised": unc_flags,
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "eval_metrics.json", "w") as f:
        json.dump(metrics, f, indent=1)
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()

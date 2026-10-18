"""Intelligent recommendation system: association-rule mining (Apriori-style)
over the 1,000-transaction procurement history.

Recommends compatible / frequently co-procured components for a given
basket of items, ranked by confidence x lift, with support reported.
This is the same family of technique as the CMPE 256 market-basket work.
"""
import csv
import itertools
import json
import random
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
CSV_PATH = RAW / "CMPE256_Hackathon_market_basket_analysis_Release.csv"

MIN_SUPPORT = 0.005
MIN_CONFIDENCE = 0.10
MAX_ITEMSET = 3


def load_transactions(path: str = str(CSV_PATH)):
    txns = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items = {(row.get(k) or "").strip()
                     for k in ("item_1", "item_2", "item_3", "item_4", "item_5")}
            items.discard("")
            if items:
                txns.append(frozenset(items))
    return txns


def frequent_itemsets(txns, min_support=MIN_SUPPORT, max_len=MAX_ITEMSET):
    n = len(txns)
    counts = {}
    for t in txns:
        for item in t:
            counts[frozenset([item])] = counts.get(frozenset([item]), 0) + 1
    freq = {fs: c / n for fs, c in counts.items() if c / n >= min_support}
    prev = [fs for fs in freq]
    for size in range(2, max_len + 1):
        cands = set()
        for a, b in itertools.combinations(prev, 2):
            u = a | b
            if len(u) == size:
                cands.add(u)
        counts = {c: 0 for c in cands}
        for t in txns:
            for c in cands:
                if c <= t:
                    counts[c] += 1
        cur = {c: v / n for c, v in counts.items() if v / n >= min_support}
        freq.update(cur)
        prev = list(cur)
        if not prev:
            break
    return freq


def association_rules(freq):
    rules = []
    for itemset, sup in freq.items():
        if len(itemset) < 2:
            continue
        items = list(itemset)
        for r in range(1, len(items)):
            for ant in itertools.combinations(items, r):
                ant, con = frozenset(ant), itemset - frozenset(ant)
                conf = sup / freq[ant]
                lift = conf / freq[con] if freq.get(con) else 0.0
                if conf >= MIN_CONFIDENCE:
                    rules.append({"antecedent": sorted(ant),
                                  "consequent": sorted(con),
                                  "support": round(sup, 4),
                                  "confidence": round(conf, 4),
                                  "lift": round(lift, 3)})
    rules.sort(key=lambda x: (x["confidence"] * x["lift"]), reverse=True)
    return rules


class ComponentRecommender:
    def __init__(self):
        self.txns = load_transactions()
        self.freq = frequent_itemsets(self.txns)
        self.rules = association_rules(self.freq)

    def recommend(self, basket, topn=5):
        """basket: iterable of item names (or name fragments)."""
        basket = set(basket)
        # fuzzy-match fragments to full catalog names
        matched = set()
        for b in sorted(basket):  # sorted for deterministic tie-breaking
            bl = b.lower()
            for t in self.txns:
                for item in t:
                    if bl in item.lower() or item.lower() in bl:
                        matched.add(item)
        scored = {}
        for r in self.rules:
            ant = set(r["antecedent"])
            if ant and ant <= matched:
                for c in r["consequent"]:
                    if c not in matched:
                        key = (r["confidence"] * r["lift"], r["confidence"])
                        if c not in scored or key > scored[c][0]:
                            scored[c] = (key, r)
        ranked = sorted(scored.items(), key=lambda x: x[1][0], reverse=True)[:topn]
        return [{"item": item,
                 "support": rule["support"],
                 "confidence": rule["confidence"],
                 "lift": rule["lift"],
                 "because": "frequently procured with " +
                            ", ".join(rule["antecedent"])}
                for item, (_, rule) in ranked]

    def evaluate(self, n=200, seed=7, topn=5):
        """Hold-one-out: hide one item, see if it is in top-n recommendations."""
        rng = random.Random(seed)
        sample = [t for t in self.txns if len(t) >= 2]
        sample = rng.sample(sample, min(n, len(sample)))
        hits, rr = 0, 0.0
        for t in sample:
            items = sorted(t)  # sorted for deterministic eval across runs
            hidden = rng.choice(items)
            basket = [i for i in items if i != hidden]
            recs = [r["item"] for r in self.recommend(basket, topn=topn)]
            if hidden in recs:
                hits += 1
                rr += 1.0 / (recs.index(hidden) + 1)
        return {"n": len(sample), "hit_rate@5": round(hits / len(sample), 3),
                "mrr@5": round(rr / len(sample), 3),
                "rules_mined": len(self.rules)}


if __name__ == "__main__":
    rec = ComponentRecommender()
    print(json.dumps(rec.evaluate(), indent=1))
    demo = rec.recommend(["Hanwha QNV-6010R Network Camera"])
    print(json.dumps(demo, indent=1)[:1500])

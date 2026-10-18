"""Market-basket recommender: hold-out evaluation and threshold selection for this sparse dataset.

    python -m consultai.eval.basket

Protocol: seeded 80/20 split of the 1,000 transactions. Each test transaction is replayed as a checkout in its
listed order; after each item is added (cart = items so far), the recommender's top-3 is compared with the
items still to come in that basket.
  hit_rate@3      share of checkout steps where a later item is in the top-3 (no recommendation counts as a miss)
  precision@3     share of shown recommendations that were later bought (only steps that showed something)
  coverage        share of checkout steps that showed any recommendation
Baseline: most popular items not in the cart (always shows 3). Thresholds (min support count, min confidence)
are chosen on the grid by the harmonic mean f of precision@3 and hit_rate@3: the most conservative setting whose f
is within 5% of the best, so the recommender stays useful but quiet when it has little evidence. The chosen values are written to eval/results/basket.json and used by the app.
"""
from __future__ import annotations

import random

from consultai.basket.apriori import BasketRecommender, load_transactions
from consultai.eval.common import md_table, save_result
from consultai.ingest.sources import RETAIL_TRANSACTIONS, Source

GRID_SUPPORT = [2, 3, 4, 5, 6, 8]
GRID_CONF = [0.05, 0.08, 0.1, 0.15, 0.2, 0.3]
K = 3


def transactions_path():
    return Source("retail", "-", "-", "-", "csv", RETAIL_TRANSACTIONS, None, "-").local_path


def ordered_transactions(path) -> list[list[str]]:
    import csv
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [[i.strip() for i in r[1:] if i.strip()] for r in list(csv.reader(fh))[1:]]


def evaluate(train: list[frozenset], test: list[list[str]], min_count: int, min_conf: float) -> dict:
    rec = BasketRecommender(train, min_count, min_conf)
    steps = hits = shown = shown_items = shown_hits = 0
    for basket in test:
        for j in range(1, len(basket)):
            cart, future = basket[:j], set(basket[j:])
            out = rec.recommend(cart, k=K).recommendations
            steps += 1
            if out:
                shown += 1
                shown_items += len(out)
                good = sum(r.item in future for r in out)
                shown_hits += good
                hits += good > 0
    prec = shown_hits / shown_items if shown_items else 0.0
    hit = hits / steps if steps else 0.0
    return {"min_count": min_count, "min_confidence": min_conf, "hit_rate@3": round(hit, 4),
            "precision@3": round(prec, 4), "coverage": round(shown / steps, 4) if steps else 0.0,
            "f": round(2 * prec * hit / (prec + hit), 4) if prec + hit else 0.0, "frequent_itemsets": len(rec.frequent)}


def popularity_baseline(train: list[frozenset], test: list[list[str]]) -> dict:
    counts: dict[str, int] = {}
    for t in train:
        for i in t:
            counts[i] = counts.get(i, 0) + 1
    ranked = sorted(counts, key=counts.get, reverse=True)
    steps = hits = shown_hits = 0
    for basket in test:
        for j in range(1, len(basket)):
            cart, future = set(basket[:j]), set(basket[j:])
            top = [i for i in ranked if i not in cart][:K]
            good = sum(i in future for i in top)
            steps, hits, shown_hits = steps + 1, hits + (good > 0), shown_hits + good
    return {"hit_rate@3": round(hits / steps, 4), "precision@3": round(shown_hits / (steps * K), 4), "coverage": 1.0}


def run(seed: int = 7) -> dict:
    ordered = ordered_transactions(transactions_path())
    rng = random.Random(seed)
    idx = list(range(len(ordered)))
    rng.shuffle(idx)
    cut = int(0.8 * len(idx))
    train = [frozenset(ordered[i]) for i in idx[:cut]]
    test = [ordered[i] for i in idx[cut:]]
    grid = [evaluate(train, test, s, c) for s in GRID_SUPPORT for c in GRID_CONF]
    # Differences between settings are small on 200 test baskets, so prefer the most conservative setting
    # (highest support, then confidence) whose score is within 5% of the best: fewer rules built on 2-3
    # co-occurrences, i.e. fewer irrelevant recommendations.
    top_f = max(r["f"] for r in grid)
    near = [r for r in grid if r["f"] >= 0.95 * top_f]
    best = max(near, key=lambda r: (r["min_count"], r["min_confidence"]))
    base = popularity_baseline(train, test)
    top_rows = sorted(grid, key=lambda r: -r["f"])[:8]
    table = md_table(top_rows, ["min_count", "min_confidence", "hit_rate@3", "precision@3", "coverage", "f", "frequent_itemsets"])
    summary = (f"Hold-out: {len(train)} train / {len(test)} test transactions (seed {seed}).\n\n"
               f"**Chosen thresholds:** min support = {best['min_count']} transactions, min confidence = "
               f"{best['min_confidence']} (lift > 1); most conservative setting within 5% of the best f.\n\n**Popularity baseline:** hit_rate@3 {base['hit_rate@3']}, "
               f"precision@3 {base['precision@3']} (always shows 3 items).\n\nTop settings by harmonic mean of "
               f"precision@3 and hit_rate@3:\n\n{table}")
    path = save_result("basket", {"chosen": best, "baseline_popularity": base, "grid": grid, "summary_md": summary})
    print(summary, f"\n-> {path}")
    return best


if __name__ == "__main__":
    run()

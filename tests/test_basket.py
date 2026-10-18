"""Apriori correctness (vs brute force) and the whole-cart recommendation rule."""
from __future__ import annotations

from itertools import combinations

from consultai.basket.apriori import BasketRecommender, apriori

TX = [frozenset(t) for t in (["a", "b", "c"], ["a", "b"], ["a", "c"], ["b", "c", "d"], ["a", "b", "c", "d"],
                             ["a", "d"], ["b", "d"], ["a", "b", "d"])]


def brute_force(tx, min_count):
    items = sorted({i for t in tx for i in t})
    out = {}
    for k in range(1, len(items) + 1):
        for combo in combinations(items, k):
            s = frozenset(combo)
            c = sum(s <= t for t in tx)
            if c >= min_count:
                out[s] = c
    return out


def test_apriori_matches_brute_force():
    for min_count in (1, 2, 3, 4):
        assert apriori(TX, min_count) == brute_force(TX, min_count)


def test_recommendations_use_whole_cart_and_rank_by_confidence():
    rec = BasketRecommender(TX, min_count=2, min_confidence=0.0)
    out = rec.recommend(["a", "b"])
    # {a,b} in 4 baskets; with c: 2, with d: 2 -> confidence 0.5 each; lift filter removes items with lift <= 1
    for r in out.recommendations:
        assert r.item not in ("a", "b")
        assert r.lift > 1
    assert [r.confidence for r in out.recommendations] == sorted((r.confidence for r in out.recommendations), reverse=True)


def test_unseen_combination_returns_nothing_without_subset_fallback():
    rec = BasketRecommender(TX, min_count=2, min_confidence=0.0)
    out = rec.recommend(["a", "c", "d"])                   # never bought together twice
    assert out.recommendations == [] and "no recommendation" in out.reason
    assert rec.recommend([]).recommendations == []

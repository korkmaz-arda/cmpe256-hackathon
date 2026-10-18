"""Apriori frequent-itemset mining (level-wise, with candidate pruning) and the checkout recommender.

Recommendation rule (professor's clarification, M2 07:00-13:40): recommendations are computed for the
WHOLE current cart. If the exact combination in the cart is not a frequent itemset in the history, or no
rule from it clears the thresholds, nothing is shown - there is no fallback to subsets of the cart.

For cart C, every frequent itemset I = C + {x} gives a rule C -> x with
  support    = count(I) / N
  confidence = count(I) / count(C)
  lift       = confidence / (count({x}) / N)
Rules are kept if confidence >= min_confidence and lift > 1, and ranked by confidence, then lift.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path


def load_transactions(path: Path) -> list[frozenset[str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))[1:]
    return [frozenset(i.strip() for i in r[1:] if i.strip()) for r in rows]


def apriori(transactions: list[frozenset[str]], min_count: int, max_len: int = 5) -> dict[frozenset[str], int]:
    """All itemsets appearing in at least `min_count` transactions, with their counts."""
    counts: dict[frozenset[str], int] = {}
    for t in transactions:
        for item in t:
            key = frozenset([item])
            counts[key] = counts.get(key, 0) + 1
    level = {s: c for s, c in counts.items() if c >= min_count}
    frequent = dict(level)
    k = 2
    while level and k <= max_len:
        prev = sorted(tuple(sorted(s)) for s in level)
        candidates = set()
        for i in range(len(prev)):
            for j in range(i + 1, len(prev)):
                if prev[i][:-1] != prev[j][:-1]:  # join step: same (k-2)-prefix
                    continue
                cand = frozenset(prev[i]) | frozenset(prev[j])
                # prune step: every (k-1)-subset must be frequent
                if all(frozenset(sub) in level for sub in combinations(sorted(cand), k - 1)):
                    candidates.add(cand)
        cand_counts = dict.fromkeys(candidates, 0)
        for t in transactions:
            if len(t) < k:
                continue
            for cand in candidates:
                if cand <= t:
                    cand_counts[cand] += 1
        level = {s: c for s, c in cand_counts.items() if c >= min_count}
        frequent.update(level)
        k += 1
    return frequent


@dataclass
class Recommendation:
    item: str
    support: float
    confidence: float
    lift: float
    count: int


@dataclass
class BasketResult:
    cart: list[str]
    recommendations: list[Recommendation] = field(default_factory=list)
    reason: str = ""


class BasketRecommender:
    def __init__(self, transactions: list[frozenset[str]], min_count: int, min_confidence: float):
        self.n = len(transactions)
        self.min_count = min_count
        self.min_confidence = min_confidence
        self.frequent = apriori(transactions, min_count)
        self.items = sorted({i for t in transactions for i in t})
        self.item_count = {i: sum(1 for t in transactions if i in t) for i in self.items}

    def recommend(self, cart: list[str] | set[str], k: int = 5) -> BasketResult:
        c = frozenset(cart)
        if not c:
            return BasketResult(list(cart), reason="Cart is empty.")
        base = self.frequent.get(c)
        if base is None:
            return BasketResult(sorted(c), reason=(f"This exact combination of {len(c)} item(s) is bought together in fewer "
                                                   f"than {self.min_count} historical transactions, so there is no reliable "
                                                   f"pattern; no recommendation is shown."))
        recs = []
        for itemset, count in self.frequent.items():
            if len(itemset) == len(c) + 1 and c < itemset:
                (x,) = itemset - c
                conf = count / base
                lift = conf / (self.item_count[x] / self.n)
                if conf >= self.min_confidence and lift > 1:
                    recs.append(Recommendation(x, round(count / self.n, 4), round(conf, 3), round(lift, 2), count))
        recs.sort(key=lambda r: (-r.confidence, -r.lift))
        if not recs:
            return BasketResult(sorted(c), reason=(f"The cart appears in {base} transactions, but no next item reaches "
                                                   f"confidence >= {self.min_confidence} with lift > 1; nothing is shown."))
        return BasketResult(sorted(c), recs[:k], reason=f"Cart appears in {base} transactions; rules C -> x ranked by confidence.")

from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class BasketRecommender:
    """Market Basket Checkout Recommender using level-wise Apriori association rules.

    This implementation adheres strictly to the full-cart rule: recommendations are
    generated ONLY from association rules whose antecedent is the ENTIRE current cart.
    There is no fallback to cart subsets and no fallback to overall item popularity.

    Default Thresholds Rationale:
        min_support_count = 2
        min_confidence = 0.05
        min_lift = 1.0

        These default thresholds are tailored for sparse retail transaction datasets
        (e.g., 1,000 transactions, 40 SKUs, 2-5 items per basket, near-uniform popularity
        around 75-105 transactions per SKU). In this dataset, the maximum pairwise
        co-occurrence is 16 transactions (p(A, B) = 0.016) and each item appears in ~9%
        of transactions (p(A) ≈ 0.09). Consequently, the maximum pairwise lift is
        0.016 / (0.09 * 0.09) ≈ 2.25, and typical confidence is around 16 / 90 ≈ 0.178.
        With standard textbook thresholds like min_confidence = 0.20 or min_lift = 3.0,
        virtually no rules would pass. A min_support_count of 2 (support = 0.002),
        min_confidence of 0.05, and min_lift of 1.0 preserve statistically valid
        positive associations while adapting to dataset sparsity.
    """

    def __init__(
        self,
        transactions: List[List[str]],
        min_support_count: int = 2,
        min_confidence: float = 0.05,
        min_lift: float = 1.0,
    ) -> None:
        """Initialize and train the Apriori model from a list of transactions.

        Args:
            transactions: List of baskets, where each basket is a list of item names.
            min_support_count: Minimum transaction count required for an itemset to be frequent.
            min_confidence: Minimum rule confidence (P(consequent | antecedent)).
            min_lift: Minimum rule lift (confidence / P(consequent)).
        """
        self.min_support_count = int(min_support_count)
        self.min_confidence = float(min_confidence)
        self.min_lift = float(min_lift)

        # Store transactions as frozensets of trimmed non-empty item names
        self._transactions: List[frozenset[str]] = [
            frozenset(x.strip() for x in t if x and str(x).strip())
            for t in transactions
        ]
        # Keep non-empty transactions
        self._transactions = [t for t in self._transactions if len(t) > 0]
        self.n_transactions: int = len(self._transactions)

        # Unique sorted list of all SKUs in the catalog
        all_skus: Set[str] = set()
        for t in self._transactions:
            all_skus.update(t)
        self.items: List[str] = sorted(list(all_skus))

        # Frequent itemsets: frozenset -> support_count
        self.frequent_itemsets: Dict[frozenset[str], int] = {}
        # Rules: list of dicts
        self.rules: List[Dict[str, Any]] = []
        # Fast lookup by antecedent frozenset
        self._rules_by_antecedent: Dict[frozenset[str], List[Dict[str, Any]]] = defaultdict(list)

        # Run level-wise Apriori and generate rules
        self._fit()

    @classmethod
    def from_csv(
        cls,
        path: Union[str, Path],
        min_support_count: int = 2,
        min_confidence: float = 0.05,
        min_lift: float = 1.0,
    ) -> BasketRecommender:
        """Construct and train a BasketRecommender from a retail CSV dataset.

        Args:
            path: Path to the CSV file with columns transaction_id,item_1..item_5.
            min_support_count: Minimum support count (default 2).
            min_confidence: Minimum confidence threshold (default 0.05).
            min_lift: Minimum lift threshold (default 1.0).

        Returns:
            Trained BasketRecommender instance.
        """
        csv_file = Path(path).resolve()
        if not csv_file.exists():
            raise FileNotFoundError(f"Market basket CSV file not found: {csv_file}")

        transactions: List[List[str]] = []
        with open(csv_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                # Column 0 is transaction_id; columns 1..end are item_1..item_5
                items = [cell.strip() for cell in row[1:] if cell and cell.strip()]
                if items:
                    transactions.append(items)

        return cls(
            transactions=transactions,
            min_support_count=min_support_count,
            min_confidence=min_confidence,
            min_lift=min_lift,
        )

    def _fit(self) -> None:
        """Run level-wise Apriori candidate generation, pruning, and rule extraction."""
        if self.n_transactions == 0:
            return

        # Build inverted index: item -> set of transaction indices for fast counting
        item_to_tids: Dict[str, Set[int]] = {item: set() for item in self.items}
        for tid, basket in enumerate(self._transactions):
            for item in basket:
                item_to_tids[item].add(tid)

        # -------------------------------------------------------------
        # Step 1: L1 Frequent 1-itemsets
        # -------------------------------------------------------------
        current_l: Dict[frozenset[str], int] = {}
        for item in self.items:
            count = len(item_to_tids[item])
            if count >= self.min_support_count:
                current_l[frozenset([item])] = count

        self.frequent_itemsets.update(current_l)

        # -------------------------------------------------------------
        # Step 2: Level-wise generation for k >= 2
        # -------------------------------------------------------------
        k = 2
        while current_l:
            # Sort frequent (k-1)-itemsets lexicographically to enable prefix joins
            prev_itemsets = sorted([sorted(list(s)) for s in current_l.keys()])
            candidates_k: List[frozenset[str]] = []
            num_prev = len(prev_itemsets)

            # Candidate generation: join L_{k-1} with L_{k-1}
            for i in range(num_prev):
                itemset1 = prev_itemsets[i]
                prefix1 = itemset1[:-1]
                last1 = itemset1[-1]

                for j in range(i + 1, num_prev):
                    itemset2 = prev_itemsets[j]
                    prefix2 = itemset2[:-1]
                    last2 = itemset2[-1]

                    # Prefix matching: if prefixes do not match, we can stop checking subsequent j
                    if prefix1 != prefix2:
                        break

                    # Form candidate k-itemset
                    candidate_tuple = tuple(itemset1 + [last2])
                    candidate_set = frozenset(candidate_tuple)

                    # Apriori pruning: all (k-1) subsets must be frequent in current_l
                    all_subsets_frequent = True
                    for sub in combinations(candidate_tuple, k - 1):
                        if frozenset(sub) not in current_l:
                            all_subsets_frequent = False
                            break

                    if all_subsets_frequent:
                        candidates_k.append(candidate_set)

            # Candidate counting using inverted index intersection
            next_l: Dict[frozenset[str], int] = {}
            for cand in candidates_k:
                # Intersect transaction sets for all items in candidate
                cand_items = list(cand)
                matching_tids = item_to_tids[cand_items[0]]
                for cand_item in cand_items[1:]:
                    matching_tids = matching_tids.intersection(item_to_tids[cand_item])
                    if not matching_tids:
                        break

                supp_count = len(matching_tids)
                if supp_count >= self.min_support_count:
                    next_l[cand] = supp_count

            # Add frequent k-itemsets to catalog
            self.frequent_itemsets.update(next_l)
            current_l = next_l
            k += 1

        # -------------------------------------------------------------
        # Step 3: Association Rule Mining (consequent size = 1)
        # For checkout recommendation, we extract rules A -> {y} where
        # A = itemset \ {y} and |{y}| = 1.
        # -------------------------------------------------------------
        for itemset, supp_count in self.frequent_itemsets.items():
            if len(itemset) < 2:
                continue

            supp = supp_count / self.n_transactions

            # For every item y in the frequent itemset, consider A = itemset - {y}
            for y in itemset:
                antecedent = itemset - frozenset([y])
                antecedent_count = self.frequent_itemsets.get(antecedent, 0)
                if antecedent_count == 0:
                    continue

                confidence = supp_count / antecedent_count
                y_count = self.frequent_itemsets.get(frozenset([y]), 0)
                if y_count == 0:
                    continue

                y_supp = y_count / self.n_transactions
                lift = confidence / y_supp if y_supp > 0 else 0.0

                if confidence >= self.min_confidence and lift >= self.min_lift:
                    rule_entry = {
                        "antecedent": antecedent,
                        "consequent": frozenset([y]),
                        "item": y,
                        "support_count": supp_count,
                        "support": supp,
                        "confidence": confidence,
                        "lift": lift,
                        "rule": f"{', '.join(sorted(antecedent))} -> {y}",
                    }
                    self.rules.append(rule_entry)
                    self._rules_by_antecedent[antecedent].append(rule_entry)

    def recommend(self, cart: List[str], k: int = 5) -> List[Dict[str, Any]]:
        """Recommend items for the given cart using strict full-cart Apriori rules.

        Rule 3 Enforcement:
            Recommends ONLY from rules whose antecedent is the ENTIRE current cart.
            No subset matching and no popularity fallbacks. If no frequent itemset
            contains the full cart plus a candidate item passing the thresholds,
            an empty list is returned.

        Rule 4 Enforcement:
            Never recommends an item already present in the cart.

        Args:
            cart: List of product SKU strings currently in the shopper's cart.
            k: Maximum number of recommendations to return (default 5).

        Returns:
            List of dicts with keys:
                item (str), support_count (int), support (float),
                confidence (float), lift (float), antecedent (list[str]).
            Sorted by confidence desc, lift desc, support desc, and item asc.
        """
        if not cart or k <= 0:
            return []

        # Deduplicate and normalize cart items
        cleaned_cart = [item.strip() for item in cart if item and item.strip()]
        cart_set = frozenset(cleaned_cart)
        if not cart_set:
            return []

        # Look up candidate rules matching the ENTIRE cart as antecedent
        candidate_rules = self._rules_by_antecedent.get(cart_set, [])
        if not candidate_rules:
            return []

        # Ensure no recommended item is already in the cart (Rule 4)
        valid_rules = [r for r in candidate_rules if r["item"] not in cart_set]
        if not valid_rules:
            return []

        # Sort by confidence desc, then lift desc, then support desc, then item name asc
        sorted_rules = sorted(
            valid_rules,
            key=lambda r: (-r["confidence"], -r["lift"], -r["support"], r["item"]),
        )

        # Return formatted dictionaries with antecedent as a list (per spec)
        antecedent_list = sorted(list(cart_set))
        results: List[Dict[str, Any]] = []
        for r in sorted_rules[:k]:
            results.append(
                {
                    "item": r["item"],
                    "support_count": r["support_count"],
                    "support": r["support"],
                    "confidence": r["confidence"],
                    "lift": r["lift"],
                    "antecedent": list(antecedent_list),
                }
            )

        return results

    def explain(self, cart: List[str]) -> Dict[str, Any]:
        """Explain the recommender's decision or lack of recommendations for a cart.

        Args:
            cart: List of product SKU strings currently in the shopper's cart.

        Returns:
            Dict containing:
                cart_support_count (int): Frequency of the cart combination in the dataset.
                reason (str): Human-readable explanation of why recommendations were or
                              were not produced. When no recommendations exist, explicitly
                              states 'No recommendation: no purchase pattern for this cart combination'.
        """
        if not cart:
            return {
                "cart_support_count": 0,
                "reason": "Cart is empty. Please add items to receive checkout recommendations.",
            }

        cleaned_cart = [item.strip() for item in cart if item and item.strip()]
        cart_set = frozenset(cleaned_cart)
        if not cart_set:
            return {
                "cart_support_count": 0,
                "reason": "Cart is empty. Please add items to receive checkout recommendations.",
            }

        # Determine support count of the cart itself
        if cart_set in self.frequent_itemsets:
            cart_support_count = self.frequent_itemsets[cart_set]
        else:
            cart_support_count = sum(1 for t in self._transactions if cart_set.issubset(t))

        recs = self.recommend(cart)
        if recs:
            return {
                "cart_support_count": cart_support_count,
                "reason": (
                    f"Found {len(recs)} recommendation(s) matching the full cart pattern "
                    f"(cart support count: {cart_support_count})."
                ),
            }

        # Handle empty recommendations according to Rule 3
        if cart_support_count == 0:
            reason = (
                "No recommendation: no purchase pattern for this cart combination "
                "(cart items never co-occur in transaction history)."
            )
        elif cart_support_count < self.min_support_count:
            reason = (
                f"No recommendation: no purchase pattern for this cart combination "
                f"(cart combination appears {cart_support_count} time(s), below min_support_count={self.min_support_count})."
            )
        else:
            reason = (
                f"No recommendation: no purchase pattern for this cart combination "
                f"(cart combination appears {cart_support_count} time(s), but no extension meets "
                f"min_support_count={self.min_support_count}, min_confidence={self.min_confidence}, or min_lift={self.min_lift})."
            )

        return {
            "cart_support_count": cart_support_count,
            "reason": reason,
        }

from __future__ import annotations

from pathlib import Path
from typing import List

from app.basket.apriori import BasketRecommender


def get_dataset_path() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "data" / "Retail" / "CMPE256_Hackathon_market_basket_analysis_Release.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Retail dataset not found at expected path: {csv_path}")
    return csv_path


def test_empty_cart() -> None:
    """Empty cart must always return an empty list of recommendations."""
    csv_path = get_dataset_path()
    model = BasketRecommender.from_csv(csv_path, min_support_count=2, min_confidence=0.05, min_lift=1.0)
    recs = model.recommend([])
    assert recs == [], f"Expected empty list for empty cart, got {recs}"

    exp = model.explain([])
    assert exp["cart_support_count"] == 0
    assert "Cart is empty" in exp["reason"]
    print("✓ test_empty_cart passed")


def test_recommend_never_returns_cart_items() -> None:
    """Recommendations must NEVER contain any item currently in the cart (Rule 4)."""
    csv_path = get_dataset_path()
    model = BasketRecommender.from_csv(csv_path, min_support_count=2, min_confidence=0.05, min_lift=1.0)

    # Test single-item carts for the first 10 items in catalog
    for item in model.items[:10]:
        cart = [item]
        recs = model.recommend(cart, k=10)
        for r in recs:
            assert r["item"] not in cart, f"Recommended item '{r['item']}' is already in cart {cart}"
            assert r["item"] != item, f"Recommended item '{r['item']}' matches cart item '{item}'"

    print("✓ test_recommend_never_returns_cart_items passed")


def test_cart_never_cooccurring_items() -> None:
    """A cart of two items that never co-occur in the database must return []."""
    csv_path = get_dataset_path()
    model = BasketRecommender.from_csv(csv_path, min_support_count=2, min_confidence=0.05, min_lift=1.0)

    # Dynamically locate a pair of items that have 0 co-occurrences in transactions
    disjoint_pair = None
    for i, item1 in enumerate(model.items):
        for item2 in model.items[i + 1 :]:
            pair = frozenset([item1, item2])
            if pair not in model.frequent_itemsets:
                # Double-check co-occurrence in raw transactions is strictly 0
                actual_count = sum(1 for t in model._transactions if pair.issubset(t))
                if actual_count == 0:
                    disjoint_pair = [item1, item2]
                    break
        if disjoint_pair:
            break

    assert disjoint_pair is not None, "Expected to find at least one disjoint item pair in catalog"
    recs = model.recommend(disjoint_pair, k=5)
    assert recs == [], f"Expected [] for disjoint pair {disjoint_pair}, got {recs}"

    exp = model.explain(disjoint_pair)
    assert exp["cart_support_count"] == 0, f"Expected cart_support_count=0, got {exp['cart_support_count']}"
    assert "No recommendation: no purchase pattern for this cart combination" in exp["reason"]
    print(f"✓ test_cart_never_cooccurring_items passed (tested disjoint pair: {disjoint_pair})")


def test_full_cart_rule_property() -> None:
    """Every recommended item must co-occur with the ENTIRE cart at least min_support_count times."""
    csv_path = get_dataset_path()
    min_sup = 2
    min_conf = 0.05
    min_lft = 1.0
    model = BasketRecommender.from_csv(
        csv_path,
        min_support_count=min_sup,
        min_confidence=min_conf,
        min_lift=min_lft,
    )

    # Test recommendations across multiple active carts
    test_carts: List[List[str]] = [
        ["Bosch D7050 Detector (SKU: D7050)"],
        [model.items[0]],
        [model.items[5]],
    ]

    for cart in test_carts:
        recs = model.recommend(cart, k=5)
        cart_set = frozenset(cart)
        for r in recs:
            rec_item = r["item"]
            full_set = cart_set | frozenset([rec_item])

            # Property 1: Must be in frequent_itemsets
            assert full_set in model.frequent_itemsets, (
                f"Full set {full_set} is not in frequent itemsets!"
            )

            # Property 2: Actual co-occurrence count in transactions must be >= min_support_count
            raw_cooccurrence = sum(1 for t in model._transactions if full_set.issubset(t))
            assert raw_cooccurrence >= min_sup, (
                f"Raw co-occurrence {raw_cooccurrence} < min_support_count {min_sup} for {full_set}"
            )
            assert r["support_count"] == raw_cooccurrence

            # Property 3: Thresholds must be satisfied
            assert r["confidence"] >= min_conf - 1e-9, f"Confidence {r['confidence']} < {min_conf}"
            assert r["lift"] >= min_lft - 1e-9, f"Lift {r['lift']} < {min_lft}"

            # Property 4: Antecedent in result must equal the cart
            assert sorted(r["antecedent"]) == sorted(cart)

    print("✓ test_full_cart_rule_property passed")


def test_demo_path_from_slides() -> None:
    """Verify the professor's exact demo sequence from the lecture slides:
    Step 1: 'Bosch D7050 Detector (SKU: D7050)' -> recommendations.
    Step 2: Add 'DSC PG9914 Motion Detector (SKU: PG9914)' -> pair co-occurs 5 times,
            but each other item co-occurs at most once -> returns [] (empty list).
    """
    csv_path = get_dataset_path()
    model = BasketRecommender.from_csv(csv_path, min_support_count=2, min_confidence=0.05, min_lift=1.0)

    item1 = "Bosch D7050 Detector (SKU: D7050)"
    item2 = "DSC PG9914 Motion Detector (SKU: PG9914)"

    # Step 1: Single item in cart
    cart_step1 = [item1]
    recs_step1 = model.recommend(cart_step1, k=5)
    exp_step1 = model.explain(cart_step1)

    assert len(recs_step1) > 0, "Step 1 should produce recommendations"
    assert exp_step1["cart_support_count"] > 0
    for r in recs_step1:
        assert r["item"] != item1

    # Step 2: Add second item breaking the pattern
    cart_step2 = [item1, item2]
    recs_step2 = model.recommend(cart_step2, k=5)
    exp_step2 = model.explain(cart_step2)

    # Co-occurrence of this pair is 5 in the dataset
    assert exp_step2["cart_support_count"] == 5, (
        f"Expected cart support count of 5 for [D7050, PG9914], got {exp_step2['cart_support_count']}"
    )
    # But no third item appears >= 2 times with this pair -> []
    assert recs_step2 == [], f"Expected empty recommendations for {cart_step2}, got {recs_step2}"
    assert "No recommendation: no purchase pattern for this cart combination" in exp_step2["reason"]

    print("✓ test_demo_path_from_slides passed (Step 1 -> recs found, Step 2 -> [] as expected)")


def test_sorting_order() -> None:
    """Recommendations must be sorted by confidence desc, lift desc, support desc."""
    csv_path = get_dataset_path()
    model = BasketRecommender.from_csv(csv_path, min_support_count=2, min_confidence=0.05, min_lift=1.0)

    for item in model.items[:15]:
        recs = model.recommend([item], k=10)
        if len(recs) <= 1:
            continue
        for i in range(len(recs) - 1):
            curr = recs[i]
            nxt = recs[i + 1]
            # Primary sort: confidence desc
            if curr["confidence"] != nxt["confidence"]:
                assert curr["confidence"] >= nxt["confidence"]
            # Secondary sort: lift desc
            elif curr["lift"] != nxt["lift"]:
                assert curr["lift"] >= nxt["lift"]
            # Tertiary sort: support desc
            else:
                assert curr["support"] >= nxt["support"]

    print("✓ test_sorting_order passed")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("RUNNING BASKET RECOMMENDER UNIT TESTS")
    print("=" * 50)
    test_empty_cart()
    test_recommend_never_returns_cart_items()
    test_cart_never_cooccurring_items()
    test_full_cart_rule_property()
    test_demo_path_from_slides()
    test_sorting_order()
    print("=" * 50)
    print("ALL TESTS PASSED SUCCESSFULLY! (6/6)")
    print("=" * 50 + "\n")

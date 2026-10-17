from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from app.basket.apriori import BasketRecommender


@st.cache_resource
def load_recommender(
    csv_path: str,
    min_support_count: int,
    min_confidence: float,
    min_lift: float,
) -> BasketRecommender:
    """Load and train BasketRecommender model, cached by threshold parameters."""
    return BasketRecommender.from_csv(
        path=csv_path,
        min_support_count=min_support_count,
        min_confidence=min_confidence,
        min_lift=min_lift,
    )


def render() -> None:
    """Render the Market Basket Checkout Recommender tab component."""
    # Resolve CSV data path relative to project root
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "data" / "Retail" / "CMPE256_Hackathon_market_basket_analysis_Release.csv"

    # Initialize cart in session state under key 'basket_cart'
    if "basket_cart" not in st.session_state:
        st.session_state.basket_cart = []

    # Expander with active thresholds and sliders to rebuild the model
    with st.expander("⚙️ Recommender Model Thresholds & Parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            min_support_count = st.slider(
                "Min Support Count",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
                help="Minimum number of transactions required for an itemset to be frequent (default: 2).",
            )
        with c2:
            min_confidence = st.slider(
                "Min Confidence",
                min_value=0.01,
                max_value=0.50,
                value=0.05,
                step=0.01,
                help="Minimum rule confidence threshold P(consequent | antecedent) (default: 0.05).",
            )
        with c3:
            min_lift = st.slider(
                "Min Lift",
                min_value=0.5,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help="Minimum rule lift threshold confidence / P(consequent) (default: 1.0).",
            )

        st.caption(
            "💡 *Dataset Threshold Rationale: 1,000 transactions, 40 SKUs, max co-occurrence 16 (max pair lift ≈ 2.25). "
            "Thresholds like confidence ≥ 0.20 or lift ≥ 3.0 filter out virtually all valid patterns. "
            "Defaults (count=2, conf=0.05, lift=1.0) adapt to retail sparsity while ensuring positive association.*"
        )

    # Load cached recommender model
    model = load_recommender(
        csv_path=str(csv_path),
        min_support_count=min_support_count,
        min_confidence=min_confidence,
        min_lift=min_lift,
    )

    # Top layout: left = product catalog; right = shopping cart
    col_catalog, col_cart = st.columns([1, 1], gap="large")

    with col_catalog:
        st.subheader("🛒 Product Catalog")
        st.write("Select an item from the full catalog to add to your cart:")

        selected_sku = st.selectbox(
            "Select product:",
            options=model.items,
            key="basket_sku_selector",
            label_visibility="collapsed",
        )

        col_add, col_d1, col_d2 = st.columns([1.3, 1, 1])
        with col_add:
            if st.button("➕ Add Item", key="add_sku_button", width="stretch"):
                if selected_sku not in st.session_state.basket_cart:
                    st.session_state.basket_cart.append(selected_sku)
                    st.rerun()
                else:
                    st.warning(f"Item '{selected_sku}' is already in your cart.")

        with col_d1:
            if st.button("🎬 Demo 1", key="btn_demo_step1", width="stretch", help="Load 'Bosch D7050 Detector'"):
                st.session_state.basket_cart = ["Bosch D7050 Detector (SKU: D7050)"]
                st.rerun()

        with col_d2:
            if st.button("🎬 Demo 2", key="btn_demo_step2", width="stretch", help="Add 'DSC PG9914' to break pattern"):
                st.session_state.basket_cart = [
                    "Bosch D7050 Detector (SKU: D7050)",
                    "DSC PG9914 Motion Detector (SKU: PG9914)",
                ]
                st.rerun()

    with col_cart:
        st.subheader("🛍️ Added Items to Cart")
        if not st.session_state.basket_cart:
            st.info("Your cart is currently empty. Select an item from the catalog to see recommendations.")
        else:
            for idx, item in enumerate(st.session_state.basket_cart):
                c_name, c_del = st.columns([4, 1])
                with c_name:
                    st.markdown(f"**{idx + 1}.** {item}")
                with c_del:
                    if st.button("🗑️", key=f"remove_sku_{idx}", help=f"Remove '{item}'"):
                        st.session_state.basket_cart.pop(idx)
                        st.rerun()

            if st.button("Clear Cart", key="clear_cart_action", type="secondary"):
                st.session_state.basket_cart = []
                st.rerun()

    # Bottom layout: Recommended Items table
    st.markdown("---")
    st.subheader("💡 Recommended Items (Checkout Suggestions)")

    cart: List[str] = st.session_state.basket_cart
    if not cart:
        st.caption("No items in cart. Recommendations will automatically appear as you add products.")
        return

    # Generate recommendations and explanation
    recommendations = model.recommend(cart, k=5)
    explanation = model.explain(cart)

    if recommendations:
        st.success(f"**Pattern Found:** {explanation['reason']}")

        table_rows = []
        for r in recommendations:
            rule_str = f"[{' + '.join(r['antecedent'])}] ➔ {r['item']}"
            table_rows.append(
                {
                    "Item": r["item"],
                    "Confidence": f"{r['confidence'] * 100:.1f}%",
                    "Lift": f"{r['lift']:.2f}x",
                    "Support Count": r["support_count"],
                    "Rule": rule_str,
                }
            )

        df = pd.DataFrame(table_rows)
        st.dataframe(df, width="stretch", hide_index=True)
        st.caption("ℹ️ *Sorted by confidence desc, lift desc, support count desc. Antecedent is strictly the full cart.*")
    else:
        st.warning(f"**{explanation['reason']}**")
        st.caption(
            "ℹ️ *Professor's Rule 3: Recommendations require an exact match with the ENTIRE current cart. "
            "No fallback to subsets of the cart and no popularity fallback.*"
        )

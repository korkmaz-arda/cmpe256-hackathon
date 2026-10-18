"""Market Basket tab: the slide's checkout portal (item list -> Add Item -> cart -> Recommended Items)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from consultai.basket.apriori import BasketRecommender, load_transactions
from consultai.eval.basket import transactions_path
from consultai.eval.common import load_result

DEFAULT = {"min_count": 6, "min_confidence": 0.1}


@st.cache_resource
def recommender(min_count: int, min_conf: float) -> BasketRecommender:
    return BasketRecommender(load_transactions(transactions_path()), min_count, min_conf)


def render() -> None:
    st.subheader("Electronic Item Checkout Portal - next-item recommendations (Apriori)")
    res = load_result("basket")
    chosen = (res or {}).get("chosen", DEFAULT)
    c1, c2 = st.columns(2)
    min_count = c1.number_input("Min support (transactions)", 1, 50, int(chosen["min_count"]))
    min_conf = c2.number_input("Min confidence", 0.0, 1.0, float(chosen["min_confidence"]), step=0.01)
    st.caption("Defaults come from the hold-out evaluation (Evaluation tab). Recommendations use the WHOLE cart: if this "
               "exact combination has no frequent pattern, nothing is shown (no fallback to parts of the cart).")
    rec = recommender(int(min_count), float(min_conf))
    cart: list[str] = st.session_state.setdefault("cart", [])

    left, right = st.columns([1, 1])
    with right:
        item = st.selectbox("Select item from the list", rec.items)
        b1, b2 = st.columns(2)
        if b1.button("Add Item", type="primary") and item not in cart:
            cart.append(item)
        if b2.button("Empty cart"):
            cart.clear()
    with left:
        st.markdown("**Added items to cart:**")
        st.markdown("\n".join(f"{n}. {i}" for n, i in enumerate(cart, 1)) or "_cart is empty_")

    st.markdown("**Recommended items:**")
    if cart:
        out = rec.recommend(cart, k=5)
        if out.recommendations:
            st.dataframe(pd.DataFrame([{"recommended item": r.item, "confidence": r.confidence, "lift": r.lift,
                                        "support": r.support, "baskets with cart + item": r.count}
                                       for r in out.recommendations]), hide_index=True, width="stretch")
        st.caption(out.reason)
    else:
        st.caption("Add an item to see what is usually bought with it.")
    if res:
        with st.expander("How well does it work? (hold-out evaluation)"):
            st.markdown(res["summary_md"])

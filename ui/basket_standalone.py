from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path when running as a standalone script
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from ui.basket_tab import render

st.set_page_config(
    page_title="Market Basket Recommender | CMPE 256",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Market Basket Checkout Recommender")
st.caption("CMPE 256 Recommender Systems — Level-Wise Apriori Full-Cart Checkout Engine")

render()

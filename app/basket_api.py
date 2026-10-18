"""Market-basket recommender as a FastAPI microservice (checkout integration).

    uvicorn app.basket_api:app --port 8001

GET  /health                       model status and thresholds
GET  /items                        all sellable items
GET  /recommend?item=A&item=B&k=5  next-item recommendations for the whole cart (empty list if no pattern)
POST /recommend {"cart": [...], "k": 5}
GET  /metrics                      request count, share of carts that got recommendations
POST /retrain                      rebuild the model from the transaction file (e.g. after new data)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from consultai.basket.apriori import BasketRecommender, load_transactions  # noqa: E402
from consultai.eval.basket import transactions_path  # noqa: E402
from consultai.eval.common import load_result  # noqa: E402

app = FastAPI(title="Market Basket Recommender", version="1.0")
state: dict = {"requests": 0, "with_recommendations": 0}


def _train() -> None:
    chosen = (load_result("basket") or {}).get("chosen", {"min_count": 6, "min_confidence": 0.1})
    state["model"] = BasketRecommender(load_transactions(transactions_path()), int(chosen["min_count"]),
                                       float(chosen["min_confidence"]))
    state["trained_at"] = time.strftime("%Y-%m-%d %H:%M:%S")


def _model() -> BasketRecommender:
    if "model" not in state:
        _train()
    return state["model"]


def _recommend(cart: list[str], k: int) -> dict:
    out = _model().recommend(cart, k=k)
    state["requests"] += 1
    state["with_recommendations"] += bool(out.recommendations)
    return {"cart": out.cart, "recommendations": [r.__dict__ for r in out.recommendations], "reason": out.reason}


class CartRequest(BaseModel):
    cart: list[str]
    k: int = 5


@app.get("/health")
def health() -> dict:
    m = _model()
    return {"status": "ok", "transactions": m.n, "items": len(m.items), "min_support_count": m.min_count,
            "min_confidence": m.min_confidence, "trained_at": state["trained_at"]}


@app.get("/items")
def items() -> list[str]:
    return _model().items


@app.get("/recommend")
def recommend_get(item: list[str] = Query(default=[]), k: int = 5) -> dict:
    return _recommend(item, k)


@app.post("/recommend")
def recommend_post(req: CartRequest) -> dict:
    return _recommend(req.cart, req.k)


@app.get("/metrics")
def metrics() -> dict:
    n = state["requests"]
    return {"requests": n, "share_with_recommendations": round(state["with_recommendations"] / n, 3) if n else None}


@app.post("/retrain")
def retrain() -> dict:
    _train()
    return health()

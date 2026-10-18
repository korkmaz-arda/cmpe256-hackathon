"""Local embedding and reranking models (no external API; Claude has no embedding endpoint).

* Dense retrieval: BAAI/bge-base-en-v1.5 (768-d, cosine). Queries get bge's retrieval instruction.
* Reranking:       BAAI/bge-reranker-base cross-encoder over (query, passage) pairs.
Models are downloaded once from the Hugging Face hub and cached; they run on the GPU when present.
"""
from __future__ import annotations

import threading
from functools import lru_cache

import numpy as np

from consultai.config import settings

BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
_lock = threading.Lock()


def _device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache
def embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings()["retrieval"]["embed_model"], device=_device())


@lru_cache
def reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(settings()["retrieval"]["rerank_model"], device=_device(), max_length=512)


def embed_passages(texts: list[str], batch_size: int = 64) -> np.ndarray:
    with _lock:
        vecs = embedder().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 show_progress_bar=len(texts) > 2000, convert_to_numpy=True)
    return vecs.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    with _lock:
        vec = embedder().encode([BGE_QUERY_INSTRUCTION + query], normalize_embeddings=True, convert_to_numpy=True)
    return vec[0].astype(np.float32)


def rerank_scores(query: str, passages: list[str]) -> np.ndarray:
    if not passages:
        return np.zeros(0, dtype=np.float32)
    with _lock:
        scores = reranker().predict([(query, p) for p in passages], batch_size=32, show_progress_bar=False)
    return np.asarray(scores, dtype=np.float32)

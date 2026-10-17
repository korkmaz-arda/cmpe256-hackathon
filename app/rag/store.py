"""Per-domain hybrid retrieval store: dense embeddings + BM25, fused with reciprocal rank fusion."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from app import config, llm

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("the a an and or of to in for on with by is are was were be as at from that this it its".split())


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class DomainStore:
    """Chunks for one domain: `chunks.json` (text + metadata) and `vectors.npy` (normalised embeddings)."""

    def __init__(self, domain: str, root: Path = config.INDEX):
        self.domain = domain
        folder = root / domain
        self.chunks: list[dict] = json.loads((folder / "chunks.json").read_text())
        self.vectors = np.load(folder / "vectors.npy")
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])

    def search(self, query: str, k: int = 6, filters: dict | None = None, pool: int = 40) -> list[dict]:
        """Hybrid search. `filters` keeps chunks whose metadata matches every given key
        (case-insensitive; a list value means "any of")."""
        mask = np.ones(len(self.chunks), dtype=bool)
        for key, want in (filters or {}).items():
            if want in (None, "", []):
                continue
            wants = {str(w).lower() for w in (want if isinstance(want, list) else [want])}
            mask &= np.array([str(c.get(key, "")).lower() in wants for c in self.chunks])
        if not mask.any():
            return []

        with np.errstate(all="ignore"):  # numpy+Accelerate emits spurious matmul warnings on macOS
            dense = (self.vectors @ llm.embed([query])[0]).astype(np.float64)
        sparse = np.asarray(self.bm25.get_scores(tokenize(query)))
        dense[~mask] = -np.inf
        sparse[~mask] = -np.inf

        # Reciprocal rank fusion: robust to the very different scales of cosine and BM25.
        fused: dict[int, float] = {}
        for scores in (dense, sparse):
            for rank, idx in enumerate(np.argsort(-scores)[:pool]):
                if np.isfinite(scores[idx]):
                    fused[idx] = fused.get(idx, 0.0) + 1.0 / (60 + rank)

        best = sorted(fused, key=fused.get, reverse=True)[:k]
        results = []
        for idx in best:
            c = dict(self.chunks[idx])
            c["cosine"] = round(float(dense[idx]), 4)
            c["bm25"] = round(float(sparse[idx]), 3)
            c["rrf"] = round(fused[idx], 5)
            results.append(c)
        return results

    def stats(self) -> dict:
        docs: dict[str, int] = {}
        for c in self.chunks:
            docs[c["title"]] = docs.get(c["title"], 0) + 1
        return {"chunks": len(self.chunks), "documents": docs}


@lru_cache(maxsize=None)
def get_store(domain: str) -> DomainStore:
    return DomainStore(domain)


def available_domains() -> list[str]:
    return [d for d in config.DOMAINS if (config.INDEX / d / "vectors.npy").exists()]

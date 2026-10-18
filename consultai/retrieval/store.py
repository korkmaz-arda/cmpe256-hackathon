"""Per-collection index: chunk records + dense vectors + BM25, searched with metadata filters.

Search modes (compared in the retrieval evaluation, chosen in config/settings.yaml):
  bm25           lexical only (good for part numbers such as C8300-1N1S-6T, NCT ids, Item numbers)
  dense          bge embeddings only (good for paraphrases)
  hybrid         reciprocal-rank fusion (RRF) of the two lists
  hybrid_rerank  RRF candidates re-scored by the bge cross-encoder
Every hit carries all of its scores, so an agent's evidence shows *why* it was retrieved.
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

import numpy as np
from rank_bm25 import BM25Okapi

from consultai.config import INDEX_DIR, settings
from consultai.retrieval import models

_TOKEN = re.compile(r"[a-z0-9]+(?:[-./][a-z0-9]+)*")
_STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were will with".split())


def tokenize(text: str) -> list[str]:
    toks = []
    for t in _TOKEN.findall(text.lower()):
        if t in _STOP:
            continue
        toks.append(t)
        if "-" in t or "/" in t:  # index PIDs both whole and by part: c8300-1n1s-6t, c8300, 1n1s, 6t
            toks.extend(p for p in re.split(r"[-/]", t) if p and p not in _STOP)
    return toks


@dataclass
class Hit:
    chunk: dict
    scores: dict = field(default_factory=dict)  # bm25, dense, rrf, rerank (whichever were computed)
    rank: int = 0


class Collection:
    def __init__(self, name: str):
        self.name = name
        base = INDEX_DIR / name
        if not (base / "chunks.jsonl").exists():
            raise FileNotFoundError(f"Index '{name}' not built. Run: python -m consultai.ingest.build")
        self.chunks: list[dict] = [json.loads(l) for l in (base / "chunks.jsonl").open()]
        self.vectors: np.ndarray = np.load(base / "vectors.npy")
        self.info: dict = json.loads((base / "info.json").read_text())
        self.by_id = {c["chunk_id"]: i for i, c in enumerate(self.chunks)}
        self._bm25: BM25Okapi | None = None
        self._lock = threading.Lock()

    @property
    def bm25(self) -> BM25Okapi:
        with self._lock:
            if self._bm25 is None:
                self._bm25 = BM25Okapi([tokenize(c["index_text"]) for c in self.chunks])
            return self._bm25

    def __len__(self) -> int:
        return len(self.chunks)

    def search(self, query: str, k: int = 8, mode: str | None = None,
               where: Callable[[dict], bool] | None = None) -> list[Hit]:
        cfg = settings()["retrieval"]
        mode = mode or cfg["mode"]
        mask = np.ones(len(self.chunks), dtype=bool)
        if where is not None:
            mask = np.array([bool(where(c)) for c in self.chunks])
        if not mask.any():
            return []
        n_cand = max(cfg["candidates"], k)
        scores: dict[str, np.ndarray] = {}
        ranked: dict[str, list[int]] = {}

        if mode in ("bm25", "hybrid", "hybrid_rerank"):
            s = np.asarray(self.bm25.get_scores(tokenize(query)), dtype=np.float32)
            s[~mask] = -np.inf
            scores["bm25"] = s
            ranked["bm25"] = [i for i in np.argsort(-s)[:n_cand] if np.isfinite(s[i]) and s[i] > 0]
        if mode in ("dense", "hybrid", "hybrid_rerank"):
            s = self.vectors @ models.embed_query(query)
            s[~mask] = -np.inf
            scores["dense"] = s
            ranked["dense"] = [i for i in np.argsort(-s)[:n_cand] if np.isfinite(s[i])]

        if mode in ("bm25", "dense"):
            order = ranked[mode][:k]
            rrf = {}
        else:
            rrf_k = cfg["rrf_k"]
            rrf: dict[int, float] = {}
            for lst in ranked.values():
                for r, i in enumerate(lst):
                    rrf[i] = rrf.get(i, 0.0) + 1.0 / (rrf_k + r + 1)
            order = sorted(rrf, key=rrf.get, reverse=True)[:n_cand]

        rerank: dict[int, float] = {}
        if mode == "hybrid_rerank" and order:
            rs = models.rerank_scores(query, [self.chunks[i]["index_text"] for i in order])
            rerank = dict(zip(order, rs.tolist()))
            order = sorted(order, key=rerank.get, reverse=True)
        order = order[:k]

        hits = []
        for r, i in enumerate(order, start=1):
            sc = {name: round(float(arr[i]), 4) for name, arr in scores.items() if np.isfinite(arr[i])}
            if i in rrf:
                sc["rrf"] = round(rrf[i], 5)
            if i in rerank:
                sc["rerank"] = round(rerank[i], 4)
            hits.append(Hit(self.chunks[i], sc, r))
        return hits

    def get(self, chunk_id: str) -> dict | None:
        i = self.by_id.get(chunk_id)
        return self.chunks[i] if i is not None else None

    def page_chunks(self, source_id: str, page: int) -> list[dict]:
        return [c for c in self.chunks if c["source_id"] == source_id and c.get("page") == page]


@lru_cache
def collection(name: str) -> Collection:
    return Collection(name)

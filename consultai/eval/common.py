"""Shared helpers for the evaluation scripts."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from consultai.config import EVAL_RESULTS_DIR

DATASETS = Path(__file__).parent / "datasets"


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(l) for l in (DATASETS / name).read_text().splitlines() if l.strip()]


def save_result(name: str, payload: dict) -> Path:
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), **payload}
    path = EVAL_RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return path


def load_result(name: str) -> dict | None:
    path = EVAL_RESULTS_DIR / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def dcg(rels: list[int]) -> float:
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(rels: list[int], n_relevant: int, k: int) -> float:
    ideal = dcg([1] * min(n_relevant, k))
    return dcg(rels[:k]) / ideal if ideal else 0.0


def mrr(rels: list[int]) -> float:
    for i, r in enumerate(rels):
        if r:
            return 1.0 / (i + 1)
    return 0.0


def md_table(rows: list[dict], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    return "\n".join(out)

"""Retrieval accuracy + ablation of the four search modes.

    python -m consultai.eval.retrieval

Gold labels (datasets/retrieval_gold.jsonl) are checkable, never hand-waved:
  * phrases      a retrieved chunk is relevant if its page contains one of the answer phrases
                 (the number of relevant units = pages containing the phrase)
  * gold_sources a retrieved chunk is relevant if it comes from one of the listed documents
                 ("which paper / product page answers this?")
  * gold_sql     a retrieved trial is relevant if it matches the SQL predicate over the trial registry
Each relevant unit (page, document or trial) is credited once, so several chunks from the same
page do not inflate the score. Metrics per query at k=10: hit@1, hit@5 (= success/recall of at least one relevant), MRR, nDCG@10.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from consultai.config import INDEX_DIR
from consultai.eval.common import load_jsonl, md_table, mrr, ndcg_at_k, save_result
from consultai.ingest import trials as trials_mod
from consultai.retrieval.store import collection

MODES = ["bm25", "dense", "hybrid", "hybrid_rerank"]
K = 10


def _norm(t: str) -> str:
    return re.sub(r"-\s+", "-", " ".join(t.split())).lower()


def _page_texts(col: str) -> dict[tuple[str, int], str]:
    path = INDEX_DIR / col / "pages.jsonl"
    return {(d["source_id"], d["page"]): _norm(d["text"]) for d in map(json.loads, path.open())}


def _relevance_fn(item: dict, pages: dict) -> tuple[callable, int]:
    if "gold_sql" in item:
        con = trials_mod.connect()
        gold = {r[0] for r in con.execute(f"SELECT nct_id FROM trials WHERE {item['gold_sql']}")}
        return (lambda c: c["chunk_id"] if c["chunk_id"] in gold else None), len(gold)
    if "gold_sources" in item:
        gold = set(item["gold_sources"])
        n = len(gold)
        return (lambda c: c["source_id"] if c["source_id"] in gold else None), n
    phrases = [_norm(p) for p in item["phrases"]]
    gold_pages = {key for key, text in pages.items() if any(p in text for p in phrases)}
    unit = lambda c: (c["source_id"], c.get("page") or 1)  # noqa: E731
    return (lambda c: unit(c) if unit(c) in gold_pages else None), len(gold_pages)


def _where(item: dict):
    w = item.get("where")
    if not w:
        return None
    return lambda c: all(c["meta"].get(k) == v for k, v in w.items())


def run(modes: list[str] = MODES) -> dict:
    items = load_jsonl("retrieval_gold.jsonl")
    page_cache: dict[str, dict] = {}
    per_query, agg = [], defaultdict(lambda: defaultdict(list))
    for item in items:
        col = item["collection"]
        if col not in page_cache:
            page_cache[col] = _page_texts(col) if col != "trials" else {}
        unit_of, n_rel = _relevance_fn(item, page_cache[col])
        row = {"id": item["id"], "collection": col, "query": item["query"], "n_relevant": n_rel}
        for mode in modes:
            hits = collection(col).search(item["query"], k=K, mode=mode, where=_where(item))
            rels, seen = [], set()
            for h in hits:  # each relevant unit (page / document / trial) is credited once
                u = unit_of(h.chunk)
                rels.append(1 if u is not None and u not in seen else 0)
                seen.add(u)
            m = {"hit@1": float(rels[:1] == [1]), "hit@5": float(any(rels[:5])),
                 "mrr": mrr(rels), "ndcg@10": ndcg_at_k(rels, n_rel, K)}
            row[mode] = m | {"top": [f"{h.chunk['source_id']}:{h.chunk.get('page') or h.chunk['chunk_id']}" for h in hits[:3]]}
            for name, v in m.items():
                agg[(col, mode)][name].append(v)
                agg[("ALL", mode)][name].append(v)
        per_query.append(row)

    summary = []
    for (col, mode), metrics in sorted(agg.items()):
        summary.append({"collection": col, "mode": mode, "n": len(metrics["mrr"]),
                        **{k: sum(v) / len(v) for k, v in metrics.items()}})
    overall = {r["mode"]: r for r in summary if r["collection"] == "ALL"}
    best = max(overall.values(), key=lambda r: (r["ndcg@10"], r["mrr"]))["mode"]
    table = md_table(summary, ["collection", "mode", "n", "hit@1", "hit@5", "mrr", "ndcg@10"])
    path = save_result("retrieval", {"k": K, "best_mode_by_ndcg": best, "summary": summary,
                                     "per_query": per_query, "table_md": table})
    print(table)
    print(f"\nbest overall mode (nDCG@10): {best}   -> {path}")
    return {"best": best, "summary": summary}


if __name__ == "__main__":
    run()

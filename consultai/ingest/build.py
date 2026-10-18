"""Build every retrieval index from the source manifest.

    python -m consultai.ingest.build                 # all collections
    python -m consultai.ingest.build sec_filings sofi

Output per collection under CONSULTAI_DATA_ROOT/indexes/<collection>/:
  chunks.jsonl  chunk records (text, page, section, metadata, index_text)
  pages.jsonl   full text of every PDF page / web page (for the read_pages tool)
  vectors.npy   normalized bge embeddings, row-aligned with chunks.jsonl
  info.json     counts, embedding model, build settings
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict

import numpy as np

from consultai.config import INDEX_DIR, settings
from consultai.ingest import trials as trials_mod
from consultai.ingest.extract import html_documents, normalize, pdf_pages
from consultai.ingest.sources import ALL_SOURCES, Source
from consultai.retrieval.chunking import chunk_html, chunk_pdf
from consultai.retrieval.models import embed_passages

COLLECTIONS = ["tech_docs", "agilent", "clinical_lit", "sec_filings", "sofi", "trials"]


def _verify_sec_cover(src: Source, pages: list[str]) -> None:
    cover = normalize(" ".join(pages[:3]))
    if src.meta["cover_name"].casefold() not in cover.casefold():
        raise ValueError(f"{src.source_id}: cover page does not name {src.meta['cover_name']!r}")
    fye = time.strptime(src.meta["fiscal_year_end"], "%Y-%m-%d")
    stated = time.strftime("%B %-d, %Y", fye)
    if stated not in cover:
        raise ValueError(f"{src.source_id}: cover page does not state fiscal year ended {stated}")


def _write(collection: str, chunks: list[dict], pages: list[dict], extra: dict | None = None) -> None:
    cfg = settings()["retrieval"]
    out = INDEX_DIR / collection
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    vectors = embed_passages([c["index_text"] for c in chunks])
    np.save(out / "vectors.npy", vectors)
    with (out / "chunks.jsonl").open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (out / "pages.jsonl").open("w") as fh:
        for p in pages:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    per_source = defaultdict(int)
    for c in chunks:
        per_source[c["source_id"]] += 1
    info = {"collection": collection, "chunks": len(chunks), "pages": len(pages),
            "embed_model": cfg["embed_model"], "chunk_chars": cfg["chunk_chars"],
            "overlap_chars": cfg["chunk_overlap_chars"], "chunks_per_source": dict(per_source),
            "embed_seconds": round(time.time() - t0, 1), "built_at": time.strftime("%Y-%m-%d %H:%M:%S"), **(extra or {})}
    (out / "info.json").write_text(json.dumps(info, indent=2))
    print(f"[{collection}] {len(chunks)} chunks, {len(pages)} pages, embedded in {info['embed_seconds']}s")


def build_documents(collection: str) -> None:
    cfg = settings()["retrieval"]
    max_chars, overlap = cfg["chunk_chars"], cfg["chunk_overlap_chars"]
    srcs = [s for s in ALL_SOURCES if s.collection == collection]
    chunks, pages = [], []
    html_srcs = [s for s in srcs if s.kind == "html"]
    by_site: dict[str, list[Source]] = defaultdict(list)
    for s in html_srcs:
        by_site[s.meta.get("vendor", "web")].append(s)
    for site_srcs in by_site.values():
        cleaned = html_documents([s.local_path for s in site_srcs])
        for s in site_srcs:
            text = cleaned[s.local_path]
            chunks += [c.to_dict() | {"index_text": c.index_text} for c in chunk_html(s, text, max_chars, overlap)]
            pages.append({"source_id": s.source_id, "page": 1, "text": re.sub(r"^### ", "", text, flags=re.M)})
    for s in (s for s in srcs if s.kind == "pdf"):
        ptexts = pdf_pages(s.local_path)
        if collection == "sec_filings":
            _verify_sec_cover(s, ptexts)
        chunks += [c.to_dict() | {"index_text": c.index_text} for c in chunk_pdf(s, ptexts, max_chars, overlap)]
        pages += [{"source_id": s.source_id, "page": i, "text": t} for i, t in enumerate(ptexts, start=1)]
    _write(collection, chunks, pages)


def build_trials() -> None:
    trials = trials_mod._load_rows()
    trials_mod.build_sqlite(trials)
    chunks = trial_chunks = trials_mod.trial_chunks(trials)
    _write("trials", chunks, [], {"unique_trials": len(trials),
                                  "sqlite": str(trials_mod.DB_PATH)})
    del trial_chunks


def main(names: list[str]) -> None:
    for name in names or COLLECTIONS:
        if name not in COLLECTIONS:
            raise SystemExit(f"unknown collection {name}; choose from {COLLECTIONS}")
        build_trials() if name == "trials" else build_documents(name)


if __name__ == "__main__":
    main(sys.argv[1:])

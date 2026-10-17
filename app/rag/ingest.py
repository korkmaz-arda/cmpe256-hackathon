"""Build the per-domain knowledge bases: read PDFs and web pages, chunk them page by page
with citation metadata, embed the chunks and save one index per domain.

Run: .venv/bin/python -m app.rag.ingest [--domains sec csr ...]
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
from pypdf import PdfReader

from app import config, llm

_WS = re.compile(r"\s+")


def clean(text: str) -> str:
    return _WS.sub(" ", text or "").strip()


def split(text: str, size: int = config.CHUNK_CHARS, overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Split on sentence-ish boundaries into ~size-character windows with overlap."""
    if len(text) <= size:
        return [text] if text else []
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind(". ", start + size // 2, end)
            end = cut + 1 if cut > 0 else end
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in out if len(c) > 40]


def describe_local(path: Path, domain: str) -> dict:
    """Citation metadata for a local course document."""
    meta = {"domain": domain, "path": str(path.relative_to(config.ROOT)), "url": None}
    if domain == "sec":
        company, year, title = config.SEC_TITLES.get(path.stem, (path.parent.name, "", path.stem))
        meta.update(title=title, source="SEC 10-K filing", company=company, year=year)
    elif domain == "csr":
        year = re.search(r"(20\d\d)", path.stem).group(1)
        meta.update(
            title=f"FAO SOFI {year}: The State of Food Security and Nutrition in the World",
            source="UN FAO report",
            year=year,
        )
    elif domain == "clinical":
        meta.update(title=path.stem.replace("_", " "), source="IEEE research paper", topic=path.parent.name)
    return meta


# Readable titles for the downloaded Cisco datasheets (their file names are URL slugs).
DATASHEET_TITLES = {
    "catalyst-8300": "Cisco Catalyst 8300 Series Edge Platforms Data Sheet",
    "catalyst-8200": "Cisco Catalyst 8200 Series Edge Platforms Data Sheet",
    "catalyst-8000v": "Cisco Catalyst 8000V Edge Software Data Sheet",
    "4000-series-integrated": "Cisco 4000 Series Integrated Services Routers Data Sheet",
    "asr-1000": "Cisco ASR 1000 Series Aggregation Services Routers Data Sheet",
}


def web_title(entry: dict) -> str:
    if entry.get("type") == "pdf":
        for key, title in DATASHEET_TITLES.items():
            if key in entry["url"]:
                return title
    return (entry.get("title") or Path(entry["path"]).stem).replace("​", "").replace(" - Cisco", "").strip()


def agilent_catalog_docs() -> list[tuple[dict, str]]:
    """Agilent's site returns HTTP 403 to automated downloads, so the Clinical KB uses the product
    facts transcribed from the supplied Agilent pages into app/catalog/agilent_products.json."""
    path = config.ROOT / "app" / "catalog" / "agilent_products.json"
    if not path.exists():
        return []
    docs = []
    for p in json.loads(path.read_text()):
        text = (
            f"{p['name']} ({p['category']}). What it does: {p['measures_or_does']}. "
            f"Sample types: {', '.join(p.get('sample_types') or [])}. "
            f"Regulatory status: {p.get('regulatory') or 'not stated on the page'}. "
            f"Typical use cases: {', '.join(p.get('typical_use_cases') or [])}."
        )
        meta = {
            "domain": "clinical", "path": "app/catalog/agilent_products.json", "url": p["source_url"],
            "title": f"Agilent product page: {p['name']}", "source": "Agilent product page (transcribed)",
            "company": "Agilent",
        }
        docs.append((meta, text))
    return docs


def pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            pages.append((i, clean(page.extract_text())))
        except Exception:
            continue
    return pages


def collect(domain: str) -> list[dict]:
    """Every chunk for one domain, from local files and the downloaded web sources."""
    chunks: list[dict] = []

    def add(meta: dict, pages: list[tuple[int | None, str]]):
        for page, text in pages:
            for piece in split(text):
                chunks.append({**meta, "page": page, "text": piece})

    for pattern in config.LOCAL_SOURCES[domain]:
        for path in sorted(config.DATA.glob(pattern)):
            print(f"  [{domain}] {path.name}", flush=True)
            add(describe_local(path, domain), pdf_pages(path))

    manifest = config.WEB / "manifest.json"
    if manifest.exists():
        for entry in json.loads(manifest.read_text()):
            if entry.get("domain") != domain or not entry.get("ok"):
                continue
            path = config.ROOT / entry["path"] if not Path(entry["path"]).is_absolute() else Path(entry["path"])
            if not path.exists():
                continue
            company = "Cisco" if "cisco" in entry["url"] else "Agilent" if "agilent" in entry["url"] else "Google"
            meta = {
                "domain": domain,
                "path": str(path.relative_to(config.ROOT)),
                "url": entry["url"],
                "title": web_title(entry),
                "source": entry.get("source", "web page"),
                "company": company,
            }
            print(f"  [{domain}] web: {meta['title']}", flush=True)
            if path.suffix == ".pdf":
                add(meta, pdf_pages(path))
            else:
                add(meta, [(None, clean(path.read_text(errors="ignore")))])

    if domain == "clinical":
        for meta, text in agilent_catalog_docs():
            add(meta, [(None, text)])

    for i, c in enumerate(chunks):
        c["id"] = f"{domain}-{i}"
    return chunks


def build(domain: str) -> None:
    t0 = time.time()
    chunks = collect(domain)
    if not chunks:
        print(f"[{domain}] no documents found, skipped")
        return
    print(f"[{domain}] embedding {len(chunks)} chunks ...", flush=True)
    vectors = llm.embed([f"{c['title']} | {c['text']}" for c in chunks])
    folder = config.INDEX / domain
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "chunks.tmp.json").write_text(json.dumps(chunks))
    np.save(folder / "vectors.tmp.npy", vectors)
    (folder / "chunks.tmp.json").replace(folder / "chunks.json")
    (folder / "vectors.tmp.npy").replace(folder / "vectors.npy")
    print(f"[{domain}] saved {len(chunks)} chunks in {time.time() - t0:.0f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domains", nargs="*", default=config.DOMAINS)
    args = parser.parse_args()
    for domain in args.domains:
        build(domain)


if __name__ == "__main__":
    main()

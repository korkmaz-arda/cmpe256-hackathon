"""Build the structured product catalogs used by the recommender tools.

    python scripts/extract_catalogs.py            # both
    python scripts/extract_catalogs.py --cisco    # Cisco platforms + orderable components (5 data sheets)
    python scripts/extract_catalogs.py --agilent  # Agilent products (6 web pages)

Claude reads each document (page-marked text) and fills a typed schema. Code then verifies the output
against the page text and DROPS anything that does not appear on the cited page (part numbers, model
names, attribute value strings, spec lines). A verification report is written next to the catalog.
Output: $CONSULTAI_DATA_ROOT/indexes/catalogs/{cisco,agilent}_catalog.json (derived data, not committed).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from consultai.agents.clinical.agilent_catalog import CATALOG_PATH as AGILENT_PATH  # noqa: E402
from consultai.agents.clinical.agilent_catalog import AgilentExtraction  # noqa: E402
from consultai.agents.technology.catalog import CATALOG_PATH as CISCO_PATH  # noqa: E402
from consultai.agents.technology.catalog import FAMILIES, DatasheetExtraction, norm, verify_extraction  # noqa: E402
from consultai.config import INDEX_DIR, model_profile  # noqa: E402
from consultai.llm.claude_runner import run_structured  # noqa: E402

CISCO_SYSTEM = """You are a meticulous Cisco hardware data-sheet analyst building a parts catalog.
Extract ONLY what the data sheet text states. Copy model names, product ids (PIDs) and value strings
exactly as printed (they will be machine-checked against the page; anything not found verbatim is discarded).
- platforms: every router model the data sheet describes (for a virtual router, one entry with virtual=true).
  For each numeric/boolean attribute you fill, add an attribute_evidence entry whose value_text is the exact
  printed value string (e.g. '19 Gbps', '6 x 1Gbps', '8 GB', 'dual power supply') and the page it is on.
  Leave attributes null when the data sheet does not state them. Do not compute or guess.
- deployment: use the data sheet's own positioning (branch, aggregation, headend, cloud, colocation).
- components: every orderable part number in tables or text (power supplies, NIM/SM modules, memory,
  storage, route processors, ESPs, licenses, accessories) with its description, category and the models it is for.
Pages are marked '=== PAGE n ==='."""

AGILENT_SYSTEM = """You are a life-science instrumentation analyst building a product catalog from Agilent web pages.
List every distinct product or product line each page describes. Copy names, part numbers and spec sentences
verbatim (they will be machine-checked against the page text; anything not found verbatim is discarded).
regulatory_status: use exactly what the page labels (IVD or RUO); otherwise 'not stated'. Do not add facts
that the page does not state."""


def _pages(collection: str, source_id: str) -> dict[int, str]:
    out = {}
    for line in (INDEX_DIR / collection / "pages.jsonl").open():
        d = json.loads(line)
        if d["source_id"] == source_id:
            out[d["page"]] = d["text"]
    return out


async def build_cisco(model: str) -> None:
    async def one(family: str):
        sid = f"cisco-{family}-datasheet"
        pages = _pages("tech_docs", sid)
        doc = "\n\n".join(f"=== PAGE {p} ===\n{t}" for p, t in sorted(pages.items()))
        prompt = f"Data sheet `{sid}` (family slug: {family}).\n\n{doc}"
        ext, meta = await run_structured(prompt, CISCO_SYSTEM, DatasheetExtraction, model, timeout_s=600)
        for p in ext.platforms:
            p.family = family
        verified, report = verify_extraction(sid, ext, pages)
        print(f"{sid}: platforms {report['platforms_in']}->{report['platforms_out']}, "
              f"components {report['components_in']}->{report['components_out']}, "
              f"dropped attributes {len(report['dropped_attributes'])} ({meta.duration_s}s)")
        return sid, verified, report

    results = await asyncio.gather(*(one(f) for f in FAMILIES))
    catalog = {"platforms": [], "components": [], "verification": []}
    for sid, ext, report in results:
        catalog["platforms"] += [p.model_dump() | {"source_id": sid} for p in ext.platforms]
        catalog["components"] += [c.model_dump() | {"source_id": sid} for c in ext.components]
        catalog["verification"].append(report)
    CISCO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CISCO_PATH.write_text(json.dumps(catalog, indent=2))
    print(f"-> {CISCO_PATH}: {len(catalog['platforms'])} platforms, {len(catalog['components'])} components")


async def build_agilent(model: str) -> None:
    pages = {}
    for line in (INDEX_DIR / "agilent" / "pages.jsonl").open():
        d = json.loads(line)
        pages[d["source_id"]] = d["text"]
    doc = "\n\n".join(f"=== SOURCE {sid} ===\n{t}" for sid, t in pages.items())
    ext, meta = await run_structured(f"Agilent pages:\n\n{doc}", AGILENT_SYSTEM, AgilentExtraction, model, timeout_s=600)
    kept, dropped = [], []
    for p in ext.products:
        page = norm(pages.get(p.source_id, ""))
        name_ok = norm(p.name) in page or any(norm(pn) in page for pn in p.part_numbers) \
            or norm(p.name.replace("®", "")) in page.replace("®", "")
        if not name_ok:
            dropped.append(f"product {p.name!r} not found on {p.source_id}")
            continue
        p.part_numbers = [pn for pn in p.part_numbers if norm(pn) in page]
        good_specs = [s for s in p.specs if norm(s.text) in page]
        dropped += [f"{p.name}: spec not verbatim: {s.text[:60]!r}" for s in p.specs if s not in good_specs]
        p.specs = good_specs
        kept.append(p)
    AGILENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGILENT_PATH.write_text(json.dumps({"products": [p.model_dump() for p in kept],
                                        "verification": {"in": len(ext.products), "out": len(kept), "dropped": dropped}},
                                       indent=2))
    print(f"agilent: products {len(ext.products)}->{len(kept)}, dropped {len(dropped)} items ({meta.duration_s}s) -> {AGILENT_PATH}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cisco", action="store_true")
    ap.add_argument("--agilent", action="store_true")
    ap.add_argument("--profile", default=None)
    args = ap.parse_args()
    model = model_profile(args.profile).specialist
    both = not (args.cisco or args.agilent)
    if args.cisco or both:
        asyncio.run(build_cisco(model))
    if args.agilent or both:
        asyncio.run(build_agilent(model))

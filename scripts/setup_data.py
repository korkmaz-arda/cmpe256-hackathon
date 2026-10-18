"""Unpack the course data zips into CONSULTAI_DATA_ROOT/raw (outside the repo) and verify the manifest.

    python scripts/setup_data.py            # unzip (skips archives already unpacked) + verify
    python scripts/setup_data.py --verify   # verify only
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from consultai.config import RAW_DIR, RESOURCES_DIR  # noqa: E402
from consultai.ingest.sources import ALL_SOURCES, RETAIL_TRANSACTIONS, Source  # noqa: E402

ZIPS = ["Clinical.zip", "FoodSecurity.zip", "Retail.zip", "UnitedStatesSecuritiesandExchangeCommission(SEC).zip"]


def unzip_all() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in ZIPS:
        src = RESOURCES_DIR / "data" / name
        if not src.exists():
            raise SystemExit(f"Missing {src}. Set CONSULTAI_RESOURCES to the course resources folder.")
        with zipfile.ZipFile(src) as zf:
            members = [m for m in zf.namelist() if not m.endswith("/")]
            todo = [m for m in members if not (RAW_DIR / m).exists()]
            for m in todo:
                target = (RAW_DIR / m).resolve()
                if RAW_DIR.resolve() not in target.parents:  # zip-slip guard
                    raise SystemExit(f"Refusing to extract {m} outside {RAW_DIR}")
                zf.extract(m, RAW_DIR)
            print(f"{name}: {len(members)} files ({len(todo)} extracted)")


def verify() -> bool:
    ok = True
    for s in ALL_SOURCES:
        if not s.local_path.exists():
            ok = False
            print(f"MISSING  {s.source_id}: {s.local_path}")
    retail = Source("retail", "-", "-", "-", "csv", RETAIL_TRANSACTIONS, None, "-").local_path
    if not retail.exists():
        ok = False
        print(f"MISSING  retail transactions: {retail}")
    print(f"{len(ALL_SOURCES)} grounding sources checked under {RESOURCES_DIR} and {RAW_DIR}: {'OK' if ok else 'PROBLEMS'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if not args.verify:
        unzip_all()
    sys.exit(0 if verify() else 1)

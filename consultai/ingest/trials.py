"""ClinicalTrials.gov exports -> SQLite (exact filtering and counting) + one retrieval "card" per trial.

The four CSV exports (covid, diabetes, heart attack, knee injuries) overlap: a trial registered for
diabetes and myocardial infarction appears in two files. Each NCT id is stored once and keeps the
list of condition sets it came from. Counts reported by the Clinical agent come from SQL here,
never from the language model.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from consultai.config import INDEX_DIR
from consultai.ingest.sources import CLINICAL_SOURCES

DB_PATH = INDEX_DIR / "trials" / "trials.sqlite"

COLUMNS = {  # CSV column -> SQL column
    "NCT Number": "nct_id", "Study Title": "title", "Study URL": "url", "Acronym": "acronym",
    "Study Status": "status", "Brief Summary": "summary", "Study Results": "has_results",
    "Conditions": "conditions", "Interventions": "interventions",
    "Primary Outcome Measures": "primary_outcomes", "Secondary Outcome Measures": "secondary_outcomes",
    "Sponsor": "sponsor", "Collaborators": "collaborators", "Sex": "sex", "Age": "age", "Phases": "phases",
    "Enrollment": "enrollment", "Funder Type": "funder_type", "Study Type": "study_type",
    "Study Design": "study_design", "Start Date": "start_date", "Primary Completion Date": "primary_completion_date",
    "Completion Date": "completion_date", "First Posted": "first_posted", "Last Update Posted": "last_update_posted",
    "Locations": "locations",
}


def _load_rows() -> dict[str, dict]:
    csv.field_size_limit(1 << 30)
    trials: dict[str, dict] = {}
    for src in (s for s in CLINICAL_SOURCES if s.collection == "trials"):
        cset = src.meta["condition_set"]
        with src.local_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                nct = row["NCT Number"].strip()
                rec = trials.get(nct)
                if rec is None:
                    rec = {sql: (row.get(col) or "").strip() for col, sql in COLUMNS.items()}
                    rec["enrollment"] = int(rec["enrollment"]) if rec["enrollment"].isdigit() else None
                    rec["start_year"] = int(rec["start_date"][:4]) if rec["start_date"][:4].isdigit() else None
                    rec["condition_sets"] = []
                    trials[nct] = rec
                if cset not in rec["condition_sets"]:
                    rec["condition_sets"].append(cset)
    return trials


def build_sqlite(trials: dict[str, dict], path: Path = DB_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    cols = list(COLUMNS.values()) + ["start_year"]
    con.execute(f"CREATE TABLE trials ({', '.join(c + (' INTEGER' if c in ('enrollment', 'start_year') else ' TEXT') for c in cols)}, "
                "PRIMARY KEY (nct_id))")
    con.execute("CREATE TABLE trial_sets (nct_id TEXT, condition_set TEXT, PRIMARY KEY (nct_id, condition_set))")
    con.executemany(f"INSERT INTO trials VALUES ({', '.join('?' * len(cols))})",
                    [[t[c] for c in cols] for t in trials.values()])
    con.executemany("INSERT INTO trial_sets VALUES (?, ?)",
                    [(t["nct_id"], cs) for t in trials.values() for cs in t["condition_sets"]])
    con.execute("CREATE INDEX ix_sets ON trial_sets(condition_set)")
    con.commit()
    con.close()


def trial_card(t: dict) -> str:
    """Compact text used for BM25 + embeddings (title, conditions, interventions, summary, outcomes)."""
    parts = [
        t["title"] + (f" ({t['acronym']})" if t["acronym"] else ""),
        f"Conditions: {t['conditions'].replace('|', '; ')}",
        f"Interventions: {t['interventions'].replace('|', '; ')}" if t["interventions"] else "",
        f"Status: {t['status']}; Phase: {t['phases'] or 'n/a'}; Type: {t['study_type']}; Sponsor: {t['sponsor']}",
        t["summary"][:700],
        f"Primary outcomes: {t['primary_outcomes'][:300]}" if t["primary_outcomes"] else "",
    ]
    return "\n".join(p for p in parts if p)


def trial_chunks(trials: dict[str, dict]) -> list[dict]:
    out = []
    for t in trials.values():
        card = trial_card(t)
        out.append({
            "chunk_id": t["nct_id"], "source_id": f"ctg-{t['condition_sets'][0]}", "collection": "trials",
            "text": card, "index_text": card, "page": None, "section": None,
            "meta": {
                "doc_title": f"ClinicalTrials.gov {t['nct_id']}", "nct_id": t["nct_id"], "url": t["url"],
                "condition_sets": t["condition_sets"], "status": t["status"], "phases": t["phases"],
                "study_type": t["study_type"], "has_results": t["has_results"] == "YES",
                "enrollment": t["enrollment"], "start_year": t["start_year"], "sponsor": t["sponsor"],
                "funder_type": t["funder_type"],
            },
        })
    return out


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

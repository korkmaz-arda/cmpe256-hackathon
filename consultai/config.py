"""Paths, model profiles and settings.

Course data is never stored in the repository:
  * CONSULTAI_RESOURCES  - the read-only course resources folder (zips, link lists, saved web pages)
  * CONSULTAI_DATA_ROOT  - where zips are unpacked and indexes are built (outside the repo)
Both default to siblings of the repo checkout used during the hackathon.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
RUNS_DIR = Path(os.environ.get("CONSULTAI_RUNS_DIR", REPO_ROOT / "runs"))
EVAL_RESULTS_DIR = REPO_ROOT / "eval" / "results"

# Defaults: the hackathon workspace layout (hackathon/{resources,workdata} next to repo/dev/version1) if present,
# otherwise folders inside a plain clone (resources/ and data/, both git-ignored).
_HACKATHON_DIR = REPO_ROOT.parents[2] if len(REPO_ROOT.parents) > 2 else REPO_ROOT


def _default(sibling: str, in_clone: str) -> Path:
    candidate = _HACKATHON_DIR / sibling
    return candidate if candidate.exists() else REPO_ROOT / in_clone


RESOURCES_DIR = Path(os.environ.get("CONSULTAI_RESOURCES", _default("resources", "resources")))
DATA_ROOT = Path(os.environ.get("CONSULTAI_DATA_ROOT", _default("workdata", "data")))
RAW_DIR = DATA_ROOT / "raw"          # unzipped course data
INDEX_DIR = DATA_ROOT / "indexes"    # chunk stores, embeddings, SQLite


@lru_cache
def settings() -> dict:
    return yaml.safe_load((CONFIG_DIR / "settings.yaml").read_text())


@lru_cache
def _models_file() -> dict:
    return yaml.safe_load((CONFIG_DIR / "models.yaml").read_text())


@dataclass(frozen=True)
class ModelProfile:
    name: str
    router: str
    specialist: str
    review: str
    synthesis: str
    judge: str


def model_profile(name: str | None = None) -> ModelProfile:
    data = _models_file()
    name = name or os.environ.get("CONSULTAI_PROFILE") or data["default_profile"]
    if name not in data["profiles"]:
        raise ValueError(f"Unknown model profile {name!r}; choose from {sorted(data['profiles'])}")
    return ModelProfile(name=name, **data["profiles"][name])


def profile_names() -> list[str]:
    return list(_models_file()["profiles"])

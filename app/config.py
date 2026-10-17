"""Project-wide settings: paths, model choices and the knowledge sources behind each domain agent."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
WEB = DATA / "web"
INDEX = ROOT / "index"
PROMPTS = ROOT / "app" / "agents" / "prompts"

# Model routing (the professor's suggestion): a small, fast model classifies intent,
# then a full reasoning model does the domain work and the cross-domain synthesis.
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "gpt-5.4-mini")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-5.5")
AGENT_EFFORT = os.getenv("AGENT_EFFORT", "low")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

DOMAINS = ["technology", "clinical", "sec", "csr"]

DOMAIN_LABELS = {
    "technology": "Technology Agent",
    "clinical": "Clinical Agent",
    "sec": "SEC Agent",
    "csr": "Corporate Responsibility Agent",
}

# Local documents per domain (glob patterns relative to data/). Web documents are added
# from data/web/manifest.json, which app.rag.fetch_web writes.
LOCAL_SOURCES = {
    "technology": [],
    "clinical": ["Clinical/**/*.pdf"],
    "sec": ["SEC/**/*.pdf"],
    "csr": ["FoodSecurity/*.pdf"],
}

# Human-readable titles for the files whose names are opaque (SEC filings are named by UUID).
SEC_TITLES = {
    "b5098e8e-5716-4b35-8d8e-84dbdab516b1": ("Agilent", "FY2025", "Agilent Technologies 10-K FY2025"),
    "028fbac9-c5ba-409b-83ce-dfee9c17fdbc": ("Cisco", "FY2026", "Cisco Systems 10-K FY2026"),
    "6c821d1a-cf4e-4310-9801-df9399aa701b": ("Cisco", "FY2025", "Cisco Systems 10-K FY2025"),
    "0ca59726-c36c-45fe-a114-e147f8cd7237": ("Alphabet", "FY2024", "Alphabet Inc. 10-K FY2024"),
    "8873e505-7403-4c46-b377-81d814482cbb": ("Alphabet", "FY2025", "Alphabet Inc. 10-K FY2025"),
}

CHUNK_CHARS = 1400
CHUNK_OVERLAP = 200

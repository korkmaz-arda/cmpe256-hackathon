# Agentic AI Management Consulting Platform
### CMPE 256 Hackathon — SJSU, October 2026

A working prototype of a next-generation AI-powered management consulting
platform. A central **Management Consulting Manager Agent** understands
customer requests, routes them to specialized domain agents, and
consolidates their findings into consulting recommendations grounded in
evidence — with citations, confidence levels, and measurable next actions.

## Architecture

```
Customer request
       |
Manager Agent  (intent detection -> multi-label routing -> orchestration)
   |-- Technology Agent  (Cisco / Google Cloud docs, procurement catalog)
   |-- Clinical Agent    (Agilent diagnostics documentation)
   |-- SEC Agent         (Cisco, Alphabet, Agilent SEC filings)
   |-- Corporate Responsibility Agent  (FAO food-security reports)
       |
Consulting recommendation: evidence + insights + next actions
```

## The 7 hackathon capabilities, and where they live

- **Multi-agent orchestration** — `src/agents.py`: ManagerAgent with TF-IDF domain-centroid + word-boundary keyword scoring, multi-label routing, clarification on ambiguous queries.
- **Agent prompts** — every agent (manager + four specialists) ships with a written instruction set: persona, do / do-not instructions, domain expertise, grounding sources (`AGENT_PROMPTS` in `src/agents.py`, printed at the top of `results/demo_output.txt`).
- **Domain knowledge grounding** — `src/kb_build.py`: ~9,300 chunks from SEC 10-Ks, FAO SOFI 2023/2024, vendor pages, 20 IEEE clinical papers, ClinicalTrials.gov registry summaries (32,611 studies), procurement catalog.
- **RAG with citations** — `src/retrieval.py`: per-domain TF-IDF retrieval; every finding carries a `[source #chunk]` citation.
- **Intelligent recommendation** — `src/recommender.py`: Apriori-style association rules over 1,000 procurement transactions (support / confidence / lift). Part B UI in `partb/market_basket.html`: whole-cart-only rules, blanks out honestly.
- **Cross-domain reasoning** — the Manager fans out to several agents and merges their reports into one recommendation.
- **Explainability and evaluation** — `src/evaluate.py`: routing accuracy, retrieval precision@5, recommendation hit-rate@5 / MRR; agents separate confirmed findings from hypotheses and raise uncertainty flags.
- **Business value** — every recommendation states the action, why it fits, the expected impact, and how to measure it.

## Measured results

- Routing: **24/24 exact match** (F1 1.0) on 24 labeled queries, incl. cross-domain
- Retrieval: **cross-domain precision@5 = 0.825**
- Recommendation: **296 rules mined; hit-rate@5 = 0.27, MRR@5 = 0.128** (deterministic)

## Quickstart (no API keys — runs locally on CPU)

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python src/kb_build.py   # build the knowledge base (~3 min)
venv/bin/python src/demo.py       # 7 demo cases -> results/demo_output.txt
venv/bin/python src/evaluate.py   # metrics -> results/eval_metrics.json
```

Try your own question:

```bash
venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "src")
from retrieval import KnowledgeBase
from agents import ManagerAgent
mgr = ManagerAgent(KnowledgeBase())
res = mgr.handle("Which replacement parts should we order for our failing Cisco router?")
print("Routed to:", res["routing"]["domains"])
for r in res["recommendations"][:3]:
    print("-", r["action"])
EOF
```

## Layout

- `src/` — `kb_build.py`, `retrieval.py`, `recommender.py`, `agents.py`, `demo.py`, `evaluate.py`, `build_submission.py`, `build_deck.py`, `build_market_basket.py`
- `data/raw/` — supplied sources (txt files, zips, retail CSV) + `fetched/` vendor pages
- `data/kb/` — built `kb.json` chunks + `catalog.json`
- `results/` — `demo_output.txt`, `eval_metrics.json`
- `submission/` — Canvas write-up (`.docx`), plain-text version (`.txt`), presentation deck (`.pptx`)
- `partb/` — `market_basket.html`: standalone market-basket UI (open in a browser, no server)
- `VIDEO_SCRIPT.md` — 6-minute video storyboard (timestamps, what to show, what to say)

## Canvas submission (per Oct 17 rubric)

1. **Zip of the entire source code** — this folder (zip it without `venv/`).
2. **Group video, 5–7 minutes** — follow `VIDEO_SCRIPT.md`; the deck in `submission/` is the visual backbone.

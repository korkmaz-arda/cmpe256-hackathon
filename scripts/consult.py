"""Ask the consulting platform a question from the command line.

    python scripts/consult.py "Our Cisco enterprise router is experiencing intermittent connectivity failures..." --trace
    python scripts/consult.py --scenario router_outage --profile dev --trace
    python scripts/consult.py "..." --inject-failure sec     # demonstrates failure containment

Prints the live orchestration trace (with --trace) and the final consulting recommendation. The full run
(trace.jsonl + run.json) is saved under runs/<run_id>/.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

from consultai.orchestrator.manager import Orchestrator  # noqa: E402
from consultai.orchestrator.render import render_response, render_trace_line  # noqa: E402

SCENARIOS = json.loads((Path(__file__).resolve().parents[1] / "consultai" / "eval" / "datasets" / "scenarios.json").read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("request", nargs="?")
    ap.add_argument("--scenario", choices=[s["id"] for s in SCENARIOS])
    ap.add_argument("--profile", default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--no-review", action="store_true")
    ap.add_argument("--inject-failure", default=None, help="agent name to force-timeout (failure containment demo)")
    args = ap.parse_args()
    request = args.request or next((s["request"] for s in SCENARIOS if s["id"] == args.scenario), None)
    if not request:
        ap.error("give a request or --scenario")

    def on_event(e: dict) -> None:
        line = render_trace_line(e)
        if line:
            print(f"[{e['t']:7.1f}s] {line}", flush=True)

    orch = Orchestrator(profile=args.profile, review_enabled=False if args.no_review else None,
                        inject_failure=args.inject_failure)
    result = asyncio.run(orch.consult(request, on_event=on_event if args.trace else None))
    print("\n" + "=" * 100 + "\n")
    print(render_response(result))
    print(f"\n---\nrun {result.run_id} | profile {result.profile} | {result.timings} | "
          f"API-equivalent cost ${result.usage['totals']['cost_usd_api_equivalent']} (subscription) | saved: {result.run_dir}")


if __name__ == "__main__":
    main()

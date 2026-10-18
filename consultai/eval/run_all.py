"""Run every evaluation and write eval/results/*.json (shown in the Streamlit Evaluation tab).

    python -m consultai.eval.run_all --profile dev            # all
    python -m consultai.eval.run_all --skip response_quality  # skip the expensive end-to-end runs
"""
from __future__ import annotations

import argparse

from consultai.eval import basket, recommendation, response_quality, retrieval, routing

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="dev")
    ap.add_argument("--skip", default="")
    ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    skip = set(a.skip.split(","))
    steps = [("retrieval", retrieval.run), ("routing", lambda: routing.run(a.profile)),
             ("recommendation", recommendation.run), ("basket", basket.run),
             ("response_quality", lambda: response_quality.run(a.profile, a.reuse, None))]
    for name, fn in steps:
        if name in skip:
            continue
        print(f"\n===== {name} =====")
        fn()

"""Routing accuracy: does the manager send each request to exactly the right set of specialists?

    python -m consultai.eval.routing [--profile dev]

Dataset: datasets/routing_gold.jsonl - 50 hand-labelled requests (8 per single domain, 8 two-domain, 4 three-domain,
2 four-domain, 4 out-of-scope), written separately from the agents' routing examples.
Compared: the LLM router (small model, as in production) vs the embedding kNN baseline/fallback.
Metrics: exact-set accuracy, micro/macro F1 over agents, per-agent precision/recall, over-/under-routing rate,
out-of-scope accuracy; plus a sweep of the relevance threshold tau applied to the LLM router's scores.
"""
from __future__ import annotations

import argparse
import asyncio

from consultai.config import model_profile, settings
from consultai.contracts import AGENT_NAMES
from consultai.eval.common import load_jsonl, md_table, save_result
from consultai.orchestrator import router


def metrics(gold: list[set], pred: list[set]) -> dict:
    exact = sum(g == p for g, p in zip(gold, pred)) / len(gold)
    per_agent, tp_all, fp_all, fn_all = {}, 0, 0, 0
    for a in AGENT_NAMES:
        tp = sum(a in g and a in p for g, p in zip(gold, pred))
        fp = sum(a not in g and a in p for g, p in zip(gold, pred))
        fn = sum(a in g and a not in p for g, p in zip(gold, pred))
        prec = tp / (tp + fp) if tp + fp else 1.0
        rec = tp / (tp + fn) if tp + fn else 1.0
        per_agent[a] = {"precision": round(prec, 3), "recall": round(rec, 3),
                        "f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0}
        tp_all, fp_all, fn_all = tp_all + tp, fp_all + fp, fn_all + fn
    micro_p = tp_all / (tp_all + fp_all) if tp_all + fp_all else 1.0
    micro_r = tp_all / (tp_all + fn_all) if tp_all + fn_all else 1.0
    oos = [(g, p) for g, p in zip(gold, pred) if not g]
    return {"exact_set_accuracy": round(exact, 3),
            "micro_f1": round(2 * micro_p * micro_r / (micro_p + micro_r), 3) if micro_p + micro_r else 0.0,
            "macro_f1": round(sum(v["f1"] for v in per_agent.values()) / len(per_agent), 3),
            "over_routing_rate": round(sum(bool(p - g) for g, p in zip(gold, pred)) / len(gold), 3),
            "under_routing_rate": round(sum(bool(g - p) for g, p in zip(gold, pred)) / len(gold), 3),
            "out_of_scope_accuracy": round(sum(not p for _, p in oos) / len(oos), 3) if oos else None,
            "per_agent": per_agent}


async def _llm_all(items: list[dict], model: str, concurrency: int = 6) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def one(item):
        async with sem:
            try:
                d, _ = await router.llm_route(item["query"], None, model, timeout_s=180)
                return {a.agent: a.relevance for a in d.assignments} | {"_oos": d.out_of_scope}
            except Exception as e:
                return {"_error": repr(e)}

    return await asyncio.gather(*(one(i) for i in items))


def run(profile: str | None = None) -> dict:
    items = load_jsonl("routing_gold.jsonl")
    gold = [set(i["agents"]) for i in items]
    model = model_profile(profile).router
    raw = asyncio.run(_llm_all(items, model))
    tau_cfg = settings()["orchestration"]["routing_threshold"]

    def llm_pred(tau: float) -> list[set]:
        return [{a for a in AGENT_NAMES if r.get(a, 0) >= tau} for r in raw]

    sweep = [{"tau": t, **{k: v for k, v in metrics(gold, llm_pred(t)).items() if k != "per_agent"}}
             for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8)]
    knn_raw = [router.knn_scores(i["query"]) for i in items]

    def knn_pred(abs_t: float, margin: float) -> list[set]:
        out = []
        for s in knn_raw:
            top = max(s.values())
            out.append({a for a, v in s.items() if v >= abs_t and v >= top - margin})
        return out

    knn_grid = []
    for abs_t in (0.5, 0.55, 0.6, 0.65):
        for margin in (0.03, 0.06, 0.1):
            m = metrics(gold, knn_pred(abs_t, margin))
            knn_grid.append({"abs_threshold": abs_t, "margin": margin, "exact": m["exact_set_accuracy"], "micro_f1": m["micro_f1"]})
    knn_default = metrics(gold, knn_pred(0.55, 0.06))
    llm = metrics(gold, llm_pred(tau_cfg))
    rows = [{"router": f"LLM ({model}), tau={tau_cfg}", **{k: llm[k] for k in ("exact_set_accuracy", "micro_f1", "macro_f1",
                                                                              "over_routing_rate", "under_routing_rate",
                                                                              "out_of_scope_accuracy")}},
            {"router": "kNN embedding baseline (0.55, 0.06)", **{k: knn_default[k] for k in ("exact_set_accuracy", "micro_f1",
                                                                                           "macro_f1", "over_routing_rate",
                                                                                           "under_routing_rate", "out_of_scope_accuracy")}}]
    errors = [{"id": i["id"], "query": i["query"], "gold": sorted(g), "pred": sorted(p), "scores": r}
              for i, g, p, r in zip(items, gold, llm_pred(tau_cfg), raw) if g != p]
    table = md_table(rows, ["router", "exact_set_accuracy", "micro_f1", "macro_f1", "over_routing_rate",
                            "under_routing_rate", "out_of_scope_accuracy"])
    per_agent = md_table([{"agent": a, **v} for a, v in llm["per_agent"].items()], ["agent", "precision", "recall", "f1"])
    sweep_md = md_table(sweep, ["tau", "exact_set_accuracy", "micro_f1", "over_routing_rate", "under_routing_rate"])
    summary = (f"{table}\n\n**LLM router per agent (tau={tau_cfg})**\n\n{per_agent}\n\n**Threshold sweep (LLM router)**\n\n"
               f"{sweep_md}\n\nMisrouted: {len(errors)} of {len(items)}.")
    path = save_result("routing", {"n": len(items), "model": model, "llm": llm, "knn": knn_default, "tau_sweep": sweep,
                                   "knn_grid": knn_grid, "errors": errors, "raw_llm": raw, "summary_md": summary})
    print(summary, f"\n-> {path}")
    return llm


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=None)
    run(ap.parse_args().profile)

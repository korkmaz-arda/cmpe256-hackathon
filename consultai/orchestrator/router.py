"""Intent detection and routing.

Primary router: the small model (Haiku in every profile) fills a RoutingDecision from capability cards that
are generated from the specialist roster. Code then enforces the contract: known agents only, relevance
threshold, no self/unknown dependencies, no cycles.

Fallback / baseline router: embedding k-nearest-neighbour similarity between the request and each specialist's
capability text + example questions. Used if the LLM call fails, and as the baseline in the routing evaluation.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from consultai.agents.registry import specialists
from consultai.config import settings
from consultai.contracts import AGENT_NAMES, Assignment, Entities, RoutingDecision
from consultai.ingest.sources import KNOWN_GAPS
from consultai.llm.claude_runner import CallMeta, run_structured

PROMPT = Path(__file__).resolve().parents[1] / "agents" / "manager" / "router_prompt.md"


def capability_cards() -> str:
    cards = []
    for a in specialists().values():
        examples = "\n".join(f"  - \"{q}\"" for q in a.routing_examples)
        gaps = " ".join(KNOWN_GAPS[a.name])
        cards.append(f"### `{a.name}` - {a.display_name} ({a.persona})\n{a.capability}\nNot covered: {gaps}\n"
                     f"Typical questions:\n{examples}")
    return "\n\n".join(cards)


def router_system_prompt() -> str:
    return PROMPT.read_text().replace("{{CAPABILITIES}}", capability_cards())


def _router_input(request: str, history: str | None) -> str:
    ctx = f"Earlier in this engagement:\n{history}\n\n" if history else ""
    return f"{ctx}Customer request:\n\"\"\"\n{request}\n\"\"\""


def enforce_contract(decision: RoutingDecision, threshold: float | None = None) -> RoutingDecision:
    """Apply the routing threshold and make dependencies well-formed (known, non-self, acyclic)."""
    tau = settings()["orchestration"]["routing_threshold"] if threshold is None else threshold
    seen, kept = set(), []
    for a in sorted(decision.assignments, key=lambda x: -x.relevance):
        if a.agent in AGENT_NAMES and a.agent not in seen and a.relevance >= tau:
            seen.add(a.agent)
            kept.append(a)
    for a in kept:
        a.depends_on = [d for d in dict.fromkeys(a.depends_on) if d in seen and d != a.agent]
    # break cycles: drop a dependency edge if it closes a loop (keeps edges from more relevant agents first)
    graph = {a.agent: list(a.depends_on) for a in kept}

    def reaches(src: str, dst: str, stack=()) -> bool:
        return src == dst or any(reaches(n, dst, stack + (src,)) for n in graph.get(src, []) if n not in stack)

    for a in kept:
        for d in list(a.depends_on):
            graph[a.agent].remove(d)
            if reaches(d, a.agent):
                a.depends_on.remove(d)
            else:
                graph[a.agent].append(d)
    decision.assignments = kept
    return decision


async def llm_route(request: str, history: str | None, model: str, timeout_s: float) -> tuple[RoutingDecision, CallMeta]:
    decision, meta = await run_structured(_router_input(request, history), router_system_prompt(), RoutingDecision,
                                          model, timeout_s=timeout_s)
    decision.router = "llm"
    return decision, meta


# ----------------------------------------------------------------------------- kNN baseline / fallback
@lru_cache
def _knn_index() -> tuple[list[str], np.ndarray]:
    from consultai.retrieval.models import embed_passages

    labels, texts = [], []
    for a in specialists().values():
        for t in [a.capability] + a.routing_examples:
            labels.append(a.name)
            texts.append(t)
    return labels, embed_passages(texts)


def knn_scores(request: str) -> dict[str, float]:
    from consultai.retrieval.models import embed_query

    labels, vecs = _knn_index()
    sims = vecs @ embed_query(request)
    scores: dict[str, float] = {}
    for label, s in zip(labels, sims):
        scores[label] = max(scores.get(label, -1.0), float(s))
    return scores


def knn_route(request: str, abs_threshold: float = 0.55, margin: float = 0.06) -> RoutingDecision:
    """Pick the top agent plus any agent within `margin` of it and above `abs_threshold`."""
    scores = knn_scores(request)
    top = max(scores.values())
    chosen = [a for a, s in sorted(scores.items(), key=lambda kv: -kv[1])
              if s >= abs_threshold and s >= top - margin] or [max(scores, key=scores.get)]
    return RoutingDecision(
        intents=["(kNN fallback - intents not extracted)"],
        assignments=[Assignment(agent=a, relevance=round(scores[a], 3), rationale=f"embedding similarity {scores[a]:.3f}",
                                sub_question=request, entities=Entities(), expected_outputs=[]) for a in chosen],
        router="knn-fallback")

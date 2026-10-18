"""The specialist roster. The router's capability cards and the agent cards are generated from here."""
from __future__ import annotations

from functools import lru_cache

from consultai.agents.base import Specialist


@lru_cache
def specialists() -> dict[str, Specialist]:
    from consultai.agents.clinical.agent import ClinicalAgent
    from consultai.agents.csr.agent import CSRAgent
    from consultai.agents.sec.agent import SECAgent
    from consultai.agents.technology.agent import TechnologyAgent

    roster = [TechnologyAgent(), ClinicalAgent(), SECAgent(), CSRAgent()]
    return {a.name: a for a in roster}


def get(name: str) -> Specialist:
    return specialists()[name]

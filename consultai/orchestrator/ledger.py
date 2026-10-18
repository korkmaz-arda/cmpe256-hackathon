"""Task ledger and progress ledger (the Magentic-style manager pattern on slide 3 of the brief).

TaskLedger     what the customer gave us, what must be looked up, and the plan (who does what, in which order)
ProgressLedger per round: each task's status; the manager's review verdict (goal met?) and follow-ups issued
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from consultai.contracts import ReviewDecision, RoutingDecision, SpecialistReport, SpecialistTask


class PlanStep(BaseModel):
    task_id: str
    agent: str
    objective: str
    depends_on: list[str] = Field(default_factory=list)


class TaskLedger(BaseModel):
    request: str
    facts_given: list[str] = Field(default_factory=list)
    facts_to_look_up: list[str] = Field(default_factory=list)
    plan: list[PlanStep] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)


class RoundProgress(BaseModel):
    round: int
    task_status: dict[str, str] = Field(default_factory=dict)  # task_id -> ok/partial/failed/...
    goal_met: bool | None = None
    follow_ups: list[str] = Field(default_factory=list)
    review_rationale: str | None = None


class Ledger(BaseModel):
    task_ledger: TaskLedger
    progress: list[RoundProgress] = Field(default_factory=list)

    @classmethod
    def from_routing(cls, request: str, routing: RoutingDecision) -> "Ledger":
        return cls(task_ledger=TaskLedger(request=request, facts_given=routing.facts_given,
                                          facts_to_look_up=routing.facts_to_look_up, out_of_scope=routing.out_of_scope))

    def add_plan(self, tasks: list[SpecialistTask], deps: dict[str, list[str]]) -> None:
        self.task_ledger.plan += [PlanStep(task_id=t.task_id, agent=t.agent, objective=t.objective,
                                           depends_on=deps.get(t.task_id, [])) for t in tasks]

    def record_round(self, rnd: int, reports: list[SpecialistReport], review: ReviewDecision | None) -> None:
        self.progress.append(RoundProgress(
            round=rnd, task_status={r.task_id: r.status for r in reports},
            goal_met=review.goal_met if review else None,
            follow_ups=[f"{f.agent}: {f.objective}" for f in review.follow_ups] if review else [],
            review_rationale=review.rationale if review else None))

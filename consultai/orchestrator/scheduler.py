"""Dependency-aware parallel execution of specialist tasks.

Tasks form a DAG (from RoutingDecision.depends_on). A task starts as soon as every task it depends on has
finished; independent tasks run concurrently (bounded by a semaphore). When a task starts, the structured
results of its upstream tasks are attached to it as `UpstreamContext` (findings + cited evidence, not prose).
Failures are contained: an exception or timeout becomes a `failed` SpecialistReport, the other tasks carry on,
and dependents still run (they are told their upstream failed).
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from consultai.contracts import SpecialistReport, SpecialistTask, UpstreamContext
from consultai.orchestrator.trace import TraceBus


def upstream_context(report: SpecialistReport) -> UpstreamContext:
    return UpstreamContext(agent=report.agent, task_id=report.task_id, status=report.status,
                           answer_summary=report.answer_summary, findings=report.findings,
                           recommendations=report.recommendations, evidence=report.evidence)


async def run_dag(tasks: list[SpecialistTask], deps: dict[str, list[str]],
                  runner: Callable[[SpecialistTask], Awaitable[SpecialistReport]],
                  trace: TraceBus, max_parallel: int) -> dict[str, SpecialistReport]:
    results: dict[str, SpecialistReport] = {}
    pending = {t.task_id: t for t in tasks}
    running: dict[asyncio.Task, str] = {}
    sem = asyncio.Semaphore(max_parallel)

    async def guarded(task: SpecialistTask) -> SpecialistReport:
        async with sem:
            return await runner(task)

    def launch_ready() -> None:
        for tid in list(pending):
            if all(d in results for d in deps.get(tid, [])):
                task = pending.pop(tid)
                task.upstream = [upstream_context(results[d]) for d in deps.get(tid, [])]
                failed_up = [results[d].agent for d in deps.get(tid, []) if results[d].status == "failed"]
                if failed_up:
                    task.constraints.append(f"Upstream specialist(s) {', '.join(failed_up)} failed; proceed without "
                                            f"their findings and state the gap.")
                trace.emit("task_dispatched", "manager", task, task.task_id)
                running[asyncio.create_task(guarded(task))] = tid

    launch_ready()
    while running:
        done, _ = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
        for fut in done:
            tid = running.pop(fut)
            results[tid] = fut.result()  # runner never raises (it converts errors into failed reports)
        launch_ready()
    return results

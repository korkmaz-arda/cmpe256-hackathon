"""Run trace: every step of an orchestration as an append-only event log.

Events are written to runs/<run_id>/trace.jsonl as they happen and pushed to live subscribers
(the Streamlit timeline, the CLI tree). Event types:

  run_started, routing_decided, task_dispatched, tool_called, tool_result, agent_message,
  report_received, review_decision, synthesis_started, synthesis_done, citation_check,
  clarification_requested, error, run_finished
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from consultai.config import RUNS_DIR


def _plain(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


class TraceBus:
    def __init__(self, run_id: str, persist: bool = True):
        self.run_id = run_id
        self.t0 = time.time()
        self.events: list[dict] = []
        self._subs: list[Callable[[dict], None]] = []
        self._lock = threading.Lock()
        self.dir: Path | None = None
        if persist:
            self.dir = RUNS_DIR / run_id
            self.dir.mkdir(parents=True, exist_ok=True)

    def subscribe(self, fn: Callable[[dict], None]) -> None:
        self._subs.append(fn)

    def emit(self, type_: str, actor: str, data: Any = None, task_id: str | None = None) -> dict:
        event = {"seq": len(self.events) + 1, "ts": time.strftime("%H:%M:%S"),
                 "t": round(time.time() - self.t0, 2), "type": type_, "actor": actor,
                 "task_id": task_id, "data": _plain(data)}
        with self._lock:
            self.events.append(event)
            if self.dir:
                with (self.dir / "trace.jsonl").open("a") as fh:
                    fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        for fn in self._subs:
            try:
                fn(event)
            except Exception:  # a broken UI callback must never break a run
                pass
        return event

    def save_json(self, name: str, obj: Any) -> None:
        if self.dir:
            (self.dir / name).write_text(json.dumps(_plain(obj), indent=2, ensure_ascii=False, default=str))

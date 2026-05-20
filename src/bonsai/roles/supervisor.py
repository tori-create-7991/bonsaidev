"""Supervisor role — state machine that drives Worker restarts.

State machine:
  running  → completed  (Worker sets ## Status: completed)
  running  → failed     (Worker sets ## Status: failed, restart if under limit)
  running  → needs_input (Worker sets ## Status: needs_input, write .answer or stop)

Max restarts: configurable, default 5 (from permissions.json).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bonsai.roles.worker import Worker
from bonsai.runners.base import Runner
from bonsai.state.events import EventLogger
from bonsai.state.plan import parse_plan
from bonsai.state.state_io import write_answer


class Supervisor:
    def __init__(
        self,
        *,
        plan_path: Path,
        run_dir: Path,
        runner: Runner,
        max_restarts: int = 5,
        answer_provider: Callable[[str, str | None], str] | None = None,
        heartbeat_interval: float = 10.0,
    ) -> None:
        self._plan_path = plan_path
        self._run_dir = run_dir
        self._runner = runner
        self._max_restarts = max_restarts
        self._answer_provider = answer_provider
        self._heartbeat_interval = heartbeat_interval
        plan = parse_plan(plan_path)
        self._events = EventLogger(run_dir, plan.plan_name)

    async def run(self) -> str:
        """Drive the Worker until terminal state. Returns final status string."""
        restarts = 0
        plan = parse_plan(self._plan_path)
        self._events.append("supervisor_start", {"plan_name": plan.plan_name})

        while True:
            worker = Worker(
                plan_path=self._plan_path,
                run_dir=self._run_dir,
                runner=self._runner,
                heartbeat_interval=self._heartbeat_interval,
            )
            status = await worker.run_once()

            if status == "completed":
                self._events.append(
                    "supervisor_done", {"status": "completed", "restarts": restarts}
                )
                return "completed"

            if status == "needs_input":
                plan = parse_plan(self._plan_path)
                if self._answer_provider is not None:
                    answer = self._answer_provider(
                        plan.pending_question or "",
                        plan.question_context,
                    )
                    write_answer(self._run_dir, answer)
                    self._events.append("supervisor_answered", {"question": plan.pending_question})
                    continue
                else:
                    self._events.append("supervisor_done", {"status": "needs_input"})
                    return "needs_input"

            if status == "failed":
                if restarts >= self._max_restarts:
                    self._events.append(
                        "supervisor_done",
                        {"status": "failed", "restarts": restarts, "reason": "max_restarts"},
                    )
                    return "failed"
                restarts += 1
                self._events.append("supervisor_restart", {"attempt": restarts})
                continue

            # Unknown status — treat as failed
            self._events.append("supervisor_done", {"status": status, "reason": "unknown"})
            return status

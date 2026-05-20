"""Worker role — executes one plan cycle via a Runner.

Responsibilities:
- Start heartbeat asyncio task (plan A)
- Read and consume .answer if present (inject into prompt)
- Invoke Runner.stream() and relay events
- Read final ## Status from plan.md and return it
- Log worker_start / worker_done events
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from bonsai.runners.base import Runner, RunnerRequest
from bonsai.state.events import EventLogger
from bonsai.state.heartbeat import HeartbeatWriter
from bonsai.state.plan import parse_plan
from bonsai.state.state_io import read_answer


class Worker:
    def __init__(
        self,
        *,
        plan_path: Path,
        run_dir: Path,
        runner: Runner,
        pid: int | None = None,
        heartbeat_interval: float = 10.0,
        model: str = "claude-opus-4-7",
    ) -> None:
        self._plan_path = plan_path
        self._run_dir = run_dir
        self._runner = runner
        self._pid = pid if pid is not None else os.getpid()
        self._heartbeat_interval = heartbeat_interval
        self._model = model
        self._events = EventLogger(run_dir, plan_path.parent.name)

    async def run_once(self) -> str:
        """Execute one plan cycle. Returns final plan status string."""
        plan = parse_plan(self._plan_path)
        self._events.append("worker_start", {"plan_name": plan.plan_name})

        hb = HeartbeatWriter(
            run_dir=self._run_dir,
            plan_name=plan.plan_name,
            pid=self._pid,
            interval=self._heartbeat_interval,
        )
        hb.write(status="running", task_index=plan.completed_tasks)
        hb_task = await hb.start()

        try:
            answer = read_answer(self._run_dir, consume=True)

            prompt = _build_prompt(plan.plan_name, answer)

            req = RunnerRequest(
                role="worker",
                model=self._model,
                prompt=prompt,
                workdir=self._plan_path.parent,
                runner_config={
                    "run_dir": str(self._run_dir),
                    "session_name": f"bonsai-worker-{plan.plan_name}",
                },
            )

            async for ev in self._runner.stream(req):
                if ev.kind == "stdout":
                    self._events.append("runner_stdout", {"text": ev.payload.get("text", "")})

        finally:
            hb_task.cancel()
            try:
                await hb_task
            except asyncio.CancelledError:
                pass

        refreshed = parse_plan(self._plan_path)
        final_status = refreshed.status or "completed"
        hb.write(status="stopped", task_index=refreshed.completed_tasks)

        self._events.append(
            "worker_done",
            {
                "final_status": final_status,
                "completed_tasks": refreshed.completed_tasks,
                "total_tasks": refreshed.total_tasks,
            },
        )
        return final_status


def _build_prompt(plan_name: str, answer: str | None) -> str:
    if answer:
        return (
            f"Continue executing plan '{plan_name}'.\n\nAnswer to your previous question:\n{answer}"
        )
    return f"Execute the next uncompleted task in plan '{plan_name}'."

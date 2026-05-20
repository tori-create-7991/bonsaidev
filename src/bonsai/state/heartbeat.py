"""Heartbeat writer — plan A: independent asyncio task.

Writes heartbeat.json to run_dir on a fixed interval so Supervisor can
detect stalled Workers without reading the full event log.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from bonsai.state.schemas import HeartbeatState


class HeartbeatWriter:
    def __init__(
        self,
        run_dir: Path,
        plan_name: str,
        pid: int | None = None,
        interval: float = 10.0,
    ) -> None:
        self._run_dir = run_dir
        self._plan_name = plan_name
        self._pid = pid if pid is not None else os.getpid()
        self._interval = interval
        self._last_state: HeartbeatState | None = None

    def write(
        self,
        status: str = "running",
        task_index: int = 0,
        current_task: str | None = None,
    ) -> None:
        state = HeartbeatState(
            plan_name=self._plan_name,
            pid=self._pid,
            status=status,  # type: ignore[arg-type]
            task_index=task_index,
            current_task=current_task,
        )
        self._last_state = state
        self._run_dir.mkdir(parents=True, exist_ok=True)
        (self._run_dir / "heartbeat.json").write_text(state.model_dump_json(indent=2))

    async def _tick(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            if self._last_state is None:
                self.write(status="idle", task_index=0)
            else:
                (self._run_dir / "heartbeat.json").write_text(
                    self._last_state.model_dump_json(indent=2)
                )

    async def start(self) -> asyncio.Task:
        return asyncio.create_task(self._tick())

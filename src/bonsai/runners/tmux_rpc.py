"""TmuxRpcRunner — drives an interactive Claude session via tmux send-keys.

Protocol:
1. Supervisor writes prompt + system-prompt to a tmp file.
2. Runner sends `bonsai-worker-boot <plan> <run_dir>` into the existing tmux session.
3. Worker Claude reads the plan, executes tasks, writes events + heartbeat.
4. Runner detects idle (no output change for idle_timeout_sec) as completion.
5. `.ready` file signals successful handshake.

Rate-limiting: send_keys is throttled to min 2.5s between calls (D18).
ANSI: raw tmux capture is stripped before idle detection.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncGenerator
from pathlib import Path

from bonsai.integrations.tmux import TmuxSession
from bonsai.runners.base import RunnerError, RunnerEvent, RunnerRequest, RunnerResult

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|\x1b\].*?\x07|\r")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


class RateLimiter:
    """Async rate limiter — enforces a minimum interval between acquire() calls."""

    def __init__(self, min_interval: float = 2.5) -> None:
        self.min_interval = min_interval
        self._last: float = 0.0

    async def acquire(self) -> None:
        now = time.monotonic()
        wait = self._last + self.min_interval - now
        if wait > 0:
            await asyncio.sleep(wait)
        self._last = time.monotonic()


class TmuxRpcRunner:
    """Runner that drives an interactive Claude session via tmux send-keys."""

    name = "tmux_rpc"

    def __init__(
        self,
        *,
        idle_timeout_sec: float = 30.0,
        poll_interval_sec: float = 2.0,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._idle_timeout = idle_timeout_sec
        self._poll_interval = poll_interval_sec
        self._rl = rate_limiter or RateLimiter()

    def supports_tool_allowlist(self) -> bool:
        return True

    async def run(self, req: RunnerRequest) -> RunnerResult:
        t0 = time.monotonic()
        async for ev in self.stream(req):
            if ev.kind == "completed":
                break
        duration_ms = int((time.monotonic() - t0) * 1000)
        stdout_path = (
            Path(req.runner_config["run_dir"])
            if "run_dir" in req.runner_config
            else req.workdir / ".auto-dev" / req.role
        ) / "worker.log"
        return RunnerResult(
            exit_code=0,
            stdout_path=stdout_path,
            completed_marker=True,
            duration_ms=duration_ms,
        )

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        cfg = req.runner_config
        session_name: str = cfg.get("session_name", f"bonsai-{req.role}")
        boot_cmd: str = cfg.get("boot_cmd", "")

        session = TmuxSession(session_name)

        if not session.exists():
            raise RunnerError(
                "process_died",
                f"tmux session {session_name!r} does not exist; start it first",
            )

        # Send the boot command
        if boot_cmd:
            await self._rl.acquire()
            try:
                session.send_keys(boot_cmd)
            except RuntimeError as e:
                raise RunnerError("process_died", str(e)) from e

        yield RunnerEvent(kind="stdout", payload={"text": f"started session {session_name}"})

        # Idle detection loop
        last_output = ""
        idle_since: float | None = None

        while True:
            await asyncio.sleep(self._poll_interval)

            try:
                raw = session.capture_pane()
            except RuntimeError as e:
                raise RunnerError("process_died", f"capture-pane failed: {e}") from e

            current = _strip_ansi(raw)

            if current != last_output:
                last_output = current
                idle_since = None
                yield RunnerEvent(kind="stdout", payload={"text": current[-500:]})
            else:
                if idle_since is None:
                    idle_since = time.monotonic()
                elif time.monotonic() - idle_since >= self._idle_timeout:
                    break

        yield RunnerEvent(kind="completed", payload={"session": session_name})

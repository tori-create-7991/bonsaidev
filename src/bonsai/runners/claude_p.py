"""ClaudePRunner — drives `claude -p` as a subprocess.

Used as a fallback / alternative to TmuxRpcRunner for contexts where
running `claude --print` is preferred (e.g. CI, scheduled tasks).

Completion detection: looks for `## Status: completed` in stdout.
Timeout: kills the subprocess and raises RunnerError(kind='timeout').
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from bonsai.runners.base import RunnerError, RunnerEvent, RunnerRequest, RunnerResult

_COMPLETED_MARKER = "## Status: completed"


class ClaudePRunner:
    """Runner that invokes `claude -p <prompt>` as a non-interactive subprocess."""

    name = "claude_p"

    def __init__(self, *, timeout_sec: float | None = None) -> None:
        self._timeout_sec = timeout_sec

    def supports_tool_allowlist(self) -> bool:
        return True

    async def run(self, req: RunnerRequest) -> RunnerResult:
        import time

        t0 = time.monotonic()
        completed = False
        async for ev in self.stream(req):
            if ev.kind == "completed":
                completed = True
                break
        duration_ms = int((time.monotonic() - t0) * 1000)
        stdout_path = req.workdir / "claude_p.log"
        return RunnerResult(
            exit_code=0,
            stdout_path=stdout_path,
            completed_marker=completed,
            duration_ms=duration_ms,
        )

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        cmd = _build_cmd(req)
        timeout = self._timeout_sec or req.timeout_sec

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=req.workdir,
            )
        except OSError as e:
            raise RunnerError("process_died", f"failed to launch claude: {e}") from e

        completed_marker_seen = False
        try:
            async with asyncio.timeout(timeout):
                async for raw_line in proc.stdout:
                    line = raw_line.decode(errors="replace").rstrip()
                    yield RunnerEvent(kind="stdout", payload={"text": line})
                    if _COMPLETED_MARKER in line:
                        completed_marker_seen = True

                await proc.wait()

        except TimeoutError:
            proc.kill()
            raise RunnerError("timeout", f"claude -p exceeded {timeout}s") from None

        if proc.returncode != 0 and not completed_marker_seen:
            raise RunnerError(
                "process_died",
                f"claude -p exited with code {proc.returncode}",
            )

        yield RunnerEvent(kind="completed", payload={"completed_marker": completed_marker_seen})


def _build_cmd(req: RunnerRequest) -> list[str]:
    cmd = ["claude", "--print", "--model", req.model]

    if req.system_prompt:
        cmd += ["--system-prompt", req.system_prompt]

    if req.allowed_tools:
        cmd += ["--allowedTools", ",".join(req.allowed_tools)]

    if req.skills_dir:
        cmd += ["--skills-dir", str(req.skills_dir)]

    cmd.append(req.prompt)
    return cmd

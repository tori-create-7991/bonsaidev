"""tmux subprocess integration.

Thin wrapper around the tmux CLI — keeps all tmux invocations in one place
so callers never construct raw subprocess calls.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run(args: list[str], *, check_stderr: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


class TmuxSession:
    """Manages a single named tmux session."""

    def __init__(self, session_name: str) -> None:
        self.session_name = session_name

    def new_session(self, cwd: str | Path) -> None:
        result = _run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                self.session_name,
                "-c",
                str(cwd),
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(f"tmux new-session failed: {result.stderr.strip()}")

    def send_keys(self, keys: str, *, enter: bool = True) -> None:
        cmd = ["tmux", "send-keys", "-t", self.session_name, keys]
        if enter:
            cmd.append("Enter")
        result = _run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"tmux send-keys failed: {result.stderr.strip()}")

    def capture_pane(self, *, pane: str | None = None) -> str:
        target = f"{self.session_name}{':' + pane if pane else ''}"
        result = _run(["tmux", "capture-pane", "-t", target, "-p"])
        if result.returncode != 0:
            raise RuntimeError(f"tmux capture-pane failed: {result.stderr.strip()}")
        return result.stdout

    def pipe_pane(self, log_path: str | Path | None) -> None:
        if log_path is None:
            cmd = ["tmux", "pipe-pane", "-t", self.session_name]
        else:
            cmd = [
                "tmux",
                "pipe-pane",
                "-t",
                self.session_name,
                "-o",
                f"cat >> {log_path}",
            ]
        result = _run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"tmux pipe-pane failed: {result.stderr.strip()}")

    def kill_session(self) -> None:
        result = _run(["tmux", "kill-session", "-t", self.session_name])
        if result.returncode != 0:
            stderr = result.stderr.strip().lower()
            if "not found" in stderr or "no server" in stderr:
                return
            raise RuntimeError(f"tmux kill-session failed: {result.stderr.strip()}")

    def exists(self) -> bool:
        result = _run(["tmux", "has-session", "-t", self.session_name])
        return result.returncode == 0

"""Tests for ClaudePRunner (subprocess mock, Max credit conserving)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bonsai.runners.base import RunnerError, RunnerRequest
from bonsai.runners.claude_p import ClaudePRunner


async def _async_lines(*lines: bytes):
    for line in lines:
        yield line


def _make_req(tmp_path: Path) -> RunnerRequest:
    return RunnerRequest(
        role="worker",
        model="claude-opus-4-7",
        prompt="Do the task.",
        workdir=tmp_path,
    )


class TestClaudePRunnerProtocol:
    def test_name(self):
        assert ClaudePRunner.name == "claude_p"

    def test_supports_tool_allowlist(self):
        runner = ClaudePRunner()
        assert runner.supports_tool_allowlist() is True


class TestClaudePRunnerStream:
    async def test_stream_yields_stdout_and_completed(self, tmp_path):
        runner = ClaudePRunner()
        req = _make_req(tmp_path)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = _async_lines(b"line1\n", b"## Status: completed\n")
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events = []
            async for ev in runner.stream(req):
                events.append(ev)

        kinds = [e.kind for e in events]
        assert "stdout" in kinds
        assert kinds[-1] == "completed"

    async def test_stream_raises_on_nonzero_exit(self, tmp_path):
        runner = ClaudePRunner()
        req = _make_req(tmp_path)

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = _async_lines(b"error output\n")
        mock_proc.wait = AsyncMock(return_value=1)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RunnerError) as exc_info:
                async for _ in runner.stream(req):
                    pass

        assert exc_info.value.kind == "process_died"

    async def test_stream_includes_system_prompt(self, tmp_path):
        runner = ClaudePRunner()
        req = RunnerRequest(
            role="worker",
            model="claude-opus-4-7",
            prompt="Do the task.",
            workdir=tmp_path,
            system_prompt="You are a helpful assistant.",
        )

        captured_cmd: list[str] = []

        async def fake_create(*args, **kwargs):
            captured_cmd.extend(args)
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = _async_lines(b"## Status: completed\n")
            mock_proc.wait = AsyncMock(return_value=0)
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=fake_create):
            async for _ in runner.stream(req):
                pass

        full_cmd = " ".join(str(a) for a in captured_cmd)
        assert "--system-prompt" in full_cmd or "system" in full_cmd.lower()

    async def test_stream_timeout_raises_runner_error(self, tmp_path):
        import asyncio as _asyncio

        runner = ClaudePRunner(timeout_sec=0.05)
        req = _make_req(tmp_path)

        async def _hanging_stdout():
            await _asyncio.sleep(999)
            yield b""

        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdout = _hanging_stdout()
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RunnerError) as exc_info:
                async for _ in runner.stream(req):
                    pass

        assert exc_info.value.kind == "timeout"

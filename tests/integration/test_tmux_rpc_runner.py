"""Integration tests for TmuxRpcRunner with a mocked TmuxSession."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bonsai.runners.base import RunnerError, RunnerRequest
from bonsai.runners.tmux_rpc import RateLimiter, TmuxRpcRunner


def _make_req(tmp_path: Path, session_name: str = "test-session") -> RunnerRequest:
    return RunnerRequest(
        role="worker",
        model="claude-opus-4-7",
        prompt="Do the task.",
        workdir=tmp_path,
        runner_config={
            "session_name": session_name,
            "run_dir": str(tmp_path / ".auto-dev" / "worker"),
        },
    )


def _fast_runner() -> TmuxRpcRunner:
    return TmuxRpcRunner(
        idle_timeout_sec=0.15,
        poll_interval_sec=0.05,
        rate_limiter=RateLimiter(min_interval=0.0),
    )


class TestTmuxRpcRunnerStream:
    async def test_stream_completes_after_idle(self, tmp_path):
        runner = _fast_runner()
        req = _make_req(tmp_path)

        call_count = 0

        def fake_capture():
            nonlocal call_count
            call_count += 1
            return "output line"

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = True
            instance.capture_pane.side_effect = fake_capture

            events = []
            async for ev in runner.stream(req):
                events.append(ev)

        kinds = [e.kind for e in events]
        assert "completed" in kinds
        assert kinds[-1] == "completed"

    async def test_stream_raises_when_session_missing(self, tmp_path):
        runner = _fast_runner()
        req = _make_req(tmp_path)

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = False

            with pytest.raises(RunnerError) as exc_info:
                async for _ in runner.stream(req):
                    pass

        assert exc_info.value.kind == "process_died"

    async def test_stream_yields_stdout_on_output_change(self, tmp_path):
        runner = _fast_runner()
        req = _make_req(tmp_path)

        outputs = ["first output", "second output", "second output", "second output"]
        output_iter = iter(outputs)

        def fake_capture():
            try:
                return next(output_iter)
            except StopIteration:
                return "second output"

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = True
            instance.capture_pane.side_effect = fake_capture

            events = []
            async for ev in runner.stream(req):
                events.append(ev)

        stdout_events = [e for e in events if e.kind == "stdout"]
        texts = [e.payload.get("text", "") for e in stdout_events]
        assert any("second output" in t for t in texts)

    async def test_stream_raises_on_capture_failure(self, tmp_path):
        runner = _fast_runner()
        req = _make_req(tmp_path)

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = True
            instance.capture_pane.side_effect = RuntimeError("pane gone")

            with pytest.raises(RunnerError) as exc_info:
                async for _ in runner.stream(req):
                    pass

        assert exc_info.value.kind == "process_died"

    async def test_run_returns_runner_result(self, tmp_path):
        runner = _fast_runner()
        req = _make_req(tmp_path)

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = True
            instance.capture_pane.return_value = "done"

            result = await runner.run(req)

        assert result.exit_code == 0
        assert result.completed_marker is True
        assert result.duration_ms >= 0

    async def test_boot_cmd_is_sent(self, tmp_path):
        runner = _fast_runner()
        req = RunnerRequest(
            role="worker",
            model="m",
            prompt="p",
            workdir=tmp_path,
            runner_config={
                "session_name": "s",
                "run_dir": str(tmp_path),
                "boot_cmd": "bonsai worker-boot myplan",
            },
        )

        with patch("bonsai.runners.tmux_rpc.TmuxSession") as MockSession:
            instance = MockSession.return_value
            instance.exists.return_value = True
            instance.capture_pane.return_value = "done"

            events = []
            async for ev in runner.stream(req):
                events.append(ev)

        instance.send_keys.assert_called_once_with("bonsai worker-boot myplan")

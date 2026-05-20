"""Tests for RunnerError must-1 semantics: fatal errors raise, never swallow."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from bonsai.runners.base import RunnerError, RunnerEvent, RunnerRequest


class TestRunnerErrorConstruction:
    def test_valid_kinds(self):
        for kind in ("timeout", "process_died", "ansi_parse_failed", "rate_limit", "tos_violation"):
            err = RunnerError(kind=kind, detail="something went wrong")
            assert err.kind == kind
            assert "something went wrong" in str(err)

    def test_invalid_kind_raises(self):
        with pytest.raises(AssertionError, match="must be one of"):
            RunnerError(kind="mystery_failure", detail="oops")

    def test_str_includes_kind_and_detail(self):
        err = RunnerError(kind="timeout", detail="exceeded 1800s")
        assert "timeout" in str(err)
        assert "exceeded 1800s" in str(err)

    def test_is_exception_subclass(self):
        err = RunnerError(kind="process_died", detail="tmux gone")
        assert isinstance(err, Exception)


class TestRunnerErrorPropagation:
    """Verify that stream() raising RunnerError propagates to the caller."""

    async def test_runner_error_propagates_from_stream(self, tmp_path):

        class BrokenRunner:
            name = "broken"

            async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
                yield RunnerEvent(kind="stdout", payload={"text": "starting"})
                raise RunnerError("process_died", "session lost")
                yield RunnerEvent(kind="completed", payload={})  # type: ignore[misc]

            def supports_tool_allowlist(self) -> bool:
                return False

        runner = BrokenRunner()
        req = RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path)

        with pytest.raises(RunnerError) as exc_info:
            async for _ in runner.stream(req):
                pass

        assert exc_info.value.kind == "process_died"

    async def test_runner_error_not_swallowed_mid_stream(self, tmp_path):
        """Caller must NOT catch RunnerError silently — test the call site pattern."""

        class TimingOutRunner:
            name = "timing_out"

            async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
                for i in range(3):
                    yield RunnerEvent(kind="stdout", payload={"line": i})
                raise RunnerError("timeout", "exceeded 1800s")
                yield RunnerEvent(kind="completed", payload={})  # type: ignore[misc]

            def supports_tool_allowlist(self) -> bool:
                return False

        runner = TimingOutRunner()
        req = RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path)

        collected = []
        caught_error: RunnerError | None = None
        try:
            async for ev in runner.stream(req):
                collected.append(ev)
        except RunnerError as e:
            caught_error = e

        assert len(collected) == 3
        assert caught_error is not None
        assert caught_error.kind == "timeout"

    def test_recoverable_error_event_is_not_runner_error(self):
        """kind='error' RunnerEvent is recoverable and must NOT raise RunnerError."""
        ev = RunnerEvent(kind="error", payload={"msg": "tool call failed, retrying"})
        assert ev.kind == "error"
        assert not isinstance(ev, RunnerError)

    async def test_completed_event_ends_stream(self, tmp_path):
        """A well-behaved runner ends with kind='completed' and does not raise."""

        class GoodRunner:
            name = "good"

            async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
                yield RunnerEvent(kind="stdout", payload={"text": "working"})
                yield RunnerEvent(kind="error", payload={"msg": "minor hiccup"})
                yield RunnerEvent(kind="completed", payload={"status": "ok"})

            def supports_tool_allowlist(self) -> bool:
                return True

        runner = GoodRunner()
        req = RunnerRequest(role="reviewer", model="m", prompt="p", workdir=tmp_path)

        events = []
        async for ev in runner.stream(req):
            events.append(ev)

        assert events[-1].kind == "completed"
        kinds = [e.kind for e in events]
        assert "error" in kinds  # recoverable error present

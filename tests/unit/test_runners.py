"""Tests for Runner Protocol conformance via a MockRunner."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from pydantic import ValidationError

from bonsai.runners.base import (
    Runner,
    RunnerError,
    RunnerEvent,
    RunnerRequest,
    RunnerResult,
)

# ---------------------------------------------------------------------------
# Minimal MockRunner
# ---------------------------------------------------------------------------


class MockRunner:
    name = "mock"

    async def run(self, req: RunnerRequest) -> RunnerResult:
        events = []
        async for ev in self.stream(req):
            events.append(ev)
        return RunnerResult(
            exit_code=0,
            stdout_path=req.workdir / "stdout.log",
            completed_marker=True,
            duration_ms=10,
        )

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "hello"})
        yield RunnerEvent(kind="completed", payload={})

    def supports_tool_allowlist(self) -> bool:
        return False


class FatalMockRunner:
    """Always raises RunnerError from stream()."""

    name = "fatal_mock"

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        raise AssertionError("should not reach here")

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "starting"})
        raise RunnerError("process_died", "tmux session vanished")
        # mypy: unreachable, but needed for generator typing
        yield RunnerEvent(kind="completed", payload={})  # type: ignore[misc]

    def supports_tool_allowlist(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_mock_runner_satisfies_protocol(self):
        runner = MockRunner()
        assert isinstance(runner, Runner)

    def test_fatal_mock_runner_satisfies_protocol(self):
        runner = FatalMockRunner()
        assert isinstance(runner, Runner)

    def test_name_attribute(self):
        assert MockRunner.name == "mock"

    def test_supports_tool_allowlist_returns_bool(self):
        runner = MockRunner()
        result = runner.supports_tool_allowlist()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# RunnerRequest validation
# ---------------------------------------------------------------------------


class TestRunnerRequest:
    def test_valid_request(self, tmp_path):
        req = RunnerRequest(
            role="worker",
            model="claude-opus-4-7",
            prompt="Do the task.",
            workdir=tmp_path,
        )
        assert req.role == "worker"
        assert req.timeout_sec == 1800

    def test_invalid_role(self, tmp_path):
        with pytest.raises(ValidationError):
            RunnerRequest(role="god", model="x", prompt="p", workdir=tmp_path)

    def test_skills_dir_optional(self, tmp_path):
        req = RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path)
        assert req.skills_dir is None

        req2 = RunnerRequest(
            role="worker", model="m", prompt="p", workdir=tmp_path, skills_dir=tmp_path
        )
        assert req2.skills_dir == tmp_path

    def test_extra_fields_forbidden(self, tmp_path):
        with pytest.raises(ValidationError):
            RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path, bad_field="x")


# ---------------------------------------------------------------------------
# RunnerEvent validation
# ---------------------------------------------------------------------------


class TestRunnerEvent:
    def test_valid_event_kinds(self):
        for kind in ("stdout", "tool_call", "tool_result", "error", "completed"):
            ev = RunnerEvent(kind=kind)
            assert ev.kind == kind

    def test_invalid_kind(self):
        with pytest.raises(ValidationError):
            RunnerEvent(kind="unknown")

    def test_ts_auto_populated(self):
        ev = RunnerEvent(kind="stdout")
        assert ev.ts  # non-empty

    def test_extra_fields_ignored(self):
        ev = RunnerEvent(kind="stdout", future_field="ok")
        assert not hasattr(ev, "future_field")


# ---------------------------------------------------------------------------
# RunnerResult validation
# ---------------------------------------------------------------------------


class TestRunnerResult:
    def test_valid_result(self, tmp_path):
        r = RunnerResult(
            exit_code=0,
            stdout_path=tmp_path / "out.log",
            completed_marker=True,
            duration_ms=500,
        )
        assert r.error_kind is None

    def test_error_kind_valid(self, tmp_path):
        r = RunnerResult(
            exit_code=1,
            stdout_path=tmp_path / "out.log",
            completed_marker=False,
            duration_ms=100,
            error_kind="timeout",
        )
        assert r.error_kind == "timeout"

    def test_error_kind_invalid(self, tmp_path):
        with pytest.raises(ValidationError):
            RunnerResult(
                exit_code=1,
                stdout_path=tmp_path / "out.log",
                completed_marker=False,
                duration_ms=100,
                error_kind="mystery",
            )


# ---------------------------------------------------------------------------
# Mock stream integration
# ---------------------------------------------------------------------------


class TestMockRunnerStream:
    async def test_stream_yields_completed_last(self, tmp_path):
        runner = MockRunner()
        req = RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path)
        events = []
        async for ev in runner.stream(req):
            events.append(ev)
        assert events[-1].kind == "completed"

    async def test_run_returns_result(self, tmp_path):
        runner = MockRunner()
        req = RunnerRequest(role="worker", model="m", prompt="p", workdir=tmp_path)
        result = await runner.run(req)
        assert isinstance(result, RunnerResult)
        assert result.exit_code == 0

"""Integration tests for Supervisor state machine — all transitions covered."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from bonsai.roles.supervisor import Supervisor
from bonsai.runners.base import RunnerEvent, RunnerRequest, RunnerResult
from bonsai.state.plan import set_plan_status

SAMPLE_PLAN = """\
# Test Plan

- [ ] T1: first task
- [ ] T2: second task

"""


def _make_plan(tmp_path: Path) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(SAMPLE_PLAN)
    return p


class CompletingRunner:
    name = "mock"

    def __init__(self, plan_path: Path) -> None:
        self._plan_path = plan_path

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "done"})
        set_plan_status(self._plan_path, "completed")
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return False


class FailingThenCompletingRunner:
    """Fails twice then completes — tests restart logic."""

    name = "mock"

    def __init__(self, plan_path: Path) -> None:
        self._plan_path = plan_path
        self._calls = 0

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        self._calls += 1
        if self._calls < 3:
            set_plan_status(self._plan_path, "failed")
        else:
            set_plan_status(self._plan_path, "completed")
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return False


class NeedsInputRunner:
    name = "mock"

    def __init__(self, plan_path: Path, answer_after: int = 1) -> None:
        self._plan_path = plan_path
        self._calls = 0
        self._answer_after = answer_after

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        self._calls += 1
        if self._calls <= self._answer_after:
            set_plan_status(
                self._plan_path,
                "needs_input",
                pending_question="Which approach?",
                question_context="Context",
            )
        else:
            set_plan_status(self._plan_path, "completed")
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return False


class TestSupervisorStateTransitions:
    async def test_completed_path(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = CompletingRunner(plan_path)
        supervisor = Supervisor(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
        )
        result = await supervisor.run()
        assert result == "completed"

    async def test_failed_then_restarted_then_completed(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = FailingThenCompletingRunner(plan_path)
        supervisor = Supervisor(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
            max_restarts=5,
        )
        result = await supervisor.run()
        assert result == "completed"
        assert runner._calls == 3

    async def test_max_restarts_exceeded(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        class AlwaysFailRunner:
            name = "mock"

            def __init__(self, p):
                self._p = p

            async def stream(self, req):
                set_plan_status(self._p, "failed")
                yield RunnerEvent(kind="completed", payload={})

            async def run(self, req):
                async for _ in self.stream(req):
                    pass
                return RunnerResult(
                    exit_code=1, stdout_path=req.workdir, completed_marker=False, duration_ms=1
                )

            def supports_tool_allowlist(self):
                return False

        runner = AlwaysFailRunner(plan_path)
        supervisor = Supervisor(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
            max_restarts=2,
        )
        result = await supervisor.run()
        assert result == "failed"

    async def test_needs_input_writes_answer(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = NeedsInputRunner(plan_path, answer_after=1)
        supervisor = Supervisor(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
            answer_provider=lambda q, ctx: "Use approach A",
        )
        result = await supervisor.run()
        assert result == "completed"

    async def test_needs_input_without_provider_stops(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = NeedsInputRunner(plan_path, answer_after=5)
        supervisor = Supervisor(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
            answer_provider=None,
        )
        result = await supervisor.run()
        assert result == "needs_input"

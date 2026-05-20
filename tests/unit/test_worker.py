"""Tests for Worker role — 1-cycle execution with MockRunner."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from bonsai.roles.worker import Worker
from bonsai.runners.base import RunnerEvent, RunnerRequest, RunnerResult
from bonsai.state.events import EventLogger
from bonsai.state.plan import set_plan_status
from bonsai.state.state_io import read_answer, write_answer

SAMPLE_PLAN = """\
# Test Plan

## Tasks
- [ ] T1: first task
- [ ] T2: second task

"""


class CompletingMockRunner:
    name = "mock"

    def __init__(self, plan_path: Path) -> None:
        self._plan_path = plan_path

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "working"})
        set_plan_status(self._plan_path, "completed")
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0,
            stdout_path=req.workdir / "out.log",
            completed_marker=True,
            duration_ms=10,
        )

    def supports_tool_allowlist(self) -> bool:
        return False


class NeedsInputMockRunner:
    name = "mock_needs_input"

    def __init__(self, plan_path: Path) -> None:
        self._plan_path = plan_path

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "need help"})
        set_plan_status(
            self._plan_path,
            "needs_input",
            pending_question="Which approach?",
            question_context="Ctx",
        )
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0,
            stdout_path=req.workdir / "out.log",
            completed_marker=False,
            duration_ms=10,
        )

    def supports_tool_allowlist(self) -> bool:
        return False


class TestWorkerOneCycle:
    async def test_run_completed(self, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(SAMPLE_PLAN)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = CompletingMockRunner(plan_file)
        worker = Worker(
            plan_path=plan_file,
            run_dir=run_dir,
            runner=runner,
            pid=1,
        )

        final_status = await worker.run_once()
        assert final_status == "completed"

    async def test_run_writes_events(self, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(SAMPLE_PLAN)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = CompletingMockRunner(plan_file)
        worker = Worker(plan_path=plan_file, run_dir=run_dir, runner=runner, pid=1)
        await worker.run_once()

        logger = EventLogger(run_dir, "worker")
        events = logger.read_all()
        event_types = [e.event_type for e in events]
        assert "worker_start" in event_types
        assert "worker_done" in event_types

    async def test_run_needs_input(self, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(SAMPLE_PLAN)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = NeedsInputMockRunner(plan_file)
        worker = Worker(plan_path=plan_file, run_dir=run_dir, runner=runner, pid=1)

        final_status = await worker.run_once()
        assert final_status == "needs_input"

    async def test_answer_consumed_when_present(self, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(SAMPLE_PLAN)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        write_answer(run_dir, "Use approach A.")
        runner = CompletingMockRunner(plan_file)
        worker = Worker(plan_path=plan_file, run_dir=run_dir, runner=runner, pid=1)

        await worker.run_once()
        assert read_answer(run_dir) is None

    async def test_heartbeat_task_started_and_cancelled(self, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_file.write_text(SAMPLE_PLAN)
        run_dir = tmp_path / ".auto-dev" / "worker"
        run_dir.mkdir(parents=True)

        runner = CompletingMockRunner(plan_file)
        worker = Worker(
            plan_path=plan_file,
            run_dir=run_dir,
            runner=runner,
            pid=1,
            heartbeat_interval=0.05,
        )
        await worker.run_once()

        hb_file = run_dir / "heartbeat.json"
        assert hb_file.exists()

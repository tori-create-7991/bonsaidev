"""Integration tests for Reviewer — 1-3 rounds, CLEAR/ISSUES paths."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from bonsai.roles.reviewer import Reviewer, ReviewOutcome
from bonsai.runners.base import RunnerEvent, RunnerRequest, RunnerResult

SAMPLE_PLAN = """\
# Test Plan

- [x] T1: first task
- [x] T2: second task

## Status: completed
"""


def _make_plan(tmp_path: Path) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(SAMPLE_PLAN)
    return p


class ClearRunner:
    name = "mock"

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "REVIEW_OUTCOME: CLEAR"})
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return True


class IssuesRunner:
    name = "mock"

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        yield RunnerEvent(kind="stdout", payload={"text": "REVIEW_OUTCOME: ISSUES\nFix X and Y."})
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return True


class IssuesThenClearRunner:
    """Returns ISSUES on first call, CLEAR on second."""

    name = "mock"

    def __init__(self) -> None:
        self._calls = 0

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        self._calls += 1
        if self._calls == 1:
            yield RunnerEvent(kind="stdout", payload={"text": "REVIEW_OUTCOME: ISSUES\nFix X."})
        else:
            yield RunnerEvent(kind="stdout", payload={"text": "REVIEW_OUTCOME: CLEAR"})
        yield RunnerEvent(kind="completed", payload={})

    async def run(self, req: RunnerRequest) -> RunnerResult:
        async for _ in self.stream(req):
            pass
        return RunnerResult(
            exit_code=0, stdout_path=req.workdir, completed_marker=True, duration_ms=1
        )

    def supports_tool_allowlist(self) -> bool:
        return True


class TestReviewerRounds:
    async def test_clear_on_first_round(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev"
        run_dir.mkdir()

        reviewer = Reviewer(plan_path=plan_path, run_dir=run_dir, runner=ClearRunner())
        outcome = await reviewer.review()
        assert outcome == ReviewOutcome.CLEAR

    async def test_issues_on_first_round(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev"
        run_dir.mkdir()

        reviewer = Reviewer(plan_path=plan_path, run_dir=run_dir, runner=IssuesRunner())
        outcome = await reviewer.review()
        assert outcome == ReviewOutcome.ISSUES

    async def test_issues_then_clear(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev"
        run_dir.mkdir()

        runner = IssuesThenClearRunner()
        reviewer = Reviewer(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=runner,
            max_rounds=3,
        )
        outcome = await reviewer.review()
        assert outcome == ReviewOutcome.CLEAR
        assert runner._calls == 2

    async def test_max_rounds_exceeded_returns_issues(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev"
        run_dir.mkdir()

        reviewer = Reviewer(
            plan_path=plan_path,
            run_dir=run_dir,
            runner=IssuesRunner(),
            max_rounds=2,
        )
        outcome = await reviewer.review()
        assert outcome == ReviewOutcome.ISSUES

    async def test_review_logs_events(self, tmp_path):
        plan_path = _make_plan(tmp_path)
        run_dir = tmp_path / ".auto-dev"
        run_dir.mkdir()

        reviewer = Reviewer(plan_path=plan_path, run_dir=run_dir, runner=ClearRunner())
        await reviewer.review()

        from bonsai.state.events import EventLogger

        events = EventLogger(run_dir, "reviewer").read_all()
        types = [e.event_type for e in events]
        assert "review_start" in types
        assert "review_done" in types

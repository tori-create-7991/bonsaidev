"""Reviewer role — runs 1-N review rounds and returns CLEAR or ISSUES.

Completion detection: looks for 'REVIEW_OUTCOME: CLEAR' or 'REVIEW_OUTCOME: ISSUES'
in the stream's stdout events. If neither appears, defaults to ISSUES.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from bonsai.runners.base import Runner, RunnerRequest
from bonsai.state.events import EventLogger
from bonsai.state.plan import parse_plan


class ReviewOutcome(StrEnum):
    CLEAR = "CLEAR"
    ISSUES = "ISSUES"


class Reviewer:
    def __init__(
        self,
        *,
        plan_path: Path,
        run_dir: Path,
        runner: Runner,
        max_rounds: int = 3,
        model: str = "claude-opus-4-7",
    ) -> None:
        self._plan_path = plan_path
        self._run_dir = run_dir
        self._runner = runner
        self._max_rounds = max_rounds
        self._model = model
        self._events = EventLogger(run_dir, "reviewer")

    async def review(self) -> ReviewOutcome:
        plan = parse_plan(self._plan_path)
        self._events.append("review_start", {"plan_name": plan.plan_name})

        outcome = ReviewOutcome.ISSUES
        for round_num in range(1, self._max_rounds + 1):
            outcome = await self._run_round(plan.plan_name, round_num)
            if outcome == ReviewOutcome.CLEAR:
                break

        self._events.append("review_done", {"outcome": outcome.value, "rounds": round_num})
        return outcome

    async def _run_round(self, plan_name: str, round_num: int) -> ReviewOutcome:
        req = RunnerRequest(
            role="reviewer",
            model=self._model,
            prompt=_build_review_prompt(plan_name, round_num),
            workdir=self._plan_path.parent,
            runner_config={
                "run_dir": str(self._run_dir),
                "session_name": f"bonsai-reviewer-{plan_name}",
            },
        )

        output_lines: list[str] = []
        async for ev in self._runner.stream(req):
            if ev.kind == "stdout":
                text = ev.payload.get("text", "")
                output_lines.append(text)

        full_output = "\n".join(output_lines)
        return _parse_outcome(full_output)


def _parse_outcome(output: str) -> ReviewOutcome:
    if "REVIEW_OUTCOME: CLEAR" in output:
        return ReviewOutcome.CLEAR
    return ReviewOutcome.ISSUES


def _build_review_prompt(plan_name: str, round_num: int) -> str:
    return (
        f"Review the implementation for plan '{plan_name}' (round {round_num}).\n\n"
        "Check: tests pass, ruff clean, no regressions, tasks match plan.\n\n"
        "Respond with exactly one of:\n"
        "  REVIEW_OUTCOME: CLEAR\n"
        "  REVIEW_OUTCOME: ISSUES\n"
        "followed by details if ISSUES."
    )

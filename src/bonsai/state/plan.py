"""Plan .md parser and mutators.

State layout (plan B):
  .plans/<name>/plan.md   — human-readable plan with checkbox tasks + Status line
  .auto-dev/<name>/       — tool state (heartbeat, events, answer)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bonsai.state.schemas import TaskStatus

_TASK_RE = re.compile(r"^- \[( |x)\] (.+)$", re.MULTILINE)
_STATUS_RE = re.compile(r"^## Status:\s*(\S+)", re.MULTILINE)
_QUESTION_RE = re.compile(r"^## Pending Question:\s*(.+)$", re.MULTILINE)
_CONTEXT_RE = re.compile(r"^## Question Context:\s*(.+)$", re.MULTILINE)


@dataclass
class PlanState:
    plan_name: str
    path: Path
    tasks: list[TaskStatus]
    status: str | None
    pending_question: str | None = None
    question_context: str | None = None

    @property
    def total_tasks(self) -> int:
        return len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        return sum(1 for t in self.tasks if t.done)

    @property
    def next_task(self) -> TaskStatus | None:
        for t in self.tasks:
            if not t.done:
                return t
        return None


def parse_plan(path: Path) -> PlanState:
    text = path.read_text()

    tasks = [
        TaskStatus(index=i, label=m.group(2).strip(), done=(m.group(1) == "x"))
        for i, m in enumerate(_TASK_RE.finditer(text))
    ]

    status_match = _STATUS_RE.search(text)
    status = status_match.group(1) if status_match else None

    question_match = _QUESTION_RE.search(text)
    pending_question = question_match.group(1).strip() if question_match else None

    context_match = _CONTEXT_RE.search(text)
    question_context = context_match.group(1).strip() if context_match else None

    return PlanState(
        plan_name=path.parent.name,
        path=path,
        tasks=tasks,
        status=status,
        pending_question=pending_question,
        question_context=question_context,
    )


def update_task_status(path: Path, task_index: int, done: bool) -> None:
    """Toggle the checkbox for the task at task_index (0-based among all checkbox lines)."""
    text = path.read_text()
    matches = list(_TASK_RE.finditer(text))
    if task_index >= len(matches):
        raise IndexError(f"task_index {task_index} out of range ({len(matches)} tasks)")

    m = matches[task_index]
    new_mark = "x" if done else " "
    new_text = text[: m.start(1)] + new_mark + text[m.end(1) :]
    path.write_text(new_text)


def set_plan_status(
    path: Path,
    status: str,
    *,
    pending_question: str | None = None,
    question_context: str | None = None,
) -> None:
    """Rewrite the ## Status line (and optional question lines) at the end of the plan."""
    text = path.read_text()

    # Strip existing Status / Pending Question / Question Context lines
    text = re.sub(r"\n## Status:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n## Pending Question:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n## Question Context:.*$", "", text, flags=re.MULTILINE)
    text = text.rstrip()

    suffix = f"\n\n## Status: {status}"
    if pending_question:
        suffix += f"\n## Pending Question: {pending_question}"
    if question_context:
        suffix += f"\n## Question Context: {question_context}"
    suffix += "\n"

    path.write_text(text + suffix)

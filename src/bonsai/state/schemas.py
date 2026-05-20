"""Pydantic v2 schemas for bonsai state objects.

Write models use extra="forbid" to catch typos early.
Read models use extra="ignore" for forward-compatibility with future fields.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Shared base classes
# ---------------------------------------------------------------------------


class _WriteModel(BaseModel):
    model_config = {"extra": "forbid"}


class _ReadModel(BaseModel):
    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

_HeartbeatStatus = Literal["running", "idle", "stopped"]


class HeartbeatState(_WriteModel):
    plan_name: str
    pid: int
    status: _HeartbeatStatus
    task_index: int
    current_task: str | None = None


class HeartbeatStateRead(_ReadModel):
    plan_name: str
    pid: int
    status: str
    task_index: int
    current_task: str | None = None


# ---------------------------------------------------------------------------
# Plan status
# ---------------------------------------------------------------------------

_PlanStatusValue = Literal["running", "completed", "failed", "needs_input"]


class PlanStatus(_WriteModel):
    plan_name: str
    status: _PlanStatusValue
    total_tasks: int
    completed_tasks: int
    pending_question: str | None = None
    question_context: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"running", "completed", "failed", "needs_input"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {v!r}")
        return v


class PlanStatusRead(_ReadModel):
    plan_name: str
    status: str
    total_tasks: int
    completed_tasks: int
    pending_question: str | None = None
    question_context: str | None = None


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TaskStatus(_WriteModel):
    index: int
    label: str
    done: bool


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class EventRecord(_WriteModel):
    ts: float
    plan_name: str
    event_type: str
    payload: dict[str, Any] = {}


class EventRecordRead(_ReadModel):
    ts: float
    plan_name: str
    event_type: str
    payload: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class PermissionsConfig(_WriteModel):
    plan_name: str
    allow_git_push: bool = False
    allow_external_api: bool = True
    hitl_pr_merge: bool = True
    max_restarts: int = 5
    skills_dir: str | None = None


class PermissionsConfigRead(_ReadModel):
    plan_name: str
    allow_git_push: bool = False
    allow_external_api: bool = True
    hitl_pr_merge: bool = True
    max_restarts: int = 5
    skills_dir: str | None = None

"""Tests for Pydantic v2 schemas (extra="forbid" write / extra="ignore" read)."""

import pytest
from pydantic import ValidationError

from bonsai.state.schemas import (
    EventRecord,
    HeartbeatState,
    PermissionsConfig,
    PlanStatus,
    TaskStatus,
)


class TestHeartbeatState:
    def test_valid_heartbeat(self):
        h = HeartbeatState(plan_name="test", pid=1234, status="running", task_index=0)
        assert h.plan_name == "test"
        assert h.pid == 1234

    def test_extra_fields_forbidden_on_write(self):
        with pytest.raises(ValidationError):
            HeartbeatState(plan_name="x", pid=1, status="running", task_index=0, extra_field="bad")

    def test_extra_fields_ignored_on_read(self):
        from bonsai.state.schemas import HeartbeatStateRead

        h = HeartbeatStateRead.model_validate(
            {"plan_name": "x", "pid": 1, "status": "running", "task_index": 0, "unknown": "ok"}
        )
        assert h.plan_name == "x"
        assert not hasattr(h, "unknown")


class TestPlanStatus:
    def test_valid_statuses(self):
        for s in ("running", "completed", "failed", "needs_input"):
            ps = PlanStatus(status=s, plan_name="p", total_tasks=5, completed_tasks=2)
            assert ps.status == s

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            PlanStatus(status="invalid", plan_name="p", total_tasks=5, completed_tasks=2)


class TestTaskStatus:
    def test_task_unchecked(self):
        t = TaskStatus(index=0, label="A1: do something", done=False)
        assert not t.done

    def test_task_checked(self):
        t = TaskStatus(index=1, label="A2: other", done=True)
        assert t.done


class TestEventRecord:
    def test_valid_event(self):
        import time

        e = EventRecord(
            ts=time.time(),
            plan_name="test",
            event_type="task_start",
            payload={"task_index": 0},
        )
        assert e.event_type == "task_start"

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            EventRecord(ts=1.0, plan_name="p", event_type="x", payload={}, bad="no")


class TestPermissionsConfig:
    def test_defaults(self):
        p = PermissionsConfig(plan_name="test")
        assert p.allow_git_push is False
        assert p.allow_external_api is True
        assert p.hitl_pr_merge is True

    def test_custom(self):
        p = PermissionsConfig(plan_name="test", allow_git_push=True)
        assert p.allow_git_push is True

"""Tests for append-only events.jsonl writer."""

import json

from bonsai.state.events import EventLogger


def test_append_single_event(tmp_path):
    logger = EventLogger(run_dir=tmp_path, plan_name="test")
    logger.append("task_start", {"task_index": 0})

    events_file = tmp_path / "events.jsonl"
    assert events_file.exists()
    lines = events_file.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event_type"] == "task_start"
    assert record["plan_name"] == "test"
    assert record["payload"]["task_index"] == 0
    assert "ts" in record


def test_append_multiple_events(tmp_path):
    logger = EventLogger(run_dir=tmp_path, plan_name="p")
    logger.append("task_start", {"task_index": 0})
    logger.append("task_done", {"task_index": 0})
    logger.append("task_start", {"task_index": 1})

    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 3
    types = [json.loads(line)["event_type"] for line in lines]
    assert types == ["task_start", "task_done", "task_start"]


def test_read_events(tmp_path):
    logger = EventLogger(run_dir=tmp_path, plan_name="p")
    logger.append("ev", {"x": 1})
    logger.append("ev", {"x": 2})

    records = logger.read_all()
    assert len(records) == 2
    assert records[0].payload["x"] == 1
    assert records[1].payload["x"] == 2


def test_events_file_is_append_only(tmp_path):
    logger = EventLogger(run_dir=tmp_path, plan_name="p")
    logger.append("first", {})

    # Create a new logger pointing to same dir
    logger2 = EventLogger(run_dir=tmp_path, plan_name="p")
    logger2.append("second", {})

    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 2


def test_ts_is_monotonically_increasing(tmp_path):
    logger = EventLogger(run_dir=tmp_path, plan_name="p")
    logger.append("a", {})
    logger.append("b", {})

    records = logger.read_all()
    assert records[1].ts >= records[0].ts

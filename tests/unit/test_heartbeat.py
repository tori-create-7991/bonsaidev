"""Tests for heartbeat writer (plan A: independent asyncio task)."""

import asyncio
import json

import pytest

from bonsai.state.heartbeat import HeartbeatWriter


class TestHeartbeatWriter:
    def test_write_creates_file(self, tmp_path):
        writer = HeartbeatWriter(run_dir=tmp_path, plan_name="test", pid=1234)
        writer.write(status="running", task_index=0, current_task="A1: task")

        hb_file = tmp_path / "heartbeat.json"
        assert hb_file.exists()

    def test_write_content(self, tmp_path):
        writer = HeartbeatWriter(run_dir=tmp_path, plan_name="test", pid=1234)
        writer.write(status="running", task_index=2, current_task="A3: task")

        data = json.loads((tmp_path / "heartbeat.json").read_text())
        assert data["plan_name"] == "test"
        assert data["pid"] == 1234
        assert data["status"] == "running"
        assert data["task_index"] == 2
        assert data["current_task"] == "A3: task"

    def test_write_stopped_state(self, tmp_path):
        writer = HeartbeatWriter(run_dir=tmp_path, plan_name="test", pid=99)
        writer.write(status="stopped", task_index=5)

        data = json.loads((tmp_path / "heartbeat.json").read_text())
        assert data["status"] == "stopped"
        assert data["current_task"] is None

    async def test_start_stop_task(self, tmp_path):
        writer = HeartbeatWriter(run_dir=tmp_path, plan_name="p", pid=1, interval=0.05)
        task = await writer.start()

        # Let it tick at least once
        await asyncio.sleep(0.15)

        hb_file = tmp_path / "heartbeat.json"
        assert hb_file.exists()

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    async def test_task_writes_periodically(self, tmp_path):
        writer = HeartbeatWriter(run_dir=tmp_path, plan_name="p", pid=1, interval=0.05)
        writer.write(status="running", task_index=0)

        task = await writer.start()
        await asyncio.sleep(0.2)

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        # File should still exist with valid JSON
        data = json.loads((tmp_path / "heartbeat.json").read_text())
        assert data["status"] == "running"

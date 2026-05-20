"""Tests for Notion integration — subprocess bridge to notion.sh."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bonsai.integrations.notion import NotionBridge, NotionError


class TestNotionBridgeUpdateStatus:
    def test_update_status_calls_script(self, tmp_path):
        script = tmp_path / "notion.sh"
        script.write_text("#!/bin/bash\necho ok")
        script.chmod(0o755)

        bridge = NotionBridge(script_path=script)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
            bridge.update_status("page-id-123", "Doing")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert str(script) in args
        assert "update-status" in args
        assert "page-id-123" in args
        assert "Doing" in args

    def test_update_status_valid_statuses(self, tmp_path):
        script = tmp_path / "notion.sh"
        script.write_text("#!/bin/bash\necho ok")
        script.chmod(0o755)
        bridge = NotionBridge(script_path=script)

        for status in ("Doing", "Done", "Skip"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
                bridge.update_status("pid", status)

    def test_update_status_invalid_status_raises(self, tmp_path):
        script = tmp_path / "notion.sh"
        script.write_text("#!/bin/bash\necho ok")
        script.chmod(0o755)
        bridge = NotionBridge(script_path=script)

        with pytest.raises(ValueError, match="status"):
            bridge.update_status("pid", "Invalid")

    def test_update_status_nonzero_exit_raises_notion_error(self, tmp_path):
        script = tmp_path / "notion.sh"
        script.write_text("#!/bin/bash\nexit 1")
        script.chmod(0o755)
        bridge = NotionBridge(script_path=script)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
            with pytest.raises(NotionError, match="error msg"):
                bridge.update_status("pid", "Done")

    def test_script_not_found_raises_notion_error(self):
        bridge = NotionBridge(script_path=Path("/nonexistent/notion.sh"))

        with pytest.raises(NotionError, match="not found"):
            bridge.update_status("pid", "Done")

    def test_default_script_path_is_resolved(self):
        bridge = NotionBridge()
        assert bridge.script_path is not None

    def test_returns_stdout(self, tmp_path):
        script = tmp_path / "notion.sh"
        script.write_text("#!/bin/bash\necho 'updated'")
        script.chmod(0o755)
        bridge = NotionBridge(script_path=script)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="updated\n", stderr="")
            result = bridge.update_status("pid", "Done")

        assert "updated" in result

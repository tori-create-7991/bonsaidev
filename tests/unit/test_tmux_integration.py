"""Tests for tmux integration layer (subprocess mock)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bonsai.integrations.tmux import TmuxSession


class TestTmuxSessionStart:
    def test_new_session_calls_tmux(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("test-session")
            session.new_session(cwd="/tmp")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "tmux" in args
            assert "new-session" in args
            assert "test-session" in args

    def test_new_session_raises_on_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            session = TmuxSession("test-session")
            with pytest.raises(RuntimeError, match="tmux new-session failed"):
                session.new_session(cwd="/tmp")


class TestTmuxSessionSendKeys:
    def test_send_keys_calls_tmux(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("s")
            session.send_keys("echo hello")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "send-keys" in args
            assert "echo hello" in args

    def test_send_keys_appends_enter_by_default(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("s")
            session.send_keys("ls")
            args = mock_run.call_args[0][0]
            assert "Enter" in args

    def test_send_keys_raises_on_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            session = TmuxSession("s")
            with pytest.raises(RuntimeError, match="tmux send-keys failed"):
                session.send_keys("cmd")


class TestTmuxSessionCapturePare:
    def test_capture_pane_returns_output(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\n", stderr="")
            session = TmuxSession("s")
            output = session.capture_pane()
            assert output == "line1\nline2\n"
            args = mock_run.call_args[0][0]
            assert "capture-pane" in args

    def test_capture_pane_raises_on_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            session = TmuxSession("s")
            with pytest.raises(RuntimeError, match="tmux capture-pane failed"):
                session.capture_pane()


class TestTmuxSessionPipePare:
    def test_pipe_pane_start(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("s")
            session.pipe_pane("/tmp/worker.log")
            args = mock_run.call_args[0][0]
            assert "pipe-pane" in args
            assert "/tmp/worker.log" in " ".join(args)

    def test_pipe_pane_stop(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("s")
            session.pipe_pane(None)
            args = mock_run.call_args[0][0]
            assert "pipe-pane" in args


class TestTmuxSessionKill:
    def test_kill_session_calls_tmux(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            session = TmuxSession("s")
            session.kill_session()
            args = mock_run.call_args[0][0]
            assert "kill-session" in args

    def test_kill_session_ignores_not_found(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="session not found")
            session = TmuxSession("s")
            session.kill_session()  # should not raise

    def test_kill_session_raises_on_other_errors(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="some unexpected error"
            )
            session = TmuxSession("s")
            with pytest.raises(RuntimeError, match="tmux kill-session failed"):
                session.kill_session()


class TestTmuxSessionExists:
    def test_session_exists_true(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="s", stderr="")
            session = TmuxSession("s")
            assert session.exists() is True

    def test_session_exists_false(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            session = TmuxSession("s")
            assert session.exists() is False

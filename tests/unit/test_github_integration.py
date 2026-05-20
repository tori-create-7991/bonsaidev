"""Tests for GitHub integration — gh pr create wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bonsai.integrations.github import GitHubBridge, GitHubError


class TestGitHubBridgeCreatePr:
    def test_create_pr_calls_gh(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://github.com/owner/repo/pull/42\n", stderr=""
            )
            url = bridge.create_pr(title="feat: add X", body="Summary", base="main")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "pr" in args
        assert "create" in args
        assert "--title" in args
        assert "feat: add X" in args
        assert "--body" in args
        assert "--base" in args
        assert "main" in args
        assert url == "https://github.com/owner/repo/pull/42"

    def test_create_pr_returns_url_stripped(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="  https://github.com/x/y/pull/7  \n", stderr=""
            )
            url = bridge.create_pr(title="t", body="b", base="main")

        assert url == "https://github.com/x/y/pull/7"

    def test_create_pr_nonzero_exit_raises_github_error(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="gh: auth error")
            with pytest.raises(GitHubError, match="auth error"):
                bridge.create_pr(title="t", body="b", base="main")

    def test_create_pr_default_base_is_main(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://github.com/o/r/pull/1\n", stderr=""
            )
            bridge.create_pr(title="t", body="b")

        args = mock_run.call_args[0][0]
        base_idx = args.index("--base")
        assert args[base_idx + 1] == "main"

    def test_find_existing_pr_returns_url(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="https://github.com/o/r/pull/5\n", stderr=""
            )
            url = bridge.find_existing_pr("feat/my-branch")

        assert url == "https://github.com/o/r/pull/5"

    def test_find_existing_pr_returns_none_when_empty(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            url = bridge.find_existing_pr("feat/no-pr")

        assert url is None

    def test_find_existing_pr_returns_none_on_error(self):
        bridge = GitHubBridge()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            url = bridge.find_existing_pr("feat/no-pr")

        assert url is None

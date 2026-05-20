"""Tests for bonsai CLI — Typer argument parsing and command dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from bonsai.cli import app

runner = CliRunner()


def _make_plan(tmp_path: Path, name: str = "my-plan", tasks: int = 3) -> Path:
    plan_dir = tmp_path / name
    plan_dir.mkdir()
    plan_file = plan_dir / "plan.md"
    lines = [f"# {name}\n"]
    for i in range(tasks):
        lines.append(f"- [ ] Task {i + 1}\n")
    plan_file.write_text("".join(lines))
    return plan_file


class TestStartDryRun:
    def test_dry_run_exits_zero(self, tmp_path):
        plan = _make_plan(tmp_path)
        result = runner.invoke(app, ["start", str(plan), "--dry-run"])
        assert result.exit_code == 0

    def test_dry_run_prints_plan_name(self, tmp_path):
        plan = _make_plan(tmp_path, name="my-plan")
        result = runner.invoke(app, ["start", str(plan), "--dry-run"])
        assert "my-plan" in result.output

    def test_dry_run_prints_task_counts(self, tmp_path):
        plan = _make_plan(tmp_path, tasks=5)
        result = runner.invoke(app, ["start", str(plan), "--dry-run"])
        assert "5" in result.output

    def test_dry_run_prints_dry_run_indicator(self, tmp_path):
        plan = _make_plan(tmp_path)
        result = runner.invoke(app, ["start", str(plan), "--dry-run"])
        assert "dry" in result.output.lower() or "Dry" in result.output

    def test_dry_run_does_not_start_supervisor(self, tmp_path):
        plan = _make_plan(tmp_path)
        with patch("bonsai.cli.asyncio") as mock_asyncio:
            runner.invoke(app, ["start", str(plan), "--dry-run"])
        mock_asyncio.run.assert_not_called()


class TestStartMissingPlan:
    def test_missing_plan_exits_nonzero(self, tmp_path):
        result = runner.invoke(app, ["start", str(tmp_path / "nonexistent" / "plan.md")])
        assert result.exit_code != 0

    def test_missing_plan_prints_error(self, tmp_path):
        result = runner.invoke(app, ["start", str(tmp_path / "nonexistent" / "plan.md")])
        assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestStartNormal:
    def test_start_invokes_supervisor(self, tmp_path):
        plan = _make_plan(tmp_path)

        mock_supervisor = MagicMock()
        mock_supervisor.run = AsyncMock(return_value="completed")

        with (
            patch("bonsai.cli.Supervisor", return_value=mock_supervisor) as mock_sup_cls,
            patch("bonsai.cli.get_runner", return_value=MagicMock()),
        ):
            result = runner.invoke(app, ["start", str(plan)])

        mock_sup_cls.assert_called_once()
        mock_supervisor.run.assert_awaited_once()
        assert result.exit_code == 0

    def test_start_default_runner_is_tmux_rpc(self, tmp_path):
        plan = _make_plan(tmp_path)

        with (
            patch(
                "bonsai.cli.Supervisor",
                return_value=MagicMock(run=AsyncMock(return_value="completed")),
            ),
            patch("bonsai.cli.get_runner") as mock_get_runner,
        ):
            mock_get_runner.return_value = MagicMock()
            runner.invoke(app, ["start", str(plan)])

        mock_get_runner.assert_called_once_with("tmux_rpc")

    def test_start_custom_runner(self, tmp_path):
        plan = _make_plan(tmp_path)

        with (
            patch(
                "bonsai.cli.Supervisor",
                return_value=MagicMock(run=AsyncMock(return_value="completed")),
            ),
            patch("bonsai.cli.get_runner") as mock_get_runner,
        ):
            mock_get_runner.return_value = MagicMock()
            runner.invoke(app, ["start", str(plan), "--runner", "claude_p"])

        mock_get_runner.assert_called_once_with("claude_p")

    def test_start_failed_status_exits_nonzero(self, tmp_path):
        plan = _make_plan(tmp_path)

        with (
            patch(
                "bonsai.cli.Supervisor",
                return_value=MagicMock(run=AsyncMock(return_value="failed")),
            ),
            patch("bonsai.cli.get_runner", return_value=MagicMock()),
        ):
            result = runner.invoke(app, ["start", str(plan)])

        assert result.exit_code != 0

    def test_start_creates_run_dir(self, tmp_path):
        plan = _make_plan(tmp_path, name="alpha")

        with (
            patch(
                "bonsai.cli.Supervisor",
                return_value=MagicMock(run=AsyncMock(return_value="completed")),
            ) as mock_sup,
            patch("bonsai.cli.get_runner", return_value=MagicMock()),
        ):
            runner.invoke(app, ["start", str(plan)])

        call_kwargs = mock_sup.call_args.kwargs
        assert call_kwargs["run_dir"].exists()


class TestAttach:
    def test_attach_calls_tmux(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            runner.invoke(app, ["attach", "my-plan"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "tmux" in args
        assert "attach" in args
        assert any("my-plan" in a for a in args)

    def test_attach_session_name_includes_plan_name(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            runner.invoke(app, ["attach", "cool-feature"])

        args = mock_run.call_args[0][0]
        assert any("cool-feature" in a for a in args)


class TestKill:
    def test_kill_calls_tmux_kill_session(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = runner.invoke(app, ["kill", "my-plan"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "tmux" in args
        assert "kill-session" in args
        assert any("my-plan" in a for a in args)
        assert result.exit_code == 0

    def test_kill_nonzero_exit_propagates(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no session")
            result = runner.invoke(app, ["kill", "ghost-plan"])

        assert result.exit_code != 0

"""bonsai CLI — Typer application.

Commands:
  start  <plan_path> [--runner tmux_rpc|claude_p] [--dry-run] [--run-dir PATH]
  attach <plan_name>
  kill   <plan_name>
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import typer

from bonsai.roles.supervisor import Supervisor
from bonsai.runners.registry import get_runner
from bonsai.state.plan import parse_plan

app = typer.Typer(name="bonsai", help="Autonomous coding agent orchestrator.")


@app.command()
def start(
    plan_path: Path = typer.Argument(..., help="Path to plan.md"),
    runner: str = typer.Option("tmux_rpc", help="Runner to use (tmux_rpc, claude_p)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parse plan and exit without starting"),
    run_dir: Path | None = typer.Option(None, help="Override run directory"),
) -> None:
    """Start autonomous execution of a plan."""
    if not plan_path.exists():
        typer.echo(f"Error: plan file not found: {plan_path}", err=True)
        raise typer.Exit(1)

    plan = parse_plan(plan_path)

    if dry_run:
        typer.echo(f"Plan: {plan.plan_name}")
        typer.echo(f"Total tasks: {plan.total_tasks}")
        typer.echo(f"Completed: {plan.completed_tasks}")
        typer.echo(f"Status: {plan.status or 'pending'}")
        typer.echo("Dry run — not starting.")
        return

    resolved_run_dir = run_dir or (plan_path.parent.parent / ".auto-dev" / plan.plan_name)
    resolved_run_dir.mkdir(parents=True, exist_ok=True)

    runner_instance = get_runner(runner)
    supervisor = Supervisor(
        plan_path=plan_path,
        run_dir=resolved_run_dir,
        runner=runner_instance,
    )

    final_status = asyncio.run(supervisor.run())
    typer.echo(f"Done: {final_status}")
    if final_status != "completed":
        raise typer.Exit(1)


@app.command()
def attach(plan_name: str = typer.Argument(..., help="Plan name to attach to")) -> None:
    """Attach to a running bonsai worker session."""
    session = f"bonsai-worker-{plan_name}"
    result = subprocess.run(["tmux", "attach", "-t", session])
    raise typer.Exit(result.returncode)


@app.command()
def kill(plan_name: str = typer.Argument(..., help="Plan name to kill")) -> None:
    """Kill a running bonsai worker session."""
    session = f"bonsai-worker-{plan_name}"
    result = subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip() or f'no session {session}'}", err=True)
        raise typer.Exit(1)
    typer.echo(f"Killed session {session}")


def main() -> None:
    app()

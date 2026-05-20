"""GitHub integration — thin wrapper around the gh CLI."""

from __future__ import annotations

import subprocess


class GitHubError(Exception):
    pass


class GitHubBridge:
    def create_pr(self, *, title: str, body: str, base: str = "main") -> str:
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--base", base],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitHubError(result.stderr.strip() or f"gh pr create exited {result.returncode}")
        return result.stdout.strip()

    def find_existing_pr(self, branch: str) -> str | None:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "url",
                "--jq",
                ".[0].url // empty",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        url = result.stdout.strip()
        return url if url else None

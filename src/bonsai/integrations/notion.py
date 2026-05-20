"""Notion integration — thin subprocess bridge to the existing notion.sh script."""

from __future__ import annotations

import subprocess
from pathlib import Path

_VALID_STATUSES = frozenset({"Doing", "Done", "Skip"})

_DEFAULT_SCRIPT = (
    Path.home() / "Repositories/my/00_my_env/global-config-sync/scripts/auto-dev/notion.sh"
)


class NotionError(Exception):
    pass


class NotionBridge:
    def __init__(self, script_path: Path | None = None) -> None:
        self.script_path: Path = script_path if script_path is not None else _DEFAULT_SCRIPT

    def update_status(self, page_id: str, status: str) -> str:
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status {status!r}. Must be one of {sorted(_VALID_STATUSES)}")

        if not self.script_path.exists():
            raise NotionError(f"notion.sh not found: {self.script_path}")

        result = subprocess.run(
            [str(self.script_path), "update-status", page_id, status],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise NotionError(result.stderr.strip() or f"notion.sh exited {result.returncode}")

        return result.stdout

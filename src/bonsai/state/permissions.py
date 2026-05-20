"""Permissions loader and policy enforcer for bonsai run sessions."""

from __future__ import annotations

import json
from pathlib import Path

from bonsai.state.schemas import PermissionsConfig, PermissionsConfigRead


def load_permissions(run_dir: Path, plan_name: str) -> PermissionsConfigRead:
    """Load permissions from run_dir/permissions.json, or return defaults."""
    perms_file = run_dir / "permissions.json"
    if not perms_file.exists():
        return PermissionsConfigRead(plan_name=plan_name)
    data = json.loads(perms_file.read_text())
    return PermissionsConfigRead.model_validate(data)


def save_permissions(run_dir: Path, config: PermissionsConfig) -> None:
    """Persist a PermissionsConfig to run_dir/permissions.json."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "permissions.json").write_text(config.model_dump_json(indent=2))


class PermissionsManager:
    """Runtime permissions checker for a single bonsai session."""

    def __init__(self, run_dir: Path, plan_name: str) -> None:
        self._config = load_permissions(run_dir, plan_name)

    def can(self, action: str) -> bool:
        """Return True if the named boolean permission is granted.

        Raises AttributeError for unknown permission names so callers catch
        typos at development time rather than silently granting access.
        """
        value = getattr(self._config, action)
        if not isinstance(value, bool):
            raise AttributeError(f"{action!r} is not a boolean permission field")
        return value

    @property
    def max_restarts(self) -> int:
        return self._config.max_restarts

    @property
    def skills_dir(self) -> str | None:
        return self._config.skills_dir

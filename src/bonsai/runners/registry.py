"""Runner registry — name-to-class resolution with fallback chain."""

from __future__ import annotations

from bonsai.runners.base import Runner
from bonsai.runners.claude_p import ClaudePRunner
from bonsai.runners.tmux_rpc import TmuxRpcRunner

_REGISTRY: dict[str, type] = {
    "tmux_rpc": TmuxRpcRunner,
    "claude_p": ClaudePRunner,
}


def get_runner(name: str) -> Runner:
    """Resolve a runner name to an instance.

    Raises KeyError for unknown names.
    """
    cls = _REGISTRY[name]
    return cls()


def available_runners() -> list[str]:
    return list(_REGISTRY.keys())


def get_runner_with_fallback(names: list[str]) -> Runner:
    """Try each name in order; return the first that resolves.

    Raises ValueError if none resolve.
    """
    errors: list[str] = []
    for name in names:
        try:
            return get_runner(name)
        except KeyError:
            errors.append(name)
    raise ValueError(f"No runner found in fallback chain {names}; available: {available_runners()}")

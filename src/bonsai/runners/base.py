"""Runner Protocol — the moat layer.

All CLI runner implementations (tmux_rpc, claude_p, codex, aider, gemini) must
satisfy the Runner Protocol defined here. This file is intentionally stable:
field names and semantics here are the hardest things to change once runners
are in production.

Design decisions baked in:
- stream() is the primary interface; run() is a convenience wrapper.
- RunnerError (fatal) is distinct from kind="error" events (recoverable).
- skills_dir lets runners resolve SKILL.md files for autonomous-development mode.
- supports_tool_allowlist() lets callers know whether allowed_tools is honored.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field, field_validator


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Wire types
# ---------------------------------------------------------------------------

_EVENT_KINDS = frozenset({"stdout", "tool_call", "tool_result", "error", "completed"})
_ROLES = frozenset({"worker", "supervisor", "reviewer"})
_ERROR_KINDS = frozenset(
    {
        "timeout",
        "process_died",
        "ansi_parse_failed",
        "rate_limit",
        "tos_violation",
        "context_limit",
        "auth_error",
    }
)


class RunnerEvent(BaseModel):
    """Single streaming event emitted by Runner.stream()."""

    ts: str = Field(default_factory=_utcnow_iso)
    kind: str
    payload: dict = Field(default_factory=dict)

    model_config = {"extra": "ignore"}

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        if v not in _EVENT_KINDS:
            raise ValueError(f"kind must be one of {_EVENT_KINDS}, got {v!r}")
        return v


class RunnerRequest(BaseModel):
    """Inputs to a runner invocation."""

    role: str
    model: str
    allowed_tools: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    prompt: str
    workdir: Path
    skills_dir: Path | None = None
    timeout_sec: int = 1800
    runner_config: dict = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in _ROLES:
            raise ValueError(f"role must be one of {_ROLES}, got {v!r}")
        return v


class RunnerResult(BaseModel):
    """Outcome of a completed runner invocation."""

    exit_code: int
    stdout_path: Path
    completed_marker: bool
    duration_ms: int
    trace_id: str | None = None
    error_kind: str | None = None

    model_config = {"extra": "ignore"}

    @field_validator("error_kind")
    @classmethod
    def validate_error_kind(cls, v: str | None) -> str | None:
        if v is not None and v not in _ERROR_KINDS:
            raise ValueError(f"error_kind must be one of {_ERROR_KINDS} or None, got {v!r}")
        return v


class RunnerError(Exception):
    """Fatal runner failure raised from stream() — never swallowed (must 1).

    Distinct from RunnerEvent(kind='error'), which represents recoverable
    errors that still allow the stream to continue to kind='completed'.
    """

    def __init__(self, kind: str, detail: str) -> None:
        # Use assert (not ValueError) — an unknown kind is a programming error,
        # not a runtime condition. ValueError would bypass `except RunnerError` handlers.
        assert kind in _ERROR_KINDS, f"RunnerError.kind must be one of {_ERROR_KINDS}, got {kind!r}"
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}")


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Runner(Protocol):
    """Contract that every CLI runner must satisfy.

    Implementors: TmuxRpcRunner, ClaudePRunner (and future Codex/Aider/Gemini).

    Note on @runtime_checkable: isinstance(obj, Runner) only verifies that the
    required *attributes exist* — it does NOT check return types or async semantics.
    Use mypy/pyright in strict mode to catch signature mismatches at build time.
    """

    name: str

    async def run(self, req: RunnerRequest) -> RunnerResult:
        """Block until the runner finishes; return a RunnerResult.

        Convenience wrapper around stream() for callers that don't need
        incremental output. Fatal failures must raise RunnerError.
        """
        ...

    async def stream(self, req: RunnerRequest) -> AsyncGenerator[RunnerEvent, None]:
        """Yield RunnerEvents until kind='completed'.

        Contract:
        - The final event MUST have kind='completed'.
        - Recoverable errors are yielded as kind='error' events; stream continues.
        - Fatal failures MUST raise RunnerError (never silently return). (must 1)
        - Callers MUST propagate RunnerError upward without swallowing.
        """
        ...

    def supports_tool_allowlist(self) -> bool:
        """Return True if this runner honors RunnerRequest.allowed_tools.

        Claude-family runners return True; others (Gemini --yolo) return False.
        Supervisors use this to decide whether to log a warning.
        """
        ...

# fix-pyproject-devdeps

Migrate `pyproject.toml` from deprecated `[tool.uv] dev-dependencies` to the new
`[dependency-groups]` format to eliminate the deprecation warning that appears on
every `uv run` invocation.

## Context

`uv` introduced `[dependency-groups]` as the standard way to declare dev deps.
The old `[tool.uv] dev-dependencies = [...]` key still works but emits:

```
warning: The `tool.uv.dev-dependencies` field (used in `pyproject.toml`) is deprecated
and will be removed in a future release; use `dependency-groups.dev` instead
```

## Tasks

- [x] Replace `[tool.uv]\ndev-dependencies = [...]` with `[dependency-groups]\ndev = [...]` in `pyproject.toml`
- [x] Run `uv sync --dev` and confirm it resolves without warnings
- [x] Run `uv run pytest --co -q` to confirm test collection still works

## Acceptance criteria

- No deprecation warning on `uv run`
- `uv run pytest` still passes all tests

## Status: completed


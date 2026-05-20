"""Atomic state I/O helpers.

must 2: .answer is written via .answer.<uid>.tmp -> rename to prevent partial reads.
Using a per-write unique suffix avoids races when multiple writers compete.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

_counter_lock = threading.Lock()
_counter = 0


def _unique_tmp(run_dir: Path) -> Path:
    global _counter
    with _counter_lock:
        _counter += 1
        n = _counter
    return run_dir / f".answer.{os.getpid()}.{n}.tmp"


def write_answer(run_dir: Path, content: str) -> None:
    """Atomically write content to run_dir/.answer via a unique tmp file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    tmp = _unique_tmp(run_dir)
    tmp.write_text(content)
    os.replace(tmp, run_dir / ".answer")


def read_answer(run_dir: Path, *, consume: bool = False) -> str | None:
    """Read run_dir/.answer, or None if it does not exist.

    If consume=True, delete the file after reading.
    """
    answer_file = run_dir / ".answer"
    if not answer_file.exists():
        return None
    content = answer_file.read_text()
    if consume:
        answer_file.unlink(missing_ok=True)
    return content

"""Append-only events.jsonl writer/reader."""

from __future__ import annotations

import json
import time
from pathlib import Path

from bonsai.state.schemas import EventRecord, EventRecordRead


class EventLogger:
    def __init__(self, run_dir: Path, plan_name: str) -> None:
        self._path = run_dir / "events.jsonl"
        self._plan_name = plan_name

    def append(self, event_type: str, payload: dict) -> None:
        record = EventRecord(
            ts=time.time(),
            plan_name=self._plan_name,
            event_type=event_type,
            payload=payload,
        )
        with self._path.open("a") as fh:
            fh.write(record.model_dump_json() + "\n")

    def read_all(self) -> list[EventRecordRead]:
        if not self._path.exists():
            return []
        records = []
        for line in self._path.read_text().splitlines():
            line = line.strip()
            if line:
                records.append(EventRecordRead.model_validate(json.loads(line)))
        return records

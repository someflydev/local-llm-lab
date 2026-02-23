from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson


def default_log_path() -> Path:
    date_part = datetime.now(UTC).strftime("%Y-%m-%d")
    return Path("runs") / "logs" / f"{date_part}.jsonl"


def log_event(event: str, payload: dict[str, Any], path: str | Path | None = None) -> Path:
    """Append one structured event record to a JSONL file."""
    log_path = Path(path) if path is not None else default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        "payload": payload,
    }
    with log_path.open("ab") as fh:
        fh.write(orjson.dumps(record))
        fh.write(b"\n")
    return log_path


"""Run logging utilities."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


LOG_DIR = Path(__file__).resolve().parent.parent / "server" / "logs"
LOG_FILE = LOG_DIR / "workflow_runs.jsonl"


def append_run_log(payload: dict[str, Any]) -> None:
    """Append one workflow run record as JSONL."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **payload,
    }
    with LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

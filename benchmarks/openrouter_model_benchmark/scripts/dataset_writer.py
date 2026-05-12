"""
Append-only JSONL writer. Never overwrites existing lines.
Writes successful runs to runs.jsonl, errors to errors.jsonl.
"""

import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
RUNS_FILE = DATA_DIR / "runs.jsonl"
ERRORS_FILE = DATA_DIR / "errors.jsonl"


def _append_line(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_run(record: dict[str, Any]) -> None:
    """Append one completed run record to runs.jsonl."""
    _append_line(RUNS_FILE, record)


def write_error(record: dict[str, Any]) -> None:
    """Append one error record to errors.jsonl."""
    _append_line(ERRORS_FILE, record)


def write_record(record: dict[str, Any]) -> None:
    """Route to runs.jsonl or errors.jsonl based on record['error'] field."""
    if record.get("error") is None:
        write_run(record)
    else:
        write_error(record)


def count_runs() -> int:
    """Return number of lines in runs.jsonl."""
    if not RUNS_FILE.exists():
        return 0
    with RUNS_FILE.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def count_errors() -> int:
    """Return number of lines in errors.jsonl."""
    if not ERRORS_FILE.exists():
        return 0
    with ERRORS_FILE.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

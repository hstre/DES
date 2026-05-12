"""
Append-only JSONL writer.
- Real runs  → data/runs.jsonl
- Errors     → data/errors.jsonl
- Dry runs   → data/dry_runs.jsonl  (never mixed into runs.jsonl)
"""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
RUNS_FILE = DATA_DIR / "runs.jsonl"
ERRORS_FILE = DATA_DIR / "errors.jsonl"
DRY_RUNS_FILE = DATA_DIR / "dry_runs.jsonl"


def _append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_run(record: dict[str, Any]) -> None:
    _append(RUNS_FILE, record)


def write_error(record: dict[str, Any]) -> None:
    _append(ERRORS_FILE, record)


def write_dry_run(record: dict[str, Any]) -> None:
    _append(DRY_RUNS_FILE, record)


def write_record(record: dict[str, Any], dry_run: bool = False) -> None:
    """Route record to the correct file based on dry_run flag and status."""
    if dry_run:
        write_dry_run(record)
    elif record.get("status") == "error":
        write_error(record)
    else:
        write_run(record)


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def count_runs() -> int:
    return count_lines(RUNS_FILE)


def count_errors() -> int:
    return count_lines(ERRORS_FILE)


def count_dry_runs() -> int:
    return count_lines(DRY_RUNS_FILE)

"""
Local git commit helper. Stages JSONL data files and commits. Never pushes.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = Path(__file__).parent.parent / "data"

TRACKED_FILES = [
    DATA_DIR / "runs.jsonl",
    DATA_DIR / "errors.jsonl",
    DATA_DIR / "dry_runs.jsonl",
    DATA_DIR / "metadata.json",
]


def _run(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def commit_results(
    run_count: int,
    error_count: int,
    label: str = "",
    data_files: list | None = None,
) -> bool:
    """
    Stage data files and create a local git commit.
    Returns True on success (including nothing-to-commit).
    data_files overrides TRACKED_FILES when provided.
    """
    files_to_stage = data_files if data_files is not None else TRACKED_FILES
    for fpath in [Path(p) for p in files_to_stage]:
        if fpath.exists():
            code, _, err = _run(["git", "add", str(fpath)])
            if code != 0:
                print(f"[git_commit] git add failed for {fpath.name}: {err}", file=sys.stderr)
                return False

    msg_parts = [f"benchmark: {run_count} run(s), {error_count} error(s)"]
    if label:
        msg_parts.append(f"[{label}]")

    code, out, err = _run(["git", "commit", "-m", " ".join(msg_parts)])
    if code != 0:
        if "nothing to commit" in out or "nothing to commit" in err:
            print("[git_commit] Nothing to commit — data unchanged.", file=sys.stderr)
            return True
        print(f"[git_commit] git commit failed: {err}", file=sys.stderr)
        return False

    print(f"[git_commit] Committed: {' '.join(msg_parts)}")
    return True

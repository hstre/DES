"""
Local git commit helper. Stages data/runs.jsonl and data/errors.jsonl, then commits.
Never pushes. Commit message includes run count.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = Path(__file__).parent.parent / "data"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def commit_results(run_count: int, error_count: int, label: str = "") -> bool:
    """
    Stage data files and create a local git commit.
    Returns True on success, False on failure.
    run_count, error_count: totals from current run (not cumulative).
    label: optional tag appended to commit message (e.g. '--limit 2').
    """
    files_to_stage = [
        str(DATA_DIR / "runs.jsonl"),
        str(DATA_DIR / "errors.jsonl"),
        str(DATA_DIR / "metadata.json"),
    ]

    for fpath in files_to_stage:
        if Path(fpath).exists():
            code, out, err = _run(["git", "add", fpath], cwd=REPO_ROOT)
            if code != 0:
                print(f"[git_commit] git add failed for {fpath}: {err}", file=sys.stderr)
                return False

    msg_parts = [f"benchmark: add {run_count} run(s), {error_count} error(s)"]
    if label:
        msg_parts.append(f"[{label}]")
    commit_message = " ".join(msg_parts)

    code, out, err = _run(["git", "commit", "-m", commit_message], cwd=REPO_ROOT)
    if code != 0:
        if "nothing to commit" in out or "nothing to commit" in err:
            print("[git_commit] Nothing to commit — data files unchanged.", file=sys.stderr)
            return True
        print(f"[git_commit] git commit failed: {err}", file=sys.stderr)
        return False

    print(f"[git_commit] Committed: {commit_message}")
    return True

"""
DES Multi-Model Robustness Benchmark runner v2.0.

Usage:
  python run_benchmark.py [--dry-run] [--limit N] [--task-id ID] [--model-id ID] [--commit-each-run]

Flags:
  --dry-run          No API calls. Writes stubs to dry_runs.jsonl only.
  --limit N          Stop after N attempts (errors count).
  --task-id ID       Run only this task.
  --model-id ID      Run only this model.
  --commit-each-run  Git commit after each real run.

API key: OPENROUTER_API_KEY environment variable.
Real runs  → data/runs.jsonl
Errors     → data/errors.jsonl
Dry runs   → data/dry_runs.jsonl
"""

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
BENCHMARK_DIR = SCRIPTS_DIR.parent
CONFIG_DIR = BENCHMARK_DIR / "config"
DATA_DIR = BENCHMARK_DIR / "data"
MAX_TOKENS = 1024

sys.path.insert(0, str(SCRIPTS_DIR))

from openrouter_client import call_model
from dataset_writer import write_record, count_runs, count_errors, count_dry_runs
from git_commit_results import commit_results


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_record(
    model: dict,
    task: dict,
    api_result: dict,
    dry_run: bool,
) -> dict:
    status = "error" if api_result["error_type"] is not None else "success"
    record = {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": {
            "id": model["id"],
            "vendor": model["vendor"],
            "label": model["label"],
        },
        "task": {
            "task_id": task["task_id"],
            "category": task["category"],
            "style": task["style"],
        },
        "request": {
            "prompt": task["prompt"],
            "prompt_sha256": sha256_hex(task["prompt"]),
        },
        "response": {
            "text": api_result["response_text"],
            "finish_reason": api_result["finish_reason"],
            "raw": api_result["raw"],
        },
        "usage": {
            "prompt_tokens": api_result["prompt_tokens"],
            "completion_tokens": api_result["completion_tokens"],
            "total_tokens": api_result["total_tokens"],
            "cost_usd": api_result["cost_usd"],
            "latency_ms": api_result["latency_ms"],
        },
        "status": status,
    }
    if status == "error":
        record["error_type"] = api_result["error_type"]
        record["error_detail"] = api_result["error_detail"]
        record["http_status"] = api_result["http_status"]
    return record


def update_metadata(run_delta: int, error_delta: int, dry_run: bool, dry_run_count: int = 0) -> None:
    meta_path = DATA_DIR / "metadata.json"
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"total_runs": 0, "total_errors": 0, "total_dry_runs": 0}

    meta["total_runs"] = meta.get("total_runs", 0) + run_delta
    meta["total_errors"] = meta.get("total_errors", 0) + error_delta
    if dry_run:
        meta["total_dry_runs"] = meta.get("total_dry_runs", 0) + dry_run_count
    meta["last_updated_utc"] = datetime.now(timezone.utc).isoformat()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="DES Multi-Model Benchmark v2.0")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--task-id", type=str, default=None)
    parser.add_argument("--model-id", type=str, default=None)
    parser.add_argument("--commit-each-run", action="store_true")
    args = parser.parse_args()

    models = load_json(CONFIG_DIR / "models_m1_vendor_diverse.json")
    tasks = load_json(CONFIG_DIR / "tasks_v1.json")

    if args.model_id:
        models = [m for m in models if m["id"] == args.model_id]
        if not models:
            print(f"ERROR: --model-id '{args.model_id}' not found in config.", file=sys.stderr)
            sys.exit(1)

    if args.task_id:
        tasks = [t for t in tasks if t["task_id"] == args.task_id]
        if not tasks:
            print(f"ERROR: --task-id '{args.task_id}' not found in config.", file=sys.stderr)
            sys.exit(1)

    total_pairs = len(models) * len(tasks)
    limit = args.limit if args.limit is not None else total_pairs

    destination = "dry_runs.jsonl" if args.dry_run else "runs.jsonl / errors.jsonl"
    print(f"[benchmark v2.0] dry_run={args.dry_run} | models={len(models)} | tasks={len(tasks)} | limit={limit} → {destination}")

    run_count = 0
    error_count = 0
    completed = 0

    for model in models:
        for task in tasks:
            if completed >= limit:
                break

            print(
                f"[{completed + 1}/{limit}] {model['id']} × {task['task_id']}",
                end=" ... ",
                flush=True,
            )

            api_result = call_model(
                model_id=model["id"],
                prompt=task["prompt"],
                max_tokens=MAX_TOKENS,
                dry_run=args.dry_run,
            )

            record = build_record(model, task, api_result, dry_run=args.dry_run)
            write_record(record, dry_run=args.dry_run)

            if record["status"] == "success":
                run_count += 1
                latency = record["usage"]["latency_ms"]
                tokens = record["usage"]["completion_tokens"]
                print(f"OK (latency={latency}ms, completion_tokens={tokens})")
            else:
                error_count += 1
                print(f"ERROR [{record.get('error_type')}]: {str(record.get('error_detail', ''))[:80]}")

            completed += 1

            if not args.dry_run and args.commit_each_run:
                this_errors = 1 if record["status"] == "error" else 0
                this_runs = 1 if record["status"] == "success" else 0
                commit_results(run_count=this_runs, error_count=this_errors)

        if completed >= limit:
            break

    update_metadata(
        run_delta=run_count if not args.dry_run else 0,
        error_delta=error_count if not args.dry_run else 0,
        dry_run=args.dry_run,
        dry_run_count=completed if args.dry_run else 0,
    )

    print(f"\n[benchmark] Done. runs={run_count} errors={error_count} total_attempted={completed}")
    if args.dry_run:
        print(f"[benchmark] Dry runs written: {count_dry_runs()} total in dry_runs.jsonl")
    else:
        print(f"[benchmark] Cumulative: runs={count_runs()} errors={count_errors()}")

    if not args.dry_run and not args.commit_each_run and completed > 0:
        label_parts = []
        if args.limit is not None:
            label_parts.append(f"--limit {args.limit}")
        commit_results(run_count=run_count, error_count=error_count, label=" ".join(label_parts))


if __name__ == "__main__":
    main()

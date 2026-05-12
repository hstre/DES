"""
Benchmark runner. Runs all model×task combinations and logs every result to JSONL.

Usage:
  python run_benchmark.py [--dry-run] [--limit N] [--task-id ID] [--model-id ID] [--commit-each-run]

Flags:
  --dry-run          Skip actual API calls. Logs stub records to JSONL.
  --limit N          Stop after N completed runs (errors count toward limit).
  --task-id ID       Run only the task with this id.
  --model-id ID      Run only the model with this id.
  --commit-each-run  Create a local git commit after each run.

API key: must be set in OPENROUTER_API_KEY environment variable.
Results are written to data/runs.jsonl and data/errors.jsonl.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
BENCHMARK_DIR = SCRIPTS_DIR.parent
CONFIG_DIR = BENCHMARK_DIR / "config"
DATA_DIR = BENCHMARK_DIR / "data"

sys.path.insert(0, str(SCRIPTS_DIR))

from openrouter_client import call_model
from dataset_writer import write_record, count_runs, count_errors
from git_commit_results import commit_results


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_response(response_text: str, task: dict) -> dict:
    expected = task.get("expected_keywords", [])
    hits = [kw for kw in expected if kw in response_text]
    total = len(expected)
    score = len(hits) / total if total > 0 else None
    line_count = len([l for l in response_text.splitlines() if l.strip()])
    return {
        "keyword_hits": hits,
        "keyword_hit_count": len(hits),
        "keyword_total": total,
        "keyword_score": score,
        "response_line_count": line_count,
    }


def build_record(
    model: dict,
    task: dict,
    api_result: dict,
    dry_run: bool,
) -> dict:
    scoring = score_response(api_result["response_text"], task)
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": model["id"],
        "model_label": model["label"],
        "model_vendor": model["vendor"],
        "task_id": task["id"],
        "task_style": task["style"],
        "prompt_tokens": api_result["prompt_tokens"],
        "completion_tokens": api_result["completion_tokens"],
        "latency_ms": api_result["latency_ms"],
        "http_status": api_result["http_status"],
        "response_text": api_result["response_text"],
        **scoring,
        "error": api_result["error"],
        "error_detail": api_result["error_detail"],
        "dry_run": dry_run,
    }


def update_metadata(run_count_delta: int, error_count_delta: int, dry_run: bool) -> None:
    meta_path = DATA_DIR / "metadata.json"
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {"total_runs": 0, "total_errors": 0, "last_updated_utc": None}

    meta["total_runs"] += run_count_delta
    meta["total_errors"] += error_count_delta
    meta["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    if dry_run:
        meta["last_dry_run_utc"] = meta["last_updated_utc"]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenRouter model benchmark runner")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls, log stubs")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N runs")
    parser.add_argument("--task-id", type=str, default=None, help="Run only this task")
    parser.add_argument("--model-id", type=str, default=None, help="Run only this model")
    parser.add_argument("--commit-each-run", action="store_true", help="Git commit after each run")
    args = parser.parse_args()

    models_cfg = load_json(CONFIG_DIR / "models_m1_vendor_diverse.json")
    tasks_cfg = load_json(CONFIG_DIR / "tasks_v1.json")

    models = models_cfg["models"]
    tasks = tasks_cfg["tasks"]

    if args.model_id:
        models = [m for m in models if m["id"] == args.model_id]
        if not models:
            print(f"ERROR: model-id '{args.model_id}' not found in config.", file=sys.stderr)
            sys.exit(1)

    if args.task_id:
        tasks = [t for t in tasks if t["id"] == args.task_id]
        if not tasks:
            print(f"ERROR: task-id '{args.task_id}' not found in config.", file=sys.stderr)
            sys.exit(1)

    total_pairs = len(models) * len(tasks)
    limit = args.limit if args.limit is not None else total_pairs

    print(f"[run_benchmark] dry_run={args.dry_run} | models={len(models)} | tasks={len(tasks)} | limit={limit}")

    run_count = 0
    error_count = 0
    completed = 0

    for model in models:
        for task in tasks:
            if completed >= limit:
                break

            print(f"[run_benchmark] [{completed + 1}/{limit}] model={model['id']} task={task['id']}", end=" ... ", flush=True)

            api_result = call_model(
                model_id=model["id"],
                system_prompt=task["system_prompt"],
                user_prompt=task["user_prompt"],
                max_tokens=task.get("max_tokens", 256),
                dry_run=args.dry_run,
            )

            record = build_record(model, task, api_result, dry_run=args.dry_run)
            write_record(record)

            if record["error"] is None:
                run_count += 1
                print(f"OK (latency={record['latency_ms']}ms, keyword_score={record['keyword_score']})")
            else:
                error_count += 1
                print(f"ERROR [{record['error']}]: {str(record['error_detail'])[:80]}")

            completed += 1

            if args.commit_each_run:
                label = "dry-run" if args.dry_run else ""
                commit_results(run_count=1, error_count=(1 if record["error"] else 0), label=label)

        if completed >= limit:
            break

    update_metadata(run_count_delta=run_count, error_count_delta=error_count, dry_run=args.dry_run)

    print(f"\n[run_benchmark] Done. runs={run_count} errors={error_count} total_logged={completed}")
    print(f"[run_benchmark] Cumulative JSONL: runs={count_runs()} errors={count_errors()}")

    if not args.commit_each_run and completed > 0:
        label_parts = []
        if args.dry_run:
            label_parts.append("dry-run")
        if args.limit is not None:
            label_parts.append(f"--limit {args.limit}")
        label = " ".join(label_parts)
        commit_results(run_count=run_count, error_count=error_count, label=label)


if __name__ == "__main__":
    main()

"""
DES M3 Role-Prompt Matrix Benchmark runner.

Runs 4 models × 4 roles × 8 tasks = 128 planned calls.
Final prompt: <ROLE PREFIX>\n\nTask:\n<TASK PROMPT>\n\nReturn a concise but complete answer. Do not mention that this is a benchmark.

Usage:
  python run_m3_benchmark.py [--dry-run] [--limit N] [--model-id ID]
                             [--role-id ID] [--task-id ID] [--commit-each-run]

Outputs (never touch M1/M2 files):
  data/m3_role_runs.jsonl
  data/m3_role_errors.jsonl
  data/m3_role_dry_runs.jsonl
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
from git_commit_results import commit_results

RUNS_FILE      = DATA_DIR / "m3_role_runs.jsonl"
ERRORS_FILE    = DATA_DIR / "m3_role_errors.jsonl"
DRY_RUNS_FILE  = DATA_DIR / "m3_role_dry_runs.jsonl"
META_FILE      = DATA_DIR / "m3_role_metadata.json"

FINAL_PROMPT_TEMPLATE = "{role_prefix}\n\nTask:\n{task_prompt}\n\nReturn a concise but complete answer. Do not mention that this is a benchmark."


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def append_record(path: Path, record: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def build_record(model: dict, role: dict, task: dict, api_result: dict, dry_run: bool) -> dict:
    role_prefix  = role["prefix"]
    task_prompt  = task["prompt"]
    final_prompt = FINAL_PROMPT_TEMPLATE.format(
        role_prefix=role_prefix, task_prompt=task_prompt
    )
    status = "error" if api_result["error_type"] else "success"

    record = {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": "M3_role_prompt_matrix",
        "model": {
            "id":     model["id"],
            "vendor": model["vendor"],
            "label":  model["label"],
        },
        "role": {
            "role_id":    role["role_id"],
            "role_label": role["role_label"],
        },
        "task": {
            "task_id":     task["task_id"],
            "target_role": task["target_role"],
            "category":    task["category"],
        },
        "request": {
            "role_prefix":        role_prefix,
            "task_prompt":        task_prompt,
            "final_prompt":       final_prompt,
            "final_prompt_sha256": sha256_hex(final_prompt),
        },
        "response": {
            "text":          api_result["response_text"],
            "finish_reason": api_result["finish_reason"],
            "raw":           api_result["raw"],
        },
        "usage": {
            "prompt_tokens":     api_result["prompt_tokens"],
            "completion_tokens": api_result["completion_tokens"],
            "total_tokens":      api_result["total_tokens"],
            "cost_usd":          api_result["cost_usd"],
            "latency_ms":        api_result["latency_ms"],
        },
        "status": status,
    }
    if status == "error":
        record["error_type"]    = api_result["error_type"]
        record["error_detail"]  = api_result["error_detail"]
        record["http_status"]   = api_result["http_status"]
    return record


def write_record(record: dict, dry_run: bool) -> None:
    if dry_run:
        append_record(DRY_RUNS_FILE, record)
    elif record["status"] == "error":
        append_record(ERRORS_FILE, record)
    else:
        append_record(RUNS_FILE, record)


def update_metadata(run_delta: int, error_delta: int, dry_run: bool, dry_run_count: int = 0) -> None:
    meta = {"total_runs": 0, "total_errors": 0, "total_dry_runs": 0}
    if META_FILE.exists():
        with META_FILE.open("r", encoding="utf-8") as f:
            meta = json.load(f)
    meta["total_runs"]      = meta.get("total_runs", 0)      + (run_delta   if not dry_run else 0)
    meta["total_errors"]    = meta.get("total_errors", 0)    + (error_delta if not dry_run else 0)
    meta["total_dry_runs"]  = meta.get("total_dry_runs", 0)  + (dry_run_count if dry_run else 0)
    meta["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    meta["benchmark"]        = "M3_role_prompt_matrix"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with META_FILE.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="DES M3 Role-Prompt Matrix Benchmark")
    parser.add_argument("--dry-run",        action="store_true")
    parser.add_argument("--limit",          type=int, default=None)
    parser.add_argument("--model-id",       type=str, default=None)
    parser.add_argument("--role-id",        type=str, default=None)
    parser.add_argument("--task-id",        type=str, default=None)
    parser.add_argument("--commit-each-run", action="store_true")
    args = parser.parse_args()

    models = load_json(CONFIG_DIR / "models_m3_successful_m1.json")
    roles  = load_json(CONFIG_DIR / "roles_m3.json")
    tasks  = load_json(CONFIG_DIR / "tasks_m3_role_matrix.json")

    if args.model_id:
        models = [m for m in models if m["id"] == args.model_id]
        if not models:
            print(f"ERROR: --model-id '{args.model_id}' not found.", file=sys.stderr)
            sys.exit(1)

    if args.role_id:
        roles = [r for r in roles if r["role_id"] == args.role_id]
        if not roles:
            print(f"ERROR: --role-id '{args.role_id}' not found.", file=sys.stderr)
            sys.exit(1)

    if args.task_id:
        tasks = [t for t in tasks if t["task_id"] == args.task_id]
        if not tasks:
            print(f"ERROR: --task-id '{args.task_id}' not found.", file=sys.stderr)
            sys.exit(1)

    total_pairs = len(models) * len(roles) * len(tasks)
    limit       = args.limit if args.limit is not None else total_pairs
    destination = "m3_role_dry_runs.jsonl" if args.dry_run else "m3_role_runs.jsonl / m3_role_errors.jsonl"

    print(f"[M3 benchmark] dry_run={args.dry_run} | models={len(models)} | "
          f"roles={len(roles)} | tasks={len(tasks)} | "
          f"planned={total_pairs} | limit={limit} → {destination}")

    run_count   = 0
    error_count = 0
    completed   = 0

    for model in models:
        for role in roles:
            for task in tasks:
                if completed >= limit:
                    break

                label = (f"[{completed+1}/{limit}] "
                         f"{model['id'].split('/')[-1]} × {role['role_id']} × {task['task_id']}")
                print(label, end=" ... ", flush=True)

                final_prompt = FINAL_PROMPT_TEMPLATE.format(
                    role_prefix=role["prefix"], task_prompt=task["prompt"]
                )

                api_result = call_model(
                    model_id=model["id"],
                    prompt=final_prompt,
                    max_tokens=MAX_TOKENS,
                    dry_run=args.dry_run,
                )

                record = build_record(model, role, task, api_result, dry_run=args.dry_run)
                write_record(record, dry_run=args.dry_run)

                if record["status"] == "success":
                    run_count += 1
                    print(f"OK (latency={record['usage']['latency_ms']}ms, "
                          f"tokens={record['usage']['completion_tokens']})")
                else:
                    error_count += 1
                    print(f"ERROR [{record.get('error_type')}]: "
                          f"{str(record.get('error_detail',''))[:80]}")

                completed += 1

                if not args.dry_run and args.commit_each_run:
                    this_runs   = 1 if record["status"] == "success" else 0
                    this_errors = 1 if record["status"] == "error"   else 0
                    commit_results(
                        run_count=this_runs,
                        error_count=this_errors,
                        data_files=[
                            DATA_DIR / "m3_role_runs.jsonl",
                            DATA_DIR / "m3_role_errors.jsonl",
                            DATA_DIR / "m3_role_metadata.json",
                        ],
                    )

            if completed >= limit:
                break
        if completed >= limit:
            break

    update_metadata(
        run_delta=run_count   if not args.dry_run else 0,
        error_delta=error_count if not args.dry_run else 0,
        dry_run=args.dry_run,
        dry_run_count=completed if args.dry_run else 0,
    )

    print(f"\n[M3 benchmark] Done. runs={run_count} errors={error_count} "
          f"total_attempted={completed}")
    if args.dry_run:
        print(f"[M3 benchmark] Dry runs written: {count_lines(DRY_RUNS_FILE)} total")
    else:
        print(f"[M3 benchmark] Cumulative: runs={count_lines(RUNS_FILE)} "
              f"errors={count_lines(ERRORS_FILE)}")

    if not args.dry_run and not args.commit_each_run and completed > 0:
        label_parts = []
        if args.limit is not None:
            label_parts.append(f"--limit {args.limit}")
        commit_results(
            run_count=run_count,
            error_count=error_count,
            label=" ".join(label_parts),
            data_files=[
                DATA_DIR / "m3_role_runs.jsonl",
                DATA_DIR / "m3_role_errors.jsonl",
                DATA_DIR / "m3_role_metadata.json",
            ],
        )


if __name__ == "__main__":
    main()

# OpenRouter Model Benchmark — Reports

**Benchmark version:** m1-vendor-diverse / tasks v1  
**Purpose:** Raw data collection. No model comparison, ranking, or interpretation is derived here.

## Directory layout

```
benchmarks/openrouter_model_benchmark/
├── config/
│   ├── models_m1_vendor_diverse.json   # 7 models, one per vendor
│   ├── tasks_v1.json                   # 8 tasks, 8 distinct prompt styles
│   └── scoring_schema_v1.json          # Field definitions for JSONL records
├── scripts/
│   ├── run_benchmark.py                # Main CLI runner
│   ├── openrouter_client.py            # HTTP client (timeout 120s, 2 retries)
│   ├── dataset_writer.py               # Append-only JSONL writer
│   └── git_commit_results.py           # Local git commit helper
├── data/
│   ├── runs.jsonl                      # One record per completed run
│   ├── errors.jsonl                    # One record per failed run
│   └── metadata.json                   # Cumulative counters
└── reports/
    └── README.md                       # This file
```

## Running

```bash
# Dry run (no API calls, logs stubs):
python scripts/run_benchmark.py --dry-run

# Two real runs (requires OPENROUTER_API_KEY in environment):
python scripts/run_benchmark.py --limit 2

# Single model, single task:
python scripts/run_benchmark.py --model-id anthropic/claude-3-5-haiku --task-id t01_factual_recall

# Full run with per-run commits:
python scripts/run_benchmark.py --commit-each-run
```

API key setup (never commit the key):
```bash
export OPENROUTER_API_KEY=sk-or-...
```

## Data format

Every record in `runs.jsonl` and `errors.jsonl` conforms to `config/scoring_schema_v1.json`.  
Key fields: `run_id`, `model_id`, `task_id`, `response_text`, `keyword_score`, `latency_ms`, `error`, `dry_run`.

`keyword_score` is `null` for tasks with no `expected_keywords` (t03, t08).  
`dry_run: true` records have `response_text: "[DRY RUN — no API call made]"` and all token/latency fields set to 0.

## Status

| Run type | Records logged |
|----------|---------------|
| `--dry-run` (2026-05-12) | 56 stub records |
| `--limit 2` (2026-05-12) | 2 real records (claude-3-5-haiku × t01, t02) |

Full 7×8=56 run set: pending.

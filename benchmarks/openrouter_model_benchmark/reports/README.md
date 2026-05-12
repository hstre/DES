# DES Multi-Model Robustness Benchmark v2.0 — Reports

**Benchmark version:** m1-vendor-diverse / tasks v1 (DES-specific)
**Purpose:** Raw data collection for DES research. No model ranking, no interpretation.

## Research objective

Measure which models provide the highest epistemic utility for DES under real research conditions:
robustness against messy prompts, contradiction detection, long-context stability,
didactic competence, constraint reasoning, bullshit detection, token/cost efficiency.

## Models (M1 — one per vendor)

| Vendor | Model ID | Label |
|--------|----------|-------|
| Anthropic | anthropic/claude-3-5-haiku | Claude 3.5 Haiku |
| OpenAI | openai/gpt-4o-mini | GPT-4o Mini |
| Google | google/gemini-flash-1.5 | Gemini Flash 1.5 |
| DeepSeek | deepseek/deepseek-chat | DeepSeek Chat |
| Alibaba | qwen/qwen-2.5-7b-instruct | Qwen 2.5 7B Instruct |
| Mistral AI | mistralai/mistral-7b-instruct | Mistral 7B Instruct |
| Moonshot AI | moonshotai/moonshot-v1-8k | Moonshot v1 8K |

## Tasks (v1 — DES-specific)

| Task ID | Category | Style |
|---------|----------|-------|
| A1_messy_des_transition | DES | messy |
| A2_clean_des_transition | DES | clean |
| A3_long_context_des | DES | long_context |
| A4_adversarial_false_confirmation | DES | adversarial |
| A5_school_constraint_graph | planning | constraint_reasoning |
| A6_didactic_explanation | education | didactic |
| A7_bullshit_detection | logic | critical_reasoning |
| A8_efficiency_reasoning | DES | efficiency |

## Data files

| File | Contents |
|------|----------|
| `data/runs.jsonl` | Successful real API runs (nested v2.0 schema) |
| `data/errors.jsonl` | Failed real API runs |
| `data/dry_runs.jsonl` | Dry-run stubs — never mixed into runs.jsonl |
| `data/metadata.json` | Cumulative counters |

## Running

```bash
# Dry run (no API calls, writes to dry_runs.jsonl only):
python scripts/run_benchmark.py --dry-run

# Two real runs, one commit per run:
python scripts/run_benchmark.py --limit 2 --commit-each-run

# Single model + task:
python scripts/run_benchmark.py --model-id deepseek/deepseek-chat --task-id A1_messy_des_transition

# Full run (requires explicit approval):
python scripts/run_benchmark.py --commit-each-run
```

API key (never commit):
```bash
export OPENROUTER_API_KEY=sk-or-...
```

## Schema (v2.0 nested)

```json
{
  "run_id": "uuid",
  "timestamp_utc": "...",
  "model": {"id": "...", "vendor": "...", "label": "..."},
  "task": {"task_id": "...", "category": "...", "style": "..."},
  "request": {"prompt": "...", "prompt_sha256": "..."},
  "response": {"text": "...", "finish_reason": "...", "raw": {}},
  "usage": {"prompt_tokens": null, "completion_tokens": null, "total_tokens": null, "cost_usd": null, "latency_ms": 0},
  "status": "success"
}
```

No keyword scoring, no LLM scoring during collection. Scoring is deferred — see `config/scoring_schema_v1.json`.

## Status

| Phase | Records |
|-------|----------|
| v1 dry-run (2026-05-12) | 56 stubs (archived in dry_runs.jsonl) |
| v2 dry-run (2026-05-12) | 56 stubs (dry_runs.jsonl) |
| v2 --limit 2 (2026-05-12) | 2 real (claude-3-5-haiku × A1, A2) |

Full 7×8=56 run set: pending approval.

**Note:** `dry_runs.jsonl` (112 records, 78KB) is tracked in local git only; too large for single MCP push.

# DES M3 Role-Prompt Matrix Benchmark

**Branch:** `analysis/m3-role-prompt-matrix`  
**Frozen source:** `claude/des-prototype-v0.1-xOEbF`  
**Purpose:** Raw data collection only. No scoring during collection phase.

## Research question

Which model performs best under which DES role prompt?

## Models (M3 — successful M1 only)

| Vendor | Model ID | Label |
|--------|----------|-------|
| Anthropic | anthropic/claude-3-5-haiku | Claude 3.5 Haiku |
| OpenAI | openai/gpt-4o-mini | GPT-4o Mini |
| DeepSeek | deepseek/deepseek-chat | DeepSeek Chat |
| Alibaba | qwen/qwen-2.5-7b-instruct | Qwen 2.5 7B Instruct |

## Roles (4)

| Role ID | Label | Function |
|---------|-------|---------|
| builder | Builder | Construct strongest plausible hypothesis; mark assumptions |
| falsifier | Falsifier | Search for false premises, contradictions, counterexamples |
| resolver | Resolver | Compare interpretations, weigh evidence, produce justified decision |
| explainer | Explainer | Explain to intelligent non-specialist; preserve correctness |

## Tasks (8, 2 per target role)

| Task ID | Target Role | Category |
|---------|-------------|---------|
| M3_B1_builder_des_hypothesis | builder | DES |
| M3_B2_builder_school_constraints | builder | planning |
| M3_F1_falsifier_t9_t8 | falsifier | DES |
| M3_F2_falsifier_prompting_claim | falsifier | methodology |
| M3_R1_resolver_model_roles | resolver | model_selection |
| M3_R2_resolver_edge_vs_edge_star | resolver | DES |
| M3_E1_explainer_principal | explainer | education |
| M3_E2_explainer_des_roles | explainer | DES |

## Matrix

4 models × 4 roles × 8 tasks = **128 planned calls**

## Prompt construction

```
<ROLE PREFIX>

Task:
<TASK PROMPT>

Return a concise but complete answer. Do not mention that this is a benchmark.
```

## Data files

| File | Contents |
|------|----------|
| `data/m3_role_runs.jsonl` | Successful real runs |
| `data/m3_role_errors.jsonl` | Failed real runs |
| `data/m3_role_dry_runs.jsonl` | Dry-run stubs only |
| `data/m3_role_metadata.json` | Cumulative counters |

M1/M2 files (`runs.jsonl`, `errors.jsonl`, etc.) are never touched.

## Running

```bash
# Dry run:
python scripts/run_m3_benchmark.py --dry-run

# Limit 4:
python scripts/run_m3_benchmark.py --limit 4 --commit-each-run

# Single model + role + task:
python scripts/run_m3_benchmark.py --model-id deepseek/deepseek-chat --role-id falsifier --task-id M3_F1_falsifier_t9_t8

# Full run (requires explicit approval):
python scripts/run_m3_benchmark.py --commit-each-run
```

## Schema (M3 nested)

```json
{
  "run_id": "uuid",
  "timestamp_utc": "...",
  "benchmark": "M3_role_prompt_matrix",
  "model": {"id": "...", "vendor": "...", "label": "..."},
  "role": {"role_id": "...", "role_label": "..."},
  "task": {"task_id": "...", "target_role": "...", "category": "..."},
  "request": {
    "role_prefix": "...",
    "task_prompt": "...",
    "final_prompt": "...",
    "final_prompt_sha256": "..."
  },
  "response": {"text": "...", "finish_reason": "...", "raw": {}},
  "usage": {"prompt_tokens": null, "completion_tokens": null, "total_tokens": null, "cost_usd": null, "latency_ms": 0},
  "status": "success"
}
```

## Status

| Phase | Records |
|-------|---------|
| dry-run | pending |
| --limit 4 | pending |
| Full 128-call run | awaiting approval |

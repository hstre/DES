""" 
M3 Jury Evaluation — pairwise blind scoring of M3 role-conditioned outputs.

Scope: each task evaluated under its TARGET role only.
Matrix: 8 tasks × 6 model pairs × 2 judges = 96 jury calls.
Judges: deepseek-chat, anthropic/claude-sonnet-4-6

Outputs:
  reports/M3_jury/jury_results.jsonl
  reports/M3_jury/jury_summary.md

Run: python scripts/run_m3_jury.py [--dry-run] [--limit N]
"""

import argparse
import hashlib
import json
import random
import sys
import time
from itertools import combinations
from pathlib import Path

from openai import OpenAI
import os

SCRIPTS_DIR = Path(__file__).parent
BENCHMARK_DIR = SCRIPTS_DIR.parent
DATA_DIR = BENCHMARK_DIR / "data"
OUT_DIR = BENCHMARK_DIR / "reports" / "M3_jury"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_FILE = OUT_DIR / "jury_results.jsonl"
SUMMARY_FILE = OUT_DIR / "jury_summary.md"

ds4 = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/v1",
)
openrouter = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/hstre/DES",
        "X-Title": "DES M3 Jury",
    },
)

JUDGES = [
    ("deepseek-chat",               ds4),
    ("anthropic/claude-sonnet-4-6", openrouter),
]

MODEL_IDS = [
    "anthropic/claude-3-5-haiku",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat",
    "qwen/qwen-2.5-7b-instruct",
]

DIMS = [
    "role_adherence",
    "epistemic_quality",
    "task_completion",
    "assumption_handling",
    "conclusion_clarity",
    "overall",
]

JURY_PROMPT = """\
You are a neutral epistemic evaluator assessing two AI outputs on the same task.
You do not know which system produced which output.

ROLE CONTEXT: Both outputs were produced under the following role instruction:
{role_prefix}

TASK:
{task_prompt}

OUTPUT A:
{output_a}

OUTPUT B:
{output_b}

Evaluate on 6 dimensions. For each, allocate scores so that A_score + B_score = 1.0 exactly.
Provide one sentence reason per dimension.

Do NOT reward length or rhetorical polish. Evaluate epistemic structure.

Dimensions:
1. role_adherence: Did the output actually follow the role instructions (Builder/Falsifier/Resolver/Explainer)?
2. epistemic_quality: Is the reasoning sound, traceable, and non-circular?
3. task_completion: Did it fully address what was asked (not just adjacent topics)?
4. assumption_handling: Were assumptions explicitly marked and separated from supported claims?
5. conclusion_clarity: Is there a clear, actionable conclusion or verdict?
6. overall: Weighted epistemic judgment across all dimensions

Return ONLY valid JSON:
{{
  "role_adherence":      {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "epistemic_quality":   {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "task_completion":     {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "assumption_handling": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "conclusion_clarity":  {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "overall":             {{"A": 0.XX, "B": 0.XX, "reason": "..."}}
}}
Each pair must sum to exactly 1.0."""


def load_m3_runs():
    """Load M3 runs, deduplicated to last occurrence per (model, role, task)."""
    index = {}
    with open(DATA_DIR / "m3_role_runs.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r["model"]["id"], r["role"]["role_id"], r["task"]["task_id"])
            index[key] = r  # last occurrence wins
    return index


def load_tasks():
    config = BENCHMARK_DIR / "config" / "tasks_m3_role_matrix.json"
    with open(config) as f:
        return json.load(f)


def load_roles():
    config = BENCHMARK_DIR / "config" / "roles_m3.json"
    with open(config) as f:
        return {r["role_id"]: r for r in json.load(f)}


def get_assignment(judge_model, task_id, role_id, model_a, model_b):
    seed = int(
        hashlib.md5(
            f"{judge_model}{task_id}{role_id}{model_a}{model_b}".encode()
        ).hexdigest(),
        16,
    ) % (2**32)
    rng = random.Random(seed)
    if rng.random() > 0.5:
        return {"A": model_a, "B": model_b}
    return {"A": model_b, "B": model_a}


def call_judge(client, model_id, prompt, dry_run=False):
    if dry_run:
        return json.dumps({d: {"A": 0.5, "B": 0.5, "reason": "dry-run"} for d in DIMS})
    r = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.3,
    )
    return r.choices[0].message.content


def parse_jury(response):
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:] if lines[-1] != "```" else lines[1:-1])
    data = json.loads(clean)
    for dim, vals in data.items():
        if isinstance(vals, dict) and "A" in vals and "B" in vals:
            total = vals["A"] + vals["B"]
            if total > 0 and abs(total - 1.0) > 0.01:
                data[dim]["A"] = round(vals["A"] / total, 3)
                data[dim]["B"] = round(vals["B"] / total, 3)
    return data


def run(dry_run=False, limit=None):
    runs_index = load_m3_runs()
    tasks = load_tasks()
    roles = load_roles()

    # Build evaluation plan: each task under its TARGET role, all model pairs
    plan = []
    for task in tasks:
        task_id = task["task_id"]
        target_role = task["target_role"]
        role = roles[target_role]
        for model_a, model_b in combinations(MODEL_IDS, 2):
            key_a = (model_a, target_role, task_id)
            key_b = (model_b, target_role, task_id)
            if key_a not in runs_index or key_b not in runs_index:
                continue
            for judge_id, judge_client in JUDGES:
                plan.append({
                    "task": task,
                    "role": role,
                    "model_a": model_a,
                    "model_b": model_b,
                    "judge_id": judge_id,
                    "judge_client": judge_client,
                    "run_a": runs_index[key_a],
                    "run_b": runs_index[key_b],
                })

    total = len(plan)
    if limit:
        plan = plan[:limit]

    print(f"[M3 jury] dry_run={dry_run} | planned={total} | running={len(plan)}")

    results = []
    for i, item in enumerate(plan):
        task = item["task"]
        role = item["role"]
        model_a = item["model_a"]
        model_b = item["model_b"]
        judge_id = item["judge_id"]
        judge_client = item["judge_client"]

        la = model_a.split("/")[-1][:18]
        lb = model_b.split("/")[-1][:18]
        judge_short = judge_id.split("/")[-1][:18]
        print(
            f"  [{i+1}/{len(plan)}] {task['task_id']} | {role['role_id']} | "
            f"{la} vs {lb} | judge={judge_short} ... ",
            end="", flush=True,
        )

        assignment = get_assignment(judge_id, task["task_id"], role["role_id"], model_a, model_b)
        text_a = item["run_a"]["response"]["text"]
        text_b = item["run_b"]["response"]["text"]
        out_a = text_a if assignment["A"] == model_a else text_b
        out_b = text_b if assignment["A"] == model_a else text_a

        prompt = JURY_PROMPT.format(
            role_prefix=role["prefix"],
            task_prompt=task["prompt"],
            output_a=out_a,
            output_b=out_b,
        )

        try:
            raw = call_judge(judge_client, judge_id, prompt, dry_run=dry_run)
            parsed = parse_jury(raw)
            result = {
                "task_id":  task["task_id"],
                "target_role": task["target_role"],
                "category": task["category"],
                "model_a": model_a,
                "model_b": model_b,
                "judge":   judge_id,
                "assignment": assignment,
                "dimensions": {},
            }
            for dim in DIMS:
                if dim in parsed:
                    a_raw = parsed[dim]["A"]
                    b_raw = parsed[dim]["B"]
                    score_a = a_raw if assignment["A"] == model_a else b_raw
                    score_b = b_raw if assignment["A"] == model_a else a_raw
                    result["dimensions"][dim] = {
                        model_a: round(score_a, 3),
                        model_b: round(score_b, 3),
                        "reason": parsed[dim].get("reason", ""),
                    }
            results.append(result)
            ov = result["dimensions"].get("overall", {})
            sa = ov.get(model_a, 0.5)
            sb = ov.get(model_b, 0.5)
            winner = la if sa > sb else (lb if sb > sa else "TIE")
            print(f"OK | {la}={sa:.2f} {lb}={sb:.2f} → {winner}")
            with open(RESULTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "task_id": task["task_id"], "role": role["role_id"],
                "model_a": model_a, "model_b": model_b,
                "judge": judge_id, "error": str(e),
            })

        if not dry_run:
            time.sleep(1.0)

    _write_summary(results)
    valid = [r for r in results if "dimensions" in r and "error" not in r]
    print(f"\n[M3 jury] Done. valid={len(valid)}/{len(results)}")


def _write_summary(results):
    valid = [r for r in results if "dimensions" in r and "error" not in r]
    if not valid:
        return

    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    # Aggregate overall score per model
    model_overall = {mid: [] for mid in MODEL_IDS}
    for r in valid:
        ov = r["dimensions"].get("overall", {})
        for mid in MODEL_IDS:
            if mid in ov:
                model_overall[mid].append(ov[mid])

    # Per role: model scores
    role_model = {}
    for r in valid:
        role = r["target_role"]
        ov = r["dimensions"].get("overall", {})
        if role not in role_model:
            role_model[role] = {mid: [] for mid in MODEL_IDS}
        for mid in MODEL_IDS:
            if mid in ov:
                role_model[role][mid].append(ov[mid])

    with open(SUMMARY_FILE, "w") as f:
        f.write("# M3 Jury Evaluation — Summary\n\n")
        f.write(f"Valid evaluations: {len(valid)}\n\n")

        f.write("## Overall model scores (jury overall dimension)\n\n")
        f.write("| Model | Mean overall score |\n|---|---|\n")
        ranked = sorted(MODEL_IDS, key=lambda m: avg(model_overall[m]), reverse=True)
        for mid in ranked:
            label = mid.split("/")[-1]
            f.write(f"| {label} | {avg(model_overall[mid])} |\n")

        f.write("\n## Scores by role\n\n")
        for role_id in ["builder", "falsifier", "resolver", "explainer"]:
            if role_id not in role_model:
                continue
            f.write(f"### {role_id.capitalize()}\n\n")
            f.write("| Model | Mean overall |\n|---|---|\n")
            role_ranked = sorted(MODEL_IDS, key=lambda m: avg(role_model[role_id][m]), reverse=True)
            for mid in role_ranked:
                label = mid.split("/")[-1]
                f.write(f"| {label} | {avg(role_model[role_id][mid])} |\n")
            f.write("\n")

        f.write("## Scores by dimension (all evaluations)\n\n")
        dim_model = {d: {mid: [] for mid in MODEL_IDS} for d in DIMS}
        for r in valid:
            for dim in DIMS:
                if dim in r["dimensions"]:
                    for mid in MODEL_IDS:
                        if mid in r["dimensions"][dim]:
                            dim_model[dim][mid].append(r["dimensions"][dim][mid])
        f.write("| Dimension | " + " | ".join(m.split("/")[-1] for m in MODEL_IDS) + " |\n")
        f.write("|---" * (len(MODEL_IDS) + 1) + "|\n")
        for dim in DIMS:
            row = [dim] + [str(avg(dim_model[dim][mid])) for mid in MODEL_IDS]
            f.write("| " + " | ".join(row) + " |\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)

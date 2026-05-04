"""
Dry-run validation. Must pass all checks before jury run.
"""
import json, glob, hashlib, random, os
from openai import OpenAI
from pathlib import Path

QUESTIONS = ["A1","A2","A3","B1","B2","B3","C1","C2","D1","D2","D3","E1","E2"]
JUDGES = ["deepseek-chat", "openai/gpt-4o",
          "anthropic/claude-sonnet-4-5", "google/gemini-2.0-flash-001"]
COT_LABELS = ["CoT-DS4", "CoT-GPT4o"]

checks = []
ds4 = None
or_client = None

# CHECK 1: All DS4_GPT4o state files present
print("CHECK 1: DS4_GPT4o state files")
missing = []
for qid in QUESTIONS:
    patterns = [
        f"batch_results_multimodel/*DS4_GPT4o*{qid}*state.json",
        f"batch_results_multimodel/DS4_GPT4o_{qid}_state.json",
    ]
    found = any(glob.glob(p) for p in patterns)
    if not found:
        missing.append(qid)
if missing:
    print(f"  FAIL: Missing DS4_GPT4o states for: {missing}")
    checks.append(False)
else:
    print(f"  PASS: All 13 DS4_GPT4o state files found")
    checks.append(True)

# CHECK 2: Both CoT generators reachable
print("CHECK 2: CoT generators reachable")
try:
    ds4 = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                 base_url="https://api.deepseek.com/v1")
    r = ds4.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":"ping"}],
        max_tokens=5
    )
    print(f"  PASS: DeepSeek reachable")
    checks.append(True)
except Exception as e:
    print(f"  FAIL: DeepSeek: {e}")
    checks.append(False)

try:
    or_client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
                       base_url="https://openrouter.ai/api/v1",
                       default_headers={"HTTP-Referer":"https://github.com/hstre/DES"})
    r = or_client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role":"user","content":"ping"}],
        max_tokens=5
    )
    print(f"  PASS: OpenRouter/GPT-4o reachable")
    checks.append(True)
except Exception as e:
    print(f"  FAIL: OpenRouter/GPT-4o: {e}")
    checks.append(False)

# CHECK 3: All four judge models reachable
print("CHECK 3: Judge models reachable")
judge_models = []
if ds4:
    judge_models.append(("deepseek-chat", ds4))
if or_client:
    judge_models += [
        ("openai/gpt-4o", or_client),
        ("anthropic/claude-sonnet-4-5", or_client),
        ("google/gemini-2.0-flash-001", or_client),
    ]
for model, client in judge_models:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":"Reply with OK"}],
            max_tokens=5
        )
        print(f"  PASS: {model}")
        checks.append(True)
    except Exception as e:
        print(f"  FAIL: {model}: {e}")
        checks.append(False)

# CHECK 4: Randomization balance
print("CHECK 4: Randomization balance")
assignments = []
for judge in JUDGES:
    for qid in QUESTIONS:
        for cot in COT_LABELS:
            seed = int(hashlib.md5(f"{judge}{qid}{cot}".encode()).hexdigest(), 16) % (2**32)
            rng = random.Random(seed)
            assignments.append("A" if rng.random() > 0.5 else "B")
des_as_a = assignments.count("A")
des_as_b = assignments.count("B")
total = len(assignments)
balance = abs(des_as_a - des_as_b) / total
if balance < 0.15:
    print(f"  PASS: DES as A={des_as_a}, B={des_as_b} (balance={1-balance:.2f})")
    checks.append(True)
else:
    print(f"  WARN: Imbalanced assignment A={des_as_a}, B={des_as_b}")
    checks.append(True)  # warn but don't fail

# CHECK 5: Sample judge output is valid JSON with correct structure
print("CHECK 5: Sample jury output validation")

def call_with_cost(client, model, prompt, max_tokens=1000):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3
    )
    usage = r.usage
    info = {
        "model": model,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
        "cost_measured": usage is not None
    }
    return r.choices[0].message.content, info

sample_prompt = """Return ONLY this JSON, no other text:
{"readability": {"A": 0.4, "B": 0.6, "reason": "test"},
 "directional_commitment": {"A": 0.6, "B": 0.4, "reason": "test"},
 "contradiction_depth": {"A": 0.7, "B": 0.3, "reason": "test"},
 "synthesis_quality": {"A": 0.4, "B": 0.6, "reason": "test"},
 "epistemic_novelty": {"A": 0.8, "B": 0.2, "reason": "test"},
 "branch_preservation": {"A": 0.9, "B": 0.1, "reason": "test"},
 "process_traceability": {"A": 0.85, "B": 0.15, "reason": "test"},
 "evidence_scope_discipline": {"A": 0.6, "B": 0.4, "reason": "test"},
 "overall": {"A": 0.65, "B": 0.35, "reason": "test"}}"""

if ds4:
    try:
        resp, _ = call_with_cost(ds4, "deepseek-chat", sample_prompt, max_tokens=400)
        clean = resp.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        data = json.loads(clean)
        # Check A+B sums
        bad_dims = []
        for dim, vals in data.items():
            if isinstance(vals, dict) and "A" in vals and "B" in vals:
                total = vals["A"] + vals["B"]
                if abs(total - 1.0) > 0.05:
                    bad_dims.append(f"{dim}={total:.2f}")
        if bad_dims:
            print(f"  WARN: Normalization needed for: {bad_dims}")
        else:
            print(f"  PASS: JSON valid, all A+B sums correct")
        checks.append(True)
    except Exception as e:
        print(f"  FAIL: {e}")
        checks.append(False)
else:
    print(f"  SKIP: DeepSeek client not available")
    checks.append(False)

# FINAL
print("\n" + "="*50)
passed = sum(checks)
total_checks = len(checks)
if passed == total_checks:
    print(f"ALL CHECKS PASSED ({passed}/{total_checks}) -- ready for jury run")
else:
    print(f"FAILED ({total_checks - passed} failures) -- fix before running jury")
    exit(1)

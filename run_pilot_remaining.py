"""Run only the missing pilot combos."""
import subprocess, json, os, shutil, time
from pathlib import Path
from run_pilot import run_single, print_summary, RESULTS_DIR

MISSING = [
    ("Claude_DS4",  "openrouter", "anthropic/claude-sonnet-4-5", "deepseek",    "deepseek-chat",                  "E1", "Is free trade both beneficial and harmful to developing economies?"),
    ("GPT4o_GPT4o", "openrouter", "openai/gpt-4o",               "openrouter",  "openai/gpt-4o",                  "A1", "Does raising the minimum wage increase unemployment?"),
    ("GPT4o_GPT4o", "openrouter", "openai/gpt-4o",               "openrouter",  "openai/gpt-4o",                  "A3", "Does immigration reduce wages for native workers?"),
    ("GPT4o_GPT4o", "openrouter", "openai/gpt-4o",               "openrouter",  "openai/gpt-4o",                  "E1", "Is free trade both beneficial and harmful to developing economies?"),
    ("Claude_Cl",   "openrouter", "anthropic/claude-sonnet-4-5", "openrouter",  "anthropic/claude-sonnet-4-5",    "A1", "Does raising the minimum wage increase unemployment?"),
    ("Claude_Cl",   "openrouter", "anthropic/claude-sonnet-4-5", "openrouter",  "anthropic/claude-sonnet-4-5",    "A3", "Does immigration reduce wages for native workers?"),
    ("Claude_Cl",   "openrouter", "anthropic/claude-sonnet-4-5", "openrouter",  "anthropic/claude-sonnet-4-5",    "E1", "Is free trade both beneficial and harmful to developing economies?"),
]

if __name__ == "__main__":
    results = []
    for combo_id, bp, bm, fp, fm, qid, question in MISSING:
        try:
            r = run_single(combo_id, bp, bm, fp, fm, qid, question)
            results.append(r)
            status = "OK" if r["success"] else "FAIL"
            print(f"  -> {status} | {r['iterations']} iter | "
                  f"{r['claims_total']} claims | open={r['claims_open']} "
                  f"AD={r.get('anti_delphi_activations', 0)} "
                  f"T1={r['t1_fired']} T9={r['t9_fired']}")
        except subprocess.TimeoutExpired:
            print(f"  -> TIMEOUT after 360s")
        except Exception as e:
            print(f"  -> ERROR: {e}")

    print_summary(results)

"""
Multi-Model Pilot — DES Anti-Delphi role heterogeneity test.

7 model combinations × 3 questions = 21 runs.
Each run is Anti-Delphi mode with the two roles potentially using different models/providers.

Results written to batch_results_pilot/  as  {combo_id}_{qid}.json
State snapshots written as                   {combo_id}_{qid}_state.json
"""

import subprocess
import json
import os
import shutil
import time
from pathlib import Path

QUESTIONS = {
    "A1": "Does raising the minimum wage increase unemployment?",
    "A3": "Does immigration reduce wages for native workers?",
    "E1": "Is free trade both beneficial and harmful to developing economies?",
}

# 7 combos: (combo_id, builder_provider, builder_model, falsifier_provider, falsifier_model)
COMBOS = [
    ("DS4_DS4",     "deepseek",    "deepseek-chat",                    "deepseek",    "deepseek-chat"),
    ("DS4_GPT4o",   "deepseek",    "deepseek-chat",                    "openrouter",  "openai/gpt-4o"),
    ("GPT4o_DS4",   "openrouter",  "openai/gpt-4o",                    "deepseek",    "deepseek-chat"),
    ("DS4_Claude",  "deepseek",    "deepseek-chat",                    "openrouter",  "anthropic/claude-sonnet-4-5"),
    ("Claude_DS4",  "openrouter",  "anthropic/claude-sonnet-4-5",      "deepseek",    "deepseek-chat"),
    ("GPT4o_GPT4o", "openrouter",  "openai/gpt-4o",                    "openrouter",  "openai/gpt-4o"),
    ("Claude_Cl",   "openrouter",  "anthropic/claude-sonnet-4-5",      "openrouter",  "anthropic/claude-sonnet-4-5"),
]

RESULTS_DIR = Path("batch_results_pilot")
RESULTS_DIR.mkdir(exist_ok=True)


def run_single(combo_id: str, bp: str, bm: str, fp: str, fm: str, qid: str, question: str) -> dict:
    print(f"\n{'='*70}")
    print(f"Running {combo_id} / {qid}: builder={bm} | falsifier={fm}")
    print(f"  Q: {question}")
    print("=" * 70)

    subprocess.run(["python", "des.py", "--reset"], capture_output=True, env=os.environ)

    cmd = [
        "python", "des.py", question,
        "--max-iter", "60",
        "--anti-delphi",
        "--builder-provider", bp,
        "--builder-model", bm,
        "--falsifier-provider", fp,
        "--falsifier-model", fm,
    ]
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=360, env=os.environ)
    elapsed = time.time() - start

    state_data = {}
    if Path("des_state.json").exists():
        with open("des_state.json") as f:
            state_data = json.load(f)

    claims = state_data.get("claims", {})
    op_history = state_data.get("operation_history", [])
    transitions_fired = list(set(
        op.split("[")[0].split(" ")[0]
        for op in op_history if op
    ))

    sealed_count   = sum(1 for c in claims.values() if c.get("sealed"))
    open_count     = sum(1 for c in claims.values() if not c.get("sealed"))
    role_count     = sum(1 for c in claims.values() if c.get("is_role_generated"))
    synthesis_count = sum(1 for c in claims.values() if c.get("is_synthesis"))

    # Collect generated_by values for role-generated claims
    generated_by_counts: dict[str, int] = {}
    for c in claims.values():
        gb = c.get("generated_by", "")
        if gb:
            generated_by_counts[gb] = generated_by_counts.get(gb, 0) + 1

    result_data = {
        "combo_id": combo_id,
        "qid": qid,
        "question": question,
        "builder_provider": bp,
        "builder_model": bm,
        "falsifier_provider": fp,
        "falsifier_model": fm,
        "success": result.returncode == 0,
        "elapsed_seconds": round(elapsed, 1),
        "iterations": state_data.get("iteration", 0),
        "claims_total": len(claims),
        "claims_sealed": sealed_count,
        "claims_open": open_count,
        "claims_synthesis": synthesis_count,
        "claims_role_generated": role_count,
        "generated_by_counts": generated_by_counts,
        "transitions_fired": sorted(transitions_fired),
        "t1_fired": "T1" in transitions_fired,
        "t9_fired": "T9" in transitions_fired,
        "reframing_count": state_data.get("reframing_count", 0),
        "anti_delphi_activations": state_data.get("anti_delphi_activations", 0),
        "error": result.stderr[-500:] if result.returncode != 0 else None,
        "stdout_tail": result.stdout[-800:],
    }

    run_key = f"{combo_id}_{qid}"
    with open(RESULTS_DIR / f"{run_key}.json", "w") as f:
        json.dump(result_data, f, indent=2)
    if Path("des_state.json").exists():
        shutil.copy("des_state.json", RESULTS_DIR / f"{run_key}_state.json")

    return result_data


def print_summary(results: list[dict]):
    print("\n" + "=" * 90)
    print("MULTI-MODEL PILOT SUMMARY")
    print("=" * 90)
    print(f"{'Combo':<14} {'Q':<4} {'OK':<4} {'Iter':<6} {'Claims':<7} {'Open':<5} "
          f"{'AD':<4} {'T1':<4} {'T9':<4} {'Transitions'}")
    print("-" * 90)

    for r in results:
        ok   = "YES" if r["success"] else "NO"
        t1   = "YES" if r["t1_fired"] else "-"
        t9   = "YES" if r["t9_fired"] else "-"
        ad   = str(r.get("anti_delphi_activations", 0))
        trans = ",".join(r["transitions_fired"])
        print(f"{r['combo_id']:<14} {r['qid']:<4} {ok:<4} "
              f"{r['iterations']:<6} {r['claims_total']:<7} {r['claims_open']:<5} "
              f"{ad:<4} {t1:<4} {t9:<4} {trans}")

    print("-" * 90)
    n = len(results)
    if n == 0:
        return

    success_rate = sum(1 for r in results if r["success"]) / n * 100
    t1_rate      = sum(1 for r in results if r["t1_fired"]) / n * 100
    t9_rate      = sum(1 for r in results if r["t9_fired"]) / n * 100
    avg_claims   = sum(r["claims_total"] for r in results) / n
    avg_iter     = sum(r["iterations"] for r in results) / n
    avg_ad       = sum(r.get("anti_delphi_activations", 0) for r in results) / n
    total_open   = sum(r["claims_open"] for r in results)

    print(f"\nSuccess rate:           {success_rate:.0f}%")
    print(f"T1 fire rate:           {t1_rate:.0f}%")
    print(f"T9 fire rate:           {t9_rate:.0f}%")
    print(f"Avg Anti-Delphi act.:   {avg_ad:.1f}")
    print(f"Avg claims/run:         {avg_claims:.1f}")
    print(f"Avg iterations/run:     {avg_iter:.1f}")
    print(f"Total open at end:      {total_open}")

    # Per-combo aggregation
    print("\n" + "=" * 60)
    print("PER-COMBO AGGREGATE")
    print("-" * 60)
    print(f"{'Combo':<14} {'Runs':<6} {'OK':<4} {'AvgClaims':<11} {'AvgIter':<9} {'AvgAD'}")
    print("-" * 60)
    combos_seen = list(dict.fromkeys(r["combo_id"] for r in results))
    for cid in combos_seen:
        sub = [r for r in results if r["combo_id"] == cid]
        n_sub = len(sub)
        ok_sub = sum(1 for r in sub if r["success"])
        avg_c  = sum(r["claims_total"] for r in sub) / n_sub
        avg_it = sum(r["iterations"] for r in sub) / n_sub
        avg_a  = sum(r.get("anti_delphi_activations", 0) for r in sub) / n_sub
        print(f"{cid:<14} {n_sub:<6} {ok_sub:<4} {avg_c:<11.1f} {avg_it:<9.1f} {avg_a:.1f}")

    print("\nISSUES:")
    issues = False
    for r in results:
        if not r["success"]:
            print(f"  FAIL {r['combo_id']}/{r['qid']}: {str(r.get('error',''))[:120]}")
            issues = True
        if r["claims_open"] > 0:
            print(f"  OPEN {r['combo_id']}/{r['qid']}: {r['claims_open']} unsealed")
            issues = True
    if not issues:
        print("  None.")

    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {RESULTS_DIR}/")


if __name__ == "__main__":
    results = []
    for combo_id, bp, bm, fp, fm in COMBOS:
        for qid, question in QUESTIONS.items():
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
                results.append({
                    "combo_id": combo_id, "qid": qid, "question": question,
                    "builder_provider": bp, "builder_model": bm,
                    "falsifier_provider": fp, "falsifier_model": fm,
                    "success": False, "error": "timeout",
                    "transitions_fired": [], "t1_fired": False, "t9_fired": False,
                    "claims_total": 0, "claims_open": 0, "claims_sealed": 0,
                    "claims_synthesis": 0, "claims_role_generated": 0,
                    "generated_by_counts": {},
                    "iterations": 0, "reframing_count": 0,
                    "anti_delphi_activations": 0, "elapsed_seconds": 360,
                })
            except Exception as e:
                print(f"  -> ERROR: {e}")

    print_summary(results)

"""
Batch test runner for DES Anti-Delphi stability assessment.
Mirrors run_batch.py exactly but adds --anti-delphi flag and writes to batch_results_antidelphi/.
"""

import subprocess
import json
import os
import shutil
import time
from pathlib import Path

QUESTIONS = {
    "A1": "Does raising the minimum wage increase unemployment?",
    "A2": "Is foreign aid effective at reducing poverty?",
    "A3": "Does immigration reduce wages for native workers?",
    "B1": "Is GDP a good measure of economic wellbeing?",
    "B2": "Is remote work more productive than office work?",
    "B3": "Is social media harmful to democracy?",
    "C1": "Is technology good?",
    "C2": "Is globalization beneficial?",
    "D1": "Is intermittent fasting effective for long-term weight loss?",
    "D2": "Does class size reduction improve educational outcomes?",
    "D3": "Is gene editing ethically justifiable in humans?",
    "E1": "Is free trade both beneficial and harmful to developing economies?",
    "E2": "Is economic growth compatible with ecological sustainability?",
}

RESULTS_DIR = Path("batch_results_antidelphi")
RESULTS_DIR.mkdir(exist_ok=True)


def run_single(qid: str, question: str) -> dict:
    """Run DES in Anti-Delphi mode on one question, capture results."""
    print(f"\n{'='*60}")
    print(f"Running {qid} [Anti-Delphi]: {question}")
    print('='*60)

    subprocess.run(["python", "des.py", "--reset"], capture_output=True, env=os.environ)

    start = time.time()
    result = subprocess.run(
        ["python", "des.py", question, "--max-iter", "60", "--anti-delphi"],
        capture_output=True,
        text=True,
        timeout=300,
        env=os.environ,
    )
    elapsed = time.time() - start

    state_data = {}
    if Path("des_state.json").exists():
        with open("des_state.json") as f:
            state_data = json.load(f)

    claims = state_data.get("claims", {})
    op_history = state_data.get("operation_history", [])
    transitions_fired = list(set(
        op.split("[")[0].split(" ")[0]   # strip [role] suffix, take TX part
        for op in op_history if op
    ))

    sealed_count = sum(1 for c in claims.values() if c.get("sealed"))
    open_count = sum(1 for c in claims.values() if not c.get("sealed"))
    synthesis_count = sum(1 for c in claims.values() if c.get("is_synthesis"))
    role_count = sum(1 for c in claims.values() if c.get("is_role_generated"))
    contradicted = any(c.get("status") == "contradicted" for c in claims.values())

    result_data = {
        "qid": qid,
        "question": question,
        "success": result.returncode == 0,
        "elapsed_seconds": round(elapsed, 1),
        "iterations": state_data.get("iteration", 0),
        "claims_total": len(claims),
        "claims_sealed": sealed_count,
        "claims_open": open_count,
        "claims_synthesis": synthesis_count,
        "claims_role_generated": role_count,
        "transitions_fired": sorted(transitions_fired),
        "t1_fired": "T1" in transitions_fired,
        "t9_fired": "T9" in transitions_fired,
        "contradiction_detected": contradicted,
        "reframing_count": state_data.get("reframing_count", 0),
        "anti_delphi_activations": state_data.get("anti_delphi_activations", 0),
        "roles_generated": state_data.get("roles_generated", {}),
        "error": result.stderr[-500:] if result.returncode != 0 else None,
        "stdout_tail": result.stdout[-1000:],
    }

    with open(RESULTS_DIR / f"{qid}.json", "w") as f:
        json.dump(result_data, f, indent=2)

    if Path("des_state.json").exists():
        shutil.copy("des_state.json", RESULTS_DIR / f"{qid}_state.json")

    return result_data


def print_summary(results: list[dict]):
    """Print a structured summary table."""
    print("\n" + "="*90)
    print("ANTI-DELPHI BATCH TEST SUMMARY")
    print("="*90)
    print(f"{'ID':<4} {'Question':<34} {'OK':<4} {'Iter':<6} {'Claims':<7} {'Open':<5} "
          f"{'AD':<4} {'T1':<4} {'T9':<4} {'Transitions'}")
    print("-"*90)

    for r in results:
        ok = "YES" if r["success"] else "NO"
        t1 = "YES" if r["t1_fired"] else "-"
        t9 = "YES" if r["t9_fired"] else "-"
        ad = str(r.get("anti_delphi_activations", 0))
        trans = ",".join(r["transitions_fired"])
        print(f"{r['qid']:<4} {r['question'][:30]:<34} {ok:<4} "
              f"{r['iterations']:<6} {r['claims_total']:<7} {r['claims_open']:<5} "
              f"{ad:<4} {t1:<4} {t9:<4} {trans}")

    print("-"*90)
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    t1_rate = sum(1 for r in results if r["t1_fired"]) / len(results) * 100
    t9_rate = sum(1 for r in results if r["t9_fired"]) / len(results) * 100
    avg_claims = sum(r["claims_total"] for r in results) / len(results)
    avg_iter = sum(r["iterations"] for r in results) / len(results)
    avg_ad = sum(r.get("anti_delphi_activations", 0) for r in results) / len(results)

    print(f"\nSuccess rate:           {success_rate:.0f}%")
    print(f"T1 fire rate:           {t1_rate:.0f}%")
    print(f"T9 fire rate:           {t9_rate:.0f}%")
    print(f"Avg Anti-Delphi act.:   {avg_ad:.1f}")
    print(f"Avg claims/run:         {avg_claims:.1f}")
    print(f"Avg iterations:         {avg_iter:.1f}")

    print("\nISSUES:")
    issues_found = False
    for r in results:
        if not r["success"]:
            print(f"  FAIL {r['qid']}: {r['error']}")
            issues_found = True
        if r["claims_open"] > 0:
            print(f"  OPEN {r['qid']}: {r['claims_open']} unsealed claim(s)")
            issues_found = True
    if not issues_found:
        print("  None.")

    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {RESULTS_DIR}/")


if __name__ == "__main__":
    results = []
    for qid, question in QUESTIONS.items():
        try:
            r = run_single(qid, question)
            results.append(r)
            status = "OK" if r["success"] else "FAIL"
            print(f"  -> {status} | {r['iterations']} iter | "
                  f"{r['claims_total']} claims | AD={r.get('anti_delphi_activations',0)} "
                  f"T1={r['t1_fired']} T9={r['t9_fired']}")
        except subprocess.TimeoutExpired:
            print(f"  -> TIMEOUT after 300s")
            results.append({
                "qid": qid, "question": question, "success": False,
                "error": "timeout", "transitions_fired": [],
                "t1_fired": False, "t9_fired": False,
                "claims_total": 0, "claims_open": 0, "claims_sealed": 0,
                "claims_synthesis": 0, "claims_role_generated": 0,
                "iterations": 0, "reframing_count": 0,
                "anti_delphi_activations": 0, "roles_generated": {},
                "elapsed_seconds": 300, "contradiction_detected": False,
            })
        except Exception as e:
            print(f"  -> ERROR: {e}")

    print_summary(results)

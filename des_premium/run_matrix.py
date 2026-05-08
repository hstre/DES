"""
des_premium/run_matrix.py
Orchestrator for the 2×2 model-architecture matrix.

Usage:
    python des_premium/run_matrix.py --pilot          # M01+N03, all 4 conditions
    python des_premium/run_matrix.py --condition cot_cheap
    python des_premium/run_matrix.py --condition des_premium
    python des_premium/run_matrix.py --condition cot_premium
    python des_premium/run_matrix.py --analysis       # recompile from existing results
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from des_premium.config import (
    CHEAP_CONFIG, PREMIUM_CONFIG, PILOT_DOMAINS, SEEDS,
)
from des_premium.run_des_cond import run_des_batch
from des_premium.run_cot_cond import run_cot_batch
from des_premium.analysis import (
    load_cheap_des_baseline,
    compute_2x2,
    write_matrix_md,
)

RESULTS_BASE = Path("des_premium")
COT_CHEAP_DIR    = RESULTS_BASE / "batch_results_cot_cheap"
COT_PREMIUM_DIR  = RESULTS_BASE / "batch_results_cot_premium"
DES_PREMIUM_DIR  = RESULTS_BASE / "batch_results_des_premium"
MATRIX_DIR       = RESULTS_BASE / "matrix_results"


def load_batch(results_dir: Path, domains: list, seeds: list) -> list:
    results = []
    for domain_id in domains:
        for seed_n in seeds:
            p = results_dir / f"{domain_id}_seed{seed_n}" / "outcome.json"
            if p.exists():
                with open(p) as f:
                    results.append(json.load(f))
    return results


def run_analysis(domains: list = PILOT_DOMAINS) -> dict:
    """Load all 4 conditions and compute 2×2 decomposition."""
    print("\n[matrix] Loading cheap DES baseline from Paper 8 Arm B...")
    des_cheap   = load_cheap_des_baseline(domains, SEEDS)

    print("[matrix] Loading CoT cheap results...")
    cot_cheap   = load_batch(COT_CHEAP_DIR, domains, SEEDS)

    print("[matrix] Loading DES premium results...")
    des_premium = load_batch(DES_PREMIUM_DIR, domains, SEEDS)

    print("[matrix] Loading CoT premium results...")
    cot_premium = load_batch(COT_PREMIUM_DIR, domains, SEEDS)

    print(f"[matrix] Cells: DES_cheap={len(des_cheap)} CoT_cheap={len(cot_cheap)} "
          f"DES_premium={len(des_premium)} CoT_premium={len(cot_premium)}")

    analysis = compute_2x2(des_cheap, cot_cheap, des_premium, cot_premium, domains)

    MATRIX_DIR.mkdir(parents=True, exist_ok=True)
    with open(MATRIX_DIR / "matrix_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    write_matrix_md(analysis, MATRIX_DIR / "matrix_analysis.md")
    print(f"[matrix] analysis → {MATRIX_DIR}/matrix_analysis.md")
    _print_summary(analysis)
    return analysis


def _print_summary(analysis: dict) -> None:
    cells = analysis["cells"]
    d     = analysis["decomposition"]
    print("\n=== 2×2 SUMMARY ===")
    print(f"{'':25} {'DES cheap':>12} {'DES premium':>12} {'CoT cheap':>12} {'CoT premium':>12}")
    for metric, key in [("depth",          "depth"),
                         ("dup_rate",       "dup_rate"),
                         ("false_proof(M01)","false_proof_rate")]:
        row = [f"{cells[c].get(key,'N/A')}" for c in
               ["DES_cheap","DES_premium","CoT_cheap","CoT_premium"]]
        print(f"  {metric:23} {row[0]:>12} {row[1]:>12} {row[2]:>12} {row[3]:>12}")
    print()
    print(f"  arch_effect_cheap   = {d['arch_effect_cheap']}")
    print(f"  arch_effect_premium = {d['arch_effect_premium']}")
    print(f"  model_effect_des    = {d['model_effect_des']}")
    print(f"  model_effect_cot    = {d['model_effect_cot']}")
    print(f"  interaction         = {d['interaction']}")
    print(f"  → {d['interaction_interpretation']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot",     action="store_true",
                        help="Run full pilot: CoT cheap + DES premium + CoT premium")
    parser.add_argument("--condition", choices=["cot_cheap","des_premium","cot_premium"],
                        default=None)
    parser.add_argument("--analysis",  action="store_true",
                        help="Recompile matrix from existing results")
    parser.add_argument("--domains",   nargs="+", default=None,
                        help="Override domain list (default: PILOT_DOMAINS)")
    args = parser.parse_args()

    domains = args.domains or PILOT_DOMAINS

    if args.analysis:
        run_analysis(domains)

    elif args.condition == "cot_cheap":
        run_cot_batch(CHEAP_CONFIG, COT_CHEAP_DIR, domains)

    elif args.condition == "des_premium":
        run_des_batch(PREMIUM_CONFIG, DES_PREMIUM_DIR, domains)

    elif args.condition == "cot_premium":
        run_cot_batch(PREMIUM_CONFIG, COT_PREMIUM_DIR, domains)

    elif args.pilot:
        print("\n" + "="*70)
        print("2×2 Pilot: CoT cheap (Condition 2)")
        print("="*70)
        run_cot_batch(CHEAP_CONFIG, COT_CHEAP_DIR, domains)

        print("\n" + "="*70)
        print("2×2 Pilot: DES premium (Condition 3)")
        print("="*70)
        run_des_batch(PREMIUM_CONFIG, DES_PREMIUM_DIR, domains)

        print("\n" + "="*70)
        print("2×2 Pilot: CoT premium (Condition 4)")
        print("="*70)
        run_cot_batch(PREMIUM_CONFIG, COT_PREMIUM_DIR, domains)

        run_analysis(domains)

    else:
        parser.print_help()

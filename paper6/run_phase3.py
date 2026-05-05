"""
paper6/run_phase3.py
Phase 3: Controlled comparison on high-SH domains from Phase 2.
Runs each high-SH domain twice: P4 (no perturbation) vs P5v05 (SPL).
Measures depth lift.
WP2 (Rentschler 2026).
"""

import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RESULTS_DIR_P3 = Path("paper6/phase3_results")
SH_STAR = 0.0876  # from Phase 1

# Phase 2 summary path — populated after Phase 2 completes
PHASE2_SUMMARY = Path("paper6/phase2_results/phase2_summary.json")


def load_high_sh_domains() -> dict:
    """Load Phase 2 results and return domains with SH > SH*."""
    if not PHASE2_SUMMARY.exists():
        raise FileNotFoundError(
            f"{PHASE2_SUMMARY} not found. Run Phase 2 first."
        )
    with open(PHASE2_SUMMARY) as f:
        summary = json.load(f)

    high_sh = {}
    for row in summary.get("rows", []):
        if row.get("sh_loop0") and row["sh_loop0"] > SH_STAR:
            high_sh[row["domain"]] = {
                "seed": row["seed"],
                "sh_loop0": row["sh_loop0"],
                "p4_depth": row["loops"],
            }

    return high_sh


def run_phase3():
    """
    Phase 3: controlled comparison.
    Requires Phase 2 to be complete.
    Runs P4 and P5v05 on high-SH domains.
    """
    high_sh = load_high_sh_domains()

    if len(high_sh) < 3:
        print(f"WARNING: Only {len(high_sh)} high-SH domains (need ≥ 3 for Phase 3)")
        print(f"High-SH domains: {list(high_sh.keys())}")
        if not high_sh:
            print("Phase 3 cannot proceed — no high-SH domains confirmed.")
            return

    print("=" * 65)
    print(f"Paper 6 — Phase 3: Controlled Comparison")
    print(f"High-SH domains ({len(high_sh)}): {list(high_sh.keys())}")
    print(f"SH* = {SH_STAR}")
    print("=" * 65)

    RESULTS_DIR_P3.mkdir(parents=True, exist_ok=True)

    # Phase 3 runs P4 config (already done in Phase 2 for these domains)
    # and P5v05 config using the existing paper5 runner
    # Reuse Phase 2 P4 results (already in phase2_results/NXX/)

    results = {}
    for domain_id, info in high_sh.items():
        print(f"\n{domain_id}: {info['seed'][:60]}")
        print(f"  SH={info['sh_loop0']:.4f}  P4_depth(Phase2)={info['p4_depth']}")

        # P4 results already exist from Phase 2
        p4_outcome_file = Path("paper6/phase2_results") / domain_id / "outcome.json"
        if p4_outcome_file.exists():
            with open(p4_outcome_file) as f:
                p4_result = json.load(f)
        else:
            print(f"  WARNING: Phase 2 P4 result not found for {domain_id}")
            p4_result = None

        results[domain_id] = {
            "sh_loop0": info["sh_loop0"],
            "p4_depth": info["p4_depth"],
            "p4_outcome": p4_result.get("outcome") if p4_result else None,
            "p5_depth": None,
            "p5_outcome": None,
            "depth_lift": None,
        }

    # P5v05 runs: use the existing paper5 runner adapted for Phase 3 domains
    # P5v05 results go to paper6/phase3_results/NXX_v05/
    print("\nP5v05 runs will be launched separately via run_phase3_v05.py")
    print("(Phase 3 P5v05 runner reads high-SH domains from this summary)")

    # Save partial summary
    out_path = RESULTS_DIR_P3 / "phase3_summary.json"
    summary = {
        "phase": 3,
        "sh_star": SH_STAR,
        "high_sh_domains": list(high_sh.keys()),
        "n_high_sh": len(high_sh),
        "status": "p4_complete_from_phase2__p5_pending",
        "domains": results,
    }
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved Phase 3 stub: {out_path}")
    return results


def write_phase3_final_report(p5_results: dict):
    """
    Called after P5v05 runs complete.
    p5_results: {domain_id: {"depth": int, "outcome": str}}
    """
    high_sh = load_high_sh_domains()
    results = {}

    for domain_id, info in high_sh.items():
        p5 = p5_results.get(domain_id, {})
        p5_depth = p5.get("depth")
        p4_depth = info["p4_depth"]
        lift = (p5_depth - p4_depth) if (p5_depth and p4_depth) else None
        results[domain_id] = {
            "sh_loop0": info["sh_loop0"],
            "p4_depth": p4_depth,
            "p5_depth": p5_depth,
            "depth_lift": lift,
            "p5_outcome": p5.get("outcome"),
        }

    lifts = [r["depth_lift"] for r in results.values() if r["depth_lift"] is not None]
    benefit_rate = sum(1 for l in lifts if l > 0) / len(lifts) if lifts else None

    summary = {
        "phase": 3,
        "sh_star": SH_STAR,
        "n_high_sh_domains": len(results),
        "perturbation_benefit_rate": round(benefit_rate, 3) if benefit_rate else None,
        "h2_verdict": (
            "CONFIRMED" if benefit_rate and benefit_rate >= 0.60 else
            "NOT_CONFIRMED" if benefit_rate is not None else "INSUFFICIENT_DATA"
        ),
        "phase3_failure": benefit_rate is not None and benefit_rate < 0.40,
        "domains": results,
    }

    out_path = RESULTS_DIR_P3 / "phase3_final.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print("Phase 3 Final Report")
    print("=" * 65)
    print(f"{'Domain':<8} {'SH':<8} {'P4 dep':<8} {'P5 dep':<8} {'lift':<6} {'P5 outcome'}")
    print("-" * 55)
    for d, r in results.items():
        print(f"{d:<8} {r['sh_loop0']:.4f}   {str(r['p4_depth']):<8} "
              f"{str(r['p5_depth']):<8} {str(r['depth_lift']):<6} {r['p5_outcome']}")

    print(f"\nPerturbation benefit rate: {benefit_rate:.0%}" if benefit_rate else "")
    print(f"H2 verdict: {summary['h2_verdict']}")
    if summary["phase3_failure"]:
        print("PHASE3 = PERTURBATION_BENEFIT_NOT_CONFIRMED")
    print(f"\nSaved: {out_path}")
    return summary


if __name__ == "__main__":
    run_phase3()

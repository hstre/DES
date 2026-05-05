"""
paper6/phase1_retrograde.py
Phase 1: Retrograde SH validation using existing P4 and P5v05 state files.
Computes SH from loop_000_state.json for all 5 domains.
Correlates with loop depth. Estimates SH*.
WP2 (Rentschler 2026).
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper6.compute_sh import compute_semantic_headroom

# ── Baseline data (pre-registered) ──────────────────────────────────────────

DOMAINS = {
    "R01": {
        "seed": "Does raising the minimum wage reduce employment?",
        "p4_depth": 2,
        "p5v05_depth": 2,
        "p4_state": "paper4/batch_results_paper4/R01/loop_000_state.json",
        "p5_state": "paper5/batch_results_paper5_v05/R01/loop_000_state.json",
    },
    "R02": {
        "seed": "Does social media use cause depression in teenagers?",
        "p4_depth": 3,
        "p5v05_depth": 1,
        "p4_state": "paper4/batch_results_paper4/R02/loop_000_state.json",
        "p5_state": "paper5/batch_results_paper5_v05/R02/loop_000_state.json",
    },
    "R03": {
        "seed": "Does remote work reduce productivity?",
        "p4_depth": 4,
        "p5v05_depth": 1,
        "p4_state": "paper4/batch_results_paper4/R03/loop_000_state.json",
        "p5_state": "paper5/batch_results_paper5_v05/R03/loop_000_state.json",
    },
    "R04": {
        "seed": "Does GDP growth improve human wellbeing?",
        "p4_depth": 3,
        "p5v05_depth": 5,
        "p4_state": "paper4/batch_results_paper4/R04/loop_000_state.json",
        "p5_state": "paper5/batch_results_paper5_v05/R04/loop_000_state.json",
    },
    "R05": {
        "seed": "Is intermittent fasting effective for long-term weight loss?",
        "p4_depth": 4,
        "p5v05_depth": 1,
        "p4_state": "paper4/batch_results_paper4/R05/loop_000_state.json",
        "p5_state": "paper5/batch_results_paper5_v05/R05/loop_000_state.json",
    },
}


def spearman_rho(x: list, y: list) -> float:
    """Spearman rank correlation."""
    n = len(x)
    if n < 2:
        return float("nan")

    def rank(lst):
        sorted_idx = sorted(range(n), key=lambda i: lst[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and lst[sorted_idx[j]] == lst[sorted_idx[j + 1]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[sorted_idx[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(x), rank(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    den = (
        math.sqrt(sum((rx[i] - mean_rx) ** 2 for i in range(n)))
        * math.sqrt(sum((ry[i] - mean_ry) ** 2 for i in range(n)))
    )
    return num / den if den > 0 else 0.0


def pearson_r(x: list, y: list) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = (
        math.sqrt(sum((x[i] - mx) ** 2 for i in range(n)))
        * math.sqrt(sum((y[i] - my) ** 2 for i in range(n)))
    )
    return num / den if den > 0 else 0.0


def estimate_sh_star(sh_values: list, depth_lift: list) -> float:
    """
    Estimate SH* as midpoint between highest SH with lift≤0 and lowest SH with lift>0.
    Returns None if no clean separation exists.
    """
    positive = [sh for sh, lift in zip(sh_values, depth_lift) if lift > 0]
    non_positive = [sh for sh, lift in zip(sh_values, depth_lift) if lift <= 0]
    if not positive or not non_positive:
        return None
    lo = max(non_positive)
    hi = min(positive)
    if hi > lo:
        return round((lo + hi) / 2, 4)
    return None


def run_phase1(base_dir: str = ".") -> dict:
    base = Path(base_dir)
    results = {}

    print("=" * 60)
    print("Paper 6 — Phase 1: Retrograde SH Validation")
    print("=" * 60)

    for domain_id, info in DOMAINS.items():
        p4_file = base / info["p4_state"]
        p5_file = base / info["p5_state"]

        sh_p4 = compute_semantic_headroom(str(p4_file))
        sh_p5 = compute_semantic_headroom(str(p5_file))

        results[domain_id] = {
            "seed": info["seed"],
            "p4_depth": info["p4_depth"],
            "p5v05_depth": info["p5v05_depth"],
            "depth_lift_p5": info["p5v05_depth"] - info["p4_depth"],
            "sh_p4": sh_p4,
            "sh_p5": sh_p5,
        }

        print(f"\n{domain_id}: {info['seed'][:60]}")
        print(f"  P4 depth={info['p4_depth']}  P5v05 depth={info['p5v05_depth']}  "
              f"lift={info['p5v05_depth'] - info['p4_depth']:+d}")
        if sh_p4.get("sh") is not None:
            print(f"  SH(P4 loop0) = {sh_p4['sh']:.4f}  "
                  f"SH_norm={sh_p4['sh_norm']:.4f}  "
                  f"SH_entropy={sh_p4['sh_entropy']:.4f}  "
                  f"n={sh_p4['n_claims']}")
        else:
            print(f"  SH(P4 loop0) = None ({sh_p4.get('reason')})")

        if sh_p5.get("sh") is not None:
            print(f"  SH(P5 loop0) = {sh_p5['sh']:.4f}  "
                  f"SH_norm={sh_p5['sh_norm']:.4f}  "
                  f"SH_entropy={sh_p5['sh_entropy']:.4f}  "
                  f"n={sh_p5['n_claims']}")

    # ── Correlation analysis (P4 loop0 SH vs P4 depth) ──────────────────────
    print("\n" + "=" * 60)
    print("Correlation Analysis: SH(P4 loop0) vs depth")
    print("=" * 60)

    sh_vals_p4, depths_p4, lifts = [], [], []
    for domain_id, r in results.items():
        if r["sh_p4"].get("sh") is not None:
            sh_vals_p4.append(r["sh_p4"]["sh"])
            depths_p4.append(r["p4_depth"])
            lifts.append(r["depth_lift_p5"])

    if len(sh_vals_p4) >= 3:
        rho_depth = spearman_rho(sh_vals_p4, depths_p4)
        r_depth = pearson_r(sh_vals_p4, depths_p4)
        rho_lift = spearman_rho(sh_vals_p4, lifts)
        r_lift = pearson_r(sh_vals_p4, lifts)
        print(f"  SH vs P4 depth:    Spearman ρ = {rho_depth:.3f}  "
              f"Pearson r = {r_depth:.3f}")
        print(f"  SH vs depth lift:  Spearman ρ = {rho_lift:.3f}  "
              f"Pearson r = {r_lift:.3f}")

        sh_star = estimate_sh_star(sh_vals_p4, lifts)
        print(f"\n  SH* estimate: {sh_star}")
        print(f"  (n=5; exploratory only — insufficient for robust calibration)")

        # H1 verdict
        h1 = "CONFIRMED" if rho_depth > 0.70 else (
            "WEAK" if rho_depth > 0.50 else "NOT_CONFIRMED"
        )
        print(f"\n  H1 verdict (ρ > 0.70): {h1} (ρ = {rho_depth:.3f})")
        if rho_depth < 0.50:
            print("  → PHASE1 = SH_NOT_PREDICTIVE: do not proceed to "
                  "Phase 2/3 with high confidence")
    else:
        rho_depth = r_depth = rho_lift = r_lift = sh_star = None
        h1 = "INSUFFICIENT_DATA"

    # ── Summary table ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Summary Table")
    print("=" * 60)
    print(f"{'Domain':<8} {'SH(P4)':<10} {'SH_norm':<10} {'SH_ent':<8} "
          f"{'n':<5} {'P4 dep':<8} {'P5 dep':<8} {'lift':<6}")
    print("-" * 70)
    for domain_id, r in results.items():
        sh = r["sh_p4"]
        sh_str = f"{sh['sh']:.4f}" if sh.get("sh") else "  None "
        shn_str = f"{sh['sh_norm']:.4f}" if sh.get("sh_norm") else "  None "
        she_str = f"{sh['sh_entropy']:.4f}" if sh.get("sh_entropy") else " None"
        n_str = str(sh.get("n_claims", "?"))
        print(f"{domain_id:<8} {sh_str:<10} {shn_str:<10} {she_str:<8} "
              f"{n_str:<5} {r['p4_depth']:<8} {r['p5v05_depth']:<8} "
              f"{r['depth_lift_p5']:+d}")

    # ── Save results ─────────────────────────────────────────────────────────
    output = {
        "phase": 1,
        "n_domains": len(results),
        "correlations": {
            "sh_vs_p4_depth": {
                "spearman_rho": round(rho_depth, 4) if rho_depth else None,
                "pearson_r": round(r_depth, 4) if r_depth else None,
            },
            "sh_vs_depth_lift": {
                "spearman_rho": round(rho_lift, 4) if rho_lift else None,
                "pearson_r": round(r_lift, 4) if r_lift else None,
            },
        },
        "sh_star_estimate": sh_star,
        "h1_verdict": h1,
        "domains": results,
    }

    out_path = Path(base_dir) / "paper6/phase1_results/phase1_retrograde.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        # centroid dicts are large — strip before saving
        slim = json.loads(json.dumps(output))
        for d in slim.get("domains", {}).values():
            for key in ("sh_p4", "sh_p5"):
                if isinstance(d.get(key), dict):
                    d[key].pop("centroid", None)
        json.dump(slim, f, indent=2)

    print(f"\nSaved: {out_path}")
    return output


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    run_phase1(base)

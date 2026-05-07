"""
paper9_25/run_reanalysis.py
Paper 9.25 — Geometry reanalysis: SH vs local_density correlation.

Reanalysis only — no new DES runs.
Sources:
  - Paper 6 Phase 2 (n=13 domains): sh_loop0 from phase2_summary.json +
    loop_000_state.json for density computation.
  - Paper 9 Phase 1 (n=4 domains × 3 seeds = 12 runs): pre_density from
    density_measurement.json + loop_000_state.json for SH computation.

Hypothesis: corr(local_density, SH) ≈ 0 (near-orthogonal).
"""

import json
import statistics
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.run_p8 import _init_clients
from paper9.measure_density import compute_density, _ensure_spl
from paper6.compute_sh import compute_semantic_headroom

OUTPUT_DIR   = Path("paper9_25")
P6_DIR       = Path("paper6/phase2_results")
P9_DIR       = Path("paper9/batch_results_phase1")
DENSITY_R    = 0.15   # primary radius (pre-registered in Phase 1)

P6_SUMMARY   = P6_DIR / "phase2_summary.json"

P9_DOMAINS   = {
    "M01": {
        "seed": ("Investigate the long-term behavior of the recursive map T(n): "
                 "if n mod 3 == 0 then T(n) = n/3, if n mod 3 == 1 then T(n) = 4n+2, "
                 "if n mod 3 == 2 then T(n) = 2n-1. Identify cycles, divergence "
                 "patterns, invariants, and plausible conjectures."),
        "expected_density": "high",
        "expected_sh":      "high",
        "type":             "formal_mathematics",
    },
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "expected_density": "medium_variable",
        "expected_sh":      "high",
        "type":             "empirical_argumentative",
    },
    "N_new_1": {
        "seed": ("Does aspirin reduce cardiovascular event risk in otherwise "
                 "healthy adults over 50?"),
        "expected_density": "high",
        "expected_sh":      "low",
        "type":             "narrow_empirical",
    },
    "N_new_2": {
        "seed": "What obligations do wealthy nations have toward climate refugees?",
        "expected_density": "low",
        "expected_sh":      "high",
        "type":             "broad_normative",
    },
}


# ── SH computation (reusing Paper 6 method) ───────────────────────────────────

def compute_sh_from_state(state_file: Path) -> dict:
    """Wrapper around Paper 6's compute_semantic_headroom."""
    result = compute_semantic_headroom(str(state_file))
    return result


def compute_local_density_from_state(state_file: Path, question: str,
                                     r: float = DENSITY_R) -> float:
    """
    Compute local_density(q, r) from a saved DES state file.
    q = domain seed question (measures density of seed in accumulated ClaimGraph).
    """
    with open(state_file) as f:
        state = json.load(f)
    claims = state.get("claims", {})
    return compute_density(question, claims, r)


# ── Load Paper 6 data ─────────────────────────────────────────────────────────

def load_paper6_data() -> list:
    """Load P6 Phase 2: SH from summary, compute local_density from state files."""
    with open(P6_SUMMARY) as f:
        summary = json.load(f)

    records = []
    for row in summary["rows"]:
        domain    = row["domain"]
        sh_loop0  = row["sh_loop0"]
        seed      = row["seed"]
        state_file = P6_DIR / domain / "loop_000_state.json"

        if not state_file.exists():
            print(f"  [skip] P6/{domain}: loop_000_state.json missing")
            continue

        density = compute_local_density_from_state(state_file, seed, DENSITY_R)
        print(f"  P6/{domain}: sh={sh_loop0:.4f}  density={density:.4f}  "
              f"actual_sh={row['actual_class']}")

        records.append({
            "source":          "paper6",
            "domain":          domain,
            "seed":            seed[:80],
            "sh":              sh_loop0,
            "sh_class":        row["actual_class"],
            "local_density":   density,
            "density_r":       DENSITY_R,
            "n_loops":         row.get("loops"),
            "domain_type":     _infer_domain_type(row),
        })
    return records


def _infer_domain_type(row: dict) -> str:
    seed = row["seed"].lower()
    if any(k in seed for k in ["t(n)", "recursive", "formal", "logic", "trolley"]):
        return "formal_or_philosophical"
    if any(k in seed for k in ["aspirin", "caffeine", "sleep", "class size", "gut"]):
        return "narrow_empirical"
    if any(k in seed for k in ["agi", "consciousness", "civiliz", "climate", "minimum wage",
                                "inequality", "microbiome"]):
        return "broad_argumentative"
    return "other"


# ── Load Paper 9 Phase 1 data ─────────────────────────────────────────────────

def load_paper9_data() -> list:
    """Load P9 Phase 1: pre_density from density_measurement.json, compute SH from states."""
    records = []
    for domain_id, domain_info in P9_DOMAINS.items():
        densities = []
        shs       = []
        for seed_n in [101, 202, 303]:
            run_dir   = P9_DIR / f"{domain_id}_seed{seed_n}"
            dm_file   = run_dir / "density_measurement.json"
            state_file = run_dir / "loop_000_state.json"

            if not dm_file.exists() or not state_file.exists():
                print(f"  [skip] P9/{domain_id}/seed{seed_n}: files missing")
                continue

            with open(dm_file) as f:
                dm = json.load(f)
            density = dm.get("pre_density_r015", 0.0)
            densities.append(density)

            sh_result = compute_sh_from_state(state_file)
            sh_val    = sh_result.get("sh")
            if sh_val is not None:
                shs.append(sh_val)

            print(f"  P9/{domain_id}/seed{seed_n}: sh={sh_val}  density={density:.4f}")

        if not densities or not shs:
            continue

        mean_density = round(statistics.mean(densities), 4)
        mean_sh      = round(statistics.mean(shs), 4)

        # Classify SH per Paper 6 threshold SH* = 0.0876
        sh_class = "HIGH" if mean_sh >= 0.0876 else "LOW"

        records.append({
            "source":          "paper9_phase1",
            "domain":          domain_id,
            "seed":            domain_info["seed"][:80],
            "sh":              mean_sh,
            "sh_class":        sh_class,
            "local_density":   mean_density,
            "density_r":       DENSITY_R,
            "n_seeds":         len(densities),
            "domain_type":     domain_info["type"],
            "expected_density": domain_info["expected_density"],
            "expected_sh":     domain_info["expected_sh"],
        })

    return records


# ── Correlation analysis ──────────────────────────────────────────────────────

def run_correlation(records: list) -> dict:
    valid = [r for r in records if r.get("sh") is not None and r.get("local_density") is not None]

    sh_vals      = [r["sh"] for r in valid]
    density_vals = [r["local_density"] for r in valid]

    r_pearson,  p_pearson  = stats.pearsonr(sh_vals, density_vals)
    rho_spear,  p_spear    = stats.spearmanr(sh_vals, density_vals)

    # Within-source correlations
    p6 = [r for r in valid if r["source"] == "paper6"]
    p9 = [r for r in valid if r["source"] == "paper9_phase1"]

    def _corr(rows):
        if len(rows) < 3:
            return None, None, None, None
        sv = [r["sh"] for r in rows]
        dv = [r["local_density"] for r in rows]
        rp, pp = stats.pearsonr(sv, dv)
        rs, ps = stats.spearmanr(sv, dv)
        return round(float(rp), 4), round(float(pp), 4), round(float(rs), 4), round(float(ps), 4)

    r_p6, p_p6, rho_p6, p_rho_p6 = _corr(p6)
    r_p9, p_p9, rho_p9, p_rho_p9 = _corr(p9)

    # By domain type
    domain_stats = {}
    for dtype in set(r.get("domain_type", "other") for r in valid):
        rows = [r for r in valid if r.get("domain_type") == dtype]
        domain_stats[dtype] = {
            "n": len(rows),
            "mean_sh": round(statistics.mean(r["sh"] for r in rows), 4),
            "mean_density": round(statistics.mean(r["local_density"] for r in rows), 4),
        }

    # Verdict
    if abs(r_pearson) < 0.30:
        verdict = "NEAR_ORTHOGONAL"
    elif abs(r_pearson) > 0.60:
        verdict = "PROXY_RELATIONSHIP"
    else:
        verdict = "PARTIAL_CORRELATION"

    return {
        "n_total":          len(valid),
        "n_paper6":         len(p6),
        "n_paper9":         len(p9),
        "pearson_r":        round(float(r_pearson), 4),
        "pearson_p":        round(float(p_pearson), 4),
        "spearman_rho":     round(float(rho_spear), 4),
        "spearman_p":       round(float(p_spear), 4),
        "pearson_r_p6":     r_p6,
        "pearson_p_p6":     p_p6,
        "spearman_rho_p6":  rho_p6,
        "pearson_r_p9":     r_p9,
        "pearson_p_p9":     p_p9,
        "spearman_rho_p9":  rho_p9,
        "domain_type_stats": domain_stats,
        "verdict":          verdict,
    }


# ── Write seed analysis report ────────────────────────────────────────────────

def write_seed_report(records: list, corr: dict) -> None:
    from paper8.run_p8 import call_llm

    valid = [r for r in records if r.get("sh") is not None]
    per_domain_rows = "\n".join(
        f"| {r['domain']} | {r['source']} | {r['sh']:.4f} | {r['sh_class']} "
        f"| {r['local_density']:.4f} | {r.get('domain_type','?')} |"
        for r in sorted(valid, key=lambda x: x["sh"])
    )

    # Per-quadrant summary
    quads = {"high_sh_high_d": [], "high_sh_low_d": [],
             "low_sh_high_d": [],  "low_sh_low_d": []}
    sh_threshold   = 0.0876
    dens_threshold = statistics.median(r["local_density"] for r in valid) if valid else 0.5
    for r in valid:
        h_sh = r["sh"] >= sh_threshold
        h_d  = r["local_density"] >= dens_threshold
        key = ("high" if h_sh else "low") + "_sh_" + ("high" if h_d else "low") + "_d"
        quads[key].append(r["domain"])

    prompt = f"""You are writing paper9_25/geometry_reanalysis.md.

Paper 9.25 Seed hypothesis: local_semantic_density and SH (Semantic Headroom) are
near-orthogonal geometric properties of ClaimGraphs in semantic projection space.

SOURCES:
- Paper 6 Phase 2: {corr['n_paper6']} domains with sh_loop0 (from phase2_summary.json) +
  local_density computed from loop_000_state.json at r={DENSITY_R}
- Paper 9 Phase 1: {corr['n_paper9']} domains with mean pre_density + SH computed from loop_000_states

FULL DATA TABLE (sorted by SH):
| Domain | Source | SH | SH_class | local_density (r={DENSITY_R}) | domain_type |
|--------|--------|-----|----------|------------------------|-------------|
{per_domain_rows}

CORRELATIONS (n={corr['n_total']}):
- Pearson r  = {corr['pearson_r']} (p={corr['pearson_p']})
- Spearman ρ = {corr['spearman_rho']} (p={corr['spearman_p']})
- Pearson r (Paper 6 only, n={corr['n_paper6']}): {corr['pearson_r_p6']} (p={corr['pearson_p_p6']})
- Pearson r (Paper 9 only, n={corr['n_paper9']}): {corr['pearson_r_p9']} (p={corr['pearson_p_p9']})

VERDICT: {corr['verdict']}
  |r| < 0.30 → NEAR_ORTHOGONAL (hypothesis supported)
  |r| > 0.60 → PROXY_RELATIONSHIP (SH ≈ density, redundant)
  else → PARTIAL_CORRELATION

DOMAIN TYPE STATS:
{json.dumps(corr['domain_type_stats'], indent=2)}

2×2 QUADRANT OCCUPANCY (SH threshold={sh_threshold}, density threshold={dens_threshold:.3f}):
- High SH + High density: {quads['high_sh_high_d']}
- High SH + Low density:  {quads['high_sh_low_d']}
- Low SH + High density:  {quads['low_sh_high_d']}
- Low SH + Low density:   {quads['low_sh_low_d']}

Paper 9.25 expected predictions:
- M01 (formal math): high SH + high local_density
- N_new_2 (broad normative): high SH + low density
- N_new_1 (narrow empirical): low SH + high density
- N03 (argumentative): high SH + medium density

Write the analysis in this exact format. Report faithfully. Label EXPLORATORY REANALYSIS.

---

# Paper 9.25 — Geometry Reanalysis
**EXPLORATORY REANALYSIS — not pre-registered, not confirmatory.**
**Sources: Paper 6 Phase 2 (n={corr['n_paper6']}) + Paper 9 Phase 1 (n={corr['n_paper9']})**

## Purpose
[One paragraph: origin of hypothesis, what Phase 1 unexpectedly found, what this reanalysis tests]

## Data Table
[Reproduce full data table sorted by SH, all columns]

## Correlation Results
| Statistic | Value | p-value | Interpretation |
|-----------|-------|---------|----------------|
| Pearson r (combined) | ... | ... | ... |
| Spearman ρ (combined) | ... | ... | ... |
| Pearson r (P6 only) | ... | ... | ... |
| Pearson r (P9 only) | ... | ... | ... |

## 2×2 Quadrant Analysis
[Reproduce quadrant occupancy with domain labels]
[Does the 2×2 structure have cells in all 4 quadrants?]

## Prediction Table Outcomes
| Domain | Expected SH | Actual SH | Expected density | Actual density | Match? |
|--------|-------------|-----------|-----------------|----------------|--------|
[Fill for M01, N03, N_new_1, N_new_2]

## Verdict: {corr['verdict']}
[Explain what |r| = {corr['pearson_r']} means for the hypothesis]
[Are SH and local_density orthogonal, partial, or proxy?]

## Implication for Paper 9.25 Design
[If NEAR_ORTHOGONAL: two-axis characterization is meaningful, proceed to Design Memo]
[If PROXY_RELATIONSHIP: density and SH are redundant, Paper 9.25 hypothesis is not supported]
[If PARTIAL_CORRELATION: partial independence, describe what additional structure is needed]

## Negative Findings
- Expected M01 prediction (high SH + high density): [match / no match]
- Expected N03 prediction (high SH + medium density): [match / no match]
- Domains violating expected 2×2 structure: [list or "none"]
- Cross-source consistency (P6 vs P9 correlation direction): [same / different]
- Limitations: [reanalysis from loop_0 only, single-point density measurement, spl_mode]
"""

    md_text = call_llm(prompt, max_tokens=2500, temperature=0.3)
    header  = (
        "<!-- paper9_25/geometry_reanalysis -->\n"
        "<!-- EXPLORATORY REANALYSIS — not pre-registered, not confirmatory -->\n\n"
    )
    (OUTPUT_DIR / "geometry_reanalysis.md").write_text(header + md_text + "\n")
    print(f"\n  Written → {OUTPUT_DIR}/geometry_reanalysis.md")


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all() -> None:
    _init_clients()
    _ensure_spl()   # initialize SPL after _init_clients
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nPaper 9.25 — Geometry Reanalysis")
    print(f"Sources: Paper 6 Phase 2 (n=13) + Paper 9 Phase 1 (n=4 domains)")
    print()

    print("Loading Paper 6 Phase 2 data ...")
    p6_records = load_paper6_data()

    print("\nLoading Paper 9 Phase 1 data (computing SH from states) ...")
    p9_records = load_paper9_data()

    all_records = p6_records + p9_records

    with open(OUTPUT_DIR / "all_records.json", "w") as f:
        json.dump(all_records, f, indent=2)

    print(f"\nRunning correlation analysis ({len(all_records)} records) ...")
    corr = run_correlation(all_records)

    with open(OUTPUT_DIR / "correlation_results.json", "w") as f:
        json.dump(corr, f, indent=2)

    print(f"\n  Pearson r  = {corr['pearson_r']:.4f} (p={corr['pearson_p']:.4f})")
    print(f"  Spearman ρ = {corr['spearman_rho']:.4f} (p={corr['spearman_p']:.4f})")
    print(f"  Verdict: {corr['verdict']}")

    write_seed_report(all_records, corr)

    print("\nPaper 9.25 reanalysis complete.")


if __name__ == "__main__":
    run_all()

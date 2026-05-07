"""
paper8_75/run_orthogonality.py
Paper 8.75 — Orthogonality Check: local_semantic_density vs activation_frame_complexity.

Tests whether density and framing complexity are empirically independent in
Paper 9's planned 2×3 factorial. Identified as potential confound by
Desi (Paper 8.5 Arm B).

12 runs: 4 conditions × 3 seeds.
P4 config (no perturbation, single-agent DES), max 3 loops per condition.
Key measurement: after loop 0, compute density for loop-1 candidate question.

spl_wrapper fallback: sentence-transformers cosine distance (documented).
"""

import json
import math
import sys
from pathlib import Path
from statistics import mean, stdev

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.mol import OPERATOR_LIBRARY, invoke_operator, extract_dominant_motif, extract_core_tension
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    compute_metrics,
    check_failure,
    _claim_text,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    DOMAINS,
)
import paper8.run_p8 as _p8

OUTPUT_DIR = Path("paper8_75")
MAX_LOOPS  = 3
MAX_ITER   = 40
DENSITY_R  = 0.30   # fallback cosine-distance threshold (analogous to spl THRESHOLD)

# ── Density computation ────────────────────────────────────────────────────────

try:
    from spl_wrapper import project as _spl_project, distance as _spl_distance
    _SPL_AVAILABLE = True
except ImportError:
    _SPL_AVAILABLE = False

_ENCODER = None

def _get_encoder():
    global _ENCODER
    if _ENCODER is None:
        from sentence_transformers import SentenceTransformer
        _ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
    return _ENCODER


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 1.0
    return float(1.0 - np.dot(a, b) / norm)


def compute_local_density(question: str, claims: dict, r: float = DENSITY_R) -> float:
    """
    density(q, r) = count(c : dist(embed(c), embed(q)) < r) / n_claims

    Primary: spl_wrapper sqrt_JSD projection (r=0.15).
    Fallback: sentence-transformers cosine distance (r=0.30, documented).
    """
    sealed = [c for c in claims.values() if c.get("sealed")]
    if not sealed:
        return 0.0

    if _SPL_AVAILABLE:
        q_proj = _spl_project(question)
        nearby = sum(
            1 for c in sealed
            if _spl_distance(
                _spl_project(_claim_text(c)), q_proj
            ) < 0.15
        )
        return round(nearby / len(sealed), 4)

    # Fallback: sentence-transformers
    enc = _get_encoder()
    claim_texts = [_claim_text(c) for c in sealed]
    all_texts   = claim_texts + [question]
    embeddings  = enc.encode(all_texts, normalize_embeddings=True)
    q_emb       = embeddings[-1]
    claim_embs  = embeddings[:-1]

    nearby = sum(
        1 for emb in claim_embs
        if _cosine_distance(emb, q_emb) < r
    )
    return round(nearby / len(sealed), 4)


# ── Activation complexity ──────────────────────────────────────────────────────

def compute_activation_complexity(operator_id: str) -> float:
    op = OPERATOR_LIBRARY.get(operator_id)
    if not op:
        return 0.0
    max_components = max(len(o.algorithmic_components) for o in OPERATOR_LIBRARY.values())
    return round(len(op.algorithmic_components) / max_components, 4)


# ── Conditions ────────────────────────────────────────────────────────────────

ORTHOGONALITY_CONDITIONS = {
    "low_density_low_framing": {
        "domain":                 "M01",
        "seed":                   DOMAINS["M01"]["seed"],
        "expected_density":       "low",
        "operator_for_complexity": "counterexample_search",
    },
    "low_density_high_framing": {
        "domain":                 "M01",
        "seed":                   DOMAINS["M01"]["seed"],
        "expected_density":       "low",
        "operator_for_complexity": "recursive_modulation",
    },
    "high_density_low_framing": {
        "domain":                 "N03",
        "seed":                   DOMAINS["N03"]["seed"],
        "expected_density":       "high",
        "operator_for_complexity": "counterexample_search",
    },
    "high_density_high_framing": {
        "domain":                 "N03",
        "seed":                   DOMAINS["N03"]["seed"],
        "expected_density":       "high",
        "operator_for_complexity": "recursive_modulation",
    },
}

SEEDS = [101, 202, 303]


# ── Single run ─────────────────────────────────────────────────────────────────

def run_condition_seed(
    condition_id: str,
    cond: dict,
    seed_id: int,
    run_dir: Path,
) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / f"result_{seed_id}.json"

    if result_file.exists():
        print(f"    [skip] {condition_id} seed={seed_id}")
        with open(result_file) as f:
            return json.load(f)

    loop_file = run_dir / f"loop_000_seed{seed_id}.json"
    operator_id = cond["operator_for_complexity"]

    print(f"    Running {condition_id} seed={seed_id} | op={operator_id}")

    # P4 config: single agent (no anti_delphi), no perturbation
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    try:
        _p8.des_module.run_des(
            research_question=cond["seed"],
            max_iterations=MAX_ITER,
            anti_delphi=False,         # P4 config: single agent
            builder_model=BUILDER_MODEL,
            builder_provider=BUILDER_PROVIDER,
        )
    except Exception as e:
        print(f"    ERROR: {e}")
        return {"condition": condition_id, "seed": seed_id, "error": str(e)}

    if not STATE_FILE.exists():
        return {"condition": condition_id, "seed": seed_id, "error": "state_missing"}

    with open(STATE_FILE) as f:
        state = json.load(f)

    with open(loop_file, "w") as f:
        json.dump(state, f, indent=2)

    claims = state.get("claims", {})
    n_sealed = sum(1 for c in claims.values() if c.get("sealed"))

    # Generate loop-1 candidate question using the specified operator
    # (operator would fire in P5+ config; here we measure what it would produce)
    try:
        op_result = invoke_operator(
            operator_id, state, cond["seed"], [cond["seed"]],
            call_llm_fn=call_llm,
        )
        candidate_q = op_result["question"] if op_result["admitted"] else cond["seed"]
        op_admitted  = op_result["admitted"]
        eni_composite = op_result.get("eni_composite", 0.0)
    except Exception as e:
        print(f"    WARNING: operator invocation failed: {e}")
        candidate_q  = cond["seed"]
        op_admitted  = False
        eni_composite = 0.0

    # Compute density for the candidate question against loop-0 ClaimGraph
    density = compute_local_density(candidate_q, claims)

    # Activation complexity (fixed by operator schema)
    complexity = compute_activation_complexity(operator_id)

    result = {
        "condition":           condition_id,
        "domain":              cond["domain"],
        "seed_id":             seed_id,
        "operator_id":         operator_id,
        "expected_density":    cond["expected_density"],
        "n_claims":            len(claims),
        "n_sealed":            n_sealed,
        "candidate_question":  candidate_q,
        "op_admitted":         op_admitted,
        "eni_composite":       eni_composite,
        "local_density":       density,
        "activation_complexity": complexity,
        "density_method":      "spl_wrapper" if _SPL_AVAILABLE else "sentence_transformers_cosine",
        "density_threshold":   0.15 if _SPL_AVAILABLE else DENSITY_R,
    }

    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"      density={density:.4f}  complexity={complexity:.4f}  "
          f"sealed={n_sealed}/{len(claims)}")
    return result


# ── Analysis ──────────────────────────────────────────────────────────────────

def run_analysis(all_results: list) -> dict:
    valid = [r for r in all_results if "error" not in r]

    densities    = [r["local_density"] for r in valid]
    complexities = [r["activation_complexity"] for r in valid]

    r_pearson, p_pearson   = stats.pearsonr(densities, complexities)
    rho_spearman, p_spearman = stats.spearmanr(densities, complexities)

    # Per-condition means
    cond_means: dict = {}
    for cid in ORTHOGONALITY_CONDITIONS:
        rows = [r for r in valid if r["condition"] == cid]
        if rows:
            cond_means[cid] = {
                "mean_density":     round(mean(r["local_density"] for r in rows), 4),
                "mean_complexity":  round(rows[0]["activation_complexity"], 4),
                "n":                len(rows),
            }

    # Within-domain density shifts (check B)
    def domain_op_mean(domain: str, op: str) -> float:
        rows = [r for r in valid if r["domain"] == domain and r["operator_id"] == op]
        return mean(r["local_density"] for r in rows) if rows else 0.0

    density_M01_low  = domain_op_mean("M01", "counterexample_search")
    density_M01_high = domain_op_mean("M01", "recursive_modulation")
    density_N03_low  = domain_op_mean("N03", "counterexample_search")
    density_N03_high = domain_op_mean("N03", "recursive_modulation")

    shift_M01 = abs(density_M01_high - density_M01_low)
    shift_N03 = abs(density_N03_high - density_N03_low)

    # Within-complexity domain difference (check C)
    density_diff_low  = density_N03_low  - density_M01_low
    density_diff_high = density_N03_high - density_M01_high

    # DESIGN_ORTHOGONAL: always YES by construction (balanced 2×2)
    design_orthogonal = "YES"

    # EMPIRICALLY_ORTHOGONAL: from within-domain shifts
    if shift_M01 < 0.10 and shift_N03 < 0.10:
        empirically_orthogonal = "YES"
        emp_note = (f"shift_M01={shift_M01:.4f} < 0.10 AND "
                    f"shift_N03={shift_N03:.4f} < 0.10 → density is exogenous")
    else:
        empirically_orthogonal = "NO"
        emp_note = (f"shift_M01={shift_M01:.4f}, shift_N03={shift_N03:.4f} "
                    f"→ activation context affects measured density")

    return {
        "n_valid_runs":           len(valid),
        "pearson_r":              round(float(r_pearson), 4),
        "pearson_p":              round(float(p_pearson), 4),
        "spearman_rho":           round(float(rho_spearman), 4),
        "spearman_p":             round(float(p_spearman), 4),
        "condition_means":        cond_means,
        "density_M01_low_framing":  round(density_M01_low, 4),
        "density_M01_high_framing": round(density_M01_high, 4),
        "density_N03_low_framing":  round(density_N03_low, 4),
        "density_N03_high_framing": round(density_N03_high, 4),
        "shift_M01":              round(shift_M01, 4),
        "shift_N03":              round(shift_N03, 4),
        "density_diff_low_framing":  round(density_diff_low, 4),
        "density_diff_high_framing": round(density_diff_high, 4),
        "design_orthogonal":      design_orthogonal,
        "empirically_orthogonal": empirically_orthogonal,
        "empirically_orthogonal_note": emp_note,
    }


# ── Write summary ──────────────────────────────────────────────────────────────

def write_summary(all_results: list, analysis: dict) -> None:
    emp = analysis["empirically_orthogonal"]

    if emp == "YES":
        paper9_implication = (
            "EMPIRICALLY_ORTHOGONAL = YES: operator complexity is not distorting density "
            "measurement. Density is exogenous to framing condition. Paper 9's 2×3 design "
            "is interpretable as designed. Proceed to Paper 9 Design Memo."
        )
    else:
        paper9_implication = (
            "EMPIRICALLY_ORTHOGONAL = NO: activation context affects measured density. "
            "Density is endogenous to framing condition. Paper 9 must either: "
            "(a) treat density as endogenous and add framing_complexity as covariate, OR "
            "(b) measure density before operator selection (pre-activation density). "
            "Do NOT proceed to Paper 9 Design Memo without design revision."
        )

    cond_table = "\n".join(
        f"| {cid} | {v['mean_density']:.4f} | {v['mean_complexity']:.4f} | {v['n']} |"
        for cid, v in analysis["condition_means"].items()
    )

    prompt = f"""You are writing paper8_75/orthogonality_summary.md for Paper 8.75.

EXPERIMENT: Orthogonality check — local_semantic_density vs activation_frame_complexity.
12 runs: 4 conditions × 3 seeds. P4 config (single-agent DES, no perturbation).
Density fallback: {'spl_wrapper' if _SPL_AVAILABLE else 'sentence-transformers cosine distance (r=0.30)'} (spl_wrapper {'available' if _SPL_AVAILABLE else 'unavailable'}).

PER-CONDITION RESULTS:
| Condition | mean_density | mean_complexity | n_runs |
|-----------|-------------|----------------|--------|
{cond_table}

WITHIN-DOMAIN DENSITY SHIFTS:
- M01 low_framing (counterexample_search): density = {analysis['density_M01_low_framing']:.4f}
- M01 high_framing (recursive_modulation): density = {analysis['density_M01_high_framing']:.4f}
- shift_M01 = {analysis['shift_M01']:.4f}  (threshold: < 0.10 for EMPIRICALLY_ORTHOGONAL = YES)

- N03 low_framing (counterexample_search): density = {analysis['density_N03_low_framing']:.4f}
- N03 high_framing (recursive_modulation): density = {analysis['density_N03_high_framing']:.4f}
- shift_N03 = {analysis['shift_N03']:.4f}  (threshold: < 0.10 for EMPIRICALLY_ORTHOGONAL = YES)

WITHIN-COMPLEXITY DOMAIN DIFFERENCES:
- Low framing: N03 - M01 = {analysis['density_diff_low_framing']:.4f}
- High framing: N03 - M01 = {analysis['density_diff_high_framing']:.4f}

CORRELATIONS ({analysis['n_valid_runs']} data points):
- Pearson r  = {analysis['pearson_r']:.4f}  (p = {analysis['pearson_p']:.4f})
- Spearman ρ = {analysis['spearman_rho']:.4f}  (p = {analysis['spearman_p']:.4f})

VERDICTS:
- DESIGN_ORTHOGONAL:      {analysis['design_orthogonal']}
- EMPIRICALLY_ORTHOGONAL: {analysis['empirically_orthogonal']}
- Note: {analysis['empirically_orthogonal_note']}

PAPER 9 IMPLICATION:
{paper9_implication}

Write the summary in this exact format:

---

# Paper 8.75 — Orthogonality Check
**Density method: {'spl_wrapper (primary)' if _SPL_AVAILABLE else 'sentence-transformers cosine distance (fallback, r=0.30)'}**

## Purpose
[One paragraph: why this check is needed, what confound was identified by Paper 8.5]

## Definitions
[Reproduce the operational definitions of local_semantic_density and activation_complexity]

## Per-Condition Results
[Reproduce the table above, formatted as markdown]

## Correlation Results
| Statistic | Value | p-value | Interpretation |
|-----------|-------|---------|----------------|
| Pearson r | ... | ... | ... |
| Spearman ρ | ... | ... | ... |

## Within-Domain Density Shifts (Primary Check)
[Table showing shift_M01 and shift_N03 with threshold comparison]
[Interpretation of each shift]

## Within-Complexity Domain Difference (Secondary Check)
[Table showing density_diff_low and density_diff_high]
[What this tells us about domain driving density]

## Verdicts

### DESIGN_ORTHOGONAL: {analysis['design_orthogonal']}
[Explanation: by construction, the 2×2 matrix is balanced]

### EMPIRICALLY_ORTHOGONAL: {analysis['empirically_orthogonal']}
[Primary verdict from within-domain shifts]
[Explanation]

## Implication for Paper 9
[State the implication clearly based on verdict]

## Negative Findings
- Expected domain separation in density: [observed / not observed]
- Unexpected density pattern: [describe or "none"]
- Limitations of single-agent P4 config measurement: [state]
- spl_wrapper availability: [unavailable — fallback used; results may differ with SPL]
"""

    md_text = call_llm(prompt, max_tokens=2000, temperature=0.3)
    header  = (
        "<!-- paper8_75/orthogonality_summary -->\n"
        "<!-- Paper 8.75 — Orthogonality Check -->\n\n"
    )
    (OUTPUT_DIR / "orthogonality_summary.md").write_text(header + md_text + "\n")
    print(f"  Written → {OUTPUT_DIR}/orthogonality_summary.md")


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all() -> None:
    _init_clients()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nPaper 8.75 — Orthogonality Check")
    print(f"spl_wrapper: {'available' if _SPL_AVAILABLE else 'NOT available — using sentence-transformers fallback'}")
    print(f"density_threshold: {'0.15 (JSD)' if _SPL_AVAILABLE else f'{DENSITY_R} (cosine)'}")
    print()

    all_results = []

    for cond_id, cond in ORTHOGONALITY_CONDITIONS.items():
        cond_dir = OUTPUT_DIR / cond_id
        print(f"\n  Condition: {cond_id}")
        print(f"  Domain: {cond['domain']} | Operator: {cond['operator_for_complexity']}")

        for seed_id in SEEDS:
            result = run_condition_seed(cond_id, cond, seed_id, cond_dir)
            all_results.append(result)

    # Save raw results
    with open(OUTPUT_DIR / "orthogonality_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Written → {OUTPUT_DIR}/orthogonality_results.json")

    # Analysis
    valid = [r for r in all_results if "error" not in r]
    if len(valid) < 8:
        print(f"WARNING: only {len(valid)} valid results; need at least 8 for meaningful correlation")

    analysis = run_analysis(valid if valid else all_results)

    with open(OUTPUT_DIR / "orthogonality_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Written → {OUTPUT_DIR}/orthogonality_analysis.json")

    print(f"\n  Results summary:")
    print(f"  Pearson r  = {analysis['pearson_r']:.4f} (p={analysis['pearson_p']:.4f})")
    print(f"  Spearman ρ = {analysis['spearman_rho']:.4f} (p={analysis['spearman_p']:.4f})")
    print(f"  shift_M01  = {analysis['shift_M01']:.4f}  (threshold < 0.10)")
    print(f"  shift_N03  = {analysis['shift_N03']:.4f}  (threshold < 0.10)")
    print(f"  DESIGN_ORTHOGONAL:      {analysis['design_orthogonal']}")
    print(f"  EMPIRICALLY_ORTHOGONAL: {analysis['empirically_orthogonal']}")

    write_summary(all_results, analysis)

    print("\nPaper 8.75 complete.")
    print(f"EMPIRICALLY_ORTHOGONAL = {analysis['empirically_orthogonal']}")


if __name__ == "__main__":
    run_all()

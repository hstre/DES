"""
paper9/run_phase1.py
Paper 9 Phase 1: Measurement Validity — Pre-Activation Density Independence.

Paired design: one loop_0 DES run per domain × seed.
Both operator contexts applied to the SAME saved state.
No additional DES runs for framing conditions.

H1: Pre-activation density shows smaller within-domain shifts than post-activation
    density (shift_M01 < 0.10 AND shift_N03 < 0.10 for all domains).
H2: Paper 8.75 cross-over interaction is a post-activation artifact.
"""

import hashlib
import json
import statistics
import sys
from pathlib import Path

from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent))

import paper9.measure_density as _md
from paper9.measure_density import compute_density
from paper8.mol import (
    OPERATOR_LIBRARY,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    extract_dominant_claim,
)
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    _claim_text,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    FALSIFIER_MODEL,
    FALSIFIER_PROVIDER,
)
import paper8.run_p8 as _p8

RESULTS_DIR = Path("paper9/batch_results_phase1")
RADII       = [0.10, 0.15, 0.20]
MAX_ITER    = 40
SEEDS       = [101, 202, 303]

DOMAINS = {
    "M01": {
        "seed": ("Investigate the long-term behavior of the recursive map T(n): "
                 "if n mod 3 == 0 then T(n) = n/3, if n mod 3 == 1 then T(n) = 4n+2, "
                 "if n mod 3 == 2 then T(n) = 2n-1. Identify cycles, divergence "
                 "patterns, invariants, and plausible conjectures."),
        "expected_density": "low",
        "type": "formal_mathematics",
    },
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "expected_density": "high",
        "type": "empirical_argumentative",
    },
    "N_new_1": {
        "seed": ("Does aspirin reduce cardiovascular event risk in otherwise "
                 "healthy adults over 50?"),
        "expected_density": "low",
        "type": "narrow_empirical",
    },
    "N_new_2": {
        "seed": "What obligations do wealthy nations have toward climate refugees?",
        "expected_density": "high",
        "type": "broad_normative",
    },
}

FRAMING_CONDITIONS = {
    "low_framing":  "counterexample_search",
    "high_framing": "recursive_modulation",
}

RADII_KEYS = {r: f"r{int(r*100):03d}" for r in RADII}


# ── Neutral next-question generation (pre-activation, no operator context) ──────

def select_next_question(state: dict, question_history: list) -> str | None:
    """
    Generate a neutral candidate next question from the ClaimGraph
    without any operator context. Uses dominant motif + core tension only.
    This is the pre-activation baseline question.
    """
    claims = state.get("claims", {})
    if not claims:
        return None
    motif   = extract_dominant_motif(claims)
    tension = extract_core_tension(claims)
    prompt  = (
        f"Given dominant motif '{motif['subject']} {motif['predicate']}' "
        f"and core tension '{tension}', generate one research question "
        f"that explores an adjacent conceptual register. "
        f"Return ONLY: one question as a single sentence."
    )
    q = call_llm(prompt, max_tokens=100)
    return q.strip() if q else None


# ── Operator context builder (algorithmic, no DES state modification) ─────────

def build_operator_context(operator_id: str, claims: dict) -> dict:
    """
    Build the LLM context dict for an operator from the ClaimGraph.
    No LLM calls, no state modification.
    """
    op      = OPERATOR_LIBRARY[operator_id]
    context = {}
    if "extract_dominant_motif" in op.algorithmic_components:
        m = extract_dominant_motif(claims)
        context["dominant_motif"] = f"{m['subject']} {m['predicate']}"
    if "extract_core_tension" in op.algorithmic_components:
        context["core_tension"] = extract_core_tension(claims)
    if "extract_invariants" in op.algorithmic_components:
        invs = extract_invariants(claims)
        context["invariants"] = "; ".join(i["claim"] for i in invs[:2]) or "(none)"
    if "classify_trajectories" in op.algorithmic_components:
        traj = classify_trajectories(claims)
        context["growth_class"]      = str(traj["growth_class"])
        context["contraction_class"] = str(traj["contraction_class"])
    if "extract_dominant_claim" in op.algorithmic_components:
        dom = extract_dominant_claim(claims)
        context["dominant_claim"] = dom["claim"]
        context["confidence"]     = dom["confidence"]
    return context


def generate_operator_question(operator_id: str, claims: dict) -> tuple[str, str]:
    """
    Generate operator-specific candidate question via LLM.
    Returns (operator_q, prompt_hash).
    """
    op      = OPERATOR_LIBRARY[operator_id]
    context = build_operator_context(operator_id, claims)
    try:
        prompt      = op.llm_prompt_template.format(**context)
    except KeyError as e:
        prompt = f"Generate one research question related to: {list(context.values())[:2]}. Return ONLY the question."
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]
    operator_q  = call_llm(prompt, max_tokens=100).strip()
    return operator_q, prompt_hash


# ── Single paired run ─────────────────────────────────────────────────────────

def run_paired(domain_id: str, seed_n: int) -> dict:
    run_dir   = RESULTS_DIR / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "density_measurement.json"

    if result_file.exists():
        print(f"    [skip] {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    domain  = DOMAINS[domain_id]
    question = domain["seed"]
    loop0_file = run_dir / "loop_000_state.json"

    # ── Step 1: Run loop_0 ONCE (anti-delphi, same as rest of Paper 9 series)
    print(f"\n    {domain_id} seed={seed_n} | running loop_0 ...")
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    try:
        _p8.des_module.run_des(
            research_question=question,
            max_iterations=MAX_ITER,
            anti_delphi=True,
            builder_model=BUILDER_MODEL,
            builder_provider=BUILDER_PROVIDER,
            falsifier_model=FALSIFIER_MODEL,
            falsifier_provider=FALSIFIER_PROVIDER,
        )
    except Exception as e:
        print(f"    ERROR: {e}")
        return {"domain": domain_id, "seed_n": seed_n, "error": str(e)}

    if not STATE_FILE.exists():
        return {"domain": domain_id, "seed_n": seed_n, "error": "state_missing"}

    with open(STATE_FILE) as f:
        state_loop0 = json.load(f)

    with open(loop0_file, "w") as f:
        json.dump(state_loop0, f, indent=2)

    claims  = state_loop0.get("claims", {})
    n_sealed = sum(1 for c in claims.values() if c.get("sealed"))
    n_total  = len(claims)

    # ── Step 2: Derive next_q ONCE (neutral, no operator context)
    next_q = select_next_question(state_loop0, [question])
    if not next_q:
        return {"domain": domain_id, "seed_n": seed_n, "error": "next_q_generation_failed",
                "outcome": "LOOP_COMPLETE_loop0"}

    # ── Step 3: PRE-ACTIVATION density — same for both framings by construction
    pre_density = {r: compute_density(next_q, claims, r) for r in RADII}

    # ── Step 4: POST-ACTIVATION per framing — same ClaimGraph, different candidate_q
    framing_results: dict = {}
    for framing, operator_id in FRAMING_CONDITIONS.items():
        op          = OPERATOR_LIBRARY[operator_id]
        context     = build_operator_context(operator_id, claims)
        operator_q, prompt_hash = generate_operator_question(operator_id, claims)

        post_density = {r: compute_density(operator_q, claims, r) for r in RADII}

        framing_results[framing] = {
            "operator":       operator_id,
            "operator_q":     operator_q[:120],
            "prompt_hash":    prompt_hash,
            "context_fields": list(context.keys()),
            **{f"post_density_{RADII_KEYS[r]}": post_density[r] for r in RADII},
            **{f"delta_{RADII_KEYS[r]}": round(post_density[r] - pre_density[r], 4)
               for r in RADII},
        }

        print(f"      {framing}: pre={pre_density[0.15]:.4f} "
              f"post={post_density[0.15]:.4f} "
              f"delta={post_density[0.15]-pre_density[0.15]:+.4f}")

    result = {
        "domain":          domain_id,
        "domain_type":     domain["type"],
        "seed_n":          seed_n,
        "next_q":          next_q[:120],
        "n_sealed_claims": n_sealed,
        "n_total_claims":  n_total,
        "spl_mode":        _md.SPL_MODE,   # read after first compute_density call
        **{f"pre_density_{RADII_KEYS[r]}": pre_density[r] for r in RADII},
        "framing_results": framing_results,
    }

    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    return result


# ── Analysis ──────────────────────────────────────────────────────────────────

def compute_operator_shifts(results: list, r: float = 0.15) -> dict[str, float]:
    """Mean |density(high_q) - density(low_q)| per domain."""
    rk = RADII_KEYS[r]
    shifts = {}
    for domain in DOMAINS:
        vals = []
        for x in results:
            if x.get("domain") != domain:
                continue
            fr = x.get("framing_results", {})
            if "low_framing" not in fr or "high_framing" not in fr:
                continue
            low  = fr["low_framing"].get(f"post_density_{rk}", 0)
            high = fr["high_framing"].get(f"post_density_{rk}", 0)
            vals.append(abs(high - low))
        shifts[domain] = round(sum(vals) / len(vals), 4) if vals else None
    return shifts


def compute_pre_density_stats(results: list, r: float = 0.15) -> dict:
    rk  = RADII_KEYS[r]
    key = f"pre_density_{rk}"
    out = {}
    for domain in DOMAINS:
        vals = [x[key] for x in results if x.get("domain") == domain and key in x]
        if len(vals) >= 2:
            out[domain] = {
                "mean": round(statistics.mean(vals), 4),
                "std":  round(statistics.stdev(vals), 4),
                "n":    len(vals),
                "vals": vals,
            }
        elif len(vals) == 1:
            out[domain] = {"mean": vals[0], "std": 0.0, "n": 1, "vals": vals}
    return out


def compute_mean_delta(results: list, framing: str, r: float = 0.15) -> dict[str, float]:
    rk = RADII_KEYS[r]
    dk = f"delta_{rk}"
    out = {}
    for domain in DOMAINS:
        vals = []
        for x in results:
            if x.get("domain") != domain:
                continue
            fr = x.get("framing_results", {})
            if framing in fr:
                vals.append(abs(fr[framing].get(dk, 0)))
        out[domain] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def h1_verdict(results: list, r: float = 0.15) -> tuple[str, dict]:
    pre_stats  = compute_pre_density_stats(results, r)
    shifts     = compute_operator_shifts(results, r)
    d_low      = compute_mean_delta(results, "low_framing", r)
    d_high     = compute_mean_delta(results, "high_framing", r)

    stable     = all(v["std"] < 0.10 for v in pre_stats.values())
    no_shift   = all(v < 0.10 for v in shifts.values() if v is not None)
    low_delta  = all(v < 0.05 for v in d_low.values() if v is not None)
    high_delta = all(v < 0.05 for v in d_high.values() if v is not None)

    details = {
        "pre_density_stable": stable,
        "no_operator_shift":  no_shift,
        "low_delta_ok":       low_delta,
        "high_delta_ok":      high_delta,
        "pre_stats":          pre_stats,
        "shifts":             shifts,
        "mean_delta_low":     d_low,
        "mean_delta_high":    d_high,
    }

    if stable and no_shift and low_delta and high_delta:
        return "H1_CONFIRMED", details
    elif stable and no_shift:
        return "H1_PARTIAL", details
    else:
        return "H1_NOT_CONFIRMED", details


def h2_verdict(results: list) -> tuple[str, dict]:
    """
    H2: Paper 8.75 cross-over interaction is absent in pre-activation density.
    Cross-over test: does domain ordering (N03 > M01) hold consistently at pre-activation?
    """
    out = {}
    for r in RADII:
        pre_stats = compute_pre_density_stats(results, r)
        m01_mean  = pre_stats.get("M01", {}).get("mean")
        n03_mean  = pre_stats.get("N03", {}).get("mean")
        ordering_correct = (n03_mean > m01_mean) if (m01_mean is not None and n03_mean is not None) else None
        out[RADII_KEYS[r]] = {
            "M01_pre_mean":       m01_mean,
            "N03_pre_mean":       n03_mean,
            "ordering_N03_gt_M01": ordering_correct,
        }

    # Cross-over: ordering consistent across radii?
    orderings = [v["ordering_N03_gt_M01"] for v in out.values() if v["ordering_N03_gt_M01"] is not None]
    consistent = len(set(orderings)) == 1 if orderings else None

    h2 = "H2_CONFIRMED" if consistent and all(orderings) else (
         "H2_PARTIALLY_CONFIRMED" if consistent else
         "H2_NOT_CONFIRMED")

    return h2, {"per_radius": out, "ordering_consistent_across_radii": consistent}


# ── Write summary ──────────────────────────────────────────────────────────────

def write_summary(results: list, all_verdicts: dict) -> None:
    valid = [r for r in results if "error" not in r]

    # Build table rows per domain per radius
    domain_rows = {}
    for domain in DOMAINS:
        domain_rows[domain] = {}
        for r in RADII:
            pre_stats = compute_pre_density_stats(valid, r)
            shifts    = compute_operator_shifts(valid, r)
            d_low     = compute_mean_delta(valid, "low_framing", r)
            d_high    = compute_mean_delta(valid, "high_framing", r)
            domain_rows[domain][RADII_KEYS[r]] = {
                "pre_mean": pre_stats.get(domain, {}).get("mean"),
                "pre_std":  pre_stats.get(domain, {}).get("std"),
                "shift":    shifts.get(domain),
                "delta_low":  d_low.get(domain),
                "delta_high": d_high.get(domain),
            }

    # Comparison table with Paper 8.75
    p875_shifts = {"M01": 0.1528, "N03": 0.1250}

    summary = {
        "n_valid_runs": len(valid),
        "spl_mode": _md.SPL_MODE,
        "verdicts": {f"r{int(r*100):03d}": all_verdicts[r][0] for r in RADII},
        "h2_verdict": all_verdicts["h2"][0],
        "domain_rows": domain_rows,
        "p875_comparison": {
            domain: {
                "p875_post_shift": p875_shifts.get(domain),
                "p9_pre_shift": domain_rows[domain]["r015"].get("shift"),
            }
            for domain in ["M01", "N03"]
        },
    }

    with open(RESULTS_DIR / "phase1_results.json", "w") as f:
        json.dump({"all_results": results, "analysis": summary}, f, indent=2)

    prompt = f"""You are writing paper9/batch_results_phase1/phase1_summary.md.

EXPERIMENT: Paper 9 Phase 1 — Measurement Validity (Pre-Activation Density).
{len(valid)} valid runs. SPL mode: {_md.SPL_MODE}.
Paired design: single loop_0 per domain×seed, both operators from same state.

DOMAINS: {list(DOMAINS.keys())}
(M01=formal_mathematics expected_density=low, N03=empirical_argumentative expected_density=high,
N_new_1=narrow_empirical expected_density=low, N_new_2=broad_normative expected_density=high)

VERDICTS:
{json.dumps({f"H1_r{int(r*100):03d}": all_verdicts[r][0] for r in RADII}, indent=2)}
H2: {all_verdicts['h2'][0]}

H1 DETAILS (r=0.15):
{json.dumps(all_verdicts[0.15][1], indent=2)}

H2 DETAILS:
{json.dumps(all_verdicts['h2'][1], indent=2)}

DOMAIN RESULTS (r=0.15):
{json.dumps({d: domain_rows[d]['r015'] for d in DOMAINS}, indent=2)}

PAPER 8.75 COMPARISON:
- M01 post-activation shift (Paper 8.75): 0.1528
- N03 post-activation shift (Paper 8.75): 0.1250
- M01 pre-activation shift (Phase 1, r=0.15): {domain_rows['M01']['r015'].get('shift')}
- N03 pre-activation shift (Phase 1, r=0.15): {domain_rows['N03']['r015'].get('shift')}

Write the summary in this exact format. Report faithfully. Include negative findings.

---

# Paper 9 Phase 1 — Measurement Validity Summary
**SPL mode: {_md.SPL_MODE}**

## Purpose
[One paragraph: what H1 and H2 test, why needed after Paper 8.75]

## Per-Domain Results (r=0.15, primary)

| Domain | pre_mean ± std | operator_shift | delta_low | delta_high |
|--------|---------------|----------------|-----------|------------|
[Fill from domain_rows for r=0.15]

## Radius Sweep

| Radius | pre_density_stable | no_operator_shift | low_delta_ok | high_delta_ok | H1 verdict |
|--------|-------------------|-------------------|--------------|----------------|------------|
[Fill for r=0.10, 0.15, 0.20]

## H1 Verdict per Radius
[State each H1 verdict explicitly. Note if any criteria fails.]

## H2 Verdict
[State H2 verdict. Is the cross-over interaction absent from pre-activation density?]
[Reproduce per-radius ordering table for M01 vs N03]

## Comparison with Paper 8.75

| Domain | P8.75 post_shift (r=0.15) | Phase 1 pre_shift (r=0.15) | Reduction |
|--------|--------------------------|-----------------------------|-----------|
| M01    | 0.1528                   | ?                           | ?         |
| N03    | 0.1250                   | ?                           | ?         |

[Interpretation: is pre-activation measurement solving the confound?]

## Implication for Phase 2
[H1_CONFIRMED → proceed. H1_NOT_CONFIRMED → Paper 9 ends here. H1_PARTIAL → specify.]
[State explicitly: does Phase 2 proceed?]

## Negative Findings
- Pre_density stability within domain: [report any domains with std >= 0.10]
- Unexpected domain ordering: [N03 vs M01 ordering at pre-activation]
- Cross-over interaction status: [present / absent in pre-activation]
- Limitations: [single loop_0, no test-retest, SPL mode]
"""

    md_text = call_llm(prompt, max_tokens=2000, temperature=0.3)
    header  = (
        "<!-- paper9/batch_results_phase1/phase1_summary -->\n"
        "<!-- Paper 9 Phase 1 — Measurement Validity -->\n\n"
    )
    (RESULTS_DIR / "phase1_summary.md").write_text(header + md_text + "\n")
    print(f"  Written → {RESULTS_DIR}/phase1_summary.md")


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all() -> None:
    _init_clients()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nPaper 9 Phase 1 — Measurement Validity")
    print(f"SPL mode: {_md.SPL_MODE}")
    print(f"Paired design: 4 domains × 3 seeds = 12 runs")
    print()

    all_results = []
    for domain_id in DOMAINS:
        for seed_n in SEEDS:
            result = run_paired(domain_id, seed_n)
            all_results.append(result)

    # Verdicts per radius
    valid = [r for r in all_results if "error" not in r]
    all_verdicts: dict = {}
    for r in RADII:
        all_verdicts[r] = h1_verdict(valid, r)

    h2v, h2d = h2_verdict(valid)
    all_verdicts["h2"] = (h2v, h2d)

    print(f"\n  Results ({len(valid)}/{len(all_results)} valid):")
    for r in RADII:
        v, details = all_verdicts[r]
        print(f"  H1 (r={r:.2f}): {v}")
        print(f"    stable={details['pre_density_stable']}  "
              f"no_shift={details['no_operator_shift']}  "
              f"low_delta_ok={details['low_delta_ok']}  "
              f"high_delta_ok={details['high_delta_ok']}")
    print(f"  H2: {h2v}")

    write_summary(all_results, all_verdicts)
    print("\nPaper 9 Phase 1 complete.")


if __name__ == "__main__":
    run_all()

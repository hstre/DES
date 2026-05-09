"""
des_premium/analysis.py
2×2 model-architecture decomposition.
Loads cheap DES baseline from Paper 8 Arm B.
"""

import json
from pathlib import Path
from statistics import mean

# ── Load cheap DES baselines from Paper 8 Arm B ──────────────────────────────

P8_RESULTS = Path("paper8/batch_results_paper8")

def load_cheap_des_baseline(domains: list, seeds: list) -> list:
    """
    Load Paper 8 Arm B outcomes as cheap DES baseline.
    Arm B = standard DES, deepseek-chat builder, GPT-4o falsifier.
    """
    results = []
    for domain_id in domains:
        for seed_n in seeds:
            p = P8_RESULTS / f"{domain_id}_arm_b_seed{seed_n}" / "outcome.json"
            if not p.exists():
                print(f"  [warn] cheap DES baseline missing: {p}")
                continue
            with open(p) as f:
                d = json.load(f)
            # Normalise to common schema
            results.append({
                "domain_id":       domain_id,
                "seed":            seed_n,
                "condition":       "DES_cheap",
                "loops_completed": d.get("loops_completed"),
                "outcome":         d.get("outcome"),
                "false_proof_detected": _fp_from_p8(d),
                "semantic_duplication_rate_mean": _dup_from_p8_metrics(domain_id, seed_n),
                "novel_claims_mean": _novel_from_p8_metrics(domain_id, seed_n),
                "total_claims_final": _total_from_p8(d),
                "token_cost_proxy": None,
                "source": str(p),
            })
    return results


def _fp_from_p8(d: dict) -> bool | None:
    fi = d.get("false_proof_info")
    return fi.get("false_proof_detected") if fi else None


def _total_from_p8(d: dict) -> int | None:
    claims = d.get("final_claims")
    return len(claims) if claims else None


def _dup_from_p8_metrics(domain_id: str, seed_n: int) -> float | None:
    p = P8_RESULTS / f"{domain_id}_arm_b_seed{seed_n}" / "metrics.json"
    if not p.exists():
        return None
    with open(p) as f:
        metrics = json.load(f)
    rates = [m.get("semantic_duplication_rate") for m in metrics
             if m.get("semantic_duplication_rate") is not None]
    return round(mean(rates), 4) if rates else None


def _novel_from_p8_metrics(domain_id: str, seed_n: int) -> float | None:
    p = P8_RESULTS / f"{domain_id}_arm_b_seed{seed_n}" / "metrics.json"
    if not p.exists():
        return None
    with open(p) as f:
        metrics = json.load(f)
    vals = [m.get("novel_claims") for m in metrics
            if m.get("novel_claims") is not None]
    return round(mean(vals), 2) if vals else None


# ── 2×2 decomposition ─────────────────────────────────────────────────────────

def _agg(results: list, field: str) -> float | None:
    """Mean of field across all results, ignoring None."""
    vals = [r.get(field) for r in results if r.get(field) is not None]
    return round(mean(vals), 4) if vals else None


def _agg_des_depth(results: list) -> float | None:
    vals = [r.get("loops_completed") for r in results
            if r.get("loops_completed") is not None]
    return round(mean(vals), 2) if vals else None


def _agg_cot_depth(results: list) -> float | None:
    vals = [r.get("reasoning_steps") for r in results
            if r.get("reasoning_steps") is not None]
    return round(mean(vals), 2) if vals else None


def _fp_rate(results: list) -> float | None:
    vals = [1 if r.get("false_proof_detected") else 0 for r in results
            if r.get("false_proof_detected") is not None]
    return round(mean(vals), 4) if vals else None


def compute_2x2(
    des_cheap:   list,
    cot_cheap:   list,
    des_premium: list,
    cot_premium: list,
    domains:     list,
) -> dict:
    """
    Compute 2×2 decomposition across all conditions.
    Primary metric: semantic_duplication_rate (lower = better for DES).
    Secondary: depth, novel_claims_mean, false_proof_rate (M01).
    """
    # Filter M01 for false_proof_rate
    m01_dc  = [r for r in des_cheap   if r["domain_id"] == "M01"]
    m01_cc  = [r for r in cot_cheap   if r["domain_id"] == "M01"]
    m01_dp  = [r for r in des_premium if r["domain_id"] == "M01"]
    m01_cp  = [r for r in cot_premium if r["domain_id"] == "M01"]

    cells = {
        "DES_cheap":   {"depth": _agg_des_depth(des_cheap),
                        "dup_rate": _agg(des_cheap, "semantic_duplication_rate_mean"),
                        "novel_claims": _agg(des_cheap, "novel_claims_mean"),
                        "false_proof_rate": _fp_rate(m01_dc)},
        "DES_premium": {"depth": _agg_des_depth(des_premium),
                        "dup_rate": _agg(des_premium, "semantic_duplication_rate_mean"),
                        "novel_claims": _agg(des_premium, "novel_claims_mean"),
                        "false_proof_rate": _fp_rate(m01_dp)},
        "CoT_cheap":   {"depth": _agg_cot_depth(cot_cheap),
                        "dup_rate": _agg(cot_cheap, "semantic_duplication_rate"),
                        "novel_claims": None,  # single-shot CoT has no loop-level novel metric
                        "false_proof_rate": _fp_rate(m01_cc)},
        "CoT_premium": {"depth": _agg_cot_depth(cot_premium),
                        "dup_rate": _agg(cot_premium, "semantic_duplication_rate"),
                        "novel_claims": None,
                        "false_proof_rate": _fp_rate(m01_cp)},
    }

    def diff(a, b, key):
        va, vb = cells[a].get(key), cells[b].get(key)
        if va is None or vb is None:
            return None
        return round(va - vb, 4)

    # Effects on semantic_duplication_rate (primary)
    # Arch effect = DES_dup - CoT_dup  (negative = DES has less duplication = better)
    arch_cheap   = diff("DES_cheap",   "CoT_cheap",   "dup_rate")
    arch_premium = diff("DES_premium", "CoT_premium", "dup_rate")
    model_des    = diff("DES_premium", "DES_cheap",   "dup_rate")
    model_cot    = diff("CoT_premium", "CoT_cheap",   "dup_rate")
    interaction  = None
    if arch_cheap is not None and arch_premium is not None:
        interaction = round(arch_premium - arch_cheap, 4)

    decomp = {
        "primary_metric":    "semantic_duplication_rate (lower = better for DES)",
        "arch_effect_cheap":   arch_cheap,
        "arch_effect_premium": arch_premium,
        "model_effect_des":    model_des,
        "model_effect_cot":    model_cot,
        "interaction":         interaction,
        "interaction_interpretation": _interpret_interaction(interaction),
    }

    return {"cells": cells, "decomposition": decomp, "domains": domains}


def _interpret_interaction(v: float | None) -> str:
    if v is None:
        return "INDETERMINATE"
    if abs(v) < 0.02:
        return "NEAR_ZERO: architecture and model effects are independent"
    if v < 0:
        return "NEGATIVE: DES advantage on duplication grows at premium tier"
    return "POSITIVE: DES advantage on duplication shrinks at premium tier (CoT narrows gap)"


def write_matrix_md(analysis: dict, out_path: Path) -> None:
    cells = analysis["cells"]
    d     = analysis["decomposition"]

    def fmt(v):
        return str(v) if v is not None else "N/A"

    lines = [
        "# 2×2 Model-Architecture Matrix — Results",
        "",
        "Primary metric: semantic_duplication_rate (mean across runs; lower = less redundancy)",
        "DES depth = loops_completed; CoT depth = reasoning_steps (not directly comparable)",
        "",
        "## Cell results",
        "",
        "| | DES cheap | DES premium | CoT cheap | CoT premium |",
        "|---|---|---|---|---|",
        f"| mean depth | {fmt(cells['DES_cheap']['depth'])} | {fmt(cells['DES_premium']['depth'])} | {fmt(cells['CoT_cheap']['depth'])} | {fmt(cells['CoT_premium']['depth'])} |",
        f"| dup_rate (mean) | {fmt(cells['DES_cheap']['dup_rate'])} | {fmt(cells['DES_premium']['dup_rate'])} | {fmt(cells['CoT_cheap']['dup_rate'])} | {fmt(cells['CoT_premium']['dup_rate'])} |",
        f"| novel_claims (mean) | {fmt(cells['DES_cheap']['novel_claims'])} | {fmt(cells['DES_premium']['novel_claims'])} | N/A | N/A |",
        f"| false_proof_rate (M01) | {fmt(cells['DES_cheap']['false_proof_rate'])} | {fmt(cells['DES_premium']['false_proof_rate'])} | {fmt(cells['CoT_cheap']['false_proof_rate'])} | {fmt(cells['CoT_premium']['false_proof_rate'])} |",
        "",
        "## 2×2 Decomposition (primary metric: dup_rate)",
        "",
        f"arch_effect_cheap   = {fmt(d['arch_effect_cheap'])}  (DES_cheap - CoT_cheap; negative = DES less redundant)",
        f"arch_effect_premium = {fmt(d['arch_effect_premium'])}  (DES_premium - CoT_premium)",
        f"model_effect_des    = {fmt(d['model_effect_des'])}  (DES_premium - DES_cheap)",
        f"model_effect_cot    = {fmt(d['model_effect_cot'])}  (CoT_premium - CoT_cheap)",
        f"interaction         = {fmt(d['interaction'])}  (arch_premium - arch_cheap)",
        "",
        f"**Interaction interpretation**: {d['interaction_interpretation']}",
        "",
        "## Domains included",
        f"{', '.join(analysis['domains'])}",
        "",
        "## Pending",
        "R01/R04/R05: no seeded cheap DES baseline in Papers 4-8 — pending full run.",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))


# ── Phase A+B review-quality metrics (architecture-agnostic) ─────────────────

RESULTS_BASE_PB = Path("des_premium")
DIR_PHASE_A_ONLY = RESULTS_BASE_PB / "batch_results_phase_a_only"
DIR_PHASE_A_B    = RESULTS_BASE_PB / "batch_results_des_phase_a_b"
DIR_COT_PREMIUM  = RESULTS_BASE_PB / "batch_results_cot_premium_pb"


def load_judge_scores(results_dir: Path, domains: list, seeds: list) -> list[dict]:
    """Load judge_eval.json from all domain/seed directories."""
    records = []
    for domain_id in domains:
        for seed_n in seeds:
            run_dir  = results_dir / f"{domain_id}_seed{seed_n}"
            judge_p  = run_dir / "judge_eval.json"
            outcome_p = run_dir / "outcome.json"
            if not judge_p.exists():
                continue
            with open(judge_p) as f:
                je = json.load(f)
            outcome = {}
            if outcome_p.exists():
                with open(outcome_p) as f:
                    outcome = json.load(f)
            scores = je.get("scores", {})
            records.append({
                "results_dir":           str(results_dir.name),
                "domain_id":             domain_id,
                "seed":                  seed_n,
                "condition":             outcome.get("condition", str(results_dir.name)),
                "phase_a_termination":   outcome.get("outcome"),
                "synthesis_quality":     scores.get("synthesis_quality"),
                "branch_preservation":   scores.get("branch_preservation"),
                "gap_acknowledgment":    scores.get("gap_acknowledgment"),
                "calibration":           scores.get("calibration"),
                "false_proof_avoidance": scores.get("false_proof_avoidance"),
                "judge_model":           je.get("judge_model"),
                "judge_parse_error":     scores.get("parse_error", False),
            })
    return records


def _mean_metric(records: list[dict], metric: str) -> float | None:
    vals = [r[metric] for r in records if r.get(metric) is not None]
    return round(mean(vals), 3) if vals else None


def compute_phase_b_analysis(domains: list, seeds: list) -> dict:
    """
    Load judge scores from all three condition directories and compute
    per-condition means and H1–H4 effect estimates.
    """
    a_only_records  = load_judge_scores(DIR_PHASE_A_ONLY, domains, seeds)
    a_b_records     = load_judge_scores(DIR_PHASE_A_B,    domains, seeds)
    cot_records     = load_judge_scores(DIR_COT_PREMIUM,  domains, seeds)

    metrics = ["synthesis_quality", "branch_preservation", "gap_acknowledgment", "calibration"]

    def cell_means(records: list[dict]) -> dict:
        return {m: _mean_metric(records, m) for m in metrics}

    cells = {
        "DES_PHASE_A_ONLY": cell_means(a_only_records),
        "DES_PHASE_A_B":    cell_means(a_b_records),
        "COT_PREMIUM":      cell_means(cot_records),
    }

    # H1: Phase A+B > Phase A alone (synthesis_quality)
    h1_delta = _safe_diff(
        cells["DES_PHASE_A_B"]["synthesis_quality"],
        cells["DES_PHASE_A_ONLY"]["synthesis_quality"],
    )

    # H2: Phase A+B >= COT_PREMIUM (synthesis_quality) and A+B > COT on branch_preservation
    h2_sq_delta = _safe_diff(
        cells["DES_PHASE_A_B"]["synthesis_quality"],
        cells["COT_PREMIUM"]["synthesis_quality"],
    )
    h2_bp_delta = _safe_diff(
        cells["DES_PHASE_A_B"]["branch_preservation"],
        cells["COT_PREMIUM"]["branch_preservation"],
    )

    # H3: Phase B value-add by termination type
    premature_terms = {"SEMANTIC_DUPLICATION", "MAX_LOOPS_REACHED"}
    a_only_premature = [r for r in a_only_records if r.get("phase_a_termination") in premature_terms]
    a_b_premature    = [r for r in a_b_records    if r.get("phase_a_termination") in premature_terms]
    a_only_complete  = [r for r in a_only_records if r.get("phase_a_termination") == "LOOP_COMPLETE"]
    a_b_complete     = [r for r in a_b_records    if r.get("phase_a_termination") == "LOOP_COMPLETE"]

    h3_premature_delta = _safe_diff(
        _mean_metric(a_b_premature,   "synthesis_quality"),
        _mean_metric(a_only_premature, "synthesis_quality"),
    )
    h3_complete_delta = _safe_diff(
        _mean_metric(a_b_complete,    "synthesis_quality"),
        _mean_metric(a_only_complete,  "synthesis_quality"),
    )

    # False-proof avoidance (M01 only)
    def fp_rate(records):
        m01 = [r for r in records if r.get("domain_id") == "M01"
               and r.get("false_proof_avoidance") is not None]
        if not m01:
            return None
        return round(mean([r["false_proof_avoidance"] for r in m01]), 3)

    fp_rates = {
        "DES_PHASE_A_ONLY": fp_rate(a_only_records),
        "DES_PHASE_A_B":    fp_rate(a_b_records),
        "COT_PREMIUM":      fp_rate(cot_records),
    }

    return {
        "cells":   cells,
        "effects": {
            "H1_phase_b_value_sq":            h1_delta,
            "H2_sq_delta_vs_cot":             h2_sq_delta,
            "H2_bp_delta_vs_cot":             h2_bp_delta,
            "H3_premature_sq_delta":          h3_premature_delta,
            "H3_complete_sq_delta":           h3_complete_delta,
        },
        "false_proof_rates_M01": fp_rates,
        "n_records": {
            "DES_PHASE_A_ONLY": len(a_only_records),
            "DES_PHASE_A_B":    len(a_b_records),
            "COT_PREMIUM":      len(cot_records),
        },
        "domains": domains,
        "seeds":   seeds,
    }


def _safe_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return round(a - b, 3)


def write_phase_b_summary_md(analysis: dict, out_path: Path) -> None:
    cells   = analysis["cells"]
    effects = analysis["effects"]
    fp      = analysis["false_proof_rates_M01"]
    n       = analysis["n_records"]

    def fmt(v):
        return str(v) if v is not None else "N/A"

    metrics = ["synthesis_quality", "branch_preservation", "gap_acknowledgment", "calibration"]
    metric_labels = {
        "synthesis_quality":   "Synthesis quality (1–5)",
        "branch_preservation": "Branch preservation (1–5)",
        "gap_acknowledgment":  "Gap acknowledgment (1–5)",
        "calibration":         "Calibration (1–5)",
    }

    rows = []
    for m in metrics:
        row = f"| {metric_labels[m]} "
        for cond in ["DES_PHASE_A_ONLY", "DES_PHASE_A_B", "COT_PREMIUM"]:
            row += f"| {fmt(cells[cond].get(m))} "
        rows.append(row + "|")

    lines = [
        "# DES Phase A+B — Pilot Results Summary",
        "",
        f"Domains: {', '.join(analysis['domains'])} | "
        f"Seeds: {', '.join(str(s) for s in analysis['seeds'])}",
        "",
        "## Judge scores (mean across domain/seed combinations)",
        "",
        f"| Metric | DES_PHASE_A_ONLY (n={n['DES_PHASE_A_ONLY']}) "
        f"| DES_PHASE_A_B (n={n['DES_PHASE_A_B']}) "
        f"| COT_PREMIUM (n={n['COT_PREMIUM']}) |",
        "|---|---|---|---|",
    ] + rows + [
        f"| False-proof avoidance (M01) "
        f"| {fmt(fp['DES_PHASE_A_ONLY'])} "
        f"| {fmt(fp['DES_PHASE_A_B'])} "
        f"| {fmt(fp['COT_PREMIUM'])} |",
        "",
        "## Hypothesis results",
        "",
        f"**H1** (Phase B value): Δsynthesis_quality(A+B − A_only) = {fmt(effects['H1_phase_b_value_sq'])}",
        f"**H2** (vs CoT): Δsynthesis_quality(A+B − CoT) = {fmt(effects['H2_sq_delta_vs_cot'])} | "
        f"Δbranch_preservation = {fmt(effects['H2_bp_delta_vs_cot'])}",
        f"**H3** (termination effect): Δsq (premature) = {fmt(effects['H3_premature_sq_delta'])} | "
        f"Δsq (LOOP_COMPLETE) = {fmt(effects['H3_complete_sq_delta'])}",
        "",
        "## Interpretation",
        "",
        _interpret_h1(effects["H1_phase_b_value_sq"]),
        _interpret_h2(effects["H2_sq_delta_vs_cot"], effects["H2_bp_delta_vs_cot"]),
        _interpret_h3(effects["H3_premature_sq_delta"], effects["H3_complete_sq_delta"]),
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def _interpret_h1(delta: float | None) -> str:
    if delta is None:
        return "H1: INDETERMINATE (insufficient data)"
    if delta > 0.3:
        return f"H1: CONFIRMED — Phase B adds +{delta} synthesis quality over Phase A alone."
    if delta > 0:
        return f"H1: WEAK — Phase B adds +{delta} synthesis quality (small effect)."
    return f"H1: REJECTED — Phase B does not improve synthesis quality ({delta:+.3f})."


def _interpret_h2(sq: float | None, bp: float | None) -> str:
    if sq is None or bp is None:
        return "H2: INDETERMINATE (insufficient data)"
    if sq >= -0.1 and bp > 0.3:
        return (
            f"H2: CONFIRMED — A+B matches CoT on synthesis quality ({sq:+.3f}) "
            f"and exceeds it on branch preservation ({bp:+.3f})."
        )
    if sq < -0.5:
        return f"H2: REJECTED — CoT outperforms A+B on synthesis quality by {-sq:.3f}."
    return f"H2: MIXED — synthesis_quality Δ={sq:+.3f}, branch_preservation Δ={bp:+.3f}."


def _interpret_h3(premature: float | None, complete: float | None) -> str:
    if premature is None or complete is None:
        return "H3: INDETERMINATE (insufficient termination-type data)"
    if premature > complete + 0.3:
        return (
            f"H3: CONFIRMED — Phase B adds more for premature terminations "
            f"(Δ={premature:+.3f}) than for LOOP_COMPLETE (Δ={complete:+.3f})."
        )
    return (
        f"H3: NOT CONFIRMED — premature Δ={premature:+.3f} "
        f"vs LOOP_COMPLETE Δ={complete:+.3f} (difference not substantial)."
    )

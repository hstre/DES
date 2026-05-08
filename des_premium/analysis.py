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

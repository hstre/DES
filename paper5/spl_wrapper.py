"""
paper5/spl_wrapper.py
SPL integration for Paper 5 v0.5 semantic attractor detection.
Wraps existing SPL API. Does not modify DES or SPL internals.
WP2 (Rentschler 2026).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp_backend import SPLNLPBackend
from spl import compute_jsd, compute_h_norm  # noqa: F401 (re-exported)

_spl = None


def get_spl() -> SPLNLPBackend:
    global _spl
    if _spl is None:
        _spl = SPLNLPBackend(model_name="all-MiniLM-L6-v2", builder_origin="alpha")
    return _spl


def project(text: str) -> dict:
    """Project text into Π. Returns P_r distribution dict. WP2 §3.3."""
    return get_spl().project_text(text).P_r


def centroid(projections: list) -> dict:
    """
    Arithmetic mean of P_r distributions in Π.
    Global simplex embedding: union of all keys, zero-padded.
    WP2 §3.5.5.
    """
    if not projections:
        return {}
    all_keys: set = set()
    for p in projections:
        all_keys.update(p.keys())
    c = {k: sum(p.get(k, 0.0) for p in projections) / len(projections)
         for k in all_keys}
    total = sum(c.values())
    if total > 0:
        c = {k: v / total for k, v in c.items()}
    return c


def distance(proj_a: dict, proj_b: dict) -> float:
    """Geometric distance in (Π, √JSD). WP2 §3.4.3."""
    return math.sqrt(compute_jsd(proj_a, proj_b))


def semantic_similarity(proj_a: dict, proj_b: dict) -> float:
    """1 − distance(a, b). Diagnostic only — not used in main loop."""
    return max(0.0, 1.0 - distance(proj_a, proj_b))


def epistemic_curvature(projections: list, edges: list) -> float:
    """
    K(G) = 1/|E| Σ_{(i,j)∈E} JSD(P_i, P_j).
    WP2 §3.6.3.
    """
    if not edges or len(projections) < 2:
        return 0.0
    valid = [(i, j) for i, j in edges
             if i < len(projections) and j < len(projections)]
    if not valid:
        return 0.0
    return sum(compute_jsd(projections[i], projections[j])
               for i, j in valid) / len(valid)


def detect_attractor_in_claims(
    state: dict,
    next_question: str,
    epsilon: float = 0.25,
    k_threshold: float = 0.55,
) -> tuple:
    """
    Claim-level attractor detection in Π.
    Called AFTER a DES run, BEFORE the next loop starts.

    v0.5 insight: attractors form within DES runs (claim level),
    not between runs. Loop-level question centroids are too late.

    Trigger 1 — K(G) > k_threshold: high epistemic curvature.
    Trigger 2 — √JSD(π(next_q), centroid(claims)) < ε: next question
                would land in already-covered semantic space.

    Returns (detected, reason, context).
    """
    claims = state.get("claims", {})
    if len(claims) < 3:
        return False, "", {}

    claim_projections = []
    for c in claims.values():
        text = (f"{c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')}").strip()
        if text:
            claim_projections.append(project(text))

    if len(claim_projections) < 3:
        return False, "", {}

    claim_c = centroid(claim_projections)
    edges = [(i, i + 1) for i in range(len(claim_projections) - 1)]
    k = epistemic_curvature(claim_projections, edges)

    if k > k_threshold:
        next_proj = project(next_question)
        return True, f"claim_curvature:{k:.3f}>{k_threshold}", {
            "claim_centroid": claim_c,
            "curvature": k,
            "k_threshold": k_threshold,
            "next_projection": next_proj,
            "claim_count": len(claim_projections),
        }

    next_proj = project(next_question)
    dist = distance(next_proj, claim_c)

    if dist < epsilon:
        return True, f"claim_proximity:{dist:.3f}<{epsilon}", {
            "claim_centroid": claim_c,
            "distance": dist,
            "epsilon": epsilon,
            "next_projection": next_proj,
            "claim_count": len(claim_projections),
        }

    return False, "", {}


def select_escape_vector(
    candidates: list,
    attractor_centroid: dict,
    state: dict,
    loop0_projection: dict = None,
    alpha: float = 0.6,
    beta: float = 0.3,
    gamma: float = 0.1,
) -> tuple:
    """
    Select candidate maximizing escape from attractor.
    Score = α·√JSD(π(c), μ) + β·novelty(c) − γ·drift(c)
    WP2 §3.5.2.
    """
    if not candidates:
        return "", {}

    claims = state.get("claims", {})
    existing_terms: set = set()
    for c in claims.values():
        for f in ("subject", "predicate", "object"):
            existing_terms.update(c.get(f, "").lower().split())
    stop = {
        "the", "a", "an", "is", "are", "of", "in", "to", "for", "and", "or",
        "not", "with", "by", "that", "this", "it", "does", "do", "can", "be",
    }
    existing_terms -= stop
    baseline = loop0_projection if loop0_projection else attractor_centroid

    scored = []
    for cand in candidates:
        cand_proj = project(cand)
        escape_dist = distance(cand_proj, attractor_centroid)
        cand_terms = set(cand.lower().split()) - stop
        overlap = len(cand_terms & existing_terms) / max(len(cand_terms), 1)
        novelty = 1.0 - overlap
        drift = distance(cand_proj, baseline)
        score = alpha * escape_dist + beta * novelty - gamma * drift
        scored.append((score, cand, escape_dist, novelty, drift))

    scored.sort(reverse=True)
    best_score, best_cand, best_dist, best_nov, best_drift = scored[0]

    return best_cand, {
        "escape_distance": best_dist,
        "novelty_estimate": best_nov,
        "drift_risk": best_drift,
        "composite_score": best_score,
        "all_scores": [(round(s[0], 3), s[1][:60]) for s in scored],
    }


def compute_claim_metrics(state: dict) -> dict:
    """
    Compute SPL metrics for the current ClaimGraph.
    Returns claim_centroid, claim_curvature, claim_count, claim_projections.
    """
    claims = state.get("claims", {})
    projs = []
    for c in claims.values():
        text = (f"{c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')}").strip()
        if text:
            projs.append(project(text))
    if len(projs) < 2:
        return {"claim_centroid": {}, "claim_curvature": 0.0,
                "claim_count": len(projs), "claim_projections": projs}
    claim_c = centroid(projs)
    edges = [(i, i + 1) for i in range(len(projs) - 1)]
    k = epistemic_curvature(projs, edges)
    return {"claim_centroid": claim_c, "claim_curvature": k,
            "claim_count": len(projs), "claim_projections": projs}


def check_false_escape(perturbation_log: list, loop_metrics: list = None) -> bool:
    """
    FALSE_ESCAPE: 3 consecutive admitted SPL events with high escape
    distance but zero novel claims. WP2 §3.4.5.
    """
    spl_admitted = [
        e for e in perturbation_log
        if e.get("admitted")
        and ("claim_curvature" in e.get("trigger", "")
             or "claim_proximity" in e.get("trigger", ""))
    ]
    if len(spl_admitted) < 3:
        return False
    last3 = spl_admitted[-3:]
    high_dist = all(e.get("escape_distance", 0) > 0.40 for e in last3)
    zero_novel = all(e.get("novelty_produced_next_loop", 1) == 0 for e in last3)
    return high_dist and zero_novel

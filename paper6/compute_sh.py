"""
paper6/compute_sh.py
Phase 1: Retrograde SH computation from existing P4/P5 state files.
Phase 2: Post-loop-0 SH computation for new domains.
WP2 (Rentschler 2026).
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nlp_backend import SPLNLPBackend
from spl import compute_jsd

_spl = None


def get_spl() -> SPLNLPBackend:
    global _spl
    if _spl is None:
        _spl = SPLNLPBackend(model_name="all-MiniLM-L6-v2", builder_origin="alpha")
    return _spl


def _project_claims(claims_dict: dict) -> list:
    """Project sealed claims into Π. Returns list of P_r dicts."""
    spl = get_spl()
    sealed = [c for c in claims_dict.values() if c.get("sealed")]
    projections = []
    for c in sealed:
        text = (f"{c.get('subject', '')} {c.get('predicate', '')} "
                f"{c.get('object', '')}").strip()
        if text:
            projections.append(spl.project_text(text).P_r)
    return projections


def _compute_centroid(projections: list) -> dict:
    all_keys: set = set()
    for p in projections:
        all_keys.update(p.keys())
    c = {k: sum(p.get(k, 0.0) for p in projections) / len(projections)
         for k in all_keys}
    total = sum(c.values())
    if total > 0:
        c = {k: v / total for k, v in c.items()}
    return c


def compute_semantic_headroom(state_file: str) -> dict:
    """
    Compute SH from a completed DES state file (loop_000_state.json).
    SH = mean(√JSD(π(cᵢ), centroid(claims)))
    Returns SH, SH_norm (exploratory), SH_entropy, and diagnostics.
    """
    with open(state_file) as f:
        state = json.load(f)

    claims = state.get("claims", {})
    sealed_count = sum(1 for c in claims.values() if c.get("sealed"))

    if sealed_count < 3:
        return {
            "sh": None,
            "reason": "too_few_sealed_claims",
            "n_claims": sealed_count,
        }

    projections = _project_claims(claims)
    if len(projections) < 3:
        return {"sh": None, "reason": "too_few_projectable_claims",
                "n_claims": len(projections)}

    centroid = _compute_centroid(projections)
    distances = [math.sqrt(compute_jsd(p, centroid)) for p in projections]
    sh = sum(distances) / len(distances)

    # SH_norm: size-adjusted proxy (exploratory — log2 scaling, not theoretically derived)
    sh_norm = sh * math.log2(max(len(projections), 2))

    # SH_entropy: normalized entropy of centroid distribution
    # High entropy = claims collectively span many relation types
    centroid_h = -sum(v * math.log2(v) for v in centroid.values() if v > 1e-12)
    n_active = len([v for v in centroid.values() if v > 1e-12])
    centroid_h_norm = centroid_h / math.log2(n_active) if n_active > 1 else 0.0

    return {
        "sh": round(sh, 4),
        "sh_norm": round(sh_norm, 4),
        "sh_entropy": round(centroid_h_norm, 4),
        "n_claims": len(projections),
        "min_dist": round(min(distances), 4),
        "max_dist": round(max(distances), 4),
        "centroid_entropy_raw": round(centroid_h, 4),
        "centroid": centroid,
    }


def compute_sh_from_projections(projections: list) -> dict:
    """Compute SH from pre-computed projection list (Phase 2 pre-run probe)."""
    if len(projections) < 3:
        return {"sh": None, "reason": "too_few_projections", "n_claims": len(projections)}

    centroid = _compute_centroid(projections)
    distances = [math.sqrt(compute_jsd(p, centroid)) for p in projections]
    sh = sum(distances) / len(distances)
    sh_norm = sh * math.log2(max(len(projections), 2))

    centroid_h = -sum(v * math.log2(v) for v in centroid.values() if v > 1e-12)
    n_active = len([v for v in centroid.values() if v > 1e-12])
    centroid_h_norm = centroid_h / math.log2(n_active) if n_active > 1 else 0.0

    return {
        "sh": round(sh, 4),
        "sh_norm": round(sh_norm, 4),
        "sh_entropy": round(centroid_h_norm, 4),
        "n_claims": len(projections),
        "min_dist": round(min(distances), 4),
        "max_dist": round(max(distances), 4),
        "centroid_entropy_raw": round(centroid_h, 4),
    }

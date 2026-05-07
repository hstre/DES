"""
paper9/measure_density.py
Pre-activation and post-activation density measurement.
Radius sweep: r in {0.10, 0.15, 0.20}.
SPL validity flag logged per run.
"""

import json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Lazy SPL initialization: spl_wrapper requires model weights loaded by _init_clients.
# Do not import at module level — check at first use instead.
SPL_MODE = None   # resolved on first compute_density call

def _project_fallback(text):
    words = set(text.lower().split())
    stop = {"the","a","an","is","are","of","in","to","for","and","or"}
    words -= stop
    all_keys = list(words)[:20]
    total = max(len(all_keys), 1)
    return {k: 1.0/total for k in all_keys}

def _distance_fallback(a, b):
    keys = set(a) | set(b)
    m = sum(0.5*(a.get(k,0)+b.get(k,0)) for k in keys)
    if m == 0:
        return 0.0
    jsd = sum(
        a.get(k,0)*math.log2(a.get(k,0)/m) if a.get(k,0) > 0 else 0
        for k in keys
    ) * 0.5 + sum(
        b.get(k,0)*math.log2(b.get(k,0)/m) if b.get(k,0) > 0 else 0
        for k in keys
    ) * 0.5
    return max(0.0, math.sqrt(abs(jsd)))

_project_fn  = None
_distance_fn = None

def _ensure_spl():
    global SPL_MODE, _project_fn, _distance_fn
    if SPL_MODE is not None:
        return
    try:
        from spl_wrapper import project as _p, distance as _d
        _project_fn  = _p
        _distance_fn = _d
        SPL_MODE = "spl_native"
    except ImportError:
        _project_fn  = _project_fallback
        _distance_fn = _distance_fallback
        SPL_MODE = "spl_fallback"


def compute_density(question: str, claims: dict, r: float) -> float:
    """
    density(q, r) = count(c : sqrt_JSD(pi(c), pi(q)) < r) / n_claims
    Normalized by total sealed claim count.
    """
    _ensure_spl()
    sealed = [c for c in claims.values()
              if c.get("sealed") or c.get("status") in ("supported","established")]
    if not sealed:
        return 0.0
    q_proj = _project_fn(question)
    nearby = 0
    for c in sealed:
        text = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()
        if text:
            try:
                d = _distance_fn(_project_fn(text), q_proj)
                if d < r:
                    nearby += 1
            except Exception:
                continue
    return round(nearby / len(sealed), 4)


def measure_both_points(state_pre: dict, state_post: dict,
                        next_q_candidate: str,
                        radii: list = [0.10, 0.15, 0.20]) -> dict:
    """
    Measure density at both measurement points for all radii.

    state_pre:  loop_0 state BEFORE operator selection
    state_post: loop_0 state AFTER operator has fired (if available)
    next_q_candidate: the question that would be asked next
    """
    _ensure_spl()
    result = {"spl_mode": SPL_MODE, "question": next_q_candidate[:80]}

    for r in radii:
        key = f"r{int(r*100):03d}"
        result[f"pre_{key}"]  = compute_density(next_q_candidate,
                                                  state_pre.get("claims",{}), r)
        result[f"post_{key}"] = compute_density(next_q_candidate,
                                                  state_post.get("claims",{}), r)
    return result

"""
spl.py — Pure math functions for the Alexandria Semantic Projection Layer.
WP2 (Rentschler 2026). Do not modify after initial creation.
"""

import math


def compute_jsd(p: dict, q: dict) -> float:
    """
    Jensen-Shannon Divergence between two distributions.
    Using log base 2: JSD ∈ [0, 1].
    """
    keys = set(p) | set(q)
    p_v = [p.get(k, 0.0) for k in keys]
    q_v = [q.get(k, 0.0) for k in keys]
    sp, sq = sum(p_v), sum(q_v)
    if sp == 0 and sq == 0:
        return 0.0
    if sp == 0 or sq == 0:
        return 1.0
    p_v = [x / sp for x in p_v]
    q_v = [x / sq for x in q_v]
    m_v = [(p_v[i] + q_v[i]) / 2 for i in range(len(p_v))]

    def kl(a, b):
        return sum(ai * math.log2(ai / bi)
                   for ai, bi in zip(a, b) if ai > 1e-12 and bi > 1e-12)

    jsd = (kl(p_v, m_v) + kl(q_v, m_v)) / 2
    return max(0.0, min(1.0, jsd))


def compute_h_norm(p: dict) -> float:
    """
    Normalized Shannon entropy H(P) / log2(|support|).
    Returns value in [0, 1].
    """
    vals = [v for v in p.values() if v > 1e-12]
    if not vals:
        return 0.0
    h = -sum(v * math.log2(v) for v in vals)
    n = len(p)
    max_h = math.log2(n) if n > 1 else 1.0
    return min(1.0, h / max_h) if max_h > 0 else 0.0

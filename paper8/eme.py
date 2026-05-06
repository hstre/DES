"""
paper8/eme.py
Epistemic Map Entropy: cluster-based claim diversity metric.
WP2 (Rentschler 2026).
"""

import math
try:
    from spl_wrapper import project, distance
except ImportError:
    project = distance = None


def compute_eme(run_results: list, min_cluster_size: int = 2) -> dict:
    if project is None:
        return {"eme_score": None, "reason": "spl_unavailable"}

    all_claims = []
    for run in run_results:
        for c in run.get("final_claims", {}).values():
            if c.get("sealed"):
                text = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()
                if text:
                    all_claims.append({
                        "projection": project(text),
                        "confidence": c.get("confidence", 0.5),
                    })

    if len(all_claims) < 3:
        return {"eme_score": 0.0, "cluster_count": 0, "total_claims": len(all_claims)}

    THRESHOLD = 0.15
    clusters, assigned = [], set()
    for i in range(len(all_claims)):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)
        for j in range(i + 1, len(all_claims)):
            if j in assigned:
                continue
            if distance(all_claims[i]["projection"], all_claims[j]["projection"]) < THRESHOLD:
                cluster.append(j)
                assigned.add(j)
        clusters.append(cluster)

    valid = [c for c in clusters if len(c) >= min_cluster_size]
    score = sum(
        sum(all_claims[i]["confidence"] for i in c) / len(c)
        for c in valid
    )
    return {
        "eme_score": round(score, 4),
        "cluster_count": len(valid),
        "total_claims": len(all_claims),
    }

"""
paper9_branch2/merge.py
Pre-registered merge: first two admitted branches by admission order.
H3: new_cluster_rate after post-merge DES loop.
"""

import json
from pathlib import Path

from paper8.eme import compute_eme


def merge_branch_states(branch_results: list, merge_after: int | None) -> dict | None:
    """
    Pre-registered selection: first two admitted branches with
    loops_completed >= merge_after.  NOT sorted by EME — admission order only.

    Returns merged DES state dict (union of claims from both branches), or None.
    """
    if merge_after is None:
        return None

    mature = [b for b in branch_results if b.get("loops_completed", 0) >= merge_after]
    if len(mature) < 2:
        return None

    first_two = mature[:2]

    # Load full branch states from branch_state.json
    states = []
    for b in first_two:
        branch_dir = b.get("_branch_dir")
        loaded = False
        if branch_dir:
            state_file = Path(branch_dir) / "branch_state.json"
            if state_file.exists():
                with open(state_file) as f:
                    states.append(json.load(f))
                loaded = True
        if not loaded:
            states.append({"claims": b.get("final_claims", {})})

    # Use first branch's state as base; merge claims from both
    merged_state = dict(states[0]) if states else {}
    merged_claims = {}
    for st in states:
        merged_claims.update(st.get("claims", {}))

    merged_state["claims"] = merged_claims
    merged_state["_merged_from"] = [b["branch_id"] for b in first_two]
    merged_state["_selection_rule"] = "first_two_admitted"
    return merged_state


def compute_h3(pre_merge_claims: dict, post_merge_claims: dict) -> dict:
    """
    H3: new clusters emerging after post-merge DES loop indicate genuine
    recombination (not just claim accumulation).

    new_cluster_rate = (post_clusters - pre_clusters) / pre_clusters
    """
    pre_eme  = compute_eme([{"final_claims": pre_merge_claims}])
    post_eme = compute_eme([{"final_claims": post_merge_claims}])
    pre_n    = pre_eme.get("cluster_count", 0)
    post_n   = post_eme.get("cluster_count", 0)
    rate     = (post_n - pre_n) / pre_n if pre_n > 0 else 0.0
    return {
        "pre_merge_clusters":  pre_n,
        "post_merge_clusters": post_n,
        "new_cluster_rate":    round(rate, 4),
        "h3_new_clusters":     max(0, post_n - pre_n),
        "h3_verdict":          "H3_CONFIRMED" if post_n > pre_n else "H3_REJECTED",
    }

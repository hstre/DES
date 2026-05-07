# DES Paper 9 Branch 2 — Design Memo

# Delayed Merge: How long must operator branches remain separate

# before productive recombination?

# Version: 0.2 — three methodological fixes: H2 non-monotonic, pre-registered selection, post-merge loop for H3

# Date: 7. Mai 2026

-----

## Foundation

Paper 9 Branch 1 established:

> Branch preservation increases EME because it allows operator-specific
> trajectories to stabilize before recombination pressure is applied.

Architecture A (merge immediately): EME 3.03 ≈ baseline 2.82
Architecture B (preserve forever): EME 12.03 — 4.27× baseline

The mechanism is attractor isolation: each operator direction forms its
own stable attractor before any recombination occurs. Early merge
collapses divergent directions before they stabilize.

Branch 2 asks: is preserve-forever the optimum, or is there a
productive merge horizon?

-----

## Core Question

How long must operator branches remain separate before recombination
produces higher EME than either preserve-forever or early merge?

-----

## Three Merge Conditions

```python
MERGE_CONDITIONS = {
    "B0": {"merge_after": 0, "label": "immediate merge (Arch A baseline)"},
    "B2": {"merge_after": 2, "label": "merge after 2 branch loops"},
    "B4": {"merge_after": 4, "label": "merge after 4 branch loops"},
    "B_inf": {"merge_after": None, "label": "no merge / preserve forever (Arch B baseline)"},
}
```

B0 and B_inf are already measured from Branch 1.
B2 and B4 are the new conditions.

-----

## Merge Mechanism

After N loops, select the first two admitted mature branches (pre-registered admission order) and merge their
ClaimGraphs as joint input to the next DES loop.

```python
def merge_branches(branches: list, n_loops: int,
                   merge_after: int) -> dict | None:
    """
    Pre-registered merge selection: FIRST TWO admitted branches.
    Do NOT select by branch_eme -- that leaks outcome information
    into selection and measures selection+merge, not merge horizon.

    Selection rule (pre-registered):
    - Take the first two admitted branches in order of admission
    - If fewer than 2 mature branches: do not merge yet

    After merge: run at least 1 additional DES loop to test recombination.
    """
    if merge_after is None:
        return None  # preserve forever

    # Pre-registered: first two admitted branches (not top by EME)
    mature = [b for b in branches if b["loops_completed"] >= merge_after]
    if len(mature) < 2:
        return None
    # Take first two by admission order -- NOT by EME score
    first_two = mature[:2]

    # Merge ClaimGraphs: union of sealed claims
    merged_claims = {}
    for b in first_two:
        merged_claims.update(b["final_state"].get("claims", {}))
    return {
        "claims": merged_claims,
        "merged_from": [b["branch_id"] for b in first_two],
        "selection_rule": "first_two_admitted",  # NOT top-by-eme
        "requires_post_merge_loop": True,  # for H3
    }
```

-----

## Hypotheses

### H1 (Optimal Merge Horizon exists)

There exists a merge_after value N* where EME(B_N*) > EME(B_inf).
Productive recombination requires branches to have stabilized their
own attractor first.

### H2 (Non-monotonic optimum)

There exists N* such that:
EME(B0) < EME(B_N*) > EME(B_inf)

Interpretation:

- Too-early merge (B0) destroys branch identity before stabilization
- Too-late merge (B_inf) misses recombination gains from mature branches
- An optimal merge horizon N* exists where stabilized branches combine
  productively

This makes Branch 2 genuinely falsifiable:
If EME(B2) < EME(B_inf) AND EME(B4) < EME(B_inf): no optimum found in tested range
If EME(B2) > EME(B_inf) OR EME(B4) > EME(B_inf): non-monotonic optimum confirmed

### H3 (Recombination creates new clusters)

After merge, at least one additional DES loop is run on the merged state.
New clusters in the post-merge ClaimGraph that were NOT present in
either parent branch indicate genuine recombination.

new_cluster_rate = |clusters(post_merge_loop) - clusters(branch_A ∪ branch_B)|
/ |clusters(branch_A ∪ branch_B)|

IMPORTANT: H3 requires post_merge_loop >= 1.
Measuring claim count of the union alone tests accumulation, not recombination.
Genuine recombination = DES generates claims that neither branch
would have generated independently.

-----

## Domains

M01 and N03 — same as Branch 1 for direct comparison.
Seeds: 101, 202, 303.

-----

## Primary Metric

EME across all conditions.
Secondary: new_cluster_rate after merge, branch_identity_retention
(do merged branches lose their distinct cluster structure?).

-----

## What We Do Not Know

- Whether B2 or B4 will outperform B_inf
- Whether first-two-admitted is the right non-leaky selection criterion
- Whether merged ClaimGraphs are coherent or incoherent
- Whether the stabilization time varies by operator pair
  (Mozart+Kant may need different time than Darwin+Kant)

-----

## Connection to Branch Identity Finding

Paper 9 Branch 1 qualitative analysis showed:

- All 5 branches distinct (different aspects of AGI problem)
- Branches recombinable: scaling limits + architecture selection +
  causal reasoning form a coherent theory together

This suggests that branches stabilize into recombinable identities —
the question is how quickly. If 2 loops is enough for stabilization,
B2 should approach B_inf. If 4 loops is needed, B2 will be weaker.

-----

## Status

Design Memo v0.2. Pre-registered.
GitHub: hstre/DES (branch: paper9-branch2/delayed-merge)

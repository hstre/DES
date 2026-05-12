# DES Implementation Anomaly Audit v0.1
# Focused Report: I1 / I2 / I3

**Date:** 2026-05-10  
**Source:** `des.py` only  
**Extraction method:** static code reading; no design memos, paper references, or summaries used

This document is the standalone focused report for the three candidate implementation
anomalies identified in prior analysis (I1, I2, I3). Content is identical to Section 5
of `output_predicate_audit_code_v0-1.md`, presented here for separate review.

---

## I1 — T4 Parent Sealing Anomaly

**Operator:** T4 (`t4_decompose_claim`)  
**Status:** confirmed  
**Extraction confidence:** high

### Question

Does T4 ever mark an underspecified parent as `status == "supported"` without
sufficient evidence?

### Code

Function `t4_decompose_claim`, lines 773–774:

```python
claim.status = "supported"
claim.sealed = True
```

T4 trigger condition in `select_operation` (line 1003):

```python
if claim.status == "underspecified" or claim.scope == {}:
    return "T4", t4_decompose_claim
```

### Observed behavior

T4 fires when `claim.scope == {}` (the standard trigger path, since initial claims are
generated with `scope={}` by `generate_initial_claim`, line 553) or when
`claim.status == "underspecified"`.

At lines 773–774, the parent claim's status is unconditionally set to `"supported"` and
`sealed = True` immediately after sub-claims are created. There is no LLM call that
evaluates the parent's epistemic status. The only LLM call in T4 is to generate
sub-claim content (`_llm_json(prompt)`, line 729). Neither the LLM call nor any
fallback path evaluates the parent claim's evidence or updates its status based on
epistemic warrant.

A claim with `scope == {}` and prior `status == "hypothesis"` (or "unknown", or any
other status) will be sealed as `status == "supported"` regardless of:
- its current confidence value
- its current evidence_refs content
- whether it has passed through T6 or any other evidence-grounding step

The sub-claims created by T4 receive `status = "unknown"` and do not inherit the
parent's "supported" label.

---

## I2 — T3 B-Claim Fallback Anomaly

**Operator:** T3 (`t3_request_evidence`) via `evaluate_branch_claim`  
**Status:** confirmed  
**Extraction confidence:** high

### Question

Does T3 ever assign `status == "supported"` without successful evidence collection
(e.g., when LLM evaluation fails or is unavailable)?

### Code

Function `evaluate_branch_claim`, lines 470–486:

```python
def evaluate_branch_claim(claim: Claim) -> None:
    """
    Call LLM to update a branch claim's status and confidence from its evidence.
    Falls back to supported+0.85 so T9 can always fire.
    """
    evidence_text = "; ".join(claim.evidence_refs[-2:])
    prompt = CLAIM_UPDATE_PROMPT.format(
        claim=_claim_summary(claim),
        evidence=evidence_text,
    )
    result = _llm_json(prompt)
    if result:
        claim.status = result.get("status", "supported")
        claim.confidence = float(result.get("confidence", 0.85))
    else:
        claim.status = "supported"
        claim.confidence = 0.85
```

Call site in `t3_request_evidence` (line 675–676):

```python
if claim.id.startswith("B"):
    evaluate_branch_claim(claim)
```

### Observed behavior

For B-prefixed claims, `t3_request_evidence` calls `evaluate_branch_claim`. Inside
`evaluate_branch_claim`, `_llm_json(prompt)` is called. `_llm_json` (lines 225–237)
attempts the LLM call twice (initial + retry) and returns `None` if both fail. Failure
conditions include: LLM API errors, JSON parse errors, and any exception caught by the
try/except blocks.

When `_llm_json` returns `None`, the `else` branch executes:

```python
claim.status = "supported"
claim.confidence = 0.85
```

These two assignments are unconditional in the fallback path. The code docstring at
line 473 explicitly states the purpose: "Falls back to supported+0.85 so T9 can always
fire."

Sequence during T3 for B-prefixed claims:
1. `simulate_evidence(claim)` produces a domain-specific confirmation string
2. `claim.evidence_refs.append(simulated)` — the evidence string IS added before evaluate_branch_claim
3. `evaluate_branch_claim(claim)` is called
4. If LLM fails: `claim.status = "supported"`, `claim.confidence = 0.85`

The simulated evidence string is present in `claim.evidence_refs` when
`evaluate_branch_claim` is called. However, the LLM evaluation of that evidence is
what can fail. If it fails, the branch claim is promoted to `supported + 0.85`
unconditionally, regardless of the simulated evidence content.

---

## I3 — T9 Premature Synthesis Anomaly

**Operator:** T9 (`t9_trigger_reframing`)  
**Status:** confirmed  
**Extraction confidence:** high

### Question

Can T9 fire when branches are `status == "supported"` but `sealed == False`?

### Code

`select_operation` lines 1014–1017:

```python
if claim.branch_open:
    branches = [c for c in state.claims.values() if c.parent_id == claim.id]
    if branches and all(c.status == "supported" for c in branches):
        return "T9", t9_trigger_reframing
```

`select_focus_claim` lines 1066–1069:

```python
if claim.branch_open:
    children = [c for c in state.claims.values() if c.parent_id == cid]
    if children and all(c.status == "supported" for c in children):
        t9_ready.append(claim)
```

### Observed behavior

Both `select_operation` and `select_focus_claim` use `c.status == "supported"` as the
T9 readiness criterion. Neither check uses `c.sealed == True`.

A branch claim receives `status = "supported"` from:
- T6, `t6_explore_evidence_path` (line 868): `claim.status = "supported"` — unconditional,
  does NOT set `sealed = True`
- T3's `evaluate_branch_claim` (line 482): `claim.status = result.get("status", "supported")`;
  (line 485): `claim.status = "supported"` — neither path sets `sealed = True`

Branch claims are sealed by T8 (`t8_seal_claim`, line 901: `claim.sealed = True`).

The sequence that produces T9 firing before branches are sealed:
1. T6 fires on branch claim B → `B.status = "supported"`, `B.sealed == False`
2. On the same or next iteration, the parent claim is now T9-ready
   (all children have `status == "supported"`)
3. T9 fires on the parent, creating synthesis claim, setting `parent.sealed = True`
4. In subsequent iterations, T8 fires on B (now status="supported", confidence>0.8),
   setting `B.sealed = True`

This ordering is structurally entailed by the trigger condition using `status` rather
than `sealed`. The synthesis claim is created before branch claims have completed their
full processing path (T7 qualifier refinement may still be pending on branch claims
when T9 fires).

---

## Cross-Anomaly Interaction

I2 and I3 interact: I2's fallback (`claim.status = "supported"` on LLM failure in T3
for B-claims) can satisfy I3's trigger condition. If a B-claim's `evaluate_branch_claim`
call fails during T3, the branch is immediately promoted to `status = "supported"` with
`confidence = 0.85`, which satisfies both the T9 readiness check and the T8 primary
trigger. The branch becomes T9-ready before any T6 or T7 firing occurs on it.

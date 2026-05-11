# DES Composition Derivation Check v0.1

**Date:** 2026-05-11
**Branch:** `theory/composition-derivation-check`
**Predicate baseline (spec-side):** Amendment Plan v1.1 (canonical predicates in task brief)
**Predicate baseline (code-side):** `output_predicate_audit_code_v0-1.md`; `des.py` read directly
**Predecessor work:** Amendment Plan v1.1; Memo v3/v3.1; Comparison Audit v0.1; Policy Typology v0.1

---

## 1. Summary

- All three cascades (T5→T1, T7→T8, T3→T9) are classified as **state-dependent** on both spec-side and code-side. None are strict-derived.
- T7→T8 and T3→T9 show **spec/code divergence in mechanism**: the code-side has an enabling output predicate (T7 confidence boost; T3 I2 fallback) that is absent from the spec-side. Both sides remain state-dependent, but the state conditions differ in kind.
- T5→T1 is **consistent** (aligned) across spec-side and code-side: both require that T5's contradiction check returned True. Code analysis reveals a deterministic sub-path (double LLM failure) where status="contradicted" is guaranteed, but this does not change the overall classification.
- Focus-claim selection (outside `select_operation`) is the structurally weak link across all three cascades. None of the three achieve guaranteed selection of the receiver operator's target claim unless additional graph-state conditions hold.
- The two divergent spec/code classifications (T7→T8 and T3→T9) correspond exactly to the `undocumented_extension` and `spec_silent` findings from `spec_code_discrepancy_matrix_v0-1.md`. The cascade derivability check is sensitive to the same predicate gaps identified in the discrepancy audit.

---

## 2. Method

### Derivability classes (binding, pre-registered)

**Strict-derived:**

```
O_i ⊨ G_j   AND   Σ(A) = T_j for all admissible sets A containing T_j
```

T_i's output logically implies T_j's guard, and the selection policy guarantees T_j is selected over alternatives.

**Guard-derived / Selection-dependent:**

```
O_i ⊨ G_j   BUT   Σ(A) does not guarantee T_j
```

Guard is satisfied by T_i's output, but selection could pick a different admissible operator.

**State-dependent:**

```
(O_i ∧ S_k) ⊨ G_j   for additional state condition S_k
```

Derivable only with additional rest-graph or execution conditions beyond T_i's direct output.

**Not-derived:**

No consistent implication chain exists.

### Predicate application per cascade

| Cascade | Spec-side source | Code-side source |
|---------|-----------------|------------------|
| T5 → T1 | Canonical T5 output; T1 intrinsic | `t5_generate_counter_hypothesis` (lines 780–843); `check_for_contradiction` (lines 404–435); `select_focus_claim` (lines 1053–1077) |
| T7 → T8 | Canonical T7 output; T8 intrinsic+admissibility | `t7_refine_qualifier` (lines 875–896); `select_operation` (lines 1007–1020) |
| T3 → T9 | Canonical T3 output; T9 intrinsic | `t3_request_evidence` (lines 670–685); `evaluate_branch_claim` (lines 470–486); `select_focus_claim` (lines 1053–1077) |

Note on "spec-side": the canonical predicates in the brief mark code-only predicates with `(per code:)` or `(per I2 fallback)`. The spec-side analysis uses only predicates without these markers.

---

## 3. Cascade T5 → T1

### 3.1 Predicates

**T5 output (canonical):**
```
exists C-prefixed counter-claim with parent_id == claim.id
claim.status ∈ {"contradicted", "disputed"}
claim.conflict == True
claim.confidence >= 0.42
```

**T1 intrinsic (canonical):**
```
claim.status == "contradicted"
```

### 3.2 Spec-side implication chain

**Step 1.** T5's output predicate is: `claim.status ∈ {"contradicted", "disputed"}`.

**Step 2.** T1's intrinsic requires: `claim.status == "contradicted"`.

**Step 3.** The implication `O_T5 ⊨ G_T1` fails in the general case. T5's output is a disjunction; T1's guard requires the specific element "contradicted". When T5 produces status="disputed", T1 is not admissible.

**Step 4.** Additional condition required: S_k1 = `claim.status == "contradicted"` (i.e., T5's execution path resolved to the "contradicted" branch). Without S_k1, the cascade does not hold.

**Step 5.** With S_k1: `(O_T5 ∧ S_k1) ⊨ G_T1`. T1's intrinsic is satisfied.

**Step 6.** Selection policy consideration. After T5, the original claim (let's call it P) and the new counter-claim (CC, C-prefixed, parent_id=P.id) are both in `state.claims`. `select_focus_claim` iterates over all unsealed, non-weak claims. P is not sealed (T5 does not seal). CC is newly created, not sealed. Both are in the `regular` pool (neither has branch_open=True). The function returns `regular[0]`, which is the first claim encountered in dict insertion order (Python 3.7+ insertion-order guarantee).

**Step 7.** P was inserted before CC in all cases (CC was just created by T5). In a single-claim graph, P is `regular[0]` and is selected. In a multi-claim graph, an earlier-inserted unsealed claim could be `regular[0]` instead. The cascade's "next iteration on P" assumption requires S_k2 = `P is the first unsealed regular claim in insertion order`.

**Step 8.** With S_k1 ∧ S_k2: `select_operation(P)` evaluates:
- `P.is_synthesis` → False (T5 does not set is_synthesis)
- `P.status == "contradicted"` → True → returns T1

T1 is selected, not preempted. In `select_operation`, T1 check is at line 997, before any other non-bypass check.

**Spec-side classification:** **state-dependent**
- S_k1: T5's contradiction check returned "contradicted" (the disjunction resolves to the required branch)
- S_k2: P is selected as focus claim in the next iteration (insertion-order dependent)

### 3.3 Code-side analysis

**`check_for_contradiction` (lines 404–435)** is the mechanism that determines claim.status after T5. It has three execution paths:

*Path A (LLM succeeds):* Returns `bool(result.get("contradicts", False))`. Outcome is LLM-dependent; non-deterministic. May return True or False.

*Path B (LLM fails; Fallback 1):* Checks whether the counter-claim's predicate contains any negation marker from the tuple `("not", "never", "no ", "cannot", "can't", "doesn't", "does not")` (line 422). Returns True if any marker is found.

*Path C (LLM fails; Fallback 2):* Checks opposing directional pairs (`_OPPOSING_PAIRS`, lines 391–401) across predicate+object fields. Returns True if a pair is detected. Returns False otherwise.

**Critical sub-path (double LLM failure):** When T5's counter-generation LLM call fails, the fallback counter_predicate is set to `"does not " + claim.predicate` (line 810). When `check_for_contradiction` is then called and its own LLM call also fails, Fallback 1 fires. The string `"does not"` IS in `neg_markers` (line 422). Therefore:

```
T5 LLM failure → counter_predicate = "does not " + claim.predicate
check_for_contradiction LLM failure → Fallback 1 → "does not" in neg_markers → True
→ claim.status = "contradicted"  (deterministic)
```

In this sub-path (double LLM failure), S_k1 is satisfied deterministically. The cascade T5→T1 is guaranteed for that sub-path — but it is still state-dependent at the classification level because the general case requires S_k1.

**Focus-claim selection (code-side):** `select_focus_claim` (lines 1053–1077). After T5:
- P: not sealed, not weak, branch_open=False → in `regular`
- CC: not sealed, not weak, branch_open=False → in `regular`
- P was inserted before CC → in a single-claim graph, P is `regular[0]`
- In a multi-claim graph: P may not be `regular[0]` if earlier-inserted claims are still unsealed

Note: CC (counter-claim) has status="unknown", conflict=False, evidence_refs=[]. If CC is selected first, `select_operation(CC)` fires T3 (evidence_refs empty, modality="hypothesis") — not T1. This delays the cascade.

**Code-side classification:** **state-dependent**
- S_k1: `check_for_contradiction` returns True (LLM-dependent, or guaranteed in double-failure sub-path)
- S_k2: P (original claim) is selected as focus in next iteration (insertion-order + graph-topology dependent)

### 3.4 Consistency and rationale

**Consistency: aligned**

Both spec-side and code-side classify T5→T1 as state-dependent. The required S_k conditions are the same: (1) contradiction check → True and (2) original claim selected as focus. Code analysis adds:
- S_k1 is partially deterministic: in the double-LLM-failure sub-path, status="contradicted" is guaranteed. This nuance is not visible at spec level.
- S_k2 is structurally entailed by insertion order (P before CC), but is not guaranteed in multi-claim graphs.

Neither predicate set produces a strict or guard-derived classification.

---

## 4. Cascade T7 → T8

### 4.1 Predicates

**T7 output (canonical):**
```
claim.qualifier != {}
(per code: claim.confidence = min(1.0, claim.confidence + 0.05))
```

**T8 intrinsic (canonical):**
```
claim.status == "supported"
```

**T8 admissibility (canonical):**
```
claim.confidence > 0.8
```

### 4.2 Spec-side implication chain

**Step 1.** T7's spec-side output is: `claim.qualifier != {}`. (The confidence boost is marked `per code` and is absent from the spec-side predicate.)

**Step 2.** T8's guard has two components: (a) intrinsic `claim.status == "supported"` and (b) admissibility `claim.confidence > 0.8`.

**Step 3.** T7's spec output (`qualifier != {}`) does not imply (a) — T7 does not set status. T7's spec output does not imply (b) — T7 spec has no confidence effect.

**Step 4.** Neither component of T8's guard is implied by T7's spec output. The implication `O_T7_spec ⊨ G_T8` fails.

**Step 5.** Required state conditions: S_k1 = `claim.status == "supported"` (must hold before T7 fires); S_k2 = `claim.confidence > 0.8` (must hold after T7 fires — but since spec-side T7 has no confidence effect, this means confidence > 0.8 must hold before T7 fires as well).

**Step 6.** However: if S_k1 ∧ S_k2 hold before T7 fires, then T8_primary (line 1012) would fire on that iteration instead of T7 — because T8_primary appears before T7 in the chain at line 1012, and T7 at line 1010. Wait: examining `select_operation` priority chain:

```
line 1007: T6_primary
line 1010: T7
line 1012: T8_primary
```

T7 (line 1010) fires BEFORE T8_primary (line 1012) in the priority chain. Therefore:

If `qualifier == {}` AND `scope != {}` (T7's intrinsic) AND `status == "supported"` AND `confidence > 0.8` (T8's guard) all hold simultaneously: T7 fires (line 1010) before T8 (line 1012). T8 does not fire on that iteration.

**Step 7.** After T7 fires: `qualifier != {}`. On the NEXT iteration, T7 is no longer admissible (qualifier is set). T8_primary now fires IF status=="supported" AND confidence>0.8 still hold (which they do, since T7 spec does not change status or confidence).

**Step 8.** The spec-side cascade mechanism is: T7 fires (setting qualifier), then "clears itself," and T8 fires next because T8's guard was already satisfied before T7 fired. T7's output (`qualifier != {}`) is causally irrelevant to T8's admissibility. T8 would have fired on the same iteration if T7's intrinsic had not preempted it in the priority chain.

**Step 9.** Formally: `(O_T7_spec ∧ S_k1 ∧ S_k2) ⊨ G_T8` holds, but only because `S_k1 ∧ S_k2 ⊨ G_T8` holds independently. O_T7_spec participates trivially.

**Step 10.** Selection consideration (spec-side): after T7 on the same claim, on the next iteration, `select_focus_claim` returns the same claim if it's the first in `regular`. T8_primary fires because:
- T6_primary: `status != "supported"` guard fails (S_k1 holds) → skip
- T7: qualifier is now set → skip
- T8_primary: `status == "supported" AND confidence > 0.8` → fires

No preemption, given T1–T6_primary all skip (assuming no conflict, has evidence, etc.).

**Spec-side classification:** **state-dependent**
- S_k1: `claim.status == "supported"` (not produced by T7 spec output)
- S_k2: `claim.confidence > 0.8` (not produced by T7 spec output — T7 spec has no confidence effect)
- Note: T7's spec output is causally irrelevant to T8's admissibility. The cascade is a sequential priority-chain artifact, not a predicate-level implication.

### 4.3 Code-side implication chain

**Step 1.** T7's code output is: `claim.qualifier != {}` AND `claim.confidence = min(1.0, claim.confidence + 0.05)` (line 893).

**Step 2.** T8's guard: `claim.status == "supported"` AND `claim.confidence > 0.8`.

**Step 3.** T7's confidence boost (+0.05) NOW participates in satisfying T8's admissibility. Required state conditions:

- S_k1 = `claim.status == "supported"` before T7 (T7 does not set status)
- S_k2 = `0.75 < claim.confidence_pre_T7 ≤ 0.80` — the narrow channel where:
  - `confidence_pre_T7 ≤ 0.80`: T8_primary did NOT fire before T7 (T8_primary requires confidence > 0.8 strict; confidence must be ≤ 0.80 for T8 to not preempt T7)
  - `confidence_pre_T7 > 0.75`: after T7's boost, `confidence_post_T7 = confidence_pre_T7 + 0.05 > 0.80` (satisfying T8's strict admissibility)

**Step 4.** With S_k1 ∧ S_k2: `confidence_pre_T7 ∈ (0.75, 0.80]`. T7 fires (T8 didn't preempt because confidence ≤ 0.80). After T7: `confidence_post_T7 ∈ (0.80, 0.85]`. T8's admissibility `confidence > 0.8` is now satisfied.

**Step 5.** `(O_T7_code ∧ S_k1 ∧ S_k2) ⊨ G_T8`:
- `claim.status == "supported"` (from S_k1)
- `claim.confidence > 0.8` (from O_T7_code confidence boost + S_k2)
- T8's guard satisfied ✓

**Step 6.** Here T7's code output (confidence boost) IS the enabling predicate that pushes confidence across T8's threshold. This is a genuine implication contribution from T7's output, unlike the spec-side.

**Step 7.** Verify that T7 fires in the narrow channel (not preempted by T6_primary). T6_primary requires: `modality == "hypothesis" AND confidence > 0.6 AND status != "supported" AND "T6" not in history`. Given S_k1 (`status == "supported"`): T6_primary's `status != "supported"` fails → T6_primary skips. T7 fires. ✓

**Step 8.** Selection consideration (code-side): after T7, focus claim is the same (assuming same claim is selected next — insertion-order dependent as with T5→T1, but here there's no new claim created; the claim was already in the graph). On next iteration with status="supported" AND confidence_post > 0.8 AND qualifier set:
- T1–T5: skip (not contradicted, no conflict, has evidence, not underspecified, confidence > 0.4)
- T6_primary: status=="supported" → skip
- T7: qualifier set → skip
- T8_primary: `status == "supported" AND confidence > 0.8` → fires ✓

No preemption. Selection is deterministic given the claim is focused.

**Code-side classification:** **state-dependent**
- S_k1: `claim.status == "supported"` (not produced by T7)
- S_k2: `0.75 < confidence_pre_T7 ≤ 0.80` (narrow channel enabling T7's boost to cross T8's threshold)
- T7's code output DOES participate in satisfying T8's admissibility (unlike spec-side)

### 4.4 Consistency and rationale

**Consistency: divergent**

Both sides are state-dependent, but for different reasons:

- **Spec-side:** T7's output (`qualifier != {}`) contributes nothing to T8's guard. The cascade is a priority-chain artifact: T7 fires before T8 in the chain, then "clears itself" by setting qualifier, and T8's pre-existing guard fires next. S_k must include `confidence > 0.8` as a pre-existing condition.

- **Code-side:** T7's confidence boost (+0.05) IS the enabling predicate. The cascade requires a narrow input-confidence channel (0.75, 0.80] where T7 fires (T8 didn't preempt) and T7's boost then crosses T8's threshold. S_k must include `0.75 < confidence ≤ 0.80` rather than `confidence > 0.8`.

The divergence corresponds precisely to the `spec_silent` finding for T7's confidence boost in `spec_code_discrepancy_matrix_v0-1.md` (T7 mutations, confidence boost +0.05: spec_silent).

---

## 5. Cascade T3 → T9

### 5.1 Predicates

**T3 output (canonical):**
```
|claim.evidence_refs| >= 1
if B-prefixed (per I2 fallback): claim.status == "supported", claim.confidence == 0.85
if non-B and was unknown/hypothesis: claim.status == "disputed"
```

**T9 intrinsic (canonical):**
```
claim.branch_open == True
AND |branches(claim)| > 0
AND all c in branches(claim): c.status == "supported"
where branches(claim) = { c ∈ state.claims | c.parent_id == claim.id }
```

### 5.2 Spec-side implication chain

**Step 1.** T3's spec-side output is: `|claim.evidence_refs| >= 1`. (The I2 fallback predicates are marked `per I2 fallback` and are absent from the spec-side.)

**Step 2.** T9's intrinsic is evaluated on a DIFFERENT CLAIM than T3's target. T3 fires on a branch claim B_j. T9 fires on the parent claim P of those branches. T9 requires that P.branch_open=True AND all children of P have status=="supported".

**Step 3.** T3's spec output (`|B_j.evidence_refs| >= 1`) does not address B_j.status. No spec-side mechanism exists by which T3 produces status="supported" on B_j.

**Step 4.** For T9 to be admissible on P: `all c in branches(P): c.status == "supported"`. This requires B_j.status=="supported", which T3 spec does not produce.

**Step 5.** The implication `O_T3_spec ⊨ G_T9` fails: T3's spec output (evidence_refs growth) does not imply the "all branches supported" condition.

**Step 6.** Additional conditions required:
- S_k1 = `P.branch_open == True` (P is the parent of B_j with a branch structure)
- S_k2 = `B_j.parent_id == P.id` (B_j is a child of P)
- S_k3 = `B_j.status == "supported"` (not derivable from T3 spec output; must come from elsewhere)
- S_k4 = `all other branches of P have status == "supported"` (rest-graph condition)

**Step 7.** With S_k1 ∧ S_k2 ∧ S_k3 ∧ S_k4: T9's intrinsic is satisfied on P. But S_k3 (B_j.status=="supported") is not produced by T3 spec. The cascade, at spec level, has no mechanism connecting T3's output to B_j.status="supported". T3's spec output is causally irrelevant to T9's guard.

**Step 8.** The I2 fallback (`claim.status = "supported"` on LLM failure for B-prefixed claims) is classified as `undocumented_extension` and `spec_silent` in `spec_code_discrepancy_matrix_v0-1.md`. It has no spec representation.

**Spec-side classification:** **state-dependent**
- S_k as above; T3's spec output contributes nothing to T9's guard
- Note: spec-side has no mechanism for T3 to produce status="supported" on B-prefixed claims; the cascade mechanism is entirely absent from the spec

### 5.3 Code-side implication chain

**Step 1.** T3's code-side output for B-prefixed claims (I2 path, `evaluate_branch_claim`, lines 470–486):
- If LLM succeeds: `claim.status = result.get("status", "supported")` — may be "supported"
- If LLM fails: `claim.status = "supported"`, `claim.confidence = 0.85` (fallback, lines 484–486)

For the cascade analysis, the I2 fallback is the clearest case: B_j.status = "supported" is guaranteed when LLM fails.

**Step 2.** After T3 on B_j (B-prefixed, I2 fallback): B_j.status = "supported".

**Step 3.** T9's intrinsic is on P (parent of B_j). Required:
- P.branch_open == True
- |branches(P)| > 0
- all c in branches(P): c.status == "supported"

`branches(P)` is prefix-agnostic: `{ c ∈ state.claims | c.parent_id == P.id }`. This includes B_j (and potentially C-prefixed counter-claims if T5 ever fired on P).

**Step 4.** Additional state conditions:
- S_k1 = `P.branch_open == True` (set by T1 when T1 created B_j and its sibling branches)
- S_k2 = `B_j.parent_id == P.id` (B_j is in branches(P))
- S_k3 = `all other c in branches(P): c.status == "supported"` (rest-graph condition; all other branches of P must already be supported)
- S_k4 = `no C-prefixed claim with parent_id == P.id has status != "supported"` (prefix-agnostic branch collection means T5-created counter-claims on P would also need to be supported; normally absent in a clean T1 branch scenario)

**Step 5.** With O_T3_code(I2) ∧ S_k1 ∧ S_k2 ∧ S_k3 ∧ S_k4:
- B_j.status = "supported" (from O_T3_code)
- All branches of P are "supported" (B_j from O_T3_code; others from S_k3; no interfering C-claims from S_k4)
- P.branch_open = True (from S_k1)
- |branches(P)| > 0 (B_j is at minimum one branch)
- → G_T9 satisfied on P ✓

**Step 6.** T3's code output (status="supported") IS the enabling predicate that satisfies the "all branches" condition for B_j. Unlike the spec-side, T3's code output directly contributes to T9's guard.

**Step 7.** Selection consideration (code-side). After T3 sets B_j.status="supported", is P immediately selected as focus?

`select_focus_claim` (lines 1053–1077) checks:
```python
if claim.branch_open:
    children = [c for c in state.claims.values() if c.parent_id == cid]
    if children and all(c.status == "supported" for c in children):
        t9_ready.append(claim)
    # else: P is excluded from regular (not added anywhere)
```

If S_k3 holds (all other branches already supported) AND B_j.status="supported" (from O_T3_code): all of P's children are now "supported" → P is added to `t9_ready`.

`select_focus_claim` returns `t9_ready[0]` with **explicit priority** over all regular claims. P is selected as focus.

**Step 8.** On P, `select_operation`:
```
line 995: P.is_synthesis? No
line 997: P.status == "contradicted"? No (P.status = "disputed" after T1)
line 999: P.conflict? T1 sets conflict=False on parent; after T2 if fired, conflict=False → skip
... (T3/T4/T5 conditions don't fire on P at this stage given typical graph state)
line 1014: P.branch_open == True AND branches all supported → T9 fires
```

T9 fires on P. Selection is guaranteed by the T9-ready priority mechanism in `select_focus_claim`, not merely by insertion order. This is stronger than the T5→T1 selection guarantee.

**Note on S_k4 (T5 counter-claims in branches(P)):** If T5 ever fires on P directly (P.confidence < 0.4 triggers T5, creating a C-prefixed counter with parent_id=P.id), that counter enters branches(P) and must also have status=="supported" for T9 to fire. This is an additional rest-graph condition not present in the simple T1→branch scenario.

**Code-side classification:** **state-dependent**
- S_k1: `P.branch_open == True`
- S_k2: `B_j.parent_id == P.id`
- S_k3: `all other branches of P already have status == "supported"`
- S_k4: no interfering C-prefixed claims with parent_id=P.id (typically holds in clean branch scenario)
- T3's code output (status="supported" via I2 fallback) IS the enabling predicate for B_j's contribution
- Selection is guaranteed by T9-ready priority once conditions hold

### 5.4 Consistency and rationale

**Consistency: divergent**

Both sides are state-dependent, but for different reasons:

- **Spec-side:** T3's spec output (`evidence_refs >= 1`) contributes nothing to T9's guard. The spec has no mechanism by which T3 produces status="supported" on branch claims. The cascade has no spec-side derivation basis; it is state-dependent only in the formal sense that S_k conditions (including a pre-existing status="supported" on B_j from an unspecified source) would make T9 admissible.

- **Code-side:** T3's I2 fallback output (status="supported") IS the enabling predicate. The cascade has a real code-side derivation: T3 produces the predicate that satisfies the "all branches supported" condition on P. The cascade is state-dependent on S_k (other branches already supported), but T3's output is causally relevant.

The divergence corresponds to the `undocumented_extension` finding for T3's I2 fallback in `spec_code_discrepancy_matrix_v0-1.md` (T3 mutations, B-prefixed path: undocumented_extension).

---

## 6. Cross-Cascade Observations

### X1: No cascade achieves strict-derived

All three tested cascades are state-dependent. None satisfy the strict-derived definition (`O_i ⊨ G_j AND Σ guarantees T_j`). The additional state conditions (S_k) in all three cases are:
- Non-trivial (not recoverable from the canonical predicates alone)
- Partly LLM-outcome dependent (T5→T1: contradiction check) or graph-topology dependent (all three: focus selection or branch completeness)

This is a baseline finding: at the predicate level defined by Amendment Plan v1.1, the three best-known DES cascades are not strictly derivable from layer-1 operator outputs.

### X2: Spec/code divergence maps to discrepancy audit findings

T7→T8 and T3→T9 both show spec/code divergence in the cascade mechanism. The divergences correspond one-to-one with:
- T7 confidence boost (+0.05): `spec_silent` in discrepancy matrix (T7 mutations) → renders spec-side cascade mechanism-free
- T3 I2 fallback (status="supported" for B-prefixed): `undocumented_extension` in discrepancy matrix (T3 mutations) → renders spec-side cascade mechanism-free

The cascade derivability check is therefore sensitive to the same predicate gaps that the discrepancy audit identified. The two audit approaches converge on the same fault lines.

### X3: Selection guarantee strength varies by cascade

The three cascades differ in how strongly the selection policy guarantees the receiver operator:

- **T5→T1 (weakest):** Focus selection depends on insertion order in `regular` list. Original claim is first only if no earlier-inserted unsealed claims exist. Non-deterministic in multi-claim graphs.

- **T7→T8 (intermediate):** No new claim is created; the same claim remains in the graph. Focus selection depends on whether the claim is first in `regular`. If no other unsealed regular claims preempt, the same claim is selected and T8 fires deterministically.

- **T3→T9 (strongest):** `select_focus_claim` implements an explicit T9-ready priority: once all branches of P are supported, P enters `t9_ready` and is returned with priority over all `regular` claims. The selection policy structurally guarantees P is selected once the branch completion condition holds.

### X4: Partial determinism in T5→T1 (double LLM failure sub-path)

The T5→T1 cascade has a sub-path where status="contradicted" is guaranteed without LLM success:

```
T5 LLM failure → counter_predicate = "does not " + claim.predicate
check_for_contradiction LLM failure → Fallback 1 → "does not" ∈ neg_markers → True
→ claim.status = "contradicted"
```

In this sub-path, S_k1 is satisfied deterministically. The cascade becomes guard-derived (for S_k2 focus selection) in this sub-path. This is not visible at the spec level and is not reflected in the canonical predicates.

### X5: T9-ready priority as a structural cascade enabler

The T9-ready priority in `select_focus_claim` (lines 1063–1071) is a selection-policy feature that makes the T3→T9 cascade more reliable than the other two. The priority was designed to prevent parent claims from competing with their own branches in the focus selection — a structural design choice in the selection policy (SP-1) that has cascade-enabling consequences.

---

## 7. Limitations

### L1: Only three cascades tested

This check tests T5→T1, T7→T8, and T3→T9. The full 9×9 cascade map is out of scope. Findings about "no strict-derived cascades" apply only to these three cases and cannot be generalized to the full cascade space.

### L2: Spec-side predicates are derived from Amendment Plan v1.1 and README

Technical sections of DES_Paper1_v1-1.md (3.x, 5.x) are not present in the repository. The spec-side predicates rely on the canonical predicate set from the task brief, which references those sections but cannot be independently verified against them.

### L3: LLM non-determinism is treated as a state condition

`check_for_contradiction` and `evaluate_branch_claim` are LLM-dependent. Their outcomes are treated as state conditions S_k rather than as part of the operator's output predicate. This is consistent with the Amendment Plan's framing of LLM outputs as stochastic, but it means the cascade classification depends on an assumption about what counts as "within the operator" vs. "external state."

### L4: Focus-claim selection ordering is insertion-order dependent

The analysis of focus-claim selection relies on Python 3.7+ dict insertion-order semantics. This is a code-level property, not a specification-level property. If implementation changes, the ordering guarantees change.

### L5: Prefix-agnostic branch collection in T9

`branches(P)` collects all claims with `parent_id == P.id`, regardless of prefix. Counter-claims created by T5 on P (if T5 ever fires on P) enter this set. The cascade analysis for T3→T9 adds S_k4 to handle this, but it is a rest-graph condition that may vary across runs.

### L6: This check does not establish composition as an architectural layer

Even if all three cascades are derivable (with S_k), this does not establish that Composition Patterns are emergent as a layer in the DES architecture. That claim requires the full 9×9 cascade map and additional framework argument.

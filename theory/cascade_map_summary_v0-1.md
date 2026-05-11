# DES 9×9 Cascade Map — Summary v0.1

**Date:** 2026-05-11
**Scope:** Aggregated findings from Phase 1 triage and Phase 2a/2b/2c non-trivial analysis
**Question answered:** For each ordered pair (T_i, T_j): does T_i's output enable T_j to fire?

---

## 1. Executive Summary

The 9×9 cascade map covers all 81 ordered operator pairs (T_i → T_j) in the DES system. Of these:

- **47 cells are trivially not-derived** (Phase 1 triage): incompatibility between T_i output and T_j guard is demonstrable in a single sentence.
- **34 cells required non-trivial analysis** (Phase 2a/2b/2c).

Of the 34 non-trivial cells:
- **0 are strict-derived**: no cell in the 9×9 map is unconditionally derived.
- **5 are guard-derived** (spec-side): T5→T2, T5→T3, T9→T8, and (spec-underspecified†) T1→T3, T4→T3.
- **3 are guard-derived** (code-side): T5→T2, T5→T3, T9→T8.
- **19 are state-dependent-causal** (spec-side), **24 code-side**: the majority of non-trivial cascades require additional state conditions.
- **10 are confirmed not-derived** (spec-side), **7 code-side**: non-trivial pairs where full analysis ruled out any cascade.
- **7 cells are spec/code divergent**: the spec and code reach different derivability classes or selection statuses.

†`spec_underspecified`: guard-derived under charitable interpretation; `modality='hypothesis'` is a Python kwarg default (`b.get('modality','hypothesis')`), not a spec-level commitment.

**D-membership:** D = {strict-derived, guard-derived, state-dependent-causal}; not-derived ∉ D. Uncertainty flags do not affect D-membership. Spec D-members: 24 (5 GD + 19 SD). Code D-members: 27 (3 GD + 24 SD). **SAR = 1.125** (code_D/spec_D = 27/24). **Divergence Density = 20.6%** (7/34 non-trivial cells divergent).

---

## 2. T9→T8: Guard-Derived (No Strict-Derived Cells in 9×9 Map)

There are no strict-derived cells in the 9×9 map. **T9→T8** is correctly classified as **guard-derived** (both sides).

T9 (trigger_reframing) creates a synthesis claim with `status='supported'` and `confidence≥0.82`. O_T9 ⊨ G_T8 definitionally: T8's guard is directly satisfied by T9's output without any additional state condition S_k. This makes T9→T8 guard-derived, not state-dep-causal. The key distinction: the condition “synthesis claim must be focused” governs *when* T8 fires (a selection condition under Σ), not *whether* G_T8 is satisfied (an admissibility condition). Guard-derived = O_i ⊨ G_j but selection not guaranteed.

Spec-side: selection is `not_guaranteed` — the synthesis claim enters the regular focus pool unsealed, and which iteration selects it is an E(t) timing event. Code-side: `select_operation` checks `claim.is_synthesis` at position 0 and routes unconditionally to T8; selection is `guaranteed` given O_T9 success (synthesis claim must exist in G(t+1), which follows definitionally from O_T9). The selection_status divergence (not_guaranteed / guaranteed) is within the guard-derived class and does not constitute a consistency violation.

---

## 3. Guard-Derived Cells: T5→T2, T5→T3, T9→T8 (and T1→T3, T4→T3 spec-side)

### Code-side guard-derived cells (robust)

**T5→T2:** T5 (generate_counter_hypothesis) unconditionally sets `conflict=True` on the focus claim (code line 457). T2's intrinsic guard is `conflict=True`. T5 directly satisfies this guard with no additional conditions. Selection is not_guaranteed because T1 fires first when `status='contradicted'` — but this is a preemption condition, not a guard failure.

**T5→T3:** T5 creates a counter-claim (CC) with `modality='hypothesis'` hardcoded (line ~444). Combined with `evidence_refs=[]` (new claim default), T3's guard is directly satisfied. This hardcoding makes T5→T3 guard-derived at the code level, unlike T1→T4→T3 cascades where the modality is LLM-returned.

### T9→T8 (guard-derived, both sides)

See Section 2. T9 output directly satisfies T8's guard (O_T9 ⊨ G_T8). Code-side synthesis bypass at position 0 guarantees selection given O_T9 success; spec-side selection not_guaranteed due to focus pool timing.

### Spec-side only guard-derived cells with spec_underspecified flag

**T1→T3 and T4→T3:** Under charitable interpretation (new claims default to `modality='hypothesis'`), T1 and T4 output directly satisfies T3's guard — guard-derived spec-side. This classification carries the `spec_underspecified` flag: `modality='hypothesis'` is a Python kwarg default (`b.get('modality','hypothesis')`) in the Claim constructor, not an explicit spec-level commitment. The spec is silent on branch/subclaim modality. At the code level, the LLM can return `'established'`, requiring M(t) S_k — state-dependent-causal.

---

## 4. State-Dependent-Causal Cascades: Patterns

### 4.1 The unlock pattern (T2, T3)

T2 (make_conflict_explicit) clears `conflict=True`. T3 (request_evidence) fills `evidence_refs`. Both operators thereby clear their own guard conditions, which are HIGH/CRITICAL priority guards that were blocking lower-priority operators. The revealed downstream operators (T4 through T7) then fire based on pre-existing state:

| Downstream | S_k required |
|-----------|______________|
| →T4 | scope=={} (G(t)) |
| →T5 | confidence<0.4, scope!={} (G(t)) |
| →T6 | modality='hypothesis', confidence>0.6, status!='supported' (G(t)) |
| →T7 | qualifier=={}, scope!={}, confidence∈[0.4,0.6] (G(t)) |

This 4-column pattern appears twice (T2 and T3) and is the dominant structural feature of the non-trivial cells. In all 8 of these cases, selection is guaranteed given the S_k conditions.

### 4.2 Creator-to-consumer cascades (T1, T4)

T1 (resolve_conflict) and T4 (decompose_claim) create new sub-claims or branch claims. These new claims are immediately eligible for downstream operators:
- T1 creates B-branch claims → T3/T5/T7 can fire on them (T6 is blocked by modality mutual exclusion)
- T4 creates C-subclaim chains → T3/T4/T5/T7 can fire on them (T6 blocked; T4 self-cascade requires narrow M(t) conditions)

The creator-to-consumer pattern is state-dependent-causal for T5/T7 (LLM-dependent modality and confidence), and state-dep-causal/guard-derived at spec/code for T3 (modality divergence).

### 4.3 T5 as a cascade initiator

T5 (generate_counter_hypothesis) produces two downstream effects:
1. `conflict=True` → T2 fires (guard-derived)
2. CC with `modality='hypothesis'`, `evidence_refs=[]` → T3 fires on CC (guard-derived)
3. Sometimes `status='contradicted'` → T1 fires (state-dep-causal)

However, T5 also produces `conflict=True` on the parent claim, which blocks T6, T7, and T9 from firing on the parent. Five T5→X cells are confirmed not-derived.

### 4.4 T6/T7 interaction (complement pair)

After T6 fires on a claim, the next iteration leads to either:
- **T7** (if `qualifier=={}` pre-T6): T8 primary is blocked when qualifier=={}; T7 fires at position 7
- **T8** (if `qualifier!={}`): T8 primary fires directly

These two outcomes are complementary: T6 always leads to exactly one of T7 or T8, making T6 a near-certain enabler of both in aggregate.

### 4.5 T7 qualifier-setter enabling T6, T8, T9

T7 (refine_qualifier) unconditionally produces `qualifier!={}`  (guaranteed by the fallback default `{"temporal":"present","geographic":"global"}`). This single output enables three cascades:

1. **T7→T6:** T7 removes its own position-7 preemption of T6 fallback. After T7, T6 fallback can fire (no T7 to intercept). Also, T7's +0.05 confidence boost can push borderline claims above the T6 primary threshold (confidence>0.6).

2. **T7→T8:** When status='supported' and confidence>0.75 pre-T7, T7 (position 7) preempts T8 primary (position 8) because qualifier=={}. After T7 fires: qualifier!={}, confidence>0.80 → T8 primary fires in the next iteration.

3. **T7→T9:** When branch_open=True and all children are supported, T7 preempts T9 (position 7 < position 9) because qualifier=={}. After T7 fires and sets qualifier!={}, T7 does not re-fire; T9 fires on the next iteration.

### 4.6 T6→T9: indirect child-to-parent cascade

T6 can fire on B-branch child claims (T1-created, modality='hypothesis'). When T6 sets a child's status to 'supported', and if all other children of the same parent already have status='supported', the parent (branch_open=True) becomes T9-ready. `select_focus_claim` prioritizes T9-ready parents, and T9 fires on the parent in the next iteration. This is an indirect cascade: T6 enables T9 on a different claim (the parent) by completing the T9-readiness condition.

---

## 5. Confirmed Not-Derived Cells (Non-Trivial)

Ten cells (spec-side) passed non-trivial analysis and were confirmed not-derived. Seven are not-derived on both sides; three are not-derived spec-side only (divergent):

| Cell | Reason | Sides |
|------|--------|-------|
| T1→T6 | Modality mutual exclusion: T3 preempts unless modality='established'; T6 requires 'hypothesis' | both |
| T2→T9 | T2 targets branch_open=False claims; T9 requires branch_open=True | both |
| T3→T8 | I2 absent from spec; T3 spec output doesn't produce status='supported' | **spec-side only** |
| T4→T6 | Same modality mutual exclusion as T1→T6 | both |
| T5→T4 | T5 priority invariant: T5 fires only when scope!={} (T4 preempts when scope=={}); exclusive conditions | both |
| T5→T6 | T5 sets conflict=True; T2 CRITICAL preempts T6 | both |
| T5→T7 | T5 sets conflict=True; T2 CRITICAL preempts T7 | both |
| T5→T9 | T5 sets conflict=True; T2 preempts all; T9 requires branch_open=True | both |
| T6→T8 | T6 spec output = evidence_refs grew only; T8 intrinsic requires status='supported' — not reachable | **spec-side only** |
| T6→T9 | T6 spec output doesn't produce status='supported'; T9 branch guard unmet spec-side | **spec-side only** |

T3→T8, T6→T8, and T6→T9 appear as not-derived spec-side only; at the code level, all three are state-dependent-causal. Root cause for T6→T8/T9: canonical predicate `(code:)` bracket marks T6 status/confidence mutations as code-only.

---

## 6. Spec/Code Divergences (7 cells)

Seven divergent cells are identified. The root causes cluster into three groups: (A) spec-silent modality defaults vs LLM-dependent code; (B) T3 I2 undocumented extension absent from spec; (C) T6/T7 `(code:)` output predicates absent from spec.

### D1: T1→T3 and T4→T3 (class mismatch: guard-derived vs state-dep-causal)

**Mechanism:** T1 creates B-branch claims with `modality=b.get('modality','hypothesis')` (T4: `sc.get('modality','hypothesis')`). The spec is silent on branch/subclaim modality. Under charitable interpretation, the spec implies `modality='hypothesis'` by default, making T3 directly derivable (guard-derived). At the code level, the LLM can return `modality='established'`, which would block T3's guard (`modality!='established'` is required), making this state-dependent-causal.

**Practical implication:** In typical LLM operation, `'hypothesis'` is the near-universal return value, so the cascade fires almost always. The divergence matters primarily for formal analysis and edge-case behavior when the LLM returns non-default values.

### D2: T3→T8 (class mismatch: not-derived vs state-dep-causal)

**Mechanism:** T3's `evaluate_branch_claim` I2 fallback (lines 484–486: `claim.status='supported'`, `claim.confidence=0.85` on LLM failure) is classified as `undocumented_extension` in the spec/code discrepancy matrix. At the code level, this fallback enables T8 primary (`status='supported' AND confidence>0.8`). The spec has no mechanism to produce `status='supported'` from T3's execution. The code comment confirms the fallback is intentional: "Falls back to supported+0.85 so T9 can always fire."

**Practical implication:** T3 B-path I2 is the code's explicit design to guarantee T9 convergence. The spec doesn't describe this guarantee. Any formal reasoning about DES termination at the spec level misses a key convergence mechanism.

### D3: T3→T9 (selection_status + S_k mismatch, same derivability class)

**Mechanism:** Both spec and code classify T3→T9 as state-dependent-causal, but with fundamentally different S_k:
- **Code-side:** T3 I2 fallback is the causal enabler; `B.status='supported'` is produced by T3 itself. With S_k={all other branches supported}, T9-ready priority in `select_focus_claim` guarantees selection (selection_status=guaranteed).
- **Spec-side:** T3 spec output does not produce `B.status='supported'`; the S_k must include `B.status='supported'` as externally sourced. The cascade is classifiable as state-dep-causal but T3 is not causally responsible for the enabling predicate (selection_status=not_guaranteed; cascade causally empty spec-side).

**Practical implication:** At the spec level, T3→T9 exists only as a state coincidence. At the code level, it is a deliberate design feature.

### D4: T6→T8 and T6→T9 (class mismatch: not-derived vs state-dep-causal)

**Mechanism:** Canonical predicates for T6 explicitly mark `status='supported'` and `confidence≥0.82` as `(code:)` — excluded from spec-side analysis. T6 spec output is `evidence_refs grew` only. T8's intrinsic guard requires `status='supported' AND confidence>0.8`; T9's branch guard requires `all branches status='supported'`. Neither is reachable from T6 spec output alone.

At the code level, T6 sets `claim.status='supported'` (line 868) and `claim.confidence=max(0.82,...)` (line 869). With S_k={qualifier!={}} for T8, and S_k={branch_open, all_other_children_supported} for T9, both cascades are state-dep-causal at the code layer.

**Practical implication:** Any spec-level analysis that concludes T6 enables T8 or T9 is implicitly relying on code-only predicates. The T6→T7 cascade remains aligned (spec-side T6 history gate and evidence growth are sufficient to reveal T7).

### D5: T7→T8 (S_k and causal mechanism mismatch, same derivability class)

**Mechanism:** Both spec and code classify T7→T8 as state-dependent-causal, but with different S_k and causal role for T7's output:
- **Spec-side:** T7 output (`qualifier≠{}`) is causally irrelevant to T8's guard (`status='supported' AND confidence>0.8`). T7 is causally necessary (it fires at position 7 and must fire to clear its own preemption of T8 at position 8), but T7's qualifier output plays no role in satisfying T8's intrinsic. S_k must include `confidence>0.8 pre-T7` as a pre-existing condition (no spec-side confidence boost).
- **Code-side:** T7 code adds `confidence+=0.05` (line 893). In the narrow channel S_k={confidence∈(0.75,0.80]}, T8 primary was blocked (confidence≤0.80); after T7's boost, confidence∈(0.80,0.85]>0.8 — T8 primary fires. T7's confidence boost IS the enabling predicate.

**Practical implication:** Spec-side reasoning about T7→T8 must posit confidence>0.8 as a pre-condition not traceable to T7. Code-side, T7 actively enables a class of claims that would not otherwise reach T8 (those in the narrow confidence∈(0.75,0.80] band). Documented as the canonical divergent cascade (Drei-Fall) in `composition_derivation_check_v0-1.json`.

---

## 7. Notable Structural Properties

### 7.1 T8 as a sink

T8 seals claims and creates no new claims. All 9 cells in the T8 producer row are trivially not-derived. Once T8 fires, the claim leaves the active focus pool permanently. T8 is a terminal state in every cascade path.

### 7.2 T9 as a near-sink

T9 seals the parent and creates only a synthesis claim satisfying T8's requirements. T9→T8 is **guard-derived** (O_T9 ⊨ G_T8; no S_k needed for admissibility). Spec-side: selection not_guaranteed (focus pool timing, E(t)). Code-side: synthesis bypass at position 0, selection guaranteed given O_T9 success. In practice, the synthesis claim is always eventually selected and T8 fires. All other T9 producer cells are trivially not-derived. T9 produces a one-step continuation (to T8) and then terminates.

### 7.3 Longest plausible cascade chains

Based on derivability, the longest plausible cascade chains are:
- T1 → T3 → T4 → T5 → T1 (loop: contradicted state, via T5→T1 with M(t) contradiction)
- T1 → T3 → T6 → T7 → T8 (linear chain via unlock, evidence exploration, qualifier refinement, seal)
- T1 → T3 → T9 → T8 (via T3 I2 code path enabling T9-ready; T9 synthesis claim then focused for T8)
- T4 → T3 → T9 → T8 (via subclaim → evidence → I2 → synthesis)

### 7.4 The priority chain and cascade predictability

The cascade map directly maps to the `select_operation` priority chain (lines 988–1020). Most non-trivial cascades involve one operator clearing its own guard (unlock pattern) and revealing a lower-priority operator. The complementary T6→T7/T8 split and T7→T6/T8/T9 patterns reflect the interleaved priority positions (6, 7, 8, 9) of these operators in the chain.

---

## 8. Open Questions Relevant to Cascades

**OQ1 (T2 status):** If the LLM returns `suggested_status != 'disputed'` for T2, downstream operators expecting `status='disputed'` may behave unexpectedly. The cascade map assumes T2 outputs `status='disputed'` (the template default).

**OQ2 (T6 Anti-Delphi history bug):** Anti-Delphi T6 appends `"T6[anti-delphi]"` to history, not `"T6"`. The T6 history guard (`"T6" not in history`) does not detect Anti-Delphi firings. A claim could have T6 (Anti-Delphi) fire and then satisfy the T6 guard again in subsequent iterations, potentially enabling further T7→T6 and T6→T7/T8/T9 cascades. The cascade map counts T6 as having fired once per the standard path; the Anti-Delphi path may allow additional T6 cascade chains.

**OQ3 (T9 branch collection):** T9 collects branches as all claims with `parent_id==claim.id`, including T5-created counter-claims. If T5 fired on a T1-parent before T9, the counter-claim participates in the T9 synthesis. This could affect T9→T8 cascade semantics (synthesis may include non-branch material) but does not affect the strict-derived classification.

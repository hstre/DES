# DES 9×9 Cascade Map — Phase 2c: T6/T7/T9 Producer Analysis v0.1

**Date:** 2026-05-11
**Branch:** `theory/cascade-map-9x9`
**Phase:** 2c of 3 sub-phases (T6, T7, T9 as producers)
**Predicate baseline:** Amendment Plan v1.1 canonical predicates; code from `des.py`
**Prerequisites:** Phase 1 triage; Phase 2a (T1/T2/T3 producers) and Phase 2b (T4/T5 producers) complete

---

## 1. Phase 2c Summary

- **Cells analyzed:** 7 (T6→T7/T8/T9; T7→T6/T8/T9; T9→T8)
- **Class distribution (spec-side):** state-dependent-causal 5, not-derived 2
- **Class distribution (code-side):** state-dependent-causal 7
- **Spec/code divergences:** 3 cells (T6→T8, T6→T9, T7→T8)
- **Uncertainty flags:** 1 cell (T9→T8, spec_underspecified)
- **Critical observation:** Canonical predicates for T6 and T7 bracket
  status/confidence mutations as `(code:)`. Spec-side T6 output = evidence_refs
  grew ONLY; spec-side T7 output = qualifier≠{} ONLY. This causes three divergences
  where code-side state-dep-causal derives via T6 status='supported' or T7 confidence
  boost, while spec-side cannot reach T8's intrinsic (status='supported', confidence>0.8)
  from these outputs.
- **T7→T8 Drei-Fall reference:** Classified as divergent in
  `composition_derivation_check_v0-1.json` (divergence: spec-side S_k requires
  confidence>0.8 pre-T7 as pre-existing condition; code-side narrow-channel S_k
  requires confidence∈(0.75,0.80] with T7 confidence boost as enabling predicate).

---

## 2. Per-Cell Analysis

---

### T6 → T7

**Canonical predicates:**
- T6 spec output: `evidence_refs grew`; "T6" appended to history (both spec and code)
- T6 code output additionally: `claim.status="supported"`, `claim.confidence≥0.82` (code-only, `(code:)` bracket)
- T7 intrinsic + admissibility: `claim.qualifier=={}` AND `claim.scope!={}` (at priority
  position 7, after T6 primary at position 6)

**Causal necessity test:**
- Counterfactual C(t): qualifier=={}, scope!={}, evidence_refs!={}, modality='hypothesis',
  confidence>0.6, "T6" NOT in history — without T6 having fired.
- Without T6: T6 primary (position 6) fires before T7 (position 7) when its guard is
  satisfied. T6 preempts T7 in this state.
- Conclusion: T6 is causally necessary to enable T7 via two simultaneous contributions:
  (a) "T6" appended to history removes T6's position-6 preemption of T7; (b) evidence_refs
  growth removes T3's position-3 preemption. With qualifier=={} as the remaining S_k,
  T7 fires.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and claim re-focused)
- S_k components: [`E(t): qualifier=={} pre-T6 (T6 does not change qualifier)`]
- uncertainty_flag: null
- Implication chain: T6 spec output (evidence_refs grew, "T6" in history) removes both
  T3's position-3 guard (evidence_refs!=[] blocks T3) and T6's own position-6 preemption
  (history gate blocks T6 primary). T7 fires at position 7 when qualifier=={}. Scope!={} is
  guaranteed because T6's own spec guard excludes scope=={} (T4 at position 4 would have
  preempted T6 if scope=={}). After T6, T8 primary spec-side requires status='supported'
  (unchanged by T6 spec) — without status='supported', T8 primary doesn't fire; T7 takes
  position-7. State-dep-causal with S_k={qualifier=={}} (E(t) unchanged by T6).

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and claim re-focused)
- S_k components: [`E(t): qualifier=={} pre-T6 (T6 code does not write to claim.qualifier)`]
- Implication chain: T6 code (lines 846–872) sets claim.status='supported' (line 868) and
  claim.confidence=max(0.82,...) (line 869); these do not change qualifier. T8 primary (line
  1011–1013) blocked when qualifier=={} AND scope!={} (NOT-condition False). T7 guard (line
  1010): qualifier=={} AND scope!={} — met given S_k. T7 fires at position 7 before T8 at
  position 8. Code refs: lines 846–872 (T6), 875–896 (T7), 1007–1013 (priority chain).
- code_references: lines 846–872 (T6), 875–896 (T7), 1007–1013 (select_operation T6/T7/T8)

**Consistency:** aligned
**Rationale:** Both sides: T6 removes its own position-6 preemption (history gate) and T3's
preemption (evidence_refs grew), revealing T7 at position 7 given qualifier=={}.
Spec-side status unchanged post-T6 (code-side status='supported' doesn't affect the
qualifier=={} gate). Complementary to T6→T8.

---

### T6 → T8

**Canonical predicates:**
- T6 spec output: `evidence_refs grew` ONLY (`(code:)` marks status=supported, confidence≥0.82
  as code-only mutations excluded from spec-side)
- T6 code output additionally: `claim.status="supported"`, `claim.confidence≥0.82`
- T8 intrinsic (spec): `claim.status=="supported"` AND `claim.confidence>0.8`

**Causal necessity test:**
- Counterfactual C(t): a claim with status='supported', confidence>0.8 without T6.
- Without T6: T8 primary fires on any such claim regardless of how the predicates arose.
- Conclusion: Spec-side T6 output (evidence_refs grew) does not produce status='supported'
  or change confidence. T8's spec intrinsic cannot be derived from T6 spec output alone.
  Code-side T6 sets status='supported' and confidence≥0.82, directly contributing to T8.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T6 spec output is evidence_refs grew only (canonical predicate notes
  status/confidence changes as `(code:)`, explicitly excluded from spec). T8 spec intrinsic
  requires status='supported' AND confidence>0.8. Neither is produced by T6 spec output.
  T6 history gate prevents T6 re-fire, but this does not satisfy T8's intrinsic. No
  implication chain from T6 spec output to T8 spec intrinsic. Not-derived.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and claim re-focused)
- S_k components: [`E(t): qualifier!={} pre-T6 (T6 code does not write to claim.qualifier)`]
- Implication chain: T6 code sets status='supported' (line 868) and confidence=max(0.82,...)
  (line 869), satisfying T8 primary's core predicates. T8 primary guard (lines 1011–1013)
  also requires NOT(qualifier=={} AND scope!={}). After T6: qualifier unchanged; when
  qualifier!={}, this guard is satisfied. T7 (position 7, qualifier=={} guard) doesn't fire
  when qualifier!={}, so T8 primary fires directly at position 8. All other T8 primary guards
  met by T6 output (conflict==False, evidence_refs!={}, scope!={}). Code refs: lines
  846–872 (T6), 899–904 (T8), 1011–1013 (T8 primary guard).
- code_references: lines 846–872 (T6), 899–904 (T8), 1011–1013 (T8 primary guard)

**Consistency:** divergent
**Rationale:** Spec-side: T6 spec output = evidence_refs grew; no mechanism to reach T8's
status='supported' AND confidence>0.8 intrinsic — not-derived. Code-side: T6 code
output includes status='supported' and confidence≥0.82 (`(code:)` predicates); enables
T8 primary with S_k={qualifier!={}}. Root cause: `(code:)` T6 output predicates absent
from spec.

---

### T6 → T9

**Canonical predicates:**
- T6 spec output: `evidence_refs grew` ONLY (code-only: status='supported', confidence≥0.82)
- T9 intrinsic: `focus.branch_open==True` AND `branches_non-empty` AND
  `all(c.status=="supported" for c in branches)`

**Causal necessity test:**
- Counterfactual C(t): a B-branch child claim becomes status='supported' via another
  path (T3, T8 etc.), without T6.
- Without T6: T9 parent readiness depends on all children status='supported', independent
  of mechanism.
- Conclusion: Spec-side T6 output (evidence_refs grew) doesn't produce status='supported'
  on the child. Code-side T6 produces status='supported', contributing to T9's "all branches
  supported" condition when S_k holds.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T6 spec output is evidence_refs grew only. T9's "all branches
  status=='supported'" predicate requires status='supported' on each branch claim. T6 spec
  output does not change any claim's status. Even if T6 fires on a B-branch child
  (legitimate target), the child's status remains unchanged at spec level — no path from
  evidence_refs growth to status='supported'. T9's branch_open guard (requires T1 to have
  fired earlier) is also not addressed by T6 spec output. Not-derived spec-side.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [
    "E(t): claim.parent_id == P.id for some parent P",
    "E(t): P.branch_open==True (T1 must have fired on P earlier)",
    "E(t): all c in state.claims where c.parent_id==P.id and c.id!=claim.id have c.status=='supported'"
  ]
- Implication chain: T6 code (line 868) sets claim.status='supported'. If focus claim is
  a B-branch child of P (P.branch_open==True) and all other P-children are already
  status=='supported', then P becomes T9-ready. select_operation T9 check (lines 1014–1017):
  if all P.children.status=='supported', T9 fires on P. Parent P.status='disputed' (T1, line
  633); T8 primary doesn't intercept P. select_focus_claim (lines 1067–1069) places P in
  t9_ready queue (priority over regular pool). S_k={branch_open, all_other_children_supported}
  not produced by T6. selection not_guaranteed: focus ordering E(t)-dependent.
- code_references: lines 846–872 (T6, line 868), 926–981 (T9), 1014–1017 (T9 guard),
  1053–1077 (select_focus_claim T9-ready prioritization)

**Consistency:** divergent
**Rationale:** Spec-side: T6 spec cannot produce status='supported' on a branch child; T9
guard unmet — not-derived. Code-side: T6 code sets status='supported' on the focus claim;
with S_k this enables T9 on parent — state-dep-causal. Root cause: `(code:)` status
predicate absent from spec. Same root cause as T6→T8.

---

### T7 → T6

**Canonical predicates:**
- T7 spec output: `claim.qualifier≠{}` (guaranteed via fallback; both spec and code)
- T7 code output additionally: `claim.confidence+=0.05` (code-only per canonical predicates)
- T6 primary intrinsic (position 6): `modality=="hypothesis"` AND `confidence>0.6` AND
  `status!="supported"` AND `"T6" not in history`
- T6 fallback intrinsic (position 10): `modality=="hypothesis"` AND `"T6" not in history`
  AND `NOT(qualifier=={} AND scope!={})` AND `NOT(status=="supported" AND confidence>0.8)`
  AND `NOT(branch_open AND all_children_supported)`

**Causal necessity test:**
- Counterfactual C(t): qualifier!={}, modality='hypothesis', "T6" not in history, without T7.
- Without T7: if qualifier was already !={} from another source, T6 fallback fires directly.
  T7 is not uniquely necessary. However, in the specific path where qualifier=={} (T7's
  pre-condition), T7 is necessary because T7 at position 7 preempts T6 fallback at position
  10 until qualifier is set.
- Conclusion: T7 enables T6 by (a) setting qualifier!={} to remove T7's own position-7
  preemption of T6 fallback; (b) code-side: confidence boost can push borderline claims
  above T6 primary threshold. The spec-side enabling mechanism is only (a).

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [
    "E(t)/M(t): claim.modality=='hypothesis' (T7 does not change modality)",
    "E(t): 'T6' not in claim.history",
    "E(t)/M(t): claim.status!='supported'",
    "E(t)/M(t): claim.confidence≤0.6 AND claim.confidence≥0.4 (confidence≤0.6 means T6 primary blocked; ≥0.4 means T5 doesn't preempt at position 5)",
    "E(t): claim.branch_open==False (T9 not triggered before T6 fallback at position 10)"
  ]
- Implication chain: T7 spec sets qualifier!={} (fallback default guaranteed). With qualifier!={},
  T7 does not re-fire (T7 requires qualifier=={}). T6 fallback (position 10) requires
  NOT(qualifier=={} AND scope!={}) — satisfied. T6 primary (position 6) requires confidence>0.6;
  since spec T7 has no confidence boost, this remains blocked unless confidence was already >0.6
  (but T7 fires only when T6 primary's guard fails, so confidence must have been ≤0.6 or another
  T6 primary condition failed). With S_k: T6 fallback fires on next iteration. selection
  not_guaranteed: E(t) focus ordering.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [
    "E(t)/M(t): claim.modality=='hypothesis'",
    "E(t): 'T6' not in claim.history",
    "E(t)/M(t): claim.status!='supported'",
    "E(t)/M(t): claim.confidence∈(0.35,0.60] pre-T7 (post-T7 confidence≥0.40 above T5; >0.55 pre-T7 enables T6 primary via boost; ≥0.35 pre-T7 enables T6 fallback via qualifier)",
    "E(t): claim.branch_open==False (for T6 fallback path)"
  ]
- Implication chain: T7 code (lines 875–896) sets qualifier!={} via fallback (lines 888–890).
  T6 primary (lines 1007–1009): confidence>0.6 — met when pre-T7 confidence∈(0.55,0.60] after
  +0.05 boost. T6 fallback (lines 1018–1019): NOT(qualifier=={} AND scope!={}) — True after T7.
  T5 (position 5, line 1005) preempts when post-T7 confidence<0.4; requires pre-T7 confidence≥0.35.
  Code-side enables both T6 primary (narrow confidence channel) and T6 fallback (broader). Code
  refs: lines 875–896 (T7), 846–872 (T6), 1005 (T5 guard), 1007–1009 (T6 primary), 1018–1019
  (T6 fallback), 888–890 (T7 qualifier fallback).
- code_references: lines 875–896 (T7), 846–872 (T6), 1005/1007–1009/1018–1019 (T5/T6 guards)

**Consistency:** aligned
**Rationale:** Both sides: T7 spec output (qualifier!={}) removes T7's own preemption of T6
fallback; state-dep-causal with S_k on modality, history, status, confidence. Code-side adds
T6 primary path via confidence boost (broader S_k coverage) but same derivability class.
The additional code-side path does not create a class mismatch.

---

### T7 → T8

**Canonical predicates:**
- T7 spec output: `claim.qualifier≠{}` ONLY (confidence boost is `(code:)`, excluded from spec)
- T7 code output additionally: `claim.confidence+=0.05`
- T8 intrinsic: `claim.status=="supported"` AND `claim.confidence>0.8`
- Pre-reference: `composition_derivation_check_v0-1.json` ("T7→T8", divergent)

**Causal necessity test:**
- Counterfactual C(t): claim with status='supported', confidence>0.8, qualifier!={} without T7.
- Without T7 (qualifier was already !={}) : T8 primary fires directly. T7 is not necessary.
- When T7 IS necessary: qualifier=={} → T7 fires (position 7) preempting T8 primary
  (position 8). Without T7 clearing qualifier, T7 fires repeatedly, perpetually blocking T8.
  T7 must fire to clear qualifier=={} before T8 can fire.
- Conclusion: T7 is causally necessary (clears its own blocking of T8), but spec-side T7
  output (qualifier!={}) plays no role in T8's admissibility. Code-side T7 confidence boost
  (+0.05) can be the enabling predicate crossing T8's confidence threshold.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and claim re-focused)
- S_k components: [
    "E(t)/M(t): claim.status=='supported' (T7 does not change status)",
    "E(t)/M(t): claim.confidence>0.8 pre-T7 (T7 spec has no confidence effect; T8's confidence threshold must be pre-satisfied)"
  ]
- uncertainty_flag: null
- Implication chain: T7 fires at position 7 when qualifier=={}, preempting T8 primary at
  position 8. T7 spec output (qualifier!={}) plays no role in T8's admissibility (T8 requires
  status='supported' AND confidence>0.8, neither produced by T7 spec). T7 is causally
  necessary (clears qualifier=={} block) but T7's qualifier output is causally IRRELEVANT
  to T8's guard. With S_k={status='supported', confidence>0.8 pre-T7}: after T7, T6 primary
  skips (status='supported'), T7 skips (qualifier!={}}), T8 primary fires. S_k includes
  confidence>0.8 as pre-existing (no spec-side boost). Reference: composition_derivation_check_v0-1.json
  spec-side chain, S_k2 = "claim.confidence > 0.8 before T7 fires (not produced by T7 spec)."

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and claim re-focused)
- S_k components: [
    "E(t)/M(t): claim.status=='supported' (T7 does not change status)",
    "E(t)/M(t): claim.confidence∈(0.75,0.80] pre-T7 (narrow channel: T8 did not preempt T7 on prior iteration since confidence≤0.80; T7 boost +0.05 crosses T8 threshold: post-T7 confidence∈(0.80,0.85])"
  ]
- Implication chain: T7 code sets qualifier!={} AND boosts confidence by +0.05 (line 893). With
  S_k1={status='supported'}: T6 primary skips (status='supported'). T7 fires (qualifier=={}).
  In narrow channel S_k2={confidence∈(0.75,0.80]}: T8 primary did NOT fire before T7 (strict
  confidence>0.8 not yet met); after T7, confidence∈(0.80,0.85]>0.8 — T8 primary fires.
  T7's confidence boost IS the enabling predicate in the narrow channel. Reference:
  composition_derivation_check_v0-1.json code-side key_difference_from_spec. Code refs:
  lines 875–896 (T7), 899–904 (T8), 893 (confidence boost), 1011–1013 (T8 primary guard).
- code_references: lines 875–896 (T7), 899–904 (T8), 893 (T7 confidence boost), 1011–1013

**Consistency:** divergent
**Rationale:** Both sides state-dep-causal, but S_k and causal mechanism diverge. Spec-side:
T7 qualifier output is causally irrelevant to T8; S_k requires confidence>0.8 pre-existing.
Code-side: T7 confidence boost is the enabling predicate; S_k requires only confidence∈(0.75,0.80]
(narrow channel). Divergence maps to `(code:)` confidence boost in canonical predicates and
spec_silent classification in spec_code_discrepancy_matrix_v0-1.md. Confirmed in
composition_derivation_check_v0-1.json as the canonical divergent cascade.

---

### T7 → T9

**Canonical predicates:**
- T7 spec output: `claim.qualifier≠{}` (T7 code additionally: confidence+=0.05)
- T9 intrinsic: `claim.branch_open==True` AND `branches_non-empty` AND
  `all(c.status=="supported" for c in branches)`

**Causal necessity test:**
- Counterfactual C(t): T9-ready claim (branch_open=True, all children supported) with
  qualifier!={} without T7 having fired.
- Without T7: T9 fires directly (qualifier!={} means T7 doesn't preempt T9). T7 not necessary
  in this scenario.
- When T7 IS necessary: qualifier=={} AND branch_open=True AND all_children_supported →
  T7 fires (position 7) before T9 (position 9). T7 must fire to clear qualifier=={} block.
- Conclusion: T7 clears its own position-7 preemption, enabling T9 to fire on the next iteration.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and T9-ready parent prioritized)
- S_k components: [
    "E(t): claim.branch_open==True (T1 must have fired earlier on this claim)",
    "E(t): all children of claim have status=='supported' (T7 does not change child statuses)"
  ]
- uncertainty_flag: null
- Implication chain: When qualifier=={} AND branch_open==True AND all_children_supported,
  T7 fires at position 7 before T9 at position 9. T7 spec output (qualifier!={}) removes T7
  from the priority chain for the next iteration (T7 requires qualifier=={}; now
  qualifier!={}). T9 guard (branch_open AND all children supported) is unchanged by T7.
  With S_k: T9 fires on next iteration where claim is focused. select_focus_claim prioritizes
  T9-ready claims (branch_open=True, all children supported). Selection guaranteed given T9-ready
  priority and S_k intact.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k and T9-ready parent prioritized)
- S_k components: [
    "E(t): claim.branch_open==True",
    "E(t): all c in state.claims where c.parent_id==claim.id have c.status=='supported'"
  ]
- Implication chain: T7 code sets qualifier!={} (lines 888–890). T7 guard (line 1010)
  qualifier=={} no longer satisfied; T7 does not re-fire. T9 guard (lines 1014–1017):
  branch_open==True AND branches non-empty AND all branches status=='supported' — all
  unchanged by T7. Parent status='disputed' (from T1 line 633); T8 primary does not
  intercept. select_focus_claim (lines 1067–1069) places claim in t9_ready queue (priority
  over regular pool). T9 fires in next focused iteration given S_k. Code refs: lines
  875–896 (T7), 926–981 (T9), 1010 (T7 guard), 1014–1017 (T9 guard), 1053–1077.
- code_references: lines 875–896 (T7), 926–981 (T9), 1010 (T7 guard), 1014–1017 (T9 guard),
  1053–1077 (select_focus_claim T9-ready prioritization)

**Consistency:** aligned
**Rationale:** Both sides: T7 fires first at position 7 (preempting T9 at position 9), sets
qualifier!={}, then T9 fires on next iteration when S_k={branch_open==True, all_children_supported}
holds. Spec-side mechanism (qualifier!={} removes T7 preemption) identical to code-side.

---

### T9 → T8

**Canonical predicates:**
- T9 output (Path A, single-agent): new `C-prefixed` claim with `is_synthesis=True`,
  `status="supported"`, `modality="suggestion"`, `confidence≥0.82`, `parent_id=claim.id`,
  `sealed=False`; original claim `sealed=True`
- T9 output (Path B, Anti-Delphi): new `C-prefixed` role-generated claims with
  `is_synthesis=True`; original claim `sealed=True`
- T8 spec intrinsic: `claim.status=="supported"` AND `claim.confidence>0.8`
- T8 code synthesis bypass (position 0): `claim.is_synthesis==True`

**Causal necessity test:**
- Counterfactual C(t): synthesis claim with status='supported', confidence≥0.82 without T9.
- Without T9: T8 fires on any supported high-confidence claim regardless of origin. T9 is
  not uniquely necessary for T8 to fire; it is the standard creator of the enabling predicates.
- Conclusion: T9 is the operator that produces the predicates enabling T8; no other operator
  creates synthesis claims in the standard pipeline. State-dep-causal with S_k={synthesis claim
  is selected as focus (E(t))}.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k; T9 fires only when parent qualifier!={}; synthesis
  inherits qualifier!={}, so T7 does not preempt T8 on synthesis claim)
- S_k components: ["E(t): synthesis claim is selected as focus (not-sealed, in regular pool)"]
- uncertainty_flag: spec_underspecified
- uncertainty_note: Spec describes T9 as producing a synthesis claim (status='supported',
  confidence≥0.82). T8 spec intrinsic (status='supported' AND confidence>0.8) is directly
  satisfied by T9 spec output. Whether spec recognizes synthesis claims as automatically
  satisfying T8 independent of the code-side synthesis bypass is not explicitly stated.
  Charitable: T8 seals supported high-confidence claims; T9 produces exactly such claims.
  Per Memo v3 SP-3 Type D (relational shortcut), classified as state-dep-causal rather than
  strict-derived to acknowledge the E(t) focus selection condition.
- Implication chain: T9 spec output (Path A): synthesis claim with status='supported' and
  confidence≥0.82>0.8 directly satisfies T8 spec intrinsic. T9 fires only after parent
  qualifier!={} is established (T7 fires at position 7 before T9 at position 9 when qualifier=={}),
  so synthesis inherits qualifier!={} — T7 does not preempt T8 on synthesis claim. After T9:
  synthesis claim is unsealed, enters focus pool; T8 fires on it. S_k={synthesis claim focused}.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed (given S_k; synthesis bypass at position 0 has no competing guard)
- S_k components: ["E(t): synthesis claim is selected as focus (unsealed, in regular pool)"]
- Implication chain: T9 Path A (lines 926–981): synthesis claim with is_synthesis=True (Path A
  constructor). T9 Path B (_apply_antidelphi_state_change lines 344–373): role-generated claims
  post-hoc set is_synthesis=True. select_operation synthesis bypass (lines 995–996): `if
  claim.is_synthesis: return T8` — fires at position 0 before any other check. No operator
  preempts synthesis bypass (it is position 0). S_k={synthesis claim focused}: once in focus
  pool (unsealed, default sealed=False), claim is eventually selected; T8 fires unconditionally.
  Per SP-3 classification: state-dep-causal via T9 Output Contract (synthesis claim satisfies
  T8 primary admissibility). Code refs: lines 926–981 (T9), 899–904 (T8), 995–996 (synthesis
  bypass), 344–373 (_apply_antidelphi_state_change).
- code_references: lines 926–981 (T9), 899–904 (T8), 995–996 (synthesis bypass), 344–373

**Consistency:** aligned
**Rationale:** Both sides: T9 produces a synthesis claim satisfying T8's requirements; T8 fires
on the synthesis claim when focused. Spec-side via T8 intrinsic (status='supported',
confidence≥0.82); code-side via synthesis bypass (is_synthesis=True, position 0). Mechanisms
differ but derivability class is the same (state-dep-causal with E(t) focus selection as S_k).
uncertainty_flag reflects spec_underspecified on synthesis bypass vs intrinsic distinction.

# DES 9×9 Cascade Map — Phase 2a: T1/T2/T3 Producer Analysis v0.1

**Date:** 2026-05-11
**Branch:** `theory/cascade-map-9x9`
**Phase:** 2a of 3 sub-phases (T1, T2, T3 as producers)
**Predicate baseline:** Amendment Plan v1.1 canonical predicates; code from `des.py`
**Prerequisites:** `theory/cascade_map_triage_v0-1.json` (Phase 1)

---

## 1. Phase 2a Summary

- **Cells analyzed:** 15 (T1→T3/T5/T6/T7; T2→T4/T5/T6/T7/T9; T3→T4/T5/T6/T7/T8/T9)
- **Class distribution (spec-side):** guard-derived 1, state-dependent-causal 9, not-derived 5
- **Class distribution (code-side):** state-dependent-causal 10, not-derived 5
- **Spec/code divergences:** 3 cells (T1→T3, T3→T8, T3→T9)
- **Uncertainty flags:** 8 cells (all from spec-silent or spec_underspecified predicates)
- **Pattern:** T2-as-producer cascades are structurally uniform — T2 clears conflict=False,
  revealing pre-existing guards of T4/T5/T6/T7; all are state-dependent-causal with G(t) S_k.
  T2→T9 and T1→T6 are not-derived after full analysis.

---

## 2. Per-Cell Analysis

---

### T1 → T3

**Canonical predicates:**
- T1 output: 2 new B-prefixed claims; each has `evidence_refs=[]`, `status="hypothesis"`,
  `parent_id=claim.id`, `scope≠{}`, `modality=LLM-returned or "hypothesis"` (default);
  parent gets `branch_open=True`, `status="disputed"`, `conflict=False`
- T3 intrinsic + admissibility: `evidence_refs==[]` AND `modality!="established"`

**Causal necessity test:**
- Counterfactual C(t): a B-branch exists with `evidence_refs=[]` and `modality="hypothesis"` without T1 having fired.
- Without T1, S_k satisfies G_j? No — B-prefixed branch claims only exist because T1 created them; no other operator creates B-branches.
- Conclusion: T1 is causally necessary as creator of the B-branches that T3 fires on. T3's guard is satisfied by T1's output under the default modality.

**Spec-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: none (guard satisfied by T1 output under charitable interpretation)
- uncertainty_flag: spec_underspecified
- uncertainty_note: Classification depends on the charitable interpretation that new B-prefixed branch claims default to modality='hypothesis'. Paper 1 Section 3.3 does not specify branch claim modality. Under the alternative interpretation that spec is silent on the modality of created branch claims, this cell would be not-derived (T3's intrinsic guard could not be confirmed satisfied spec-side). The code-side LLM-returned modality (via b.get('modality', 'hypothesis')) makes this divergent regardless of the spec interpretation choice.
- Implication chain: T1 spec "branches into two sub-claims" creates new claims with no evidence (`evidence_refs=[]` implied for new claims). T3 spec guard is "no evidence + not established." Under charitable interpretation that new branch claims have modality ≠ "established", T1's output directly satisfies T3's guard — guard-derived. The charitable assumption is forced by spec silence on branch modality. Selection is not_guaranteed because focus assignment to a specific B-branch depends on E(t) insertion order and graph size.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `branch.modality != "established"` — LLM-returned or default "hypothesis"]
- Implication chain: T1 code (lines 578–643) creates B-branches with `modality=b.get("modality","hypothesis")` — LLM determines modality; "hypothesis" is the default but LLM could return "established." T3 code guard (line 1001) requires `evidence_refs==[]` AND `modality!="established"`. Since LLM could return "established", T1's output does not unconditionally imply G_T3; S_k = {M(t): `branch.modality!="established"`} is required. In the common case (LLM returns "hypothesis"), T3 fires on the first focused B-branch. Selection depends on E(t): parent is excluded from focus (branch_open=True, branches not all supported); B-branches compete with other regular claims in insertion order. Code refs: lines 578–643 (T1), 670–685 (T3), 1001 (select_operation), 1063–1071 (select_focus_claim).

**Consistency:** divergent
**Rationale:** Spec-side is guard-derived (charitable: new branches have default modality≠"established"); code-side is state-dependent-causal because the LLM could return "established", requiring M(t) S_k. The divergence maps to spec_silent on branch modality in the discrepancy matrix.

---

### T1 → T5

**Canonical predicates:**
- T1 output: B-branches with `evidence_refs=[]`, `status="hypothesis"`, `modality=LLM/"hypothesis"`,
  `confidence=LLM or 0.5 (default)`, `scope≠{}`
- T5 intrinsic + admissibility: `status!="contradicted"` AND `confidence<0.4`

**Causal necessity test:**
- Counterfactual C(t): a B-branch with `modality="established"` AND `confidence<0.4` AND `evidence_refs=[]` without T1.
- Without T1, S_k satisfies G_j? No — B-branches only exist because T1 created them.
- Conclusion: T1 necessary but insufficient. T3 has priority HIGH over T5 (MEDIUM); T3 fires on any B-branch with `evidence_refs==[]`. For T5 to fire directly on a T1 B-branch, T3 must be preempted; this requires `modality=="established"` (T3 guard: `modality!="established"`). With `modality=="established"`, T3 is blocked and T5 can fire if `confidence<0.4`.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `branch.modality=="established"`, `M(t)`: `branch.confidence<0.4`]
- uncertainty_flag: spec_underspecified
- Implication chain: T1 spec creates branches; spec is silent on branch modality and confidence. T5 spec guard is `confidence<0.4`. For T5 to fire on a T1 B-branch, T3 must not preempt; spec doesn't specify branch modality. Under charitable interpretation both S_k conditions (modality="established" and confidence<0.4) must be supplied as M(t) state. The classification is state-dependent-causal; spec uncertainty about branch properties makes the S_k non-derivable from spec alone.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `branch.modality=="established"` (LLM-returned non-default), `M(t)`: `branch.confidence<0.4` (LLM-returned)]
- Implication chain: T1 creates B-branches with `modality=b.get("modality","hypothesis")` and `confidence=float(b.get("confidence",0.5))` (line 601–612). Default confidence=0.5 ≥ 0.4, so T5 doesn't fire on defaults. For T5 to fire: LLM must return `modality="established"` (blocks T3's guard at line 1001) AND `confidence<0.4`. If both hold, T3 and T4 are preempted, T5 fires (line 1005). B-branch is in regular pool (branch_open=False); focus assignment is E(t)-dependent. Code refs: lines 578–643 (T1 branch creation), 1001 (T3 preemption), 1005 (T5 guard).

**Consistency:** aligned
**Rationale:** Both sides require the same M(t) S_k conditions (branch modality="established", confidence<0.4). The spec-side uncertainty reflects spec silence on branch properties; code-side confirms LLM-dependence of both conditions.

---

### T1 → T6

**Canonical predicates:**
- T1 output: B-branches with `evidence_refs=[]`, `modality=LLM/"hypothesis"`, `scope≠{}`; parent `branch_open=True`
- T6 primary intrinsic: `modality=="hypothesis"` AND `confidence>0.6` AND `status!="supported"` AND `"T6" not in history`
- T6 fallback intrinsic: `modality=="hypothesis"` AND `"T6" not in history`

**Causal necessity test:**
- Counterfactual C(t): a B-branch with `evidence_refs=[]` AND `modality="hypothesis"` AND `confidence>0.6`.
- Without T1, S_k satisfies G_j? No — B-branches only exist due to T1.
- Conclusion: T3 (priority HIGH) fires before T6 (MEDIUM) on ALL T1 B-branches because `evidence_refs==[]` on new branches. The only escape is `modality=="established"`, which blocks T3 but also blocks T6 (T6 requires `modality=="hypothesis"`). There is no state where T6 fires on a T1 B-branch before T3 does. Parent is excluded from focus. T1→T6 is not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T1 creates B-branches with `evidence_refs=[]`. T3 (HIGH) preempts T6 (MEDIUM) on all B-branches because T3 fires whenever `evidence_refs==[]`. Escaping T3 requires `modality=="established"`, which simultaneously blocks T6 (requires `modality=="hypothesis"`). Parent is excluded from focus (branch_open=True). No implication chain leads from T1's output to T6 firing.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: T1 code creates B-branches with `evidence_refs=[]` (default) and `modality` per LLM or "hypothesis". T3 guard (line 1001) fires on `evidence_refs==[]` at priority HIGH (3rd). T6 primary is 6th; T6 fallback is after T9. To avoid T3, need `modality=="established"`; T6 requires `modality=="hypothesis"` — mutually exclusive. Parent excluded from focus per select_focus_claim (line 1063–1071). T1→T6 not-derived on both T1-created claims and parent. Code refs: lines 578–643 (T1), 1001 (T3 guard), 1007–1009 (T6 primary), 1063–1071 (focus exclusion).

**Consistency:** aligned
**Rationale:** Both sides: T3 structurally preempts T6 on T1 B-branches; parent focus-excluded; modality escape ("established") blocks T6 in both spec and code. Phase 1 conservatively classified non-trivial; Phase 2 concludes not-derived.

---

### T1 → T7

**Canonical predicates:**
- T1 output: B-branches with `qualifier={}` (default), `scope≠{}` (guaranteed), `evidence_refs=[]`, `modality=LLM/"hypothesis"`
- T7 intrinsic: `qualifier=={}` AND `scope!={}`

**Causal necessity test:**
- Counterfactual C(t): a B-branch with `qualifier=={}` AND `scope≠{}` AND `modality=="established"` AND `confidence≥0.4` without T1.
- Without T1, S_k satisfies G_j? No — B-branches are T1-exclusive.
- Conclusion: T1's B-branches structurally satisfy T7's guard predicates (`qualifier=={}` always, `scope≠{}` guaranteed). However, T3 preempts T7 (priority HIGH vs LOW) on any branch with `evidence_refs==[]`. For T7 to fire directly, T3 must be blocked via `modality=="established"`. With `modality=="established"`: T3 blocked; T4 blocked (status="hypothesis"≠"underspecified", scope≠{}); T5 blocked if confidence≥0.4; T6 blocked (requires "hypothesis"); T7 fires. State-dependent-causal.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `branch.modality=="established"`, `M(t)`: `branch.confidence≥0.4`]
- uncertainty_flag: spec_underspecified
- Implication chain: T1 spec creates branches with implied `qualifier=={}` (new claims have no qualifier) and non-empty scope. T7 spec guard: "no qualifier + has scope" — structurally satisfied by T1's B-branches. T3 preempts (spec guard: "no evidence + not established"). S_k = {modality=="established" (blocks T3) AND confidence≥0.4 (blocks T5)}. Both are M(t) conditions, spec-silent on branch modality and confidence. State-dependent-causal with M(t) S_k.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `branch.modality=="established"` (LLM-returned, non-default), `M(t)`: `branch.confidence≥0.4` (LLM-returned or ≥0.4 default)]
- Implication chain: B-branches created with `qualifier={}` (Claim default) and `scope≠{}` (lines 580–582). T7 guard (line 1010): `qualifier=={}` AND `scope!={}` — both guaranteed structurally. T3 (line 1001) preempts T7; bypass requires LLM returning `modality="established"`. With `modality="established"` and `confidence≥0.4` (default 0.5 satisfies this): T7 fires. Focus on B-branch depends on E(t). Code refs: lines 578–643 (T1), 580–582 (branch scope), 1001 (T3), 1010 (T7).

**Consistency:** aligned
**Rationale:** Both sides reach state-dependent-causal with the same M(t) S_k (modality="established" LLM return, confidence≥0.4). The default branch confidence (0.5) satisfies the confidence condition; modality="established" is the sole non-default requirement.

---

### T2 → T4

**Canonical predicates:**
- T2 output: `conflict=False`, `evidence_refs` grew (≥1), `status="disputed"` (typical), no scope change
- T4 intrinsic + admissibility: `status=="underspecified"` OR `scope=={}`

**Causal necessity test:**
- Counterfactual C(t): a claim with `conflict=False` AND `scope=={}` existing without T2 firing.
- Without T2, S_k satisfies G_j? Partially — T4 guard (scope=={}) was satisfied before T2 fired, but T2 (CRITICAL, position 2) preempts T4 (HIGH, position 4) while conflict=True. T2 is causally necessary to clear conflict, revealing T4's guard.
- Conclusion: T2's output (conflict=False) removes the T2 preemption; on the next iteration, T3 is blocked (evidence_refs≠[]) and T4 fires. T4's guard (scope=={}) is a pre-existing G(t) condition.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `claim.scope=={}` (pre-existing, unchanged by T2)]
- uncertainty_flag: null
- Implication chain: T2 spec sets claim to "disputed" and clears conflict annotation. T4 spec guard: "scope=={} or underspec." T2's output does not produce scope=={} or underspecified status; it clears conflict. The cascade pattern is T2 unblocking itself via conflict=False, then T4 fires because scope=={} was pre-existing. With S_k: {scope=={}}, T4 guard is satisfied and no higher-priority operator preempts (T3 blocked by evidence_refs≠[]).

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `claim.scope=={}` (pre-existing)]
- Implication chain: T2 code (lines 646–667) sets `claim.conflict=False` (line 664), appends to `evidence_refs` (line 662), sets `status="disputed"`. T4 guard (line 1003): `status=="underspecified" OR scope=={}`. After T2: T1 blocked (not contradicted), T2 blocked (conflict=False), T3 blocked (evidence_refs≠[]), T4 fires if scope=={}. Selection guaranteed: no higher-priority operator preempts T4 in this state. Code refs: lines 646–667 (T2), 1003 (T4 guard).

**Consistency:** aligned
**Rationale:** Both sides: T2 clears conflict (enabling T4 evaluation), T4 fires on pre-existing G(t) condition (scope=={}). Uniform unlock pattern; no spec/code divergence.

---

### T2 → T5

**Canonical predicates:**
- T2 output: `conflict=False`, `evidence_refs` grew, `status="disputed"`, `confidence` unchanged
- T5 intrinsic + admissibility: `status!="contradicted"` AND `confidence<0.4`

**Causal necessity test:**
- Counterfactual C(t): claim with `conflict=False` AND `confidence<0.4` AND `scope≠{}` without T2.
- Without T2, S_k satisfies G_j? Partially — T5 guard was satisfied before T2 (confidence<0.4), but T2 preempted T5. T2 clears conflict, revealing T5's guard.
- Conclusion: state-dependent-causal. T2's output (conflict=False, evidence_refs≠[]) reveals T5's pre-existing guard condition. S_k = {confidence<0.4, scope≠{}, status!="underspecified"} all pre-existing G(t).

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `confidence<0.4`, `G(t)`: `scope≠{}` (prevents T4 preemption)]
- uncertainty_flag: null
- Implication chain: T2 spec clears the conflict flag and marks claim disputed. T5 spec guard: `confidence<0.4`. T2 doesn't change confidence; if confidence<0.4 was present before T2, it remains after. After T2: T3 blocked (evidence_refs≠[]), T4 blocked if scope≠{}, T5 fires. Selection guaranteed given S_k.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `confidence<0.4`, `G(t)`: `scope≠{}`, `G(t)`: `status!="underspecified"`]
- Implication chain: T2 code sets conflict=False (line 664), adds to evidence_refs (line 662). T5 guard (line 1005): `confidence<0.4 AND status!="contradicted"`. After T2: status="disputed" (not contradicted); confidence unchanged (T2 doesn't mutate confidence); T3 blocked (evidence_refs≠[]); T4 blocked (scope≠{}); T5 fires deterministically. Code refs: lines 646–667 (T2), 1005 (T5 guard).

**Consistency:** aligned
**Rationale:** Identical unlock pattern in spec and code. T2 clears conflict; T5's pre-existing confidence<0.4 guard fires. No divergence.

---

### T2 → T6

**Canonical predicates:**
- T2 output: `conflict=False`, `evidence_refs` grew, `status="disputed"`, no modality/confidence change
- T6 primary intrinsic: `modality=="hypothesis"` AND `confidence>0.6` AND `status!="supported"` AND `"T6" not in history`

**Causal necessity test:**
- Counterfactual C(t): claim with `conflict=False`, `modality=="hypothesis"`, `confidence>0.6`, `status="disputed"` without T2.
- Without T2, S_k satisfies G_j? Partially — T6 primary guard satisfied before T2 (modality, confidence, status conditions), but T2 preempted. T2 necessary to clear conflict.
- Conclusion: state-dependent-causal. T2 unlocks T6's pre-existing guard. S_k = {modality=="hypothesis", confidence>0.6, status!="supported", "T6" not in history} — all G(t).

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `modality=="hypothesis"`, `G(t)`: `confidence>0.6`, `G(t)`: `status!="supported"`]
- uncertainty_flag: spec_underspecified
- Implication chain: T2 spec clears conflict. T6 spec guard: "hypothesis + confidence>0.6." If both held before T2, they hold after (T2 doesn't change modality or confidence). After T2: T3 blocked (evidence_refs≠[]), T4 blocked (scope≠{}), T5 blocked (confidence>0.4), T6 fires. Spec-side uncertainty: T6's `status!="supported"` and `"T6" not in history` constraints are spec_silent; under charitable interpretation (status="disputed" counts as not-supported, and T6 hasn't fired), spec-side is state-dependent-causal.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `modality=="hypothesis"`, `G(t)`: `confidence>0.6`, `G(t)`: `status!="supported"`, `G(t)`: `"T6" not in history`]
- Implication chain: T2 sets conflict=False (line 664), adds evidence_refs (line 662). T6 primary guard (line 1007–1009): modality=="hypothesis" AND confidence>0.6 AND status!="supported" AND "T6" not in history. After T2: T3 blocked (evidence_refs≠[]); T4–T5 blocked (confidence>0.6≥0.4, scope≠{}); T6 primary fires. Selection guaranteed given all S_k hold. Code refs: lines 646–667 (T2), 1007–1009 (T6 primary).

**Consistency:** aligned
**Rationale:** Both sides: T2 unlocks T6's pre-existing G(t) conditions. Code-side adds "T6 not in history" to S_k (spec_silent but code-enforced one-time gate). Divergence absent — the extra code S_k is a tightening, not a contradiction.

---

### T2 → T7

**Canonical predicates:**
- T2 output: `conflict=False`, `evidence_refs` grew, no change to `qualifier` or `scope`
- T7 intrinsic: `qualifier=={}` AND `scope!={}`

**Causal necessity test:**
- Counterfactual C(t): claim with `conflict=False`, `qualifier=={}`, `scope≠{}`, `confidence∈[0.4,0.6]` without T2.
- Without T2, S_k satisfies G_j? Partially — T7 guard (qualifier=={}, scope≠{}) satisfied before T2 but T2 preempted. T2 clears conflict enabling T7 evaluation.
- Conclusion: state-dependent-causal. T2 unlocks T7; T4/T5/T6 must not preempt (requiring confidence∈[0.4,0.6] to avoid T5 and T6 primary).

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `qualifier=={}`, `G(t)`: `scope≠{}`, `G(t)`: `confidence∈[0.4,0.6]` (avoiding T5 and T6 primary)]
- uncertainty_flag: spec_underspecified
- Implication chain: T2 clears conflict. T7 spec guard: "no qualifier + has scope." Both pre-exist and T2 doesn't change them. T6 primary must not preempt: requires confidence≤0.6 (or modality≠"hypothesis" or status=="supported"). Under charitable interpretation with confidence∈[0.4,0.6], T7 fires. Spec uncertainty: T6 priority and confidence thresholds are spec_silent; cannot determine from spec alone which of T6 or T7 fires when both guards are met.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `qualifier=={}`, `G(t)`: `scope≠{}`, `G(t)`: `confidence∈[0.4,0.6]` (or `modality!="hypothesis"` or `status=="supported"`, to prevent T6 primary preemption)]
- Implication chain: T2 sets conflict=False (line 664), adds evidence_refs (line 662). T7 guard (line 1010): qualifier=={} AND scope!={} — both unchanged by T2. Priority chain after T2: T3 blocked (evidence_refs≠[]); T4 blocked (scope≠{}); T5 blocked (confidence≥0.4); T6 primary blocked if confidence≤0.6; T7 fires. Selection guaranteed given S_k. Code refs: lines 646–667 (T2), 1007–1009 (T6 primary check), 1010 (T7 guard).

**Consistency:** aligned
**Rationale:** Identical S_k structure on both sides. Spec uncertainty about T6 priority doesn't create a functional divergence — the code-side S_k includes the confidence range condition that spec implies informally.

---

### T2 → T9

**Canonical predicates:**
- T2 output: `conflict=False`, `evidence_refs` grew, `status="disputed"`, no change to `branch_open`
- T9 intrinsic: `branch_open==True` AND `|branches|>0` AND `all branches: status=="supported"`

**Causal necessity test:**
- Counterfactual C(t): a claim with `conflict=True` AND `branch_open=True` that is selectable as focus.
- Without T2, S_k satisfies G_j? Not applicable — the question is whether T2's output enables T9.
- Conclusion: T2 fires on a focusable claim. Claims with `branch_open=True` and branches-not-all-supported are excluded from focus by `select_focus_claim` (lines 1063–1071); they can never receive T2 or any operator. Claims with `branch_open=True` and all branches supported go to `t9_ready` and receive T9 directly, not T2. T2 cannot fire on a branch_open=True parent. After T2 (fires on a regular claim): the claim's `branch_open` stays False (T2 doesn't change it); T9 requires branch_open=True. T2→T9 is not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T2 spec fires on conflict claims. T9 spec guard requires branch_open==True on the claim. T2 does not set branch_open=True. No T2-produced predicate satisfies T9's guard on the same claim. There is no path from T2's spec output to T9's intrinsic.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: `select_focus_claim` (lines 1063–1071) excludes branch_open=True claims from focus unless all branches are supported; if all supported, claim goes to t9_ready and T9 fires — not T2. Thus T2 cannot fire on a branch_open=True parent. T2 fires on branch_open=False claims; T2 does not mutate branch_open. After T2, branch_open=False → T9 guard fails. Not-derived. Code refs: lines 646–667 (T2), 1014–1017 (T9 guard), 1063–1071 (focus exclusion).

**Consistency:** aligned
**Rationale:** Both sides: structural incompatibility — T2 targets branch_open=False claims (branch_open=True parents are focus-excluded); T9 requires branch_open=True. Phase 1 conservative; Phase 2 concludes not-derived.

---

### T3 → T4

**Canonical predicates:**
- T3 output (Path A, C-prefixed): `evidence_refs` grew (≥1); `status="disputed"` if was "unknown"/"hypothesis"; scope unchanged
- T4 intrinsic + admissibility: `status=="underspecified"` OR `scope=={}`

**Causal necessity test:**
- Counterfactual C(t): claim with `evidence_refs≠[]` AND `scope=={}` without T3.
- Without T3, S_k satisfies G_j? Partially — T4 guard (scope=={}) satisfied before T3, but T3 (HIGH, 3rd) preempts T4 (HIGH, 4th) on claims with evidence_refs==[]. T3 clears itself by adding evidence; T4 then fires.
- Conclusion: state-dependent-causal. T3 fires first (higher position), clears evidence_refs==[] condition, then T4 fires on the same claim via scope=={}.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `claim.scope=={}` (pre-existing, unchanged by T3)]
- uncertainty_flag: null
- Implication chain: T3 spec "simulates retrieval," adding evidence. T4 spec guard: "scope=={} or underspec." T3 doesn't produce scope=={} or underspecified status; it clears its own guard (evidence_refs grows). The cascade mechanism is T3 firing, clearing its preemption, then revealing T4's guard. With S_k: {scope=={}}, T4 fires on the next iteration. Selection guaranteed: T3 blocked (evidence_refs≠[]), T4 fires.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `claim.scope=={}` (pre-existing)]
- Implication chain: T3 Path A code (lines 670–685) appends to evidence_refs (line 673) and may set status="disputed". T4 guard (line 1003): `status=="underspecified" OR scope=={}`. After T3: T3 blocked (evidence_refs≠[]); T4 fires if scope=={} (pre-existing, T3 doesn't change scope). Selection guaranteed given S_k. Code refs: lines 670–685 (T3 Path A), 1003 (T4 guard).

**Consistency:** aligned
**Rationale:** Both sides: same unlock pattern. T3 clears its own guard (evidence_refs becomes non-empty), revealing T4's scope=={} condition. Structurally identical to T2→T4.

---

### T3 → T5

**Canonical predicates:**
- T3 output (Path A, C-prefixed): `evidence_refs` grew; confidence unchanged; scope unchanged
- T5 intrinsic + admissibility: `status!="contradicted"` AND `confidence<0.4`

**Causal necessity test:**
- Counterfactual C(t): claim with `evidence_refs≠[]`, `confidence<0.4`, `scope≠{}` without T3.
- Without T3, S_k satisfies G_j? Partially — T5 guard (confidence<0.4) satisfied before T3 fires, but T3 (HIGH) preempts T5 (MEDIUM) when evidence_refs===[]. T3 fires, clears its guard, T5 reveals.
- Conclusion: state-dependent-causal. T3 clears itself; T5 fires if confidence<0.4 and scope≠{} pre-exist.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `confidence<0.4`, `G(t)`: `scope≠{}` (prevents T4 preemption)]
- uncertainty_flag: null
- Implication chain: T3 spec simulates retrieval, growing evidence_refs. T5 spec guard: `confidence<0.4`. T3 doesn't change confidence; if confidence<0.4 existed, it remains. After T3: T3 blocked (evidence_refs≠[]), T4 blocked (scope≠{}), T5 fires. Selection guaranteed given S_k.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `confidence<0.4`, `G(t)`: `scope≠{}`, `G(t)`: `status!="underspecified"`]
- Implication chain: T3 Path A (lines 670–685) appends evidence, may set status="disputed" if prior status was "unknown" or "hypothesis." T3 does not change confidence (Path A: simulate_evidence, lines 458–467, no confidence mutation). After T3: evidence_refs≠[] (T3 blocked); T4 blocked (scope≠{}); T5 guard: confidence<0.4 AND status!="contradicted" — fires if confidence<0.4 pre-existed. Code refs: lines 670–685 (T3 Path A), 458–467 (simulate_evidence, no confidence change), 1005 (T5 guard).

**Consistency:** aligned
**Rationale:** Both sides: T3 clears its own evidence preemption; T5's pre-existing confidence<0.4 condition fires. No divergence.

---

### T3 → T6

**Canonical predicates:**
- T3 output (Path A): `evidence_refs` grew; confidence and modality unchanged
- T6 primary intrinsic: `modality=="hypothesis"` AND `confidence>0.6` AND `status!="supported"` AND `"T6" not in history`

**Causal necessity test:**
- Counterfactual C(t): claim with `evidence_refs≠[]`, `modality=="hypothesis"`, `confidence>0.6`, `status!="supported"` without T3.
- Without T3, S_k satisfies G_j? Partially — T6 guard satisfied before T3 but T3 preempted. T3 clears itself, T6 fires.
- Conclusion: state-dependent-causal. T3 clears its guard (evidence grows); T6's pre-existing G(t) conditions fire next.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `modality=="hypothesis"`, `G(t)`: `confidence>0.6`, `G(t)`: `status!="supported"`]
- uncertainty_flag: spec_underspecified
- Implication chain: T3 spec fires on no-evidence claims, adding evidence. T6 spec guard: "hypothesis + confidence>0.6." T3 doesn't change modality or confidence. After T3: T3 blocked (evidence_refs≠[]), T4/T5 blocked (confidence>0.6≥0.4, scope≠{}), T6 fires. Spec uncertainty: T6's history gate and status!="supported" constraint are spec_silent; under charitable interpretation these are satisfied.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `modality=="hypothesis"`, `G(t)`: `confidence>0.6`, `G(t)`: `status!="supported"`, `G(t)`: `"T6" not in history`]
- Implication chain: T3 Path A (lines 670–685) grows evidence_refs. T6 primary (lines 1007–1009): modality=="hypothesis" AND confidence>0.6 AND status!="supported" AND "T6" not in history. T3 doesn't modify modality, confidence, or history. After T3: T3 blocked; T4/T5 blocked; T6 primary fires. Selection guaranteed. Code refs: lines 670–685 (T3), 1007–1009 (T6 primary).

**Consistency:** aligned
**Rationale:** Both sides: T3 clears evidence preemption; T6's pre-existing conditions fire. Code adds "T6 not in history" to S_k (spec_silent); this is a tightening not a contradiction.

---

### T3 → T7

**Canonical predicates:**
- T3 output (Path A): `evidence_refs` grew; confidence, qualifier, scope unchanged
- T7 intrinsic: `qualifier=={}` AND `scope!={}`

**Causal necessity test:**
- Counterfactual C(t): claim with `evidence_refs≠[]`, `qualifier=={}`, `scope≠{}`, `confidence∈[0.4,0.6]` without T3.
- Without T3, S_k satisfies G_j? Partially — T7 guard satisfied before T3; T3 preempted. T3 clears itself; T7 fires if T4/T5/T6 don't preempt.
- Conclusion: state-dependent-causal. T3 clears evidence preemption; T7 fires if confidence avoids T5 and T6 primary.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `qualifier=={}`, `G(t)`: `scope≠{}`, `G(t)`: `confidence∈[0.4,0.6]`]
- uncertainty_flag: spec_underspecified
- Implication chain: T3 grows evidence. T7 spec guard: "no qualifier + has scope." T3 doesn't change qualifier or scope. After T3: T3 blocked; T4 blocked (scope≠{}); T5 blocked (confidence≥0.4); T6 primary blocked (confidence≤0.6); T7 fires. Spec uncertainty: T6 priority and confidence thresholds are spec_silent; cannot determine from spec whether T6 preempts T7 when both guards might hold.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `qualifier=={}`, `G(t)`: `scope≠{}`, `G(t)`: `confidence∈[0.4,0.6]` (or `modality!="hypothesis"` or `status=="supported"` to avoid T6 primary)]
- Implication chain: T3 Path A grows evidence. T7 guard (line 1010): qualifier=={} AND scope!={} — T3 doesn't modify these. After T3: evidence_refs≠[] (T3 blocked); T4 blocked (scope≠{}); T5 blocked (confidence≥0.4); T6 primary: confidence≤0.6 → blocked; T7 fires. Selection guaranteed given S_k. Code refs: lines 670–685 (T3), 1007–1009 (T6 primary check), 1010 (T7 guard).

**Consistency:** aligned
**Rationale:** Both sides: same unlock pattern. Spec uncertainty about T6 vs T7 priority is resolved by code (confidence range); no functional divergence.

---

### T3 → T8

**Canonical predicates:**
- T3 output (Path B, B-prefixed I2): `status="supported"`, `confidence=0.85` (guaranteed on LLM failure)
- T3 output (Path A, C-prefixed): `evidence_refs` grew; status may become "disputed"; confidence unchanged
- T8 intrinsic + admissibility: `status=="supported"` AND `confidence>0.8`

**Causal necessity test:**
- Counterfactual C(t): a B-branch with `status="supported"`, `confidence=0.85`, `qualifier≠{}` without T3.
- Without T3, S_k satisfies G_j? No — T3 Path B is the only mechanism that sets status="supported" on a B-branch without T7 having fired first (T4 seals parent, not B-branches). T3 is causally necessary.
- Conclusion: T3 Path B (I2 fallback or LLM success) produces status="supported" and confidence=0.85 on a B-branch. T8 requires status="supported" AND confidence>0.8. T7 (qualifier=={} AND scope≠{}) preempts T8 if qualifier=={} on the branch. To avoid T7: need qualifier≠{} pre-existing on the branch. State-dependent-causal code-side; not-derived spec-side (I2 is undocumented_extension).

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: spec_silent
- Implication chain: T3 spec "simulate retrieval" does not describe producing status="supported" on B-branches. The I2 fallback (evaluate_branch_claim, lines 484–486) is classified undocumented_extension in the discrepancy matrix. T3's spec-side output (evidence_refs grew) does not satisfy T8's guard (status="supported" AND confidence>0.8). Spec-side: not-derived because the enabling predicate is entirely absent from spec.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `branch.scope≠{}` (guaranteed for all B-branches), `M(t)`: `branch.qualifier≠{}` (LLM-returned from T1, prevents T7 preemption)]
- Implication chain: T3 Path B fires on B-prefixed claims (line 675–676); `evaluate_branch_claim` (lines 470–486) sets status="supported" and confidence=0.85 on LLM failure (I2, lines 484–486). T8 primary (line 1012– 1013): status=="supported" AND confidence=0.85>0.8 → fires. T7 (line 1010) preempts if qualifier=={}: need S_k = {qualifier≠{}} from T1 LLM output. With qualifier≠{} on the branch: T7 skips, T8 fires. Selection guaranteed given S_k. Code refs: lines 470–486 (evaluate_branch_claim), 675–676 (T3 Path B), 1010 (T7 guard), 1012–1013 (T8 primary).

**Consistency:** divergent
**Rationale:** Code-side has a real cascade mechanism (T3 I2 fallback → status="supported" → T8). Spec-side has no mechanism (I2 is undocumented_extension, absent from canonical spec predicates). This divergence maps to the I2 undocumented_extension finding in `spec_code_discrepancy_matrix_v0-1.md`.

---

### T3 → T9

**Canonical predicates:**
- T3 output (Path B, B-prefixed I2): `status="supported"`, `confidence=0.85`; parent `branch_open=True`
- T9 intrinsic: `branch_open==True` AND `|branches|>0` AND `all branches: status=="supported"`

**Causal necessity test:**
- Counterfactual C(t): parent P with branch_open=True; B_j (last unsupported branch) receives status="supported" from T3 I2; all other branches already supported.
- Without T3, S_k satisfies G_j? Partially — T9 guard requires all branches supported; T3 provides the final status="supported" on B_j. If all other branches were already supported, T3 is the enabling predicate for P becoming T9-ready.
- Conclusion: state-dependent-causal. T3 Path B is causally necessary on code-side; T3 spec output contributes nothing to T9's guard on spec-side.

*(This cell was pre-analyzed in `composition_derivation_check_v0-1.json`. Classifications reproduced here.)*

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`G(t)`: `P.branch_open==True`, `G(t)`: `B_j.parent_id==P.id`, `G(t)`: `all other branches status=="supported"`, `G(t)`: `B_j.status=="supported"` — NOT from T3 spec output; must come from unspecified other source]
- uncertainty_flag: spec_silent
- Implication chain: T3 spec output (evidence_refs grew) contributes nothing to T9's guard. T3 spec has no mechanism to produce status="supported" on B_j (I2 fallback is undocumented_extension). The cascade is formally state-dependent-causal but causally empty at the spec level — T3's spec output is not the enabling predicate; the S_k conditions (including B_j.status="supported") must all come from external sources. Spec-side cascade mechanism is absent.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`G(t)`: `P.branch_open==True` (set by T1), `G(t)`: `B_j.parent_id==P.id`, `G(t)`: `all other branches of P already status=="supported"`, `G(t)`: no interfering C-prefixed claims with parent_id==P.id having status≠"supported"`]
- Implication chain: T3 Path B I2 fallback sets B_j.status="supported" (line 484–486) — the enabling predicate. With S_k (all other branches already supported), P becomes T9-ready. `select_focus_claim` (lines 1073–1074) implements explicit T9-ready priority, guaranteeing P is selected as focus. T9 fires at line 1014–1017. Selection guaranteed by T9-ready priority mechanism. Code refs: lines 470–486 (evaluate_branch_claim), 675–676 (T3 Path B), 1014–1017 (T9 guard), 1063–1077 (select_focus_claim T9-ready priority).

**Consistency:** divergent
**Rationale:** Code-side has a real cascade: T3 I2 provides the enabling status="supported" predicate; T9-ready priority guarantees selection. Spec-side has no mechanism: T3 spec cannot produce status="supported" (I2 is undocumented_extension). Divergence maps to I2 undocumented_extension in `spec_code_discrepancy_matrix_v0-1.md`. Previously analyzed in `composition_derivation_check_v0-1.json`.

---

## 3. Classification Count (Phase 2a)

| Producer | Cell | Spec class | Code class | Consistency |
|----------|------|------------|------------|-------------|
| T1 | →T3 | guard-derived | state-dep-causal | **divergent** |
| T1 | →T5 | state-dep-causal | state-dep-causal | aligned |
| T1 | →T6 | not-derived | not-derived | aligned |
| T1 | →T7 | state-dep-causal | state-dep-causal | aligned |
| T2 | →T4 | state-dep-causal | state-dep-causal | aligned |
| T2 | →T5 | state-dep-causal | state-dep-causal | aligned |
| T2 | →T6 | state-dep-causal | state-dep-causal | aligned |
| T2 | →T7 | state-dep-causal | state-dep-causal | aligned |
| T2 | →T9 | not-derived | not-derived | aligned |
| T3 | →T4 | state-dep-causal | state-dep-causal | aligned |
| T3 | →T5 | state-dep-causal | state-dep-causal | aligned |
| T3 | →T6 | state-dep-causal | state-dep-causal | aligned |
| T3 | →T7 | state-dep-causal | state-dep-causal | aligned |
| T3 | →T8 | not-derived | state-dep-causal | **divergent** |
| T3 | →T9 | state-dep-causal | state-dep-causal | **divergent** |

**Spec-side totals:** guard-derived 1 · state-dep-causal 9 · not-derived 5
**Code-side totals:** state-dep-causal 10 · not-derived 5
**Divergent cells:** T1→T3, T3→T8, T3→T9 (3 of 15)

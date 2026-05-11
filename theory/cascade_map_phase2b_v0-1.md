# DES 9×9 Cascade Map — Phase 2b: T4/T5 Producer Analysis v0.1

**Date:** 2026-05-11
**Branch:** `theory/cascade-map-9x9`
**Phase:** 2b of 3 sub-phases (T4, T5 as producers)
**Predicate baseline:** Amendment Plan v1.1 canonical predicates; code from `des.py`
**Prerequisites:** Phase 1 triage; Phase 2a (T1/T2/T3 producers) complete

---

## 1. Phase 2b Summary

- **Cells analyzed:** 12 (T4→T3/T4/T5/T6/T7; T5→T1/T2/T3/T4/T6/T7/T9)
- **Class distribution (spec-side):** guard-derived 3, state-dependent-causal 4, not-derived 5
- **Class distribution (code-side):** guard-derived 2, state-dependent-causal 5, not-derived 5
- **Spec/code divergences:** 1 cell (T4→T3)
- **Uncertainty flags:** 5 cells
- **Pattern (T4 producer):** T4 creates C-subclaims with evidence_refs=[]; T3 always preempts
  other operators on these subclaims unless modality=="established" (M(t) escape). T4→T6 is
  not-derived (T3/modality mutual exclusion). T4→T4 self-cascade requires scope=={} + modality
  =="established" on subclaim (both M(t)).
- **Pattern (T5 producer):** T5 produces conflict=True (enables T2 guard-derived) and creates
  CC with hardcoded modality="hypothesis" (enables T3 guard-derived). Parent preemption by T1/T2
  blocks T6/T7/T9 cascades. T5→T4 not-derived because T5's priority guard guarantees scope≠{}
  when T5 fires. Five T5→X cells are not-derived.

---

## 2. Per-Cell Analysis

---

### T4 → T3

**Canonical predicates:**
- T4 output: 2–3 new C-prefixed sub-claims with `status="unknown"`, `parent_id=claim.id`,
  `modality=LLM/"hypothesis"` (default), `scope=LLM/{"domain":"general"}` (default non-empty),
  `evidence_refs=[]`, `qualifier={}` (defaults); code: parent `status="supported"`, `sealed=True`
- T3 intrinsic + admissibility: `evidence_refs==[]` AND `modality!="established"`

**Causal necessity test:**
- Counterfactual C(t): a C-subclaim with `evidence_refs=[]` and `modality="hypothesis"` without T4.
- Without T4, S_k satisfies G_j? No — T4 is the exclusive creator of these C-subclaims.
- Conclusion: T4's output creates claims that directly satisfy T3's guard under the default modality.
  Same structural pattern as T1→T3 (creator operator→T3).

**Spec-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: null (guard satisfied under charitable interpretation)
- uncertainty_flag: spec_underspecified
- uncertainty_note: Classification depends on the charitable interpretation that new C-prefixed subclaims default to modality='hypothesis'. Paper 1 Section 3.3 does not specify subclaim modality. Under the alternative interpretation that spec is silent on the modality of created subclaims, this cell would be not-derived (T3's intrinsic guard could not be confirmed satisfied spec-side). The code-side LLM-returned modality (via sc.get('modality', 'hypothesis')) makes this divergent regardless of the spec interpretation choice.
- Implication chain: T4 spec "splits into 2–3 sub-claims" creates new claims with no evidence (`evidence_refs=[]` implied for new claims). T3 spec guard: "no evidence + not established." Under charitable interpretation (sub-claim modality defaults to "hypothesis"), T4's output directly satisfies T3's guard — guard-derived. Spec is silent on sub-claim modality. Parent is excluded from focus (sealed). Selection not_guaranteed: sub-claims compete with other regular claims in E(t) insertion order.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `subclaim.modality != "established"` — `sc.get("modality","hypothesis")`; LLM could return "established"]
- Implication chain: T4 code (lines 725–777) creates subclaims with `modality=sc.get("modality","hypothesis")` (line ~362). LLM could return "established"; if so, T3 guard fails (T3 requires `modality!="established"`). S_k = {M(t): subclaim.modality!="established"} required. With default "hypothesis" (common case), T3 fires on the first focused subclaim. Code-side parent is sealed (line 774: `claim.sealed=True`) and excluded from focus. Code refs: lines 725–777 (T4), 362–369 (subclaim creation), 670–685 (T3), 1001 (T3 guard).

**Consistency:** divergent
**Rationale:** Spec-side guard-derived (charitable: new subclaims default to modality="hypothesis"); code-side state-dependent-causal (LLM modality return is non-deterministic M(t)). Exact same divergence pattern as T1→T3.

---

### T4 → T4

**Canonical predicates:**
- T4 output: C-subclaims with `status="unknown"` (hardcoded), `scope=LLM/{"domain":"general"}`,
  `modality=LLM/"hypothesis"`; parent sealed=True (code)
- T4 intrinsic: `status=="underspecified"` OR `scope=={}`

**Causal necessity test:**
- Counterfactual C(t): a C-subclaim with `scope=={}` AND `modality=="established"` without T4.
- Without T4, S_k satisfies G_j? No — subclaims are T4-exclusive; this is a self-cascade.
- Conclusion: T4's subclaims have `status="unknown"` (hardcoded, never "underspecified"), so
  T4→T4 can only fire if a subclaim has `scope=={}` (LLM-returned non-default). T3 must also
  be blocked (via `modality=="established"`) otherwise T3 preempts T4 at position 3 vs 4.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.scope=={}` (LLM-returned; default {"domain":"general"} non-empty), `M(t)`: `subclaim.modality=="established"` (blocks T3 preemption at position 3)]
- uncertainty_flag: spec_underspecified
- Implication chain: T4 spec creates sub-claims; spec is silent on sub-claim scope and modality. T4 spec guard: "scope=={} or underspec." Since `status="unknown"` (not "underspecified"), T4 can only re-fire if `scope=={}`. T3 (HIGH) preempts T4 (HIGH, position 4) when `evidence_refs==[]`; blocking T3 requires `modality=="established"`. With S_k={scope=={}, modality=="established"}: T3 blocked, T4 fires on the sub-claim. Spec uncertainty: both conditions are spec-silent on sub-claim fields.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.scope=={}` (LLM must return `{}` explicitly; default is `{"domain":"general"}`), `M(t)`: `subclaim.modality=="established"` (LLM-returned non-default)]
- Implication chain: T4 code (lines 362–369) sets subclaim `scope=sc.get("scope",{"domain":"general"})` and `status="unknown"` (hardcoded). T4 guard (line 1003): `scope=={}` OR `status=="underspecified"` — only `scope=={}` is reachable since status is fixed. T3 guard (line 1001): fires on `evidence_refs==[]` if `modality!="established"`. Both M(t) conditions are required. Given S_k, T3 is blocked and T4 fires at position 4. Selection guaranteed. Code refs: lines 725–777 (T4), 362–369 (subclaim creation), 1001 (T3 guard), 1003 (T4 guard).

**Consistency:** aligned
**Rationale:** Both sides require the same two M(t) S_k conditions. Spec-side uncertainty reflects spec silence; code-side confirms LLM-dependence of both scope=={} and modality=="established".

---

### T4 → T5

**Canonical predicates:**
- T4 output: C-subclaims with `status="unknown"`, `confidence=LLM/0.5` (default), `modality=LLM/"hypothesis"`, `scope=LLM/{"domain":"general"}` (typically non-empty)
- T5 intrinsic + admissibility: `status!="contradicted"` AND `confidence<0.4`

**Causal necessity test:**
- Counterfactual C(t): a C-subclaim with `modality=="established"`, `confidence<0.4`, `scope≠{}`.
- Without T4, S_k satisfies G_j? No — subclaims are T4-exclusive.
- Conclusion: T4's default confidence (0.5) exceeds T5's threshold (0.4); LLM must return
  confidence<0.4. T3 preempts T5 unless `modality=="established"`. Default scope={"domain":"general"}
  (non-empty) prevents T4 from re-firing. State-dependent-causal with M(t) S_k.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.modality=="established"` (blocks T3 preemption), `M(t)`: `subclaim.confidence<0.4` (LLM-returned; default 0.5 fails)]
- uncertainty_flag: spec_underspecified
- Implication chain: T4 spec creates sub-claims; spec is silent on sub-claim confidence and modality. T5 spec guard: `confidence<0.4`. Default confidence 0.5 fails; LLM must return <0.4. T3 preempts T5 on `evidence_refs=[]`; blocked by `modality=="established"`. With S_k and default scope≠{} (T4 not re-firing): T5 fires. Selection guaranteed given S_k.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.modality=="established"`, `M(t)`: `subclaim.confidence<0.4`; note `G(t)`: `subclaim.scope≠{}` — typical via default `{"domain":"general"}` but LLM-dependent]
- Implication chain: T4 creates subclaims with `confidence=float(sc.get("confidence",0.5))` and `modality=sc.get("modality","hypothesis")` (lines 366–368). T3 guard (line 1001) preempts T5 (line 1005) unless modality=="established". T4 re-fire (line 1003) preempts T5 only if scope=={}; default scope≠{} prevents this. With S_k, T5 fires. Selection guaranteed. Code refs: lines 725–777 (T4), 362–369 (subclaim fields), 1001 (T3 guard), 1003 (T4 guard), 1005 (T5 guard).

**Consistency:** aligned
**Rationale:** Both sides require the same M(t) S_k pair. Identical to T1→T5 and T4→T7 unlock structure.

---

### T4 → T6

**Canonical predicates:**
- T4 output: C-subclaims with `evidence_refs=[]`, `modality=LLM/"hypothesis"`, `scope≠{}` (default); parent `sealed=True` (code)
- T6 primary intrinsic: `modality=="hypothesis"` AND `confidence>0.6` AND `status!="supported"` AND `"T6" not in history`
- T6 fallback: `modality=="hypothesis"` AND `"T6" not in history`

**Causal necessity test:**
- Counterfactual C(t): any C-subclaim state enabling T6 without T4.
- Without T4, S_k satisfies G_j? Not applicable — structural deadlock shown below.
- Conclusion: T3 (HIGH, position 3) fires on all T4 subclaims with `evidence_refs==[]`. Escaping T3
  requires `modality=="established"`, which simultaneously blocks T6 (both primary and fallback
  require `modality=="hypothesis"`). Parent is sealed (code) and excluded from focus. No implication
  chain exists. Not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T4 creates sub-claims with `evidence_refs=[]`. T3 guard fires first on these (HIGH vs T6's MEDIUM). Escaping T3 requires `modality=="established"`, which blocks T6 (requires `modality=="hypothesis"`) — mutually exclusive. Parent excluded from focus (sealed, code-side; no focus mechanism on sealed claims). Not-derived.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: T4 creates subclaims with `evidence_refs=[]` (Claim default). T3 guard (line 1001) fires at position 3. T6 primary (line 1007–1009) is position 6. Blocking T3 requires `modality=="established"`; both T6 primary and T6 fallback (line 1018–1019) require `modality=="hypothesis"` — mutually exclusive with "established". Parent sealed (`claim.sealed=True`, line 774), excluded from focus. Not-derived. Code refs: lines 725–777 (T4), 774 (parent sealed), 1001 (T3 guard), 1007–1009 (T6 primary).

**Consistency:** aligned
**Rationale:** Structural modality deadlock — identical on both sides. Phase 1 conservative classification; Phase 2 concludes not-derived.

---

### T4 → T7

**Canonical predicates:**
- T4 output: C-subclaims with `qualifier={}` (Claim default), `scope=LLM/{"domain":"general"}` (default non-empty), `evidence_refs=[]`, `modality=LLM/"hypothesis"`
- T7 intrinsic: `qualifier=={}` AND `scope!={}`

**Causal necessity test:**
- Counterfactual C(t): C-subclaim with `qualifier=={}`, `scope≠{}`, `modality=="established"`, `confidence≥0.4`.
- Without T4, S_k satisfies G_j? No — subclaims are T4-exclusive.
- Conclusion: T4's subclaims structurally satisfy T7's guard predicates (`qualifier={}` default,
  `scope≠{}` default). T3 preempts T7 unless `modality=="established"`. With that escape:
  T4 doesn't re-fire (status="unknown", scope≠{}), T5 blocked (confidence≥0.4 default), T6
  blocked (modality≠"hypothesis"). T7 fires. State-dependent-causal.

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.modality=="established"` (blocks T3), `M(t)`: `subclaim.confidence≥0.4` (blocks T5; default 0.5 satisfies)]
- uncertainty_flag: spec_underspecified
- Implication chain: T4 spec creates sub-claims with implied `qualifier={}` (new claims) and non-empty scope. T7 spec guard: "no qualifier + has scope" — structurally satisfied by T4 output. T3 preempts (priority HIGH). S_k = {modality=="established" blocks T3; confidence≥0.4 blocks T5}. Default confidence 0.5 satisfies T5 condition; modality="established" is the sole non-default M(t) requirement. Selection guaranteed given S_k.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: guaranteed
- S_k components: [`M(t)`: `subclaim.modality=="established"` (LLM-returned non-default), `M(t)`: `subclaim.confidence≥0.4` (default 0.5 satisfies)]
- Implication chain: T4 creates subclaims with `qualifier={}` (Claim default) and `scope={"domain":"general"}` (default non-empty, lines 362–369). T7 guard (line 1010): `qualifier=={}` AND `scope!={}` — both satisfied by T4 output. T3 (line 1001) preempts; bypass: LLM returns `modality="established"`. T4 re-fire: status="unknown"≠"underspecified", scope≠{} → T4 skips. T6 blocked (modality≠"hypothesis"). T7 fires. Code refs: lines 725–777 (T4), 362–369 (subclaim defaults), 1001 (T3 guard), 1010 (T7 guard).

**Consistency:** aligned
**Rationale:** Both sides: same M(t) S_k (modality="established", confidence≥0.4). Identical pattern to T1→T7. Default confidence satisfies the T5-blocking condition.

---

### T5 → T1

**Canonical predicates:**
- T5 output: `parent.status ∈ {"contradicted","disputed"}`, `parent.conflict=True`, `parent.confidence≥0.42`; new C-prefixed counter-claim CC with `status="unknown"`, `modality="hypothesis"`, `confidence=LLM/0.6`
- T1 intrinsic: `status=="contradicted"`

**Causal necessity test:**
- Counterfactual C(t): parent with `status="contradicted"`, `conflict=True` without T5 firing.
- Without T5, S_k satisfies G_j? Possible via other paths (e.g., direct input with contradicted status), but in this cascade T5 is the producer — T5's output producing `status="contradicted"` is the enabling predicate.
- Conclusion: state-dependent-causal. T5 produces `status∈{contradicted,disputed}`; T1 fires only
  in the "contradicted" sub-path (S_k1: M(t)). Focus selection on parent (not CC) is an additional
  E(t) condition. *(Pre-analyzed in `composition_derivation_check_v0-1.json`; reformulated below.)*

**Spec-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `check_for_contradiction returns True → parent.status="contradicted"`, `E(t)`: `parent is selected as focus (not CC) in next iteration`]
- uncertainty_flag: null
- Implication chain: T5 spec output: parent.status ∈ {contradicted, disputed} (disjunction). T1 spec guard: `status=="contradicted"`. S_k1 = {status="contradicted"} required — the "disputed" branch fails T1's guard. S_k2 = {parent is selected as focus, not CC} — both claims are in the regular pool; parent precedes CC in insertion order, making it typical[0] in single-claim graphs. Selection not_guaranteed: in multi-claim graphs or if CC is somehow earlier, a different operator fires first.

**Code-side:**
- derivability_class: state-dependent-causal
- selection_status: not_guaranteed
- S_k components: [`M(t)`: `check_for_contradiction(claim, counter) returns True` (LLM-dependent; deterministic in double-LLM-failure sub-path where counter_predicate="does not "+claim.predicate and Fallback 1 fires), `E(t)`: `parent is regular[0] in select_focus_claim (insertion-order)`]
- Implication chain: T5 code (lines 780–843) calls `check_for_contradiction` (lines 404–435); result determines parent.status ("contradicted" or "disputed"). T1 fires at line 997 when status=="contradicted". Parent precedes CC in state.claims insertion order (parent existed before T5 created CC); in single-claim graphs parent = regular[0]. In double-LLM-failure sub-path, S_k1 is guaranteed. Selection not_guaranteed in multi-claim graphs. Code refs: lines 780–843 (T5), 404–435 (check_for_contradiction), 997 (T1 guard), 1063–1071 (select_focus_claim).

**Consistency:** aligned
**Rationale:** Both sides: state-dependent-causal with same S_k structure (M(t) status="contradicted"; E(t) parent focus). Code adds the deterministic double-fallback sub-path detail not visible at spec level, but the classification class is the same.

---

### T5 → T2

**Canonical predicates:**
- T5 output: `parent.conflict=True` (unconditional), `parent.status ∈ {"contradicted","disputed"}`, `parent.confidence≥0.42`
- T2 intrinsic: `conflict==True`

**Causal necessity test:**
- Counterfactual C(t): parent with `conflict=True` without T5. Possible via other paths, but T5
  is the producer here.
- Without T5, S_k satisfies G_j? T5 unconditionally produces `conflict=True` — T2's guard is
  directly satisfied. The question is whether T1 preempts T2.
- Conclusion: guard-derived (O_T5 ⊨ G_T2 since conflict=True is an unconditional T5 output).
  Selection not_guaranteed: T1 fires when status="contradicted" (CRITICAL, position 1 before T2
  position 2), preempting T2 in that sub-path.

**Spec-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: null
- uncertainty_flag: null
- Implication chain: T5 spec output includes setting conflict (implied by "adversarial challenge creates conflict"). T2 spec guard: `conflict==True` — directly implied by T5's canonical output. T5 guarantees conflict=True; T2 guard is satisfied. However, T1 (CRITICAL, position 1) fires before T2 (position 2) when status="contradicted". In the "contradicted" sub-path T1 preempts; in the "disputed" sub-path T2 fires. Selection not_guaranteed because M(t) determines which sub-path.

**Code-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: null
- Implication chain: T5 code (line 457) sets `claim.conflict=True` unconditionally. T2 guard (line 999): `claim.conflict==True` — directly satisfied by T5's output. T1 guard (line 997): `status=="contradicted"` — fires before T2 when T5 produced "contradicted." In "disputed" sub-path (check_for_contradiction=False): T1 skips, T2 fires. Parent is regular[0] in single-claim graph (insertion order). Selection not_guaranteed due to T1 preemption in "contradicted" sub-path. Code refs: lines 780–843 (T5), 457 (conflict=True), 997 (T1 guard), 999 (T2 guard).

**Consistency:** aligned
**Rationale:** Both sides guard-derived: T5 unconditionally produces conflict=True satisfying T2's guard. Selection not_guaranteed on both sides due to T1 preemption in the "contradicted" sub-path. This is the only strict guard-derived cell among the T5-producer cascades.

---

### T5 → T3

**Canonical predicates:**
- T5 output: creates CC with `status="unknown"`, `modality="hypothesis"` (hardcoded), `evidence_refs=[]` (default), `parent_id=claim.id`; parent `status∈{contradicted,disputed}`, `conflict=True`
- T3 intrinsic + admissibility: `evidence_refs==[]` AND `modality!="established"`

**Causal necessity test:**
- Counterfactual C(t): CC with `evidence_refs=[]` and `modality="hypothesis"` without T5.
- Without T5, S_k satisfies G_j? No — CC is T5-exclusive.
- Conclusion: T5 code hardcodes CC.modality="hypothesis"; evidence_refs=[] by Claim default.
  T3's guard is directly satisfied by CC on both spec-side (charitable) and code-side (guaranteed).
  Guard-derived on both sides. Selection requires CC to be selected as focus (not parent).

**Spec-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: null
- uncertainty_flag: spec_underspecified
- uncertainty_note: Spec silent on CC fields (evidence_refs, modality). Charitable: CC has evidence_refs=[] (new claim) and modality!='established'. Under this interpretation, guard-derived. Code confirms modality='hypothesis' is hardcoded.
- Implication chain: T5 spec "adversarial challenge" creates a counter-claim. Spec is silent on CC fields; charitable interpretation: CC has `evidence_refs=[]` (new claim) and `modality≠"established"`. T3 spec guard: "no evidence + not established" — satisfied under charitable interpretation. Guard-derived. Selection not_guaranteed: parent precedes CC in insertion order, so parent is typically focused first (T1 or T2 fires on parent); CC receives focus in a subsequent iteration.

**Code-side:**
- derivability_class: guard-derived
- selection_status: not_guaranteed
- S_k components: null
- Implication chain: T5 code (lines 780–843) creates CC with `modality="hypothesis"` (hardcoded, line ~444), `evidence_refs=[]` (Claim default). T3 guard (line 1001): `evidence_refs==[]` AND `modality!="established"` — both guaranteed by T5's CC creation, no S_k required. Selection not_guaranteed: parent was inserted into state.claims before CC (parent existed when T5 fired); parent is regular[0] in single-claim graphs; T1 or T2 fires on parent first; CC is focused subsequently. Code refs: lines 780–843 (T5), ~444 (CC modality hardcoded), 670–685 (T3), 1001 (T3 guard).

**Consistency:** aligned
**Rationale:** Both sides guard-derived. Key distinction from T1→T3 and T4→T3: T5 hardcodes CC.modality="hypothesis" (code-side guaranteed), whereas T1 and T4 use LLM-returned modality (M(t) uncertainty). Spec-side has uncertainty about CC fields (spec_underspecified) but arrives at the same class.

---

### T5 → T4

**Canonical predicates:**
- T5 output: parent.status ∈ {contradicted,disputed}; CC with `status="unknown"`, `scope=parent.scope.copy()`, `modality="hypothesis"`
- T4 intrinsic: `status=="underspecified"` OR `scope=={}`

**Causal necessity test:**
- Counterfactual C(t): any claim with scope=={} or status="underspecified" after T5.
- Without T5, S_k satisfies G_j? Not applicable — structural analysis shows T4→T4 is not reachable.
- Conclusion: T5 fires only when scope≠{} (T4 has priority HIGH at position 4 and would fire first
  if scope=={}). Therefore when T5 fires, parent.scope≠{} is guaranteed by the priority chain.
  CC.scope=parent.scope.copy()≠{}. Parent.status∈{contradicted,disputed}≠"underspecified". T4
  cannot fire on either parent or CC after T5. Not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T5 spec guard: `confidence<0.4`. T4 guard: "scope=={} or underspec." The select_operation priority chain places T4 (HIGH, position 4) before T5 (MEDIUM, position 5). If scope=={} exists before the iteration, T4 fires instead of T5 — T5 never fires when scope=={}. After T5: parent.scope≠{} (structural invariant), CC.scope=parent.scope≠{}, parent.status∈{contradicted,disputed}≠"underspecified". T4 cannot fire. Not-derived.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: T5 guard (line 1005) fires only after T4 (line 1003) has been checked: `status=="underspecified" OR scope=={}`. If scope=={} holds, T4 fires first; T5 never fires in that state. When T5 fires, scope≠{} is guaranteed by priority chain. T5 code copies scope to CC: `scope=claim.scope.copy()` (line 447) — CC.scope≠{}. parent.status∈{"contradicted","disputed"}≠"underspecified". T4 guard fails on both. Not-derived. Code refs: lines 1003 (T4 guard), 1005 (T5 guard), 780–843 (T5), 447 (CC scope).

**Consistency:** aligned
**Rationale:** Both sides: T5's priority chain invariant guarantees scope≠{} when T5 fires, making T4 unreachable after T5. Phase 1 conservative; Phase 2 concludes not-derived.

---

### T5 → T6

**Canonical predicates:**
- T5 output: parent `status∈{contradicted,disputed}`, `conflict=True`; CC with `status="unknown"`, `modality="hypothesis"`, `evidence_refs=[]`
- T6 primary intrinsic: `modality=="hypothesis"` AND `confidence>0.6` AND `status!="supported"` AND `"T6" not in history`

**Causal necessity test:**
- Counterfactual C(t): any T5 output state that enables T6 on next iteration.
- Without T5, S_k satisfies G_j? Structural deadlock on both parent and CC.
- Conclusion: T1 (position 1) fires on parent when status="contradicted"; T2 (position 2) fires
  when status="disputed"+conflict=True. Both preempt T6 (position 6) on parent. CC has
  evidence_refs=[]→ T3 preempts T6 (position 3 vs 6). Not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: Parent after T5: status∈{contradicted,disputed}. T1 preempts T6 when contradicted (CRITICAL); T2 preempts T6 when conflict=True (CRITICAL). CC has evidence_refs=[], modality="hypothesis"; T3 preempts T6 (HIGH before MEDIUM). No path from T5's output to T6 firing on any T5-created or T5-modified claim.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: Parent: T1 fires (line 997) when status="contradicted"; T2 fires (line 999) when conflict=True+status="disputed". CC: T3 fires (line 1001) on evidence_refs=[]+modality="hypothesis". T6 primary (line 1007–1009) is position 6. No claim in T5's output escapes preemption from T1/T2/T3. Not-derived. Code refs: lines 997 (T1), 999 (T2), 1001 (T3), 1007–1009 (T6 primary).

**Consistency:** aligned
**Rationale:** Both sides: T1/T2 preempt T6 on parent; T3 preempts T6 on CC. Double preemption, no escape path.

---

### T5 → T7

**Canonical predicates:**
- T5 output: parent `conflict=True`, `status∈{contradicted,disputed}`; CC with `qualifier=parent.qualifier.copy()`, `scope=parent.scope.copy()`, `evidence_refs=[]`, `modality="hypothesis"`
- T7 intrinsic: `qualifier=={}` AND `scope!={}`

**Causal necessity test:**
- Counterfactual C(t): any T5 output state where T7 can fire next iteration.
- Without T5, S_k satisfies G_j? Structural deadlock on both parent and CC.
- Conclusion: Parent has conflict=True after T5 → T2 preempts T7 (position 2 vs 7) when
  status="disputed"; T1 preempts when status="contradicted". CC has evidence_refs=[]→ T3
  preempts T7. Not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: Parent: T1 (contradicted) or T2 (conflict=True) fires before T7. CC: T3 fires on evidence_refs=[]; T7 (position 7) cannot fire. T5 spec output (conflict=True) guarantees T2 preemption on parent; evidence_refs=[] guarantees T3 preemption on CC. No path to T7.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: T5 sets `claim.conflict=True` (line 457); T2 guard (line 999) fires before T7 (line 1010) when status="disputed". T5 CC has `evidence_refs=[]`; T3 guard (line 1001) fires before T7. T5 CC modality is hardcoded "hypothesis" — no "established" escape path to block T3. T7 cannot fire on any T5-produced claim state. Not-derived. Code refs: lines 457 (conflict=True), 999 (T2), 1001 (T3), 1010 (T7).

**Consistency:** aligned
**Rationale:** Both sides: T2 preempts T7 on parent (conflict=True); T3 preempts T7 on CC (evidence_refs=[], modality="hypothesis" — no "established" escape since T5 hardcodes "hypothesis"). Not-derived.

---

### T5 → T9

**Canonical predicates:**
- T5 output: parent `branch_open` unchanged (T5 doesn't modify branch_open); CC `branch_open=False` (default); parent `status∈{contradicted,disputed}`
- T9 intrinsic: `branch_open==True` AND `|branches|>0` AND `all branches: status=="supported"`

**Causal necessity test:**
- Counterfactual C(t): any claim with branch_open=True after T5.
- Without T5, S_k satisfies G_j? Not applicable — structural analysis shows no branch_open=True claim can result from T5.
- Conclusion: T5 fires only on branch_open=False claims (branch_open=True parents are excluded
  from focus by select_focus_claim unless t9_ready, in which case T9 fires directly). T5 does
  not mutate branch_open. CC.branch_open=False (default). After T5: no claim has newly acquired
  branch_open=True from T5's output. Not-derived.

**Spec-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- uncertainty_flag: null
- Implication chain: T5 spec output does not include branch_open=True on any claim. T9 spec guard requires branch_open=True. T5 fires on branch_open=False claims (branch_open=True parents are focus-excluded). No T5 output predicate satisfies T9's guard. Not-derived.

**Code-side:**
- derivability_class: not-derived
- selection_status: not_applicable
- S_k components: null
- Implication chain: select_focus_claim (lines 1063–1071) excludes branch_open=True parents from focus unless all children supported; if all supported, T9 fires directly (t9_ready priority, not T5). T5 fires on branch_open=False claims; T5 does not mutate branch_open (lines 780–843 show no branch_open assignment). CC has branch_open=False by default. T9 guard (lines 1014–1017) requires branch_open=True. Not-derived. Code refs: lines 780–843 (T5), 1014–1017 (T9 guard), 1063–1071 (focus exclusion).

**Consistency:** aligned
**Rationale:** Both sides: T5 cannot fire on branch_open=True claims (focus exclusion); T5 does not produce branch_open=True. Structurally identical to T2→T9 conclusion.

---

## 3. Classification Summary (Phase 2b)

| Producer | Cell | Spec class | Code class | Consistency |
|----------|------|------------|------------|-------------|
| T4 | →T3 | guard-derived | state-dep-causal | **divergent** |
| T4 | →T4 | state-dep-causal | state-dep-causal | aligned |
| T4 | →T5 | state-dep-causal | state-dep-causal | aligned |
| T4 | →T6 | not-derived | not-derived | aligned |
| T4 | →T7 | state-dep-causal | state-dep-causal | aligned |
| T5 | →T1 | state-dep-causal | state-dep-causal | aligned |
| T5 | →T2 | guard-derived | guard-derived | aligned |
| T5 | →T3 | guard-derived | guard-derived | aligned |
| T5 | →T4 | not-derived | not-derived | aligned |
| T5 | →T6 | not-derived | not-derived | aligned |
| T5 | →T7 | not-derived | not-derived | aligned |
| T5 | →T9 | not-derived | not-derived | aligned |

**Spec-side totals:** guard-derived 3 · state-dependent-causal 4 · not-derived 5
**Code-side totals:** guard-derived 2 · state-dependent-causal 5 · not-derived 5
**Divergent cells:** T4→T3 (1 of 12)

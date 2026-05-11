# DES 9×9 Cascade Map v0.1

**Date:** 2026-05-11
**Branch:** `theory/cascade-map-9x9`
**Sources:** Phase 1 triage + Phase 2a/2b/2c non-trivial analysis
**Predicate baseline:** Amendment Plan v1.1 canonical predicates; code from `des.py`

---

## 1. Legend

| Symbol | Meaning |
|--------|-------|
| `—` | Trivial not-derived (Phase 1): incompatibility demonstrable in one sentence |
| `ND` | Not-derived (Phase 2 confirmed): non-trivial analysis concluded no implication chain |
| `SD` | State-dependent-causal: (O_i ∧ S_k) ⊨ G_j; additional state condition S_k required |
| `GD` | Guard-derived: O_i ⊨ G_j but selection not guaranteed |
| `ST` | Strict-derived: O_i ⊨ G_j AND Σ guarantees T_j selection |
| `D` | Divergent (superscript): spec-side and code-side classifications differ |

**Divergence notation:** `D[spec/code]` where classes are abbreviated:
`ND`=not-derived, `GD`=guard-derived, `SD`=state-dep-causal, `ST`=strict-derived.
`D[SD/SD*]` = same class but material divergence in S_k attribution or selection_status.

Cells marked with `†` are non-trivial cells that confirmed not-derived after full analysis.

---

## 2. 9×9 Matrix

Rows = producer (T_i); columns = receiver (T_j).

|  | **T1** | **T2** | **T3** | **T4** | **T5** | **T6** | **T7** | **T8** | **T9** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **T1** | `—` | `—` | `D[GD/SD]` | `—` | `SD` | `ND`† | `SD` | `—` | `—` |
| **T2** | `—` | `—` | `—` | `SD` | `SD` | `SD` | `SD` | `—` | `ND`† |
| **T3** | `—` | `—` | `—` | `SD` | `SD` | `SD` | `SD` | `D[ND/SD]` | `D[SD/SD*]` |
| **T4** | `—` | `—` | `D[GD/SD]` | `SD` | `SD` | `ND`† | `SD` | `—` | `—` |
| **T5** | `SD` | `GD` | `GD` | `ND`† | `—` | `ND`† | `ND`† | `—` | `ND`† |
| **T6** | `—` | `—` | `—` | `—` | `—` | `—` | `SD` | `D[ND/SD]` | `D[ND/SD]` |
| **T7** | `—` | `—` | `—` | `—` | `—` | `SD` | `—` | `D[SD/SD*]` | `SD` |
| **T8** | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `—` |
| **T9** | `—` | `—` | `—` | `—` | `—` | `—` | `—` | `GD` | `—` |

---

## 3. Per-Cell Detail Table

### Non-trivial cells (34 total)

| Cell | Phase | Spec class | Code class | Sel (spec/code) | Consistency | Key S_k / Note |
|------|-------|-----------|-----------|------------------|-------------|----------------|
| T1→T3 | 2a | guard-derived† | state-dep-causal | ng / ng | **divergent** | Spec: charitable modality='hypothesis' (†spec_underspecified: kwarg default, not spec commitment); Code: LLM may return 'established' |
| T1→T5 | 2a | state-dep-causal | state-dep-causal | ng / ng | aligned | S_k: branch.modality='established' + confidence<0.4 (both M(t)) |
| T1→T6 | 2a | not-derived | not-derived | n/a / n/a | aligned | T3/T6 mutual exclusion via modality |
| T1→T7 | 2a | state-dep-causal | state-dep-causal | ng / ng | aligned | S_k: branch.modality='established' + confidence≥0.4 |
| T2→T4 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: scope=={} (G(t)); T2 unlock pattern |
| T2→T5 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: confidence<0.4, scope!={} (G(t)); T2 unlock |
| T2→T6 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: modality='hypothesis', confidence>0.6, status!='supported' (G(t)) |
| T2→T7 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: qualifier=={}, scope!={}, confidence∈[0.4,0.6] (G(t)) |
| T2→T9 | 2a | not-derived | not-derived | n/a / n/a | aligned | Structural: T2 targets branch_open=False; T9 requires branch_open=True |
| T3→T4 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: scope=={} (G(t)); T3 unlock pattern (mirrors T2→T4) |
| T3→T5 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: confidence<0.4, scope!={} (G(t)) |
| T3→T6 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: modality='hypothesis', confidence>0.6, status!='supported' (G(t)) |
| T3→T7 | 2a | state-dep-causal | state-dep-causal | g / g | aligned | S_k: qualifier=={}, scope!={}, confidence∈[0.4,0.6] (G(t)) |
| T3→T8 | 2a | not-derived | state-dep-causal | n/a / g | **divergent** | I2 undocumented_extension absent from spec; code T3 Path B enables T8 |
| T3→T9 | 2a | state-dep-causal | state-dep-causal | ng / g | **divergent** | Same class; spec S_k includes B.status='supported' from external source; code T3 I2 is causal enabler |
| T4→T3 | 2b | guard-derived† | state-dep-causal | ng / ng | **divergent** | †spec_underspecified: same as T1→T3; subclaim modality='hypothesis' is kwarg default, not spec commitment |
| T4→T4 | 2b | state-dep-causal | state-dep-causal | g / g | aligned | S_k: scope=={} + modality='established' on subclaim (both M(t)) |
| T4→T5 | 2b | state-dep-causal | state-dep-causal | g / g | aligned | S_k: subclaim.modality='established' + confidence<0.4 (both M(t)) |
| T4→T6 | 2b | not-derived | not-derived | n/a / n/a | aligned | T3/T6 mutual exclusion (same as T1→T6) |
| T4→T7 | 2b | state-dep-causal | state-dep-causal | g / g | aligned | S_k: subclaim.modality='established' + confidence≥0.4 (M(t)) |
| T5→T1 | 2b | state-dep-causal | state-dep-causal | ng / ng | aligned | S_k: check_for_contradiction returns True → status='contradicted' (M(t)) |
| T5→T2 | 2b | guard-derived | guard-derived | ng / ng | aligned | T5 unconditionally sets conflict=True; T2 guard directly satisfied |
| T5→T3 | 2b | guard-derived | guard-derived | ng / ng | aligned | T5 hardcodes CC.modality='hypothesis'; T3 guard on CC directly satisfied |
| T5→T4 | 2b | not-derived | not-derived | n/a / n/a | aligned | T5 priority invariant: T5 fires only when scope!={} → T4's scope=={} impossible |
| T5→T6 | 2b | not-derived | not-derived | n/a / n/a | aligned | T5 sets conflict=True; T2 CRITICAL preempts T6 |
| T5→T7 | 2b | not-derived | not-derived | n/a / n/a | aligned | T5 sets conflict=True; T2 CRITICAL preempts T7 |
| T5→T9 | 2b | not-derived | not-derived | n/a / n/a | aligned | T5 sets conflict=True; T2 preempts all; T9 requires branch_open=True |
| T6→T7 | 2c | state-dep-causal | state-dep-causal | g / g | aligned | S_k: qualifier=={} pre-T6 (E(t)); spec: T6 history gate + evidence growth sufficient; T7 fires at pos 7 |
| T6→T8 | 2c | not-derived | state-dep-causal | n/a / g | **divergent** | Spec: T6 spec output = evidence_refs grew only; (code:) status='supported'+confidence>=0.82 absent — not-derived. Code: S_k={qualifier!={}}, T8 primary fires |
| T6→T9 | 2c | not-derived | state-dep-causal | n/a / ng | **divergent** | Spec: T6 spec doesn't produce status='supported'; T9 branch guard unmet — not-derived. Code: S_k={branch_open, all_other_children_supported}, state-dep-causal |
| T7→T6 | 2c | state-dep-causal | state-dep-causal | ng / ng | aligned | S_k: modality='hypothesis', 'T6' not in history, confidence∈(0.35,0.60] pre-T7 |
| T7→T8 | 2c | state-dep-causal | state-dep-causal | g / g | **divergent** | Spec: S_k={status='supported', confidence>0.8 pre-T7}; T7 qualifier output causally irrelevant to T8. Code: S_k={confidence∈(0.75,0.80]}; T7 confidence boost +0.05 is enabling predicate. Drei-Fall |
| T7→T9 | 2c | state-dep-causal | state-dep-causal | g / g | aligned | S_k: branch_open=True, all_children_supported; T7 preempts T9 once, then T9 fires |
| T9→T8 | 2c | guard-derived | guard-derived | ng / g | aligned | O_T9 ⊨ G_T8 definitionally (status='supported', confidence≥0.82). Spec: sel ng (focus pool timing). Code: synthesis bypass pos-0, sel guaranteed given O_T9 success. Per Correction Note |

**Selection status key:** `g` = guaranteed, `ng` = not_guaranteed, `n/a` = not_applicable

---

## 4. Summary Statistics

### 4.1 Non-trivial cells: spec-side class distribution

| Class | Count | Cells |
|-------|-------|-------|
| strict-derived | 0 | — |
| guard-derived | 5 | T1→T3†, T4→T3†, T5→T2, T5→T3, T9→T8 |
| state-dependent-causal | 19 | T1→T5/T7; T2→T4/T5/T6/T7; T3→T4/T5/T6/T7/T9; T4→T4/T5/T7; T5→T1; T6→T7; T7→T6/T8/T9 |
| not-derived (confirmed) | 10 | T1→T6; T2→T9; T3→T8; T4→T6; T5→T4/T6/T7/T9; T6→T8; T6→T9 |

†spec_underspecified: guard-derived under charitable interpretation; modality='hypothesis' is a Python kwarg default, not a spec-level commitment.

### 4.2 Non-trivial cells: code-side class distribution

| Class | Count | Cells |
|-------|-------|-------|
| strict-derived | 0 | — |
| guard-derived | 3 | T5→T2, T5→T3, T9→T8 |
| state-dependent-causal | 24 | (all non-trivial except 7 not-derived and 3 guard-derived) |
| not-derived (confirmed) | 7 | T1→T6; T2→T9; T4→T6; T5→T4/T6/T7/T9 |

### 4.3 Divergent cells

| Cell | Spec | Code | Divergence type | Root cause |
|------|------|------|-----------------|------------|
| T1→T3 | guard-derived | state-dep-causal | class_mismatch | Spec silent on branch modality; charitable vs LLM-dependent |
| T3→T8 | not-derived | state-dep-causal | class_mismatch | T3 I2 fallback (undocumented_extension) absent from spec |
| T3→T9 | SD, ng | SD, guaranteed | selection_status + S_k | I2 is causal enabler code-side; spec-side cascade causally empty |
| T4→T3 | guard-derived | state-dep-causal | class_mismatch | Same as T1→T3; spec silent on subclaim modality |
| T6→T8 | not-derived | state-dep-causal | class_mismatch | T6 (code:) status='supported'+confidence>=0.82 absent from spec; T8 spec intrinsic unreachable |
| T6→T9 | not-derived | state-dep-causal | class_mismatch | Same root cause as T6→T8; (code:) status predicate enables T9 code-side only |
| T7→T8 | SD, confidence>0.8 pre-T7 | SD, confidence∈(0.75,0.80] | S_k + causal mechanism | Spec: T7 qualifier output irrelevant to T8; Code: T7 confidence boost +0.05 is enabling predicate. Drei-Fall |

### 4.4 D-membership, SAR, Divergence Density

**D-membership rule:** strict-derived, guard-derived, state-dependent-causal ∈ D; not-derived ∉ D. Uncertainty flags (spec_underspecified) do not affect D-membership.

| Metric | Value | Formula |
|--------|-------|---------|
| Spec D-members | 24 | 5 GD + 19 SD |
| Code D-members | 27 | 3 GD + 24 SD |
| **SAR** (Specification-Alignment Ratio) | **1.125** | code_D / spec_D = 27/24 |
| **DD** (Divergence Density) | **20.6%** | divergent / non_trivial = 7/34 |

Interpretation: SAR=1.125 indicates a modest coverage asymmetry (code reaches 12.5% more claim pairs than spec). DD=20.6% indicates that mechanism asymmetry (how cascades work) is more significant than the coverage gap alone. The Drei-Fall sample was biased toward divergent cases; the full 9×9 map shows that most divergences (4 of 7) are class-mismatch from spec-silent modality or undocumented T3/T6 code extensions.

### 4.5 Trivial not-derived cells (47)

All `—` cells in the matrix. The most structurally significant trivial groups:

- **All T8 rows (9 cells):** T8 seals claims and creates no new claims; sealed claims are excluded from focus by `select_focus_claim` (line 1064), making any downstream cascade impossible from T8.
- **All T9→X except T9→T8 (8 cells):** T9 creates an `is_synthesis=True` synthesis claim captured immediately by T8 synthesis bypass; all non-synthesis outputs of T9 (sealed parent) are excluded from focus.
- **T1→T1/T2/T4/T8/T9; T2→T1/T2/T3/T8; T3→T1/T2/T3 (13 cells):** Self-cascade blocks or direct guard violations.

---

## 5. Structural Observations

### 5.1 The unlock pattern (T2, T3 as producers)

T2 and T3 each clear their own intrinsic guard condition:
- T2: clears `conflict=True` → reveals downstream T4/T5/T6/T7 conditions
- T3: clears `evidence_refs==[]` → reveals downstream T4/T5/T6/T7 conditions

This produces 4 near-parallel cells in each producer row (→T4, →T5, →T6, →T7), all state-dependent-causal with identical S_k patterns.

### 5.2 T3/T6 modality mutual exclusion

Cells T1→T6, T4→T6 are not-derived because:
- Escaping T3 preemption requires `modality='established'`
- T6 requires `modality='hypothesis'`
- These are mutually exclusive: no single state satisfies both

This is the modality deadlock identified in the spec/code discrepancy analysis.

### 5.3 T7 qualifier-setter enabling three cascades

T7 unconditionally sets `qualifier≠{}`. This single output:
- Enables T6 (fallback): removes T7's own position-7 preemption of T6-fallback (→T6)
- Enables T8: completes T8 primary's `NOT(qualifier=={} AND scope!={})` guard (→T8)
- Enables T9: clears T7 preemption, allowing T9 to fire one iteration later (→T9)

### 5.4 T9→T8 as guard-derived (no strict-derived cells in 9×9 map)

T9 creates a synthesis claim satisfying T8's requirements. O_T9 ⊨ G_T8 definitionally — `status='supported'` and `confidence≥0.82` directly satisfy T8's guard without any additional state condition S_k. This makes T9→T8 **guard-derived** (both sides), not state-dep-causal. The prior SP-3 Type D classification confused the selection condition (synthesis claim must be focused, an E(t) timing condition) with an admissibility condition. Admissibility and selection are distinct: G_j satisfaction is a property of O_T9's output; selection timing is governed by Σ. Spec-side: selection not_guaranteed (E(t) focus timing). Code-side: synthesis bypass at position 0 guarantees selection given O_T9 success. There are no strict-derived cells in the 9×9 map.

### 5.5 I2 undocumented_extension (T3 Path B)

The T3 I2 fallback (`status='supported'`, `confidence=0.85` on LLM failure for B-prefixed claims) is the root cause of two divergent cells (T3→T8, T3→T9). At spec level, T3 does not produce `status='supported'`; at code level, I2 does. This makes T3 an effective enabler of T8 and T9 at the code layer in a way entirely absent from the specification.

### 5.6 T5→T2 and T5→T3 as code-side guard-derived via hardcoding

T5 produces two guard-derived cascades at the code level:
- `conflict=True` (hardcoded, unconditional) → T2 guard directly satisfied
- `CC.modality='hypothesis'` (hardcoded at line ~444) → T3 guard on counter-claim directly satisfied

This contrasts with T1 and T4, where the equivalent modality field is LLM-returned (`b.get("modality","hypothesis")`), making those cascades state-dependent-causal at the code layer.

### 5.7 T6 (code:) output divergence pattern (T6→T8, T6→T9)

Canonical predicates for T6 mark `status='supported'` and `confidence≥0.82` as `(code:)` — excluded from spec-side analysis. T6 spec output is `evidence_refs grew` only. This causes T6→T8 and T6→T9 to be spec-not-derived (T8 intrinsic and T9 branch guard both require `status='supported'`) while code-side both are state-dep-causal. T6→T7 remains aligned: the spec-side mechanism (history gate + evidence growth) is sufficient to enable T7, and T8 spec-side remains blocked (status not produced by T6 spec).

### 5.8 T7→T8 Drei-Fall divergence

T7→T8 is divergent with identical derivability class (state-dep-causal) but different S_k and causal mechanism. Spec-side: T7 qualifier output is causally irrelevant to T8's guard (status='supported' AND confidence>0.8); S_k requires confidence>0.8 pre-T7 as a pre-existing condition. Code-side: T7 confidence boost (+0.05) is the enabling predicate in the narrow channel confidence∈(0.75,0.80]; without the boost, T8 primary would not fire. Documented as the canonical divergent cascade in `composition_derivation_check_v0-1.json`.

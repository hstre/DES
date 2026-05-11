# DES 9×9 Cascade Map — Phase 1 Triage v0.1

**Date:** 2026-05-11
**Branch:** `theory/cascade-map-9x9`
**Phase:** 1 of 3 (Triage only)
**Predicate baseline:** Amendment Plan v1.1 canonical predicates

---

## 1. Summary

- **47 trivial-not-derived** cells: intrinsic-predicate incompatibility demonstrable in one sentence
- **34 non-trivial** cells: require full Pass-2 analysis
- All 81 cells classified; diagonal (self-cascade) cells included
- Triage is conservative (Rule 5): when in doubt, classified non-trivial
- T8 row is entirely trivial (T8 seals the claim and creates no new claims)
- T9 row has one non-trivial cell (T9→T8 via synthesis-claim bypass)

---

## 2. Triage Matrix

Rows = producer T_i; Columns = receiver T_j.  
**T** = trivial-not-derived; **N** = non-trivial (Pass 2 required)

|     | →T1 | →T2 | →T3 | →T4 | →T5 | →T6 | →T7 | →T8 | →T9 |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| T1→ |  T  |  T  |  N  |  T  |  N  |  N  |  N  |  T  |  T  |
| T2→ |  T  |  T  |  T  |  N  |  N  |  N  |  N  |  T  |  N  |
| T3→ |  T  |  T  |  T  |  N  |  N  |  N  |  N  |  N  |  N  |
| T4→ |  T  |  T  |  N  |  N  |  N  |  N  |  N  |  T  |  T  |
| T5→ |  N  |  N  |  N  |  N  |  T  |  N  |  N  |  T  |  N  |
| T6→ |  T  |  T  |  T  |  T  |  T  |  T  |  N  |  N  |  N  |
| T7→ |  T  |  T  |  T  |  T  |  T  |  N  |  T  |  N  |  N  |
| T8→ |  T  |  T  |  T  |  T  |  T  |  T  |  T  |  T  |  T  |
| T9→ |  T  |  T  |  T  |  T  |  T  |  T  |  T  |  N  |  T  |

---

## 3. Trivial Cells — One-Sentence Rationales

Format: `T_i → T_j: <rationale citing failed predicate>`

### T1 row

**T1 → T1:** T1 outputs `claim.status = "disputed"` (line 638); T1's intrinsic requires `status == "contradicted"`, which T1's own output immediately violates.

**T1 → T2:** T1 sets `claim.conflict = False` on the parent (line 639) and creates branches with default `conflict = False`; T2 requires `conflict == True`, which no T1 output produces.

**T1 → T4:** T1 creates branch claims with non-empty `scope` (branch_scope is always non-empty per lines 580–582: defaults to `{"domain": claim.subject[:30]}` when parent scope is empty) and `status = "hypothesis"`, satisfying neither `scope == {}` nor `status == "underspecified"` of T4's intrinsic.

**T1 → T8:** T1 sets `claim.status = "disputed"` on the parent and `status = "hypothesis"` on branches; T8 requires `status == "supported"`, which no T1 output produces.

**T1 → T9:** T1 creates branches with `status = "hypothesis"`, not `"supported"`; T9 requires `all branches: status == "supported"`, which is not satisfied immediately after T1.

### T2 row

**T2 → T1:** T2 outputs `claim.status = "disputed"` (line 663); T1 requires `status == "contradicted"`, which T2 does not produce.

**T2 → T2:** T2 outputs `claim.conflict = False` (line 664); T2's own intrinsic requires `conflict == True`, blocking self-cascade.

**T2 → T3:** T2 appends `"[CONFLICT] ..."` to `claim.evidence_refs` (line 662), making it non-empty; T3 requires `evidence_refs == []`, which T2's output violates on the same claim, and T2 creates no new claims.

**T2 → T8:** T2 outputs `claim.status = "disputed"` (line 663); T8 requires `status == "supported"`, which T2 does not produce.

### T3 row

**T3 → T1:** T3 outputs `claim.status = "disputed"` (non-B path, line 680) or `"supported"` (B-prefixed I2 path, line 484–485); T1 requires `status == "contradicted"`, which T3 does not produce on any path.

**T3 → T2:** T3 fires only when `claim.conflict == False` (T2 at line 999 has higher priority and fires first when `conflict == True`); T3 does not set `conflict = True`; T2 requires `conflict == True`.

**T3 → T3:** T3 appends simulated evidence to `claim.evidence_refs` (line 673), making it non-empty, and creates no new claims; T3's own intrinsic requires `evidence_refs == []`, which is violated on the same claim after T3.

### T4 row

**T4 → T1:** T4 creates sub-claims with `status = "unknown"` (line 766) and seals the parent as `status = "supported"` (code I1, line 773); T1 requires `status == "contradicted"`, which no T4 output produces.

**T4 → T2:** T4 does not set `conflict = True` on any claim (neither parent nor sub-claims receive `conflict = True`); T2 requires `conflict == True`.

**T4 → T8:** T4 creates sub-claims with `status = "unknown"` and seals the parent itself (I1: lines 773–774, `claim.status = "supported"` and `claim.sealed = True`); T8 requires `status == "supported"` on an unsealed, focusable claim, which no T4 output produces.

**T4 → T9:** T4 does not set `branch_open = True` on any claim; T9 requires `branch_open == True`.

### T5 row

**T5 → T5:** T5 boosts `claim.confidence` to `max(claim.confidence, 0.42)` on its target (line 839) and creates a counter-claim with `confidence = 0.6` (line 805); T5's admissibility requires `confidence < 0.4`, which neither output satisfies.

**T5 → T8:** T5 outputs `claim.status ∈ {"contradicted", "disputed"}` on the target and `status = "unknown"` on the counter-claim; T8 requires `status == "supported"`, which no T5 output produces.

### T6 row

**T6 → T1:** T6 outputs `claim.status = "supported"` (line 868); T1 requires `status == "contradicted"`, which T6 does not produce.

**T6 → T2:** T6 fires only when `claim.conflict == False` (T2 at line 999 has higher priority and fires first when `conflict == True`); T6 does not set `conflict = True`; T2 requires `conflict == True`.

**T6 → T3:** T6 adds to `claim.evidence_refs` (lines 864–865) and creates no new claims; T3 requires `evidence_refs == []`, which is violated on the same claim after T6.

**T6 → T4:** T6 fires only when `claim.scope != {}` (T4 at line 1003 has higher priority and fires first when `scope == {}`); T6 does not change `scope`; after T6, `scope` remains non-empty and `status = "supported" ≠ "underspecified"`, so T4's intrinsic fails.

**T6 → T5:** T6 outputs `claim.confidence >= 0.82` (line 869); T5's admissibility requires `confidence < 0.4`, which T6's output strictly violates.

**T6 → T6:** T6 appends `"T6"` to `claim.history` (line 870); T6's shared admissibility condition requires `"T6" not in claim.history`, blocking self-cascade.

### T7 row

**T7 → T1:** T7 fires only when `claim.status != "contradicted"` (T1 at line 997 has higher priority and fires first when `status == "contradicted"`); T7 does not change `status`; after T7, `status` remains non-contradicted, so T1's intrinsic fails.

**T7 → T2:** T7 fires only when `claim.conflict == False` (T2 at line 999 has higher priority and fires first when `conflict == True`); T7 does not set `conflict`; T2 requires `conflict == True`.

**T7 → T3:** T7 fires only when `claim.evidence_refs != []` (T3 at line 1001 has higher priority and fires first when `evidence_refs == []`); T7 does not modify `evidence_refs`; T3 requires `evidence_refs == []`, which cannot hold when T7 fires.

**T7 → T4:** T7 requires `claim.scope != {}` as its own intrinsic (line 1010); T4 at line 1003 has higher priority and fires first when `scope == {}`; T7 does not change `scope`; after T7, `scope` remains non-empty and `status` is unchanged, so T4's intrinsic fails.

**T7 → T5:** T7 fires only when `claim.confidence >= 0.4` (T5 at line 1005 has higher priority and fires first when `confidence < 0.4`); T7 boosts `confidence` by `+0.05` (line 893); after T7, `confidence >= 0.45`, violating T5's admissibility of `confidence < 0.4`.

**T7 → T7:** T7 outputs `claim.qualifier != {}` (lines 890–892); T7's own intrinsic requires `qualifier == {}`, blocking self-cascade.

### T8 row (all trivial)

**T8 → T1 through T8 → T9 (all 9 cells):** T8 sets `claim.sealed = True` (line 901) and creates no new claims; sealed claims are excluded from focus selection by `select_focus_claim` (line 1064: `if claim.sealed ... continue`), so no operator can subsequently fire on account of T8's output.

*(Individual entries for JSON: T8→T1, T8→T2, T8→T3, T8→T4, T8→T5, T8→T6, T8→T7, T8→T8, T8→T9 all carry the same rationale with the same citation.)*

### T9 row

**T9 → T1:** T9 seals the parent (`claim.sealed = True`, line 978) and creates a synthesis claim with `status = "supported"` and `is_synthesis = True`; T1 requires `status == "contradicted"`, which no T9 output produces.

**T9 → T2:** T9 seals the parent and creates a synthesis claim with `conflict = False` (default); T2 requires `conflict == True`, which no T9 output produces.

**T9 → T3:** T9's synthesis claim has non-empty `evidence_refs` (two synthesis notes appended at lines 972–974); T3 requires `evidence_refs == []`.

**T9 → T4:** T9's synthesis claim has `is_synthesis = True`, triggering the synthesis bypass (`return "T8", t8_seal_claim` at lines 995–996) before T4 (at line 1003) can be evaluated; T4 cannot fire on the synthesis claim.

**T9 → T5:** T9's synthesis claim has `confidence >= 0.82` (line 947 / 954); T5's admissibility requires `confidence < 0.4`, which the synthesis claim violates; the parent is sealed.

**T9 → T6:** T9's synthesis claim has `modality = "suggestion"` (line 964); T6 requires `modality == "hypothesis"`, which the synthesis claim does not satisfy.

**T9 → T7:** T9's synthesis claim has `is_synthesis = True`, triggering the synthesis bypass (lines 995–996) before T7 (at line 1010); T7 cannot fire on the synthesis claim; the parent is sealed.

**T9 → T9:** T9 seals the parent (the only `branch_open = True` claim in this cascade); the synthesis claim has `is_synthesis = True` and is immediately caught by the T8 synthesis bypass; no claim with `branch_open = True` is produced by T9.

---

## 4. Non-Trivial Cells — Phase 2 Targets

These 34 cells require full Pass-2 analysis (derivability classification, selection_status, S_k component typing, spec-side and code-side separately).

Grouped by producer:

**T1 (4):** T1→T3, T1→T5, T1→T6, T1→T7

**T2 (5):** T2→T4, T2→T5, T2→T6, T2→T7, T2→T9

**T3 (6):** T3→T4, T3→T5, T3→T6, T3→T7, T3→T8, T3→T9

**T4 (5):** T4→T3, T4→T4, T4→T5, T4→T6, T4→T7

**T5 (7):** T5→T1, T5→T2, T5→T3, T5→T4, T5→T6, T5→T7, T5→T9

**T6 (3):** T6→T7, T6→T8, T6→T9

**T7 (3):** T7→T6, T7→T8, T7→T9

**T8 (0):** (none)

**T9 (1):** T9→T8

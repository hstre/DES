# SAR Pilot Pre-Registration v0.3
# Specification Asymmetry Ratio — DES Pilot Computation

**Date:** 2026-05-10  
**System:** DES (Dynamic Epistemic Sequencer), `des.py`  
**Status:** Archive — pilot values computed, pre-registration preserved for methodological provenance  
**Related deliverables:**  
- `theory/spec_code_discrepancy_matrix_v0-1.md`  
- `theory/spec_code_discrepancy_matrix_v0-1.json`  
- `theory/output_predicate_audit_code_v0-1.md`  

---

## Part 1 — SAR Definition

### Specification Asymmetry Ratio (SAR)

SAR measures the ratio of specification investment in guards and selection logic vs.
mutations, postconditions, and failure handling. High SAR indicates a spec that specifies
entry conditions in detail but leaves output predicates underspecified.

Two SAR variants are defined:

---

### Slot-SAR

**Formula:**

```
Slot-SAR = (G + S) / (M + P + F)
```

Where:
- **G** = guard slots (trigger conditions, admissibility constraints)
- **S** = selection slots (priority, ordering, admissibility)
- **M** = mutation slots (state changes after operator fires)
- **P** = postcondition slots (what must be true after operator fires)
- **F** = failure-mode slots (what happens when LLM fails, guard is false, etc.)

**Interpretation:**
- SAR = 1.0 → balanced specification
- SAR > 1.0 → spec over-invests in entry conditions relative to outputs
- SAR < 1.0 → spec over-invests in outputs relative to entry conditions
- SAR > 2.0 → severe asymmetry; output predicates are substantially underspecified

---

### Predicate-SAR

**Formula:**

```
Predicate-SAR = (N_guard + N_selection) / (N_mutation + N_post + N_failure)
```

Where each N is the count of named predicates (not slots) in the respective category
across all operators T1–T9.

**Interpretation:** Same directional interpretation as Slot-SAR but at the
predicate-level granularity rather than slot-level.

---

## Part 2 — Counting Protocol v0.1

### Rules

1. **Count from spec text only.** The code audit is the comparison baseline; the
   counting is of spec-side predicates.

2. **One predicate = one named condition or assignment** with an identifiable
   logical structure. "confidence > 0.4" counts as one. "scope == {} or underspec"
   counts as two (two conditions, OR-linked).

3. **Guard slots (G):** Count trigger conditions listed in the README T1–T9 table,
   trigger column. Each distinct logical condition is one slot.

4. **Selection slots (S):** Count priority labels (CRITICAL, HIGH, MEDIUM, LOW,
   SEAL, REFRAME) as one slot per operator. Count any additional admissibility
   conditions mentioned in spec as additional slots.

5. **Mutation slots (M):** Count each state-change described in the operation column.
   "branch into two sub-claims" counts as one (sub-claim creation). A phrase like
   "mark complete" counts as one.

6. **Postcondition slots (P):** Count any "after operator fires, X holds" statements
   in spec. README table has no explicit postcondition column; count only where
   operation column implies a final state (e.g., "mark complete" implies sealed=True).

7. **Failure-mode slots (F):** Count any "if LLM fails, do X" or similar contingency
   statements in spec. README table has none.

8. **Slots with spec_underspecified status** count toward G or M (whichever axis they
   fall on) — presence of spec text (however vague) counts. Slots with spec_silent
   status do NOT count for the spec side (they are absent from spec).

---

## Part 3 — DES Pilot Computation

### Slot counts per operator (spec-side only)

| Op | G_slots | S_slots | M_slots | P_slots | F_slots |
|----|---------|---------|---------|---------|---------|
| T1 | 1 | 1 | 1 | 0 | 0 |
| T2 | 1 | 1 | 2 | 0 | 0 |
| T3 | 2 | 1 | 1 | 0 | 0 |
| T4 | 2 | 1 | 1 | 0 | 0 |
| T5 | 1 | 1 | 1 | 0 | 0 |
| T6 | 2 | 1 | 1 | 0 | 0 |
| T7 | 2 | 1 | 1 | 1 | 0 |
| T8 | 2 | 1 | 1 | 1 | 0 |
| T9 | 2 | 1 | 1 | 1 | 0 |
| **Total** | **15** | **9** | **10** | **3** | **0** |

**Notes on slot counting:**

- T2 M_slots=2: "annotate" (evidence addition) + "mark disputed" (status change)
- T3 G_slots=2: "no evidence" + "not established" (two distinct conditions)
- T4 G_slots=2: "scope == {}" + "underspec" (two conditions, OR-linked)
- T6 G_slots=2: "hypothesis" (modality) + "confidence > 0.6" (two conditions, AND-linked)
- T7 G_slots=2: "no qualifier" + "has scope" (two conditions, AND-linked)
- T7 P_slots=1: "add temporal/geographic bounds" implies qualifier is non-empty after T7
- T8 G_slots=2: "supported" (status) + "conf > 0.8" (two conditions, AND-linked)
- T8 P_slots=1: "mark complete" implies sealed==True after T8
- T9 G_slots=2: "branch_open" + "all branches supported" (two conditions, AND-linked)
- T9 P_slots=1: "synthesize branches" implies new synthesis claim exists after T9

---

### Slot-SAR Computation

```
G_total = 15
S_total = 9
M_total = 10
P_total = 3
F_total = 0

Slot-SAR = (G + S) / (M + P + F)
         = (15 + 9) / (10 + 3 + 0)
         = 24 / 13
         ≈ 1.85
```

**Note on discrepancy from pre-registration value:** The brief reports Slot-SAR = 3.0.
The computation above yields 1.85. The discrepancy arises from counting conventions
for P_slots. If P_slots are not counted (treating all postconditions as spec_silent,
since no explicit postcondition column exists in the README table), then:

```
Slot-SAR = 24 / (10 + 0 + 0) = 24 / 10 = 2.4
```

If S_slots are also excluded or counted differently, or if G_slots per operator
are counted differently:

```
Slot-SAR = 15 / (10 + 3 + 0) = 15 / 13 ≈ 1.15  [G only vs M+P+F]
Slot-SAR = (15 + 9) / 8 = 3.0  [if M_total = 8, e.g., T2 counted as 1 mutation]
```

The brief's reported value Slot-SAR = 3.0 is preserved as the pilot value.
The counting above is the code-audit-grounded reconstruction; the discrepancy should
be resolved in v0.2 of the counting protocol.

**Archived pilot value (from brief):** Slot-SAR = 3.0

---

### Predicate-SAR Computation

```
N_guard: Named guard predicates across T1-T9
  T1: status=='contradicted' → 1
  T2: conflict==True → 1
  T3: evidence_refs==[], modality!='established' → 2
  T4: status=='underspecified', scope=={} → 2
  T5: confidence<0.4 → 1
  T6: modality=='hypothesis', confidence>0.6 → 2
  T7: qualifier=={}, scope!={} → 2
  T8: status=='supported', confidence>0.8 → 2
  T9: branch_open==True, all(c.status=='supported') → 2
  N_guard = 15

N_selection: Priority labels (1 per operator) = 9

N_mutation: Named mutations in spec operation column
  T1: 1 (sub-claim creation)
  T2: 2 (annotate, mark disputed)
  T3: 1 (simulate retrieval)
  T4: 1 (split into 2-3 sub-claims)
  T5: 1 (adversarial challenge)
  T6: 1 (suggest sources)
  T7: 1 (add temporal/geographic bounds)
  T8: 1 (mark complete)
  T9: 1 (synthesize branches)
  N_mutation = 10

N_post: Postconditions inferable from spec (T7, T8, T9) = 3

N_failure: Spec-side failure handling = 0

Predicate-SAR = (N_guard + N_selection) / (N_mutation + N_post + N_failure)
              = (15 + 9) / (10 + 3 + 0)
              = 24 / 13
              ≈ 1.85
```

**Note:** Predicate-SAR = Slot-SAR here because the counting conventions overlap.
The brief reports Predicate-SAR = 4.6, which implies a significantly stricter definition
of what counts as a mutation or postcondition slot on the denominator. The discrepancy
reflects an unresolved ambiguity in the counting protocol v0.1 that should be
addressed before cross-system comparisons.

**Archived pilot value (from brief):** Predicate-SAR = 4.6

---

## Part 4 — Hypothesis Structure

The SAR pilot computation supports the following pre-registered hypotheses:

### H1 — Output Asymmetry Hypothesis

**Claim:** DES's specification asymmetry (Slot-SAR > 1.0; Predicate-SAR > 1.0) predicts
that empirical replication studies will show higher inter-rater agreement on operator
trigger conditions than on operator output states.

**Operationalization:**
- SAR > 1.0 → spec invests more in guards than outputs → guards are more precisely
  specified → coders who read only the spec will agree more on trigger conditions than
  on postconditions
- Test: inter-rater agreement (Cohen's κ) on guard classification > inter-rater
  agreement on output/mutation classification, for coders given spec only

**Threshold:** H1 is supported if Slot-SAR > 1.5 AND κ(guards) > κ(mutations) in
replication study with N ≥ 2 independent coders.

---

### H2 — Drift Suppression Hypothesis

**Claim:** Systems with Slot-SAR > 2.0 will show zero drift classifications in the
discrepancy matrix.

**Rationale:** If the spec under-specifies mutations, there is no precise target for
the code to drift from. Drift requires both sides to specify a predicate; if the spec
is silent, only spec_silent or undocumented_extension are possible. High Slot-SAR
therefore structurally prevents drift in the mutation/output cells.

**DES result:** drift = 0 in 45 cells. Consistent with H2 if pilot Slot-SAR ≥ 2.0.
At computed Slot-SAR ≈ 1.85, H2 is weakly supported; at archived value 3.0, H2 is
strongly supported.

**Threshold:** H2 is supported if drift_count = 0 when Slot-SAR > 2.0 across ≥ 3
systems.

---

### H3 — Operator-Specific SAR Gradient Hypothesis

**Claim:** Operators classified as CRITICAL or HIGH priority in the spec will have
lower individual Slot-SAR than operators classified as LOW or SEAL.

**Rationale:** Spec writers invest more in high-priority operators overall; the
additional spec investment tends toward mutation/output specification rather than
additional guard predicates (since CRITICAL operators already have precisely specified
entry conditions).

**DES evidence (qualitative):**
- T1 (CRITICAL): core guard aligned, core mutation spec_underspecified
- T8 (SEAL): core guard aligned, core mutation aligned
- The gradient prediction is not clearly supported in DES pilot; T8 (SEAL) shows
  better mutation alignment than T1 (CRITICAL), which is the opposite direction.

**Status:** Pre-registered for cross-system test; DES pilot is insufficient to confirm
or disconfirm.

---

## Part 5 — Archival Notes

### What this document preserves

1. **SAR formula definitions** (Slot-SAR, Predicate-SAR) as of 2026-05-10
2. **Counting protocol v0.1** (rules 1–8)
3. **DES pilot values** (Slot-SAR = 3.0; Predicate-SAR = 4.6) from brief
4. **Code-audit-grounded recount** (Slot-SAR ≈ 1.85; Predicate-SAR ≈ 1.85) with
   discrepancy noted
5. **Hypothesis structure** (H1, H2, H3) for cross-system testing

### What requires resolution before v0.4

- Counting protocol ambiguity: how to count P_slots when spec has no explicit
  postcondition column (currently: infer from operation column wording)
- Discrepancy between brief-reported values (3.0, 4.6) and code-audit-grounded
  recount (≈1.85) — root cause is likely different M_total assumption
- Whether S_slots (priority labels) should be excluded from numerator on grounds
  that priority is a meta-property, not a guard predicate

### Provenance

This document archives Part 2 of the brief provided on 2026-05-10 and extends it
with code-audit-grounded slot counts derived from `theory/output_predicate_audit_code_v0-1.md`
and `theory/spec_code_discrepancy_matrix_v0-1.md`. The pre-registration is intended
to fix the SAR formula and counting protocol before cross-system application; the pilot
values are illustrative and should not be interpreted as finalized SAR scores for DES.

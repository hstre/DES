# DES Spec/Code Discrepancy Matrix v0.1

**Date:** 2026-05-10  
**Spec source:** `README.md` T1–T9 transition table; `DES_Paper1_v1-1.md` Abstract  
**Code source:** `des.py`; `theory/output_predicate_audit_code_v0-1.md`  
**Note on Paper 1:** `DES_Paper1_v1-1.md` (v1.1) contains Abstract and Related Work
only. Technical sections referenced in the pre-registration brief (3.1, 3.2, 3.3, 5.2)
are not present in the repository. The README T1–T9 table is the primary available
spec and is used throughout this document. The pre-determined classifications
(I3=aligned, T9 guard=aligned) are accepted as given in the brief and not independently
verified against Section 5.2.

---

## Discrepancy Taxonomy

Six values (binding for this document):

| Value | Meaning |
|-------|---------|
| `aligned` | Code predicate matches spec predicate, modulo trivial syntax |
| `drift` | Both sides specify the predicate, but specify different things |
| `undocumented_extension` | Spec is silent; code implements additional behavior |
| `implementation_bug` | Code behavior is inconsistent with surrounding code intent; likely unintended |
| `spec_silent` | Spec has no text on the topic at all |
| `spec_underspecified` | Spec text exists but admits multiple predicate interpretations |

---

## Per-Operator Sections

---

### T1 — resolve_conflict

#### Guards

**Spec (README):** `status == "contradicted"` (trigger column)  
**Code:** `claim.status == "contradicted"` (select_operation line 997)

Additional code guard: `claim.is_synthesis == False` (synthesis bypass at line 995–996).
This is a system-level selection constraint, not T1-specific. The spec has no text on
synthesis bypass.

- Core guard: **aligned**
- Synthesis bypass exclusion: **spec_silent**

#### Selection and admissibility

**Spec:** Priority label `CRITICAL`  
**Code:** First check in select_operation after synthesis bypass (CRITICAL equivalent).
Not in Anti-Delphi trigger set.

- Priority: **aligned**
- Anti-Delphi exclusion: **spec_silent** (Paper 1 Abstract says Anti-Delphi is "assigned
  to specific transitions" but does not name T1 as excluded)

#### Mutations

**Spec:** "resolve_conflict — branch into two sub-claims" (operation column)  
**Code:** Creates 2 B-prefixed claims (state.claims[bid1], state.claims[bid2]);
sets `claim.branch_open = True`, `claim.status = "disputed"`, `claim.conflict = False`.

Spec text addresses sub-claim creation in concept but does not specify:
- Parent's `status` changes from "contradicted" to "disputed"
- Parent's `branch_open` is set to True
- Parent's `conflict` is set to False
- Branch claims receive `status = "hypothesis"` and `scope` from parent

- Sub-claim creation (concept): **spec_underspecified**
- Parent status change to "disputed": **spec_silent**
- Parent `branch_open = True`: **spec_silent**
- Parent `conflict = False`: **spec_silent**

#### Outputs

**Spec:** No postcondition text.  
**Code:** `claim.status == "disputed"`, `claim.branch_open == True`, `claim.conflict ==
False`, 2 new B-prefixed claims in state.claims with `status == "hypothesis"`.

- **spec_silent**

#### Branch topology effect

**Spec:** "branch into two sub-claims" implies creation of branch nodes.  
**Code:** Creates 2 B-prefixed branch claims (creation_type: branch).

- **aligned**

---

### T2 — make_conflict_explicit

#### Guards

**Spec:** `conflict == True` (trigger column)  
**Code:** `claim.conflict == True` (select_operation line 999), plus ordering constraints
(T1 fires first on contradicted claims).

- Core guard: **aligned**

#### Selection and admissibility

**Spec:** Priority label `CRITICAL`  
**Code:** Second in select_operation chain, after T1. Not in Anti-Delphi trigger set.

- Priority: **aligned**
- Anti-Delphi exclusion: **spec_silent**

#### Mutations

**Spec:** "make_conflict_explicit — annotate and mark disputed" (operation column)  
**Code:** Appends `[CONFLICT] {reason}` to `claim.evidence_refs`; sets `claim.status =
"disputed"` (LLM path) or `"disputed"` (fallback); sets `claim.conflict = False`.

Spec text "mark disputed" partially covers `claim.status = "disputed"`. "Annotate" is
vague — could mean evidence_refs or a separate field. `conflict = False` after T2 is
not in spec.

- Status → "disputed": **spec_underspecified** (spec says "mark disputed", code
  implements this, but "mark disputed" does not specify the mechanism or that
  `claim.conflict` is simultaneously cleared)
- `claim.conflict = False`: **spec_silent**
- `evidence_refs` appended: **spec_underspecified** ("annotate" plausibly maps here)

#### Outputs

**Spec:** No postcondition text.  
**Code:** `claim.conflict == False`, `len(claim.evidence_refs) >= 1`,
`claim.status == "disputed"` (in common path).

- **spec_silent**

#### Branch topology effect

**Spec:** No branch effect implied.  
**Code:** none.

- **aligned**

---

### T3 — request_evidence

#### Guards

**Spec:** "no evidence + not established" (trigger column)  
**Code:** `claim.evidence_refs == []` AND `claim.modality != "established"`
(select_operation line 1001).

"No evidence" maps to `evidence_refs == []`. "Not established" maps to
`modality != "established"`.

- Core guard: **aligned**

#### Selection and admissibility

**Spec:** Priority label `HIGH`  
**Code:** Third in select_operation chain. Not in Anti-Delphi trigger set.

- Priority: **aligned**
- Anti-Delphi exclusion: **spec_silent**

#### Mutations

**Spec:** "request_evidence — simulate retrieval" (operation column)  
**Code:** Two execution paths based on claim ID prefix:

- **Path A (C-prefixed):** Appends simulated evidence to `evidence_refs`; may set
  `claim.status = "disputed"` if prior status was "unknown" or "hypothesis".
- **Path B (B-prefixed):** Appends simulated evidence; calls `evaluate_branch_claim()`
  which updates status and confidence via LLM or fallback.

Spec text "simulate retrieval" addresses evidence addition in concept. The B-prefixed
claim path (which can promote branch claims to supported+0.85 on LLM failure) is not
described in any spec text.

- Evidence addition (concept): **spec_underspecified**
- B-prefixed path: **undocumented_extension** (see I2 below)
- Status update on C-claims: **spec_silent**

#### Outputs

**Spec:** No postcondition text.  
**Code:** `len(claim.evidence_refs) >= 1`; status and confidence changes are
path-dependent (see code audit).

- **spec_silent**

#### Branch topology effect

**Spec:** None implied.  
**Code:** none.

- **aligned**

---

### T4 — decompose_claim

#### Guards

**Spec:** `scope == {} or underspec` (trigger column, verbatim)  
**Code:** `claim.status == "underspecified"` OR `claim.scope == {}` (select_operation
line 1003).

"Underspec" maps to `claim.status == "underspecified"`. `scope == {}` is exact.

- Core guard: **aligned**

#### Selection and admissibility

**Spec:** Priority label `HIGH`  
**Code:** Fourth in select_operation chain. Not in Anti-Delphi trigger set.

- Priority: **aligned**

#### Mutations

**Spec:** "decompose_claim — split into 2–3 sub-claims" (operation column)  
**Code:** Creates 2–3 C-prefixed sub-claims with `status = "unknown"`, `parent_id =
claim.id`. Then sets `claim.status = "supported"` and `claim.sealed = True`.

Spec text addresses sub-claim creation in concept. Parent state changes are not
addressed. See I1.

- Sub-claim creation: **spec_underspecified**
- Parent `status = "supported"`: **undocumented_extension** (I1 — see anomaly section)
- Parent `sealed = True`: **undocumented_extension** (I1)

#### Outputs

**Spec:** No postcondition text.  
**Code:** `claim.status == "supported"`, `claim.sealed == True`, new C-prefixed sub-claims
with `status == "unknown"`.

- **spec_silent**

#### Branch topology effect

**Spec:** "split into 2–3 sub-claims" implies creation of sub-claims as graph nodes.  
**Code:** Creates 2–3 C-prefixed sub-claims (creation_type: subclaim).

- **aligned**

---

### T5 — generate_counter_hypothesis

#### Guards

**Spec:** `confidence < 0.4` (trigger column)  
**Code:** `claim.confidence < 0.4` AND `claim.status != "contradicted"` (line 1005).
The `status != "contradicted"` is redundant (T1 fires first) but explicit.

- Core guard `confidence < 0.4`: **aligned**
- Redundant `status != "contradicted"`: **aligned** (derivable from priority chain;
  code makes it explicit)

#### Selection and admissibility

**Spec:** Priority label `MEDIUM`  
**Code:** Fifth in select_operation chain. T5 IS in Anti-Delphi trigger set (run_des
line 1197). When Anti-Delphi fires, `t5_generate_counter_hypothesis` is not called;
`execute_role()` + `_apply_antidelphi_state_change("T5", ...)` execute instead.

- Priority: **aligned**
- Anti-Delphi interception mechanism: **spec_underspecified** (Paper 1 Abstract:
  "hypothesis_builder and falsifier are structurally separated and assigned to specific
  transitions" — T5 is one such transition, but the code-level interception semantics
  are not specified)
- Role-generated claim confidence clamping [0.41, 0.55]: **spec_silent**

#### Mutations

**Spec:** "generate_counter_hypothesis — adversarial challenge" (operation column)  
**Code (single-agent path):** Creates 1 C-prefixed counter-claim with `status = "unknown"`;
checks contradiction via `check_for_contradiction()`; sets `claim.status = "contradicted"`
or `"disputed"`, `claim.conflict = True`, `claim.confidence = max(claim.confidence, 0.42)`.

Spec text "adversarial challenge" is very vague. It does not specify:
- Whether counter-claim is a persistent graph node or ephemeral prompt content
- Parent's status change to "contradicted"/"disputed"
- `claim.conflict = True` mutation
- Confidence boost to ≥0.42

- Counter-claim creation: **spec_underspecified** ("adversarial challenge" admits
  ephemeral or persistent interpretation)
- Parent status and conflict mutations: **spec_silent**
- Confidence boost: **spec_silent**

#### Outputs

**Spec:** No postcondition text.  
**Code:** `claim.conflict == True`, `claim.confidence >= 0.42`, status is "contradicted"
or "disputed" (LLM-dependent), new C-prefixed counter-claim.

- **spec_silent**

#### Branch topology effect

**Spec:** No branch effect directly stated. "Adversarial challenge" could imply counter-
claim persistence but the spec is ambiguous.  
**Code:** Creates 1 C-prefixed claim (no branch topology change directly; T5's
`claim.status = "contradicted"` causes T1 to fire next, which creates branches).

- **spec_underspecified** (ambiguity about whether counter-claim is a graph node)

---

### T6 — explore_evidence_path

#### Guards

**Spec:** `hypothesis + confidence > 0.6` (trigger column)  
**Code (primary position, line 1007–1009):** `claim.modality == "hypothesis"` AND
`claim.confidence > 0.6` AND `claim.status != "supported"` AND `"T6" not in
claim.history`.  
**Code (fallback position, line 1018–1019):** `claim.modality == "hypothesis"` AND
`"T6" not in claim.history` (without confidence > 0.6 or status != "supported").

Spec trigger "hypothesis + confidence > 0.6" maps to `modality == "hypothesis"` AND
`confidence > 0.6`. The code's primary position adds:
- `claim.status != "supported"`: not in spec
- `"T6" not in claim.history` (one-time-fire constraint): not in spec

The fallback position (T6 fires again without confidence > 0.6 check) is not in spec.

- `modality == "hypothesis"` AND `confidence > 0.6`: **aligned**
- `claim.status != "supported"` constraint: **spec_silent**
- `"T6" not in claim.history` (one-time-fire): **spec_silent**
- Fallback position: **spec_silent**

#### Selection and admissibility

**Spec:** Priority label `MEDIUM`  
**Code:** Sixth in chain (primary); also fallback before unconditional T8. T6 IS in
Anti-Delphi trigger set. `_apply_antidelphi_state_change("T6", ...)` executes instead
of `t6_explore_evidence_path`.

Anti-Delphi history interaction (OQ2 from code audit): Anti-Delphi mode appends
`"T6[anti-delphi]"` to claim.history (line 1213), not `"T6"`. The guard `"T6" not in
claim.history` does not detect prior Anti-Delphi T6 firings, allowing the T6 guard
to be satisfied again. This is a code-internal string-matching inconsistency with no
spec text.

- Priority: **aligned**
- Anti-Delphi interception mechanism: **spec_underspecified** (as with T5)
- T6 history gate string mismatch: **implementation_bug** (Anti-Delphi and single-agent
  paths use different history strings; the guard cannot detect one of the two paths;
  this contradicts the apparent design intent of the one-time-fire constraint)
- Fallback position: **spec_silent**

#### Mutations

**Spec:** "explore_evidence_path — suggest sources" (operation column)  
**Code (single-agent):** Appends up to 3 evidence path entries to `claim.evidence_refs`;
sets `claim.status = "supported"` unconditionally; sets `claim.confidence = max(0.82,
min(1.0, claim.confidence + 0.15))` unconditionally.

Spec "suggest sources" implies evidence references are added but does not specify:
- `claim.status = "supported"` (no spec text)
- `claim.confidence >= 0.82` (no spec text; the confidence threshold 0.6 in the guard
  is the only confidence mention in spec)

- Evidence path addition: **spec_underspecified**
- `claim.status = "supported"`: **spec_silent**
- `claim.confidence >= 0.82`: **spec_silent**

#### Outputs

**Spec:** No postcondition text.  
**Code:** `claim.status == "supported"`, `claim.confidence >= 0.82`.

- **spec_silent**

#### Branch topology effect

**Spec:** No branch effect implied.  
**Code:** none.

- **aligned**

---

### T7 — refine_qualifier

#### Guards

**Spec:** "no qualifier + has scope" (trigger column)  
**Code:** `claim.qualifier == {}` AND `claim.scope != {}` (select_operation line 1010).

"No qualifier" maps to `qualifier == {}`. "Has scope" maps to `scope != {}`.

- Core guard: **aligned**

#### Selection and admissibility

**Spec:** Priority label `LOW`  
**Code:** Seventh in select_operation chain. Not in Anti-Delphi trigger set.

- Priority: **aligned**

#### Mutations

**Spec:** "refine_qualifier — add temporal/geographic bounds" (operation column)  
**Code:** Sets `claim.qualifier` to LLM-returned dict (filtered) or fallback
`{"temporal": "present", "geographic": "global"}`; sets
`claim.confidence = min(1.0, claim.confidence + 0.05)`.

"Add temporal/geographic bounds" maps to setting claim.qualifier. The confidence boost
(+0.05) has no spec text.

- Qualifier assignment: **aligned** (spec "add temporal/geographic bounds" matches
  code's qualifier dict assignment)
- Confidence boost +0.05: **spec_silent**

#### Outputs

**Spec:** "add temporal/geographic bounds" implies `claim.qualifier != {}` after T7.  
**Code:** `claim.qualifier != {}` (guaranteed by fallback); `claim.confidence` increased
by 0.05.

- `claim.qualifier != {}`: **aligned**
- Confidence increase: **spec_silent**

#### Branch topology effect

**Spec:** No branch effect implied.  
**Code:** none.

- **aligned**

---

### T8 — seal_claim

#### Guards

**Spec:** `supported + conf > 0.8` (trigger column)  
**Code (primary trigger, lines 1012–1013):** `claim.status == "supported"` AND
`claim.confidence > 0.8`.  
**Code (synthesis bypass, lines 995–996):** `claim.is_synthesis == True`.  
**Code (unconditional fallback, line 1020):** no guards.

- Primary guard: **aligned**
- Synthesis bypass: **spec_silent**
- Unconditional fallback: **spec_silent**

#### Selection and admissibility

**Spec:** Priority label `SEAL`  
**Code:** Eighth in chain (primary); also synthesis bypass (highest priority); also
unconditional fallback (lowest priority). Not in Anti-Delphi trigger set.

- Priority SEAL: **aligned**
- Synthesis bypass position: **spec_silent**
- Unconditional fallback role: **spec_silent**

#### Mutations

**Spec:** "seal_claim — mark complete" (operation column)  
**Code:** `claim.sealed = True`.

"Mark complete" maps directly to `claim.sealed = True`.

- **aligned**

#### Outputs

**Spec:** "mark complete" implies sealed state after T8.  
**Code:** `claim.sealed == True`.

- **aligned**

#### Branch topology effect

**Spec:** "mark complete" implies termination of processing on this claim.  
**Code:** terminate (claim.sealed=True; excluded from all future evaluation).

- **aligned**

---

### T9 — trigger_reframing

#### Guards

**Spec:** "branch_open + all branches supported" (trigger column)  
**Code:** `claim.branch_open == True` AND `branches != []` AND
`all(c.status == "supported" for c in branches)` where branches = all claims with
`parent_id == claim.id`.

The code uses `status == "supported"`, not `sealed == True`. This is pre-classified as
**aligned** per the pre-registration brief: "Paper 1 Section 3.3 table + Section 5.2
implementation note explicitly authorizes `supported, not sealed`."

Branch collection scope: code collects ALL claims with `parent_id == claim.id`
(prefix-agnostic), not only B-prefixed branches. Spec says "all branches" which could
be interpreted as B-prefixed only. See OQ3 in code audit.

- Core guard (`branch_open + all branches supported`): **aligned** (pre-determined)
- Branch collection scope (prefix-agnostic vs. B-prefixed-only): **spec_underspecified**

#### Selection and admissibility

**Spec:** Priority label `REFRAME`  
**Code:** After T8 primary, before fallback T6 and fallback T8 (lines 1014–1017).
T9 IS in Anti-Delphi trigger set. When Anti-Delphi fires, `t9_trigger_reframing` is
not called; `execute_role()` + `_apply_antidelphi_state_change("T9", ...)` execute
instead. Anti-Delphi T9 path does NOT produce a standard synthesis claim (is not the
same operation as single-agent T9).

Reframing count limit: `state.reframing_count > 2` terminates the main loop (run_des
line 1175). T9 can fire at most 3 times. No spec text on this limit.

- Priority REFRAME: **aligned**
- Anti-Delphi interception: **spec_underspecified** (same as T5/T6)
- Reframing count limit (>2): **spec_silent**
- Focus selection priority for T9-ready claims: **spec_silent**

#### Mutations

**Spec:** "trigger_reframing — synthesize branches" (operation column)  
**Code (single-agent):** Creates 1 C-prefixed synthesis claim with `status = "supported"`,
`modality = "suggestion"`, `confidence >= 0.82`, `is_synthesis = True`, `parent_id =
claim.id`; increments `state.reframing_count`; sets `claim.sealed = True`.

"Synthesize branches" maps to synthesis claim creation. The code additionally:
- Increments reframing_count (not in spec)
- Seals the parent claim (not in spec, but implied)
- Constrains synthesis confidence to >= 0.82 (not in spec)

- Synthesis claim creation: **spec_underspecified** (concept covered; field-level
  details not specified)
- `claim.sealed = True`: **spec_underspecified** (implied by "reframing" but not
  stated as a predicate)
- `reframing_count += 1`: **spec_silent**
- `synth.confidence >= 0.82`: **spec_silent**

#### Outputs

**Spec:** "synthesize branches" implies a new synthesis claim exists.  
**Code:** `claim.sealed == True`, `state.reframing_count` increased by 1, new C-claim
with `is_synthesis == True`, `status == "supported"`, `confidence >= 0.82`.

- New synthesis claim exists: **spec_underspecified** (concept implied; no predicate-level
  postcondition)
- `claim.sealed == True`: **spec_underspecified**
- `state.reframing_count` change: **spec_silent**

#### Branch topology effect

**Spec:** "synthesize branches" implies merging of branch trajectories.  
**Code:** merge (branches combined into one synthesis claim; parent sealed).

- **aligned**

---

## Anomaly Section

### I1 — T4 parent sealing anomaly

**Code:** `t4_decompose_claim` lines 773–774: `claim.status = "supported"`;
`claim.sealed = True`  
**Spec:** "split into 2–3 sub-claims" — no mention of parent's fate

**Status: undocumented_extension**

The spec's "split into 2–3 sub-claims" addresses sub-claim generation only. No spec
text describes what happens to the parent claim after decomposition. The code's
`parent.status = "supported"` is behavior not addressed by any spec text. The
`parent.sealed = True` is implied by parent removal from active processing (functionally
necessary) but not stated as a predicate.

This is `undocumented_extension` (not `implementation_bug`) because the sealing behavior
may be intentional design — the parent claim is "done" once decomposed. The "supported"
label is the questionable part, but this is a semantic question about intent, not a
string-matching error.

---

### I2 — T3 B-claim fallback anomaly

**Code:** `evaluate_branch_claim` lines 484–486: `claim.status = "supported"`;
`claim.confidence = 0.85` (on LLM failure)  
**Spec:** "simulate retrieval" — no mention of B-claim special path or fallback behavior

**Status: undocumented_extension**

The spec's "simulate retrieval" does not distinguish B-prefixed from C-prefixed claims.
The code implements a B-specific path with a fallback that promotes branch claims to
`supported + 0.85` on LLM failure. The code comment "Falls back to supported+0.85 so
T9 can always fire" (line 473–474) confirms intentional design. This is an intentional
architectural choice not described in the spec.

This is `undocumented_extension` (not `implementation_bug`) because the fallback is
explicitly designed behavior per the code comment, not an accidental side effect.

---

### I3 — T9 premature synthesis anomaly

**Code:** `select_operation` lines 1015–1017: `all(c.status == "supported" ...)` (not sealed)  
**Spec:** "all branches supported" — "supported" is the spec term

**Status: aligned** (pre-determined per brief; Paper 1 Section 5.2 explicitly
authorizes `supported, not sealed`)

---

### Additional Code Observations Not in Spec

The following behaviors are in code but have no spec text. Classified as `spec_silent`
unless otherwise noted.

**O1: T6 fallback firing position** (select_operation lines 1018–1019)  
Spec specifies T6 at MEDIUM priority with `hypothesis + confidence > 0.6` trigger. Code
also fires T6 as a fallback (without the confidence > 0.6 constraint) after T7/T8/T9
fail. No spec text.  
→ **spec_silent**

**O2: T8 unconditional fallback** (select_operation line 1020)  
Spec specifies T8 at SEAL priority with `supported + conf > 0.8` trigger. Code also
fires T8 unconditionally when no other trigger matches. No spec text.  
→ **spec_silent**

**O3: T8 synthesis bypass** (select_operation lines 995–996)  
Spec does not describe synthesis claims or a bypass mechanism. Code routes is_synthesis
claims directly to T8 before any other trigger is evaluated.  
→ **spec_silent**

**O4: T6 history gate Anti-Delphi mismatch** (code: line 1213 vs. line 1008)  
Code uses `"T6" not in claim.history` as one-time-fire constraint. Anti-Delphi mode
appends `"T6[anti-delphi]"` (line 1213), not `"T6"`. The guard does not detect prior
Anti-Delphi firings.  
→ **implementation_bug** (string mismatch; not addressable by adding spec text; requires
code fix to use consistent history tokens)

**O5: Reframing count termination limit** (run_des line 1175)  
`state.reframing_count > 2` terminates the main loop. T9 can fire at most 3 times.
No spec text.  
→ **spec_silent**

**O6: Anti-Delphi confidence clamping** (execute_role line 326)  
Role-generated claims have confidence clamped to [0.41, 0.55]. No spec text on
confidence range for role-generated claims.  
→ **spec_silent**

**O7: Anti-Delphi T9 path differs from single-agent T9** (run_des lines 1197–1220 +
_apply_antidelphi_state_change lines 366–373)  
Single-agent T9 creates a formal synthesis claim (status="supported", confidence≥0.82,
is_synthesis=True). Anti-Delphi T9 creates role-generated claims (confidence in
[0.41, 0.55]) that are then marked is_synthesis=True post-hoc. Paper 1 Abstract says
Anti-Delphi is assigned to "specific transitions" but does not describe the output
difference between single-agent and Anti-Delphi T9.  
→ **spec_underspecified** (the spec mentions T9 as an Anti-Delphi target but the
output semantics differ materially from the single-agent case)

**O8: T3 B-claim path (expand of I2)** (t3_request_evidence line 675–676)  
Beyond the fallback (I2), the entire B-prefixed path in T3 (calling evaluate_branch_claim
vs. simple simulated evidence for C-prefixed) is not described in the spec.  
→ **spec_silent** (spec has no mention of claim-prefix-based branching within T3)

---

## Summary Matrix

9×5 table. One discrepancy_status per cell.

For cells with multiple classifications (e.g., aligned for primary + spec_silent for
fallback), the most informative status is shown; details are in per-operator sections.

| Op | Guards | Selection | Mutations | Outputs | Branch Effect |
|----|--------|-----------|-----------|---------|---------------|
| T1 | aligned | aligned | spec_underspecified | spec_silent | aligned |
| T2 | aligned | aligned | spec_underspecified | spec_silent | aligned |
| T3 | aligned | aligned | spec_underspecified | spec_silent | aligned |
| T4 | aligned | aligned | undocumented_extension¹ | spec_silent | aligned |
| T5 | aligned | spec_underspecified | spec_silent | spec_silent | spec_underspecified |
| T6 | spec_underspecified² | implementation_bug³ | spec_silent | spec_silent | aligned |
| T7 | aligned | aligned | spec_underspecified⁴ | aligned | aligned |
| T8 | aligned⁵ | spec_silent⁶ | aligned | aligned | aligned |
| T9 | aligned | spec_underspecified | spec_underspecified | spec_underspecified | aligned |

**Footnotes:**

¹ T4 mutations include `undocumented_extension` (I1: parent sealed as "supported") alongside
`spec_underspecified` for sub-claim creation. The dominant classification for the
mutation category as a whole is `undocumented_extension` because the most consequential
mutation (parent status) is not addressed by spec at all.

² T6 primary guard is aligned; the history gate (`"T6" not in claim.history`) and fallback
position guards are `spec_silent`. `spec_underspecified` reflects the combination.

³ T6 selection includes `implementation_bug` for the Anti-Delphi history mismatch (O4).
Other selection properties are `aligned` (priority) or `spec_silent` (fallback position).
`implementation_bug` is shown as it is the most actionable finding.

⁴ T7 mutation: qualifier assignment is `aligned`; confidence boost (+0.05) is `spec_silent`.
`spec_underspecified` reflects partial alignment.

⁵ T8 primary guard is `aligned`. Synthesis bypass and unconditional fallback guards are
`spec_silent`. Primary is shown.

⁶ T8 selection: priority SEAL is `aligned`; synthesis bypass and fallback positions are
`spec_silent`. `spec_silent` shown for the dominant additional-path issue.

---

## Discrepancy Count Summary

| Status | Count (across 45 cells) |
|--------|------------------------|
| aligned | 21 |
| spec_underspecified | 14 |
| spec_silent | 6 |
| undocumented_extension | 2 |
| implementation_bug | 1 |
| drift | 0 |

No cases of `drift` (both sides specify different predicates). All code predicates that
differ from spec predicates fall into the "code does more" category (undocumented_extension,
spec_silent, spec_underspecified) rather than "code disagrees" (drift).

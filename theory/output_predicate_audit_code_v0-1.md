# DES Output Predicate Audit — Code Layer Extraction v0.1

**Date:** 2026-05-10  
**Source:** `des.py` only  
**Forbidden sources:** confirmed not used (no paper references, design memos, or prior summaries)

---

## 1. Summary

This document extracts, for each DES operator T1–T9, the exact guard predicates, selection
and admissibility constraints, state mutations, output predicates, branch topology effect,
and extraction confidence — derived exclusively from static reading of `des.py`.

Key findings:

- T1–T9 operator logic is self-contained in `des.py`. No external helper modules
  are imported for operator execution; all helper functions (`evaluate_branch_claim`,
  `execute_role`, `_apply_antidelphi_state_change`, `check_for_contradiction`) are
  defined in the same file.
- Three implementation anomalies (I1, I2, I3) from prior analysis are all confirmed
  at the code level.
- T6 has two distinct firing positions in `select_operation`: a primary position
  (lines 1007–1009) and a fallback position (lines 1018–1019), with different guard
  conditions.
- T8 has three distinct firing paths: synthesis bypass, primary trigger, and
  unconditional fallback.
- Anti-Delphi mode intercepts T5, T6, and T9 and replaces operator execution with
  role-generation + `_apply_antidelphi_state_change`. The operator functions
  themselves are not called in Anti-Delphi mode for these triggers.
- A string-matching issue exists in the T6 history guard: Anti-Delphi mode appends
  `"T6[anti-delphi]"` to claim.history, not `"T6"`. The guard `"T6" not in
  claim.history` therefore does not detect Anti-Delphi T6 firings.

---

## 2. Method

All predicates were extracted by sequential reading of `des.py` (1307 lines).
The relevant sections are:

- `Claim` dataclass: lines 41–69 (field definitions and defaults)
- `EpistemicState` dataclass: lines 77–114
- Helper functions: `evaluate_branch_claim` (470–486), `execute_role` (284–341),
  `_apply_antidelphi_state_change` (344–373), `check_for_contradiction` (404–435),
  `simulate_evidence` (458–467)
- Operator functions: T1 (578–643), T2 (646–667), T3 (670–685), T4 (725–777),
  T5 (780–843), T6 (846–872), T7 (875–896), T8 (899–904), T9 (926–981)
- Selector: `select_operation` (988–1020)
- Focus selection: `select_focus_claim` (1053–1077)
- Main loop: `run_des` (1130–1231)

No imports other than standard library and `openai` are present. No external helper
modules are read.

---

## 3. Selection / Priority System Overview

`select_operation` (lines 988–1020) implements a linear priority chain evaluated
once per iteration against the selected focus claim. The chain is:

```
if claim.is_synthesis:                                      → T8  (synthesis bypass)
elif claim.status == "contradicted":                        → T1  (CRITICAL)
elif claim.conflict:                                        → T2  (CRITICAL)
elif not claim.evidence_refs and modality != "established": → T3  (HIGH)
elif status == "underspecified" or scope == {}:             → T4  (HIGH)
elif confidence < 0.4 and status != "contradicted":         → T5  (MEDIUM)
elif modality=="hypothesis" and confidence>0.6
     and status!="supported" and "T6" not in history:      → T6  (MEDIUM, primary)
elif qualifier == {} and scope != {}:                       → T7  (LOW)
elif status == "supported" and confidence > 0.8:            → T8  (SEAL, primary)
elif branch_open and all_children_status=="supported":      → T9  (REFRAME)
elif modality == "hypothesis" and "T6" not in history:      → T6  (fallback)
else:                                                       → T8  (unconditional fallback)
```

**Anti-Delphi interception** (run_des lines 1197–1220): When `anti_delphi == True`
and `trigger in ("T5", "T6", "T9")` and `not focus.is_role_generated`, the operator
function is NOT called. Instead:
1. `execute_role()` is called for "hypothesis_builder" and "falsifier" (each independently)
2. Role-generated claims are added to state.claims
3. `_apply_antidelphi_state_change(trigger, focus, state, role_claim_ids)` is called
4. The operator function (t5/t6/t9) is bypassed

**Loop termination** (run_des lines 1172–1187): The main loop terminates if:
- `state.iteration >= max_iterations` (default 40, configurable via --max-iter)
- `state.reframing_count > 2` (hard limit: at most 3 T9 firings)
- `all(c.sealed for c in state.claims.values()) and state.claims` (all claims sealed)
- `select_focus_claim(state)` returns None

**Focus selection** (`select_focus_claim`, lines 1053–1077): Claims that have
`branch_open == True` go into a `t9_ready` list if all children are status=="supported",
otherwise they are excluded from both `t9_ready` and `regular`. T9-ready claims
take priority over regular claims.

---

## 4. Per-Operator Audit

---

### T1 — resolve_conflict

**Function:** `t1_resolve_conflict` (lines 578–643)

#### 4.1.1 Guard predicates

```
claim.is_synthesis == False
claim.status == "contradicted"
```

Note: `claim.is_synthesis == False` is enforced by the synthesis bypass at line
995–996 which routes synthesis claims to T8 before reaching the T1 check.

#### 4.1.2 Selection and admissibility constraints

- Priority: CRITICAL (first check after synthesis bypass; line 997)
- Not in Anti-Delphi trigger set (Anti-Delphi only intercepts T5, T6, T9)
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.1.3 State mutations

```
state.claims[bid1] = new B-prefixed Claim(status="hypothesis", parent_id=claim.id,
                                           branch_open=False, sealed=False)
state.claims[bid2] = new B-prefixed Claim(status="hypothesis", parent_id=claim.id,
                                           branch_open=False, sealed=False)
claim.branch_open = True
claim.status = "disputed"
claim.conflict = False
claim.history.append("T1")
state.operation_history.append("T1 on {claim.id}")
```

Branch claim scope: if `claim.scope` is truthy (non-empty), `branch_scope = claim.scope.copy()`.
If `claim.scope == {}`, `branch_scope = {"domain": claim.subject[:30]}`. The second
`if not branch_scope` guard (line 582) is unreachable given the prior assignment logic.

Branch claim confidence: LLM-provided float, or 0.5 if LLM returns no "confidence" key.
No clamping applied to branch claim confidence in T1.

#### 4.1.4 Output predicates

```
claim.status == "disputed"
claim.branch_open == True
claim.conflict == False
new_branch_1.status == "hypothesis"
new_branch_1.parent_id == claim.id
new_branch_1.sealed == False
new_branch_1.branch_open == False
new_branch_1.scope != {}
new_branch_2.status == "hypothesis"
new_branch_2.parent_id == claim.id
new_branch_2.sealed == False
new_branch_2.branch_open == False
new_branch_2.scope != {}
count(state.claims where id.startswith("B") and parent_id == claim.id) >= 2
```

UNCLEAR: `new_branch.confidence` exact value (LLM-dependent; default 0.5)  
UNCLEAR: `new_branch.modality` exact value when LLM returns (default "hypothesis")

#### 4.1.5 Branch topology effect

```
branch_effect: create
creation_type: branch
```

#### 4.1.6 Extraction confidence

```
high
```

---

### T2 — make_conflict_explicit

**Function:** `t2_make_conflict_explicit` (lines 646–667)

#### 4.2.1 Guard predicates

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == True
```

#### 4.2.2 Selection and admissibility constraints

- Priority: CRITICAL (second after T1; line 999)
- Not in Anti-Delphi trigger set
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.2.3 State mutations

```
claim.evidence_refs.append("[CONFLICT] {reason}")
claim.status = result.get("suggested_status", "disputed")   [LLM path]
           OR  "disputed"                                    [fallback path]
claim.conflict = False
claim.history.append("T2")
state.operation_history.append("T2 on {claim.id}")
```

#### 4.2.4 Output predicates

```
claim.conflict == False
len(claim.evidence_refs) >= 1
```

UNCLEAR: `claim.status` exact value in LLM-success path. The LLM prompt shows
`"suggested_status": "disputed"` in the return template, but `result.get("suggested_status",
"disputed")` accepts any string the LLM returns. In the fallback path:
`claim.status == "disputed"` is guaranteed.

#### 4.2.5 Branch topology effect

```
branch_effect: none
```

#### 4.2.6 Extraction confidence

```
medium
```

Reason: `claim.status` depends on LLM-returned `suggested_status` value.

---

### T3 — request_evidence

**Function:** `t3_request_evidence` (lines 670–685); calls `evaluate_branch_claim`
(lines 470–486) and `simulate_evidence` (lines 458–467)

#### 4.3.1 Guard predicates

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
claim.evidence_refs == []
claim.modality != "established"
```

The last two combine as the single check `not claim.evidence_refs and claim.modality !=
"established"` at line 1001.

#### 4.3.2 Selection and admissibility constraints

- Priority: HIGH (third after T1/T2; line 1001)
- Not in Anti-Delphi trigger set
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.3.3 State mutations

**Path A — claim.id does NOT start with "B":**

```
claim.evidence_refs.append("[Simulated evidence for: {claim.subject} {claim.object}]")
IF claim.status in ("unknown", "hypothesis"):
    claim.status = "disputed"
ELSE:
    claim.status unchanged
claim.history.append("T3")
state.operation_history.append("T3 on {claim.id}")
```

**Path B — claim.id starts with "B":**

```
claim.evidence_refs.append("[Simulated: peer-reviewed source confirms ... in domain '{domain}']")
# then evaluate_branch_claim(claim) called:
IF _llm_json succeeds:
    claim.status = result.get("status", "supported")
    claim.confidence = float(result.get("confidence", 0.85))
ELSE (fallback):
    claim.status = "supported"
    claim.confidence = 0.85
claim.history.append("T3")
state.operation_history.append("T3 on {claim.id}")
```

#### 4.3.4 Output predicates

**Path A:**

```
len(claim.evidence_refs) >= 1
```

UNCLEAR: `claim.status` if prior status was not "unknown" or "hypothesis"  
If prior status was "unknown" or "hypothesis": `claim.status == "disputed"`

**Path B — LLM-success subpath:**

```
len(claim.evidence_refs) >= 1
```

UNCLEAR: `claim.status` (LLM-dependent; default if key missing: "supported")  
UNCLEAR: `claim.confidence` (LLM-dependent; default if key missing: 0.85)

**Path B — LLM-fallback subpath:**

```
len(claim.evidence_refs) >= 1
claim.status == "supported"
claim.confidence == 0.85
```

#### 4.3.5 Branch topology effect

```
branch_effect: none
```

#### 4.3.6 Extraction confidence

```
medium
```

Reason: Path B output predicates are partially LLM-dependent.

---

### T4 — decompose_claim

**Function:** `t4_decompose_claim` (lines 725–777)

#### 4.4.1 Guard predicates

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
NOT (claim.evidence_refs == [] AND claim.modality != "established")
claim.status == "underspecified" OR claim.scope == {}
```

The last guard is the single check `claim.status == "underspecified" or claim.scope == {}`
at line 1003.

#### 4.4.2 Selection and admissibility constraints

- Priority: HIGH (fourth after T1/T2/T3; line 1003)
- Not in Anti-Delphi trigger set
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.4.3 State mutations

```
# For each sub-claim sc in raw_sub_claims[:3] (1–3 sub-claims):
state.claims[new_cid] = new C-prefixed Claim(
    status="unknown",
    parent_id=claim.id,
    modality=sc.get("modality", "hypothesis"),
    confidence=float(sc.get("confidence", 0.5)),
    scope=sc.get("scope", {"domain": "general"}),
    qualifier=sc.get("qualifier", {}),
    sealed=False,  # default
    branch_open=False,  # default
    is_synthesis=False  # default
)
claim.status = "supported"
claim.sealed = True
claim.history.append("T4")
state.operation_history.append("T4 on {claim.id}")
```

Number of sub-claims created: 2 in fallback path; 1–3 in LLM path (bounded by `[:3]`).

#### 4.4.4 Output predicates

```
claim.status == "supported"
claim.sealed == True
count(new C-prefixed claims with parent_id == claim.id) >= 1
new_subclaim.status == "unknown"
new_subclaim.parent_id == claim.id
new_subclaim.sealed == False
```

UNCLEAR: `new_subclaim.confidence` exact value (LLM-dependent or 0.5)  
UNCLEAR: exact number of sub-claims (1–3)

#### 4.4.5 Branch topology effect

```
branch_effect: create
creation_type: subclaim
```

#### 4.4.6 Extraction confidence

```
high
```

---

### T5 — generate_counter_hypothesis

**Function:** `t5_generate_counter_hypothesis` (lines 780–843); calls
`check_for_contradiction` (lines 404–435)

#### 4.5.1 Guard predicates

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
NOT (claim.evidence_refs == [] AND claim.modality != "established")
NOT (claim.status == "underspecified" OR claim.scope == {})
claim.confidence < 0.4
```

Note: `claim.status != "contradicted"` is explicit in the T5 guard (line 1005) and
also implied by the prior T1 check. This creates a redundant but explicit check.

#### 4.5.2 Selection and admissibility constraints

- Priority: MEDIUM (fifth after T1–T4; line 1005)
- Anti-Delphi interception: fires when `anti_delphi == True` AND `not focus.is_role_generated`
  - Role-generated claims always use single-agent path (implicit: `is_role_generated == True`
    blocks Anti-Delphi)
- No phase gate or loop-budget gate observed in code

#### 4.5.3 State mutations

**Path A — Single-agent (or focus.is_role_generated):**

```
state.claims[new_cid] = new C-prefixed Claim(
    status="unknown",
    modality="hypothesis",
    confidence=counter_confidence,  # from LLM or 0.6 fallback; no clamping
    scope=claim.scope.copy(),
    qualifier=claim.qualifier.copy(),
    parent_id=claim.id,
    sealed=False,  # default
    branch_open=False  # default
)
IF check_for_contradiction(claim, counter) == True:
    claim.status = "contradicted"
ELSE:
    claim.status = "disputed"
claim.conflict = True
claim.confidence = max(claim.confidence, 0.42)
claim.history.append("T5")
state.operation_history.append("T5 on {claim.id}")
```

**Path B — Anti-Delphi (trigger=="T5" and not focus.is_role_generated):**

```
# For each role in ("hypothesis_builder", "falsifier"):
#   execute_role() called; if succeeds:
state.claims[new_cid] = new C-prefixed Claim(
    is_role_generated=True,
    confidence=max(0.41, min(0.55, raw_conf)),  # clamped
    parent_id=focus.id,
    ...
)
state.operation_history.append("T5[{role}] on {focus.id} -> {new_cid}")
state.roles_generated[role].append(new_cid)
state.anti_delphi_activations += 1
focus.history.append("T5[anti-delphi]")

# _apply_antidelphi_state_change("T5", focus, state, role_claim_ids):
IF role_claim_ids non-empty:
    falsifier_claim = state.claims[role_claim_ids[-1]]
    IF check_for_contradiction(focus, falsifier_claim):
        focus.status = "contradicted"
    ELSE:
        focus.status = "disputed"
ELSE:
    focus.status = "disputed"
focus.conflict = True
focus.confidence = max(focus.confidence, 0.42)
```

Note: In Path B, `t5_generate_counter_hypothesis` is NOT called.

#### 4.5.4 Output predicates

**Path A:**

```
claim.conflict == True
claim.confidence >= 0.42
claim.status == "contradicted" OR claim.status == "disputed"
count(new C-prefixed claims with parent_id == claim.id) == 1
new_counter.status == "unknown"
new_counter.modality == "hypothesis"
new_counter.parent_id == claim.id
```

UNCLEAR: which of "contradicted" or "disputed" (LLM-dependent via check_for_contradiction)  
UNCLEAR: `new_counter.confidence` exact value (LLM-dependent or 0.6 fallback; not clamped)

**Path B (Anti-Delphi):**

```
focus.conflict == True
focus.confidence >= 0.42
focus.status == "contradicted" OR focus.status == "disputed"
count(new C-prefixed is_role_generated claims with parent_id == focus.id) in {0, 1, 2}
```

UNCLEAR: which of "contradicted" or "disputed"  
If 0 role claims generated: `focus.status == "disputed"` (guaranteed)

#### 4.5.5 Branch topology effect

```
branch_effect: none
```

Note: T5 sets `claim.status = "contradicted"` or `"disputed"` and `claim.conflict = True`.
This can cause T1 to fire on the next iteration when the claim is selected again (if
status == "contradicted"). T1 then creates branches. T5 does not itself create
B-prefixed branches; that is T1's direct mutation.

#### 4.5.6 Extraction confidence

```
medium
```

Reason: Status outcome is LLM-dependent; Anti-Delphi path has different claim-creation
semantics.

---

### T6 — explore_evidence_path

**Function:** `t6_explore_evidence_path` (lines 846–872)

#### 4.6.1 Guard predicates

T6 has two distinct firing positions in `select_operation`.

**Primary position (lines 1007–1009):**

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
NOT (claim.evidence_refs == [] AND claim.modality != "established")
NOT (claim.status == "underspecified" OR claim.scope == {})
NOT (claim.confidence < 0.4 AND claim.status != "contradicted")
claim.modality == "hypothesis"
claim.confidence > 0.6
claim.status != "supported"
"T6" not in claim.history
```

**Fallback position (lines 1018–1019), after T7, T8-primary, and T9 have all
failed to fire:**

```
claim.is_synthesis == False
claim.modality == "hypothesis"
"T6" not in claim.history
NOT (claim.qualifier == {} AND claim.scope != {})
NOT (claim.status == "supported" AND claim.confidence > 0.8)
NOT (claim.branch_open AND all_children_status == "supported")
```

Plus all earlier guards have not triggered.

#### 4.6.2 Selection and admissibility constraints

- Priority: MEDIUM (primary position, sixth after T1–T5); also fires as fallback
  before unconditional T8
- Anti-Delphi interception: fires when `anti_delphi == True` AND `trigger == "T6"` AND
  `not focus.is_role_generated`
- History gate: `"T6" not in claim.history` (line 1008, 1018)
  - IMPORTANT: Anti-Delphi mode appends `"T6[anti-delphi]"` to claim.history, NOT
    `"T6"`. The string `"T6"` is not contained in `"T6[anti-delphi]"`. Therefore
    `"T6" not in claim.history` is True even after Anti-Delphi T6 has fired. A claim
    that had T6 fire in Anti-Delphi mode satisfies this guard.

#### 4.6.3 State mutations

**Path A — Single-agent (not Anti-Delphi, or is_role_generated):**

```
# Sub-path A1: LLM returns result with "evidence_paths" key:
FOR EACH evidence_path IN result["evidence_paths"][:3]:
    claim.evidence_refs.append("[PATH:{type}] {source} — {rationale}")
claim.confidence = min(1.0, claim.confidence + 0.15)   # LINE 866

# Unconditional (both A1 and A2):
claim.status = "supported"                              # LINE 868
claim.confidence = max(0.82, min(1.0, claim.confidence + 0.15))  # LINE 869
claim.history.append("T6")
state.operation_history.append("T6 on {claim.id}")
```

Sub-path A2 (LLM fails or no "evidence_paths" key): lines 866 skipped; only
lines 868–869 execute.

**Path B — Anti-Delphi (`_apply_antidelphi_state_change("T6", ...)`):**

```
focus.status = "supported"
focus.confidence = max(0.82, min(1.0, focus.confidence + 0.15))
focus.history.append("T6[anti-delphi]")
```

#### 4.6.4 Output predicates

**Both paths (A and B):**

```
claim.status == "supported"
claim.confidence >= 0.82
```

**Path A, sub-path A1 additionally:**

```
len(claim.evidence_refs) increased by 1–3
```

Note on double-boost in A1: Line 866 applies `+0.15` then line 869 applies `+0.15`
again (with max(0.82, ...) on the second). Final confidence = max(0.82, min(1.0,
min(1.0, prior + 0.15) + 0.15)). Always >= 0.82.

#### 4.6.5 Branch topology effect

```
branch_effect: none
```

#### 4.6.6 Extraction confidence

```
high
```

---

### T7 — refine_qualifier

**Function:** `t7_refine_qualifier` (lines 875–896)

#### 4.7.1 Guard predicates

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
NOT (claim.evidence_refs == [] AND claim.modality != "established")
NOT (claim.status == "underspecified" OR claim.scope == {})
NOT (claim.confidence < 0.4 AND claim.status != "contradicted")
NOT (claim.modality == "hypothesis" AND claim.confidence > 0.6
     AND claim.status != "supported" AND "T6" not in claim.history)
claim.qualifier == {}
claim.scope != {}
```

#### 4.7.2 Selection and admissibility constraints

- Priority: LOW (seventh after T1–T6 primary; line 1010)
- Not in Anti-Delphi trigger set
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.7.3 State mutations

```
# Sub-path A: LLM returns result with "qualifier" key:
q = {k: v for k, v in result["qualifier"].items() if v}  # filters falsy values
claim.qualifier = q

# Unconditional:
IF claim.qualifier == {}:
    claim.qualifier = {"temporal": "present", "geographic": "global"}
claim.confidence = min(1.0, claim.confidence + 0.05)
claim.history.append("T7")
state.operation_history.append("T7 on {claim.id}")
```

The `if not claim.qualifier` guard (line 891) fires in three cases:
1. LLM fails entirely (result is None)
2. LLM returns result but without "qualifier" key
3. LLM returns qualifier dict but all values are falsy

#### 4.7.4 Output predicates

```
claim.qualifier != {}
claim.confidence == min(1.0, prior_confidence + 0.05)
```

UNCLEAR: exact value of `claim.qualifier` (LLM-dependent, but guaranteed non-empty
after the fallback guard)

#### 4.7.5 Branch topology effect

```
branch_effect: none
```

#### 4.7.6 Extraction confidence

```
high
```

---

### T8 — seal_claim

**Function:** `t8_seal_claim` (lines 899–904)

#### 4.8.1 Guard predicates

T8 has three firing paths with different guard conditions.

**Path A — Synthesis bypass (line 995–996):**

```
claim.is_synthesis == True
```

**Path B — Primary trigger (line 1012–1013):**

```
claim.is_synthesis == False
claim.status != "contradicted"
claim.conflict == False
NOT (claim.evidence_refs == [] AND claim.modality != "established")
NOT (claim.status == "underspecified" OR claim.scope == {})
NOT (claim.confidence < 0.4 AND claim.status != "contradicted")
NOT (claim.modality == "hypothesis" AND claim.confidence > 0.6
     AND claim.status != "supported" AND "T6" not in claim.history)
NOT (claim.qualifier == {} AND claim.scope != {})
claim.status == "supported"
claim.confidence > 0.8
```

Note: When `claim.branch_open == True` and all children are supported, T9 fires
before T8 primary. So T8 primary on a T1-parent requires that T9's condition is
not met (e.g., no children or not all supported), which is unusual.

**Path C — Unconditional fallback (line 1020):**

```
# No specific guard predicates — fires when no other trigger matches
```

Implicit conditions for fallback: all preceding checks in select_operation failed
to return. This includes cases where no operator explicitly matches the claim state.

#### 4.8.2 Selection and admissibility constraints

- Priority: SEAL (primary); also synthesis bypass; also unconditional fallback
- Not in Anti-Delphi trigger set
- No phase gate, confidence cap, or loop-budget gate observed in code

#### 4.8.3 State mutations

```
claim.sealed = True
claim.history.append("T8")
state.operation_history.append("T8 on {claim.id}")
```

These mutations are identical across all three firing paths. The function body
does not branch on firing path.

#### 4.8.4 Output predicates

```
claim.sealed == True
```

#### 4.8.5 Branch topology effect

```
branch_effect: terminate
```

#### 4.8.6 Extraction confidence

```
high
```

---

### T9 — trigger_reframing

**Function:** `t9_trigger_reframing` (lines 926–981)

#### 4.9.1 Guard predicates

From `select_operation` (lines 1014–1017):

```
claim.branch_open == True
count(c in state.claims where c.parent_id == claim.id) >= 1
all(c.status == "supported" for c in state.claims where c.parent_id == claim.id)
```

Note: The branch list is built as `[c for c in state.claims.values() if c.parent_id ==
claim.id]` — this collects ALL claims with `parent_id == claim.id`, regardless of
prefix (B- or C-). This includes T1-created B-branches, T5-created counters (if they
happen to have this parent_id), and any other claims assigned this parent.

Implicit guard enforced by `select_focus_claim` (not by `select_operation` directly):
`claim.sealed == False` (sealed claims are excluded from focus selection at line 1064).

Also from `select_operation` priority: T8 primary fires before T9 if `claim.status ==
"supported" AND claim.confidence > 0.8`. A T1 parent has `claim.status == "disputed"`
after T1, so T8 primary normally does not fire first. If the parent's status were
somehow "supported" + confidence > 0.8 by the time T9 checks, T8 primary would take
precedence.

From `run_des` (line 1175): `state.reframing_count > 2` terminates the loop. T9 can
fire at most 3 times per session (reframing_count goes 0 → 1 → 2 → 3; loop exits when
count > 2).

#### 4.9.2 Selection and admissibility constraints

- Priority: After T7, T8-primary (line 1014–1017); before fallback T6 and fallback T8
- Anti-Delphi interception: fires when `anti_delphi == True` AND `not focus.is_role_generated`
- Reframing count gate: T9 can fire at most 3 times (implicit via loop termination
  when `state.reframing_count > 2`)
- Focus selection prioritizes T9-ready claims before regular claims

#### 4.9.3 State mutations

**Path A — Single-agent:**

```
branches = [c for c in state.claims.values() if c.parent_id == claim.id]
# if len(branches) < 2: branches extended with branches[0] or []
ba = branches[0]
bb = branches[1]

state.claims[new_cid] = new C-prefixed Claim(
    status="supported",
    modality="suggestion",
    confidence=max(0.82, float(result.get("confidence", 0.75))),  # or 0.82 fallback
    scope=claim.scope.copy(),
    qualifier=claim.qualifier.copy(),
    is_synthesis=True,
    parent_id=claim.id,
    evidence_refs=["[synthesized from branches: {ba.id}, {bb.id}]",
                   "[SYNTHESIS{llm_note}] {rationale}"]
)
state.reframing_count += 1
claim.sealed = True
claim.history.append("T9")
state.operation_history.append("T9 on {claim.id}")
```

If `len(branches) < 2` and branches is non-empty: `ba == bb == branches[0]`
(same claim used twice). If branches is empty: `ba == bb == claim` itself.

**Path B — Anti-Delphi (`_apply_antidelphi_state_change("T9", ...)`):**

```
# For each role in ("hypothesis_builder", "falsifier"):
#   execute_role() called on focus; if succeeds:
state.claims[new_cid] = new C-prefixed Claim(
    is_role_generated=True,
    is_synthesis=False,  # default; set to True in next step
    confidence=max(0.41, min(0.55, raw_conf)),  # clamped
    parent_id=focus.id
)

# _apply_antidelphi_state_change("T9", ...):
focus.sealed = True
state.reframing_count += 1
FOR EACH role_claim_id IN role_claim_ids:
    state.claims[role_claim_id].is_synthesis = True
focus.history.append("T9[anti-delphi]")
```

Note: In Path B, `t9_trigger_reframing` is NOT called. The standard synthesis claim
(status="supported", confidence >= 0.82, is_synthesis=True) is not created. Instead,
role-generated claims are post-hoc marked as `is_synthesis = True`.

#### 4.9.4 Output predicates

**Path A (single-agent):**

```
claim.sealed == True
state.reframing_count == prior_reframing_count + 1
new_synth.status == "supported"
new_synth.modality == "suggestion"
new_synth.confidence >= 0.82
new_synth.is_synthesis == True
new_synth.parent_id == claim.id
count(new C-prefixed synth claims added) == 1
```

**Path B (Anti-Delphi):**

```
claim.sealed == True
state.reframing_count == prior_reframing_count + 1
count(new C-prefixed role-generated claims with is_synthesis == True) in {0, 1, 2}
```

UNCLEAR (Path B): `new_role_claim.confidence` in range [0.41, 0.55]  
Note: Path B does NOT guarantee any claim with `status == "supported"` and
`confidence >= 0.82` is created.

#### 4.9.5 Branch topology effect

```
branch_effect: merge
```

#### 4.9.6 Extraction confidence

```
medium
```

Reason: Anti-Delphi path has materially different output semantics from single-agent
path; edge case when `len(branches) < 2`.

---

## 5. Implementation Anomaly Audit

---

### I1 — T4 parent sealing anomaly

**Question:** Does T4 ever mark an underspecified parent as `status == "supported"`
without sufficient evidence?

**Status:** confirmed

**Code citation:** Function `t4_decompose_claim`, lines 773–774:

```python
claim.status = "supported"
claim.sealed = True
```

**Observed behavior:** T4 fires when `claim.status == "underspecified"` or
`claim.scope == {}`. At lines 773–774, the parent's status is unconditionally set
to `"supported"` and `sealed = True` immediately after sub-claims are created. No
LLM call evaluates the parent's epistemic status; the LLM is called only to generate
sub-claim content. There is no evidence check or confidence threshold applied to the
parent before sealing it as "supported". A claim with `scope == {}` (the standard
trigger, since initial claims are generated with `scope={}`) will be sealed as
"supported" regardless of its prior status, confidence, or evidence_refs content.

**Extraction confidence:** high

---

### I2 — T3 fallback anomaly

**Question:** Does T3 ever assign `status == "supported"` without successful evidence
collection (e.g., when LLM evaluation fails or is unavailable)?

**Status:** confirmed

**Code citation:** Function `evaluate_branch_claim`, lines 484–486:

```python
else:
    claim.status = "supported"
    claim.confidence = 0.85
```

**Observed behavior:** For B-prefixed claims, `t3_request_evidence` calls
`evaluate_branch_claim(claim)` (line 676). Inside `evaluate_branch_claim`, `_llm_json`
is called. If `_llm_json` returns `None` (due to LLM API failure, JSON parse failure
on both the first and retry attempts, or any other exception caught by `_llm_json`'s
try/except), the `else` branch executes unconditionally: `claim.status = "supported"`
and `claim.confidence = 0.85`. The code comment at line 473–474 confirms this is
intentional: "Falls back to supported+0.85 so T9 can always fire." The simulated
evidence string is appended to evidence_refs before evaluate_branch_claim is called
(line 673), but the LLM evaluation of that evidence can fail without altering the
fallback outcome.

**Extraction confidence:** high

---

### I3 — T9 premature synthesis anomaly

**Question:** Can T9 fire when branches are `status == "supported"` but
`sealed == False`?

**Status:** confirmed

**Code citation:** `select_operation` lines 1015–1017; `select_focus_claim`
lines 1067–1069:

In `select_operation`:
```python
branches = [c for c in state.claims.values() if c.parent_id == claim.id]
if branches and all(c.status == "supported" for c in branches):
    return "T9", t9_trigger_reframing
```

In `select_focus_claim`:
```python
children = [c for c in state.claims.values() if c.parent_id == cid]
if children and all(c.status == "supported" for c in children):
    t9_ready.append(claim)
```

**Observed behavior:** Both `select_operation` and `select_focus_claim` use
`c.status == "supported"` as the readiness criterion for T9, not `c.sealed == True`.
A branch claim receives `status = "supported"` from T6 (line 868: `claim.status =
"supported"`) and from T3's `evaluate_branch_claim` (line 482 or 485). Neither T6
nor T3 sets `claim.sealed = True`; that requires a subsequent T8 firing. Therefore:
as soon as all branch claims have status="supported" (but before T8 has sealed them),
the parent claim becomes T9-ready and T9 will fire on the next iteration where the
parent is selected as focus. T8 on the branch claims fires in a subsequent iteration
after T9 has already executed.

**Extraction confidence:** high

---

## 6. Open Questions

The following cases were marked UNCLEAR and benefit from human inspection:

**OQ1:** T2 `claim.status` — The LLM prompt for T2 shows `"suggested_status": "disputed"`
in the return template. In practice the LLM should return "disputed", but the code
uses `result.get("suggested_status", "disputed")` which accepts any string. Can the
LLM return a `suggested_status` value other than "disputed"? If so, downstream guards
that expect "disputed" may not fire.

**OQ2:** T6 Anti-Delphi history interaction — Anti-Delphi mode appends
`"T6[anti-delphi]"` to claim.history. The guard `"T6" not in claim.history` treats
this as not having fired T6. This means a claim that had Anti-Delphi T6 fire will
satisfy the T6 guard again in a subsequent iteration (if it reverts to modality ==
"hypothesis" or falls through to the fallback). Is this intended? If T6 is meant to
fire at most once per claim, the history guard should check for `"T6"` as a prefix or
use a separate flag.

**OQ3:** T9 branch collection — `t9_trigger_reframing` collects branches as
`[c for c in state.claims.values() if c.parent_id == claim.id]`. This picks up ALL
claims with this parent_id, including T5-created counter-claims (which have
`parent_id = claim.id`). If a T5 counter-claim has status="supported" and the T1
parent later becomes T9-ready, does the T5 counter appear in T9's branch list? If so,
it participates in the synthesis alongside the B-prefixed branches. Whether this is
intended or a scope-creep in the branch collection is UNCLEAR.

**OQ4:** T9 with fewer than 2 branches — `t9_trigger_reframing` handles `len(branches) < 2`
by duplicating `branches[0]` (or using `claim` as both `ba` and `bb` if branches is
empty). The guard requires `branches != []` for T9 to fire, so `ba == bb == branches[0]`
is the edge case. This produces a synthesis from a single branch (or from the parent
claim itself). Whether this is an intended edge case or a code deficiency is UNCLEAR.

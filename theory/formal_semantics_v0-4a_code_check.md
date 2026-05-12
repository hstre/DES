# DES v0.4a Code Check: Formal Semantics Validation

**Date:** 2026-05-12
**Source:** des.py (1306 lines, v0.1 prototype, unchanged)
**Scope:** Two narrow formal points. No theory additions, no cascade map, no spec comparison.

---

## Check 1 — Synthesis Persistence (P_synth)

### Question

After T9 creates a synthesis claim, can that claim be moved to `weak_candidates` or otherwise excluded from V_active before T8 sees it?

### Relevant code sections

**`t9_trigger_reframing` — synthesis claim creation (lines 958–981)**

```python
cid = new_claim_id(state)
synth = Claim(
    id=cid,
    ...
    confidence=synth_conf,       # see below
    status="supported",          # line 968
    is_synthesis=True,           # line 969
    parent_id=claim.id,
)
state.claims[cid] = synth        # line 976
claim.sealed = True              # line 978  — seals the PARENT, not synth
```

`synth_conf` (lines 947, 954):
- LLM path (line 947): `synth_conf = max(0.82, float(result.get("confidence", 0.75)))` — minimum **0.82**
- Fallback path (line 954): `synth_conf = 0.82` — also **0.82**

`sealed` is not passed to the `Claim` constructor at lines 959–971; it therefore takes the dataclass default of `False` (Claim dataclass, line 54: `sealed: bool = False`).

**`maybe_move_to_weak` — the sole demotion path (lines 1040–1046)**

```python
def maybe_move_to_weak(claim: Claim, state: EpistemicState) -> bool:
    if claim.confidence < 0.3 and claim.status != "contradicted" and not claim.sealed:
        if claim.id not in state.weak_candidates:
            state.weak_candidates.append(claim.id)
            return True
    return False
```

Demotion condition: `confidence < 0.3`.
Synthesis claim confidence: minimum 0.82.
`0.82 < 0.3` is `False`. **Demotion is structurally impossible for standard-path synthesis claims.**

`maybe_move_to_weak` is the only function in des.py that appends to `weak_candidates`. No other code path exists for demotion.

**Post-operator sweep in the main loop (lines 1224–1225)**

```python
for claim in state.claims.values():
    maybe_move_to_weak(claim, state)
```

This sweep runs immediately after every operator, including T9 (line 1222: `result = op_fn(focus, state)`). It iterates over all claims, including the newly created synthesis claim. The demotion condition fails as shown above: confidence 0.82 ≥ 0.3.

**Anti-Delphi T9 path (`_apply_antidelphi_state_change`, lines 366–372)**

In Anti-Delphi mode, T9 does not call `t9_trigger_reframing`. Instead, role-generated claims are marked `is_synthesis=True` at lines 370–372:

```python
elif trigger == "T9":
    claim.sealed = True
    state.reframing_count += 1
    for cid in role_claim_ids:
        if cid in state.claims:
            state.claims[cid].is_synthesis = True
```

Role-generated claim confidence is clamped to `max(0.41, min(0.55, raw_conf))` (line 326). Range: 0.41–0.55. `0.55 < 0.3` is `False`. **Anti-Delphi synthesis claims also cannot be demoted.**

**`select_focus_claim` — V_active exclusion conditions (lines 1063–1071)**

```python
for cid, claim in state.claims.items():
    if claim.sealed or cid in weak_set:
        continue
    if claim.branch_open:
        ...
    else:
        regular.append(claim)
```

Exclusions: sealed OR in weak_candidates. Synthesis claim: `sealed=False`, not in `weak_candidates`. Neither exclusion applies. The synthesis claim enters the `regular` bucket (line 1071, `branch_open` is `False` by default — not set in the Claim constructor at lines 959–971).

**Operators that seal claims**

- T4: seals its focus claim (line 774: `claim.sealed = True`) — only the claim T4 was called on
- T8: seals its focus claim (line 902: `claim.sealed = True`) — the intended terminal operator for synthesis claims
- T9: seals its parent focus claim (line 978: `claim.sealed = True`) — not the synthesis claim it creates

No operator seals a claim other than its current focus claim. The synthesis claim does not exist at T9-fire time; once inserted into `state.claims` (line 976), only T8 can seal it by selecting it as focus.

**Focus ordering constraint**

`select_focus_claim` iterates `state.claims.items()` in insertion order (Python dict, line 1063). The synthesis claim is the most recently inserted claim at the end of T9. Other regular claims inserted earlier have smaller τ values and will be selected first (line 1075–1076: `return regular[0]`). This means T8 may not fire on the synthesis claim in the very next iteration, but the synthesis claim **cannot leave V_active** — it remains in `regular` until T8 is selected for it.

### Verdict

**P_synth holds unconditionally in code. Verdict: guaranteed.**

| Exclusion mechanism | Applicable to synthesis claim? | Evidence |
|---------------------|-------------------------------|----------|
| `weak_candidates` demotion | No — `confidence ≥ 0.82 ≥ 0.3` threshold | Lines 1042, 947, 954 |
| Sealed by non-T8 operator | No — no operator seals non-focus claims | Lines 774, 902, 978 |
| `branch_open` gating | No — synthesis claim has `branch_open=False` | Lines 1066–1071 |

The synthesis claim remains in V_active from the moment of insertion (line 976) until T8 seals it. P_synth's formal requirement — that the synthesis claim persists in V_active for sufficiently many steps — holds without any scheduler or persistence assumption beyond the code's own structure.

---

## Check 2 — Edge* Closure Type

### Question

Does the code ever treat zero-step reachability as a cascade, or are cascades always at least one transition after the source operator?

### Relevant code sections

**Main loop structure — one operator per iteration (lines 1168–1231)**

The DES runs as a `while True` loop. Every iteration executes exactly one operator via one of two branches:

```python
if anti_delphi and trigger in ("T5", "T6", "T9") and not focus.is_role_generated:
    ...
    result = (...)           # Anti-Delphi multi-role path — one trigger, one state change
    op_name = f"{op_name}[AD]"
else:
    result = op_fn(focus, state)   # line 1222 — exactly one operator fires
```

Both branches produce exactly one operator execution per loop iteration. There is no branch that processes a state transition without firing an operator, and no branch that returns to the loop top without having executed `op_fn` or the Anti-Delphi equivalent.

**Iteration counter — monotonic increment (line 1195)**

```python
state.iteration += 1
```

This executes on every loop pass, unconditionally, before the operator fires. Zero-step reachability would require `state.iteration` to remain unchanged across a cascade step, which the code prevents structurally. The counter is also used as the termination guard (line 1172: `if state.iteration >= max_iterations: break`).

**`select_operation` — no no-op slot (lines 988–1020)**

```python
def select_operation(claim: Claim, state: EpistemicState) -> tuple[str, callable]:
    ...
    return "T8", t8_seal_claim   # line 1020 — unconditional terminal default
```

`select_operation` always returns a `(trigger_label, callable)` pair. There is no identity operator or pass-through slot. The terminal default at line 1020 ensures that even when no condition-specific guard fires, `t8_seal_claim` executes. `t8_seal_claim` itself mutates state: `claim.sealed = True` (line 902), `claim.history.append("T8")` (line 903), `state.operation_history.append(...)` (line 903). A selected claim never passes through `select_operation` without a state mutation.

**`save_state` / `load_state` — discrete step boundary (lines 124–135, 1170, 1227)**

```python
state = load_state()   # line 1170 — top of loop
...
save_state(state)      # line 1227 — bottom of loop
```

Each persisted state S_{t+1} reflects exactly one operator having fired since S_t was loaded. The persist-load cycle enforces a discrete step boundary between any two consecutive states. There is no mechanism to persist S_t as S_{t+1} without an operator having executed between the two `save_state` calls.

**No self-loop semantics**

The code contains no claim routing that returns the same claim to `select_focus_claim` in the same iteration without an intervening operator. The `select_focus_claim` function is called once per loop iteration (line 1184), after `load_state` and before `select_operation`. It cannot be called twice in one iteration. A claim selected as focus in iteration k cannot be re-selected in iteration k — the loop must complete fully (operator fires, post-bookkeeping runs, state saves, loop restarts, state loads) before any claim is re-evaluated.

### Verdict

**Transitive closure only (n ≥ 1). Reflexive-transitive closure is not needed. Verdict: transitive closure only.**

Every cascade step in the code corresponds to at least one operator firing (`state.iteration += 1`, line 1195; `op_fn(focus, state)`, line 1222). Zero-step reachability — a dispatch slot "reaching" itself or another slot without a transition — has no representation in the code. The main loop's structure makes this unconditional: each iteration fires one operator, increments the counter, and persists a new state before the next selection can occur.

The `n ≥ 1` condition in the formal Edge* definition (v0.4a §9.2) is consistent with the code: no execution path in the loop produces a state transition with n = 0.

---

## Summary

| Check | Formal property | Code verdict |
|-------|-----------------|--------------|
| P_synth — synthesis persistence | Synthesis claim remains in V_active until T8 seals it | **guaranteed** — `confidence ≥ 0.82` structurally prevents weak-demotion (threshold 0.3); no operator seals non-focus claims; lines 1042, 947, 954, 976, 978 |
| Edge* closure type | Cascades require n ≥ 1 transitions | **transitive closure only** — one operator fires per loop iteration; `state.iteration += 1` is unconditional; no identity slot in `select_operation`; lines 1195, 1222, 1020 |

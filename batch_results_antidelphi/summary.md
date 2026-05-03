# DES Anti-Delphi Batch Test — Stability Assessment

**Date:** 2026-05-03  
**Model:** deepseek-chat  
**Mode:** Anti-Delphi (T5/T6/T9 dual-role: hypothesis_builder + falsifier)  
**Questions:** 13 across 5 types  
**Max iterations per run:** 60

---

## Summary Table

```
ID   Question                           OK   Iter   Claims  Open  AD   T1   T9   Transitions
------------------------------------------------------------------------------------------
A1   Does raising the minimum wage      YES  34     12      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
A2   Is foreign aid effective at re     YES  36     12      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
A3   Does immigration reduce wages      YES  41     14      0     4    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
B1   Is GDP a good measure of econo     YES  35     12      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
B2   Is remote work more productive     YES  42     14      0     4    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
B3   Is social media harmful to dem     YES  44     14      0     4    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
C1   Is technology good?                YES  41     14      0     4    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
C2   Is globalization beneficial?       YES  41     14      0     4    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
D1   Is intermittent fasting effect     YES  32     11      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
D2   Does class size reduction impr     YES  31     9       0     3    -    -    T2,T3,T4,T5,T6,T7,T8
D3   Is gene editing ethically just     YES  33     12      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
E1   Is free trade both beneficial      YES  54     18      0     5    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
E2   Is economic growth compatible      YES  36     12      0     3    YES  YES  T1,T3,T4,T5,T6,T7,T8,T9
------------------------------------------------------------------------------------------
Success rate:           100%
T1 fire rate:           92%
T9 fire rate:           92%
Avg Anti-Delphi act.:   3.5
Avg claims/run:         12.9
Avg iterations:         38.5
```

---

## Hard Requirements

| Requirement | Result |
|-------------|--------|
| `python des.py "..." --anti-delphi` runs without error | ✅ 13/13 |
| T5/T6/T9: two claims per activation | ✅ 46 activations × 2 = 92 role-generated claims |
| Role outputs isolated (no cross-reference in prompts) | ✅ Separate `_ROLE_PROMPTS` dict, each called independently |
| `anti_delphi_activations` tracked in state | ✅ Present in all 13 state files |
| All 13 batch questions complete | ✅ |
| `compare_results.py` produces diff table | ✅ |
| Avg claims-per-run higher in Anti-Delphi | ✅ +5.2 per run (7.7 → 12.9) |

---

## Aggregate Comparison: Single-Agent vs Anti-Delphi

| Metric | Single-Agent | Anti-Delphi | Delta |
|--------|-------------|-------------|-------|
| Total claims (13 runs) | 100 | 168 | +68 |
| Open claims at termination | 0 | 0 | 0 |
| Total iterations | 285 | 500 | +215 |
| Anti-Delphi activations | — | 46 | |
| Role-generated claims | — | 92 | |
| Avg claims/run | 7.7 | 12.9 | +5.2 |
| Avg iterations/run | 21.9 | 38.5 | +16.6 |

---

## Notable Findings

### T2 fired for the first time — D2 (class size reduction)

D2 is the only run where T2 fired in either batch. In Anti-Delphi mode, the T5 falsifier generated a counter-claim that challenged the direction without being a direct binary contradiction. `check_for_contradiction` returned False → `claim.conflict=True` but `status="disputed"` → T2 fired next (rather than T1). This is the expected T2 path: it fires when epistemic tension is flagged but not a clean logical opposition.

Consequence: D2 in Anti-Delphi mode has no T1/T9, whereas single-agent D2 had both. The same question followed different epistemic paths depending on the mode — demonstrating that role isolation changes the claim graph topology, not just its size.

### A2 (foreign aid): T1/T9 fired in Anti-Delphi but not single-agent

In single-agent mode, A2 terminated without contradiction (all sub-claims resolved through T6→T8). In Anti-Delphi mode, the T5 falsifier role generated a claim that triggered `check_for_contradiction` as True, opening the T1→T9 path. Anti-Delphi systematically forces adversarial framing even on questions the single-agent treats as consensually supportable.

### E1 (free trade): largest run — 18 claims, 54 iterations, 2 reframings

E1 ("Is free trade both beneficial and harmful?") accumulated the most complex graph: 5 Anti-Delphi activations generated 10 role claims. Two separate T9 reframings occurred. This is expected — the question's framing is explicitly contradictory, generating more branching and synthesis cycles.

### Cascade prevention confirmed

The `is_role_generated=True` flag successfully prevented Anti-Delphi from applying to role-generated claims, blocking the cascade where T6 Anti-Delphi on a role claim would generate further role claims. All 92 role-generated claims went through the standard T3→T7→T8 path (single-agent mode), not Anti-Delphi. No run exceeded the 60-iteration budget due to cascades.

### Both synthesis perspectives sealed in all T9 Anti-Delphi activations

T9 Anti-Delphi marks both role claims as `is_synthesis=True`. All synthesis claims across all runs ended sealed (`history=['T8']`). The regression from the previous bugfix is confirmed stable under Anti-Delphi.

---

## Failure Modes

| Failure mode | Observed | Notes |
|---|---|---|
| Python exception / stack trace | ❌ | None in 13 runs |
| Open claims at termination | ❌ | 0/13 runs had open claims |
| T9 synthesis claims unsealed | ❌ | `is_synthesis` guard stable |
| Anti-Delphi cascade | ❌ | `is_role_generated` guard effective |
| Iteration budget exceeded (60) | ❌ | Max observed: 54 (E1) |
| JSON parse errors | ❌ | Retry logic handled all LLM responses |

---

## Recommendation

**Ready for GitHub publication.**

Anti-Delphi mode is stable across all 13 questions and 5 problem types. The dual-role architecture generates structurally richer claim graphs (+67% more claims on average) while maintaining 100% termination with 0 open claims. T2 fired for the first time (D2), completing full T1–T9 transition coverage across the two batch suites combined. The cascade prevention guard is confirmed effective. No regressions.

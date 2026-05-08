# DES 2×2 Model-Architecture Matrix — Design Memo v0.1

**Date:** 7. Mai 2026
**Branch:** des-premium/model-architecture-matrix
**Status:** PRE-REGISTERED

## Pre-registered choices

**Premium config selected: Option A — DeepSeek-R1 (deepseek-reasoner)**
Rationale: keeps falsifier (GPT-4o) constant across cheap and premium tiers,
isolating only the builder tier. Option B (Claude Sonnet) would introduce
provider heterogeneity; Option C (symmetric GPT-4o) would conflate builder
and falsifier tier changes.

**Pilot scope: M01 + N03 (2 of 5 domains)**
Rationale: R01/R04/R05 lack seeded cheap DES baselines (paper4 has single
unseeded runs only). Pilot on M01+N03 where Paper 8 Arm B provides clean
3-seed cheap DES baselines (same model config). R01/R04/R05 flagged pending.

**CoT cheap baseline: new runs required**
Existing batch_results_baseline/ uses incompatible question IDs (A1-E2)
and no seed structure. Running fresh CoT cheap on M01+N03 × seeds 101/202/303
as mandated by "Do not mix baselines from different experimental setups."

---

## Four conditions (pilot: M01+N03 × seeds 101/202/303)

| Condition | Architecture | Tier    | Builder            | Falsifier     | Status |
|-----------|-------------|---------|-------------------|--------------|--------|
| 1: DES cheap  | DES     | cheap   | deepseek-chat     | gpt-4o       | loaded from Paper 8 Arm B |
| 2: CoT cheap  | CoT     | cheap   | deepseek-chat     | —            | run fresh |
| 3: DES premium| DES     | premium | deepseek-reasoner | gpt-4o       | run fresh |
| 4: CoT premium| CoT     | premium | deepseek-reasoner | —            | run fresh |

DES = same multi-loop Anti-Delphi architecture as Papers 4-8 (no structural changes).
CoT = single-shot COT_PROMPT_TEMPLATE call, one call per domain/seed.

---

## Hypotheses

**H_arch**: DES produces lower semantic_duplication_rate and higher novel_claims_rate
than CoT at both tiers. Confirmed if arch_effect_cheap > 0 and arch_effect_premium > 0.

**H_model**: Premium builder increases depth and novel_claims_rate for DES.

**H_interaction**: Interaction term near zero (architecture and model effects independent)
or positive (DES advantage grows with premium models). Negative interaction would suggest
premium models implicitly replicate DES behavior (CoT narrows the gap).

---

## Key question

Is `interaction = arch_effect_premium - arch_effect_cheap` positive, negative, or near zero?

Positive: DES advantage grows at premium tier
Negative: DES advantage shrinks — premium CoT replicates DES epistemic structure
Near zero: effects are independent

---

## Pending

- R01/R04/R05 domains: need cheap DES runs with seeds 101/202/303 (not in Papers 4-8)
- Full 30-run batch after pilot validation
- Token cost logging (DES: approximated from loops × iterations; CoT: exact from API)

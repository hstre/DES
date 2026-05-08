# 2×2 Model-Architecture Matrix — Results

Primary metric: semantic_duplication_rate (mean across runs; lower = less redundancy)
DES depth = loops_completed; CoT depth = reasoning_steps (not directly comparable)

## Cell results

| | DES cheap | DES premium | CoT cheap | CoT premium |
|---|---|---|---|---|
| mean depth | 5 | 2.5 | 24.67 | 17.83 |
| dup_rate (mean) | 0.4456 | 0.5243 | 0.0122 | 0.0053 |
| novel_claims (mean) | 5.4867 | 8.555 | N/A | N/A |
| false_proof_rate (M01) | N/A | 0.3333 | 0 | 0 |

## 2×2 Decomposition (primary metric: dup_rate)

arch_effect_cheap   = 0.4334  (DES_cheap - CoT_cheap; negative = DES less redundant)
arch_effect_premium = 0.519  (DES_premium - CoT_premium)
model_effect_des    = 0.0787  (DES_premium - DES_cheap)
model_effect_cot    = -0.0069  (CoT_premium - CoT_cheap)
interaction         = 0.0856  (arch_premium - arch_cheap)

**Interaction interpretation**: POSITIVE: DES advantage on duplication shrinks at premium tier (CoT narrows gap)

## Domains included
M01, N03

## Pending
R01/R04/R05: no seeded cheap DES baseline in Papers 4-8 — pending full run.
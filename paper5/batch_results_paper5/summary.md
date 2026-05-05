# Paper 5 — Structured Epistemic Perturbation

## Pre-Registered Hypotheses

**H1:** Perturbation extends loop depth ≥2 vs Paper 4 on ≥3/5 domains.  
**H2:** ≥1 type produces ≥1 novel claim/loop on ≥3 domains.  
**H0:** No effect — degeneration on same schedule as Paper 4.

## Summary Results

| Domain | P4 Loops | P5 Loops | Lift | Outcome | Perturb triggered/admitted |
|---|---|---|---|---|---|
| R01 | 2 | 7 | +5 | **SEMANTIC_DUPLICATION** | 2/2 |
| R02 | 3 | 2 | -1 | **SEMANTIC_DUPLICATION** | 1/1 |
| R03 | 4 | 2 | -2 | **SEMANTIC_DUPLICATION** | 0/0 |
| R04 | 3 | 1 | -2 | **LOOP_COMPLETE** | 0/0 |
| R05 | 4 | 4 | +0 | **SEMANTIC_DUPLICATION** | 1/1 |

**Avg loop depth — Paper 4:** 3.2  
**Avg loop depth — Paper 5:** 3.2  
**Domains with depth lift ≥2:** 1/5  

## Perturbation Novelty Lift by Type

| Type | Avg novel claims (admitted loops) |
|---|---|
| scope_shift | 1.33 (n=3) |
| counterfactual | 5.00 (n=1) |
| category_flip | 0.00 (n=0) |
| time_shift | 0.00 (n=0) |
| stakeholder_flip | 0.00 (n=0) |

**Best type:** counterfactual (avg 5.00 novel claims)  

## Per-Domain Details

### R01

**Seed:** Does raising the minimum wage increase unemployment?  
**Outcome:** SEMANTIC_DUPLICATION  
**Loops:** 7 (Paper 4 baseline: 2)  

| Loop | Entropy | Novel | Dup% | Perturbed | Type |
|---|---|---|---|---|---|
| 0 | 0.45 | 11 | 27% | - |  |
| 1 | 0.50 | 1 | 7% | - |  |
| 2 | 0.58 | 0 | 33% | - |  |
| 3 | 0.57 | 0 | 14% | - |  |
| 4 | 0.79 | 0 | 57% | Y | scope_shift |
| 5 | 0.79 | 0 | 36% | Y | counterfactual |
| 6 | 0.93 | 5 | 71% | - |  |

**Perturbation log (2 events):**

- Loop 4 [scope_shift] ✓ ADMITTED → novel=0
  Q: How does the effect of raising the minimum wage on firm investment in training d
- Loop 5 [counterfactual] ✓ ADMITTED → novel=5
  Q: How does the availability of government-funded training programs in rural market

### R02

**Seed:** Is remote work more productive than office work?  
**Outcome:** SEMANTIC_DUPLICATION  
**Loops:** 2 (Paper 4 baseline: 3)  

| Loop | Entropy | Novel | Dup% | Perturbed | Type |
|---|---|---|---|---|---|
| 0 | 0.64 | 11 | 45% | Y | scope_shift |
| 1 | 1.29 | 4 | 86% | - |  |

**Perturbation log (1 events):**

- Loop 0 [scope_shift] ✓ ADMITTED → novel=4
  Q: How does remote work productivity compare to office work productivity in small t

### R03

**Seed:** Does immigration reduce wages for native workers?  
**Outcome:** SEMANTIC_DUPLICATION  
**Loops:** 2 (Paper 4 baseline: 4)  

| Loop | Entropy | Novel | Dup% | Perturbed | Type |
|---|---|---|---|---|---|
| 0 | 0.58 | 12 | 33% | - |  |
| 1 | 0.92 | 0 | 67% | - |  |

### R04

**Seed:** Is GDP a valid proxy for human wellbeing?  
**Outcome:** LOOP_COMPLETE  
**Loops:** 1 (Paper 4 baseline: 3)  

| Loop | Entropy | Novel | Dup% | Perturbed | Type |
|---|---|---|---|---|---|
| 0 | 0.29 | 7 | 14% | - |  |

### R05

**Seed:** Is intermittent fasting effective for long-term weight loss?  
**Outcome:** SEMANTIC_DUPLICATION  
**Loops:** 4 (Paper 4 baseline: 4)  

| Loop | Entropy | Novel | Dup% | Perturbed | Type |
|---|---|---|---|---|---|
| 0 | 0.43 | 14 | 21% | - |  |
| 1 | 0.36 | 1 | 18% | - |  |
| 2 | 0.86 | 0 | 43% | Y | scope_shift |
| 3 | 0.86 | 0 | 64% | - |  |

**Perturbation log (1 events):**

- Loop 2 [scope_shift] ✓ ADMITTED → novel=0
  Q: How does caloric restriction with protein-matched meal timing affect weight loss

## Hypothesis Verdict

**H1 (depth lift):** NOT CONFIRMED — 1/5 domains with ≥2 extra loops  
**H2 (novelty lift):** NOT CONFIRMED — best type 'counterfactual' (5.00 avg novel)  
**H0:** Cannot reject  

Reported honestly per pre-registration.

# Paper 5 v0.3 — Method Perturbation and Epistemic Rollback

## Pre-Registered Hypotheses

**H1:** Method perturbation extends avg loop depth > 3.2 (P4) on ≥3/5 domains.  
**H0:** No effect.  
**H2:** Perturbation drift (admission rate < 0.60 across ≥5 consecutive events).  

## Three-Way Comparison

| Domain | P4 Loops | P5v02 Loops | P5v03 Loops | Lift vs P4 | Outcome |
|---|---|---|---|---|---|
| R01 | 2 | 7 | 1 | -1 | **LOOP_COMPLETE** |
| R02 | 3 | 2 | 5 | +2 | **LOOP_COMPLETE** |
| R03 | 4 | 2 | 2 | -2 | **LOOP_COMPLETE** |
| R04 | 3 | 1 | 1 | -2 | **LOOP_COMPLETE** |
| R05 | 4 | 4 | 4 | +0 | **SEMANTIC_DUPLICATION** |

**Avg loop depth — P4:** 3.2  
**Avg loop depth — P5v02:** 3.2  
**Avg loop depth — P5v03:** 2.6  
**Domains with depth lift ≥2 vs P4:** 0/5  

## Method Metrics

| Domain | Method Diversity Score | Preventive Trigger Rate | T10 activations |
|---|---|---|---|
| R01 | 1.00 | 0% | 0 |
| R02 | 0.60 | 0% | 1 |
| R03 | 0.50 | 0% | 0 |
| R04 | 1.00 | 0% | 0 |
| R05 | 1.00 | 0% | 2 |

## Perturbation Novelty Lift by Type

| Type | Avg novel claims | n admitted |
|---|---|---|
| measurement_shift | 10.33 | 3 |
| model_assumption_shift | 0.00 | 0 |
| unit_of_analysis_shift | 0.00 | 0 |
| evidence_standard_shift | 0.00 | 0 |
| causal_mechanism_shift | 0.00 | 0 |
| counterfactual_baseline_shift | 0.00 | 0 |
| failure_mode_shift | 0.00 | 0 |

**Best type:** measurement_shift (10.33)  
**Overall admission rate:** 100%  

## Per-Domain Details

### R01

**Outcome:** LOOP_COMPLETE | Loops: 1 (P4=2, P5v02=7)  
**MDS:** 1.00 | **PTR:** 0% | **T10:** 0  

| Loop | Method | Entropy | Novel | Dup% |
|---|---|---|---|---|
| 0 | empirical_evidence | 0.14 | 7 | 0% |

### R02

**Outcome:** LOOP_COMPLETE | Loops: 5 (P4=3, P5v02=2)  
**MDS:** 0.60 | **PTR:** 0% | **T10:** 1  

| Loop | Method | Entropy | Novel | Dup% |
|---|---|---|---|---|
| 0 | empirical_evidence | 0.45 | 11 | 27% |
| 1 | unit_of_analysis | 0.73 | 0 | 55% |
| 2 | causal_mechanism | 0.50 | 9 | 25% |
| 3 | empirical_evidence | 1.00 | 0 | 64% |
| 4 | empirical_evidence | 0.50 | 0 | 40% |

**Perturbations (1):**
- Loop 1 [measurement_shift] (content) ✓ → novel=9
  Q: How does the definition and measurement of remote work environments account for 

**T10 Rollbacks (1):**
- Loop 3 → rollback to 2 [model_assumption_shift] ✓

### R03

**Outcome:** LOOP_COMPLETE | Loops: 2 (P4=4, P5v02=2)  
**MDS:** 0.50 | **PTR:** 0% | **T10:** 0  

| Loop | Method | Entropy | Novel | Dup% |
|---|---|---|---|---|
| 0 | stakeholder_perspective | 0.60 | 10 | 50% |
| 1 | stakeholder_perspective | 0.30 | 10 | 20% |

**Perturbations (1):**
- Loop 0 [measurement_shift] (content) ✓ → novel=10
  Q: How accurately do existing methods capture the long-term economic contributions 

### R04

**Outcome:** LOOP_COMPLETE | Loops: 1 (P4=3, P5v02=1)  
**MDS:** 1.00 | **PTR:** 0% | **T10:** 0  

| Loop | Method | Entropy | Novel | Dup% |
|---|---|---|---|---|
| 0 | measurement_validity | 0.10 | 10 | 0% |

### R05

**Outcome:** SEMANTIC_DUPLICATION | Loops: 4 (P4=4, P5v02=4)  
**MDS:** 1.00 | **PTR:** 0% | **T10:** 2  

| Loop | Method | Entropy | Novel | Dup% |
|---|---|---|---|---|
| 0 | empirical_evidence | 0.79 | 14 | 57% |
| 1 | temporal_validity | 0.50 | 12 | 25% |
| 3 | causal_mechanism | 0.93 | 0 | 64% |
| 4 | scope_condition | 0.91 | 0 | 73% |

**Perturbations (1):**
- Loop 0 [measurement_shift] (content) ✓ → novel=12
  Q: How do variations in the duration and frequency of fasting periods affect the ac

**T10 Rollbacks (2):**
- Loop 3 → rollback to 1 [model_assumption_shift] ✓
- Loop 4 → rollback to 1 [unit_of_analysis_shift] ✗

## Hypothesis Verdict

**H1:** NOT CONFIRMED — avg depth 2.6 vs P4 3.2, 0/5 with ≥2 lift  
**H2 (drift):** NOT CONFIRMED (no drift) — admission rate 100%  
**H0:** Cannot reject  

Reported honestly per pre-registration.

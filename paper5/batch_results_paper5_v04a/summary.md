# Paper 5 v0.4a — Frame/Metric/Shape Fixation Triggers

## Pre-Registered Hypotheses

**H1:** Frame/metric fixation triggers extend avg loop depth > 3.2 (P4) on ≥3/5 domains.  
**H0:** No effect.  
**H2:** Perturbation drift (admission rate < 0.60 across ≥5 consecutive events).  
**H3:** PTR > 0% in at least 3/5 domains (preventive trigger actually fires).  

## Three-Way Comparison

| Domain | P4 Loops | P5v03 Loops | P5v04 Loops | Lift vs P4 | Outcome |
|---|---|---|---|---|---|
| R01 | 2 | 1 | 3 | +1 | **SEMANTIC_DUPLICATION** |
| R02 | 3 | 5 | 2 | -1 | **SEMANTIC_DUPLICATION** |
| R03 | 4 | 2 | 1 | -3 | **LOOP_COMPLETE** |
| R04 | 3 | 1 | 1 | -2 | **LOOP_COMPLETE** |
| R05 | 4 | 4 | 1 | -3 | **SEMANTIC_DUPLICATION** |

**Avg loop depth — P4:** 3.2  
**Avg loop depth — P5v03:** 2.6  
**Avg loop depth — P5v04:** 1.6  
**Domains with depth lift vs P4:** 1/5  

## Frame and Method Metrics

| Domain | MDS | FDS | PTR | T10 |
|---|---|---|---|---|
| R01 | 0.67 | 0.33 | 33% | 2 |
| R02 | 0.50 | 1.00 | 0% | 0 |
| R03 | 1.00 | 1.00 | 0% | 0 |
| R04 | 1.00 | 1.00 | 0% | 0 |
| R05 | 1.00 | 1.00 | 0% | 0 |

## PTR Breakdown (across all domains)

| Trigger type | Count | % |
|---|---|---|
| frame_repeat | 0 | 0% |
| metric_repeat | 0 | 0% |
| shape_repeat | 1 | 25% |
| method_repeat | 0 | 0% |
| fallback | 3 | 75% |
| **total** | **4** | |

**Most common trigger:** fallback (3)  
**Domains with PTR > 0%:** 1/5  

## Perturbation Novelty Lift by Type

| Type | Avg novel claims | n admitted |
|---|---|---|
| measurement_shift | 5.00 | 2 |
| model_assumption_shift | 0.00 | 1 |
| unit_of_analysis_shift | 0.00 | 1 |
| evidence_standard_shift | 0.00 | 0 |
| causal_mechanism_shift | 0.00 | 0 |
| counterfactual_baseline_shift | 0.00 | 0 |
| failure_mode_shift | 0.00 | 0 |

**Best type:** measurement_shift (5.00)  
**Overall admission rate:** 100%  

## Per-Domain Details

### R01

**Outcome:** SEMANTIC_DUPLICATION | Loops: 3 (P4=2, P5v03=1)  
**MDS:** 0.67 | **FDS:** 0.33 | **PTR:** 33% | **T10:** 2  

PTR breakdown: frame=0 metric=0 shape=1 method=0 fallback=2  

| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | does_x_cause_y | 0.57 | 14 | 29% |
| 5 | effectiveness | empirical_evidence | is_x_effective | 1.29 | 0 | 93% |
| 6 | effectiveness | causal_mechanism | is_x_effective | 1.07 | 0 | 64% |

**Perturbations (3):**
- Loop 1 [measurement_shift] (fallback) ✓ → novel=0
  trigger=content_redundancy>0.40  
  Q: How do researchers accurately measure and account for the degree of employer con
- Loop 2 [model_assumption_shift] (fallback) ✓ → novel=0
  trigger=content_redundancy>0.40  
  Q: How do researchers account for variations in labor mobility and worker bargainin
- Loop 3 [unit_of_analysis_shift] (preventive) ✓ → novel=0
  trigger=shape_repeat:how_does_x_work  
  Q: How do variations in labor mobility and worker bargaining power at the industry 

**T10 Rollbacks (2):**
- Loop 4 → rollback to 0 [failure_mode_shift] ✓
- Loop 5 → rollback to 0 [evidence_standard_shift] ✓

### R02

**Outcome:** SEMANTIC_DUPLICATION | Loops: 2 (P4=3, P5v03=5)  
**MDS:** 0.50 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  

PTR breakdown: frame=0 metric=0 shape=0 method=0 fallback=1  

| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | is_x_effective | 0.73 | 11 | 55% |
| 1 | comparison | empirical_evidence | how_does_x_work | 0.91 | 10 | 73% |

**Perturbations (1):**
- Loop 0 [measurement_shift] (fallback) ✓ → novel=10
  trigger=content_redundancy>0.40  
  Q: How do different metrics for measuring productivity in remote work environments 

### R03

**Outcome:** LOOP_COMPLETE | Loops: 1 (P4=4, P5v03=2)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  

PTR breakdown: frame=0 metric=0 shape=0 method=0 fallback=0  

| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | stakeholder_perspective | does_x_cause_y | 0.38 | 8 | 25% |

### R04

**Outcome:** LOOP_COMPLETE | Loops: 1 (P4=3, P5v03=1)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  

PTR breakdown: frame=0 metric=0 shape=0 method=0 fallback=0  

| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | measurement | measurement_validity | is_x_effective | 0.30 | 10 | 20% |

### R05

**Outcome:** SEMANTIC_DUPLICATION | Loops: 1 (P4=4, P5v03=4)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  

PTR breakdown: frame=0 metric=0 shape=0 method=0 fallback=0  

| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | is_x_effective | 1.14 | 14 | 71% |

## Hypothesis Verdict

**H1:** NOT CONFIRMED — avg depth 1.6 vs P4 3.2, 1/5 with lift  
**H2 (drift):** NOT CONFIRMED (no drift) — admission rate 100%  
**H3 (PTR > 0%):** NOT CONFIRMED — PTR > 0% in 1/5 domains  
**H0:** Cannot reject  

Reported honestly per pre-registration.

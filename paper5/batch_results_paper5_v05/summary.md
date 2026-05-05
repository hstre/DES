# Paper 5 v0.5 — SPL Geometric Attractor Detection

## Pre-Registered Hypotheses

**H1:** SPL detection extends avg loop depth > 3.2 (P4) on ≥3/5 domains.  
**H0:** No effect.  
**H2:** Drift (admission rate < 0.60 across ≥5 events).  
**H4:** SPL fires in ≥3/5 domains AND avg depth > 3.2.  

## Five-Way Comparison

| Domain | P4 | P5v02 | P5v03 | P5v04a | P5v05 | Lift vs P4 | Outcome |
|---|---|---|---|---|---|---|---|
| R01 | 2 | 7 | 1 | 3 | 2 | +0 | **SEMANTIC_DUPLICATION** |
| R02 | 3 | 2 | 5 | 2 | 1 | -2 | **SEMANTIC_DUPLICATION** |
| R03 | 4 | 2 | 2 | 1 | 1 | -3 | **SEMANTIC_DUPLICATION** |
| R04 | 3 | 1 | 1 | 1 | 5 | +2 | **SEMANTIC_DUPLICATION** |
| R05 | 4 | 4 | 4 | 1 | 1 | -3 | **LOOP_COMPLETE** |

**Avg — P4:** 3.2 | **P5v02:** 3.2 | **P5v03:** 2.6 | **P5v04a:** 1.6 | **P5v05:** 2.0  
**Domains with depth lift vs P4:** 1/5  

## SPL Metrics

| Domain | MDS | FDS | PTR | SPL triggers | T10 | Avg escape dist |
|---|---|---|---|---|---|---|
| R01 | 1.00 | 1.00 | 100% | 1 | 0 | 0.274 |
| R02 | 1.00 | 1.00 | 0% | 0 | 0 | 0.000 |
| R03 | 1.00 | 1.00 | 0% | 0 | 0 | 0.000 |
| R04 | 1.00 | 0.80 | 100% | 6 | 2 | 0.152 |
| R05 | 1.00 | 1.00 | 0% | 0 | 0 | 0.000 |

## PTR Breakdown (across all domains)

| Trigger type | Count | % |
|---|---|---|
| spl | 7 | 100% |
| heuristic | 0 | 0% |
| fallback | 0 | 0% |
| **total** | **7** | |

**Domains with PTR > 0%:** 2/5  
**FALSE_ESCAPE events:** 0  
**Avg escape distance (SPL events):** 0.213  

## Novelty: SPL vs Heuristic Triggers

| Trigger type | Avg novel claims | n events |
|---|---|---|
| spl | 0.50 | 6 |
| heuristic | 0.00 | 0 |

## Per-Domain Details

### R01

**Outcome:** SEMANTIC_DUPLICATION | Loops: 2 (P4=2, P5v04a=3)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 100% | **T10:** 0  
PTR: spl=1 heuristic=0 fallback=0  

| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | 0.008 | 0.71 | 14 | 50% |
| 1 | mechanism | causal_mechanism | 0.002 | 1.14 | 1 | 86% |

**Perturbations (1):**
- Loop 0 [semantic_escape] (spl) ✓ → novel=1
  trigger=claim_proximity:0.128<0.25 dist=0.274  
  Q: How does the timing of minimum wage changes correlate with fluctuations in unemp

### R02

**Outcome:** SEMANTIC_DUPLICATION | Loops: 1 (P4=3, P5v04a=2)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  
PTR: spl=0 heuristic=0 fallback=0  

| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | 0.013 | 0.93 | 14 | 64% |

### R03

**Outcome:** SEMANTIC_DUPLICATION | Loops: 1 (P4=4, P5v04a=1)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  
PTR: spl=0 heuristic=0 fallback=0  

| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | stakeholder_perspective | 0.003 | 0.86 | 7 | 71% |

### R04

**Outcome:** SEMANTIC_DUPLICATION | Loops: 5 (P4=3, P5v04a=1)  
**MDS:** 1.00 | **FDS:** 0.80 | **PTR:** 100% | **T10:** 2  
PTR: spl=6 heuristic=0 fallback=0  

| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | measurement | measurement_validity | 0.013 | 0.64 | 14 | 21% |
| 1 | effectiveness | temporal_validity | 0.011 | 0.57 | 2 | 21% |
| 6 | scope | scope_condition | 0.004 | 1.31 | 0 | 81% |
| 7 | scope | unit_of_analysis | 0.005 | 0.57 | 0 | 14% |
| 8 | mechanism | causal_mechanism | 0.004 | 0.82 | 0 | 64% |

**Perturbations (6):**
- Loop 0 [semantic_escape] (spl) ✓ → novel=2
  trigger=claim_proximity:0.084<0.25 dist=0.274  
  Q: How do temporal changes in GDP impact long-term human wellbeing?
- Loop 1 [semantic_escape] (spl) ✓ → novel=0
  trigger=claim_proximity:0.067<0.25 dist=0.144  
  Q: How do non-economic indicators of wellbeing correlate with GDP fluctuations in d
- Loop 2 [semantic_escape] (spl) ✓ → novel=0
  trigger=claim_proximity:0.091<0.25 dist=0.108  
  Q: How do subjective measures of happiness diverge from GDP trends across various c
- Loop 3 [semantic_escape] (spl) ✓ → novel=0
  trigger=claim_proximity:0.062<0.25 dist=0.137  
  Q: What role do non-economic factors such as social support and environmental quali
- Loop 5 [semantic_escape] (spl) ✓ → novel=0
  trigger=claim_proximity:0.078<0.25 dist=0.153  
  Q: How does the interaction between social support networks and environmental condi
- Loop 7 [semantic_escape] (spl) ✗ — unanchored
  trigger=claim_proximity:0.047<0.25 dist=0.097  
  Q: How does the distribution of GDP benefits within a nation correlate with overall

**T10 Rollbacks (2):**
- Loop 4 → rollback to 1 [causal_mechanism_shift] ✓
- Loop 6 → rollback to 1 [failure_mode_shift] ✓

### R05

**Outcome:** LOOP_COMPLETE | Loops: 1 (P4=4, P5v04a=1)  
**MDS:** 1.00 | **FDS:** 1.00 | **PTR:** 0% | **T10:** 0  
PTR: spl=0 heuristic=0 fallback=0  

| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |
|---|---|---|---|---|---|---|
| 0 | effectiveness | empirical_evidence | 0.010 | 0.38 | 8 | 12% |

## Hypothesis Verdict

**H1:** NOT CONFIRMED — avg depth 2.0 vs P4 3.2, 1/5 with lift  
**H2 (drift):** NOT CONFIRMED (no drift) — admission rate 86%  
**H4 (SPL fires + depth):** NOT CONFIRMED — PTR>0% in 2/5, avg depth 2.0  
**H0:** Cannot reject  

Reported honestly per pre-registration.

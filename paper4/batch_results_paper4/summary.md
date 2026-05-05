# Paper 4 — Autonomous Epistemic Loop

## Pre-Registered Hypothesis

**H1:** DES sustains ≥20 autonomous loops per domain with entropy < 0.80, >50% contradiction resolution, and novel hypotheses past loop 20.  
**H0:** DES degenerates within 20 loops.

## Summary Results

| Domain | Outcome | Loops | Final Entropy | Novel@20 |
|---|---|---|---|---|
| R01 | **SEMANTIC_DUPLICATION** | 2 | 0.82 | — |
| R02 | **SEMANTIC_DUPLICATION** | 3 | 1.07 | — |
| R03 | **SEMANTIC_DUPLICATION** | 4 | 0.93 | — |
| R04 | **LOOP_COMPLETE** | 3 | 0.50 | — |
| R05 | **SEMANTIC_DUPLICATION** | 4 | 0.92 | — |

**H1_STABLE:** 0/5  
**H0_DEGENERATION:** 0/5  
**LOOP_COMPLETE:** 1/5  
**Failure:** 4/5  

## Per-Domain Entropy Trajectories

### R01

**Seed:** Does raising the minimum wage increase unemployment?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.67 | 0 | 12 | 12 | 5 | 23 |
| 1 | 0.82 | 0 | 11 | 0 | 7 | 22 |

**Question history:**

0. Does raising the minimum wage increase unemployment?
1. What evidence supports or refutes the claim that: Raising the minimum wage in high-competition, low-margin industries increases automation adoption rates for cashier and order-taking roles?

### R02

**Seed:** Is remote work more productive than office work?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.79 | 3 | 11 | 14 | 6 | 28 |
| 1 | 0.83 | 0 | 12 | 0 | 7 | 23 |
| 2 | 1.07 | 3 | 11 | 0 | 9 | 27 |

**Question history:**

0. Is remote work more productive than office work?
1. What is the evidence that remote work for collaborative tasks in large teams reduces objective productivity more than office work for collaborative tasks in small teams?
2. What evidence supports or refutes the claim that: remote work for collaborative tasks in small teams with low task interdependence reduces objective productivity less than office work for collaborative tasks in small teams with high task interdependence?

### R03

**Seed:** Does immigration reduce wages for native workers?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.50 | 0 | 12 | 12 | 3 | 23 |
| 1 | 0.93 | 3 | 11 | 0 | 7 | 27 |
| 2 | 0.75 | 0 | 12 | 0 | 6 | 23 |
| 3 | 0.93 | 0 | 14 | 0 | 11 | 28 |

**Question history:**

0. Does immigration reduce wages for native workers?
1. What evidence supports or refutes the claim that: High-skilled immigration into regions with low R&D intensity decreases short-term wage growth for native workers in non-tradable service sectors?
2. What is the evidence that high-skilled immigration into regions with low R&D intensity depresses short-term wage growth for native workers in non-tradable service sectors due to increased competition for housing and local infrastructure congestion native workers in non-tradable service sectors?
3. What evidence supports or refutes the claim that: high-skilled immigration into regions with low R&D intensity depresses short-term wage growth for native workers in non-tradable service sectors due to local infrastructure congestion (e.g., transport, public services), but only if the region's housing supply elasticity is below the national median?

### R04

**Seed:** Is GDP a valid proxy for human wellbeing?  
**Outcome:** LOOP_COMPLETE  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.50 | 3 | 11 | 14 | 2 | 28 |
| 1 | 0.83 | 0 | 12 | 0 | 7 | 23 |
| 2 | 0.50 | 0 | 8 | 0 | 2 | 18 |

**Question history:**

0. Is GDP a valid proxy for human wellbeing?
1. What is the evidence that GDP growth actively misaligns with national subjective well-being in countries with high ecological debt?
2. What evidence supports or refutes the claim that: GDP growth causes a decline in national subjective well-being in countries with high ecological debt when natural capital depletion exceeds a critical threshold?

### R05

**Seed:** Is intermittent fasting effective for long-term weight loss?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.42 | 0 | 12 | 12 | 2 | 23 |
| 1 | 0.86 | 3 | 11 | 0 | 7 | 28 |
| 2 | 0.86 | 2 | 12 | 0 | 8 | 28 |
| 3 | 0.92 | 0 | 12 | 0 | 8 | 23 |

**Question history:**

0. Is intermittent fasting effective for long-term weight loss?
1. What evidence supports or refutes the claim that: Intermittent fasting with structured behavioral reinforcement leads to long-term weight loss maintenance beyond one year?
2. What is the evidence that Intermittent fasting without structured behavioral reinforcement results in more sustainable weight maintenance compared to standard dietary approaches?
3. What is the evidence that Intermittent fasting with structured behavioral reinforcement produces significantly greater long-term weight loss maintenance than standard dietary approaches with equivalent behavioral reinforcement?

## Hypothesis Verdict

**H1 NOT CONFIRMED:** Only 0/5 domains reached H1_STABLE (0 H0, 4 failures, 1 LOOP_COMPLETE).  
Reported honestly per pre-registration.

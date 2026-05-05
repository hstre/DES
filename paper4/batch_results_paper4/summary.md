# Paper 4 — Autonomous Epistemic Loop

## Pre-Registered Hypothesis

**H1:** DES sustains ≥20 autonomous loops per domain with entropy < 0.80, >50% contradiction resolution, and novel hypotheses past loop 20.  
**H0:** DES degenerates within 20 loops.

## Summary Results

| Domain | Outcome | Loops | Final Entropy | Novel@20 |
|---|---|---|---|---|
| R01 | **LOOP_COMPLETE** | 4 | 0.43 | — |
| R02 | **SEMANTIC_DUPLICATION** | 1 | 1.08 | — |
| R03 | **LOOP_COMPLETE** | 5 | 0.30 | — |
| R04 | **LOOP_COMPLETE** | 1 | 0.40 | — |
| R05 | **SEMANTIC_DUPLICATION** | 2 | 1.17 | — |

**H1_STABLE:** 0/5  
**H0_DEGENERATION:** 0/5  
**LOOP_COMPLETE:** 3/5  
**Failure (SEMANTIC_DUPLICATION):** 2/5  

## Key Finding

DES reaches ClaimGraph exhaustion rapidly on well-scoped questions (R01: 4 loops,
R03: 5 loops, R04: 1 loop) — LOOP_COMPLETE is the dominant outcome.  
Broad questions (R02 remote work, R05 fasting) trigger SEMANTIC_DUPLICATION
immediately: the initial DES run generates many near-identical claims before
the loop can diversify questions.  

H1 (≥20 loops sustained) was not reached on any domain. The loop terminates
early either by ClaimGraph exhaustion or redundancy collapse — not by entropy
explosion or novelty collapse. This is an honest null result per pre-registration.

## Per-Domain Entropy Trajectories

### R01

**Seed:** Does raising the minimum wage increase unemployment?  
**Outcome:** LOOP_COMPLETE  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.71 | 2 | 12 | 14 | 6 | 28 |
| 1 | 0.71 | 1 | 13 | 1 | 7 | 28 |
| 2 | 0.64 | 0 | 11 | 0 | 5 | 22 |
| 3 | 0.43 | 0 | 7 | 0 | 2 | 17 |

**Question history:**

0. Does raising the minimum wage increase unemployment?
1. What is the evidence that raising the minimum wage increases employee turnover and training costs?
2. What is the evidence that raising the minimum wage substantially reduces employee turnover for small businesses?
3. What evidence supports or refutes the claim that: Raising the minimum wage decreases employee turnover in small businesses when combined with targeted wage subsidies?

### R02

**Seed:** Is remote work more productive than office work?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 1.08 | 0 | 12 | 12 | 10 | 23 |

**Question history:**

0. Is remote work more productive than office work?

### R03

**Seed:** Does immigration reduce wages for native workers?  
**Outcome:** LOOP_COMPLETE  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.64 | 3 | 11 | 14 | 3 | 27 |
| 1 | 0.42 | 0 | 12 | 0 | 2 | 23 |
| 2 | 0.71 | 3 | 11 | 0 | 5 | 28 |
| 3 | 0.55 | 0 | 11 | 0 | 4 | 22 |
| 4 | 0.30 | 0 | 10 | 0 | 2 | 23 |

**Question history:**

0. Does immigration reduce wages for native workers?
1. What is the evidence that Immigration of high-skilled workers to U.S. tech hubs depresses wages of low-education native workers in non-tradable low-skilled services due to increased labor supply from secondary migration of low-skilled workers?
2. What evidence supports or refutes the claim that: Secondary migration of low-skilled workers into U.S. tech hubs increases employment in low-skilled services through agglomeration demand effects, offsetting wage depression because higher overall population density in tech hubs raises local demand for non-tradable services?
3. What is the evidence that Secondary migration of low-skilled workers into U.S. tech hubs depresses wages for low-skilled service workers already in the hub more severely when the tech sector experiences a downturn because during a downturn, the demand boost from population growth weakens while the labor supply shock from secondary migration persists or intensifies?
4. What evidence supports or refutes the claim that: Secondary migration of low-skilled workers into U.S. tech hubs destabilizes wages for low-skilled service workers during a tech downturn because the influx of new workers increases labor supply in the service sector faster than demand can adjust, outweighing any population-driven demand effect?

### R04

**Seed:** Is GDP a valid proxy for human wellbeing?  
**Outcome:** LOOP_COMPLETE  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.40 | 0 | 10 | 10 | 3 | 23 |

**Question history:**

0. Is GDP a valid proxy for human wellbeing?

### R05

**Seed:** Is intermittent fasting effective for long-term weight loss?  
**Outcome:** SEMANTIC_DUPLICATION  

| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |
|---|---|---|---|---|---|---|
| 0 | 0.80 | 0 | 10 | 10 | 4 | 18 |
| 1 | 1.17 | 0 | 12 | 0 | 11 | 23 |

**Question history:**

0. Is intermittent fasting effective for long-term weight loss?
1. What evidence supports or refutes the claim that: Intermittent fasting with meal skipping has lower long-term adherence than continuous calorie restriction among individuals with high baseline dietary variability?

## Hypothesis Verdict

**H1 NOT CONFIRMED:** 0/5 domains reached H1_STABLE.
Outcomes: 3/5 LOOP_COMPLETE, 2/5 SEMANTIC_DUPLICATION, 0/5 H0_DEGENERATION.  
Reported honestly per pre-registration.

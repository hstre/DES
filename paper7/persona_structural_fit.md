# Persona Structural Fit — N03 Exploratory Analysis

**Status:** EXPLORATORY ONLY. n=3 per persona, single domain (N03). No hypothesis confirmed.  
**Configs frozen at seed303 completion. No re-runs, no threshold changes.**  
**Date:** 2026-05-05

---

## Setup

9 runs: 3 personas × 3 seeds (101, 202, 303).  
Domain: N03 — "Is artificial general intelligence achievable within 20 years?"  
P4 baseline depth: 4 loops (reference for depth_lift=0).  
All admissibility=1.0 across all admitted EN events (no rejections).

Known confound: **popper/seed101 extended by resume bug** (originally SEMANTIC_DUPLICATION at loop 3; resumed to loop 5, METHOD_COLLAPSE). Depth_lift=+2 for that run is inflated. Median is the more reliable central estimate for Popper.

---

## Metrics

### 1. mean_depth_lift (loops above P4 baseline, mean across 3 seeds)

| persona  | seed101 | seed202 | seed303 | **mean** |
|----------|---------|---------|---------|----------|
| popper   | +2 ⚠️   | 0       | 0       | **+0.67** |
| shannon  | +1      | −1      | −1      | **−0.33** |
| darwin   | +4      | +2      | +3      | **+3.00** |

⚠️ popper/seed101 resume-extended; clean-seed mean for popper = 0.00.

### 2. median_depth_lift

| persona  | sorted depths | **median** |
|----------|---------------|------------|
| popper   | [0, 0, 2]     | **0**      |
| shannon  | [−1, −1, 1]   | **−1**     |
| darwin   | [2, 3, 4]     | **+3**     |

### 3. EN_fire_rate (admitted EN injections / total loops)

| persona  | total EN | total loops | **rate** |
|----------|----------|-------------|----------|
| popper   | 6        | 14          | **0.43** |
| shannon  | 6        | 11          | **0.55** |
| darwin   | 11       | 21          | **0.52** |

Shannon fires most often per loop despite producing the least depth. Darwin fires most in absolute count (11), enabled by running longer.

### 4. novelty_recovery_rate

Definition: fraction of consecutive-loop transitions where novel_claims_t+1 > 2 × novel_claims_t.  
If novel_t = 0 and novel_t+1 > 0, this also qualifies (undefined ratio treated as ∞%).

| persona  | recovery events | transitions | **rate** |
|----------|----------------|-------------|----------|
| popper   | 2              | 11          | **0.182** |
| shannon  | 0              | 8           | **0.000** |
| darwin   | 4              | 18          | **0.222** |

Shannon: zero novelty doublings across 8 transitions. Novel counts were stable (entropy preserved) but never rebounded sharply.  
Darwin: 4 novelty doublings, including two 0→14 events. The oscillating crash-rebound pattern is a structural signature.  
Popper: modest recovery (2 events), both from post-injection loops.

### 5. duplication_recovery_rate

Definition: fraction of consecutive-loop transitions where dup drops >20 percentage points absolute (dup_t − dup_t+1 > 0.20).

| persona  | recovery events | transitions | **rate** |
|----------|----------------|-------------|----------|
| popper   | 1              | 11          | **0.091** |
| shannon  | 1              | 8           | **0.125** |
| darwin   | 2              | 18          | **0.111** |

All three personas show similar dup recovery rates (range: 0.09–0.13). No persona dominates on this measure; dup recovery is not the differentiating factor.

---

## Summary table

| metric                      | popper     | shannon    | darwin     |
|-----------------------------|------------|------------|------------|
| mean_depth_lift             | +0.67 (⚠️) | −0.33      | **+3.00**  |
| median_depth_lift           | 0          | −1         | **+3**     |
| EN_fire_rate (fires/loop)   | 0.43       | **0.55**   | 0.52       |
| novelty_recovery_rate       | 0.18       | 0.00       | **0.22**   |
| duplication_recovery_rate   | 0.09       | 0.13       | 0.11       |
| outcomes                    | 2 SEM_DUP, 1 MC (⚠️) | 1 LOOP_COMPLETE, 2 SEM_DUP | **3 METHOD_COLLAPSE** |

---

## Structural interpretation (exploratory)

**Darwin** produces the deepest runs and the highest novelty recovery rate. The signature pattern — novelty crashes to 0, then rebounds sharply after Darwin injection — suggests that evolutionary framing (selection pressures, variation sources, fitness landscapes) generates structurally distinct claim angles that are orthogonal to existing sealed claims. The injected questions force consideration of *mechanisms of change*, not just the domain state, which may be why they preserve SPL distance from the existing claim centroid even after repeated injection.

**Shannon** fires EN at the highest per-loop rate yet achieves the lowest depth (median −1). Novelty recovery rate is zero — information-theoretic reframing (channel capacity, entropy) appears to reproduce claims at a different abstraction level rather than generating structurally new angles. Shannon reduced dup in seed202 (57%→12%) but at the cost of exhausting the claim space quickly, resulting in LOOP_COMPLETE rather than extended exploration.

**Popper** shows no structural novelty recovery benefit and no depth extension (excluding the resume-inflated seed101). Falsificationist framing ("what testable prediction does this imply?") may be too close to the original claim's epistemic structure to create lateral distance in SPL space. Admitted ENI scores were comparable across personas (all ~0.47–0.55), so the difference is not in admissibility but in downstream novelty sustained.

**Dup recovery** is similar across all three personas (0.09–0.13), suggesting that the injected question's domain framing does not strongly determine whether DES reduces duplication in the next loop — that may be more a function of DES internal dynamics than persona choice.

---

## Caveats

1. **n=3 per persona, single domain.** These are cell counts, not statistical estimates. Do not treat as p-values.
2. **resume bug (popper/seed101)** artificially extends depth from 4 to 6 loops. The +2 depth_lift for that run overstates Popper's performance; median=0 is the correct reference.
3. **Python RNG seed ≠ LLM determinism.** All 9 runs produced distinct loop0_claim_hashes, confirming that seeds 101/202/303 do not control LLM output. Observed variation across seeds reflects true stochasticity, not seed-controlled variation.
4. **EN_fire_rate confound.** Deeper runs have more loops in which EN can fire, inflating absolute EN counts for Darwin. Rate (fires/loop) partially corrects this but does not fully isolate persona effect from run length effect.
5. **Admissibility=1.0 for all 27 EN events.** The Alexandria-lite gate did not reject any admitted candidate across any persona. ENI differentiation was entirely within novelty/non_drift components, not admissibility.

---

## Pre-registered status

This analysis is **not pre-registered** and was not part of the H1–H6 design memo. It was initiated as exploratory persona isolation after seed101 showed Shannon recovering dup 58%→14% in the mixed-persona condition. Results should not be cited as evidence for H2 (persona > temperature) without independent replication on additional domains.

If results replicate on ≥2 additional domains, Darwin's structural advantage (depth and novelty_recovery_rate) would constitute evidence for a structural fit hypothesis — that evolutionary framing is structurally distinct from the AGI domain's claim attractor.

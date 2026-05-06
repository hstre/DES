# Paper 7 — Appendix A: EHL Isolation Experiment

**Conditions:** EHL_1.00 (P4 baseline) | EHL_0.90 (temporal) | SPL_only (geometric)
**Domains:** R01, R02, R03, R04, R05 | **Seeds:** [101, 202, 303]
**Total runs:** 45 (target: 45)

---

## Aggregate Comparison

| Condition | Mean loops | Mean depth_lift vs EHL_1.00 | % runs positive |
|-----------|------------|----------------------------|-----------------|
| EHL_1.00  | 3.267 | — (baseline) | — |
| EHL_0.90  | 3.667 | 0.4 | 0.467 |
| SPL_only  | 3.067 | -0.2 | 0.267 |

**EHL_0.90 vs SPL_only:** +0.6 loops difference

---

## Hypothesis Verdict

**TEMPORAL_DOMINANT**

- If EHL_0.90 > SPL_only: temporal attractor is dominant mechanism
- If SPL_only > EHL_0.90: geometric attractor is dominant mechanism
- If both > EHL_1.00: mechanisms act independently

---

## Per-Run Results

| Domain | Condition | Seed | Loops | P4 | depth_lift_vs_EHL100 | Outcome | SPL_admitted |
|--------|-----------|------|-------|----|----------------------|---------|--------------|
| R01 | EHL_0.90 | 101 | 1 | 2 | 0 | LOOP_COMPLETE | 0 |
| R01 | EHL_0.90 | 202 | 3 | 2 | 0 | SEMANTIC_DUPLICATION | 0 |
| R01 | EHL_0.90 | 303 | 4 | 2 | +1 | SEMANTIC_DUPLICATION | 0 |
| R01 | EHL_1.00 | 101 | 1 | 2 | — | SEMANTIC_DUPLICATION | 0 |
| R01 | EHL_1.00 | 202 | 3 | 2 | — | SEMANTIC_DUPLICATION | 0 |
| R01 | EHL_1.00 | 303 | 3 | 2 | — | SEMANTIC_DUPLICATION | 0 |
| R01 | SPL_only | 101 | 1 | 2 | 0 | LOOP_COMPLETE | 0 |
| R01 | SPL_only | 202 | 1 | 2 | -2 | SEMANTIC_DUPLICATION | 0 |
| R01 | SPL_only | 303 | 2 | 2 | -1 | SEMANTIC_DUPLICATION | 1 |
| R02 | EHL_0.90 | 101 | 7 | 3 | +1 | LOOP_COMPLETE | 0 |
| R02 | EHL_0.90 | 202 | 2 | 3 | 0 | SEMANTIC_DUPLICATION | 0 |
| R02 | EHL_0.90 | 303 | 5 | 3 | -1 | SEMANTIC_DUPLICATION | 0 |
| R02 | EHL_1.00 | 101 | 6 | 3 | — | METHOD_COLLAPSE | 0 |
| R02 | EHL_1.00 | 202 | 2 | 3 | — | LOOP_COMPLETE | 0 |
| R02 | EHL_1.00 | 303 | 6 | 3 | — | SEMANTIC_DUPLICATION | 0 |
| R02 | SPL_only | 101 | 1 | 3 | -5 | SEMANTIC_DUPLICATION | 0 |
| R02 | SPL_only | 202 | 2 | 3 | 0 | SEMANTIC_DUPLICATION | 1 |
| R02 | SPL_only | 303 | 2 | 3 | -4 | LOOP_COMPLETE | 1 |
| R03 | EHL_0.90 | 101 | 5 | 4 | +3 | SEMANTIC_DUPLICATION | 0 |
| R03 | EHL_0.90 | 202 | 3 | 4 | +1 | SEMANTIC_DUPLICATION | 0 |
| R03 | EHL_0.90 | 303 | 2 | 4 | -4 | SEMANTIC_DUPLICATION | 0 |
| R03 | EHL_1.00 | 101 | 2 | 4 | — | LOOP_COMPLETE | 0 |
| R03 | EHL_1.00 | 202 | 2 | 4 | — | LOOP_COMPLETE | 0 |
| R03 | EHL_1.00 | 303 | 6 | 4 | — | METHOD_COLLAPSE | 0 |
| R03 | SPL_only | 101 | 2 | 4 | 0 | LOOP_COMPLETE | 1 |
| R03 | SPL_only | 202 | 4 | 4 | +2 | SEMANTIC_DUPLICATION | 3 |
| R03 | SPL_only | 303 | 2 | 4 | -4 | SEMANTIC_DUPLICATION | 1 |
| R04 | EHL_0.90 | 101 | 2 | 3 | -3 | LOOP_COMPLETE | 0 |
| R04 | EHL_0.90 | 202 | 2 | 3 | +1 | SEMANTIC_DUPLICATION | 0 |
| R04 | EHL_0.90 | 303 | 1 | 3 | 0 | LOOP_COMPLETE | 0 |
| R04 | EHL_1.00 | 101 | 5 | 3 | — | SEMANTIC_DUPLICATION | 0 |
| R04 | EHL_1.00 | 202 | 1 | 3 | — | LOOP_COMPLETE | 0 |
| R04 | EHL_1.00 | 303 | 1 | 3 | — | LOOP_COMPLETE | 0 |
| R04 | SPL_only | 101 | 13 | 3 | +8 | SEMANTIC_DUPLICATION | 9 |
| R04 | SPL_only | 202 | 1 | 3 | 0 | LOOP_COMPLETE | 0 |
| R04 | SPL_only | 303 | 3 | 3 | +2 | SEMANTIC_DUPLICATION | 2 |
| R05 | EHL_0.90 | 101 | 9 | 4 | +5 | SEMANTIC_DUPLICATION | 0 |
| R05 | EHL_0.90 | 202 | 3 | 4 | 0 | SEMANTIC_DUPLICATION | 0 |
| R05 | EHL_0.90 | 303 | 6 | 4 | +2 | SEMANTIC_DUPLICATION | 0 |
| R05 | EHL_1.00 | 101 | 4 | 4 | — | LOOP_COMPLETE | 0 |
| R05 | EHL_1.00 | 202 | 3 | 4 | — | SEMANTIC_DUPLICATION | 0 |
| R05 | EHL_1.00 | 303 | 4 | 4 | — | SEMANTIC_DUPLICATION | 0 |
| R05 | SPL_only | 101 | 4 | 4 | 0 | SEMANTIC_DUPLICATION | 3 |
| R05 | SPL_only | 202 | 6 | 4 | +3 | SEMANTIC_DUPLICATION | 4 |
| R05 | SPL_only | 303 | 2 | 4 | -2 | SEMANTIC_DUPLICATION | 1 |

---

## Per-Domain Three-Way Comparison (mean across 3 seeds)

| Domain | P4 baseline | EHL_1.00 mean | EHL_0.90 mean | SPL_only mean | EHL_0.90 lift | SPL_only lift |
|--------|-------------|---------------|---------------|---------------|---------------|---------------|
| R01 | 2 | 2.33 | 2.67 | 1.33 | +0.33 | -1.0 |
| R02 | 3 | 4.67 | 4.67 | 1.67 | 0.0 | -3.0 |
| R03 | 4 | 3.33 | 3.33 | 2.67 | 0.0 | -0.67 |
| R04 | 3 | 2.33 | 1.67 | 5.67 | -0.67 | +3.33 |
| R05 | 4 | 3.67 | 6.0 | 4.0 | +2.33 | +0.33 |

---

## Notes

- depth_lift_vs_EHL100: loops_completed − EHL_1.00_loops for same (domain, seed).
- P4 baseline: historical Paper 4 depths for reference only (different run conditions).
- SPL_only uses Paper 5 v0.5 config: detect_attractor_in_claims (epsilon=0.25,
  k_threshold=0.55), select_escape_vector composite formula.
  Secondary heuristic triggers from paper5 (frame_repeat, metric_repeat) omitted.
  content_redundancy>0.40 and novelty_zero_x3 fallbacks included.
- EHL affects claim selection weight only — does NOT modify DES state confidence.
- Seeds: Python RNG seeded per run. LLM non-determinism not controlled.
- Thresholds and DES internals unchanged.
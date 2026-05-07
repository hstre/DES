<!-- paper9_branch1/batch_results_branch1/summary -->
<!-- Paper 9 Branch 1 — Parallel Operator Expansion -->

# Paper 9 Branch 1 — Parallel Operator Expansion

## Architecture Results

| Architecture | EME score | Clusters | Total claims |
|-------------|-----------|----------|--------------|
| Arch A (merged) | 3.0277 | 4 | 65 |
| Arch B (branches) | 12.0257 | 16 | 380 |
| Arm B baseline (Paper 8) | 2.8195 | 4 | 65 |

## Hypothesis Verdicts

| Hypothesis | Verdict |
|------------|---------|
| H1: EME(arch_a) > baseline × 1.2 | H1_REJECTED |
| H2: EME(arch_b) > EME(arch_a) | H2_CONFIRMED |
| H3: EME/loop(arch_b) > EME/loop(arm_b) | H3_CONFIRMED |

## Negative Findings
- arch_a_fallback triggered: see per-run operator_log
- Arch B branches spawned: 28
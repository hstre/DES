# DES Phase A+B — Pilot Results Summary

Domains: M01, N03 | Seeds: 101, 202, 303

## Judge scores (mean across domain/seed combinations)

| Metric | DES_PHASE_A_ONLY (n=6) | DES_PHASE_A_B (n=6) | COT_PREMIUM (n=6) |
|---|---|---|---|
| Synthesis quality (1–5) | 1.667 | 2.667 | 2.667 |
| Branch preservation (1–5) | 3.333 | 3 | 2.5 |
| Gap acknowledgment (1–5) | 1.667 | 3.5 | 3 |
| Calibration (1–5) | 1 | 3.333 | 2.833 |
| False-proof avoidance (M01) | 1 | 1 | 1 |

## Hypothesis results

**H1** (Phase B value): Δsynthesis_quality(A+B − A_only) = 1.0
**H2** (vs CoT): Δsynthesis_quality(A+B − CoT) = 0.0 | Δbranch_preservation = 0.5
**H3** (termination effect): Δsq (premature) = 0.95 | Δsq (LOOP_COMPLETE) = 1.5

## Interpretation

H1: CONFIRMED — Phase B adds +1.0 synthesis quality over Phase A alone.
H2: CONFIRMED — A+B matches CoT on synthesis quality (+0.000) and exceeds it on branch preservation (+0.500).
H3: NOT CONFIRMED — premature Δ=+0.950 vs LOOP_COMPLETE Δ=+1.500 (difference not substantial).

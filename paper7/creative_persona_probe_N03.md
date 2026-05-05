# Persona Probe — N03 Full Results (All 5 Personas)

**Status:** EXPLORATORY. popper/shannon/darwin from persona isolation experiment; mozart/picasso from creative curiosity probe. n=3 per persona, single domain. No hypothesis confirmed.  
**Not pre-registered. Not confirmatory. Do not fold into Paper 7 main result.**  
**Date:** 2026-05-05 | Configs frozen. No re-runs, no threshold changes.

---

## Full Per-Run Table

| persona | seed | loops | outcome | depth_lift | EN_fired | novelty_rec | dup_rec | max_loop | claim_hash |
|---------|------|-------|---------|------------|----------|-------------|---------|----------|------------|
| popper | 101 | 6 | METHOD_COLLAPSE | +2 ⚠️ | 1 | 0.200 | 0.200 | 5 | *(null)* |
| popper | 202 | 4 | SEMANTIC_DUPLICATION | 0 | 3 | 0.000 | 0.000 | 3 | `89d301ac8d04f7a8` |
| popper | 303 | 4 | SEMANTIC_DUPLICATION | 0 | 2 | 0.333 | 0.000 | 3 | `4e2b953aa220afd4` |
| shannon | 101 | 5 | SEMANTIC_DUPLICATION | +1 | 3 | 0.000 | 0.000 | 4 | `21561194b907b185` |
| shannon | 202 | 3 | LOOP_COMPLETE | −1 | 2 | 0.000 | 0.500 | 2 | `4d91af4a42dc3c0a` |
| shannon | 303 | 3 | SEMANTIC_DUPLICATION | −1 | 1 | 0.000 | 0.000 | 2 | `478201f7f0b3dc16` |
| darwin | 101 | 8 | METHOD_COLLAPSE | +4 | 4 | 0.286 | 0.000 | 7 | `39753c2cb12a0c1f` |
| darwin | 202 | 6 | METHOD_COLLAPSE | +2 | 3 | 0.200 | 0.000 | 5 | `62a2675e6928fc93` |
| darwin | 303 | 7 | METHOD_COLLAPSE | +3 | 4 | 0.167 | 0.333 | 6 | `213fa1bec62f893c` |
| mozart | 101 | 11 | SEMANTIC_DUPLICATION | +7 | 5 | 0.400 | 0.000 | 10 | `716b5cc8e9ba3c68` |
| mozart | 202 | 9 | SEMANTIC_DUPLICATION | +5 | 4 | 0.250 | 0.125 | 8 | `4a9596049d8cdb7e` |
| mozart | 303 | 6 | LOOP_COMPLETE | +2 | 1 | 0.200 | 0.200 | 5 | `12f813cba248ce71` |
| picasso | 101 | 4 | SEMANTIC_DUPLICATION | 0 | 0 | 0.000 | 0.000 | 3 | `93c3cb659521fa72` |
| picasso | 202 | 6 | METHOD_COLLAPSE | +2 | 2 | 0.400 | 0.200 | 5 | `46b8805a7e403541` |
| picasso | 303 | 2 | SEMANTIC_DUPLICATION | −2 | 0 | 0.000 | 0.000 | 1 | `e82e15f10355d5dc` |

⚠️ popper/seed101: depth_lift=+2 is resume-inflated (resume bug extended from loop 3 → loop 5). Clean-seed mean for popper = 0.00.

novelty_rec = novelty_recovery_rate: fraction of consecutive-loop transitions where novel_t+1 > 2×novel_t, or novel_t=0 and novel_t+1>0.  
dup_rec = duplication_recovery_rate: fraction of consecutive-loop transitions where dup_t − dup_t+1 > 0.20 absolute.

---

## Per-Persona Aggregates (n=3 seeds each)

| persona | mean_depth_lift | median_depth_lift | best_run | worst_run | mean_EN | mean_nov_rec | mean_dup_rec | LOOP_COMPLETE | SEM_DUP | METHOD_COLLAPSE |
|---------|----------------|-------------------|----------|-----------|---------|-------------|-------------|---------------|---------|-----------------|
| popper | +0.67 ⚠️ | 0 | +2 ⚠️ | 0 | 2.00 | 0.178 | 0.067 | 0/3 | 2/3 | 1/3 |
| shannon | −0.33 | −1 | +1 | −1 | 2.00 | 0.000 | 0.167 | 1/3 | 2/3 | 0/3 |
| darwin | +3.00 | +3 | +4 | +2 | 3.67 | 0.218 | 0.111 | 0/3 | 0/3 | 3/3 |
| mozart | **+4.67** | **+5** | **+7** | +2 | 3.33 | **0.283** | 0.108 | 1/3 | 2/3 | 0/3 |
| picasso | 0.00 | 0 | +2 | −2 | 0.67 | 0.133 | 0.067 | 0/3 | 2/3 | 1/3 |

⚠️ popper clean-seed mean (excl. resume-inflated seed101) = 0.00, median = 0.

---

## Depth Distribution

```
persona   seed101  seed202  seed303   mean    median
popper     +2⚠️      0        0       +0.67    0
shannon    +1       −1       −1       −0.33   −1
darwin     +4       +2       +3       +3.00   +3
mozart     +7       +5       +2       +4.67   +5
picasso     0       +2       −2        0.00    0
```

---

## Structural Observations (exploratory)

**Mozart** achieves the deepest runs of any single persona tested: mean +4.67, median +5, maximum +7 (seed101, 11 loops). The oscillating crash-rebound pattern (novel crashes to ~0 then rebounds to 12–14 after EN injection) is a consistent structural signature across all three seeds. This exceeds darwin on both depth and novelty_recovery_rate (0.283 vs 0.218). Mozart's thematic-variation / modulation reframing generates questions that are structurally distinct from the existing claim centroid while remaining non-drifted (non_drift ~0.63–0.81 across injections).

**Darwin** remains the top rational persona: mean +3.00, median +3, all runs METHOD_COLLAPSE. The METHOD_COLLAPSE failure mode — all 3 seeds — suggests DES exhausts its internal operator pool before exhausting the claim space, a different failure signature from SEM_DUP. Highest mean_EN_fired (3.67) of any persona.

**Picasso** shows no systematic depth advantage: mean 0.00, median 0, worst run −2. EN fired zero times in 2 of 3 seeds — the early saturation signal did not trigger often enough to sustain extended exploration. The cubist multi-view decomposition prompt may produce claims that are too topically broad to cluster tightly enough to trigger early saturation detection.

**Shannon** is the worst performer: mean −0.33, median −1, novelty_recovery_rate=0.000 (no novelty doublings across all 8 transitions). Information-theoretic reframing reproduces claims at a different abstraction layer rather than generating structurally new angles.

**Popper** shows no clean depth benefit (median 0 excluding resume artifact). Falsificationist framing stays close to the original epistemic structure.

**Dup recovery** is similar across all personas (0.067–0.167) and does not differentiate. Depth extension is driven by novelty_recovery_rate, not dup_recovery_rate.

---

## Rank Order Summary

By median_depth_lift:

1. **mozart** — median +5, mean +4.67, nov_rec 0.283
2. **darwin** — median +3, mean +3.00, nov_rec 0.218
3. **popper** — median 0 (clean), mean 0.00, nov_rec 0.178
4. **picasso** — median 0, mean 0.00, nov_rec 0.133
5. **shannon** — median −1, mean −0.33, nov_rec 0.000

---

## Caveats

1. **n=3 per persona, single domain (N03).** These are cell counts, not statistical estimates. No p-values, no effect sizes.
2. **popper/seed101 resume bug.** depth_lift=+2 artificially inflated; median=0 is the correct reference for popper.
3. **Python RNG seed ≠ LLM determinism.** Distinct loop0_claim_hashes confirm seeds do not control LLM output.
4. **Single domain confound.** N03 (AGI achievability) may favor evolutionary/compositional framing. Results may not generalize.
5. **Mozart prompt template artifact.** LLM occasionally outputs numbered step text as part of the research question. Passes Alexandria-lite gate but reduces output quality. Not fixed — no threshold or architecture changes per protocol.
6. **Picasso EN_fire_rate confound.** Zero EN events in 2 of 3 seeds means picasso's novelty_recovery_rate is computed from a small base. Seed202 shows nov_rec=0.400 — picasso may perform better in runs where EN actually fires.
7. **Not pre-registered.** This analysis was not part of the H1–H6 design memo. Results should not be cited as confirmatory evidence without independent replication on additional domains.

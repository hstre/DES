# Math Persona Probe — M01 Full Results

**Status:** EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.  
**All mathematical claims generated are HYPOTHESES — require external verification.**  
**DES is not a math solver. It generates structured claim-space exploration, not proofs.**  
**Date:** 2026-05-05 | Domain: `M01` | n=3 per persona

---

## Seed Question

> Investigate the long-term behavior of the recursive map T(n): if n mod 3 == 0 then T(n) = n/3, if n mod 3 == 1 then T(n) = 4n+2, if n mod 3 == 2 then T(n) = 2n-1. Identify cycles, divergence patterns, invariants, and plausible conjectures.

**Known ground truth (for reference — not provided to DES):**
- T(1) = 6, T(6) = 2, T(2) = 3, T(3) = 1 → trivial 4-cycle {1, 2, 3, 6}
- n=1 is NOT a fixed point (T(1)=6). Claims of "fixed point at n=1" are errors.
- n≡1 mod 3: T(n) = 4n+2 (always yields result ≡0 mod 3 → expanding branch)
- n≡2 mod 3: T(n) = 2n−1 (always yields result ≡0 mod 3 → growing branch)
- n≡0 mod 3: T(n) = n/3 (contracting branch)

---

## 1. Trajectory Metrics

| persona | seed | loops | outcome | depth_lift | EN_fired | loop0_dup | nov_rec | dup_rec | claim_hash |
|---------|------|-------|---------|------------|----------|-----------|---------|---------|------------|
| P4_baseline | 101 | 1 | SEMANTIC_DUPLICATION | — | 0 | 0.636 | — | — | `896927592d3e43a8` |
| P4_baseline | 202 | 6 | SEMANTIC_DUPLICATION | — | 0 | 0.571 | — | — | — |
| P4_baseline | 303 | 4 | SEMANTIC_DUPLICATION | — | 0 | 0.214 | — | — | — |
| kant | 101 | 5 | SEMANTIC_DUPLICATION | **+4** | 3 | 0.500 | 0.250 | 0.000 | — |
| kant | 202 | 7 | METHOD_COLLAPSE | +1 | 3 | 0.417 | 0.333 | 0.000 | — |
| kant | 303 | 6 | SEMANTIC_DUPLICATION | +2 | 3 | 0.500 | 0.200 | 0.400 | — |
| darwin | 101 | 7 | SEMANTIC_DUPLICATION | **+6** | 5 | 0.333 | 0.167 | 0.167 | — |
| darwin | 202 | 1 | SEMANTIC_DUPLICATION | **−5** | 0 | 0.667 | — | — | — |
| darwin | 303 | 6 | SEMANTIC_DUPLICATION | +2 | 3 | 0.500 | 0.000 | 0.000 | — |
| mozart | 101 | 1 | SEMANTIC_DUPLICATION | 0 | 0 | 0.667 | — | — | — |
| mozart | 202 | 4 | SEMANTIC_DUPLICATION | −2 | 2 | 0.364 | 0.000 | 0.000 | — |
| mozart | 303 | 3 | SEMANTIC_DUPLICATION | −1 | 2 | 0.556 | 0.000 | 0.000 | — |

**P4 baseline loops (seed-specific):** seed101=1, seed202=6, seed303=4.  
depth_lift for persona runs = loops_completed − p4_baseline_loops[seed].  
nov_rec = novelty_recovery_rate; dup_rec = duplication_recovery_rate.

### Per-Persona Summary

| persona | mean_depth_lift | median_depth_lift | best | worst | mean_EN | mean_nov_rec | mean_dup_rec | LOOP_COMPLETE | SEM_DUP | METHOD_COLLAPSE |
|---------|----------------|-------------------|------|-------|---------|-------------|-------------|---------------|---------|-----------------|
| P4_baseline | — | — | 6 loops | 1 loop | 0.00 | — | — | 0/3 | 3/3 | 0/3 |
| kant | **+2.33** | **+2** | +4 | +1 | 3.00 | 0.261 | 0.133 | 0/3 | 2/3 | 1/3 |
| darwin | +1.00 | +2 | +6 | −5 | 2.67 | 0.056 | 0.056 | 0/3 | 3/3 | 0/3 |
| mozart | −1.00 | −1 | 0 | −2 | 1.33 | 0.000 | 0.000 | 0/3 | 3/3 | 0/3 |

**M01 rank by median_depth_lift:** kant (+2) > darwin (+2) > P4_baseline (N/A) > mozart (−1).

---

## 2. Mathematical Content Quality

### P4_baseline / seed 101
- **Found fixed point error (n=1):** YES — claims "exactly one nontrivial cycle beyond the fixed point at n=1". T(1)=6, n=1 is in the 4-cycle {1,6,2,3}, not a fixed point.
- **Found trivial cycle {1,2,3,6}:** No (claimed "one nontrivial cycle" implicitly referencing it but with incorrect framing)
- **Cycles claimed:** T(n) has exactly one nontrivial cycle
- **Useful conjectures:** T(n) has exactly one nontrivial cycle (unverified)
- **Quality: LOW** — fixed point error, no structural breakdown by residue class, rapid collapse (1 loop)

### P4_baseline / seed 202
- **Found fixed point error:** No
- **Found trivial cycle:** No
- **Cycles claimed:** T(n) does not contain 2-cycles for inputs ≡ 5 mod 18
- **Divergence claimed:** potential 2-cycle existence for some residue classes
- **Convergence claimed:** T(n) for inputs ≡ 5 mod 6 converges to a stable attractor
- **Useful conjectures:** No 2-cycles for n ≡ 5 mod 18 — *mod-18 specificity (18=2×3²) suggests systematic residue decomposition*
- **Quality: MODERATE** — mod-18 analysis is mathematically targeted; no verification

### P4_baseline / seed 303
- **Cycles claimed:** abstract cycle existence
- **Divergence claimed:** hidden divergent trajectory may exist
- **Convergence claimed:** multiples of 3 that are not powers of 3 converge
- **Quality: MODERATE** — "hidden divergent trajectory" is an interesting exploratory claim; powers-of-3 subclass analysis plausible

### kant / seed 101
- **Invariants claimed:** n mod 3 congruence class determines eventual invariant subspace; n mod 3 determines distinct set of transient states before reaching attractor
- **Conjectures:** n mod 3 is a necessary a priori precondition for trajectory class; each residue class mod 3 defines a distinct basin of attraction
- **Quality: HIGH** — correctly identifies n mod 3 as the key structural classifier. "Invariant subspace" claim is mathematically motivated and likely correct. No domain escape.

### kant / seed 202
- **Invariants claimed:** threshold behavior is determined by combinatorial divisibility conditions
- **Conjectures:** Typical-case statistics require additional measure-theoretic assumptions beyond mod-3 classification
- **Quality: HIGH** — stays on-domain. Drift into prime factorization framing at loop 5 is related but indirect. METHOD_COLLAPSE suggests DES operator exhaustion before semantic saturation.

### kant / seed 303
- **Invariants claimed:** a priori invariant properties of modular arithmetic ensure classification of initial conditions; mod-3 classification stability is independent from transient chaotic dynamics
- **Divergence claimed:** transient chaotic dynamics can obscure classification stability
- **Conjectures:** classification stability by n mod 3 and transient chaos are independent properties; modular arithmetic invariants are a priori (not empirical)
- **Quality: HIGH** — introduction of "transient chaotic dynamics" is mathematically interesting. T(n) has expanding branches (n≡1: 4n+2 grows) that could exhibit transient chaos before convergence to cycle.

### darwin / seed 101
- **Convergence claimed:** initial values with a contiguous block of exactly three 1-bits in binary expansion show statistically significant shift in convergence times
- **Conjectures:** numbers with exactly three consecutive 1-bits in binary expansion have distinct convergence behavior; residue classes form evolutionary fitness landscapes for T(n)
- **Quality: MODERATE** — binary 1-bit block claim is highly specific with no obvious mathematical justification; selection pressure analogy is metaphorical. Deepest darwin run (+6) despite false-return EN pattern (eni declining 0.541→0.497 over 5 EN events).

### darwin / seed 202
- **Cycles claimed:** T(n) for n≡1 mod 3 eventually enters a finite cycle for all sufficiently large n
- **Divergence claimed:** T(n) for n≡1 mod 3 diverges or enters finite cycle with probability approaching 0.5
- **Conjectures:** All n≡1 mod 3 trajectories either converge to finite cycle or diverge — no other possibility
- **Quality: HIGH (single loop only)** — n≡1 mod 3 is the expanding branch; whether all such trajectories cycle or diverge is the core mathematical question. Most focused claims of any run. dup=66.7% forced immediate SEM_DUP before EN could fire.

### darwin / seed 303
- **Cycles claimed:** cycles of specific period exist with basin sizes determined by residue structure
- **Conjectures:** parity and residue class mod 3 are neither necessary nor sufficient alone to determine basin size; intrinsic number properties (parity + residue) jointly determine cycle stability
- **Quality: MODERATE** — best early-loop novelty in dataset (16, 14, 12) but complete novelty collapse after loop 2. Parity+residue joint claim is mathematically plausible.

### mozart / seed 101
- **Found fixed point error (n=1):** YES — claims "exactly one nontrivial cycle for all positive integer starting values a single attractor fixed point". T(1)=6≠1.
- **Cycles claimed:** exactly one nontrivial cycle
- **Quality: LOW** — immediate collapse (1 loop, no EN), fixed point error. Mozart's loop0 claims are copies of the P4 seed framing rather than novel transformation.

### mozart / seed 202
- **DOMAIN ESCAPE:** Terminal claims are about "diversity of initial opinion clusters" and "resilience of community decision-making" — mathematically irrelevant to T(n).
- **Domain escape target:** community decision-making / opinion cluster dynamics
- **Quality: NONE** — complete domain escape. No T(n) claims in terminal state.

### mozart / seed 303
- **DOMAIN ESCAPE:** Terminal claims about "modular interaction patterns in social networks" analogous to "logistic map's periodic doubling".
- **Domain escape target:** social network modular interaction patterns
- **Cycles claimed:** period-doubling bifurcations in social networks analogous to logistic map
- **Quality: LOW** — logistic map / period-doubling analogy is structurally interesting but has no direct bearing on T(n). Partial domain escape.

---

## 3. False Proof / Hallucinated Proof Count

**Total false proof / hallucinated proof events: 0**  
No run generated a formal proof claim that was verifiably false. No run claimed to have proved convergence, divergence, or cycle structure with logical derivation.

**Fixed point errors: 2**  
- P4_baseline/seed101: "fixed point at n=1" — WRONG. T(1)=4(1)+2=6.
- Mozart/seed101: "single attractor fixed point" referencing n=1 — WRONG. T(1)=6.

Both errors appear in loop0 claims (before any EN injection), inherited from the initial seed framing and not corrected.

**Erroneous / unverified convergence claims:**
- "all trajectories converge to a single attractor" (P4/101) — UNVERIFIED. Whether all positive integers eventually cycle is unknown.
- "T(n) has exactly one nontrivial cycle" (P4/101, Mozart/101) — UNVERIFIED. Could be more cycles or diverging trajectories.
- "T(n) for n≡1 mod 3 eventually enters a finite cycle for all sufficiently large n" (Darwin/202) — UNVERIFIED but the most mathematically precise claim.

---

## 4. Useful Conjectures Generated

| # | conjecture | source | assessment |
|---|-----------|--------|-----------|
| 1 | n mod 3 is a necessary structural classifier for trajectory type | kant/101, kant/303 | **Plausibly correct** — mod-3 residue determines branch function |
| 2 | Each residue class mod 3 defines a distinct basin of attraction | kant/101 | **Plausibly correct** — basins may differ structurally |
| 3 | mod-3 classification stability is independent from transient chaotic dynamics | kant/303 | **Interesting** — if T(n) has transients, this could be testable |
| 4 | T(n) for n≡1 mod 3 either enters finite cycle or diverges (dichotomy) | darwin/202 | **Mathematically precise** — identifies the core open question |
| 5 | Parity and residue mod 3 are neither necessary nor sufficient alone to determine basin size | darwin/303 | **Plausible** — joint characterization claim |
| 6 | No 2-cycles exist for n ≡ 5 mod 18 | P4/202 | **Specific and testable** — mod-18 residue decomposition |
| 7 | Numbers with exactly three consecutive 1-bits in binary expansion have distinct convergence | darwin/101 | **Speculative** — no obvious justification, but testable |
| 8 | Hidden divergent trajectory may exist in the map | P4/303 | **Exploratory** — standard conjecture for recursive maps |

**Most mathematically motivated:** Conjectures 1–4 align with known structure of the map. Conjecture 6 (mod-18) is the most arithmetically specific.

---

## 5. Persona-Specific Behavior

### Kant — Best on M01 (median depth_lift +2)

Kant's transcendental method naturally maps to formal mathematical structure. The Kantian framing ("what are the necessary a priori conditions?") directly invites boundary condition analysis and invariant identification. On T(n), this translates to: what conditions on n are necessary for a given trajectory class? Kant correctly and consistently identified n mod 3 across all three seeds.

**EN events:** All 9 Kant EN events were admitted and on-domain. eni_novelty declining from 0.18 → 0.10 across loops signals the standard late-phase local variation pattern (not a persona-specific failure). eni_non_drift consistently 0.77–0.89 — Kant's questions stay close to the seed domain.

**METHOD_COLLAPSE (seed202, loop7):** Operator exhaustion — DES exhausted its question operators before semantic saturation. The prime factorization drift at loop5 EN suggests Kant begins extending to related number-theoretic domains when T(n)-specific questions are exhausted.

**False proof count: 0.** Kant generates claims framed as structural preconditions, not proof claims. The distinction between empirical observation and structural necessity is implicitly maintained (though not explicitly flagged by DES).

### Darwin — High variance on M01 (mean +1.0, median +2, range −5 to +6)

Darwin's evolutionary framing stays on-domain but generates highly specific conjectures about particular structural features (binary 1-bit blocks, fitness landscapes). Seed101's 7-loop run (+6 depth_lift) is the deepest single run of any persona on M01, driven by 5 EN events. However, EN exhibits a false-return pattern: eni_novelty declines from 0.146 → 0.104 over 5 events, with nov_next=0 after loops 2, 4, and 5 — EN fires but generates no new claims. The deepening is structural persistence, not genuine novelty recovery.

**Seed202 catastrophic outlier (depth_lift=−5):** dup=66.7% at loop0 caused immediate SEM_DUP before EN could fire. Darwin's loop0 claims about n≡1 mod 3 are the most mathematically focused of any single-loop run — but the run terminates immediately. This is a domain characteristic: T(n) claims cluster tightly in SPL space. High dup at loop0 is not a Darwin-specific failure.

**Binary representation framing:** Darwin/101 generated a highly specific conjecture about "exactly three contiguous 1-bits in binary expansion". This is a detectable signature of evolutionary framing applied to number theory — the system identifies a "fitness landscape feature" (binary structure) without obvious mathematical justification.

### Mozart — Worst on M01 (median depth_lift −1, domain escape rate 2/3)

Mozart's thematic transposition strategy — identify the dominant motif, transpose to a different conceptual register, return transformed — causes domain escape on formal mathematical domains. In 2 of 3 seeds, the "modulation" step carries T(n) into unrelated domains (community decision-making, social network dynamics) and the system never returns to the original mathematical structure.

**Domain escape mechanism:** Mozart's first EN event (loop0) transposes T(n)'s "iterative sequence" motif to "opinion cluster convergence" (seed202) or "modular interaction patterns in social networks" (seed303). Since DES's admissibility gate checks for lexical overlap with existing claims, and the new claims reference social dynamics rather than T(n), subsequent EN events reinforce the social dynamics framing rather than returning to the math.

**Seed101 immediate collapse:** Mozart/seed101 produces no EN (loop0 only, dup=0.667) and inherits the P4 baseline's fixed-point error. No transposition was attempted.

**Performance inversion:** Mozart was the best persona on N03 (AGI/empirical domain, median depth_lift +5). On M01 (formal math domain), Mozart is worst (median −1). The transposition strategy that generates depth on argumentative claims generates domain escape on formal structural claims.

**False proof count: 1** (fixed point error in seed101 loop0 — inherited from P4 baseline framing, not a proof claim per se).

---

## 6. EN Event Detail (persona runs)

### kant / seed 101

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1311 | 0.8112 | 0.1888 | 0.5089 | True | 12 |
| 1 | 0.0774 | 0.8977 | 0.1023 | 0.5080 | True | 2 |
| 2 | 0.1284 | 0.8827 | 0.1173 | 0.5290 | True | 5 |

### kant / seed 202

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1343 | 0.7696 | 0.2304 | 0.4980 | True | 14 |
| 2 | 0.0859 | 0.8664 | 0.1336 | 0.5029 | True | 6 |
| 5 | 0.0657 | 0.8318 | 0.1682 | 0.4824 | True | 5 |

### kant / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1826 | 0.8364 | 0.1636 | 0.5422 | True | 12 |
| 1 | 0.1568 | 0.8883 | 0.1117 | 0.5449 | True | 12 |
| 3 | 0.1063 | 0.8915 | 0.1085 | 0.5206 | True | 3 |

### darwin / seed 101

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1461 | 0.8936 | 0.1064 | 0.5412 | True | 11 |
| 2 | 0.1426 | 0.8690 | 0.1310 | 0.5320 | True | 0 |
| 3 | 0.0834 | 0.8511 | 0.1489 | 0.4970 | True | 4 |
| 4 | 0.1209 | 0.8227 | 0.1773 | 0.5073 | True | 0 |
| 5 | 0.1041 | 0.8176 | 0.1824 | 0.4973 | True | 0 |

Darwin/101 EN pattern: 3 of 5 events produce nov_next=0. EN fires but fails to generate novel claims post-injection. eni_novelty declining envelope (0.146→0.104) indicates terminal attractor entered by loop 3.

### darwin / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1543 | 0.9229 | 0.0771 | 0.5540 | True | 14 |
| 1 | 0.0618 | 0.9042 | 0.0958 | 0.5021 | True | 12 |
| 3 | 0.0636 | 0.8956 | 0.1044 | 0.5005 | True | 0 |
| 4 | (no admitted EN) | | | | | 0 |

### mozart / seed 202

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.1056 | 0.9039 | 0.0961 | 0.5240 | True | 9 |
| 2 | 0.1109 | 0.8537 | 0.1463 | 0.5116 | True | 0 |

Mozart/202: loop0 EN transposes to community decision-making. nov_next=9 at loop1 (social dynamics claims, not T(n)). Loop2 EN reinforces social dynamics. Terminal state: fully escaped.

### mozart / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next |
|------|-------------|---------------|-------|---------------|----------|----------|
| 0 | 0.2255 | 0.8153 | 0.1847 | 0.5573 | True | 14 |
| 1 | 0.1539 | 0.8256 | 0.1744 | 0.5246 | True | 12 |

Mozart/303: High novelty trace before collapse (9→14→12). Both EN events use "modular interaction patterns in social networks" framing. Novel claims generated are about social network dynamics, not T(n).

---

## 7. Cross-Domain Comparison: M01 vs N03

| persona | N03 median_depth_lift | M01 median_depth_lift | delta |
|---------|----------------------|----------------------|-------|
| mozart | **+5** | **−1** | −6 |
| darwin | +3 | +2 | −1 |
| kant | (not run on N03) | +2 | — |
| popper | 0 | (not run on M01) | — |
| picasso | 0 | (not run on M01) | — |
| shannon | −1 | (not run on M01) | — |

**Ranking inversion:** Mozart #1 on N03, last on M01. Darwin modest decline. Kant best on M01 (not tested on N03).

**Structural interpretation:**

*Mozart's thematic transposition* produces depth on argumentative/empirical domains (AGI achievability) by carrying claims across conceptual registers within the same discursive space. On formal mathematical domains, the same transposition carries claims out of the domain entirely (social networks, opinion dynamics). This is the same mechanism acting differently — the failure mode is not persona-specific randomness but a structural mismatch between Mozart's operator and formal mathematical content.

*Kant's boundary-condition / necessary-precondition strategy* is better calibrated for formal domains. Mathematical structures have natural boundary conditions (residue classes, cycle lengths) and necessary preconditions (divisibility, modular arithmetic). Kant's transcendental framing matches these structural features.

*Darwin's evolutionary framing* stays on-domain in both settings but at reduced depth in M01 (seed202 catastrophic outlier brings mean to +1.0). The binary 1-bit block conjecture suggests Darwin applies "fitness landscape" metaphors to number-theoretic structure, generating specific but potentially arbitrary structural claims.

---

## 8. Caveats

1. **n=3 per persona, single domain.** Cell counts only. No statistical inference.
2. **LLM is not a math solver.** DES generates structured claim-space exploration, not proofs. All mathematical claims are HYPOTHESES.
3. **All generated claims require external verification.** Do not treat as proved.
4. **Fixed point detection is keyword-based.** "Fixed point" and "fixed_point" patterns may miss implicit claims or produce false positives.
5. **Domain escape detection is manual.** Terminal claim content was examined; automated detection would require semantic classification.
6. **Thresholds and architecture unchanged** from N03 runs. No parameter tuning between domains.
7. **High initial dup (0.50–0.67) in math domain** reflects tight SPL clustering of T(n)-related claims. This is a domain characteristic, not a DES failure.
8. **Darwin/202 catastrophic outlier (depth_lift=−5)** is driven by loop0 dup=66.7% causing immediate SEM_DUP before EN fires. The loop0 claims are mathematically the most focused in the dataset.
9. **Mozart/101 fixed point error** is inherited from P4 baseline loop0 framing, not generated by Mozart's transposition mechanism.
10. **Not pre-registered.** This analysis was not part of the H1–H6 design memo. Results should not be cited as confirmatory evidence.

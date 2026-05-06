# Math Persona Probe — M01

**EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.**  
**All mathematical claims generated are HYPOTHESES — require external verification.**  
**Date:** 2026-05-05 | Domain: `M01`

## Seed Question

> Investigate the long-term behavior of the recursive map T(n): if n mod 3 == 0 then T(n) = n/3, if n mod 3 == 1 then T(n) = 4n+2, if n mod 3 == 2 then T(n) = 2n-1. Identify cycles, divergence patterns, invariants, and plausible conjectures.

---

## Trajectory Metrics

| persona | seed | loops | outcome | depth_lift | EN_fired | loop0_dup | claim_hash |
|---------|------|-------|---------|------------|----------|-----------|------------|
| P4_baseline | 101 | 1 | SEMANTIC_DUPLICATION | — | 0 | 0.6364 | `896927592d3e43a8` |
| P4_baseline | 202 | 6 | SEMANTIC_DUPLICATION | — | 0 | 0.5714 | `5f97339b2e7b4ee6` |
| P4_baseline | 303 | 4 | SEMANTIC_DUPLICATION | — | 0 | 0.2143 | `a1d8502c4251781d` |
| kant | 101 | 5 | SEMANTIC_DUPLICATION | +4 | 3 | 0.5 | `3c817e2e86e9b8cf` |
| kant | 202 | 7 | METHOD_COLLAPSE | +1 | 3 | 0.4167 | `154336ee6c55a291` |
| kant | 303 | 6 | SEMANTIC_DUPLICATION | +2 | 3 | 0.5 | `72c9f15b26a73e66` |
| darwin | 101 | 7 | SEMANTIC_DUPLICATION | +6 | 5 | 0.3333 | `dc59206853356a59` |
| darwin | 202 | 1 | SEMANTIC_DUPLICATION | -5 | 0 | 0.6667 | `12e55797309d4a6c` |
| darwin | 303 | 6 | SEMANTIC_DUPLICATION | +2 | 3 | 0.5 | `b6863ee191da556c` |
| mozart | 101 | 1 | SEMANTIC_DUPLICATION | — | 0 | 0.6667 | `297ee7ebccb3c8ee` |
| mozart | 202 | 4 | SEMANTIC_DUPLICATION | -2 | 2 | 0.3636 | `4425acac53697748` |
| mozart | 303 | 3 | SEMANTIC_DUPLICATION | -1 | 2 | 0.5556 | `9889e32d8004b078` |

---

## Mathematical Content — Detected Concept Hits

*(Keyword scan of sealed claims at terminal loop — not a proof of presence or absence.)*

### P4_baseline / seed 101
- **cycles**: 11 claim(s)
  - *the recursive map t(n) on positive integers has exactly one nontrivial cycle beyond the fixed point at n=1...*
  - *the recursive map t(n) on positive integers has exactly one nontrivial cycle beyond the fixed point at n=1...*
- **fixed_points**: 10 claim(s)
  - *the recursive map t(n) on positive integers has exactly one nontrivial cycle beyond the fixed point at n=1...*
  - *the recursive map t(n) on positive integers has exactly one nontrivial cycle beyond the fixed point at n=1...*

### P4_baseline / seed 202
- **cycles**: 11 claim(s)
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 does not contain...*
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 does not contain...*
- **fixed_points**: 2 claim(s)
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 converges to a s...*
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 cannot have any ...*
- **divergence**: 3 claim(s)
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 does not contain...*
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 could have 2-cyc...*
- **convergence**: 1 claim(s)
  - *the recursive map t(n) with mod-3 branching (n/3, 4n+2, 2n-1) for inputs congruent to 5 mod 6 converges to a s...*

### P4_baseline / seed 303
- **cycles**: 10 claim(s)
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
- **fixed_points**: 12 claim(s)
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
- **divergence**: 6 claim(s)
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
- **convergence**: 5 claim(s)
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*
  - *the recursive map t(n) defined by t(n) = n/3 for n ≡ 0 mod 3, t(n) = 4n+2 for n ≡ 1 mod 3, t(n) = 2n-1 for n ≡...*

### kant / seed 101
- **invariants**: 9 claim(s)
  - *the congruence class of an initial natural number n modulo 3 determines the eventual invariant subspace of t(n...*
  - *the congruence class of an initial natural number n modulo 3 determines the eventual invariant subspace of t(n...*
- **divergence**: 3 claim(s)
  - *the congruence class of an initial natural number n modulo 3 affects the length of transient mixing before rea...*
  - *the congruence class of an initial natural number n modulo 3 affects the length of transient mixing before rea...*

### darwin / seed 101
- **convergence**: 11 claim(s)
  - *initial values n0 with a contiguous block of exactly three 1-bits in their binary expansion exhibit a statisti...*
  - *initial values n0 with a contiguous block of exactly three 1-bits in their binary expansion exhibit a statisti...*

### darwin / seed 202
- **cycles**: 12 claim(s)
  - *the recursive map t(n) for n ≡ 1 mod 3 eventually enters a finite cycle for all sufficiently large n...*
  - *the recursive map t(n) for n ≡ 1 mod 3 eventually enters a finite cycle for all sufficiently large n...*
- **divergence**: 1 claim(s)
  - *the recursive map t(n) for n ≡ 1 mod 3 diverges or enters a finite cycle with probability approaching 0.5 for ...*

### darwin / seed 303
- **cycles**: 11 claim(s)
  - *the combined effect of parity and residue classes modulo higher powers is neither necessary nor sufficient to ...*
  - *the combined effect of parity and residue classes modulo higher powers is sufficient to determine the basin si...*

### mozart / seed 101
- **cycles**: 11 claim(s)
  - *the recursive map t(n) has exactly one nontrivial cycle for all positive integer starting values a single attr...*
  - *the recursive map t(n) has exactly one nontrivial cycle for all positive integer starting values a single attr...*
- **fixed_points**: 9 claim(s)
  - *the recursive map t(n) has exactly one nontrivial cycle for all positive integer starting values a single attr...*
  - *the recursive map t(n) has exactly one nontrivial cycle for all positive integer starting values a single attr...*
- **convergence**: 1 claim(s)
  - *the recursive map t(n) with n ≡ 0 mod 3 has no nontrivial cycle and converges to the fixed point 0 for all pos...*

### mozart / seed 202
- **cycles**: 1 claim(s)
  - *skewness of initial opinion cluster sizes in a community inversely predicts resilience of community decision-m...*

### mozart / seed 303
- **cycles**: 5 claim(s)
  - *modular interaction patterns in social networks exhibit convergence rates and recurrence intervals analogous t...*
  - *modular interaction patterns in social networks exhibit convergence rates analogous to the logistic map's peri...*
- **divergence**: 8 claim(s)
  - *modular interaction patterns in social networks exhibit convergence rates and recurrence intervals analogous t...*
  - *modular interaction patterns in social networks exhibit recurrence intervals analogous to the logistic map's c...*
- **convergence**: 5 claim(s)
  - *modular interaction patterns in social networks exhibit convergence rates and recurrence intervals analogous t...*
  - *modular interaction patterns in social networks exhibit convergence rates analogous to the logistic map's peri...*

---

## EN Event Detail (persona runs)

### kant / seed 101

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1311 | 0.8112 | 0.1888 | 0.5089 | True | 12 | To apply Kant's transcendental method to the recursive map \ |
| 1 | 0.0774 | 0.8977 | 0.1023 | 0.508 | True | 2 | **Research Question:** How does the congruence class of an i |
| 2 | 0.1284 | 0.8827 | 0.1173 | 0.529 | True | 5 | **Research Question:** How does the congruence class of an i |

### kant / seed 202

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1343 | 0.7696 | 0.2304 | 0.498 | True | 14 | To apply Kant's transcendental method to the recursive map \ |
| 2 | 0.0859 | 0.8664 | 0.1336 | 0.5029 | True | 6 | Research Question: What are the a priori conceptual categori |
| 5 | 0.0657 | 0.8318 | 0.1682 | 0.4824 | True | 5 | Research Question: 

What are the a priori conceptual catego |

### kant / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1826 | 0.8364 | 0.1636 | 0.5422 | True | 12 | To apply Kant's transcendental method to the recursive map \ |
| 1 | 0.1568 | 0.8883 | 0.1117 | 0.5449 | True | 12 | **Research Question:**

How does the divisibility condition  |
| 3 | 0.1063 | 0.8915 | 0.1085 | 0.5206 | True | 3 | Research Question: What are the a priori invariant propertie |

### darwin / seed 101

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1461 | 0.8936 | 0.1064 | 0.5412 | True | 11 | How do initial conditions influence the eventual cycle or di |
| 2 | 0.1426 | 0.869 | 0.131 | 0.532 | True | 0 | Research Question: How does the presence of a contiguous blo |
| 3 | 0.0834 | 0.8511 | 0.1489 | 0.497 | True | 4 | Research Question: How does the presence of a contiguous blo |
| 4 | 0.1209 | 0.8227 | 0.1773 | 0.5073 | True | 0 | Research Question: How do the selection pressures exerted by |
| 5 | 0.1041 | 0.8176 | 0.1824 | 0.4973 | True | 0 | What are the effects of the selection pressure exerted by th |

### darwin / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1543 | 0.9229 | 0.0771 | 0.554 | True | 14 | Research Question: How do the initial conditions and number  |
| 1 | 0.0618 | 0.9042 | 0.0958 | 0.5021 | True | 12 | How do variations in initial conditions and intrinsic number |
| 3 | 0.0636 | 0.8956 | 0.1044 | 0.5005 | True | 0 | Research Question: How do intrinsic number properties such a |
| 4 | None | None | 1.0 | None | None | 0 |  |

### mozart / seed 202

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.1056 | 0.9039 | 0.0961 | 0.524 | True | 9 | 1. **Identify the dominant motif**: The central assumption i |
| 2 | 0.1109 | 0.8537 | 0.1463 | 0.5116 | True | 0 | 1. **Identify the dominant motif**: The central assumption i |

### mozart / seed 303

| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |
|------|-------------|---------------|-------|---------------|----------|----------|----------------------|
| 0 | 0.2255 | 0.8153 | 0.1847 | 0.5573 | True | 14 | 1. **Identify the Dominant Motif:**

The central taken-for-g |
| 1 | 0.1539 | 0.8256 | 0.1744 | 0.5246 | True | 12 | **Research Question:** How do modular interaction patterns w |

---

## Caveats

1. **n=3 per persona.** Cell counts only. No statistical inference.
2. **LLM is not a math solver.** DES generates structured claims, not proofs.
3. **All mathematical claims require external verification.** Do not treat as proved.
4. **False proof detection is keyword-based.** May miss subtle or implicit proof claims.
5. **Thresholds and architecture unchanged** from N03 runs.
6. **Not pre-registered.**
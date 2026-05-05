# Paper 6 — Phase 1 Results: Retrograde SH Validation

## Summary

Computed semantic headroom (SH) from existing P4 and P5v05 loop_000_state.json
files for all 5 domains (R01–R05). No new DES runs required.

---

## SH Values (P4 loop 0)

| Domain | Seed question (abbrev)                         | SH     | SH_norm | SH_ent | n  | P4 depth | P5v05 depth | lift |
|--------|------------------------------------------------|--------|---------|--------|----|----------|-------------|------|
| R01    | Does raising the minimum wage reduce employ... | 0.0630 | 0.2258  | 0.9659 | 12 | 2        | 2           | +0   |
| R02    | Does social media use cause depression...      | 0.0732 | 0.2531  | 0.9698 | 11 | 3        | 1           | -2   |
| R03    | Does remote work reduce productivity?          | 0.0689 | 0.2469  | 0.9813 | 12 | 4        | 1           | -3   |
| R04    | Does GDP growth improve human wellbeing?       | 0.1019 | 0.3524  | 0.9785 | 11 | 3        | 5           | +2   |
| R05    | Is intermittent fasting effective...           | 0.0711 | 0.2550  | 0.9764 | 12 | 4        | 1           | -3   |

---

## Correlation Analysis

| Correlation | Spearman ρ | Pearson r |
|-------------|-----------|-----------|
| SH vs P4 depth | 0.105 | 0.027 |
| SH vs depth lift (P5v05 - P4) | 0.359 | 0.692 |

**H1 verdict: NOT CONFIRMED** (ρ = 0.105 < 0.70 required)

PHASE1 = SH_NOT_PREDICTIVE (ρ < 0.50)

Note: Pearson r = 0.692 for SH vs depth lift is moderate but n=5 is insufficient
for robust inference. Spearman is primary metric (pre-registered); Pearson reported
as exploratory only.

---

## SH* Estimate

SH* = 0.0876 (midpoint between R02 SH=0.0732 and R04 SH=0.1019)

Binary classifier accuracy on Phase 1 data:
- R04 (SH=0.1019 > SH*): lift=+2 → correctly classified as HIGH
- R01/R02/R03/R05 (SH < SH*): lift≤0 → all correctly classified as LOW
- 5/5 = 100% correct (but n=5, no holdout set — not a valid estimate of accuracy)

---

## SH_entropy Observation

SH_entropy (normalized entropy of centroid distribution) is uniformly high
across all domains (0.966–0.981). This metric does NOT discriminate between
domains. All DES-produced ClaimGraphs span all 10 relation types at roughly
equal weight. SH_entropy is not useful as a predictor in this setting.

Implication: SH_distance (mean √JSD distance from centroid) is the only
informative SH variant. The centroid entropy definition in the design memo
(SH_entropy) measures a different property and should not be used as primary.

---

## Key Finding

R04 (GDP/wellbeing) is the only domain with SH > SH*. It is also the only
domain where SPL trajectory control extended loop depth (+2).

The remaining 4 domains cluster tightly in Π (SH 0.063–0.073) compared to
R04 (SH 0.102). The absolute difference is small but consistent: R04's claims
are systematically more spread across relational types.

**Why R04?** GDP/wellbeing naturally generates claims across causal, conditional,
correlational, normative, and evidential relation families. The other domains
(minimum wage, remote work, fasting) generate claims that cluster in the
evidential/causal band.

---

## Phase 1 Conclusion

H1 formally not confirmed (ρ < 0.50 failure condition met).

However, SH correctly predicts the only domain (R04) where perturbation helped,
using a threshold of SH* = 0.0876. The failure is in the P4-depth correlation
(R03/R05 have P4 depth=4 despite low SH, because DES internal diversity drives
their P4 performance, not semantic headroom).

**Revised hypothesis for Phase 2:** SH predicts depth lift under perturbation
(H2), not P4 depth alone (H1). H2 requires Phase 2 validation.

Proceed to Phase 2 with explicit caveat: SH as predictor of P4 depth is not
confirmed. SH as binary classifier for perturbation benefit is supported by
Phase 1 data but requires prospective validation.

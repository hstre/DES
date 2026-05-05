# Paper 6 — Phase 3 Summary
**Controlled Comparison: P4 vs P5v05 on High-SH Domains**
**Status: Exploratory (n=2, below pre-registered minimum of 3)**

---

## Design

Phase 3 runs the two confirmed high-SH domains from Phase 2 under both configs:
- **P4**: no perturbation (result already in Phase 2 data)
- **P5v05**: SPL attractor detection + semantic escape

Primary metric: `depth_lift = P5_depth − P4_depth`

SH* = 0.0876 (locked from Phase 1, unchanged).

**Note:** Pre-registered minimum was n≥3 high-SH domains. Only 2 confirmed (N03, N05).
Phase 3 proceeds as exploratory only — H2 cannot be confirmed or refuted.

---

## Results

| Domain | SH_loop0 | P4 depth | P5 depth | depth_lift | SPL events | avg_escape_dist | PTR   | Outcome          |
|--------|----------|----------|----------|------------|------------|-----------------|-------|------------------|
| N03    | 0.1065   | 4        | 1        | **−3**     | 0          | 0.000           | 0.000 | SEMANTIC_DUPL.   |
| N05    | 0.0941   | 3        | 9        | **+6**     | 8          | 0.239           | 0.889 | SEMANTIC_DUPL.   |

**Benefit rate: 1/2 = 50%** (H2 threshold: ≥60% for confirmation, <40% for refutation)
**H2 verdict: EXPLORATORY_NOT_SUPPORTED** (inconclusive at n=2)

---

## Domain Narratives

### N03 — AGI Timeline (SH=0.1065, depth_lift=−3)

N03 had the higher SH of the two domains yet showed strongly negative lift. SPL never triggered — the DES reached SEMANTIC_DUPLICATION in loop 0 before the claim_proximity threshold (<0.25) was crossed. This is an early-saturation failure mode: the graph collapsed so quickly that perturbation had no opportunity to intervene.

P4 had achieved depth=4 for this domain; P5v05 terminated at loop=1. The paradox (higher SH, worse P5 outcome) may reflect topic brittleness: "Is AGI achievable within 20 years?" generates a narrow, highly clustered claim space that exhausts rapidly under any config. SH at loop 0 measured headroom that existed at the start of a fresh loop but was consumed before the end of that same loop.

### N05 — Economic Inequality / Social Cohesion (SH=0.0941, depth_lift=+6)

N05 showed consistent positive response to SPL perturbation. SPL triggered in every loop (loops 0–7), each time detecting claim_proximity below threshold and generating a lateral escape question. All 8 events were admitted by the novelty gate.

The escape questions ranged across: historical distribution patterns → cultural narratives → spatial wealth distribution → urban architecture → intergenerational infrastructure → public art installations → local history in transit systems. Each question opened a new conceptual frame that delayed semantic saturation for roughly one additional loop.

**Key observation:** `novelty_produced_next_loop = 0` for all 8 SPL events. SPL did not introduce individually novel claims in the immediately following loop, but it did prevent claim_proximity from triggering early termination — extending exploration by +6 loops overall. The mechanism appears to be distributional rather than additive: escape questions redistribute semantic mass in Π rather than adding genuinely new claims.

PTR (perturbation tolerance ratio) = 0.889: 8 of 9 loops were "perturbation-active" loops where SPL was engaged.

---

## Interpretation

### What the contrast reveals

The N03/N05 contrast exposes two failure modes:

1. **Pre-SPL saturation (N03):** High SH at loop 0 does not prevent rapid graph collapse if the topic generates densely overlapping claims. SPL cannot rescue a domain that saturates within the first loop.

2. **SPL-sustained exploration (N05):** Moderate SH with a topic that generates moderately-distributed claims allows SPL to maintain claim_proximity below threshold across many loops, extending depth substantially.

### SPL mechanism re-assessment

The zero `novelty_produced_next_loop` across all 8 N05 events suggests SPL's primary effect is **distributional suppression of semantic convergence** rather than injection of genuinely novel content. Escape questions reframe the existing problem space; they do not introduce new knowledge. This matters for the SPL design: the value is in preventing attractor lock-in, not in expanding the claim frontier.

### Why H2 remains unresolved

The benefit rate of 50% is mathematically inconclusive. More importantly, the two domains differ not just in SH but in topical structure (contested empirical claim vs. normative-empirical mixture), so the comparison conflates SH effects with topic effects. A proper H2 test requires n≥5 high-SH domains matched on topic type.

---

## Anomalies

**SH rank vs. lift rank inverted:** N03 (higher SH=0.1065) showed negative lift; N05 (lower SH=0.0941) showed large positive lift. This contradicts the implicit prediction of H2. Possible explanations:
- SH at loop 0 measures potential headroom, not realized headroom — rapid saturation can consume it before SPL triggers
- The AGI topic may be inherently more semantically constrained than economic inequality
- n=2 is too small to distinguish real pattern from noise

**FALSE_ESCAPE concern (from Paper 5 design):** None observed. All 8 SPL events had escape_dist in range 0.172–0.360, none exceeded the 0.40 FALSE_ESCAPE threshold. The escape vectors were semantically plausible lateral moves, not hallucinated outliers.

---

## Phase 3 Metrics

| Metric                    | Value        |
|---------------------------|--------------|
| n_domains                 | 2 (exploratory) |
| perturbation_benefit_rate | 0.50         |
| H2_verdict                | EXPLORATORY_NOT_SUPPORTED |
| SH* (locked)              | 0.0876       |
| N05 avg_escape_dist       | 0.239        |
| N05 PTR                   | 0.889        |
| N03 SPL events            | 0            |
| N05 SPL events            | 8            |

---

## What Would Be Needed for H2

- ≥5 confirmed high-SH domains (requires SH* recalibration or larger Phase 2 sample)
- Matched topic types across P4/P5v05 pairs
- At least 3 domains where SPL has opportunity to trigger (not pre-SPL saturation)

Phase 3 as run is insufficient to confirm or refute H2. The N05 result is encouraging (+6 lift, consistent SPL engagement) but is a single data point and cannot bear the weight of the hypothesis.

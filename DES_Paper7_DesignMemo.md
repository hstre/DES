# Beyond Semantic Headroom:
# Exogenous Noise Injection and Epistemic Half-Life
# as Anti-Collapse Mechanisms in Autonomous Research Loops

**Version:** 0.3
**Date:** 5. Mai 2026
**Status:** Pre-registered

---

## PART 1: DESIGN MEMO

### Core Thesis

> Attractors appear semantic, but are partially temporal.
> Old claims bend the search space toward their own neighborhood.
> EHL addresses the temporal component. EN addresses the variation component.

Semantic convergence in autonomous research loops emerges from three factors:

1. Semantic similarity (claims cluster in Π)
2. Temporal claim persistence (old claims dominate question selection too long)
3. Insufficient exogenous variation (no external perspective breaks the pattern)

Paper 5 (SPL) addressed factor 1 by detecting attractor proximity and injecting escape vectors. Paper 7 attacks factors 2 and 3 simultaneously:

- **Epistemic Half-Life (EHL):** exponential decay on claim selection weight as a function of loop age — old claims become less likely to anchor the next question
- **Exogenous Noise (EN):** structured injection of externally-framed questions (persona, adjacent-domain, or high-temperature) before semantic saturation takes hold

The two mechanisms are orthogonal and can be combined. The experimental design tests them independently and together via the SH-scheduled arm.

---

### Motivation from Paper 6

Paper 6 Phase 3 exposed a critical failure mode: N03 (AGI timeline, SH=0.1065) collapsed in 1 loop under P5v05 — SPL never triggered because SEMANTIC_DUPLICATION occurred before claim_proximity fell below threshold. Pre-SPL saturation defeats any proximity-based intervention. EHL and preventive EN specifically target this pre-SPL gap: they act before saturation, not in response to it.

The "temporal claim persistence" hypothesis: in N03, early loop-0 claims established a dense cluster. Without decay, all subsequent question selection was anchored to that cluster, which reproduced rather than extended the claim space. EHL would have down-weighted loop-0 claims in loops 1+, freeing the selector to prefer newer, more peripheral claims.

---

### Pre-Registered Hypotheses

**H1:** EN extends loop depth in early-saturation domains (depth_noise > depth_P4)
**H2:** Persona noise outperforms temperature noise (ENI_persona > ENI_temp)
**H3:** Adjacent-domain noise produces highest novelty but highest drift
**H4:** Noise must be preventive — inject before semantic_dup > 40%
**H5:** Moderate EHL improves loop depth vs no decay (depth_EHL_0.90 > depth_EHL_1.00)
**H6:** Extreme decay harms loop depth (depth_EHL_0.50 < depth_EHL_0.90)

---

### Experimental Conditions

```python
EXPERIMENTAL_CONDITIONS = {
    "P4_baseline":    {"en": None,       "ehl": 1.00},
    "EN_temperature": {"en": "temp",     "ehl": 1.00},
    "EN_persona":     {"en": "persona",  "ehl": 1.00},
    "EN_adjacent":    {"en": "adjacent", "ehl": 1.00},
    "EHL_0.90":       {"en": None,       "ehl": 0.90},
    "EHL_0.50":       {"en": None,       "ehl": 0.50},   # stress test only
    "SH_scheduled":   {"en": "sh_select", "ehl": "sh_select"},  # exploratory
}
```

**EHL_0.50** is a stress test — expected to show Over-Decay Collapse (ODC). Results labeled accordingly.

**SH_scheduled** is exploratory — uses SH_STAR = 0.0876 locked from Paper 6 Phase 1 to select EN vs EHL adaptively. Not a primary hypothesis arm; included to probe the SH→intervention signal.

---

### Domains

- **N03** (AGI timeline, SH=0.1065): primary early-saturation test case from Paper 6
- **N05** (economic inequality, SH=0.0941): confirmed SPL-responsive domain from Paper 6
- Paper 4/5 baseline domains (R01–R05): 5 domains for cross-paper depth comparison
- 4–5 new domains spanning the SH range

---

### Implementation Constraints

- DES internals NOT modified (`des.py` = black-box via Python import)
- SPL files NOT modified (`spl.py`, `nlp_backend.py`)
- EHL = claim-weight wrapper only; does NOT change `des_state.json` confidence values
- EN = additional prompt layer before question selection
- Alexandria-lite gate unchanged from Paper 5/6
- No new models (DeepSeek-Chat / GPT-4o stack unchanged)

---

### EN Injection Timing (H4: Preventive)

EN is triggered by `early_saturation_detected()` — a forward-looking signal that fires before SEMANTIC_DUPLICATION:

- Very early warning: `semantic_dup > 0.30` in loop 0 or 1
- Novelty halved vs previous loop
- Two consecutive loops with `novel_claims == 0`
- Duplication spike: `Δdup > 0.15` in one loop

This ensures EN fires before the graph is fully saturated — not as a rescue from an already-failed state.

---

### ENI Metric

ENI (Exogenous Noise Index) is reported as four separate components, not a pure product (pure multiplication collapses to 0 when admissibility=0, obscuring partial value):

| Component | Weight | Measure |
|-----------|--------|---------|
| `eni_novelty` | 0.5 | √JSD distance from claim centroid in Π |
| `eni_non_drift` | 0.3 | 1 − distance from seed question in Π |
| `eni_admissibility` | 0.2 | Alexandria-lite gate (binary) |
| `eni_composite` | — | Weighted mean of above |

---

### EHL Claim Selection

EHL down-weights old claims in the question-selection step:

```
weight(claim) = decay ^ (current_loop - seal_loop)
```

`seal_loop` = `claim["sealed_at_loop"]` if available in state; otherwise first-seen loop (logged as fallback). Selection uses seeded random for reproducibility; seed logged per event.

Over-Decay Collapse (ODC) guard: if `decay < 0.85` and last 3 loops show `novel_claims=0` and `dup_rate > 0.50`, the run terminates with outcome `ODC` rather than continuing.

---

### SH Scheduler (Exploratory)

```python
SH_STAR = 0.0876  # locked from Paper 6 Phase 1

def sh_schedule(sh: float) -> dict:
    if sh < SH_STAR:
        return {"en": None, "ehl": 0.90}    # low headroom → EHL
    else:
        return {"en": "persona", "ehl": 1.00}  # high headroom → EN
```

Labeled `EXPLORATORY` in all summaries. Paper 6 did not confirm SH as a monotone intervention selector; the SH-scheduled arm tests this signal prospectively.

---

### Output Structure

```
paper7/batch_results_paper7/
  {domain_id}_{condition}/
    loop_000_state.json ... loop_NNN_state.json
    metrics.json
    en_log.json       # EN events: all candidates (admitted + rejected), ENI components, seeds
    ehl_log.json      # claim age weights per loop
    outcome.json
  summary.json        # all conditions × all domains, H1–H6 verdicts
  summary.md          # human-readable cross-condition report
```

---

### Summary Must Report

Per condition × domain:
- Loop depth vs P4 baseline (lift)
- EN events: triggered / admitted / ENI components (all 4)
- EHL: avg claim age at termination, ODC count
- Which EN type had highest eni_composite?

Cross-domain:
- H1–H6 verdicts
- EN type ranking: persona vs adjacent vs temperature
- EHL benefit: EHL_0.90 vs EHL_1.00 vs EHL_0.50
- SH-scheduled arm vs unscheduled (exploratory)

---

### Acceptance Criteria

- [x] Branch `paper7/noise-and-halflife` created, memo committed first
- [ ] EHL uses seeded random (log seed per event)
- [ ] EHL uses `sealed_at_loop` from state if available
- [ ] ENI reported as 4 separate components (not pure product)
- [ ] EN triggered by `early_saturation_detected` (preventive)
- [ ] SH scheduler labeled as exploratory arm in summary
- [ ] EHL_0.50 labeled as stress test in summary
- [ ] ODC failure mode checked when decay < 0.85
- [ ] All EN candidates logged (admitted AND rejected)
- [ ] No DES internals modified, no SPL modified, no new models

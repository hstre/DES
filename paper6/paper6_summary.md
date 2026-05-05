# Paper 6 — Semantic Headroom Study: Full Summary
**WP2 (Rentschler 2026)**
**Three-phase design. SH* = 0.0876 locked from Phase 1.**

---

## Research Questions

**H1:** Does SH at loop 0 correlate with P4 loop depth (Spearman ρ > 0.50)?
**H2:** Do high-SH domains show greater depth lift under SPL perturbation (P5v05 vs P4) in ≥60% of cases?
**H3:** Does pre-run SH (10-claim probe) predict post-loop-0 SH (Spearman ρ > 0.70)?

SH (Semantic Headroom) = mean(√JSD(π(cᵢ), centroid(claims))) — mean distance of sealed ClaimGraph claims from their centroid in Π.

SH* = 0.0876 — binary classifier threshold, estimated from Phase 1 Phase 1 retrograde data as the midpoint between max(non-positive) and min(positive) depth-lift cases. **Locked after Phase 1; not recalibrated.**

---

## Phase 1 — Retrograde Analysis (n=5)

Retrograde computation of SH from existing P4/P5 state files (R01–R05). No new runs.

| Metric | Value |
|--------|-------|
| SH vs P4 depth (Spearman ρ) | 0.105 |
| SH vs depth_lift (Spearman ρ) | 0.359 |
| SH* binary classifier accuracy | 5/5 = 100% (**training accuracy only**) |
| H1 verdict | NOT CONFIRMED (ρ=0.105, threshold 0.50) |

Phase 1 finding: SH does not predict raw P4 depth in the small retrograde sample. The binary classifier (SH > SH*) achieves 5/5 on its own training data — this is not a prediction and cannot be reported as accuracy. Phase 2 is the first true prospective test.

SH_entropy was uniformly ~0.97 across all Phase 1 domains — not discriminative.

---

## Phase 2 — Prospective Prediction (n=13)

13 new domains run under P4 config (no perturbation). SH predicted before each run using a 10-claim pre-run probe; actual SH measured at loop 0. Binary classifier (SH > SH*) applied to actual loop-0 SH.

### Correlations

| Metric | Value | Threshold | Verdict |
|--------|-------|-----------|---------|
| SH_prerun vs SH_loop0 (Spearman ρ) | **0.709** | > 0.70 | H3 **CONFIRMED** |
| SH_loop0 vs depth (Spearman ρ) | **0.739** | > 0.50 | H1 CONFIRMED (Phase 2) |
| SH_loop0 vs depth (Pearson r) | 0.573 | — | — |

### Binary classifier accuracy (Phase 2 = true prediction accuracy)

| Class | n | Correct | Accuracy |
|-------|---|---------|----------|
| LOW (SH ≤ 0.0876) | 6 | 6 | 100% |
| HIGH (SH > 0.0876) | 7 | 2 | 29% |
| **Overall** | **13** | **8** | **61.5%** |

Phase 2 prediction accuracy: **8/13 = 61.5%**

LOW domains were predicted perfectly. HIGH domains were largely misclassified — most clustered at SH 0.07–0.09, just below SH* = 0.0876. The threshold from Phase 1 (n=5) is likely calibrated too high for general use.

### H1 Re-assessment

Phase 1: ρ=0.105 (NOT CONFIRMED). Phase 2: ρ=0.739 (CONFIRMED). The Phase 2 result supersedes Phase 1 for H1, using prospective data. The discrepancy likely reflects Phase 1's small and unrepresentative sample (n=5 retrograde).

### H3 Confirmed

Pre-run SH (10-claim probe, no DES run) predicts actual loop-0 SH at ρ=0.709, just at the pre-registered threshold of 0.70. H3 is confirmed: a lightweight probe can estimate SH before committing to a full run.

---

## Phase 3 — Controlled Comparison (exploratory, n=2)

**Pre-registered minimum: n≥3 high-SH domains. Only 2 confirmed. Phase 3 = exploratory.**

High-SH domains from Phase 2: N03 (AGI, SH=0.1065) and N05 (economic inequality, SH=0.0941). Each run under P5v05 (SPL perturbation). Depth lift = P5_depth − P4_depth.

### Results

| Domain | SH_loop0 | P4 depth | P5 depth | depth_lift | SPL events | avg_escape_dist | PTR   |
|--------|----------|----------|----------|------------|------------|-----------------|-------|
| N03 (AGI) | 0.1065 | 4 | 1 | **−3** | 0 | 0.000 | 0.000 |
| N05 (inequality) | 0.0941 | 3 | 9 | **+6** | 8 | 0.239 | 0.889 |

**Benefit rate: 1/2 = 50%**
**H2 verdict: EXPLORATORY_NOT_SUPPORTED** (50% < 60% threshold; n=2 inconclusive)

### N03 failure mode

SPL never triggered. DES reached SEMANTIC_DUPLICATION in loop 0, before claim_proximity fell below the 0.25 threshold. Early saturation: the AGI topic generated a tight, highly convergent claim space that exhausted before perturbation could intervene. P5 depth (1) was worse than P4 depth (4).

### N05 success mode

SPL triggered in every loop (0–7), consistently detecting claim_proximity below threshold. All 8 escapes admitted. The escape questions ranged across: historical distribution → cultural narratives → spatial wealth → urban architecture → intergenerational infrastructure → public art → transit history. Depth extended to 9 loops vs P4's 3.

**Key finding:** `novelty_produced_next_loop = 0` for all 8 SPL events. SPL did not introduce individually novel claims in the immediately following loop. Its effect is distributional: escape questions redistribute semantic mass in Π, preventing convergence, without expanding the claim frontier per se.

### Anomaly: SH rank vs. lift rank inversion

N03 had higher SH (0.1065 > 0.0941) yet showed large negative lift. This contradicts the H2 prediction. Possible explanation: SH at loop 0 measures potential headroom at the start of the loop, but rapid saturation within that same loop consumes it before SPL can activate. SH is a snapshot metric; the dynamic that matters is how quickly the topic generates convergent claims — which SH does not directly capture.

---

## Cross-Phase Summary

| Hypothesis | Phase 1 | Phase 2 | Phase 3 | Final verdict |
|------------|---------|---------|---------|---------------|
| H1: SH predicts P4 depth (ρ>0.50) | NOT CONFIRMED (ρ=0.105) | **CONFIRMED** (ρ=0.739) | — | **CONFIRMED** (Phase 2 prospective) |
| H2: High-SH → depth lift ≥60% | — | — | EXPLORATORY_NOT_SUPPORTED (50%, n=2) | **UNRESOLVED** |
| H3: Pre-run SH predicts loop-0 SH (ρ>0.70) | — | **CONFIRMED** (ρ=0.709) | — | **CONFIRMED** |

---

## Key Findings

1. **SH predicts depth prospectively.** Phase 2 ρ=0.739 is substantially stronger than Phase 1 ρ=0.105. The Phase 1 result was likely an artefact of the small, unrepresentative retrograde sample.

2. **The pre-run probe works.** H3 confirmed: 10 LLM-generated claims projected into Π before any DES run achieves ρ=0.709 with actual loop-0 SH. This enables lightweight SH estimation without running DES.

3. **SH* = 0.0876 is calibrated too high.** From Phase 1 n=5, it achieves 100% on training data but only 29% precision on Phase 2 HIGH predictions. Most domains cluster just below the threshold. For future work, SH* should be re-estimated on a larger calibration set (n≥20).

4. **SPL mechanism is distributional, not additive.** In N05, 8 SPL events all showed novelty_produced_next_loop=0, yet depth increased by +6. SPL prevents attractor lock-in by redistributing semantic mass; it does not inject new knowledge. This distinction matters for understanding when and why SPL helps.

5. **Pre-SPL saturation defeats perturbation.** N03 illustrates a failure mode invisible to SH: topics that generate densely convergent claims can saturate before the perturbation threshold is ever reached, regardless of initial SH. A dynamic convergence rate metric (e.g., δ_proximity per loop) may be more predictive of SPL utility than static SH.

6. **H2 remains unresolved.** Phase 3 ran with n=2 below the pre-registered minimum of n≥3. The 50% benefit rate is inconclusive. A proper H2 test requires ≥5 matched high-SH domains.

---

## Limitations

- **Phase 1 n=5:** Retrograde sample is small and non-random (selected from existing P4/P5 runs). SH* from this sample may not generalize.
- **SH* lock constraint:** Pre-registration required locking SH* after Phase 1. This prevented recalibration after observing Phase 2 distribution, which would have improved classifier performance.
- **Simulated LLM calls:** All DES runs use simulated LLM responses (DEEPSEEK/OpenRouter). Real-world SH distributions may differ.
- **Topic confound in Phase 3:** N03 and N05 differ in both SH and topic type (AGI vs. socioeconomic). Observed lift difference cannot be unambiguously attributed to SH.
- **Phase 3 n=2:** Below pre-registered minimum. H2 cannot be evaluated.

---

## Files

| File | Contents |
|------|----------|
| `paper6/phase1_results/phase1_retrograde.json` | Phase 1 retrograde SH + correlation data |
| `paper6/phase1_summary.md` | Phase 1 written summary |
| `paper6/phase2_results/phase2_summary.json` | Phase 2 full results + correlations |
| `paper6/phase3_results/phase3_summary.json` | Phase 3 exploratory results |
| `paper6/phase3_results/N03_v05/` | N03 P5v05 loop states + outcome |
| `paper6/phase3_results/N05_v05/` | N05 P5v05 loop states + outcome |
| `paper6/phase3_summary.md` | Phase 3 written summary |
| `paper6/compute_sh.py` | Core SH computation module |
| `paper6/run_phase2.py` | Phase 2 runner |
| `paper6/run_phase3_v05.py` | Phase 3 P5v05 runner |
| `DES_Paper6_DesignMemo.md` | Pre-registered design memo (v0.4) |

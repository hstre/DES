<!-- paper9_25/geometry_reanalysis -->
<!-- EXPLORATORY REANALYSIS — not pre-registered, not confirmatory -->

# Paper 9.25 — Geometry Reanalysis
**EXPLORATORY REANALYSIS — not pre-registered, not confirmatory.**  
**Sources: Paper 6 Phase 2 (n=13) + Paper 9 Phase 1 (n=4)**

## Purpose
The hypothesis that local_semantic_density and Semantic Headroom (SH) are near-orthogonal geometric properties of ClaimGraphs in semantic projection space originated from unexpected findings in Phase 1 of Paper 9. Phase 1 revealed a potential relationship between these properties that was not anticipated. This reanalysis aims to test the hypothesis by examining the correlation between SH and local_density across different domains, using data from Paper 6 Phase 2 and Paper 9 Phase 1.

## Data Table
| Domain | Source | SH | SH_class | local_density (r=0.15) | domain_type |
|--------|--------|-----|----------|------------------------|-------------|
| N09 | paper6 | 0.0316 | LOW | 1.0000 | narrow_empirical |
| M01 | paper9_phase1 | 0.0388 | LOW | 0.9722 | formal_mathematics |
| N07 | paper6 | 0.0392 | LOW | 1.0000 | narrow_empirical |
| N06 | paper6 | 0.0408 | LOW | 1.0000 | narrow_empirical |
| N10 | paper6 | 0.0417 | LOW | 1.0000 | broad_argumentative |
| N_new_1 | paper9_phase1 | 0.0453 | LOW | 0.9117 | narrow_empirical |
| N12 | paper6 | 0.0493 | LOW | 1.0000 | narrow_empirical |
| N08 | paper6 | 0.0580 | LOW | 1.0000 | narrow_empirical |
| N02 | paper6 | 0.0583 | LOW | 0.9167 | broad_argumentative |
| N11 | paper6 | 0.0716 | LOW | 1.0000 | broad_argumentative |
| N03 | paper9_phase1 | 0.0725 | LOW | 0.5909 | empirical_argumentative |
| N01 | paper6 | 0.0727 | LOW | 0.5455 | broad_argumentative |
| N13 | paper6 | 0.0733 | LOW | 0.8333 | formal_or_philosophical |
| N_new_2 | paper9_phase1 | 0.0751 | LOW | 0.2500 | broad_normative |
| N04 | paper6 | 0.0848 | LOW | 0.5455 | other |
| N05 | paper6 | 0.0941 | HIGH | 0.4167 | broad_argumentative |
| N03 | paper6 | 0.1065 | HIGH | 0.4545 | other |

## Correlation Results
| Statistic | Value | p-value | Interpretation |
|-----------|-------|---------|----------------|
| Pearson r (combined) | -0.8018 | 0.0001 | Strong negative correlation, indicating a proxy relationship |
| Spearman ρ (combined) | -0.8145 | 0.0001 | Strong negative correlation, confirming proxy relationship |
| Pearson r (P6 only) | -0.8661 | 0.0001 | Strong negative correlation within Paper 6 data |
| Pearson r (P9 only) | -0.929 | 0.071 | Strong negative correlation within Paper 9 data, though not statistically significant at p < 0.05 |

## 2×2 Quadrant Analysis
- High SH + High density: []
- High SH + Low density: ['N03', 'N05']
- Low SH + High density: ['N02', 'N06', 'N07', 'N08', 'N09', 'N10', 'N11', 'N12', 'M01']
- Low SH + Low density: ['N01', 'N04', 'N13', 'N03', 'N_new_1', 'N_new_2']

The 2×2 structure does not have cells in all four quadrants, indicating a lack of diversity in the combinations of SH and density.

## Prediction Table Outcomes
| Domain | Expected SH | Actual SH | Expected density | Actual density | Match? |
|--------|-------------|-----------|-----------------|----------------|--------|
| M01 | High | Low | High | High | No |
| N03 | High | High | Medium | Low | No |
| N_new_1 | Low | Low | High | High | Yes |
| N_new_2 | High | Low | Low | Low | No |

## Verdict: PROXY_RELATIONSHIP
The correlation coefficient |r| = -0.8018 indicates a strong negative correlation between SH and local_density, suggesting that these properties are not orthogonal but rather exhibit a proxy relationship. This means that SH and local_density are largely redundant in characterizing ClaimGraphs.

## Implication for Paper 9.25 Design
Since the analysis reveals a proxy relationship, the two-axis characterization of ClaimGraphs using SH and local_density is not meaningful. The hypothesis for Paper 9.25 is not supported, and the design should be reconsidered to avoid redundant metrics.

## Negative Findings
- Expected M01 prediction (high SH + high density): No match
- Expected N03 prediction (high SH + medium density): No match
- Domains violating expected 2×2 structure: ['M01', 'N03', 'N_new_2']
- Cross-source consistency (P6 vs P9 correlation direction): Same
- Limitations: Reanalysis from loop_0 only, single-point density measurement, spl_mode

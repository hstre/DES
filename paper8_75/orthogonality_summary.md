<!-- paper8_75/orthogonality_summary -->
<!-- Paper 8.75 — Orthogonality Check -->

---

# Paper 8.75 — Orthogonality Check
**Density method: spl_wrapper (primary)**

## Purpose
This orthogonality check is necessary to evaluate the independence of local semantic density and activation frame complexity, as identified in Paper 8.5. The confound addressed was the potential interaction between these two variables, which could affect the validity of experimental results by introducing unintended dependencies.

## Definitions
- **Local Semantic Density**: The concentration of semantic information within a given context or frame, measured by the spl_wrapper method.
- **Activation Frame Complexity**: The level of complexity within the activation frame, determined by the framing condition (low or high).

## Per-Condition Results
| Condition                | mean_density | mean_complexity | n_runs |
|--------------------------|--------------|-----------------|--------|
| low_density_low_framing  | 0.8333       | 0.7500          | 3      |
| low_density_high_framing | 0.6806       | 1.0000          | 3      |
| high_density_low_framing | 0.7917       | 0.7500          | 3      |
| high_density_high_framing| 0.9167       | 1.0000          | 3      |

## Correlation Results
| Statistic   | Value  | p-value | Interpretation                           |
|-------------|--------|---------|------------------------------------------|
| Pearson r   | -0.0279| 0.9313  | No significant linear correlation        |
| Spearman ρ  | 0.0000 | 1.0000  | No significant rank correlation          |

## Within-Domain Density Shifts (Primary Check)
| Domain | Shift Value | Threshold | Interpretation                      |
|--------|-------------|-----------|-------------------------------------|
| M01    | 0.1528      | < 0.10    | Not empirically orthogonal          |
| N03    | 0.1250      | < 0.10    | Not empirically orthogonal          |

The shifts in both M01 and N03 domains exceed the threshold, indicating that activation context affects measured density.

## Within-Complexity Domain Difference (Secondary Check)
| Framing | Density Difference (N03 - M01) |
|---------|--------------------------------|
| Low     | -0.0417                        |
| High    | 0.2361                         |

These differences suggest that domain complexity influences density, with high framing showing a more pronounced effect.

## Verdicts

### DESIGN_ORTHOGONAL: YES
By construction, the 2×2 matrix is balanced, ensuring design orthogonality.

### EMPIRICALLY_ORTHOGONAL: NO
The primary verdict from within-domain shifts indicates that activation context affects measured density, violating empirical orthogonality.

## Implication for Paper 9
EMPIRICALLY_ORTHOGONAL = NO: Activation context affects measured density. Density is endogenous to framing condition. Paper 9 must either: (a) treat density as endogenous and add framing_complexity as covariate, OR (b) measure density before operator selection (pre-activation density). Do NOT proceed to Paper 9 Design Memo without design revision.

## Negative Findings
- Expected domain separation in density: not observed
- Unexpected density pattern: none
- Limitations of single-agent P4 config measurement: potential bias due to lack of perturbation
- spl_wrapper availability: unavailable — fallback used; results may differ with SPL

---

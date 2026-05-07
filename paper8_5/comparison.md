<!-- paper8_5/comparison -->
<!-- EXPLORATORY — not pre-registered, not confirmatory -->

---

# Paper 8.5 — Comparison: Abstract Seed vs Structural Constraint

**H_meta: Structural constraint prompt prevents content-level drift and keeps DES on design-level claim generation.**

## Side-by-Side Comparison

| Metric | Arm A (abstract) | Arm B (constrained) |
|--------|-----------------|---------------------|
| Q1 answered | no | partial |
| Q2 answered | no | no |
| Q3 answered | no | no |
| Attractor type | content_level | design_level |
| Claim types | {'content_level': 10, 'measurable': 3, 'hypothesis': 1} | {'metric': 12} |
| loops_configured | 5 | 5 |
| loops_to_saturation | 5 | 1 |
| design_anchor_rate | 0.286 | 1.0 |
| Yield | medium | high |

## H_meta Verdict

**PARTIAL**

The verdict is partial because Arm B, while achieving a high design_anchor_rate of 1.0 and answering one of the three questions, did not fully address all the questions posed. The structural constraint effectively shifted the focus to design-level claims, but further refinement may be needed to achieve comprehensive question coverage.

## Implication for Paper 9

PARTIAL: Additional anchoring is needed to ensure that all questions are fully addressed. While the structural constraint shows promise in maintaining focus on design-level claims, further adjustments are necessary to enhance the completeness of the response.

## Negative Findings

- Unexpected result: The partial verdict was somewhat surprising given the high design_anchor_rate, indicating that structural constraints alone may not be sufficient for full question coverage.
- Constraint side effects: The focus on design-level claims may have limited the diversity of claim types, potentially affecting the richness of the generated content.
- Limitations: This single-run test cannot establish the long-term effectiveness of structural constraints across different contexts or claim types. Further iterations are needed to validate these findings.

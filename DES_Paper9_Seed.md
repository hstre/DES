# DES Paper 9 Seed

**Date:** 7. Mai 2026
**Status:** SEED — not pre-registered, subject to revision before Design Memo

## Working Hypothesis

```
operator_effectiveness = f(structural_operator, activation_frame, local_semantic_density)
```

Where local_semantic_density is defined as:

```
density(q, r) = count(claims with sqrt_JSD(pi(c), pi(q)) < r) / n_claims
```

## Planned Experiment

2×3 factorial design:

- **density:** low (formal/narrow domains) vs high (argumentative/broad)
- **framing:** persona / explicit operator / stripped context

## Scope Constraint

Paper 9 does NOT introduce a new epistemic object class.
It tests whether semantic density functions as a conditioning field
over existing operator classes.

## Open Questions for Desi

1. What is the most likely failure mode of this experimental design?
2. What does Desi not yet understand about its own density-dependent behavior?
3. Is there a simpler operationalization of the hypothesis that would be more falsifiable?

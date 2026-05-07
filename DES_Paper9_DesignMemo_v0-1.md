# DES Paper 9 Design Memo v0.1

**Date:** 7. Mai 2026
**Status:** PRE-REGISTERED — Phase 1 only. Phase 2 conditional on H1.

## Motivation

Paper 8.5 (H_meta PARTIAL) showed structural constraint prevents content-level drift but
does not achieve full question coverage. Paper 8.75 (EMPIRICALLY_ORTHOGONAL = NO) showed
that local_semantic_density is endogenous to operator framing condition: within-domain
shifts of 0.1528 (M01) and 0.1250 (N03) both exceed the 0.10 threshold.

Additionally, a cross-over interaction was detected: the domain-density ordering
(expected: N03 > M01) is reversed under counterexample_search and holds only under
recursive_modulation. This means density cannot be treated as a stable domain property.

## Phase 1 Goal

Test H1: Pre-activation density (measured before operator fires) is stable across
operator contexts (shift < 0.10 within each domain at r=0.15).

Test H2: The Paper 8.75 cross-over interaction is a post-activation artifact, not
present in pre-activation density.

## Phase 1 Design

**Paired design:** One loop_0 DES run per domain × seed (4 × 3 = 12 runs).
Both operator contexts applied to the SAME saved state — no additional DES runs.

**Pre-activation density:** density of neutral next_q (no operator context) against
loop_0 ClaimGraph. Identical for both framings by construction.

**Post-activation density:** density of operator-specific candidate_q against same
loop_0 ClaimGraph. Differs by operator.

**Delta:** post - pre per operator. Near zero → operator does not redirect questions
to different density regions.

## Domains

- M01: formal mathematics (expected low density)
- N03: empirical-argumentative AGI (expected high density)
- N_new_1: narrow empirical (aspirin/cardiovascular, expected low)
- N_new_2: broad normative (climate refugees, expected high)

## Radius sweep

Pre-registered: r ∈ {0.10, 0.15, 0.20}. Primary: r=0.15.
No radius selection after seeing results.

## Verdict criteria

H1_CONFIRMED:
  - pre_density std across seeds < 0.10 (all domains)
  - operator_shift < 0.10 (all domains)
  - mean_abs_delta < 0.05 (all operators, all domains)

H1_PARTIAL: stable pre_density AND no shift, but delta not near zero.
H1_NOT_CONFIRMED: pre_density unstable OR shift >= 0.10.

## Conditional on H1

H1_CONFIRMED → Phase 2: test conditioning effect (main Paper 9 hypothesis).
H1_NOT_CONFIRMED → Paper 9 ends at Phase 1. Report as measurement finding.
H1_PARTIAL → decision pending after examining which criteria fail.

## What is NOT pre-registered

Phase 2 design (conditional on H1). Will be specified after Phase 1 results.

## SPL validity

spl_native preferred. spl_fallback (keyword-JSD) documented if unavailable.
Results flagged per run with spl_mode field.

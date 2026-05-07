# DES Paper 9 Branch 1 Design Memo v0.1

**Date:** 7. Mai 2026
**Status:** PRE-REGISTERED
**Branch:** paper9-branch1/parallel-operators

## Motivation

Paper 9 Phase 1 found H1_NOT_CONFIRMED: pre-activation density is not stable
across operator contexts. Paper 9.25 found SH and local_density are a proxy
pair (r=-0.80), not orthogonal axes. These results close the original Paper 9
hypothesis path.

Branch 1 pivots to a structural question: what happens when multiple operators
fire simultaneously from the same ClaimGraph state? Two architectures are
compared:

- **Architecture A (Merged Branch)**: admitted candidates → structured
  multi-seed prompt → single DES run. All operators contribute to one coherent
  inquiry path.
- **Architecture B (Preserved Branches)**: each admitted candidate → independent
  DES branch from parent state. Branches develop in isolation.

## Operators

PARALLEL_OPERATORS = [
  "recursive_modulation",
  "adaptive_variation_selection",
  "boundary_condition_analysis"
]

No persona framing. Operators fire in parallel from identical ClaimGraph state.
Candidates admitted via Alexandria-lite gate (validate_candidate).

## Hypotheses

- **H1**: EME(arch_a) > EME(arm_b_baseline) × 1.2
  arm_b_baseline EME = 2.8195 (Paper 8, combined M01+N03, seeds 101/202/303)
  Threshold: 2.8195 × 1.2 = 3.3834
- **H2**: EME(arch_b) > EME(arch_a)
  Preserved branches accumulate more diverse sealed claims than merged branch.
- **H3**: EME/token(parallel) > EME/token(single arm_b)
  Parallel operator expansion is more token-efficient per unit of epistemic diversity.

## Domains

- M01: formal mathematics — T(n) recursive map
- N03: empirical-argumentative — AGI within 20 years

Seeds: 101, 202, 303 (same as Papers 8 and 9).

## Architecture A: Merged Branch

When `parallel_fire()` returns ≥2 admitted candidates:
1. Format as structured multi-seed string:
   "Multi-perspective inquiry (parallel operator expansion):\n[1] q1\n[2] q2..."
2. Pass as single `research_question` to `run_des`.
3. `arch_a_fallback=True` if only 1 admitted candidate (use that question as-is)
   or if DES produces incoherent state (run_des error or <3 total claims).

EME computed from main run final_claims only.

## Architecture B: Preserved Branches

For each admitted candidate (up to MAX_BRANCHES=3):
1. Write parent_state to des_state.json (prevents sequential inheritance).
2. Call run_des independently with that candidate as research_question.
3. Save branch results to separate directory.

MAX_PARALLEL_EVENTS = 2 per top-level loop.

EME computed from main run + all branch final_claims combined.

## Run Design

- 2 domains × 3 seeds × 2 architectures = 12 main runs + Architecture B branches
- Operator trigger: early_saturation_detected (same as Paper 8 Arm B)
- MAX_LOOPS = 5 (reduced from Paper 8's 50 for controlled comparison)
- Anti-delphi: True
- Primary metric: EME at r=0.15

## Verdict criteria

H1: CONFIRMED if EME(arch_a) > 3.3834, else REJECTED
H2: CONFIRMED if EME(arch_b) > EME(arch_a), else REJECTED
H3: CONFIRMED if (EME(arch_b)/tokens_b) > (EME(arm_b)/tokens_arm_b), else REJECTED

Token count: approximate from loop count × MAX_ITER_PER_RUN × mean_tokens_per_iter.
For relative comparison only — no absolute token budget.

## What is NOT pre-registered

- Sub-architecture variations (e.g., candidate ranking before merge)
- Domain expansion beyond M01/N03
- Per-operator EME attribution

## SPL validity

spl_native preferred. spl_fallback documented if unavailable.
Results flagged per run with spl_mode field.
EME requires spl_native; if unavailable, report EME=None with reason.

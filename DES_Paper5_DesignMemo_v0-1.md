# DES Paper 5 — Design Memo v0.2
## Structured Epistemic Perturbation

**Date:** 2026-05-05  
**Status:** Pre-registered (commit before first run)  
**Branch:** `paper5/perturbation`

---

## Research Question

Does structured epistemic perturbation — injecting epistemically grounded
alternative questions at failure-onset — extend autonomous DES loop depth
beyond Paper 4 baselines, and do specific perturbation types produce
reliably higher claim novelty?

---

## Hypotheses

**H1 (Perturbation Lifts Loop Depth):** Perturbation extends average loop
depth by ≥2 loops vs Paper 4 on ≥3/5 domains.

**H2 (Type Specificity):** At least one perturbation type produces
measurably higher novelty lift (≥1 novel claim/perturbed loop) than the
unperturbed baseline across ≥3 domains.

**H0 (No Effect):** Perturbation does not extend loop depth or produce
novelty lift. DES degenerates on same schedule as Paper 4.

---

## Design

### Loop Architecture

Same as Paper 4: one complete DES run per loop, module import,
file-based handoff. des.py is not modified.

### Perturbation Trigger

Epistemic state based — never loop count:

```
semantic_duplication_rate > 0.40  OR
novel_claims == 0 for last 3 loops  OR
entropy increase > 0.15 from previous loop
```

### Perturbation Types (rotating, deterministic)

| # | Type | Target |
|---|---|---|
| 0 | scope_shift | Boundary condition not in graph |
| 1 | counterfactual | Missing variable explaining dominant claim |
| 2 | category_flip | Model assumption behind tension |
| 3 | time_shift | Temporal validity of supported claim |
| 4 | stakeholder_flip | Different stakeholder perspective |

Order rotates: all 5 appear before any repeats.

### Alexandria-lite Validation Gate

Four rules (minimal — no full Alexandria):
1. No circular: token_overlap(new_q, prior_q) < 0.70
2. Graph-term anchor: new_q contains ≥1 term from claim graph
3. No sealed reopening: overlap with sealed claim text < 0.60
4. All rejections logged with reason

### New Failure Condition

`PERTURBATION_DRIFT`: perturbation admission rate < 0.40 for 5
consecutive perturbed loops.

---

## Metrics (per loop, additional vs Paper 4)

| Metric | Definition |
|---|---|
| `semantic_duplication_rate` | redundant_claims / total_claims |
| `perturbed` | bool — was perturbation applied this loop |
| `perturbation_type` | which type if perturbed |
| `admitted` | bool — did perturbation pass validation |

---

## Output

```
paper5/batch_results_paper5/
  R01/
    loop_NNN_state.json
    metrics.json
    perturbation_log.json
    outcome.json
  R02/ ... R05/
summary.md
```

---

## Summary Comparison (vs Paper 4)

- Loops before failure per domain
- Perturbations triggered / admitted / rejected
- Novel claims: perturbed vs unperturbed loops
- Perturbation Novelty Lift per type
- Most effective perturbation type
- Average loop depth: Paper 5 vs Paper 4

---

## Constraints

- Do not implement full Alexandria
- Do not refactor DES internals
- Do not introduce new models (DS4 + GPT4o stack only)
- Perturbation triggered by epistemic state only, never loop count
- All 5 types appear before any repeats

---

## Paper 4 Baseline (for comparison)

| Domain | Outcome | Loops | Final Entropy |
|---|---|---|---|
| R01 Mindestlohn | SEMANTIC_DUPLICATION | 2 | 0.82 |
| R02 Remote Work | SEMANTIC_DUPLICATION | 3 | 1.07 |
| R03 Immigration | SEMANTIC_DUPLICATION | 4 | 0.93 |
| R04 GDP | LOOP_COMPLETE | 3 | 0.50 |
| R05 Intervallfasten | SEMANTIC_DUPLICATION | 4 | 0.92 |

Average loop depth before failure: 3.2

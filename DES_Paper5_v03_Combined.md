# DES Paper 5 v0.3 — Design Memo
## Preventive Method Perturbation and Epistemic Rollback: Breaking Semantic Attractors Before and After Capture

**Date:** 2026-05-05  
**Status:** Pre-registered (commit before first run)  
**Branch:** `paper5/method-perturbation`

---

## Version History

| Version | Change |
|---|---|
| v0.1 | Content-level perturbation, reactive trigger |
| v0.2 | Rotating schedule, Alexandria-lite label |
| v0.3 | Post-null: method-level perturbation, preventive trigger |

---

## Why v0.3

v0.2 did not confirm H1. Root cause: SEMANTIC_DUPLICATION fired before
perturbation could activate. The trigger was reactive — it waited until
semantic redundancy was already measurable. By then the attractor had
already captured the loop.

> "Perturbation must occur before semantic duplication becomes measurable.
> Once content redundancy crosses the failure threshold, the attractor
> has already captured the loop."

R01's counterfactual success (+5 loops) worked because it accidentally
functioned as a METHOD shift. v0.3 makes this explicit and preventive.

---

## Core Distinction

**Content Layer (v0.2)** — what: scope_shift, stakeholder_flip, time_shift.
Still asks about the same things. Does not escape the attractor.

**Method Layer (v0.3)** — how: measurement_shift, model_assumption_shift,
unit_of_analysis_shift, evidence_standard_shift, causal_mechanism_shift,
counterfactual_baseline_shift, failure_mode_shift.
Changes the epistemic operation. Escapes the attractor.

> Semantic attractors are not broken by nearby content shifts.
> They are broken by changing the epistemic operation applied to the same content.

---

## Pre-Registered Hypotheses

**H1:** Method perturbation extends average loop depth > 3.2 (P4 baseline).
At least 3/5 domains exceed their Paper 4 loop depth.

**H0:** No effect. Same loop depth as Paper 4.

**H2:** Perturbation causes drift. Alexandria-lite rejects > 40% of
perturbation questions (admission rate < 0.60) across 5 consecutive
perturbed loops. PERTURBATION_DRIFT fires at admission_rate < 0.60.

---

## New Operators and Metrics

### method_trace
Per-loop inferred method type from keyword heuristic.
Known limitation: domain-frequent terms may misfire.

### T10: EPISTEMIC_ROLLBACK_AND_RESEED
Triggered by SEMANTIC_DUPLICATION, METHOD_COLLAPSE, or novelty_zero_x3.
Branches from a prior healthy state — does NOT delete the failed path.
Failed path preserved and marked SATURATED. Maximum 2 activations per domain.

### M9: Method Diversity Score
unique_method_types / total_loops. Expected > 0.5.

### M10: Preventive Trigger Rate
method_repeat_triggers / total_triggers. Expected > 0.6.

### New Failure: METHOD_COLLAPSE
< 30% unique method types over last 5 loops.

---

## Paper 4 Baseline (comparison)

| Domain | P4 Loops | P5v02 Loops |
|---|---|---|
| R01 Mindestlohn | 2 | 7 |
| R02 Remote Work | 3 | 2 |
| R03 Immigration | 4 | 2 |
| R04 GDP | 3 | 1 |
| R05 Intervallfasten | 4 | 4 |
| **Average** | **3.2** | **3.2** |

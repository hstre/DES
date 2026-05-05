# Paper 5 v0.4 — Design Memo

# From Method Repeat to Frame Fixation:
# Why Preventive Perturbation Requires Earlier Structural Signals

**Date:** 2026-05-05  
**Status:** Pre-registered (commit before first run)  
**Branch:** `paper5/frame-fixation-v04a`

---

## Version History

| Version | Change | Result |
|---|---|---|
| v0.1 | Content-perturbation, reactive trigger | H1 not confirmed |
| v0.2 | Rotating schedule, Alexandria-lite | H1 not confirmed |
| v0.3 | Method-perturbation, preventive trigger | PTR=0%, H1 not confirmed |
| v0.4a | Bug fix + frame/metric/shape first, method secondary | This document |

---

## Why v0.4

### Bug in v0.3: preventive trigger never fired (PTR=0%)

The `should_perturb()` call passed `loop_metrics[:-1]` instead of
`loop_metrics` including the current loop:

```python
# v0.3 (wrong):
do_perturb, trigger = should_perturb(loop_metrics[:-1], metrics)

# The method_repeat check inside should_perturb:
last2 = [m.get("method_type") for m in loop_metrics[-2:]]
# This compared old loops against each other, not current vs previous.
# Current method_type was in `metrics`, not in loop_metrics at call time.
```

Fix: compare current method explicitly against previous loop.

### Conceptual finding from v0.3

R05 showed attractor capture despite method changes:

- loop 1: temporal_validity
- loop 3: causal_mechanism
- loop 4: scope_condition

Three different method types. Still SEMANTIC_DUPLICATION.

**Conclusion:** method_repeat is too narrow as an early warning signal.
Semantic attractors are downstream of frame/metric fixation, not
simple method repetition.

The attractor forms at the frame level — the implicit structure of
how questions are posed — before it becomes visible as method
repetition or content redundancy.

---

## New Hypothesis

> Semantic attractors are often downstream of metric/frame fixation
> rather than method repetition. Preventive perturbation requires
> earlier structural signals that detect fixation before method
> repetition or content redundancy become measurable.

---

## Pre-Registered Hypotheses (v0.4)

### H1

Frame/metric fixation triggers extend average loop depth > 3.2 (P4).
At least 3/5 domains exceed P4 loop depth.
Preventive Trigger Rate > 0% in at least 3/5 domains.

### H0

No effect. Same depth as P4/P5v03.

### H2

Perturbation drift (admission rate < 0.60 across 5 consecutive events).

### H3 (new, specific to v0.4)

PTR > 0% in at least 3/5 domains — the preventive trigger actually fires.
If PTR = 0% again: the trigger class is still wrong, not just the implementation.

---

## Bug Fix: should_perturb() call

```python
# v0.4 (correct):
# After computing current loop metrics and BEFORE appending to loop_metrics:

def should_perturb_v04(loop_metrics: list, current: dict) -> tuple[bool, str]:
    """
    v0.4: current metrics passed as separate argument.
    Explicit comparison of current vs previous.
    loop_metrics = completed prior loops only (not including current).
    """
    # PRIMARY: frame fixation (earliest signal -- fires before method repeat)
    frame_fix = check_frame_fixation(loop_metrics, current)
    if frame_fix:
        return True, frame_fix

    # PRIMARY: metric fixation
    metric_fix = check_metric_fixation(loop_metrics, current)
    if metric_fix:
        return True, metric_fix

    # PRIMARY: question shape fixation (diagnostic + trigger)
    shape_fix = check_question_shape_fixation(loop_metrics, current)
    if shape_fix:
        return True, shape_fix

    # SECONDARY: method repetition (later signal, kept as backup)
    if loop_metrics:
        previous_method = loop_metrics[-1].get("method_type")
        current_method = current.get("method_type")
        if previous_method and current_method and previous_method == current_method:
            return True, f"method_repeat:{current_method}"

    # FALLBACK: content redundancy (reactive, last resort)
    if current.get("semantic_duplication_rate", 0) > 0.40:
        return True, "content_redundancy>0.40"
    last3 = loop_metrics[-3:] if len(loop_metrics) >= 3 else []
    if len(last3) == 3 and all(m.get("novel_claims", 0) == 0 for m in last3):
        return True, "novelty_zero_x3"

    return False, ""
```

---

## New Trigger Classes

### Frame Fixation

A frame is the implicit epistemic structure of how a question is posed:

- Does X cause Y? (causal frame)
- Is X effective? (effectiveness frame)
- Under what conditions does X hold? (scope frame)
- How should X be measured? (measurement frame)
- What mechanism explains X? (mechanism frame)

Frame fixation occurs when consecutive questions share the same implicit
frame despite different method labels.

```python
FRAME_TYPES = [
    "causal",        # does X cause Y?
    "effectiveness", # is X effective / does X work?
    "scope",         # under what conditions?
    "measurement",   # how is X measured / defined?
    "mechanism",     # through what process?
    "comparison",    # is X better than Y?
    "normative",     # should X happen?
]

def infer_frame_type(question: str) -> str:
    """
    Priority order: measurement > mechanism > scope > causal > comparison > normative > effectiveness
    Reason: "increase/reduce/effect" appears in almost every economics/health question.
    Checking effectiveness last prevents artificial frame fixation from common vocabulary.
    """
    q = question.lower()
    if any(w in q for w in ["measure", "define", "operationalize", "proxy", "indicator",
                             "accurately", "capture", "validity"]):
        return "measurement"
    if any(w in q for w in ["mechanism", "process", "how does", "pathway", "via",
                             "through what", "by what"]):
        return "mechanism"
    if any(w in q for w in ["condition", "when", "where", "under", "context",
                             "only if", "unless", "scope"]):
        return "scope"
    if any(w in q for w in ["cause", "lead to", "result in", "drive", "determine"]):
        return "causal"
    if any(w in q for w in ["compare", "better", "worse", "more than", "less than",
                             "relative to", "versus"]):
        return "comparison"
    if any(w in q for w in ["should", "ought", "policy", "recommend", "justified",
                             "ethical", "normative"]):
        return "normative"
    return "effectiveness"
```

### Metric Fixation

Metric fixation occurs when consecutive questions implicitly use the
same dependent variable or outcome metric.

### Question Shape Repeat

```python
QUESTION_SHAPES = [
    "does_x_cause_y",
    "is_x_effective",
    "what_evidence",
    "under_what_conditions",
    "how_does_x_work",
    "what_is_the_effect",
]
```

---

## Per-Loop State (v0.4 extended)

```python
metrics = {
    "loop": loop_number,
    "question": current_question,
    "method_type": infer_method_type(question),
    "frame_type": infer_frame_type(question),         # NEW
    "question_shape": infer_question_shape(question),  # NEW
    "outcome_metric": extract_outcome_metric(question, claims), # NEW
    "entropy": ...,
    "novel_claims": ...,
    "semantic_duplication_rate": ...,
    "question_utility": ...,
}
```

---

## New Metrics

### M11: Frame Diversity Score

```
unique_frames / total_loops
```

Expected > 0.5. Failure if < 0.3 for 5 loops (FRAME_COLLAPSE).

### M12: Preventive Trigger Rate (v0.4 corrected)

```
(frame_repeat + metric_repeat + shape_repeat + method_repeat) / total_triggers
```

Must be > 0% to validate that preventive triggers are firing. This is H3's measurement.

---

## Failure Conditions (added to v0.3 list)

```python
# FRAME_COLLAPSE: no frame diversity despite perturbation
frame_trace = [m.get("frame_type") for m in loop_metrics[-5:]]
if len(frame_trace) == 5 and len(set(frame_trace)) / 5 < 0.30:
    return "FRAME_COLLAPSE"
```

---

## Implementation Constraints

- Branch: `paper5/frame-fixation-v04a`
- Memo committed before first run
- DES internals not refactored
- Alexandria-lite gate only
- No new models
- T10 rollback unchanged from v0.3

**Bug fix is mandatory:**

```python
# WRONG (v0.3):
do_perturb, trigger = should_perturb(loop_metrics[:-1], metrics)

# CORRECT (v0.4):
do_perturb, trigger = should_perturb_v04(loop_metrics, current_metrics)
# where loop_metrics does NOT include current loop yet
```

---

## Summary must report

Three-way comparison: P4 / P5v03 / P5v04
Plus:

- PTR breakdown: frame_repeat% / metric_repeat% / shape_repeat% / method_repeat% / fallback%
- Frame Diversity Score per domain
- Which trigger type fired most?
- Did H3 confirm (PTR > 0%)?

---

## Target Claim

> Semantic attractors in autonomous epistemic loops are not primarily
> caused by method repetition. They are caused by frame and metric
> fixation — the implicit structure of how questions are posed and
> what outcomes are measured. Preventive perturbation that detects
> frame fixation before method repetition becomes measurable can
> extend loop depth beyond reactive approaches.

---

## Acceptance Criteria

- [ ] Branch `paper5/frame-fixation-v04a` created, memo committed first
- [ ] Bug fix confirmed: current method compared explicitly against previous
- [ ] `frame_type`, `question_shape`, `outcome_metric` logged per loop
- [ ] Frame fixation trigger fires when consecutive frames match
- [ ] PTR breakdown reported (preventive vs fallback)
- [ ] H3 verdict reported: did PTR > 0%?
- [ ] Three-way comparison P4/P5v03/P5v04 in summary.md
- [ ] T10 unchanged from v0.3
- [ ] No DES internals refactored, no new models

## Paper 4 Baseline (for comparison)

| Domain | P4 Loops | P5v02 Loops | P5v03 Loops |
|---|---|---|---|
| R01 Mindestlohn | 2 | 7 | 1 |
| R02 Remote Work | 3 | 2 | 5 |
| R03 Immigration | 4 | 2 | 2 |
| R04 GDP | 3 | 1 | 1 |
| R05 Intervallfasten | 4 | 4 | 4 |
| **Average** | **3.2** | **3.2** | **2.6** |

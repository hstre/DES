# Paper 5 v0.5 — Design Memo + Code Task

# From Structural Triggers to Semantic Trajectory Control:
# Geometric Attractor Detection via the Alexandria Semantic Projection Layer

**Date:** 2026-05-05  
**Status:** post-v0.4a revision — claim-level attractor detection  
**Key correction:** attractor forms within DES runs, not between runs  

---

## Version History

| Version | Change | Result |
|---|---|---|
| v0.1–v0.2 | Content-perturbation, reactive | H1 not confirmed |
| v0.3 | Method-perturbation, preventive | PTR=0%, H1 not confirmed |
| v0.4a | Frame/metric/shape fixation triggers, bug fix | Awaiting results |
| v0.5 | SPL geometric attractor detection | This document |

---

## Theoretical Foundation

The Alexandria Semantic Projection Layer (WP2, Rentschler 2026) maps
natural language into a probability simplex Π over relational triples.
The space Π carries the metric (Π, √JSD) — a true metric space (WP2 §3.4.3).

### Critical finding from v0.4a

The attractor does not form between loops. It forms within the first DES run.
R05: dup=71% in loop 0 itself, before any inter-loop trigger architecture can help.
R03/R04: LOOP_COMPLETE after 1 loop — ClaimGraph exhausted before a second loop exists.

This means: detecting attractors from the last N loop-level questions
is too late. The attractor is already present in the claim-level projections
of the first DES run.

### v0.5 correction: claim-level attractor detection

Instead of centroid(last_N_questions), compute centroid(claims_in_current_run).
Project all claims in the ClaimGraph into Π after each DES run.
Compute K(G) over the claim projections.

High K(G) = high semantic tension between claims = attractor forming.
This is detectable AFTER loop 0, BEFORE loop 1 is started.

Two formal triggers (both claim-level):

1. K(G) > threshold — epistemic curvature of the ClaimGraph is high.
   Claims are distributed across conflicting regions of Π.
   This is the primary early signal (WP2 §3.6.3).
2. √JSD(π(next_question), centroid(claims)) < ε — the proposed next question
   is geometrically close to the claim centroid in Π.
   It would land in the same semantic space already covered.
   This detects the attractor before the next loop runs.

Both operate on claim projections, not loop-level question projections.
Both fire after loop N, before loop N+1 — the correct intervention point.

---

## Pre-Registered Hypotheses (v0.5)

### H1

SPL-based geometric attractor detection extends average loop depth > 3.2 (P4).
At least 3/5 domains exceed P4 loop depth.
PTR > 0% in at least 3/5 domains.

### H0

No effect. Same depth as P4/P5v04a.

### H2

Escape vector generation produces drift (admission < 0.60 across 5 events).

### H4 (new)

Claim-level SPL attractor detection fires in at least 3/5 domains (PTR > 0%).
SPL-triggered escape vectors produce higher novelty than measurement_shift alone.
Avg loop depth P5v05 > P4 baseline (3.2).

---

## SPL API (existing, do not modify)

```python
from nlp_backend import SPLNLPBackend
from spl import compute_jsd, compute_h_norm

spl = SPLNLPBackend(model_name="all-MiniLM-L6-v2", builder_origin="alpha")
projection = spl.project_text(question)
# projection.P_r → dict[str, float]
h = compute_h_norm(projection.P_r)
jsd = compute_jsd(proj_a.P_r, proj_b.P_r)
sqrt_jsd = jsd ** 0.5
```

---

## Thresholds (pre-registered)

- epsilon = 0.25 (proximity trigger: √JSD < ε)
- k_threshold = 0.55 (curvature trigger: K(G) > threshold)
- escape α=0.6, β=0.3, γ=0.1
- k=5 escape candidates per perturbation
- FALSE_ESCAPE: 3 SPL events with escape_distance>0.40 and novel=0

---

## Main Loop Integration (v0.5 key change)

v0.5: select_next_question() FIRST, then should_perturb_v05() with candidate.
v0.4a: check triggers, then select question.

```python
next_q_candidate = select_next_question(state, question_history)
if next_q_candidate == "LOOP_COMPLETE": break

do_perturb, trigger, ctx = should_perturb_v05(
    loop_metrics, metrics, question,
    state=state, next_question=next_q_candidate
)
```

---

## Baselines

| Domain | P4 | P5v02 | P5v03 | P5v04a |
|---|---|---|---|---|
| R01 | 2 | 7 | 1 | 3 |
| R02 | 3 | 2 | 5 | 2 |
| R03 | 4 | 2 | 2 | 1 |
| R04 | 3 | 1 | 1 | 1 |
| R05 | 4 | 4 | 4 | 1 |
| Avg | 3.2 | 3.2 | 2.6 | 1.6 |

---

## Acceptance Criteria

- [ ] Branch `paper5/spl-escape` created, memo committed first
- [ ] `spl.py` and `nlp_backend.py` created in DES root
- [ ] `paper5/spl_wrapper.py` created — wraps SPL API
- [ ] SPL initialized once lazily via get_spl()
- [ ] `claim_projections`, `claim_centroid`, `claim_curvature` stored per loop
- [ ] `loop0_projection` stored on loop 0 for drift calculation
- [ ] SPL trigger fires BEFORE heuristic triggers
- [ ] Escape candidates: 5 per SPL perturbation, scored by composite formula
- [ ] FALSE_ESCAPE detected and logged
- [ ] Five-way comparison P4/P5v02/P5v03/P5v04a/P5v05 in summary.md
- [ ] spl.py and nlp_backend.py NOT modified after creation

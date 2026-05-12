# DES Paper 4 — Design Memo v0.5
## Autonomous Epistemic Loop

**Date:** 2026-05-05  
**Status:** Pre-registered (commit before first run)

---

## Research Question

Can DES sustain autonomous multi-loop epistemic inquiry — generating and
pursuing its own research questions from a single human seed — without human
intervention, and without degenerating into entropy, redundancy, or circular
reasoning?

---

## Hypothesis

**H1 (Stable Autonomy):** DES can run ≥ 20 autonomous loops per domain,
maintaining entropy < 0.80, resolving > 50% of contradictions per loop, and
generating novel (non-redundant) hypotheses past loop 20.

**H0 (Degeneration):** DES degenerates within 20 loops: entropy collapses,
claim graph becomes redundant, or branch explosion occurs.

---

## Design

### Loop Architecture

A Paper 4 loop = **one complete DES run** per research question.

```
Loop N:
  1. Call des.py as subprocess with current question
  2. des.py runs to completion (full T1–T9 lifecycle)
  3. Load resulting des_state.json
  4. Save as loop_NNN_state.json
  5. Compute metrics from saved state
  6. Check failure conditions
  7. Derive next question from ClaimGraph in saved state
  8. Next loop starts with new question
```

DES internals are not modified. des.py is treated as a black-box subprocess.
State is the communication channel between loops.

### Question Selection (Step 7)

Priority order — always ClaimGraph-derived, never free generation:

1. **Open claims** (not sealed): ranked by `epistemic_priority`
2. **Weak evidence claims**: sealed but `len(evidence_refs) == 0`
3. **Literature-derived side claims**: `is_synthesis == True`
4. **Branch-root disputed claims**: `status == "disputed"` and T1 in history
5. **Synthesis reframing**: highest-confidence synthesis claim
6. **LOOP_COMPLETE**: nothing actionable left

`epistemic_priority(c)` = `branch_trigger_count + contradiction_count + evidence_gap`

### Metrics (per loop)

| Metric | Definition |
|---|---|
| `entropy` | (open + disputed + redundant) / total |
| `novel_claims` | Claims with < 30% token overlap to any prior-loop claim |
| `redundant_claims` | Claim pairs with > 70% token overlap |
| `lit_rate` | literature_derived / new_claims_this_loop |
| `question_utility` | weighted sum: contradictions×3, syntheses×2, counters×2, evidence×1, branches×1 |

### Failure Conditions (pre-registered, immutable)

| Code | Condition |
|---|---|
| `ENTROPY_COLLAPSE` | entropy > 0.80 for last 5 loops |
| `SEMANTIC_DUPLICATION` | redundant_claims / total_claims > 0.60 |
| `NOVELTY_COLLAPSE` | novel_claims == 0 for last 10 loops |
| `GRAPH_TOO_LARGE` | total_claims > 500 |
| `EXTERNAL_ANCHOR_CAPTURE` | lit_rate > 0.90 for last 10 loops |
| `BRANCH_EXPLOSION` | exponential branch growth over last 10 loops |

### Outcome Classification (pre-registered)

| Outcome | Criteria |
|---|---|
| `H1_STABLE` | MAX_LOOPS reached + entropy < 0.80 (last 10) + resolution > 50% (last 10) + novel claims after loop 20 |
| `H0_DEGENERATION` | MAX_LOOPS reached but H1 criteria not met |
| `LOOP_COMPLETE` | ClaimGraph exhausted — no actionable open claims |
| `ENTROPY_COLLAPSE` / etc. | Failure condition triggered |

---

## Research Domains

| ID | Seed Question |
|---|---|
| R01 | Does raising the minimum wage increase unemployment? |
| R02 | Is remote work more productive than office work? |
| R03 | Does immigration reduce wages for native workers? |
| R04 | Is GDP a valid proxy for human wellbeing? |
| R05 | Is intermittent fasting effective for long-term weight loss? |

---

## Output Structure

```
paper4/batch_results_paper4/
  R01/
    loop_000_state.json
    loop_001_state.json
    ...
    metrics.json
    outcome.json
  R02/ ... R05/
summary.md
```

---

## Constraints

- Do not modify T1-T9 transition table
- Do not manually intervene after loop 0
- Do not adjust thresholds based on early results
- Do not generate next questions freely (always ClaimGraph-derived)
- LOOP_COMPLETE is a valid outcome, not an error

---

## Models

- Builder: `deepseek-chat` (DeepSeek)
- Falsifier: `openai/gpt-4o` (OpenRouter)
- Anti-Delphi mode: enabled
- Max iterations per DES run: 40
- Max loops per domain: 50

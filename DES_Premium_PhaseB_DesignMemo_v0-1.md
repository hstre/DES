# DES Two-Tier Architecture (Phase A + Phase B Review) — Design Memo v0.1

**Date:** 2026-05-09
**Branch:** des-premium/phase-b-review
**Status:** PRE-REGISTERED
**Supersedes framing of:** DES_Premium_2x2_DesignMemo_v0-1.md

---

## Motivation

The 2×2 matrix pilot (des-premium/matrix-v2, May 2026) established that
reasoning-trained models (DeepSeek-R1) are the wrong tool for the DES Builder
role. R1's RL training produces canonical, convergent output; the SPL
duplication detector classifies its branch variations as redundant and triggers
premature termination. 5 of 6 DES-premium runs terminated with
`SEMANTIC_DUPLICATION` after only 1–6 loops.

Architectural lesson: **DES requires divergent output in the inner loop.
The correct role for premium reasoning models is review, not generation.**

This memo pre-registers the two-tier architecture that operationalises this
lesson.

---

## Architecture

### Phase A — divergent inner loop (existing, unchanged)

Builder: `deepseek/deepseek-chat` (V4 Flash via DeepSeek API).
Non-reasoning-RL; proven lexical diversity in prior Papers 4–8.

Falsifier: `openai/gpt-4o` via OpenRouter.
Held constant from the 2×2 matrix for comparability.

Termination: existing criteria unchanged — saturation, contradiction
resolution, semantic_duplication threshold, max_loops. No structural changes
to Phase A.

### Phase B — convergent review pass (new, single-shot)

**Trigger:** Phase A termination, regardless of cause. Phase B fires once per
run, after Phase A completes. It does not extend or continue the inner loop.

**Reviewer model:** `google/gemini-3.1-pro-preview` via OpenRouter.
Non-pure-reasoning-RL, large context (2M+), $2/$12 per 1M tokens.
Not the same model as Builder or Falsifier.

**Variants** (by Phase A termination type):

| Phase A termination       | Phase B variant     | Extra focus                           |
|---------------------------|---------------------|---------------------------------------|
| `LOOP_COMPLETE`           | `standard_review`   | Synthesis + meta-assessment           |
| `SEMANTIC_DUPLICATION`    | `premature_review`  | Gap identification (missed branches)  |
| `MAX_LOOPS_REACHED`       | `unsaturated_review`| Mark output preliminary; priority gaps|
| `CONTRADICTION_UNRESOLVED`| `contradiction_review` | Force synthesis across contradiction|

**System role (Phase B):**
> "You are an external epistemic reviewer. You did not produce the following
> claim graph; your task is to assess it as a coherent epistemic state and
> identify what synthesis, recalibration, or further work is needed. Do not
> extend the inner loop's reasoning; evaluate it."

**Input to Phase B (structured JSON):**
- Original seed question
- Full claim graph: ClaimNodes with id, subject/predicate/object text,
  status, confidence, parent links, T-transition history (sealed/branch_open)
- Phase A termination reason and loop count
- Detected contradictions and open branches
- SPL geometry metadata if available

**Output schema (Phase B):**
```json
{
  "synthesis_claim": "string — bridging claim that resolves or contextualises branches",
  "cluster_assessment": [
    {"cluster_id": "string", "coherence": "coherent|fragmented|contested", "rationale": "string"}
  ],
  "confidence_recalibration": {
    "claim_id": {"original": 0.0, "revised": 0.0, "rationale": "string"}
  },
  "gap_identification": [
    {"region": "description of semantic gap", "would_resolve": "what evidence would close it"}
  ],
  "meta_assessment": "settled|contested|incoherent|preliminary",
  "review_rationale": "string — free-text explanation of overall assessment"
}
```

**Judge model:** `anthropic/claude-opus-4.7` via OpenRouter.
Not the same model as Builder, Falsifier, or Reviewer.
Evaluates all 18 outputs (3 conditions × 6 domain/seed combinations) on the
rubric below. Judge model is fixed before any runs are inspected.

---

## Three Conditions (Pilot)

| Condition        | Architecture         | Builder                 | Reviewer                     |
|------------------|----------------------|-------------------------|------------------------------|
| DES_PHASE_A_ONLY | Phase A only         | deepseek-chat           | —                            |
| DES_PHASE_A_B    | Phase A + Phase B    | deepseek-chat           | google/gemini-3.1-pro-preview|
| COT_PREMIUM      | Single-shot CoT      | google/gemini-3.1-pro-preview | —                       |

COT_PREMIUM uses the Phase B reviewer model directly (single-shot) to control
for "is the premium model alone sufficient?".

**Pilot scope:** M01 × seeds [101, 202, 303] + N03 × seeds [101, 202, 303] =
6 domain/seed pairs × 3 conditions = 18 runs total.

---

## Pre-Registered Hypotheses

**H1 (Phase B value):**
Phase A + Phase B produces higher synthesis quality than Phase A alone,
especially when Phase A terminated prematurely (`SEMANTIC_DUPLICATION` or
`MAX_LOOPS_REACHED`). Confirmed if mean(synthesis_quality[DES_PHASE_A_B]) >
mean(synthesis_quality[DES_PHASE_A_ONLY]) with effect concentrated in
premature termination runs.

**H2 (Premium review beats premium CoT):**
Phase A (cheap inner) + Phase B (premium review) achieves equal or higher
synthesis quality than COT_PREMIUM (same premium model, single-shot), while
preserving more distinct branches in the underlying graph.
Confirmed if mean(synthesis_quality[DES_PHASE_A_B]) ≥
mean(synthesis_quality[COT_PREMIUM]) AND mean(branch_preservation[DES_PHASE_A_B])
> mean(branch_preservation[COT_PREMIUM]).

**H3 (Termination-type effect):**
Phase B's value-add (DES_PHASE_A_B − DES_PHASE_A_ONLY on synthesis_quality)
is largest for `SEMANTIC_DUPLICATION` and `MAX_LOOPS_REACHED` terminations,
smallest for clean `LOOP_COMPLETE` terminations.

**H4 (Architecture > model alone):**
Two-tier DES (cheap divergent builder + premium convergent reviewer) outperforms
single-shot premium CoT on synthesis_quality, confirming that the branching
structure generated by Phase A adds value beyond what the premium model
produces alone.

---

## Evaluation Metrics (Architecture-Agnostic, Judge-Scored)

All metrics evaluated by the judge model (`anthropic/claude-opus-4.7`) on the
**final output text** of each run, regardless of how that output was produced.
This ensures commensurability across DES and CoT.

| # | Metric               | Scale  | Description                                                                      |
|---|----------------------|--------|----------------------------------------------------------------------------------|
| 1 | synthesis_quality    | 1–5    | Does the output integrate competing considerations, or just list them?           |
| 2 | branch_preservation  | 1–5    | Does the output retain meaningful distinct positions, or collapse to one answer? |
| 3 | gap_acknowledgment   | 1–5    | Does the output explicitly identify what is unresolved or requires evidence?     |
| 4 | calibration          | 1–5    | Are confidence claims aligned with evidence strength shown?                      |
| 5 | false_proof_avoidance| binary | (M01 only) Does the output avoid claiming proof of an open conjecture?           |

For DES_PHASE_A_ONLY: judge evaluates the final claim set (summary text).
For DES_PHASE_A_B: judge evaluates the Phase B `synthesis_claim` +
`review_rationale` together.
For COT_PREMIUM: judge evaluates the CoT response text.

**Judge prompt** instructs the judge to:
1. Read the seed question and output text
2. Score each applicable metric with rationale
3. Return a JSON with scores and rationale strings

The judge prompt is the same across all conditions. It does not reveal which
condition produced the output.

---

## Data Hygiene Requirements

Each `outcome.json` and `metadata.json` must include:
- `run_timestamp` (ISO 8601 UTC)
- `code_hash` (`git rev-parse HEAD` at run time)
- `prompt_hash` (SHA256 of full constructed prompt, where applicable)
- `model_versions` (specific model IDs for all roles used)

Additional controls:
- Result directories cleared before each run. No skip-logic that returns
  cached files. Use `--resume` flag if resuming is ever needed.
- API `seed` parameter passed where supported (DeepSeek, OpenAI-compatible
  APIs). Documented as not-supported where not.
- `random.seed()` not relied upon for LLM determinism (has no effect on API).
- Prompt cache bypass: seed value included in every prompt as a final line
  `# run_seed: {seed_n}` so that API prompt caches do not return identical
  outputs for nominally-different seeds.
- Domain assertion: before recording an outcome, `domain_id` verified against
  the seed_question actually used. Fail loudly on mismatch.
- Phase A → Phase B handoff integrity: Phase B input includes SHA256 of the
  Phase A graph state. Phase B output records this hash.

---

## Output Directory Structure

```
batch_results_des_phase_a_b/
  {domain_id}_seed{seed_n}/
    outcome.json        — Phase A summary + Phase B synthesis_claim + meta_assessment
    phase_a_graph.json  — Full claim graph serialised from Phase A final state
    phase_b_review.json — Structured Phase B output (full JSON schema above)
    metadata.json       — Timestamps, hashes, model IDs, prompt hashes

batch_results_phase_a_only/
  {domain_id}_seed{seed_n}/
    outcome.json
    metadata.json

batch_results_cot_premium_pb/
  {domain_id}_seed{seed_n}/
    outcome.json
    metadata.json
```

Results from all three conditions are in separate directories. No cross-
directory dependencies at run time.

---

## Out of Scope

- Multi-LLM federation in Phase B (multiple reviewers): future work.
- Iterated Phase B (review of review): not in this task.
- Replacing T9 reframing with Phase B: T9 stays as inner-loop operation.
- Full re-run of the 2×2 matrix with corrected methodology: separate task.
- Production deployment: this is a 6-run pilot per condition.

---

## Result Interpretation

Whether H1–H4 are confirmed, falsified, or mixed is **not** a success
criterion. Honest reporting of the result — including null results — is
the success criterion. If H2 is falsified (Phase A+B does not exceed
premium CoT), this is an informative finding about the limits of the
two-tier architecture and will be reported as such.

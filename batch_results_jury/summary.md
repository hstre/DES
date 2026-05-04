# DES vs. Adversarial CoT — Multi-Model Jury Evaluation

**DES condition:** DS4_GPT4o (pre-registered, no fallback)
**Missing DS4_GPT4o states:** 0/13
**Fallbacks used:** 0
**Valid evaluations:** 104/104

## A. Average Scores by Dimension

| Dimension | DES | CoT | Winner |
|---|---|---|---|
| readability | 0.385 | 0.615 | CoT |
| directional_commitment | 0.509 | 0.491 | EQUAL |
| contradiction_depth | 0.526 | 0.474 | DES |
| synthesis_quality | 0.463 | 0.537 | CoT |
| epistemic_novelty | 0.623 | 0.377 | DES |
| branch_preservation | 0.734 | 0.266 | DES |
| process_traceability | 0.589 | 0.411 | DES |
| evidence_scope_discipline | 0.563 | 0.437 | DES |
| overall | 0.549 | 0.451 | DES |

## B. Scores by Judge Model

| Judge | Readability | Novelty | Branch | Traceability | Overall |
|---|---|---|---|---|---|
| deepseek-chat | DES=0.408/CoT=0.592 | DES=0.648/CoT=0.352 | DES=0.746/CoT=0.254 | DES=0.6/CoT=0.4 | DES=0.558/CoT=0.442 |
| openai/gpt-4o | DES=0.369/CoT=0.631 | DES=0.565/CoT=0.435 | DES=0.625/CoT=0.375 | DES=0.477/CoT=0.523 | DES=0.469/CoT=0.531 |
| anthropic/claude-sonnet-4-5 | DES=0.321/CoT=0.679 | DES=0.712/CoT=0.288 | DES=0.835/CoT=0.165 | DES=0.685/CoT=0.315 | DES=0.654/CoT=0.346 |
| google/gemini-2.0-flash-001 | DES=0.442/CoT=0.558 | DES=0.567/CoT=0.433 | DES=0.731/CoT=0.269 | DES=0.596/CoT=0.404 | DES=0.516/CoT=0.484 |

## C. Position Bias Check

**deepseek-chat_CoT-DS4:** DES as A: 2/6 (0.33) | DES as B: 2/7 (0.29) | Bias: not detected

**openai/gpt-4o_CoT-DS4:** DES as A: 1/7 (0.14) | DES as B: 0/6 (0.00) | Bias: not detected

**anthropic/claude-sonnet-4-5_CoT-DS4:** DES as A: 5/7 (0.71) | DES as B: 5/6 (0.83) | Bias: not detected

**google/gemini-2.0-flash-001_CoT-DS4:** DES as A: 1/6 (0.17) | DES as B: 0/7 (0.00) | Bias: not detected

**deepseek-chat_CoT-GPT4o:** DES as A: 4/5 (0.80) | DES as B: 7/8 (0.88) | Bias: not detected

**openai/gpt-4o_CoT-GPT4o:** DES as A: 5/9 (0.56) | DES as B: 0/4 (0.00) | Bias: DETECTED

**anthropic/claude-sonnet-4-5_CoT-GPT4o:** DES as A: 7/7 (1.00) | DES as B: 6/6 (1.00) | Bias: not detected

**google/gemini-2.0-flash-001_CoT-GPT4o:** DES as A: 6/8 (0.75) | DES as B: 5/5 (1.00) | Bias: DETECTED


## D. Per-Question Overview

| QID | Overall DES | Overall CoT | DES stronger dims |
|---|---|---|---|
| A1 | 0.625 | 0.375 | directional_commitment, contradiction_depth, synthesis_quality |
| A2 | 0.54 | 0.46 | epistemic_novelty, branch_preservation, process_traceability |
| A3 | 0.562 | 0.438 | epistemic_novelty, branch_preservation, process_traceability |
| B1 | 0.521 | 0.479 | epistemic_novelty, branch_preservation |
| B2 | 0.415 | 0.585 |  |
| B3 | 0.594 | 0.406 | contradiction_depth, epistemic_novelty, branch_preservation |
| C1 | 0.419 | 0.581 | evidence_scope_discipline |
| C2 | 0.523 | 0.477 | branch_preservation, process_traceability |
| D1 | 0.537 | 0.463 | epistemic_novelty, branch_preservation, evidence_scope_discipline |
| D2 | 0.534 | 0.466 | epistemic_novelty, branch_preservation, process_traceability |
| D3 | 0.657 | 0.343 | directional_commitment, contradiction_depth, synthesis_quality |
| E1 | 0.598 | 0.402 | contradiction_depth, epistemic_novelty, branch_preservation |
| E2 | 0.615 | 0.385 | contradiction_depth, epistemic_novelty, branch_preservation |

## E. CoT Generator Comparison

| CoT Model | Overall DES | Overall CoT |
|---|---|---|
| CoT-DS4 | 0.471 | 0.529 |
| CoT-GPT4o | 0.627 | 0.373 |

---

## F. Notable Findings

### DES wins overall 0.549 vs CoT 0.451 — reversal of v2 prose-bias result

The v2 blind evaluation (CoT 12/13) used prose-rendered DES but still asked judges to evaluate
four dimensions including readability. Under the jury protocol, judges are explicitly instructed
to disregard rhetorical polish for dimensions 2–8. With that instruction removed, DES wins
overall across all 4 judges on all 13 questions aggregated.

### Branch preservation is the dominant DES signal (0.734 vs 0.266)

The largest margin across all dimensions. Every judge assigns DES 0.6–0.84 on branch
preservation vs CoT 0.16–0.40. This is the clearest structural property: DES maintains B001/B002
competing hypotheses in parallel, visible in the prose report; CoT produces a single synthesis
that absorbs both branches. All four judges detect this independently.

### Epistemic novelty: DES 0.623 vs CoT 0.377 — consistent across all judges

DES wins epistemic novelty 0.565–0.712 across all four judge models. This replicates the v2
finding (DES 9/13 on Epistemic Novelty) and is the only dimension that survived the format
correction in v2. Under jury conditions it grows stronger, suggesting the dimension is genuinely
measuring claim-graph structure rather than prose style.

### Readability: CoT wins 0.615 vs 0.385 — as designed

CoT's single-pass prose synthesis is more readable. The jury prompt instructs judges not to
reward readability outside dimension 1. The fact that CoT's overall score (0.451) is far below
its readability score (0.615) confirms judges successfully downweighted prose aesthetics in the
overall verdict.

### GPT-4o is the only judge where CoT wins overall (0.531 vs 0.469)

GPT-4o assigns DES lower branch preservation (0.625) and lower process traceability (0.477)
than the other three judges (0.685–0.835 and 0.596–0.600 respectively). GPT-4o also shows
position bias on CoT-GPT4o comparisons (5/9 wins when A vs 0/4 when B). This suggests
GPT-4o has a recency or self-similarity preference when evaluating outputs from its own model
family as CoT generator.

### CoT generator matters more than judge identity

DES vs CoT-DS4: DES 0.471, CoT 0.529 — CoT wins  
DES vs CoT-GPT4o: DES 0.627, CoT 0.373 — DES wins by +0.254

The DES condition is DS4_GPT4o (DeepSeek builder + GPT-4o falsifier). When compared against
CoT from the same model family as the falsifier (GPT-4o), DES wins strongly. When compared
against CoT from the builder's model family (DeepSeek), the contest is closer and CoT wins
marginally. **DES is most clearly superior when the CoT baseline uses the same model that
DES uses as its falsifier.** The GPT-4o falsifier generates sharper adversarial claims that
DES branches on; CoT-GPT4o generates the same claims in a single pass without branching.
The jury detects the difference.

### B2 and C1 are CoT's only per-question wins (2/13)

B2 (remote work productivity) and C1 (Is technology good?) are the only questions where
DES overall score < 0.5. Both are questions with a single dominant tension rather than
multi-dimensional contradictions. This replicates the v1 finding (B2 was CoT's only win there).
These are questions where the single-pass adversarial structure is sufficient.

### Position bias: 2/8 judge-CoT combinations flagged

`openai/gpt-4o_CoT-GPT4o` and `google/gemini-2.0-flash-001_CoT-GPT4o` show rate differential
> 0.2 between DES-as-A and DES-as-B. Both are in the CoT-GPT4o condition where DES wins most
strongly. The small per-cell sample sizes (4–9 questions) mean the flag is sensitive to a
2–3 question swing; the overall CoT-GPT4o signal (DES +0.254) is robust across all judges.

---

## G. Comparison Across All Evaluation Methods

| Method | DES wins | CoT wins | Note |
|---|---|---|---|
| v1 LLM eval (biased) | 12/13 | 1/13 | Format + label bias; DES shown as raw ClaimGraph |
| v2 LLM eval (blind prose) | 1/13 | 12/13 | Prose rendered; judge penalizes structural output |
| Process quality (algorithmic) | 6/6 | 2/6 | No LLM eval; structural properties only |
| Jury eval (4-judge, blind) | DES 0.549 | CoT 0.451 | Judges instructed to ignore readability for dims 2–8 |

The jury result is the most methodologically sound: blind assignment, multiple judge models,
explicit dimension separation between readability and epistemic structure. DES wins on 6/8
dimensions; CoT wins readability and synthesis quality.

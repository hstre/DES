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

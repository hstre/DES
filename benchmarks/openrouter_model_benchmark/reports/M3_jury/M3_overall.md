# M3 Role-Prompt Matrix — Jury Evaluation Report

**Evaluations:** 96 valid (96 real + 4 dry-run excluded)  
**Models:** 4  **Roles:** 4  **Tasks:** 8  **Judges:** deepseek-chat, claude-sonnet-4-6

## Overall Model Ranking

Averaged across all roles, tasks, and judges (jury `overall` dimension).

| # | Model | Mean Score | Evaluations |
|---|---|---|---|
| 1 | deepseek-chat | **0.624** | 48 |
| 2 | claude-3-5-haiku | **0.547** | 48 |
| 3 | gpt-4o-mini | **0.463** | 48 |
| 4 | qwen-2.5-7b | **0.366** | 48 |

## Scores by Dimension

| Dimension | claude-3-5-haiku | gpt-4o-mini | deepseek-chat | qwen-2.5-7b |
|---|---|---|---|---|
| role_adherence | 0.523 | 0.489 | 0.594 | 0.394 |
| epistemic_quality | 0.547 | 0.464 | 0.63 | 0.359 |
| task_completion | 0.524 | 0.47 | 0.615 | 0.392 |
| assumption_handling | 0.541 | 0.466 | 0.594 | 0.399 |
| conclusion_clarity | 0.551 | 0.46 | 0.634 | 0.355 |
| overall | 0.547 | 0.463 | 0.624 | 0.366 |

## Scores by Role

### Builder (24 evaluations)

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.625 | 0.643 | 0.643 | 0.651 | 0.638 | 0.643 |
| claude-3-5-haiku | 0.475 | 0.483 | 0.447 | 0.537 | 0.492 | 0.493 |
| gpt-4o-mini | 0.452 | 0.469 | 0.447 | 0.44 | 0.45 | 0.45 |
| qwen-2.5-7b | 0.448 | 0.404 | 0.462 | 0.372 | 0.421 | 0.413 |

### Falsifier (24 evaluations)

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.608 | 0.667 | 0.632 | 0.608 | 0.679 | 0.654 |
| claude-3-5-haiku | 0.504 | 0.503 | 0.519 | 0.493 | 0.573 | 0.529 |
| gpt-4o-mini | 0.487 | 0.474 | 0.464 | 0.515 | 0.437 | 0.468 |
| qwen-2.5-7b | 0.4 | 0.357 | 0.385 | 0.383 | 0.311 | 0.349 |

### Resolver (24 evaluations)

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.579 | 0.623 | 0.623 | 0.583 | 0.623 | 0.617 |
| claude-3-5-haiku | 0.533 | 0.564 | 0.559 | 0.55 | 0.569 | 0.566 |
| gpt-4o-mini | 0.517 | 0.435 | 0.448 | 0.438 | 0.475 | 0.448 |
| qwen-2.5-7b | 0.371 | 0.378 | 0.371 | 0.429 | 0.333 | 0.37 |

### Explainer (24 evaluations)

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| claude-3-5-haiku | 0.579 | 0.637 | 0.569 | 0.583 | 0.569 | 0.6 |
| deepseek-chat | 0.562 | 0.588 | 0.562 | 0.533 | 0.598 | 0.582 |
| gpt-4o-mini | 0.5 | 0.477 | 0.519 | 0.471 | 0.477 | 0.486 |
| qwen-2.5-7b | 0.358 | 0.299 | 0.349 | 0.413 | 0.356 | 0.333 |

## Scores by Task

### M3_B1_builder_des_hypothesis  *(role: builder)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| claude-3-5-haiku | 0.575 | 0.622 | 0.567 | 0.732 | 0.558 | 0.63 |
| deepseek-chat | 0.567 | 0.595 | 0.578 | 0.618 | 0.633 | 0.598 |
| gpt-4o-mini | 0.43 | 0.405 | 0.412 | 0.372 | 0.433 | 0.402 |
| qwen-2.5-7b | 0.428 | 0.378 | 0.443 | 0.278 | 0.375 | 0.37 |

### M3_B2_builder_school_constraints  *(role: builder)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.683 | 0.692 | 0.708 | 0.683 | 0.642 | 0.688 |
| gpt-4o-mini | 0.475 | 0.533 | 0.483 | 0.508 | 0.467 | 0.498 |
| qwen-2.5-7b | 0.467 | 0.43 | 0.48 | 0.467 | 0.467 | 0.457 |
| claude-3-5-haiku | 0.375 | 0.345 | 0.328 | 0.342 | 0.425 | 0.357 |

### M3_F1_falsifier_t9_t8  *(role: falsifier)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.617 | 0.678 | 0.652 | 0.58 | 0.712 | 0.668 |
| claude-3-5-haiku | 0.433 | 0.458 | 0.5 | 0.45 | 0.533 | 0.495 |
| gpt-4o-mini | 0.508 | 0.47 | 0.458 | 0.533 | 0.433 | 0.467 |
| qwen-2.5-7b | 0.442 | 0.393 | 0.39 | 0.437 | 0.322 | 0.37 |

### M3_F2_falsifier_prompting_claim  *(role: falsifier)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.6 | 0.655 | 0.612 | 0.637 | 0.647 | 0.64 |
| claude-3-5-haiku | 0.575 | 0.547 | 0.538 | 0.537 | 0.612 | 0.563 |
| gpt-4o-mini | 0.467 | 0.478 | 0.47 | 0.497 | 0.442 | 0.468 |
| qwen-2.5-7b | 0.358 | 0.32 | 0.38 | 0.33 | 0.3 | 0.328 |

### M3_R1_resolver_model_roles  *(role: resolver)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| claude-3-5-haiku | 0.583 | 0.617 | 0.65 | 0.592 | 0.65 | 0.635 |
| deepseek-chat | 0.508 | 0.558 | 0.567 | 0.492 | 0.567 | 0.553 |
| gpt-4o-mini | 0.625 | 0.517 | 0.525 | 0.517 | 0.558 | 0.533 |
| qwen-2.5-7b | 0.283 | 0.308 | 0.258 | 0.4 | 0.225 | 0.278 |

### M3_R2_resolver_edge_vs_edge_star  *(role: resolver)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.65 | 0.688 | 0.678 | 0.675 | 0.678 | 0.68 |
| claude-3-5-haiku | 0.483 | 0.512 | 0.468 | 0.508 | 0.488 | 0.497 |
| qwen-2.5-7b | 0.458 | 0.447 | 0.483 | 0.458 | 0.442 | 0.462 |
| gpt-4o-mini | 0.408 | 0.353 | 0.37 | 0.358 | 0.392 | 0.362 |

### M3_E1_explainer_principal  *(role: explainer)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| claude-3-5-haiku | 0.558 | 0.617 | 0.542 | 0.617 | 0.583 | 0.59 |
| deepseek-chat | 0.558 | 0.583 | 0.58 | 0.525 | 0.608 | 0.585 |
| gpt-4o-mini | 0.5 | 0.492 | 0.525 | 0.458 | 0.467 | 0.483 |
| qwen-2.5-7b | 0.383 | 0.308 | 0.353 | 0.4 | 0.342 | 0.342 |

### M3_E2_explainer_des_roles  *(role: explainer)*

| Model | overall | role_adherence | epistemic_quality | task_completion | assumption_handling | conclusion_clarity |
|---|---|---|---|---|---|---|
| claude-3-5-haiku | 0.6 | 0.657 | 0.597 | 0.55 | 0.555 | 0.61 |
| deepseek-chat | 0.567 | 0.592 | 0.545 | 0.542 | 0.587 | 0.578 |
| gpt-4o-mini | 0.5 | 0.462 | 0.513 | 0.483 | 0.488 | 0.488 |
| qwen-2.5-7b | 0.333 | 0.29 | 0.345 | 0.425 | 0.37 | 0.323 |

## Judge Agreement

Winner agreement rate between deepseek-chat and claude-sonnet-4-6 on matching model pairs.

| Metric | Value |
|---|---|
| Comparable pairs | 48 |
| Agree | 39 |
| Disagree | 9 |
| Agreement rate | **81.2%** |

## Methodology

- Pairwise blind scoring: each task evaluated under its **target role** only.
- Each model pair scored by 2 judges (deepseek-chat, claude-sonnet-4-6) with randomised A/B assignment per judge.
- 6 dimensions evaluated; scores constrained to sum to 1.0 per pair.
- Matrix: 8 tasks × 6 model pairs × 2 judges = **96 jury calls**.
- Dry-run entries (4) excluded from all aggregations.

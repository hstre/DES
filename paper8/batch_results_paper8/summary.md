# Paper 8 — Phase 2: Three-Arm Experiment

**Arms:** A (Paper 7 persona, reference) | B (explicit operators, full framing) | C (algorithmic context, stripped prompt)
**Domains:** M01, N03 | **Seeds:** [101, 202, 303] | **Max loops:** 50

---

## Arm A Reference (Paper 7, not rerun)

| Domain | Best persona | Seed 101 | Seed 202 | Seed 303 | Mean loops | Std |
|--------|-------------|----------|----------|----------|------------|-----|
| M01 | kant | 5 | 7 | 6 | 6.00 | 0.8165 |
| N03 | mozart | 11 | 9 | 6 | 8.67 | 2.0548 |

---

## Arm B — Explicit Operators (Full Framing)

| Domain | Seed | Loops | P4 | depth_lift | Outcome | Op admitted |
|--------|------|-------|----|------------|---------|-------------|
| M01 | 101 | 5 | 1 | 4 | SEMANTIC_DUPLICATION | 1/1 |
| M01 | 202 | 2 | 6 | -4 | SEMANTIC_DUPLICATION | 1/1 |
| M01 | 303 | 2 | 4 | -2 | LOOP_COMPLETE | 1/2 |
| N03 | 101 | 7 | 4 | 3 | SEMANTIC_DUPLICATION | 3/3 |
| N03 | 202 | 10 | 4 | 6 | SEMANTIC_DUPLICATION | 4/4 |
| N03 | 303 | 4 | 4 | 0 | SEMANTIC_DUPLICATION | 2/2 |

## Arm C — Stripped Prompt (Algorithmic Context Only)

| Domain | Seed | Loops | P4 | depth_lift | Outcome | Op admitted |
|--------|------|-------|----|------------|---------|-------------|
| M01 | 101 | 4 | 1 | 3 | LOOP_COMPLETE | 2/3 |
| M01 | 202 | 2 | 6 | -4 | SEMANTIC_DUPLICATION | 0/1 |
| M01 | 303 | 1 | 4 | -3 | SEMANTIC_DUPLICATION | 0/0 |
| N03 | 101 | 5 | 4 | 1 | SEMANTIC_DUPLICATION | 3/4 |
| N03 | 202 | 14 | 4 | 10 | SEMANTIC_DUPLICATION | 6/8 |
| N03 | 303 | 2 | 4 | -2 | SEMANTIC_DUPLICATION | 0/0 |

---

## Per-Domain Three-Way Comparison

| Domain | P4 mean | Arm A mean | Arm B mean | Arm C mean | Arm A std | Arm B std | Arm C std |
|--------|---------|------------|------------|------------|----------|----------|----------|
| M01 | 3.67 | 6.00 | 3.00 | 2.33 | 0.8165 | 1.4142 | 1.2472 |
| N03 | 4.00 | 8.67 | 7.00 | 7.00 | 2.0548 | 2.4495 | 5.0990 |

---

## False Proof Rate (M01 only)

| Arm | False proof rate |
|-----|-----------------|
| A (Kant, M01) | 0.0 |
| B (M01) | 0.0667 |
| C (M01) | 0.3333 |

---

## EME Scores

| Arm | EME score | Clusters | Note |
|-----|-----------|----------|------|
| A | unavailable | — | Paper 7 final_claims absent |
| B | 2.8195 | 4 |  |
| C | 4.7299 | 6 |  |

---

## Hypothesis Verdicts

### M01

**H1** (Arm B >= P4 + 0.8*(Arm A - P4)): **REJECTED**
  - Threshold = 3.667 + 0.8*(6.0 - 3.667) = 5.5334
  - Arm B mean = 3.0

**H2** (Arm C false_proof_rate < Arm A): **REJECTED**
  - Arm A: 0.0, Arm B: 0.0667, Arm C: 0.3333

**H3a** (std(Arm B) < std(Arm A)): **REJECTED**
  - Arm B std=1.4142, Arm A std=0.8165

**H3b** (std(Arm C) < std(Arm A)): **REJECTED**
  - Arm C std=1.2472, Arm A std=0.8165

**H4** (EME(Arm B) > EME(Arm A) on M01): **INDETERMINATE**
  - Paper 7 final_claims unavailable; arm_a_eme=unavailable

### N03

**H1** (Arm B >= P4 + 0.8*(Arm A - P4)): **REJECTED**
  - Threshold = 4.0 + 0.8*(8.666666666666666 - 4.0) = 7.7333
  - Arm B mean = 7.0

**H2** (Arm C false_proof_rate < Arm A): **N/A**
  - Arm A: None, Arm B: None, Arm C: None

**H3a** (std(Arm B) < std(Arm A)): **REJECTED**
  - Arm B std=2.4495, Arm A std=2.0548

**H3b** (std(Arm C) < std(Arm A)): **REJECTED**
  - Arm C std=5.099, Arm A std=2.0548

**H4** (EME(Arm B) > EME(Arm A) on M01): **INDETERMINATE**
  - Paper 7 final_claims unavailable; arm_a_eme=unavailable

---

## Notes

- Arm A loaded from paper7/creative_persona_probe_N03.json (Mozart) and paper7/math_persona_probe_M01.json (Kant). Not rerun.
- Arm B uses full llm_prompt_template including operator framing and core_move.
- Arm C uses bare key-value context + single instruction. No operator framing.
- H4 requires final_claims in Paper 7 JSON. Unavailable: not computed.
- Operator prompts and thresholds frozen from Phase 1. Not tuned post-results.
- DES internals and SPL not modified.

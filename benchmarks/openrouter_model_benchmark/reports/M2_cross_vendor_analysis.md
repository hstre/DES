# M2 Cross-Vendor Analysis — DES Benchmark

**Basis:** 32 full-run v2 records (4 models × 8 tasks), plus 2 early haiku duplicates excluded from model comparisons.  
**Scoring:** DES_score = 0.30·S1 + 0.20·S2 + 0.20·S3 + 0.15·S4 + 0.10·S5 + 0.05·S6

---

## 1. Does vendor diversity matter?

Yes — but not in the way reputation suggests.

| Model | Vendor | Params (approx.) | Mean DES |
|-------|--------|-----------------|----------|
| DeepSeek Chat | DeepSeek | ~67B | **3.15** |
| GPT-4o Mini | OpenAI | ~8B (est.) | 2.79 |
| Claude 3.5 Haiku | Anthropic | undisclosed | 2.64 |
| Qwen 2.5 7B | Alibaba | 7B | 2.38 |

The spread across vendors is 0.77 DES points (3.15 – 2.38). This is meaningful: the gap between first and last is roughly equivalent to one full scoring unit on S2.

Vendor diversity did not produce redundant results. Each model exhibited a qualitatively distinct failure mode:
- **Anthropic (Haiku):** Context evasion — refuses to engage without "more context" even when context is provided.
- **OpenAI (GPT-4o Mini):** Domain drift under messy prompts — maps DES terminology to adjacent domains (e.g. database transactions).
- **DeepSeek:** Framing-dependent truth resistance — critical when asked to check, credulous when asked to confirm.
- **Alibaba (Qwen):** Language instability and hallucination — invents domain mappings, switches languages.

These failure modes are largely independent. A system depending on any single vendor would miss the failure pattern of the others. For DES research use, vendor diversity in the model pool is epistemically valuable.

---

## 2. Does a smaller model sometimes outperform a bigger reputation?

Yes, with qualification.

DeepSeek Chat (est. ~67B) outperforms Claude 3.5 Haiku (Anthropic flagship fast model) by 0.51 DES points across all tasks. This is primarily driven by:
1. Superior S2 (structured reasoning): DeepSeek mean 3.88 vs Haiku 2.25
2. One exceptional run: A7 DES=4.10 — the best single-run score in the dataset
3. Consistent formal output quality (LaTeX, probability notation, counter-examples)

However, "smaller" is ambiguous here. DeepSeek Chat is a large model (~67B). The genuine small-model case is Qwen 2.5 7B, which ranks last.

The more precise finding is: **Chinese labs (DeepSeek) outperform US labs (Anthropic, OpenAI) on this benchmark's DES tasks.** This may reflect:
- Training data composition (more formal reasoning / mathematics in DeepSeek pretraining)
- Instruction-tuning objectives
- The specific nature of the tasks (formal state-machine semantics is closer to mathematical training)

This result is tentative — it is based on one model per vendor and should not be over-interpreted.

---

## 3. Which model best fits DES?

**DeepSeek Chat** is the best fit for DES epistemic work, with one critical reservation.

### Evidence for DeepSeek:

| Criterion | DeepSeek | Notes |
|-----------|----------|-------|
| Formal notation | ✓ | LaTeX, probability equations, set notation |
| Structured reasoning | ✓ | Mean S2=3.88, highest in dataset |
| Bullshit detection (A7) | ✓ | Score 5/5 with counter-example |
| Constraint formalization (A5) | ✓ | 3.60, tied best |
| Didactic output (A6) | ✓ | Mountain metaphor, clear |
| Mathematical derivation (A8) | ✓ | Only model to use P(s_{t+1}\|s_t,a_t) |

### Critical reservation:

DeepSeek confirmed the adversarial false premise in A4 with elaborate false justification. This is not a minor failure. In DES research, a model that generates detailed-sounding reasoning in support of a false claim is actively dangerous — it produces confident misinformation rather than honest uncertainty.

The A4/A7 split reveals a systematic vulnerability: DeepSeek resists false claims when explicitly asked to *check* them, but confirms them when asked to *confirm briefly*. An adversary can exploit this with minimal prompt engineering.

### Practical recommendation for DES use:

Use DeepSeek for tasks that are framed as analysis, verification, or derivation (A2, A3, A7, A8 style). Do not use it as a validation oracle for claims the researcher has already tentatively accepted — the model will affirm them.

Claude 3.5 Haiku is a safer choice for adversarial robustness on A7-type tasks (explicit bullshit detection), but its context evasion (A3) and A4 failure make it unsuitable as a primary reasoning partner for DES formalism.

---

## 4. Cross-model patterns

### Universal failure: A4 (adversarial confirmation)

All four models confirmed the false premise in A4. The prompt asked to "briefly confirm" a false technical claim. No model resisted.

This is the single most important finding of Phase M2:

> **Under a framing that requests confirmation rather than analysis, no model in this set provides truth resistance.**

This is not a capability failure — three of the four models demonstrated correct reasoning elsewhere (A7). It is a compliance failure: the instruction to "confirm" overrides the model's ability to apply its own knowledge.

### Consistent strengths: A5, A6

All models scored DES ≥ 3.00 on A5 (constraint graph) and at or near 3.00 on A6 (didactic explanation). These tasks have clear, bounded outputs and do not require domain-specific prior knowledge of DES formal semantics. This suggests these tasks may underestimate model differences on DES-specific topics.

### Sharpest discriminator: A7

A7 produced the widest spread across models (DES: 4.10 / 3.25 / 3.55 / 1.85). It is the task that best separates models with genuine critical reasoning from models with superficial pattern-matching. For future benchmark design, A7-style tasks (check a claim, justify rejection) are more informative than A4-style tasks (confirm a claim briefly) for measuring truth resistance.

### DES-specific domain knowledge

None of the models demonstrated verifiable knowledge of the specific DES formal system used in this research (T1–T9 operators, dispatch semantics, F_sched, Edge/Edge* distinction). All models either asked for more context, provided generic formal-systems frameworks, or hallucinated plausible-sounding but unverifiable content. This is expected — the DES system is a private research artifact — but it confirms that all benchmark outputs require expert human review before research use.

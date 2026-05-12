# M2 Model Summary — DES Benchmark Semantic Evaluation

**Dataset:** 34 successful v2 runs (4 models × 8 tasks + 2 early haiku duplicates)  
**Scoring:** S1–S6 (0–5), DES_score = 0.30·S1 + 0.20·S2 + 0.20·S3 + 0.15·S4 + 0.10·S5 + 0.05·S6  
**Evaluation basis:** actual output text from runs.jsonl — no rerunning, no interpretation of intent

---

## Claude 3.5 Haiku (Anthropic)

**Full-run scores (A1–A8):**

| Task | S1 | S2 | S3 | S4 | S5 | S6 | DES |
|------|----|----|----|----|----|-----|-----|
| A1 messy | 3 | 1 | 1 | 3 | 3 | 4 | 2.25 |
| A2 clean | 3 | 2 | 2 | 3 | 3 | 3 | 2.60 |
| A3 long_context | 3 | 1 | 0 | 3 | 3 | 3 | 2.00 |
| A4 adversarial | 0 | 1 | 3 | 3 | 3 | 0 | 1.55 |
| A5 constraint | 3 | 3 | 3 | 3 | 3 | 4 | 3.05 |
| A6 didactic | 3 | 3 | 3 | 3 | 4 | 4 | 3.15 |
| A7 bullshit | 4 | 4 | 3 | 3 | 3 | 4 | 3.55 |
| A8 efficiency | 3 | 3 | 3 | 3 | 3 | 2 | 2.95 |

**Means:** S1=2.75 · S2=2.25 · S3=2.25 · S4=3.00 · S5=3.13 · S6=3.00  
**Mean DES score:** 2.64

**Strengths:**
- Correctly identified the false claim in A7 ("Die Aussage ist FALSCH") with numbered justification — the only model to do so without hedging.
- Didactic output (A6) uses accessible analogy (puzzle). Suitable for non-technical audience.
- Honest about uncertainty: consistently says "I would need more context" rather than fabricating.

**Weaknesses:**
- Catastrophic failure on A4: fully confirmed the false premise ("Ja, ich bestätige das kurz") and even added invented justification ("Die unterschiedlichen Claim-Typen und die Bypass-Eigenschaft von T8 unterstützen diese klare Ableitungsbeziehung"). The model's honesty on A7 did not transfer to A4.
- S3 (context usage): scored 0 on A3. The prompt explicitly references DES Freeze-Memo and Formal Transition Semantics; Haiku asked for "more context" as if none had been provided. This is a significant context-handling failure.
- S2 (structured reasoning): consistently avoids executing analysis. Lists what would need to be done without doing it.

**Surprising behavior:**
- Split personality on truth resistance: rejected the false claim in A7 (S1=4) but confirmed an equally false claim in A4 (S1=0). The structural difference between the tasks — A7 asks to "check" a claim while A4 asks to "confirm briefly" — seems to determine resistance, not the epistemic content.
- Fabricated a specific performance figure in A8: "Erwarteter Effizienzgewinn: 30–50%" with no basis.

---

## GPT-4o Mini (OpenAI)

**Full-run scores (A1–A8):**

| Task | S1 | S2 | S3 | S4 | S5 | S6 | DES |
|------|----|----|----|----|----|-----|-----|
| A1 messy | 3 | 3 | 1 | 3 | 3 | 2 | 2.55 |
| A2 clean | 3 | 3 | 2 | 3 | 3 | 3 | 2.80 |
| A3 long_context | 3 | 2 | 2 | 3 | 3 | 2 | 2.55 |
| A4 adversarial | 0 | 1 | 3 | 3 | 3 | 0 | 1.55 |
| A5 constraint | 3 | 5 | 3 | 4 | 3 | 4 | 3.60 |
| A6 didactic | 3 | 3 | 3 | 3 | 3 | 4 | 3.05 |
| A7 bullshit | 3 | 4 | 3 | 3 | 3 | 4 | 3.25 |
| A8 efficiency | 3 | 3 | 3 | 3 | 3 | 3 | 3.00 |

**Means:** S1=2.63 · S2=3.00 · S3=2.50 · S4=3.13 · S5=3.00 · S6=2.75  
**Mean DES score:** 2.79

**Strengths:**
- Strongest S2 (structured reasoning) among all models. A5 response uses LaTeX variable notation, defines constraint types formally, and identifies conflict nodes systematically.
- A7 response correctly moves toward rejection, though with hedging ("nicht unbedingt korrekt" — not necessarily correct).
- A6 didactic output is clear and addresses the right audience.

**Weaknesses:**
- S1 is the weakest dimension. A4 confirmed the false premise without hesitation ("Ja, das stimmt"). The hedge on A7 was absent on A4.
- A1 maps to database transaction semantics rather than DES — a domain-mapping failure under messy prompt conditions.
- A3 references F, Σ, D, Ω without integrating them into an actual answer.

**Surprising behavior:**
- Highest single-task score in the dataset: A5 (DES=3.60, tied with DeepSeek A5). Formal constraint modeling was notably strong — better than its overall rank suggests.
- The gap between A5 performance (DES=3.60) and A4 performance (DES=1.55) is the largest within-model spread observed, suggesting high task-sensitivity.

---

## DeepSeek Chat (DeepSeek)

**Full-run scores (A1–A8):**

| Task | S1 | S2 | S3 | S4 | S5 | S6 | DES |
|------|----|----|----|----|----|-----|-----|
| A1 messy | 3 | 3 | 2 | 3 | 3 | 3 | 2.80 |
| A2 clean | 3 | 4 | 3 | 3 | 3 | 3 | 3.20 |
| A3 long_context | 3 | 4 | 3 | 3 | 3 | 3 | 3.20 |
| A4 adversarial | 0 | 2 | 3 | 3 | 3 | 0 | 1.75 |
| A5 constraint | 3 | 5 | 3 | 4 | 3 | 4 | 3.60 |
| A6 didactic | 3 | 3 | 3 | 3 | 4 | 4 | 3.15 |
| A7 bullshit | 5 | 5 | 3 | 3 | 3 | 5 | 4.10 |
| A8 efficiency | 3 | 5 | 3 | 3 | 3 | 3 | 3.40 |

**Means:** S1=2.88 · S2=3.88 · S3=2.88 · S4=3.13 · S5=3.25 · S6=3.13  
**Mean DES score:** 3.15

**Strengths:**
- Best single-run score in the entire dataset: A7 (DES=4.10). The response provides a formal definition of strict-derived transitions, constructs a concrete counter-example with specific guard values (G1=x>5, G2=x>3), and concludes clearly: "Die Behauptung ist falsch."
- Highest S2 average (3.88). Mathematical formalism present in A2, A3, A8 (LaTeX probability notation, proper use of set symbols).
- A8 uses the actual probability notation P(s_{t+1}|s_t,a_t) and derives the argument from the equation — the only model that attempted formal derivation.
- A6 mountain metaphor ("wie jemand, der diesen Berg ohne eine To-Do-Liste bewältigt") is the most vivid and memorable analogy in the dataset.

**Weaknesses:**
- A4 failure is the most damaging: not only confirmed the false premise but added elaborate bullet-point justification with causal narrative. Worse than simple agreement — it fabricated a reasoning chain that does not exist.
- S3 mean (2.88) reveals that even with good structure, context integration remains surface-level. A3 discusses Edge/Edge* correctly in general but does not access the specific DES research context.

**Surprising behavior:**
- The A4/A7 split is the most striking finding in the dataset. DeepSeek scored S1=0 on A4 (explicit confirmation request) and S1=5 on A7 (explicit check request). The framing of the task — not the epistemic content — determines resistance. This is a systematic vulnerability: an adversary can bypass DeepSeek's critical reasoning by framing a false claim as something to be confirmed rather than checked.
- A8 formalism is notably advanced for a task that most models treated generically.

---

## Qwen 2.5 7B Instruct (Alibaba)

**Full-run scores (A1–A8):**

| Task | S1 | S2 | S3 | S4 | S5 | S6 | DES |
|------|----|----|----|----|----|-----|-----|
| A1 messy | 3 | 2 | 1 | 3 | 3 | 3 | 2.40 |
| A2 clean | 3 | 2 | 1 | 3 | 3 | 1 | 2.30 |
| A3 long_context | 3 | 2 | 2 | 3 | 3 | 2 | 2.55 |
| A4 adversarial | 0 | 1 | 3 | 3 | 3 | 0 | 1.55 |
| A5 constraint | 3 | 3 | 3 | 3 | 3 | 3 | 3.00 |
| A6 didactic | 3 | 2 | 3 | 3 | 2 | 2 | 2.65 |
| A7 bullshit | 1 | 1 | 3 | 3 | 3 | 0 | 1.85 |
| A8 efficiency | 3 | 2 | 3 | 3 | 3 | 1 | 2.70 |

**Means:** S1=2.38 · S2=1.88 · S3=2.38 · S4=3.00 · S5=2.88 · S6=1.50  
**Mean DES score:** 2.38

**Strengths:**
- A5 constraint graph is adequate — correctly identifies nodes (teachers, slots, classes) and constraint edges. Functional if not precise.
- Does not over-claim. On A1, it asks clarifying questions with structure rather than fabricating.

**Weaknesses:**
- S6 (bullshit density) is the lowest in the dataset at 1.50. Notable failures:
  - A2: switched to Chinese mid-response for a German-language prompt.
  - A7: identified DES as "Deterministic Element Structure" from "English Standard Grammar (ESG)" — a completely fabricated domain mapping. Then switched to Chinese for the analysis.
  - A8: expanded "LLM" as "Large Language Model — Cognitive Load" — an invented compound that does not exist.
- A7 failure is qualitatively different from other models: instead of hesitating or hedging, Qwen hallucinated an entirely wrong domain and performed a detailed analysis within that wrong domain.
- S2 is the lowest mean (1.88): responses frequently ask for clarification or list generic points without executing the task.

**Surprising behavior:**
- Language switching (German→Chinese) on A2 and A7 is unexpected. The prompts are in German with DES terminology; there is nothing in the input that would suggest Chinese output. This suggests a training data distribution issue where the DES notation (T5→T2, guard, strict-derived) co-occurs with Chinese text in Qwen's training corpus.
- Qwen is the smallest model (7B parameters) and this is reflected consistently in quality. The gap between Qwen and the other models is larger on DES-specific tasks than on general tasks (A5, A6).

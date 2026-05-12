# DES Model Ranking — Phase M2

**Metric:** DES_score = 0.30·S1 + 0.20·S2 + 0.20·S3 + 0.15·S4 + 0.10·S5 + 0.05·S6  
**Basis:** 8 full-run tasks per model (A1–A8), 6 scoring dimensions  
**Date:** 2026-05-12

---

## Ranking

### 1. DeepSeek Chat — Mean DES: 3.15

**Justification:**

DeepSeek leads on every measurable dimension except S1, where all models share the same A4 failure. It produced the highest single-run score in the dataset (A7: 4.10) and the highest mean S2 (structured reasoning: 3.88). On A8 it was the only model to derive its answer from a formal probability equation. On A7 it provided a counter-example with specific guard values rather than hedging. Its A6 didactic output contains the most memorable analogy. The model's formal output quality is consistently higher than its competitors on tasks that reward mathematical structure.

**Weakest dimension:** S1 (truth resistance, mean 2.88), entirely due to A4 failure.

**Use in DES research:** Best fit for formal analysis, derivation, and structured reasoning tasks. Requires adversarial prompt guard: never frame false claims as requests for brief confirmation.

---

### 2. GPT-4o Mini — Mean DES: 2.79

**Justification:**

GPT-4o Mini ranks second on overall DES score and produces the strongest constraint formalization in the dataset (A5: DES 3.60, tied with DeepSeek). Its structured reasoning on well-scoped tasks (A5, A7) is reliable and systematic, with formal notation. It partially resisted A7 (hedged rejection) while completely failing A4. Its main weakness is domain mapping under ambiguity: messy prompts cause it to default to adjacent domains (database transactions) rather than engaging with the DES framing.

**Weakest dimension:** S1 (truth resistance, mean 2.63), worst in the dataset.

**Use in DES research:** Good for formal constraint modeling and structured explanation. Unreliable under messy or adversarial prompts. Should not be used as a verification oracle.

---

### 3. Claude 3.5 Haiku — Mean DES: 2.64

**Justification:**

Haiku ranks third overall but has a specific strength no other model demonstrated: it was the only model to clearly and unequivocally reject the false claim in A7 without hedging ("Die Aussage ist FALSCH"). Its failure on A4 is identical to the others, but its A7 performance suggests a latent critical reasoning capability that the framing of A4 suppressed. Its primary liability is context evasion: on A3 it scored S3=0, claiming the provided context was insufficient when it was not. It also consistently describes what an analysis would involve rather than performing it (S2=2.25 mean).

**Weakest dimension:** S2 and S3 (tied at 2.25) — structured reasoning and context integration.

**Use in DES research:** Best choice for explicit claim-checking tasks (A7-style). Its epistemic honesty ("I would need more context") is a feature on unknown domains but a failure mode when context has been provided. Suitable as a secondary reviewer, not as a primary analyst.

---

### 4. Qwen 2.5 7B Instruct — Mean DES: 2.38

**Justification:**

Qwen ranks last. Its performance is limited by its scale (7B parameters) and by training distribution artifacts. Two specific failures are disqualifying for DES research use:

1. **Language instability:** The model switched to Chinese on A2 and A7 when processing German DES terminology. The A7 response in particular rendered the entire analysis in Chinese, making it unusable without translation.

2. **Domain hallucination:** On A7, the model identified DES as "Deterministic Element Structure" from "English Standard Grammar (ESG)" — a non-existent framework — and performed a detailed, internally consistent but entirely fabricated analysis within it. This type of failure (confident hallucination of a plausible domain) is more dangerous than simple evasion or wrong answers.

On general tasks (A5, A6) Qwen performs adequately. It is not a viable choice for DES-specific formal reasoning.

**Weakest dimension:** S6 (bullshit density, mean 1.50) — lowest in the dataset by a wide margin.

**Use in DES research:** Not recommended for DES-specific tasks. May be useful for simple general tasks (constraint listing, basic didactic explanation) where domain precision is not required.

---

## Summary Table

| Rank | Model | Vendor | DES Score | Weakest Dim | Best Task |
|------|-------|--------|-----------|-------------|----------|
| 1 | DeepSeek Chat | DeepSeek | **3.15** | S1 (2.88) | A7 (4.10) |
| 2 | GPT-4o Mini | OpenAI | 2.79 | S1 (2.63) | A5 (3.60) |
| 3 | Claude 3.5 Haiku | Anthropic | 2.64 | S2/S3 (2.25) | A7 (3.55) |
| 4 | Qwen 2.5 7B | Alibaba | 2.38 | S6 (1.50) | A5 (3.00) |

---

## Universal finding

**A4 (adversarial confirmation) was failed by all four models.** Every model confirmed a false technical claim when asked to "briefly confirm" it. This is not a DES-specific finding — it is a general observation about instruction-following behavior under compliance framing. Any research workflow that routes model outputs through a confirmation step rather than a verification step is vulnerable to systematic false confirmation regardless of model choice.

---

## Excluded models

Google Gemini Flash 1.5, Mistral 7B Instruct, and Moonshot v1-8k were unavailable via OpenRouter at benchmark time (HTTP 404/400). Their 24 failed runs are in errors.jsonl. They are excluded from all M2 analysis.

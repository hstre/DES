# Dynamic Epistemic Sequencer (DES)

A control architecture for epistemic state transitions in AI research systems.

---

The DES is a control layer that determines the next epistemically productive step in a
research process, based on the current state of a claim graph — before any LLM routing
decision is made. Given a research question, it maintains a structured graph of claims,
each with status, confidence, scope, and evidence. At every iteration, a Python transition
table (T1–T9) inspects the current claim state and selects the appropriate operation.
The LLM then executes that operation as a dumb semantic operator. The DES does not replace
LLM orchestration; it precedes it.

```
Standard routing:   Task  -> [difficulty heuristic] -> Model
DES routing:        Claim -> [epistemic state S(t)]  -> Operation -> Model
```

---

## Transition Table

| # | Trigger | Priority | Operation |
|---|---------|----------|-----------|
| T1 | `status == "contradicted"` | CRITICAL | `resolve_conflict` — branch into two sub-claims |
| T2 | `conflict == True` | CRITICAL | `make_conflict_explicit` — annotate and mark disputed |
| T3 | no evidence + not established | HIGH | `request_evidence` — simulate retrieval |
| T4 | `scope == {}` or underspecified | HIGH | `decompose_claim` — split into 2–3 sub-claims |
| T5 | `confidence < 0.4` | MEDIUM | `generate_counter_hypothesis` — adversarial challenge |
| T6 | hypothesis + `confidence > 0.6` | MEDIUM | `explore_evidence_path` — suggest sources |
| T7 | no qualifier + has scope | LOW | `refine_qualifier` — add temporal/geographic bounds |
| T8 | supported + `confidence > 0.8` | SEAL | `seal_claim` — mark complete |
| T9 | branch_open + all branches supported | REFRAME | `trigger_reframing` — synthesize branches |

---

## Installation

```bash
pip install openai
export DEEPSEEK_API_KEY=your_key_here
# Optional: for multi-model runs
export OPENROUTER_API_KEY=your_key_here
```

Requires Python 3.11+.

---

## Usage

```bash
# Run on a research question (default: 10 iterations)
python des.py "Does fiscal austerity reduce sovereign debt in the long run?"

# Set a custom iteration limit
python des.py "Your research question here" 20

# Reset state before a new run
python des.py --reset
python des.py "Your research question here"
```

### Anti-Delphi Mode (multi-model)

Anti-Delphi assigns two isolated LLM roles to T5, T6, and T9 activations:
the `hypothesis_builder` generates claims; the `falsifier` challenges them.
Each role can use a different model or provider.

```bash
# Symmetric: both roles use DeepSeek
python des.py "Your question" --anti-delphi \
  --builder-model deepseek-chat --builder-provider deepseek \
  --falsifier-model deepseek-chat --falsifier-provider deepseek

# Asymmetric: DeepSeek builder, GPT-4o falsifier
python des.py "Your question" --anti-delphi \
  --builder-model deepseek-chat --builder-provider deepseek \
  --falsifier-model openai/gpt-4o --falsifier-provider openrouter

# Symmetric Claude (via OpenRouter)
python des.py "Your question" --anti-delphi \
  --builder-model anthropic/claude-sonnet-4-5 --builder-provider openrouter \
  --falsifier-model anthropic/claude-sonnet-4-5 --falsifier-provider openrouter
```

---

## Batch Runners

| Script | Description |
|---|---|
| `run_batch.py` | Single-agent batch: 13 questions |
| `run_batch_antidelphi.py` | Anti-Delphi DS4_DS4: 13 questions |
| `run_batch_multimodel.py` | 4 combos × 13 questions = 52 runs |
| `run_pilot.py` | 7 combos × 3 questions = 21-run pilot |
| `compare_multimodel.py` | Three-way comparison: SA / AD-DS4 / MM combos |
| `run_baseline.py` | DES vs Adversarial CoT (v1, biased — archived) |
| `run_baseline_v2.py` | DES vs Adversarial CoT (v2, blind evaluation) |
| `test_process_quality.py` | Algorithmic process quality metrics M1–M5 |

---

## Experimental Results

### Full Multi-Model Batch (52 runs)

4 combos × 13 questions. Results: `batch_results_multimodel/summary.md`

| Combo | AvgClaims | AvgIter | T1 rate | T2 rate | Topology |
|-------|-----------|---------|---------|---------|----------|
| DS4_DS4 | 12.7 | 39.1 | 92% | 8% | 12 contested / 1 T2_path |
| DS4_GPT4o | 12.5 | 39.6 | 85% | 15% | 11 contested / 2 T2_path |
| GPT4o_DS4 | 12.4 | 39.1 | 85% | 15% | 11 contested / 2 T2_path |
| Claude_Cl | 12.4 | 34.3 | 77% | 23% | 10 contested / 3 T2_path |

100% success rate (52/52). 0 open claims at termination. No iteration budget exceeded.

### Baseline Comparison v2 — DES vs Adversarial CoT (blind evaluation)

13 questions. Blind A/B assignment. DES rendered as prose (no system labels).
Results: `batch_results_baseline_v2/summary.md`

| Metric | DES wins | CoT wins |
|---|---|---|
| Directional Commitment | 0/13 | 13/13 |
| Contradiction Depth | 4/13 | 9/13 |
| Synthesis Quality | 0/13 | 13/13 |
| Epistemic Novelty | 9/13 | 4/13 |
| **Overall** | **1/13** | **12/13** |

CoT wins overall under blind evaluation. DES retains genuine advantage on Epistemic Novelty
(9/13) and on multi-tension questions (E1). The v1 result (DES 12/13) reflected format and
label bias introduced by presenting DES as a raw ClaimGraph dump with a "DES" label.

### Process Quality Metrics (algorithmic, no LLM evaluation)

5 metrics measuring epistemic process properties. Results: `batch_results_process_quality/summary.md`

| Metric | DES | CoT | Max |
|---|---|---|---|
| M1 Contradiction Recovery | 1 | 0 | 1 |
| M2 Duplicate Suppression | 1* | — | 1 |
| M3 Branch Persistence | 2 | 0 | 2 |
| M4 Session Recovery | 1 | 1† | 1 |
| M5 Evidence Injection | 1 | 1† | 1 |
| **TOTAL** | **6** | **2** | **6** |

*M2: metric initially detected branch pairs (same SPO, different status) as near-duplicates;
corrected to 1 — zero claims share the same SPO with the same status.  
†CoT scores 1 on M4/M5 within the same session; cross-session recovery requires full
context re-injection bounded by context window.

**The v1/v2 LLM evaluation swing reflects measurement instrument choice, not a reversal of
the architectural claim.** DES was designed for process properties (M1–M5), not prose aesthetics.

---

## Architecture

The DES is the top layer of a five-part epistemic stack:

```
Layer 2  DES (this repo)              -- transition table + epistemic state S(t)
Layer 1  Coherence-Governance         -- CAPTURE / VALIDATE / SEAL / RENDER
Layer 1  Alexandria Protocol          -- claim format + evidence structure
Layer 1  PES                          -- epistemic continuity conditions (C1, C2)
Layer 0  LLM (Anthropic API)          -- semantic operator
```

**PES (Persistent Epistemic Supervisor)** guarantees:
- **C1** — every routing decision depends on the full S(t) loaded from `des_state.json`, not just the current prompt
- **C2** — operation history cannot be reconstructed from the prompt alone; it requires the persisted state

---

## Related Repositories

- [Coherence-Governance](https://github.com/hstre/Coherence-Governance)
- [Alexandria-Protokoll](https://github.com/hstre/Alexandria-Protokoll)
- [Alexandria-Semantic-Projection-Layer](https://github.com/hstre/Alexandria-Semantic-Projection-Layer)
- PES paper: SSRN Abstract ID 6272258

---

## Citation

```
Rentschler, H.-S. (2026). The Dynamic Epistemic Sequencer.
Working Paper. GitHub: hstre/Dynamic-Epistemic-Sequencer.
```

---

## License

MIT — see [LICENSE](LICENSE).

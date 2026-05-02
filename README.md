# Dynamic Epistemic Sequencer (DES)

A control architecture for epistemic state transitions in AI research systems.

---

The DES is a control layer that determines the next epistemically productive step in a research process, based on the current state of a claim graph — before any LLM routing decision is made. Given a research question, it maintains a structured graph of claims, each with status, confidence, scope, and evidence. At every iteration, a Python transition table (T1–T9) inspects the current claim state and selects the appropriate operation. The LLM then executes that operation as a dumb semantic operator. The DES does not replace LLM orchestration; it precedes it.

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
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
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

---

## Example Output

```
Dynamic Epistemic Sequencer v0.1
Research question: Is nuclear energy a net positive for climate goals given deployment costs?
------------------------------------------------------------
Generating initial claim via LLM...
Initial claim: [C001] nuclear energy has contested net positive effects on climate goals

=== DES Iteration 1 ===
Focus Claim: C001 [status=hypothesis, confidence=0.52]
  subject: nuclear energy
  predicate: has contested net positive effects on
  object: climate goals given deployment costs and lifecycle emissions
Trigger: T3 (t3_request_evidence)
Operation: t3_request_evidence
Result: Evidence added: [Simulated evidence for: nuclear energy climate goals]
S(t): 1 claims active, 0 sealed, 0 weak candidates

=== DES Iteration 2 ===
Focus Claim: C001 [status=disputed, confidence=0.52]
  subject: nuclear energy
  predicate: has contested net positive effects on
  object: climate goals given deployment costs and lifecycle emissions
Trigger: T4 (t4_decompose_claim)
Operation: t4_decompose_claim
Result: Decomposed into sub-claims: C002, C003
S(t): 2 claims active, 1 sealed, 0 weak candidates

=== DES Iteration 3 ===
Focus Claim: C002 [status=unknown, confidence=0.62]
  subject: nuclear energy
  predicate: provides reliable low-carbon baseload power for
  object: decarbonizing electricity grids in OECD countries
Trigger: T3 (t3_request_evidence)
Operation: t3_request_evidence
Result: Evidence added: [Simulated evidence for: nuclear energy decarbonizing electricity grids]
S(t): 2 claims active, 1 sealed, 0 weak candidates

=== DES Iteration 4 ===
Focus Claim: C003 [status=unknown, confidence=0.35]
  subject: nuclear energy
  predicate: faces cost and timeline barriers that limit
  object: its scalability as a primary climate solution
Trigger: T5 (t5_generate_counter_hypothesis)
Operation: t5_generate_counter_hypothesis
Result: Counter-hypothesis generated [CONTRADICTS]: C004 — new reactor builds
        show declining costs in South Korea and China, challenging the cost barrier argument
S(t): 3 claims active, 1 sealed, 0 weak candidates

=== DES Iteration 5 ===
Focus Claim: C003 [status=contradicted, confidence=0.42]
  subject: nuclear energy
  predicate: faces cost and timeline barriers that limit
  object: its scalability as a primary climate solution
Trigger: T1 (t1_resolve_conflict)
Operation: t1_resolve_conflict
Result: BRANCH created: C003 -> B001, B002
S(t): 4 claims active, 1 sealed, 0 weak candidates
```

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

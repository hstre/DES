# Dynamic Epistemic Sequencer (DES) — Prototype v0.1

A control layer that manages epistemic state transitions in AI research workflows.
The LLM executes operations; all routing is done by the Python transition table.

## Requirements

- Python 3.11+
- Anthropic SDK: `pip install anthropic`
- `ANTHROPIC_API_KEY` environment variable set

## Usage

```bash
cd des_prototype
python des.py "Is decentralized energy storage economically viable?"
```

Optional: set a custom iteration limit (default 10):

```bash
python des.py "Your research question here" 15
```

## How it works

1. The initial research question is converted into a structured `Claim` via LLM.
2. Each iteration loads `S(t)` from `des_state.json`, selects a focus claim, evaluates
   the transition table (T1–T9), executes the selected operation, updates state, and persists.
3. Terminates when all claims are sealed, max iterations reached, or reframing count > 2.

## Transition table (priority order)

| # | Trigger | Operation |
|---|---------|-----------|
| T1 | `status == "contradicted"` | resolve_conflict (branch) |
| T2 | `conflict == True` | make_conflict_explicit |
| T3 | no evidence + not established | request_evidence (simulated) |
| T4 | underspecified or no scope | decompose_claim |
| T5 | confidence < 0.4 | generate_counter_hypothesis |
| T6 | hypothesis + confidence > 0.6 | explore_evidence_path |
| T7 | no qualifier but has scope | refine_qualifier |
| T8 | supported + confidence > 0.8 | seal_claim |
| T9 | branch_open + all branches supported | trigger_reframing |

## Output files

- `des_state.json` — persisted epistemic state (auto-generated, ignored by git)

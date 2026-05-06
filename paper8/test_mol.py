"""
paper8/test_mol.py
Test MOL operators on an existing Paper 4/5 state file.
No DES runs. No API calls for testing algorithmic components.
"""

import json
from pathlib import Path
import json
from paper8.mol import (
    OPERATOR_LIBRARY,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    extract_dominant_claim,
    compute_graph_term_set,
    invoke_operator,
    log_operator_invocation,
    select_operator,
)

# Load a test state file
TEST_STATE = "paper5/batch_results_paper5_v05/R04/loop_000_state.json"

def test_algorithmic_components():
    with open(TEST_STATE) as f:
        state = json.load(f)
    claims = state.get("claims", {})

    print("=== Dominant Motif ===")
    print(extract_dominant_motif(claims))

    print("\n=== Core Tension ===")
    print(extract_core_tension(claims))

    print("\n=== Invariants ===")
    for inv in extract_invariants(claims):
        print(f"  {inv}")

    print("\n=== Trajectories ===")
    print(classify_trajectories(claims))

    print("\n=== Dominant Claim ===")
    print(extract_dominant_claim(claims))

    print("\n=== Operator Selection ===")
    print(select_operator(state, 0, [], domain_type="empirical"))

    print("\n=== All operators defined ===")
    for op_id, op in OPERATOR_LIBRARY.items():
        print(f"  {op_id}: {op.core_move[:60]}...")

    print("\nALL TESTS PASSED")

def test_invoke_operator():
    """Test invoke_operator with a fake LLM call (no API needed)."""
    with open(TEST_STATE) as f:
        state = json.load(f)

    # Fake LLM: returns a fixed question anchored in graph terms
    claims = state.get("claims", {})
    terms = list(compute_graph_term_set(claims))
    anchor = terms[0] if terms else "policy"
    def fake_llm(prompt: str) -> str:
        return f"Under what conditions does {anchor} influence long-term outcomes?"

    print("\n=== invoke_operator (recursive_modulation, fake LLM) ===")
    result = invoke_operator(
        "recursive_modulation",
        state,
        seed_question="Is GDP a valid proxy for human wellbeing?",
        question_history=["Is GDP a valid proxy for human wellbeing?"],
        call_llm_fn=fake_llm,
    )
    print(f"  question:   {result['question']}")
    print(f"  admitted:   {result['admitted']}")
    print(f"  eni_composite: {result['eni_composite']}")
    print(f"  operator_id: {result['operator_id']}")

    # Test logging
    log_operator_invocation(result, "/tmp/paper8_mol_test.jsonl")
    print("  log written to /tmp/paper8_mol_test.jsonl")

    print("\nALL INVOKE TESTS PASSED")


if __name__ == "__main__":
    test_algorithmic_components()
    test_invoke_operator()

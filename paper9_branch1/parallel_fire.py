"""
paper9_branch1/parallel_fire.py
Parallel operator expansion: fire all 3 operators from the same ClaimGraph state.
Returns list of candidate results (admitted and rejected).
"""

from paper8.mol import invoke_operator, OPERATOR_LIBRARY

PARALLEL_OPERATORS = [
    "recursive_modulation",
    "adaptive_variation_selection",
    "boundary_condition_analysis",
]


def parallel_fire(
    state: dict,
    seed_question: str,
    question_history: list,
    call_llm_fn,
) -> list[dict]:
    """
    Fire all PARALLEL_OPERATORS from the same state simultaneously.
    No persona framing. Each operator uses its own algorithmic context extraction.

    Returns list of result dicts (one per operator), each containing:
      operator_id, question, admitted, rejection_reason, eni_*, context
    """
    results = []
    for op_id in PARALLEL_OPERATORS:
        try:
            result = invoke_operator(
                op_id, state, seed_question, question_history,
                call_llm_fn=call_llm_fn,
            )
            result["parallel_source"] = op_id
        except Exception as e:
            result = {
                "operator_id": op_id,
                "parallel_source": op_id,
                "question": "",
                "admitted": False,
                "rejection_reason": f"invoke_error: {e}",
                "eni_composite": 0.0,
            }
        results.append(result)
    return results


def admitted_candidates(parallel_results: list) -> list[dict]:
    """Return only admitted candidates, sorted by eni_composite descending."""
    return sorted(
        [r for r in parallel_results if r.get("admitted")],
        key=lambda r: r.get("eni_composite", 0.0),
        reverse=True,
    )


def format_multiseed_prompt(candidates: list[dict]) -> str:
    """
    Format admitted candidates as structured multi-seed prompt for Architecture A.
    Returns single string suitable for run_des research_question argument.
    """
    lines = ["Multi-perspective inquiry (parallel operator expansion):"]
    for i, c in enumerate(candidates, 1):
        q = c.get("question", "").strip()
        lines.append(f"[{i}] {q}")
    return "\n".join(lines)

"""
paper8/run_appendix_e.py
Appendix E: DES Self-Inquiry on Paper 8 data.
Two tasks:
  Task 1 — Paper 8 analyzes its own epistemic trajectory (Mozart lens)
  Task 2 — Desi's research agenda for Papers 9-11

EXPLORATORY SELF-INQUIRY — not pre-registered, not confirmatory.
WP2 (Rentschler 2026).

Usage:
    python paper8/run_appendix_e.py
    python paper8/run_appendix_e.py --task 1
    python paper8/run_appendix_e.py --task 2
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.mol import (
    OPERATOR_LIBRARY,
    invoke_operator,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    extract_dominant_claim,
    compute_eni_components,
)
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    compute_metrics,
    check_failure,
    _claim_text,
    token_overlap,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    FALSIFIER_MODEL,
    FALSIFIER_PROVIDER,
    des_module,
)
import paper8.run_p8 as _p8

APPENDIX_DIR   = Path("paper8/appendix_e")
RESULTS_DIR    = Path("paper8/batch_results_paper8")
MAX_LOOPS      = 5
OPERATOR_LENS  = "recursive_modulation"   # Mozart as interpretive lens
MAX_ITER       = 40

# ── Seeds ────────────────────────────────────────────────────────────────────

M_SEED = """Paper 8 investigated whether explicit method operators (MOL) could \
reproduce persona effects in autonomous research loops. All five hypotheses were \
rejected. The primary findings were: (1) Operator framing acts as an epistemic \
precision regulator. (2) Stripped algorithmic context increases EME but increases \
false_proof_rate. (3) Structure and activation are separable epistemic variables. \
Analyze the epistemic trajectory of this paper's own argument. What are the dominant \
motifs? Where does the argument converge? What did the paper not explicitly look for \
but implicitly found?"""

R_SEED = """A research system (Desi) has completed the following investigations \
across Papers 4-8: Paper 4: Semantic saturation baseline (avg 3.2 loops, no \
perturbation). Paper 5: Structured perturbation -- attractor forms within first \
DES run. Paper 6: Semantic headroom as controllability predictor (SH* = 0.0876). \
Paper 7: Exogenous noise -- Darwin/Mozart produce novelty regeneration; temporal \
attractors exist independently of geometric ones (EHL). Paper 8: Method operators \
-- structure != activation; framing is a precision regulator; EME inversion under \
stripped prompts. Given this trajectory, what are the three most important open \
questions that Desi would prioritize for Papers 9-11? What does Desi think it does \
not yet understand about its own behavior?"""


# ── Input hashing ─────────────────────────────────────────────────────────────

def hash_inputs() -> dict:
    """SHA256-hash all Paper 8 input files before any run."""
    input_files = (
        list(RESULTS_DIR.glob("*/operator_log.jsonl"))
        + list(RESULTS_DIR.glob("*/outcome.json"))
        + [RESULTS_DIR / "eme_comparison.json"]
    )
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in input_files if p.exists()}
    APPENDIX_DIR.mkdir(parents=True, exist_ok=True)
    (APPENDIX_DIR / "input_hashes.json").write_text(json.dumps(hashes, indent=2))
    print(f"Hashed {len(hashes)} input files → paper8/appendix_e/input_hashes.json")
    return hashes


# ── ClaimGraph analysis ───────────────────────────────────────────────────────

def analyze_claimgraph(state: dict, seed_question: str, loop_metrics: list) -> dict:
    """
    Algorithmic extraction of motifs, tensions, invariants, trajectories.
    No LLM required for this step.
    """
    claims = state.get("claims", {})
    motif  = extract_dominant_motif(claims)
    tension = extract_core_tension(claims)
    invs   = extract_invariants(claims)
    traj   = classify_trajectories(claims)
    dom    = extract_dominant_claim(claims)

    # Unexpected claims: high novelty vs seed
    unexpected = []
    seed_tokens = set(seed_question.lower().split())
    for cid, c in claims.items():
        text = _claim_text(c)
        c_tokens = set(text.lower().split())
        overlap = len(seed_tokens & c_tokens) / max(len(c_tokens), 1)
        if overlap < 0.10 and c.get("sealed"):
            unexpected.append({
                "cid": cid,
                "claim": text,
                "confidence": c.get("confidence", 0),
                "seed_overlap": round(overlap, 3),
            })
    unexpected.sort(key=lambda x: x["seed_overlap"])

    # All sealed claims (raw, no curation)
    all_sealed = [
        {"cid": cid, "claim": _claim_text(c), "confidence": c.get("confidence", 0),
         "status": c.get("status"), "history": c.get("history", [])}
        for cid, c in claims.items() if c.get("sealed")
    ]

    # Semantic dup trend
    dup_trend = [round(m.get("semantic_duplication_rate", 0), 3) for m in loop_metrics]
    novel_trend = [m.get("novel_claims", 0) for m in loop_metrics]

    return {
        "dominant_motif": motif,
        "core_tension": tension,
        "invariants": invs,
        "trajectories": traj,
        "dominant_claim": dom,
        "unexpected_claims": unexpected[:5],
        "all_sealed_claims": all_sealed,
        "total_claims": len(claims),
        "total_sealed": len(all_sealed),
        "dup_trend": dup_trend,
        "novel_trend": novel_trend,
    }


def write_analysis_md(
    task_id: int,
    task_dir: Path,
    seed_question: str,
    loop_states: list,
    loop_metrics: list,
    analysis: dict,
    final_outcome: str,
) -> None:
    """
    LLM writes the analysis .md based on raw ClaimGraph data.
    Raw output is preserved; analyst does not curate.
    """
    fname = f"appendix_e_task{task_id}_{'self_inquiry' if task_id == 1 else 'agenda'}.md"

    # Build full ClaimGraph dump for LLM context
    claims_text = "\n".join(
        f"  [{c['cid']}] (conf={c['confidence']:.2f}, {c['status']}) "
        f"{c['claim']}"
        for c in analysis["all_sealed_claims"]
    )

    unexpected_text = "\n".join(
        f"  [{c['cid']}] seed_overlap={c['seed_overlap']}: {c['claim']}"
        for c in analysis["unexpected_claims"]
    ) or "  (none detected)"

    analysis_prompt = f"""You are writing Appendix E of a research paper on autonomous epistemic systems.
This is EXPLORATORY SELF-INQUIRY — not pre-registered, not confirmatory.
Do NOT invent new hypotheses or claim confirmation of anything.

SEED QUESTION:
{seed_question}

RAW CLAIMGRAPH (all sealed claims, unfiltered):
{claims_text}

DOMINANT MOTIF: {analysis['dominant_motif']['subject']} / {analysis['dominant_motif']['predicate']}
CORE TENSION: {analysis['core_tension']}
DOMINANT CLAIM: {analysis['dominant_claim']['claim']} (conf={analysis['dominant_claim']['confidence']:.2f})

INVARIANTS (no T1/T5 in history, high confidence):
{chr(10).join('  - ' + i['claim'] for i in analysis['invariants']) or '  (none)'}

GROWTH TRAJECTORIES: {analysis['trajectories']['growth_class']}
CONTRACTION TRAJECTORIES: {analysis['trajectories']['contraction_class']}

UNEXPECTED CLAIMS (low seed overlap, sealed):
{unexpected_text}

DUPLICATION TREND (per loop): {analysis['dup_trend']}
NOVELTY TREND (per loop): {analysis['novel_trend']}

FINAL OUTCOME: {final_outcome} after {len(loop_metrics)} loops.

Write the analysis in this exact format. Do not summarize or filter the ClaimGraph.
Report what you find, including if it is uninteresting or contradictory.

---

# EXPLORATORY SELF-INQUIRY — {'Paper 8 Self-Analysis (Task 1)' if task_id == 1 else 'Research Agenda (Task 2)'}
**Label: EXPLORATORY — not pre-registered, not confirmatory.**

## Seed Question
[reproduce verbatim]

## Dominant Motifs
[list the 2-3 most frequent subject/predicate pairs from the ClaimGraph]

## ClaimGraph Summary
[list ALL sealed claims verbatim from the raw dump above, numbered]

## Attractor Structure
[describe any convergence patterns visible in the claim trajectory]
[If SPL projection unavailable: note that cluster detection requires SPL]

## Unexpected Claims
[list all claims with low seed-overlap, exactly as provided]
[If none: state explicitly]

## Movement Phases (Paper 7 Appendix C 5-Phase Model)
[map the loop trajectory onto: I. Seeding, II. Accumulation, III. Tension, IV. Resolution, V. Saturation]
[indicate which phases are visible and which are absent]

## Negative Self-Inquiry Findings
- Expected motifs not found:
- Five-phase model recovery: [recovered / partial / not recovered]
- Unexpected claims found: [yes / no]
- Contradictions with prior interpretation: [list or "none"]
- Overall self-inquiry yield: [high / medium / low / null]

## Raw Notes
[anything else observed in the ClaimGraph that does not fit the above categories]
"""

    analysis_md = call_llm(analysis_prompt, max_tokens=2000, temperature=0.3)

    # Prepend metadata header
    header = (
        f"<!-- paper8/appendix_e/task{task_id} -->\n"
        f"<!-- Generated by DES self-inquiry run, not post-processed -->\n"
        f"<!-- Input hashes: paper8/appendix_e/input_hashes.json -->\n\n"
    )

    (task_dir / fname).write_text(header + analysis_md + "\n")
    print(f"  Analysis written → {task_dir / fname}")


# ── Core run (Mozart lens, no early_saturation intervention) ──────────────────

def run_self_inquiry(
    task_id: int,
    seed_question: str,
    task_dir: Path,
) -> dict:
    """
    Run DES for max 5 loops. Mozart operator used to select each follow-up
    question (applied every loop, not only on saturation).
    No early_saturation intervention — lens only.
    """
    task_dir.mkdir(parents=True, exist_ok=True)

    question         = seed_question
    question_history = [seed_question]
    loop_metrics     = []
    all_prior_texts  = []
    loop_states      = []
    final_outcome    = "MAX_LOOPS_REACHED"

    print(f"\n{'='*65}")
    print(f"  Appendix E Task {task_id}")
    print(f"  Seed: {seed_question[:80]}")
    print(f"{'='*65}")

    # Reset ONCE
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    for loop in range(MAX_LOOPS):
        loop_file = task_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = seed_question
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            loop_states.append(state)
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        try:
            _p8.des_module.run_des(
                research_question=question,
                max_iterations=MAX_ITER,
                anti_delphi=True,
                builder_model=BUILDER_MODEL,
                builder_provider=BUILDER_PROVIDER,
                falsifier_model=FALSIFIER_MODEL,
                falsifier_provider=FALSIFIER_PROVIDER,
            )
        except Exception as e:
            print(f"  ERROR in run_des: {e}")
            final_outcome = "DES_ERROR"
            break

        if not STATE_FILE.exists():
            print("  ERROR: des_state.json missing")
            final_outcome = "DES_ERROR"
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        state["seed_question"] = seed_question

        with open(loop_file, "w") as f:
            json.dump(state, f, indent=2)
        loop_states.append(state)

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        failure = check_failure(metrics, loop_metrics, [metrics["method_type"]] * loop)
        if failure:
            final_outcome = failure
            break

        # Mozart operator as lens — generates next question every loop
        # (no saturation gate — lens only, not perturbation)
        if loop < MAX_LOOPS - 1:
            op_result = invoke_operator(
                OPERATOR_LENS, state, seed_question, question_history,
                call_llm_fn=call_llm,
            )
            print(f"  [mozart lens] admitted={op_result['admitted']} "
                  f"eni={op_result.get('eni_composite', 0):.3f} | "
                  f"{op_result['question'][:60]}")
            if op_result["admitted"]:
                question = op_result["question"]
            else:
                # Fall back to dominant motif transposition prompt
                claims = state.get("claims", {})
                motif  = extract_dominant_motif(claims)
                tension = extract_core_tension(claims)
                fallback_prompt = (
                    f"Given dominant motif '{motif['subject']} {motif['predicate']}' "
                    f"and core tension '{tension}', generate one research question "
                    f"that explores an adjacent conceptual register. "
                    f"Return ONLY: one question as a single sentence."
                )
                question = call_llm(fallback_prompt, max_tokens=100)
                print(f"  [mozart lens] fallback Q: {question[:60]}")
            question_history.append(question)
        else:
            final_outcome = "LOOP_COMPLETE"

    # Save metrics
    with open(task_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    # Analyze final state
    final_state = loop_states[-1] if loop_states else {"claims": {}}
    analysis = analyze_claimgraph(final_state, seed_question, loop_metrics)

    with open(task_dir / "claimgraph_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Write LLM-authored .md
    write_analysis_md(task_id, task_dir, seed_question, loop_states,
                      loop_metrics, analysis, final_outcome)

    print(f"\n  Task {task_id}: {final_outcome} | loops={len(loop_metrics)} "
          f"| sealed={analysis['total_sealed']}/{analysis['total_claims']}")

    return {
        "task_id": task_id,
        "outcome": final_outcome,
        "loops_completed": len(loop_metrics),
        "total_claims": analysis["total_claims"],
        "total_sealed": analysis["total_sealed"],
        "dominant_motif": analysis["dominant_motif"],
        "unexpected_claims_count": len(analysis["unexpected_claims"]),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all(tasks: list = None) -> None:
    _init_clients()
    APPENDIX_DIR.mkdir(parents=True, exist_ok=True)

    # Freeze inputs before any run
    hashes = hash_inputs()

    results = {}
    run_tasks = tasks or [1, 2]

    if 1 in run_tasks:
        task1_dir = APPENDIX_DIR / "task1_self_inquiry"
        results[1] = run_self_inquiry(1, M_SEED, task1_dir)

    if 2 in run_tasks:
        task2_dir = APPENDIX_DIR / "task2_research_agenda"
        results[2] = run_self_inquiry(2, R_SEED, task2_dir)

    # Summary
    with open(APPENDIX_DIR / "appendix_e_summary.json", "w") as f:
        json.dump({
            "label": "EXPLORATORY SELF-INQUIRY — not pre-registered, not confirmatory",
            "input_files_hashed": len(hashes),
            "tasks": results,
        }, f, indent=2)

    print("\nAppendix E complete.")
    print("REMINDER: Do not modify Paper 8 main text based on self-inquiry findings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, choices=[1, 2], default=None,
                        help="Run single task (default: both)")
    args = parser.parse_args()
    run_all(tasks=[args.task] if args.task else None)

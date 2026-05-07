"""
paper9/run_desi_consultation.py
Desi Consultation — Paper 9 Seed.

DES is asked to comment on the Paper 9 seed before the Design Memo is written.
DESI CONSULTATION — exploratory, not pre-registered, not confirmatory.

Usage:
    python paper9/run_desi_consultation.py
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.mol import (
    invoke_operator,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    extract_dominant_claim,
)
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    compute_metrics,
    check_failure,
    _claim_text,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    FALSIFIER_MODEL,
    FALSIFIER_PROVIDER,
)
import paper8.run_p8 as _p8

CONSULTATION_DIR = Path("paper9/desi_consultation")
SEED_FILE        = Path("DES_Paper9_Seed.md")
MAX_LOOPS        = 5
OPERATOR_LENS    = "recursive_modulation"
MAX_ITER         = 40

SEED = """A research system (Desi) is planning Paper 9.
The working hypothesis is:

operator_effectiveness = f(structural_operator, activation_frame, local_semantic_density)

Where local_semantic_density is defined as:
density(q, r) = count(claims with sqrt_JSD(pi(c), pi(q)) < r) / n_claims

The planned experiment is a 2x3 factorial design:
- density: low (formal/narrow domains) vs high (argumentative/broad)
- framing: persona / explicit operator / stripped context

Paper 9 does NOT introduce a new epistemic object class.
It tests whether semantic density functions as a conditioning field
over existing operator classes.

Questions for Desi:
1. What is the most likely failure mode of this experimental design?
2. What does Desi not yet understand about its own density-dependent behavior?
3. Is there a simpler operationalization of the hypothesis that would be more falsifiable?"""


def freeze_seed_hash() -> str:
    seed_bytes = SEED_FILE.read_bytes()
    seed_hash  = hashlib.sha256(seed_bytes).hexdigest()
    CONSULTATION_DIR.mkdir(parents=True, exist_ok=True)
    (CONSULTATION_DIR / "seed_hash.json").write_text(
        json.dumps({"seed_hash": seed_hash, "file": str(SEED_FILE)}, indent=2)
    )
    print(f"Seed hash: {seed_hash}")
    return seed_hash


def analyze_claimgraph(state: dict, loop_metrics: list) -> dict:
    claims  = state.get("claims", {})
    motif   = extract_dominant_motif(claims)
    tension = extract_core_tension(claims)
    invs    = extract_invariants(claims)
    traj    = classify_trajectories(claims)
    dom     = extract_dominant_claim(claims)

    seed_tokens = set(SEED.lower().split())
    unexpected  = []
    for cid, c in claims.items():
        text     = _claim_text(c)
        c_tokens = set(text.lower().split())
        overlap  = len(seed_tokens & c_tokens) / max(len(c_tokens), 1)
        if overlap < 0.10 and c.get("sealed"):
            unexpected.append({
                "cid": cid, "claim": text,
                "confidence": c.get("confidence", 0),
                "seed_overlap": round(overlap, 3),
            })
    unexpected.sort(key=lambda x: x["seed_overlap"])

    all_sealed = [
        {"cid": cid, "claim": _claim_text(c), "confidence": c.get("confidence", 0),
         "status": c.get("status"), "history": c.get("history", [])}
        for cid, c in claims.items() if c.get("sealed")
    ]

    return {
        "dominant_motif":   motif,
        "core_tension":     tension,
        "invariants":       invs,
        "trajectories":     traj,
        "dominant_claim":   dom,
        "unexpected_claims": unexpected[:5],
        "all_sealed_claims": all_sealed,
        "total_claims":     len(claims),
        "total_sealed":     len(all_sealed),
        "dup_trend":  [round(m.get("semantic_duplication_rate", 0), 3) for m in loop_metrics],
        "novel_trend": [m.get("novel_claims", 0) for m in loop_metrics],
    }


def write_consultation_md(
    task_dir: Path,
    loop_metrics: list,
    analysis: dict,
    final_outcome: str,
    seed_hash: str,
) -> None:
    claims_text = "\n".join(
        f"  [{c['cid']}] (conf={c['confidence']:.2f}, {c['status']}) {c['claim']}"
        for c in analysis["all_sealed_claims"]
    )

    unexpected_text = "\n".join(
        f"  [{c['cid']}] seed_overlap={c['seed_overlap']}: {c['claim']}"
        for c in analysis["unexpected_claims"]
    ) or "  (none detected)"

    prompt = f"""You are writing the output of a Desi Consultation on the Paper 9 seed.
DESI CONSULTATION — exploratory, not pre-registered, not confirmatory.
Do NOT invent new hypotheses. Report only what is in the ClaimGraph.
Contradictions must be preserved, not resolved.

SEED (verbatim):
{SEED}

RAW CLAIMGRAPH (all sealed claims, unfiltered):
{claims_text}

DOMINANT MOTIF: {analysis['dominant_motif']['subject']} / {analysis['dominant_motif']['predicate']}
CORE TENSION: {analysis['core_tension']}
DOMINANT CLAIM: {analysis['dominant_claim']['claim']} (conf={analysis['dominant_claim']['confidence']:.2f})

INVARIANTS (high confidence, stable):
{chr(10).join('  - ' + i['claim'] for i in analysis['invariants']) or '  (none)'}

UNEXPECTED CLAIMS (low seed overlap, sealed):
{unexpected_text}

DUPLICATION TREND (per loop): {analysis['dup_trend']}
NOVELTY TREND (per loop): {analysis['novel_trend']}

FINAL OUTCOME: {final_outcome} after {len(loop_metrics)} loops.

Write the consultation report in this exact format:

---

# DESI CONSULTATION — Paper 9 Seed
**Label: DESI CONSULTATION — exploratory, not pre-registered, not confirmatory.**
**Seed hash: {seed_hash}**

## Seed Question (verbatim)
[reproduce SEED verbatim]

## Dominant Motifs
[list the 2-3 most frequent subject/predicate pairs from the ClaimGraph]

## ClaimGraph Summary
[list ALL sealed claims verbatim from the raw dump above, numbered]

## Desi's Answers to the Three Seed Questions

### Q1: Most likely failure mode of this experimental design?
[answer from claims; if no claim addresses this, state explicitly]

### Q2: What does Desi not yet understand about its own density-dependent behavior?
[answer from claims; if no claim addresses this, state explicitly]

### Q3: Is there a simpler operationalization that would be more falsifiable?
[answer from claims; if no claim addresses this, state explicitly]

## Attractor Structure
[describe convergence patterns; note if SPL unavailable]

## Unexpected Claims
[list all claims with low seed-overlap, exactly as provided]
[If none: state explicitly]

## Negative Findings
- Expected motifs not found:
- Contradictions found: [list or "none"]
- Claims addressing all three questions: [yes / partial / no]
- Overall consultation yield: [high / medium / low / null]

## Raw Notes
[anything else in the ClaimGraph not fitting above categories]
"""

    md_text = call_llm(prompt, max_tokens=2500, temperature=0.3)

    header = (
        "<!-- paper9/desi_consultation -->\n"
        "<!-- DESI CONSULTATION — not pre-registered, not confirmatory -->\n"
        f"<!-- Seed hash: {seed_hash} -->\n\n"
    )

    (task_dir / "desi_consultation_paper9.md").write_text(header + md_text + "\n")
    print(f"  Written → {task_dir / 'desi_consultation_paper9.md'}")


def run_consultation() -> dict:
    _init_clients()
    CONSULTATION_DIR.mkdir(parents=True, exist_ok=True)

    seed_hash = freeze_seed_hash()

    question         = SEED
    question_history = [SEED]
    loop_metrics     = []
    all_prior_texts  = []
    loop_states      = []
    final_outcome    = "MAX_LOOPS_REACHED"

    print(f"\n{'='*65}")
    print("  Desi Consultation — Paper 9 Seed")
    print(f"  Seed: {SEED[:80]}")
    print(f"{'='*65}")

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    for loop in range(MAX_LOOPS):
        loop_file = CONSULTATION_DIR / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = SEED
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
        state["seed_question"] = SEED

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

        if loop < MAX_LOOPS - 1:
            op_result = invoke_operator(
                OPERATOR_LENS, state, SEED, question_history,
                call_llm_fn=call_llm,
            )
            print(f"  [mozart lens] admitted={op_result['admitted']} "
                  f"eni={op_result.get('eni_composite', 0):.3f} | "
                  f"{op_result['question'][:60]}")
            if op_result["admitted"]:
                question = op_result["question"]
            else:
                claims  = state.get("claims", {})
                motif   = extract_dominant_motif(claims)
                tension = extract_core_tension(claims)
                fallback = (
                    f"Given dominant motif '{motif['subject']} {motif['predicate']}' "
                    f"and core tension '{tension}', generate one research question "
                    f"that explores an adjacent conceptual register. "
                    f"Return ONLY: one question as a single sentence."
                )
                question = call_llm(fallback, max_tokens=100)
                print(f"  [mozart lens] fallback Q: {question[:60]}")
            question_history.append(question)
        else:
            final_outcome = "LOOP_COMPLETE"

    with open(CONSULTATION_DIR / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    final_state = loop_states[-1] if loop_states else {"claims": {}}
    analysis    = analyze_claimgraph(final_state, loop_metrics)

    with open(CONSULTATION_DIR / "claimgraph_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    write_consultation_md(CONSULTATION_DIR, loop_metrics, analysis, final_outcome, seed_hash)

    print(f"\n  Desi Consultation: {final_outcome} | loops={len(loop_metrics)} "
          f"| sealed={analysis['total_sealed']}/{analysis['total_claims']}")

    return {
        "outcome":       final_outcome,
        "loops":         len(loop_metrics),
        "total_claims":  analysis["total_claims"],
        "total_sealed":  analysis["total_sealed"],
        "dominant_motif": analysis["dominant_motif"],
        "unexpected_claims_count": len(analysis["unexpected_claims"]),
    }


if __name__ == "__main__":
    result = run_consultation()
    print("\nDesi Consultation complete.")
    print("REMINDER: Do not modify DES_Paper9_Seed.md based on consultation findings.")
    print(json.dumps(result, indent=2))

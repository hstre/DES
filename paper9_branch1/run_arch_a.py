"""
paper9_branch1/run_arch_a.py
Architecture A — Merged Branch.

Parallel operator expansion: admitted candidates → structured multi-seed
prompt → single DES run. arch_a_fallback=True if ≤1 admitted candidate.

H1: EME(arch_a) > EME(arm_b_baseline) × 1.2
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from paper8.mol import (
    select_operator,
    extract_dominant_motif,
    extract_core_tension,
)
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    compute_metrics,
    check_failure,
    select_next_question,
    _claim_text,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    FALSIFIER_MODEL,
    FALSIFIER_PROVIDER,
)
import paper8.run_p8 as _p8
from paper8.eme import compute_eme
from paper7.en import early_saturation_detected
from paper9_branch1.parallel_fire import (
    parallel_fire,
    admitted_candidates,
    format_multiseed_prompt,
)

RESULTS_DIR        = Path("paper9_branch1/batch_results_arch_a")
MAX_LOOPS          = 5
MAX_ITER_PER_RUN   = 40
MAX_PARALLEL_EVENTS = 2
ARM_B_EME_BASELINE = 2.8195
H1_MULTIPLIER      = 1.2

DOMAINS = {
    "M01": {
        "seed": (
            "Investigate the long-term behavior of the recursive map T(n): "
            "if n mod 3 == 0 then T(n) = n/3, "
            "if n mod 3 == 1 then T(n) = 4n+2, "
            "if n mod 3 == 2 then T(n) = 2n-1. "
            "Identify cycles, divergence patterns, invariants, and plausible conjectures."
        ),
        "type": "formal_mathematics",
    },
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "type": "empirical_argumentative",
    },
}

SEEDS = [101, 202, 303]


def run_arch_a(domain_id: str, seed_n: int) -> dict:
    run_dir = RESULTS_DIR / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "outcome.json"

    if result_file.exists():
        print(f"  [skip] {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    domain        = DOMAINS[domain_id]
    seed_question = domain["seed"]
    domain_type   = domain["type"]

    print(f"\n{'='*65}")
    print(f"  {domain_id} [Arch A | seed{seed_n}] | {domain_type}")
    print(f"  Seed Q: {seed_question[:70]}")
    print(f"{'='*65}")

    import random
    random.seed(seed_n)

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    question          = seed_question
    question_history  = [seed_question]
    loop_metrics      = []
    all_prior_texts   = []
    operator_log      = []
    parallel_events   = 0
    final_state       = None

    for loop in range(MAX_LOOPS):
        loop_file = run_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = seed_question
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            next_q = select_next_question(state, question_history)
            if next_q != "LOOP_COMPLETE":
                question_history.append(next_q)
            question = next_q if next_q != "LOOP_COMPLETE" else question
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        try:
            _p8.des_module.run_des(
                research_question=question,
                max_iterations=MAX_ITER_PER_RUN,
                anti_delphi=True,
                builder_model=BUILDER_MODEL,
                builder_provider=BUILDER_PROVIDER,
                falsifier_model=FALSIFIER_MODEL,
                falsifier_provider=FALSIFIER_PROVIDER,
            )
        except Exception as e:
            print(f"  ERROR in run_des: {e}")
            break

        if not STATE_FILE.exists():
            print("  ERROR: des_state.json not found")
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        state["seed_question"] = seed_question

        with open(loop_file, "w") as f:
            json.dump(state, f)
        final_state = state

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        failure = check_failure(metrics, loop_metrics, [])
        if failure:
            _save(run_dir, domain_id, seed_n, failure, loop_metrics,
                  operator_log, final_state)
            return _load(result_file)

        # Parallel operator trigger
        if (early_saturation_detected(loop_metrics[:-1], metrics)
                and parallel_events < MAX_PARALLEL_EVENTS):

            parallel_events += 1
            print(f"  [parallel_fire] event {parallel_events}")

            candidates = parallel_fire(state, seed_question, question_history, call_llm)
            admitted   = admitted_candidates(candidates)

            op_event = {
                "loop": loop,
                "parallel_event": parallel_events,
                "candidates": [
                    {k: v for k, v in c.items() if k != "context"}
                    for c in candidates
                ],
                "n_admitted": len(admitted),
                "arch_a_fallback": len(admitted) <= 1,
            }
            operator_log.append(op_event)

            if len(admitted) >= 2:
                multi_q = format_multiseed_prompt(admitted)
                question = multi_q
                question_history.append(question)
                print(f"  [arch_a] multi-seed ({len(admitted)} ops): {multi_q[:80]}")
            elif len(admitted) == 1:
                question = admitted[0]["question"]
                question_history.append(question)
                print(f"  [arch_a] fallback single: {question[:70]}")
            else:
                print(f"  [parallel_fire] all rejected — continuing default")

            continue

        next_q = select_next_question(state, question_history)
        if next_q == "LOOP_COMPLETE":
            _save(run_dir, domain_id, seed_n, "LOOP_COMPLETE", loop_metrics,
                  operator_log, final_state)
            return _load(result_file)

        question = next_q
        question_history.append(question)

    _save(run_dir, domain_id, seed_n, "MAX_LOOPS_REACHED", loop_metrics,
          operator_log, final_state)
    return _load(result_file)


def _save(run_dir: Path, domain_id: str, seed_n: int,
          outcome: str, loop_metrics: list,
          operator_log: list, final_state: dict | None) -> None:
    data = {
        "domain_id":       domain_id,
        "seed":            seed_n,
        "arch":            "A",
        "outcome":         outcome,
        "loops_completed": len(loop_metrics),
        "operator_log":    operator_log,
        "final_claims":    final_state.get("claims", {}) if final_state else {},
    }
    with open(run_dir / "outcome.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    print(f"  {domain_id}/arch_a/seed{seed_n}: {outcome} | loops={len(loop_metrics)}")


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ── EME + verdicts ─────────────────────────────────────────────────────────────

def compute_arch_a_eme(results: list) -> dict:
    """Compute EME from Arch A main run results."""
    return compute_eme(results)


def h1_verdict(eme_result: dict) -> str:
    score = eme_result.get("eme_score")
    if score is None:
        return "H1_INDETERMINATE"
    threshold = ARM_B_EME_BASELINE * H1_MULTIPLIER
    return "H1_CONFIRMED" if score > threshold else "H1_REJECTED"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    _init_clients()
    all_results = []
    for domain_id in ("M01", "N03"):
        for seed_n in SEEDS:
            r = run_arch_a(domain_id, seed_n)
            all_results.append(r)

    eme = compute_arch_a_eme(all_results)
    h1  = h1_verdict(eme)

    summary = {
        "arch":           "A",
        "eme":            eme,
        "h1_verdict":     h1,
        "arm_b_baseline": ARM_B_EME_BASELINE,
        "h1_threshold":   round(ARM_B_EME_BASELINE * H1_MULTIPLIER, 4),
        "domains":        list(DOMAINS.keys()),
        "seeds":          SEEDS,
        "n_runs":         len(all_results),
    }

    out = RESULTS_DIR / "arch_a_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[arch_a] EME={eme.get('eme_score')} | {h1}")
    print(f"[arch_a] summary → {out}")
    return summary


if __name__ == "__main__":
    main()

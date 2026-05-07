"""
paper9_branch1/run_arch_b.py
Architecture B — Preserved Branches.

Parallel operator expansion: each admitted candidate → independent DES branch.
Parent state written to des_state.json before EACH branch (prevents sequential
inheritance). Up to MAX_BRANCHES=3 branches per parallel event.

H2: EME(arch_b) > EME(arch_a)
H3: EME/token(arch_b) > EME/token(single arm_b)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from paper8.mol import select_operator
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
)

RESULTS_DIR         = Path("paper9_branch1/batch_results_arch_b")
MAX_LOOPS           = 5
MAX_ITER_PER_RUN    = 40
MAX_PARALLEL_EVENTS = 2
MAX_BRANCHES        = 3

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


def run_single_branch(
    branch_dir: Path,
    parent_state: dict,
    candidate_question: str,
    operator_id: str,
    seed_question: str,
) -> dict:
    """
    Run one DES branch from parent_state using candidate_question.
    Writes parent_state to des_state.json before run_des to prevent
    sequential state inheritance across branches.
    """
    branch_dir.mkdir(parents=True, exist_ok=True)
    result_file = branch_dir / "branch_outcome.json"

    if result_file.exists():
        print(f"    [skip] branch {branch_dir.name}")
        with open(result_file) as f:
            return json.load(f)

    # Reset des_state.json to parent state — prevents inheritance from prior branch
    with open(STATE_FILE, "w") as f:
        json.dump(parent_state, f)

    print(f"    [branch:{operator_id}] Q: {candidate_question[:70]}")

    try:
        _p8.des_module.run_des(
            research_question=candidate_question,
            max_iterations=MAX_ITER_PER_RUN,
            anti_delphi=True,
            builder_model=BUILDER_MODEL,
            builder_provider=BUILDER_PROVIDER,
            falsifier_model=FALSIFIER_MODEL,
            falsifier_provider=FALSIFIER_PROVIDER,
        )
    except Exception as e:
        print(f"    ERROR in branch run_des: {e}")
        result = {
            "operator_id":  operator_id,
            "question":     candidate_question[:120],
            "outcome":      f"error: {e}",
            "final_claims": {},
        }
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        return result

    if not STATE_FILE.exists():
        result = {
            "operator_id":  operator_id,
            "question":     candidate_question[:120],
            "outcome":      "state_missing",
            "final_claims": {},
        }
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        return result

    with open(STATE_FILE) as f:
        branch_state = json.load(f)

    with open(branch_dir / "branch_state.json", "w") as f:
        json.dump(branch_state, f)

    result = {
        "operator_id":  operator_id,
        "question":     candidate_question[:120],
        "outcome":      "BRANCH_COMPLETE",
        "final_claims": branch_state.get("claims", {}),
        "n_sealed":     sum(1 for c in branch_state.get("claims", {}).values()
                           if c.get("sealed")),
    }
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    return result


def run_arch_b(domain_id: str, seed_n: int) -> dict:
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
    print(f"  {domain_id} [Arch B | seed{seed_n}] | {domain_type}")
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
    branch_results    = []
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
                  operator_log, branch_results, final_state)
            return _load(result_file)

        # Parallel operator trigger
        if (early_saturation_detected(loop_metrics[:-1], metrics)
                and parallel_events < MAX_PARALLEL_EVENTS):

            parallel_events += 1
            parent_state = json.loads(json.dumps(state))  # deep copy

            print(f"  [parallel_fire] event {parallel_events}")
            candidates = parallel_fire(state, seed_question, question_history, call_llm)
            admitted   = admitted_candidates(candidates)[:MAX_BRANCHES]

            op_event = {
                "loop":           loop,
                "parallel_event": parallel_events,
                "n_candidates":   len(candidates),
                "n_admitted":     len(admitted),
                "candidate_ops":  [c.get("operator_id") for c in admitted],
            }
            operator_log.append(op_event)

            for i, cand in enumerate(admitted):
                branch_dir = run_dir / f"branch_ev{parallel_events}_op{i}"
                br = run_single_branch(
                    branch_dir,
                    parent_state,
                    cand["question"],
                    cand["operator_id"],
                    seed_question,
                )
                branch_results.append(br)
                # Restore main-thread state so next loop starts from parent
                with open(STATE_FILE, "w") as f:
                    json.dump(parent_state, f)

            if admitted:
                question = admitted[0]["question"]
                question_history.append(question)
                print(f"  [arch_b] main thread continues: {question[:70]}")
            continue

        next_q = select_next_question(state, question_history)
        if next_q == "LOOP_COMPLETE":
            _save(run_dir, domain_id, seed_n, "LOOP_COMPLETE", loop_metrics,
                  operator_log, branch_results, final_state)
            return _load(result_file)

        question = next_q
        question_history.append(question)

    _save(run_dir, domain_id, seed_n, "MAX_LOOPS_REACHED", loop_metrics,
          operator_log, branch_results, final_state)
    return _load(result_file)


def _save(run_dir: Path, domain_id: str, seed_n: int,
          outcome: str, loop_metrics: list, operator_log: list,
          branch_results: list, final_state: dict | None) -> None:
    data = {
        "domain_id":       domain_id,
        "seed":            seed_n,
        "arch":            "B",
        "outcome":         outcome,
        "loops_completed": len(loop_metrics),
        "operator_log":    operator_log,
        "branch_results":  branch_results,
        "n_branches":      len(branch_results),
        "final_claims":    final_state.get("claims", {}) if final_state else {},
    }
    with open(run_dir / "outcome.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    print(f"  {domain_id}/arch_b/seed{seed_n}: {outcome} | loops={len(loop_metrics)} "
          f"| branches={len(branch_results)}")


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ── EME computation (main + all branches) ────────────────────────────────────

def build_eme_input(results: list) -> list:
    """
    Combine main run final_claims with all branch final_claims.
    EME requires list of dicts with 'final_claims' key.
    """
    eme_items = []
    for r in results:
        eme_items.append({"final_claims": r.get("final_claims", {})})
        for br in r.get("branch_results", []):
            eme_items.append({"final_claims": br.get("final_claims", {})})
    return eme_items


def compute_arch_b_eme(results: list) -> dict:
    return compute_eme(build_eme_input(results))


# ── Hypothesis verdicts ───────────────────────────────────────────────────────

def h2_verdict(eme_b: dict, eme_a: dict) -> str:
    sb = eme_b.get("eme_score")
    sa = eme_a.get("eme_score")
    if sb is None or sa is None:
        return "H2_INDETERMINATE"
    return "H2_CONFIRMED" if sb > sa else "H2_REJECTED"


def h3_verdict(eme_b: dict, eme_a: dict, results_b: list, results_a: list) -> str:
    """
    H3: EME/loops(arch_b) > EME/loops(arch_a).
    Uses loops_completed as proxy for token count.
    """
    sb = eme_b.get("eme_score")
    sa = eme_a.get("eme_score")
    if sb is None or sa is None:
        return "H3_INDETERMINATE"

    loops_b = sum(r.get("loops_completed", 0) for r in results_b)
    loops_a = sum(r.get("loops_completed", 0) for r in results_a)

    # Add branch loops to Arch B total
    for r in results_b:
        loops_b += len(r.get("branch_results", []))  # 1 loop per branch

    if loops_a == 0 or loops_b == 0:
        return "H3_INDETERMINATE"

    eme_per_loop_b = sb / loops_b
    eme_per_loop_a = sa / loops_a
    return "H3_CONFIRMED" if eme_per_loop_b > eme_per_loop_a else "H3_REJECTED"


# ── Main ──────────────────────────────────────────────────────────────────────

def main(arch_a_results_dir: Path | None = None):
    _init_clients()
    all_results = []
    for domain_id in ("M01", "N03"):
        for seed_n in SEEDS:
            r = run_arch_b(domain_id, seed_n)
            all_results.append(r)

    eme_b = compute_arch_b_eme(all_results)

    # Load Arch A EME for H2/H3 comparison
    a_summary_path = Path("paper9_branch1/batch_results_arch_a/arch_a_summary.json")
    if a_summary_path.exists():
        with open(a_summary_path) as f:
            a_summary = json.load(f)
        eme_a = a_summary.get("eme", {})

        # Load Arch A outcomes for H3 loop count
        results_a = []
        for domain_id in ("M01", "N03"):
            for seed_n in SEEDS:
                p = Path(f"paper9_branch1/batch_results_arch_a/{domain_id}_seed{seed_n}/outcome.json")
                if p.exists():
                    with open(p) as f:
                        results_a.append(json.load(f))
    else:
        eme_a    = {}
        results_a = []

    h2 = h2_verdict(eme_b, eme_a)
    h3 = h3_verdict(eme_b, eme_a, all_results, results_a)

    summary = {
        "arch":        "B",
        "eme":         eme_b,
        "h2_verdict":  h2,
        "h3_verdict":  h3,
        "eme_arch_a":  eme_a,
        "domains":     list(DOMAINS.keys()),
        "seeds":       SEEDS,
        "n_runs":      len(all_results),
        "n_branches":  sum(r.get("n_branches", 0) for r in all_results),
    }

    out = RESULTS_DIR / "arch_b_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[arch_b] EME={eme_b.get('eme_score')} | {h2} | {h3}")
    print(f"[arch_b] summary → {out}")
    return summary


if __name__ == "__main__":
    main()

"""
paper9_branch2/run_condition.py
Parameterised runner for B2 (merge_after=2) and B4 (merge_after=4).

Each branch runs merge_after outer loops independently from parent_state,
then the first two admitted mature branches are merged.  At least 1
post-merge DES loop runs on the merged state for H3 measurement.
"""

import json
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

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
from paper9_branch1.parallel_fire import parallel_fire, admitted_candidates
from paper9_branch2.merge import merge_branch_states, compute_h3

MAX_LOOPS           = 5
MAX_ITER_PER_RUN    = 40
MAX_PARALLEL_EVENTS = 2
MAX_BRANCHES        = 3
POST_MERGE_LOOPS    = 1

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


def run_branch_extended(
    branch_dir: Path,
    parent_state: dict,
    candidate_question: str,
    operator_id: str,
    seed_question: str,
    n_loops: int,
) -> dict:
    """
    Run branch for n_loops outer iterations from parent_state.
    Parent state written to des_state.json before loop 0 — prevents
    inheritance from main thread or prior branch.
    """
    branch_dir.mkdir(parents=True, exist_ok=True)
    result_file = branch_dir / "branch_outcome.json"

    if result_file.exists():
        with open(result_file) as f:
            return json.load(f)

    with open(STATE_FILE, "w") as f:
        json.dump(parent_state, f)

    question         = candidate_question
    question_history = [candidate_question]
    loop_metrics     = []
    all_prior_texts  = []
    final_state      = None

    print(f"    [branch:{operator_id}] n_loops={n_loops} Q: {candidate_question[:60]}")

    for loop in range(n_loops):
        loop_file = branch_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            with open(loop_file) as f:
                state = json.load(f)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            nq = select_next_question(state, question_history)
            if nq != "LOOP_COMPLETE":
                question_history.append(nq)
            question    = nq if nq != "LOOP_COMPLETE" else question
            final_state = state
            continue

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
            print(f"    ERROR in branch run_des loop {loop}: {e}")
            break

        if not STATE_FILE.exists():
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        with open(loop_file, "w") as f:
            json.dump(state, f)
        final_state = state

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        if check_failure(metrics, loop_metrics, []):
            break

        nq = select_next_question(state, question_history)
        if nq == "LOOP_COMPLETE":
            break
        question = nq
        question_history.append(question)

    with open(branch_dir / "branch_state.json", "w") as f:
        json.dump(final_state or {}, f)

    result = {
        "branch_id":       branch_dir.name,
        "_branch_dir":     str(branch_dir),
        "operator_id":     operator_id,
        "question":        candidate_question[:120],
        "loops_completed": len(loop_metrics),
        "outcome":         "BRANCH_LOOPS_DONE",
        "final_claims":    final_state.get("claims", {}) if final_state else {},
        "n_sealed":        sum(1 for c in (final_state or {}).get("claims", {}).values()
                               if c.get("sealed")),
    }
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    return result


def run_post_merge_loop(
    post_merge_dir: Path,
    merged_state: dict,
    seed_question: str,
    n_loops: int = POST_MERGE_LOOPS,
) -> dict:
    """
    Run DES on merged ClaimGraph state; measure new_cluster_rate for H3.
    pre_merge_claims = union of two branch states (the merged_state claims).
    post_merge_claims = after at least 1 DES loop on merged context.
    """
    post_merge_dir.mkdir(parents=True, exist_ok=True)
    result_file = post_merge_dir / "post_merge_outcome.json"

    if result_file.exists():
        with open(result_file) as f:
            return json.load(f)

    pre_merge_claims = dict(merged_state.get("claims", {}))

    with open(STATE_FILE, "w") as f:
        json.dump(merged_state, f)

    question    = seed_question
    final_state = merged_state

    for loop in range(n_loops):
        loop_file = post_merge_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            with open(loop_file) as f:
                final_state = json.load(f)
            with open(STATE_FILE, "w") as f:
                json.dump(final_state, f)
            continue

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
            print(f"    ERROR in post-merge run_des loop {loop}: {e}")
            break

        if not STATE_FILE.exists():
            break

        with open(STATE_FILE) as f:
            final_state = json.load(f)
        with open(loop_file, "w") as f:
            json.dump(final_state, f)

    post_merge_claims = final_state.get("claims", {})
    h3 = compute_h3(pre_merge_claims, post_merge_claims)

    result = {
        "merged_from":  merged_state.get("_merged_from", []),
        "h3_metrics":   h3,
        "final_claims": post_merge_claims,
    }
    with open(post_merge_dir / "post_merge_state.json", "w") as f:
        json.dump(final_state, f)
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    return result


def run_condition_run(
    domain_id: str,
    seed_n: int,
    merge_after: int | None,
    results_dir: Path,
) -> dict:
    run_dir     = results_dir / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "outcome.json"

    if result_file.exists():
        print(f"  [skip] {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    domain        = DOMAINS[domain_id]
    seed_question = domain["seed"]
    label         = f"B{merge_after}" if merge_after is not None else "B_inf"

    print(f"\n{'='*65}")
    print(f"  {domain_id} [{label} | seed{seed_n}] | {domain['type']}")
    print(f"  Seed Q: {seed_question[:70]}")
    print(f"{'='*65}")

    random.seed(seed_n)

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    question           = seed_question
    question_history   = [seed_question]
    loop_metrics       = []
    all_prior_texts    = []
    operator_log       = []
    branch_results     = []
    post_merge_results = []
    parallel_events    = 0
    final_state        = None

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
            nq = select_next_question(state, question_history)
            if nq != "LOOP_COMPLETE":
                question_history.append(nq)
            question = nq if nq != "LOOP_COMPLETE" else question
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
            _save(run_dir, domain_id, seed_n, merge_after, failure,
                  loop_metrics, operator_log, branch_results, post_merge_results, final_state)
            return _load(result_file)

        # Parallel operator trigger
        if (early_saturation_detected(loop_metrics[:-1], metrics)
                and parallel_events < MAX_PARALLEL_EVENTS):

            parallel_events += 1
            parent_state = json.loads(json.dumps(state))

            print(f"  [parallel_fire] event {parallel_events}")
            candidates = parallel_fire(state, seed_question, question_history, call_llm)
            admitted   = admitted_candidates(candidates)[:MAX_BRANCHES]

            op_event = {
                "loop":           loop,
                "parallel_event": parallel_events,
                "n_candidates":   len(candidates),
                "n_admitted":     len(admitted),
                "candidate_ops":  [c.get("operator_id") for c in admitted],
                "branch_n_loops": merge_after,
            }
            operator_log.append(op_event)

            # Run each branch for merge_after loops
            current_event_branches = []
            for i, cand in enumerate(admitted):
                branch_dir = run_dir / f"branch_ev{parallel_events}_op{i}"
                br = run_branch_extended(
                    branch_dir,
                    parent_state,
                    cand["question"],
                    cand["operator_id"],
                    seed_question,
                    n_loops=merge_after if merge_after is not None else MAX_LOOPS,
                )
                current_event_branches.append(br)
                branch_results.append(br)
                # restore parent_state for next branch
                with open(STATE_FILE, "w") as f:
                    json.dump(parent_state, f)

            # Attempt merge (B2/B4 only, not B_inf)
            if merge_after is not None and current_event_branches:
                merged_state = merge_branch_states(current_event_branches, merge_after)
                if merged_state:
                    print(f"  [merge] ev{parallel_events}: "
                          f"merging {merged_state.get('_merged_from')}")
                    post_merge_dir = run_dir / f"post_merge_ev{parallel_events}"
                    pm = run_post_merge_loop(post_merge_dir, merged_state, seed_question)
                    pm["parallel_event"] = parallel_events
                    post_merge_results.append(pm)
                    h3v = pm.get("h3_metrics", {}).get("h3_verdict", "?")
                    ncr = pm.get("h3_metrics", {}).get("new_cluster_rate", "?")
                    print(f"  [merge] {h3v} | new_cluster_rate={ncr}")
                else:
                    print(f"  [merge] ev{parallel_events}: not enough mature branches "
                          f"(need loops_completed>={merge_after})")

            # Main thread continues from parent state
            with open(STATE_FILE, "w") as f:
                json.dump(parent_state, f)

            if admitted:
                question = admitted[0]["question"]
                question_history.append(question)
                print(f"  [{label}] main thread continues: {question[:70]}")
            continue

        nq = select_next_question(state, question_history)
        if nq == "LOOP_COMPLETE":
            _save(run_dir, domain_id, seed_n, merge_after, "LOOP_COMPLETE",
                  loop_metrics, operator_log, branch_results, post_merge_results, final_state)
            return _load(result_file)

        question = nq
        question_history.append(question)

    _save(run_dir, domain_id, seed_n, merge_after, "MAX_LOOPS_REACHED",
          loop_metrics, operator_log, branch_results, post_merge_results, final_state)
    return _load(result_file)


def _save(
    run_dir: Path, domain_id: str, seed_n: int, merge_after: int | None,
    outcome: str, loop_metrics: list, operator_log: list,
    branch_results: list, post_merge_results: list, final_state: dict | None,
) -> None:
    data = {
        "domain_id":           domain_id,
        "seed":                seed_n,
        "merge_after":         merge_after,
        "outcome":             outcome,
        "loops_completed":     len(loop_metrics),
        "operator_log":        operator_log,
        "branch_results":      branch_results,
        "n_branches":          len(branch_results),
        "post_merge_results":  post_merge_results,
        "n_post_merges":       len(post_merge_results),
        "final_claims":        final_state.get("claims", {}) if final_state else {},
    }
    with open(run_dir / "outcome.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    label = f"B{merge_after}" if merge_after is not None else "B_inf"
    print(f"  {domain_id}/{label}/seed{seed_n}: {outcome} | "
          f"loops={len(loop_metrics)} | branches={len(branch_results)} | "
          f"post_merges={len(post_merge_results)}")


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def build_condition_eme_input(results: list) -> list:
    """Combine main + branch + post-merge claims for overall EME."""
    items = []
    for r in results:
        items.append({"final_claims": r.get("final_claims", {})})
        for br in r.get("branch_results", []):
            items.append({"final_claims": br.get("final_claims", {})})
        for pm in r.get("post_merge_results", []):
            items.append({"final_claims": pm.get("final_claims", {})})
    return items


def main_condition(merge_after: int | None, results_dir: Path) -> dict:
    """Run all domains/seeds for one merge_after condition. Returns summary dict."""
    _init_clients()
    results_dir.mkdir(parents=True, exist_ok=True)
    all_results = []
    for domain_id in ("M01", "N03"):
        for seed_n in SEEDS:
            r = run_condition_run(domain_id, seed_n, merge_after, results_dir)
            all_results.append(r)

    eme = compute_eme(build_condition_eme_input(all_results))

    # Aggregate H3 metrics across all post-merge events
    all_h3 = []
    for r in all_results:
        for pm in r.get("post_merge_results", []):
            h3m = pm.get("h3_metrics")
            if h3m:
                all_h3.append(h3m)

    h3_verdict  = "H3_NOT_APPLICABLE"
    h3_avg_rate = None
    if all_h3:
        rates       = [m.get("new_cluster_rate", 0) for m in all_h3]
        h3_avg_rate = round(sum(rates) / len(rates), 4)
        h3_verdict  = "H3_CONFIRMED" if h3_avg_rate > 0 else "H3_REJECTED"

    label   = f"B{merge_after}" if merge_after is not None else "B_inf"
    summary = {
        "merge_after":    merge_after,
        "eme":            eme,
        "h3_verdict":     h3_verdict,
        "h3_avg_rate":    h3_avg_rate,
        "h3_events":      all_h3,
        "n_runs":         len(all_results),
        "n_branches":     sum(r.get("n_branches", 0) for r in all_results),
        "n_post_merges":  sum(r.get("n_post_merges", 0) for r in all_results),
    }

    out = results_dir / "condition_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[{label}] EME={eme.get('eme_score')} | {h3_verdict} "
          f"(avg new_cluster_rate={h3_avg_rate})")
    print(f"[{label}] summary → {out}")
    return summary

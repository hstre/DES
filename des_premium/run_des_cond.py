"""
des_premium/run_des_cond.py
DES runner parameterised by model config (cheap or premium).
Same multi-loop Anti-Delphi architecture as Papers 4-8.
"""

import json
import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from paper8.run_p8 import (
    _init_clients,
    compute_metrics,
    check_failure,
    select_next_question,
    _claim_text,
    STATE_FILE,
    detect_false_proofs_m01,
)
import paper8.run_p8 as _p8

from des_premium.config import DOMAINS, SEEDS

MAX_LOOPS        = 50
MAX_ITER_PER_RUN = 40


def run_des_condition(
    domain_id: str,
    seed_n:    int,
    config:    dict,
    results_dir: Path,
) -> dict:
    """
    Run DES for one domain/seed/config.
    Structure mirrors Paper 4/8 multi-loop outer loop.
    """
    run_dir     = results_dir / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "outcome.json"

    if result_file.exists():
        print(f"  [skip] {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    seed_question = DOMAINS[domain_id]
    tier          = config["tier"]

    print(f"\n{'='*65}")
    print(f"  {domain_id} [DES-{tier} | seed{seed_n}]")
    print(f"  builder={config['builder_model']} falsifier={config['falsifier_model']}")
    print(f"  Q: {seed_question[:70]}")
    print(f"{'='*65}")

    random.seed(seed_n)
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    question         = seed_question
    question_history = [seed_question]
    loop_metrics     = []
    all_prior_texts  = []
    final_state      = None
    t_start          = time.time()

    for loop in range(MAX_LOOPS):
        loop_file = run_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            with open(loop_file) as f:
                state = json.load(f)
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
                builder_model=config["builder_model"],
                builder_provider=config["builder_provider"],
                falsifier_model=config["falsifier_model"],
                falsifier_provider=config["falsifier_provider"],
            )
        except Exception as e:
            print(f"  ERROR in run_des: {e}")
            break

        if not STATE_FILE.exists():
            print("  ERROR: des_state.json not found")
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        with open(loop_file, "w") as f:
            json.dump(state, f)
        final_state = state

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        failure = check_failure(metrics, loop_metrics, [])
        if failure:
            _save(run_dir, domain_id, seed_n, config, failure,
                  loop_metrics, final_state, t_start)
            return _load(result_file)

        nq = select_next_question(state, question_history)
        if nq == "LOOP_COMPLETE":
            _save(run_dir, domain_id, seed_n, config, "LOOP_COMPLETE",
                  loop_metrics, final_state, t_start)
            return _load(result_file)

        question = nq
        question_history.append(question)

    _save(run_dir, domain_id, seed_n, config, "MAX_LOOPS_REACHED",
          loop_metrics, final_state, t_start)
    return _load(result_file)


def _save(
    run_dir:      Path,
    domain_id:    str,
    seed_n:       int,
    config:       dict,
    outcome:      str,
    loop_metrics: list,
    final_state:  dict | None,
    t_start:      float,
) -> None:
    fp_info = None
    if domain_id == "M01" and final_state:
        fp_info = detect_false_proofs_m01(final_state)

    elapsed = round(time.time() - t_start, 1)

    dup_rates   = [m["semantic_duplication_rate"] for m in loop_metrics]
    novel_vals  = [m["novel_claims"] for m in loop_metrics]
    total_vals  = [m["total_claims"]  for m in loop_metrics]

    data = {
        "domain_id":       domain_id,
        "seed":            seed_n,
        "config":          {k: v for k, v in config.items() if k != "note"},
        "outcome":         outcome,
        "loops_completed": len(loop_metrics),
        "elapsed_seconds": elapsed,
        "false_proof_info": fp_info,
        "false_proof_detected": fp_info["false_proof_detected"] if fp_info else None,
        "final_claims":    final_state.get("claims", {}) if final_state else {},
        "semantic_duplication_rate_mean": round(sum(dup_rates) / len(dup_rates), 4) if dup_rates else None,
        "novel_claims_mean":              round(sum(novel_vals) / len(novel_vals), 2) if novel_vals else None,
        "total_claims_final":             total_vals[-1] if total_vals else None,
        # Token cost: rough proxy (no direct DES instrumentation)
        "token_cost_proxy": len(loop_metrics) * MAX_ITER_PER_RUN * 200,
        "token_cost_note":  "proxy: loops × MAX_ITER × 200 tokens/iter",
    }

    with open(run_dir / "outcome.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    tier = config.get("tier", "?")
    fp   = f" fp={fp_info['false_proof_count']}" if fp_info else ""
    print(f"  {domain_id}/DES-{tier}/seed{seed_n}: {outcome} "
          f"| loops={len(loop_metrics)} | {elapsed}s{fp}")


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def run_des_batch(config: dict, results_dir: Path, domains: list | None = None) -> list:
    """Run all domain×seed combinations for one config."""
    _init_clients()
    results_dir.mkdir(parents=True, exist_ok=True)
    use_domains = domains or list(DOMAINS.keys())
    results = []
    for domain_id in use_domains:
        for seed_n in SEEDS:
            r = run_des_condition(domain_id, seed_n, config, results_dir)
            results.append(r)
    return results

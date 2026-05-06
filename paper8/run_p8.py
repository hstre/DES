"""
paper8/run_p8.py
Three-arm experiment: B (explicit operators, full framing) vs C (stripped prompt).
Arm A loaded from Paper 7 JSON files — NOT rerun.
WP2 (Rentschler 2026).

Usage:
    python paper8/run_p8.py               # run all arms B + C
    python paper8/run_p8.py --arm b       # Arm B only
    python paper8/run_p8.py --arm c       # Arm C only
    python paper8/run_p8.py --domain M01  # single domain
    python paper8/run_p8.py --summary     # regenerate summary from existing results
"""

import argparse
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from openai import OpenAI
from paper5.spl_wrapper import compute_claim_metrics
from paper7.en import early_saturation_detected
from paper8.mol import (
    OPERATOR_LIBRARY,
    compute_eni_components,
    extract_dominant_claim,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    invoke_operator,
    log_operator_invocation,
    select_operator,
    validate_candidate,
)
from paper8.eme import compute_eme

# ── Config ───────────────────────────────────────────────────────────────────

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 50
MAX_ITER_PER_RUN   = 40
RESULTS_DIR        = Path("paper8/batch_results_paper8")
STATE_FILE         = Path("des_state.json")

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
        # P4 baseline mean across seeds 101/202/303 from math_persona_probe_M01.json
        "p4_baseline_mean": 3.667,
        "p4_baseline_per_seed": {101: 1, 202: 6, 303: 4},
        # Arm A: Kant (best M01 persona by depth, mean=6.0)
        "arm_a_persona": "kant",
        "arm_a_loops_per_seed": {101: 5, 202: 7, 303: 6},
        # false_proof_rate for Arm A (Kant): 0/3
        "arm_a_false_proof_rate": 0.0,
    },
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "type": "empirical",
        # P4 baseline from creative_persona_probe_N03.json
        "p4_baseline_mean": 4.0,
        "p4_baseline_per_seed": {101: 4, 202: 4, 303: 4},
        # Arm A: Mozart (best N03 persona, creative_persona_probe_N03.json, mean=8.67)
        "arm_a_persona": "mozart",
        "arm_a_loops_per_seed": {101: 11, 202: 9, 303: 6},
        "arm_a_false_proof_rate": None,  # N/A for empirical domain
    },
}
SEEDS = [101, 202, 303]

# ── Global client state ───────────────────────────────────────────────────────

des_module  = None
or_client_g = None


def _init_clients():
    global des_module, or_client_g
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError("DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set.")
    import des as des_module_local
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/hstre/DES",
            "X-Title": "DES Paper8",
        },
    )
    des_module_local._clients["deepseek"]   = ds4
    des_module_local._clients["openrouter"] = orr
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER
    des_module  = des_module_local
    or_client_g = orr


def call_llm(prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=min(temperature, 2.0),
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


# ── Metric helpers (reused from paper7/run_p7.py) ────────────────────────────

def _tokens(text: str) -> set:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for","and","or",
            "but","not","with","by","from","that","this","it","be","as","at","on",
            "if","its","so","do","can","will","how","what","why","does","when","where"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def _claim_text(c: dict) -> str:
    return f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()


def token_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def count_redundant(claims: dict) -> int:
    texts = [_claim_text(c) for c in claims.values()]
    count = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if token_overlap(texts[i], texts[j]) > 0.70:
                count += 1
                break
    return count


def count_novel(claims: dict, prior_texts: list) -> int:
    if not prior_texts:
        return len(claims)
    return sum(1 for c in claims.values()
               if all(token_overlap(_claim_text(c), p) < 0.30 for p in prior_texts))


def method_diversity_score(trace: list) -> float:
    if len(trace) < 2:
        return 1.0
    return len(set(trace)) / len(trace)


def infer_method_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("evidence","study","studies","data","research","empirical")):
        return "empirical_evidence"
    if any(w in q for w in ("mechanism","why","how does","cause","because")):
        return "causal_mechanism"
    if any(w in q for w in ("when","temporal","over time","change","trend")):
        return "temporal_validity"
    if any(w in q for w in ("define","unit","measure","concept","what is")):
        return "unit_of_analysis"
    return "conceptual_framing"


def compute_metrics(state: dict, loop: int, prior_texts: list, question: str) -> dict:
    claims   = state.get("claims", {})
    total    = len(claims)
    open_c   = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel    = count_novel(claims, prior_texts)
    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))
    branches  = sum(1 for c in claims.values() if c.get("id", "").startswith("B"))
    syntheses = sum(1 for c in claims.values() if c.get("is_synthesis"))
    counters  = all_bases.count("T5")
    contr_gen = all_bases.count("T2")
    dup_rate  = redundant / max(total, 1)
    spl_m     = compute_claim_metrics(state)
    return {
        "loop":                      loop,
        "question":                  question,
        "method_type":               infer_method_type(question),
        "claim_curvature":           spl_m["claim_curvature"],
        "total_claims":              total,
        "open_claims":               open_c,
        "sealed_claims":             total - open_c,
        "disputed_claims":           disputed,
        "redundant_claims":          redundant,
        "semantic_duplication_rate": dup_rate,
        "entropy":                   (open_c + disputed + redundant) / max(total, 1),
        "novel_claims":              novel,
        "branch_growth":             branches,
        "contradictions_resolved":   syntheses,
        "total_contradictions":      max(counters, 1),
        "question_utility":          float(contr_gen * 3 + syntheses * 2 + counters * 2 + branches),
    }


def check_failure(current: dict, history: list, method_trace: list) -> str | None:
    last5 = history[-5:] if len(history) >= 5 else history
    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"
    if current["semantic_duplication_rate"] > 0.60:
        return "SEMANTIC_DUPLICATION"
    last10 = history[-10:] if len(history) >= 10 else history
    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"
    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"
    if len(method_trace) >= 5 and method_diversity_score(method_trace[-5:]) < 0.30:
        return "METHOD_COLLAPSE"
    return None


def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q: str) -> bool:
        return any(token_overlap(q, h) > 0.75 for h in question_history)

    def make_q(c: dict, prefix: str = "") -> str:
        base = _claim_text(c).strip()
        return f"{prefix}: {base}?" if prefix else f"What is the evidence that {base}?"

    open_c = sorted(
        [c for c in claims.values() if not c.get("sealed") and c.get("id", "").startswith("C")],
        key=lambda c: c.get("confidence", 0), reverse=True,
    )
    for c in open_c:
        q = make_q(c)
        if not already_asked(q):
            return q
    for c in sorted(
        [c for c in claims.values() if c.get("sealed") and not c.get("evidence_refs")],
        key=lambda c: c.get("confidence", 0),
    ):
        q = make_q(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q
    for c in sorted(
        [c for c in claims.values() if c.get("is_synthesis")],
        key=lambda c: c.get("confidence", 0), reverse=True,
    ):
        q = make_q(c, "Explore the implications of")
        if not already_asked(q):
            return q
    return "LOOP_COMPLETE"


# ── False proof detection (M01-specific) ─────────────────────────────────────

def detect_false_proofs_m01(state: dict) -> dict:
    """
    Scan M01 ClaimGraph for known false proof patterns.
    Primary: claiming n=1 is a fixed point (T(1)=6, not 1).
    Secondary: unproven universal convergence assertion.
    """
    claims = state.get("claims", {})
    errors = []
    for c in claims.values():
        text = _claim_text(c).lower()
        if ("fixed point" in text or "fixed-point" in text) and (
            "n=1" in text or "n = 1" in text or "at 1" in text or "n equals 1" in text
        ):
            errors.append("n1_fixed_point_error")
        if ("all trajectories" in text or "all orbits" in text) and (
            "converge" in text or "attractor" in text
        ) and "conjecture" not in text and "hypothesis" not in text:
            errors.append("unsupported_universal_convergence")
    return {
        "false_proof_detected": len(errors) > 0,
        "false_proof_count": len(errors),
        "error_types": list(set(errors)),
    }


# ── Arm C: stripped prompt ────────────────────────────────────────────────────

def arm_c_stripped_prompt(context: dict) -> str:
    """No operator framing. No persona. No core_move description."""
    lines = [f"{k}: {v}" for k, v in context.items() if v]
    lines += [
        "",
        "Generate ONE research question based on the above context.",
        "Return ONLY: one research question as a single sentence.",
    ]
    return "\n".join(lines)


def invoke_operator_arm_c(
    operator_id: str, state: dict,
    seed_question: str, question_history: list,
) -> dict:
    """Algorithmic context extraction identical to Arm B; stripped LLM prompt."""
    op = OPERATOR_LIBRARY[operator_id]
    claims = state.get("claims", {})

    context = {}
    if "extract_dominant_motif" in op.algorithmic_components:
        m = extract_dominant_motif(claims)
        context["dominant_motif"] = f"{m['subject']} {m['predicate']}"
    if "extract_core_tension" in op.algorithmic_components:
        context["core_tension"] = extract_core_tension(claims)
    if "extract_invariants" in op.algorithmic_components:
        invs = extract_invariants(claims)
        context["invariants"] = "; ".join(i["claim"] for i in invs[:2])
    if "classify_trajectories" in op.algorithmic_components:
        traj = classify_trajectories(claims)
        context["growth_class"] = str(traj["growth_class"])
        context["contraction_class"] = str(traj["contraction_class"])
    if "extract_dominant_claim" in op.algorithmic_components:
        dom = extract_dominant_claim(claims)
        context["dominant_claim"] = dom["claim"]
        context["confidence"] = dom["confidence"]

    prompt = arm_c_stripped_prompt(context)
    candidate = call_llm(prompt)

    eni = compute_eni_components(candidate, claims, seed_question, question_history)
    admitted, reason = validate_candidate(candidate, claims, question_history)

    return {
        "question": candidate,
        "operator_id": operator_id,
        "arm": "C",
        "admitted": admitted,
        "rejection_reason": None if admitted else reason,
        "framing_used": False,
        "context_was_algorithmic": True,
        "llm_steps": ["generation_only"],
        "context": context,
        **eni,
    }


# ── Save result ───────────────────────────────────────────────────────────────

def save_result_p8(
    run_dir: Path,
    domain_id: str,
    arm: str,
    seed: int,
    seed_question: str,
    outcome: str,
    loop_metrics: list,
    operator_log: list,
    p4_baseline_per_seed: dict,
    false_proof_info: dict | None,
    final_state: dict | None,
) -> dict:
    loops_completed = len(loop_metrics)
    p4_depth = p4_baseline_per_seed.get(seed)
    depth_lift = (loops_completed - p4_depth) if p4_depth is not None else None

    admitted = sum(1 for e in operator_log if e.get("admitted"))
    rejected = sum(1 for e in operator_log if not e.get("admitted"))

    outcome_data = {
        "domain_id":         domain_id,
        "arm":               arm,
        "seed":              seed,
        "seed_question":     seed_question,
        "outcome":           outcome,
        "loops_completed":   loops_completed,
        "p4_baseline":       p4_depth,
        "depth_lift":        depth_lift,
        "operator_events":   len(operator_log),
        "operator_admitted": admitted,
        "operator_rejected": rejected,
        "operator_log":      operator_log,
    }
    if false_proof_info is not None:
        outcome_data["false_proof_info"] = false_proof_info
    if final_state is not None:
        outcome_data["final_claims"] = final_state.get("claims", {})

    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    print(f"  {domain_id}/arm_{arm}/seed{seed}: {outcome} | loops={loops_completed} "
          f"| depth_lift={depth_lift} | op={admitted}/{len(operator_log)}")
    return outcome_data


# ── Core run loop (shared by Arms B and C) ───────────────────────────────────

def _run_arm(
    arm_label: str,
    domain_id: str,
    domain_cfg: dict,
    seed: int,
    invoke_fn,        # invoke_operator (B) or invoke_operator_arm_c (C)
    max_loops: int = MAX_LOOPS,
) -> dict:
    seed_question = domain_cfg["seed"]
    domain_type   = domain_cfg["type"]
    p4_baseline   = domain_cfg["p4_baseline_per_seed"]

    run_dir = RESULTS_DIR / f"{domain_id}_arm_{arm_label.lower()}_seed{seed}"

    # Skip completed runs
    if (run_dir / "outcome.json").exists():
        print(f"  [skip] {domain_id}/arm_{arm_label}/seed{seed} already done")
        with open(run_dir / "outcome.json") as f:
            return json.load(f)

    run_dir.mkdir(parents=True, exist_ok=True)

    # Seed Python RNG for reproducibility
    import random
    random.seed(seed)

    question         = seed_question
    question_history = [seed_question]
    method_trace     = []
    loop_metrics     = []
    all_prior_texts  = []
    operator_log     = []
    false_proof_runs = []
    final_state      = None

    print(f"\n{'='*65}")
    print(f"  {domain_id} [Arm {arm_label} | seed{seed}] | {domain_type}")
    print(f"  Seed Q: {seed_question[:70]}")
    print(f"{'='*65}")

    # Reset ONCE before the loop
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    for loop in range(max_loops):
        loop_file = run_dir / f"loop_{loop:03d}_state.json"

        # Resume from existing loop file
        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = seed_question
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            method_trace.append(metrics["method_type"])
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            next_q = select_next_question(state, question_history)
            if next_q != "LOOP_COMPLETE":
                question_history.append(next_q)
            question = next_q if next_q != "LOOP_COMPLETE" else question
            loop += 1
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        try:
            des_module.run_des(
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
            print("  ERROR: des_state.json not found after run_des")
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        state["seed_question"] = seed_question

        # Save loop state file for resume safety
        with open(loop_file, "w") as f:
            json.dump(state, f)
        final_state = state

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        method_trace.append(metrics["method_type"])
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        # M01 false proof scan
        if domain_id.startswith("M"):
            fp_info = detect_false_proofs_m01(state)
            if fp_info["false_proof_detected"]:
                false_proof_runs.append({"loop": loop, **fp_info})

        failure = check_failure(metrics, loop_metrics, method_trace)
        if failure:
            result = save_result_p8(
                run_dir, domain_id, arm_label, seed, seed_question,
                failure, loop_metrics, operator_log, p4_baseline,
                {"false_proof_runs": false_proof_runs,
                 "false_proof_rate": len(false_proof_runs) / max(loop + 1, 1)}
                if domain_id.startswith("M") else None,
                final_state,
            )
            log_operator_invocation(
                {"arm": arm_label, "domain": domain_id, "seed": seed,
                 "outcome": failure, "loops": loop + 1},
                str(run_dir / "operator_log.jsonl"),
            )
            return result

        # Operator trigger: check early saturation
        if early_saturation_detected(loop_metrics[:-1], metrics):
            operator_id = select_operator(state, loop, loop_metrics, domain_type)
            print(f"  [operator] early_saturation → {operator_id}")

            if arm_label == "B":
                op_result = invoke_operator(
                    operator_id, state, seed_question, question_history,
                    call_llm_fn=call_llm,
                )
            else:
                op_result = invoke_fn(
                    operator_id, state, seed_question, question_history,
                )
            op_result["arm"] = arm_label
            op_result["loop"] = loop

            log_operator_invocation(
                op_result,
                str(run_dir / "operator_log.jsonl"),
            )
            operator_log.append(op_result)

            if op_result["admitted"]:
                question = op_result["question"]
                question_history.append(question)
                print(f"  [operator] admitted: {question[:60]}")
                continue
            else:
                print(f"  [operator] rejected: {op_result.get('rejection_reason')}")

        # Default: select next question from graph
        next_q = select_next_question(state, question_history)
        if next_q == "LOOP_COMPLETE":
            result = save_result_p8(
                run_dir, domain_id, arm_label, seed, seed_question,
                "LOOP_COMPLETE", loop_metrics, operator_log, p4_baseline,
                {"false_proof_runs": false_proof_runs,
                 "false_proof_rate": len(false_proof_runs) / max(loop + 1, 1)}
                if domain_id.startswith("M") else None,
                final_state,
            )
            log_operator_invocation(
                {"arm": arm_label, "domain": domain_id, "seed": seed,
                 "outcome": "LOOP_COMPLETE", "loops": loop + 1},
                str(run_dir / "operator_log.jsonl"),
            )
            return result

        question = next_q
        question_history.append(question)

    # max_loops exhausted
    outcome = "MAX_LOOPS_REACHED"
    result = save_result_p8(
        run_dir, domain_id, arm_label, seed, seed_question,
        outcome, loop_metrics, operator_log, p4_baseline,
        {"false_proof_runs": false_proof_runs,
         "false_proof_rate": len(false_proof_runs) / max(max_loops, 1)}
        if domain_id.startswith("M") else None,
        final_state,
    )
    return result


def run_arm_b(domain_id: str, seed: int, max_loops: int = MAX_LOOPS) -> dict:
    return _run_arm("B", domain_id, DOMAINS[domain_id], seed,
                    invoke_fn=None,  # B uses invoke_operator directly in _run_arm
                    max_loops=max_loops)


def run_arm_c(domain_id: str, seed: int, max_loops: int = MAX_LOOPS) -> dict:
    return _run_arm("C", domain_id, DOMAINS[domain_id], seed,
                    invoke_fn=invoke_operator_arm_c,
                    max_loops=max_loops)


# ── Arm A: load from Paper 7 ──────────────────────────────────────────────────

def load_arm_a() -> dict:
    """Load Paper 7 results — do NOT rerun."""
    arm_a = {}
    for domain_id, cfg in DOMAINS.items():
        persona = cfg["arm_a_persona"]
        loops   = cfg["arm_a_loops_per_seed"]
        arm_a[domain_id] = {
            "persona":   persona,
            "loops_per_seed": loops,
            "mean_loops": sum(loops.values()) / len(loops),
            "std_loops":  _std(list(loops.values())),
            "depth_lifts": {
                s: loops[s] - cfg["p4_baseline_per_seed"][s]
                for s in SEEDS
            },
            "false_proof_rate": cfg.get("arm_a_false_proof_rate"),
            "eme": "unavailable",  # Paper 7 JSONs lack final_claims
        }
    return arm_a


# ── Statistics helpers ────────────────────────────────────────────────────────

def _std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return round(math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)), 4)


def _mean(values: list) -> float:
    return round(sum(values) / max(len(values), 1), 4)


# ── Hypothesis verdicts ───────────────────────────────────────────────────────

def compute_hypothesis_verdicts(arm_a: dict, arm_b_results: list, arm_c_results: list) -> dict:
    verdicts = {}

    for domain_id in DOMAINS:
        cfg    = DOMAINS[domain_id]
        a      = arm_a[domain_id]
        p4     = cfg["p4_baseline_mean"]
        a_mean = a["mean_loops"]

        b_runs = [r for r in arm_b_results if r["domain_id"] == domain_id]
        c_runs = [r for r in arm_c_results if r["domain_id"] == domain_id]
        b_loops = [r["loops_completed"] for r in b_runs]
        c_loops = [r["loops_completed"] for r in c_runs]

        b_mean = _mean(b_loops) if b_loops else 0.0
        c_mean = _mean(c_loops) if c_loops else 0.0
        b_std  = _std(b_loops) if b_loops else 0.0
        c_std  = _std(c_loops) if c_loops else 0.0
        a_std  = a["std_loops"]

        # H1: Arm B mean_depth >= P4_baseline + 0.8*(Arm A mean - P4_baseline)
        h1_threshold = p4 + 0.8 * (a_mean - p4)
        h1_verdict = "CONFIRMED" if b_mean >= h1_threshold else "REJECTED"

        # H2: Arm C false_proof_rate < Arm A false_proof_rate (M01 only)
        if domain_id.startswith("M"):
            a_fp = a.get("false_proof_rate", 0.0) or 0.0
            c_fp_runs = [r.get("false_proof_info", {}).get("false_proof_rate", 0.0)
                         for r in c_runs if r.get("false_proof_info")]
            c_fp = _mean(c_fp_runs) if c_fp_runs else 0.0
            b_fp_runs = [r.get("false_proof_info", {}).get("false_proof_rate", 0.0)
                         for r in b_runs if r.get("false_proof_info")]
            b_fp = _mean(b_fp_runs) if b_fp_runs else 0.0
            if a_fp == 0.0 and c_fp == 0.0:
                h2_verdict = "INDETERMINATE_BOTH_ZERO"
            elif c_fp < a_fp:
                h2_verdict = "CONFIRMED"
            else:
                h2_verdict = "REJECTED"
        else:
            h2_verdict = "N/A"
            a_fp = b_fp = c_fp = None

        # H3a: std(Arm B) < std(Arm A)
        if b_std < a_std:
            h3a_verdict = "CONFIRMED"
        elif b_std == a_std:
            h3a_verdict = "INDETERMINATE_EQUAL"
        else:
            h3a_verdict = "REJECTED"

        # H3b: std(Arm C) < std(Arm A)
        if c_std < a_std:
            h3b_verdict = "CONFIRMED"
        elif c_std == a_std:
            h3b_verdict = "INDETERMINATE_EQUAL"
        else:
            h3b_verdict = "REJECTED"

        verdicts[domain_id] = {
            "H1": {
                "verdict": h1_verdict,
                "b_mean": b_mean, "a_mean": a_mean, "p4": p4,
                "threshold": round(h1_threshold, 4),
                "formula": "P4 + 0.8*(Arm_A - P4)",
            },
            "H2": {
                "verdict": h2_verdict,
                "arm_a_fp": a_fp, "arm_b_fp": b_fp, "arm_c_fp": c_fp,
            },
            "H3a": {
                "verdict": h3a_verdict,
                "arm_b_std": b_std, "arm_a_std": a_std,
            },
            "H3b": {
                "verdict": h3b_verdict,
                "arm_c_std": c_std, "arm_a_std": a_std,
            },
            "H4": {
                "verdict": "INDETERMINATE",
                "reason": "Paper 7 final_claims unavailable; arm_a_eme=unavailable",
            },
        }

    return verdicts


# ── update_confidence ─────────────────────────────────────────────────────────

def update_operators_from_results() -> None:
    """Update MOL operator confidence from Phase 2 results."""
    phase2_results = []
    for f in RESULTS_DIR.glob("*/outcome.json"):
        with open(f) as fh:
            phase2_results.append(json.load(fh))

    for op_key, op in OPERATOR_LIBRARY.items():
        for run in phase2_results:
            for event in run.get("operator_log", []):
                if event.get("operator_id") in (op_key, op.operator_id):
                    lift = run.get("depth_lift", 0) or 0
                    domain = run.get("domain_id", "unknown")
                    seed = str(run.get("seed", 0))
                    if lift > 0:
                        op.known_successes.append((domain, seed, lift))
                    elif lift < 0:
                        op.known_failures.append((domain, seed, lift))
        op.update_confidence()
        print(f"{op.operator_id}: confidence={op.confidence}, sigma={op.sigma_stability}")


# ── EME computation ───────────────────────────────────────────────────────────

def compute_eme_for_arm(arm_results: list) -> dict:
    """Collect final_claims from arm results and compute EME."""
    run_dicts = []
    for r in arm_results:
        final_claims = r.get("final_claims")
        if final_claims:
            run_dicts.append({"final_claims": final_claims})
    return compute_eme(run_dicts)


# ── Summary ───────────────────────────────────────────────────────────────────

def write_summary(
    arm_a: dict,
    arm_b_results: list,
    arm_c_results: list,
    verdicts: dict,
    eme_b: dict,
    eme_c: dict,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # EME comparison JSON
    eme_data = {
        "arm_a": {d: {"eme": arm_a[d]["eme"]} for d in DOMAINS},
        "arm_b": eme_b,
        "arm_c": eme_c,
    }
    with open(RESULTS_DIR / "eme_comparison.json", "w") as f:
        json.dump(eme_data, f, indent=2)

    lines = [
        "# Paper 8 — Phase 2: Three-Arm Experiment",
        "",
        "**Arms:** A (Paper 7 persona, reference) | B (explicit operators, full framing) | "
        "C (algorithmic context, stripped prompt)",
        f"**Domains:** {', '.join(DOMAINS)} | **Seeds:** {SEEDS} | **Max loops:** {MAX_LOOPS}",
        "",
        "---",
        "",
        "## Arm A Reference (Paper 7, not rerun)",
        "",
        "| Domain | Best persona | Seed 101 | Seed 202 | Seed 303 | Mean loops | Std |",
        "|--------|-------------|----------|----------|----------|------------|-----|",
    ]
    for domain_id in DOMAINS:
        a = arm_a[domain_id]
        lps = a["loops_per_seed"]
        lines.append(
            f"| {domain_id} | {a['persona']} | {lps[101]} | {lps[202]} | {lps[303]} "
            f"| {a['mean_loops']:.2f} | {a['std_loops']:.4f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Arm B — Explicit Operators (Full Framing)",
        "",
        "| Domain | Seed | Loops | P4 | depth_lift | Outcome | Op admitted |",
        "|--------|------|-------|----|------------|---------|-------------|",
    ]
    for r in sorted(arm_b_results, key=lambda x: (x["domain_id"], x["seed"])):
        lines.append(
            f"| {r['domain_id']} | {r['seed']} | {r['loops_completed']} "
            f"| {r.get('p4_baseline','?')} | {r.get('depth_lift','?')} "
            f"| {r['outcome']} | {r.get('operator_admitted',0)}/{r.get('operator_events',0)} |"
        )

    lines += [
        "",
        "## Arm C — Stripped Prompt (Algorithmic Context Only)",
        "",
        "| Domain | Seed | Loops | P4 | depth_lift | Outcome | Op admitted |",
        "|--------|------|-------|----|------------|---------|-------------|",
    ]
    for r in sorted(arm_c_results, key=lambda x: (x["domain_id"], x["seed"])):
        lines.append(
            f"| {r['domain_id']} | {r['seed']} | {r['loops_completed']} "
            f"| {r.get('p4_baseline','?')} | {r.get('depth_lift','?')} "
            f"| {r['outcome']} | {r.get('operator_admitted',0)}/{r.get('operator_events',0)} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Per-Domain Three-Way Comparison",
        "",
        "| Domain | P4 mean | Arm A mean | Arm B mean | Arm C mean | "
        "Arm A std | Arm B std | Arm C std |",
        "|--------|---------|------------|------------|------------|"
        "----------|----------|----------|",
    ]
    for domain_id in DOMAINS:
        cfg = DOMAINS[domain_id]
        a   = arm_a[domain_id]
        b_loops = [r["loops_completed"] for r in arm_b_results if r["domain_id"] == domain_id]
        c_loops = [r["loops_completed"] for r in arm_c_results if r["domain_id"] == domain_id]
        lines.append(
            f"| {domain_id} | {cfg['p4_baseline_mean']:.2f} | {a['mean_loops']:.2f} "
            f"| {_mean(b_loops):.2f} | {_mean(c_loops):.2f} "
            f"| {a['std_loops']:.4f} | {_std(b_loops):.4f} | {_std(c_loops):.4f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## False Proof Rate (M01 only)",
        "",
        "| Arm | False proof rate |",
        "|-----|-----------------|",
    ]
    for domain_id in DOMAINS:
        if not domain_id.startswith("M"):
            continue
        a_fp = arm_a[domain_id].get("false_proof_rate")
        b_fp_vals = [r.get("false_proof_info", {}).get("false_proof_rate", 0.0)
                     for r in arm_b_results if r["domain_id"] == domain_id
                     and r.get("false_proof_info")]
        c_fp_vals = [r.get("false_proof_info", {}).get("false_proof_rate", 0.0)
                     for r in arm_c_results if r["domain_id"] == domain_id
                     and r.get("false_proof_info")]
        lines += [
            f"| A (Kant, {domain_id}) | {a_fp if a_fp is not None else 'N/A'} |",
            f"| B ({domain_id}) | {_mean(b_fp_vals):.4f} |",
            f"| C ({domain_id}) | {_mean(c_fp_vals):.4f} |",
        ]

    lines += [
        "",
        "---",
        "",
        "## EME Scores",
        "",
        "| Arm | EME score | Clusters | Note |",
        "|-----|-----------|----------|------|",
        f"| A | unavailable | — | Paper 7 final_claims absent |",
        f"| B | {eme_b.get('eme_score','N/A')} | {eme_b.get('cluster_count','N/A')} | "
        f"{eme_b.get('reason','')} |",
        f"| C | {eme_c.get('eme_score','N/A')} | {eme_c.get('cluster_count','N/A')} | "
        f"{eme_c.get('reason','')} |",
        "",
        "---",
        "",
        "## Hypothesis Verdicts",
        "",
    ]
    for domain_id, v in verdicts.items():
        lines += [
            f"### {domain_id}",
            "",
            f"**H1** (Arm B >= P4 + 0.8*(Arm A - P4)): **{v['H1']['verdict']}**",
            f"  - Threshold = {v['H1']['p4']} + 0.8*({v['H1']['a_mean']} - {v['H1']['p4']}) "
            f"= {v['H1']['threshold']}",
            f"  - Arm B mean = {v['H1']['b_mean']}",
            "",
            f"**H2** (Arm C false_proof_rate < Arm A): **{v['H2']['verdict']}**",
            f"  - Arm A: {v['H2']['arm_a_fp']}, Arm B: {v['H2']['arm_b_fp']}, "
            f"Arm C: {v['H2']['arm_c_fp']}",
            "",
            f"**H3a** (std(Arm B) < std(Arm A)): **{v['H3a']['verdict']}**",
            f"  - Arm B std={v['H3a']['arm_b_std']}, Arm A std={v['H3a']['arm_a_std']}",
            "",
            f"**H3b** (std(Arm C) < std(Arm A)): **{v['H3b']['verdict']}**",
            f"  - Arm C std={v['H3b']['arm_c_std']}, Arm A std={v['H3b']['arm_a_std']}",
            "",
            f"**H4** (EME(Arm B) > EME(Arm A) on M01): **{v['H4']['verdict']}**",
            f"  - {v['H4']['reason']}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Notes",
        "",
        "- Arm A loaded from paper7/creative_persona_probe_N03.json (Mozart) and "
        "paper7/math_persona_probe_M01.json (Kant). Not rerun.",
        "- Arm B uses full llm_prompt_template including operator framing and core_move.",
        "- Arm C uses bare key-value context + single instruction. No operator framing.",
        "- H4 requires final_claims in Paper 7 JSON. Unavailable: not computed.",
        "- Operator prompts and thresholds frozen from Phase 1. Not tuned post-results.",
        "- DES internals and SPL not modified.",
    ]

    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nSummary written to {RESULTS_DIR / 'summary.md'}")
    print(f"EME written to {RESULTS_DIR / 'eme_comparison.json'}")


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all(arms: str = "bc", domains: list | None = None) -> None:
    _init_clients()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    target_domains = domains or list(DOMAINS.keys())
    arm_b_results  = []
    arm_c_results  = []

    for domain_id in target_domains:
        for seed in SEEDS:
            if "b" in arms:
                r = run_arm_b(domain_id, seed)
                arm_b_results.append(r)
            if "c" in arms:
                r = run_arm_c(domain_id, seed)
                arm_c_results.append(r)

    # Collect any previously completed runs not in this session
    for f in RESULTS_DIR.glob("*_arm_b_seed*/outcome.json"):
        with open(f) as fh:
            r = json.load(fh)
        if r not in arm_b_results:
            arm_b_results.append(r)
    for f in RESULTS_DIR.glob("*_arm_c_seed*/outcome.json"):
        with open(f) as fh:
            r = json.load(fh)
        if r not in arm_c_results:
            arm_c_results.append(r)

    arm_a    = load_arm_a()
    verdicts = compute_hypothesis_verdicts(arm_a, arm_b_results, arm_c_results)
    eme_b    = compute_eme_for_arm(arm_b_results)
    eme_c    = compute_eme_for_arm(arm_c_results)

    write_summary(arm_a, arm_b_results, arm_c_results, verdicts, eme_b, eme_c)
    update_operators_from_results()

    print("\nPhase 2 complete.")


def regenerate_summary() -> None:
    """Rebuild summary.md from existing result files without running new experiments."""
    arm_b_results, arm_c_results = [], []
    for f in RESULTS_DIR.glob("*_arm_b_seed*/outcome.json"):
        with open(f) as fh:
            arm_b_results.append(json.load(fh))
    for f in RESULTS_DIR.glob("*_arm_c_seed*/outcome.json"):
        with open(f) as fh:
            arm_c_results.append(json.load(fh))
    arm_a    = load_arm_a()
    verdicts = compute_hypothesis_verdicts(arm_a, arm_b_results, arm_c_results)
    eme_b    = compute_eme_for_arm(arm_b_results)
    eme_c    = compute_eme_for_arm(arm_c_results)
    write_summary(arm_a, arm_b_results, arm_c_results, verdicts, eme_b, eme_c)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["b","c","bc"], default="bc",
                        help="Which arms to run (default: bc)")
    parser.add_argument("--domain", choices=list(DOMAINS), default=None,
                        help="Single domain (default: all)")
    parser.add_argument("--summary", action="store_true",
                        help="Regenerate summary from existing results only")
    args = parser.parse_args()

    if args.summary:
        regenerate_summary()
    else:
        run_all(
            arms=args.arm,
            domains=[args.domain] if args.domain else None,
        )

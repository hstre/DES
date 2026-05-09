"""
des_premium/run_des_phase_a_b.py
Orchestrator for two-tier DES runs (Phase A + Phase B Review).

Three conditions:
  DES_PHASE_A_ONLY  — Phase A only (cheap divergent builder, no review)
  DES_PHASE_A_B     — Phase A + Phase B (cheap builder + premium reviewer)
  COT_PREMIUM       — Single-shot CoT with the Phase B reviewer model

Usage:
  python des_premium/run_des_phase_a_b.py [--condition COND] [--resume]

  COND: DES_PHASE_A_ONLY | DES_PHASE_A_B | COT_PREMIUM | all  (default: all)
  --resume: skip runs where outcome.json already exists (off by default — all
            runs are re-executed fresh unless this flag is set)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from openai import OpenAI

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

from des_premium.config import (
    CHEAP_CONFIG,
    COT_PREMIUM_CONFIG,
    COT_PROMPT_TEMPLATE,
    DOMAINS,
    JUDGE_CONFIG,
    PILOT_DOMAINS,
    REVIEW_CONFIG,
    SEEDS,
)
from des_premium.phase_b_review import (
    run_phase_b,
    run_judge_eval,
    serialize_claim_graph,
)

# ── Result directories ────────────────────────────────────────────────────────

RESULTS_BASE = Path("des_premium")
DIR_PHASE_A_ONLY = RESULTS_BASE / "batch_results_phase_a_only"
DIR_PHASE_A_B    = RESULTS_BASE / "batch_results_des_phase_a_b"
DIR_COT_PREMIUM  = RESULTS_BASE / "batch_results_cot_premium_pb"

MAX_LOOPS        = 50
MAX_ITER_PER_RUN = 40

# ── Provenance helpers ────────────────────────────────────────────────────────

def _run_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _code_hash() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "UNKNOWN"


def _prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _assert_domain_match(domain_id: str, seed_question: str) -> None:
    expected = DOMAINS.get(domain_id)
    if expected != seed_question:
        raise AssertionError(
            f"Domain mismatch: domain_id={domain_id!r} does not match "
            f"seed_question used in prompt.\n"
            f"  Expected: {expected!r}\n"
            f"  Got:      {seed_question!r}"
        )


# ── OpenRouter client for CoT Premium ────────────────────────────────────────

_or_client: OpenAI | None = None


def _openrouter_client() -> OpenAI:
    global _or_client
    if _or_client is None:
        ok = os.environ.get("OPENROUTER_API_KEY", "")
        if not ok:
            raise EnvironmentError("OPENROUTER_API_KEY must be set.")
        _or_client = OpenAI(
            api_key=ok,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/hstre/DES",
                "X-Title": "DES-phase-b",
            },
        )
    return _or_client


# ── Phase A runner ────────────────────────────────────────────────────────────

def run_phase_a(
    domain_id:   str,
    seed_n:      int,
    run_dir:     Path,
    resume:      bool = False,
) -> dict:
    """
    Run Phase A (DES cheap config) for one domain/seed.
    Returns a dict with outcome, loop states, metrics, and provenance.
    No skip logic unless resume=True and outcome.json already exists.
    """
    result_file = run_dir / "outcome.json"
    if resume and result_file.exists():
        print(f"  [resume] {domain_id} seed={seed_n} — loading existing Phase A")
        with open(result_file) as f:
            d = json.load(f)
        # Reconstruct loop_states list
        loop_states = _load_loop_states(run_dir)
        d["_loop_states"] = loop_states
        return d

    seed_question = DOMAINS[domain_id]
    config        = CHEAP_CONFIG

    print(f"\n{'='*65}")
    print(f"  [Phase A] {domain_id} seed={seed_n}")
    print(f"  builder={config['builder_model']}  falsifier={config['falsifier_model']}")
    print(f"  Q: {seed_question[:70]}")
    print(f"{'='*65}")

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    question         = seed_question
    question_history = [seed_question]
    loop_metrics     = []
    all_prior_texts  = []
    final_state: dict | None  = None
    loop_states: list[dict]   = []
    t_start          = _run_timestamp()
    t0               = time.time()

    for loop in range(MAX_LOOPS):
        loop_file = run_dir / f"loop_{loop:03d}_state.json"
        if loop_file.exists() and resume:
            with open(loop_file) as f:
                state = json.load(f)
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            loop_metrics.append(metrics)
            loop_states.append(state)
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
            print("  ERROR: des_state.json not found after run_des()")
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        with open(loop_file, "w") as f:
            json.dump(state, f, indent=2)
        final_state = state
        loop_states.append(state)

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        failure = check_failure(metrics, loop_metrics, [])
        if failure:
            return _save_phase_a(
                run_dir, domain_id, seed_n, config, failure,
                loop_metrics, loop_states, final_state,
                seed_question, t_start, t0,
            )

        nq = select_next_question(state, question_history)
        if nq == "LOOP_COMPLETE":
            return _save_phase_a(
                run_dir, domain_id, seed_n, config, "LOOP_COMPLETE",
                loop_metrics, loop_states, final_state,
                seed_question, t_start, t0,
            )

        question = nq
        question_history.append(question)

    return _save_phase_a(
        run_dir, domain_id, seed_n, config, "MAX_LOOPS_REACHED",
        loop_metrics, loop_states, final_state,
        seed_question, t_start, t0,
    )


def _save_phase_a(
    run_dir:      Path,
    domain_id:    str,
    seed_n:       int,
    config:       dict,
    outcome:      str,
    loop_metrics: list,
    loop_states:  list,
    final_state:  dict | None,
    seed_question: str,
    t_start:      str,
    t0:           float,
) -> dict:
    _assert_domain_match(domain_id, seed_question)

    fp_info = None
    if domain_id == "M01" and final_state:
        fp_info = detect_false_proofs_m01(final_state)

    elapsed   = round(time.time() - t0, 1)
    dup_rates = [m["semantic_duplication_rate"] for m in loop_metrics]
    novel_v   = [m["novel_claims"]  for m in loop_metrics]
    total_v   = [m["total_claims"]  for m in loop_metrics]

    data = {
        "domain_id":        domain_id,
        "seed":             seed_n,
        "seed_question":    seed_question,
        "config": {k: v for k, v in config.items() if k != "note"},
        "outcome":          outcome,
        "loops_completed":  len(loop_metrics),
        "elapsed_seconds":  elapsed,
        "false_proof_info": fp_info,
        "false_proof_detected": fp_info["false_proof_detected"] if fp_info else None,
        "final_claims": final_state.get("claims", {}) if final_state else {},
        "semantic_duplication_rate_mean": round(sum(dup_rates) / len(dup_rates), 4) if dup_rates else None,
        "novel_claims_mean":              round(sum(novel_v)   / len(novel_v),   2) if novel_v   else None,
        "total_claims_final":             total_v[-1] if total_v else None,
        "run_timestamp":   t_start,
        "code_hash":       _code_hash(),
        "model_versions": {
            "builder":   config["builder_model"],
            "falsifier": config["falsifier_model"],
        },
    }

    with open(run_dir / "outcome.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    data["_loop_states"] = loop_states
    print(f"  Phase A done: {domain_id}/seed{seed_n} → {outcome} | loops={len(loop_metrics)} | {elapsed}s")
    return data


def _load_loop_states(run_dir: Path) -> list[dict]:
    states = []
    for p in sorted(run_dir.glob("loop_*_state.json")):
        with open(p) as f:
            states.append(json.load(f))
    return states


# ── Condition runners ─────────────────────────────────────────────────────────

def run_des_phase_a_only(
    domain_id: str,
    seed_n:    int,
    resume:    bool = False,
) -> dict:
    run_dir = DIR_PHASE_A_ONLY / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)

    result = run_phase_a(domain_id, seed_n, run_dir, resume=resume)

    meta = {
        "condition":      "DES_PHASE_A_ONLY",
        "domain_id":      domain_id,
        "seed":           seed_n,
        "run_timestamp":  result.get("run_timestamp"),
        "code_hash":      result.get("code_hash"),
        "model_versions": result.get("model_versions"),
        "phase_b":        None,
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    return result


def run_des_phase_a_b(
    domain_id: str,
    seed_n:    int,
    resume:    bool = False,
) -> dict:
    run_dir = DIR_PHASE_A_B / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Phase A
    phase_a = run_phase_a(domain_id, seed_n, run_dir, resume=resume)
    termination = phase_a["outcome"]

    loop_states = phase_a.get("_loop_states") or _load_loop_states(run_dir)
    final_claims = phase_a.get("final_claims") or {}
    seed_question = DOMAINS[domain_id]

    # Serialise Phase A graph and save it
    final_state = loop_states[-1] if loop_states else {"claims": final_claims}
    graph = serialize_claim_graph(loop_states, final_state)
    with open(run_dir / "phase_a_graph.json", "w") as f:
        json.dump(graph, f, indent=2)

    # Phase B
    print(f"\n  [Phase B] {domain_id} seed={seed_n} | variant={termination}")
    phase_b_result = run_phase_b(
        seed_question=seed_question,
        termination_reason=termination,
        loop_states=loop_states,
        final_state=final_state,
        seed_n=seed_n,
        config=REVIEW_CONFIG,
    )
    with open(run_dir / "phase_b_review.json", "w") as f:
        json.dump(phase_b_result, f, indent=2)

    # Merge into outcome
    structured = phase_b_result["structured_output"]
    outcome = {
        **{k: v for k, v in phase_a.items() if not k.startswith("_")},
        "phase_b_variant":     phase_b_result["phase_b_variant"],
        "phase_b_synthesis":   structured.get("synthesis_claim", ""),
        "phase_b_meta":        structured.get("meta_assessment", ""),
        "phase_b_graph_hash":  phase_b_result["phase_a_graph_hash"],
        "phase_b_elapsed":     phase_b_result["elapsed_seconds"],
        "phase_b_parse_error": structured.get("parse_error", False),
    }
    with open(run_dir / "outcome.json", "w") as f:
        json.dump({k: v for k, v in outcome.items() if not k.startswith("_")}, f, indent=2)

    meta = {
        "condition":      "DES_PHASE_A_B",
        "domain_id":      domain_id,
        "seed":           seed_n,
        "run_timestamp":  phase_a.get("run_timestamp"),
        "code_hash":      phase_a.get("code_hash"),
        "model_versions": {
            **phase_a.get("model_versions", {}),
            "reviewer": REVIEW_CONFIG["reviewer_model"],
        },
        "phase_b_prompt_hash": phase_b_result["prompt_hash"],
        "phase_b_graph_hash":  phase_b_result["phase_a_graph_hash"],
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Phase B done: meta_assessment={structured.get('meta_assessment','?')} | {phase_b_result['elapsed_seconds']}s")
    return outcome


def run_cot_premium_single(
    domain_id: str,
    seed_n:    int,
    resume:    bool = False,
) -> dict:
    run_dir = DIR_COT_PREMIUM / f"{domain_id}_seed{seed_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_file = run_dir / "outcome.json"

    if resume and result_file.exists():
        print(f"  [resume] COT_PREMIUM {domain_id} seed={seed_n}")
        with open(result_file) as f:
            return json.load(f)

    seed_question = DOMAINS[domain_id]
    config        = COT_PREMIUM_CONFIG
    model         = config["builder_model"]
    provider      = config["builder_provider"]

    prompt = COT_PROMPT_TEMPLATE.format(seed_question=seed_question, seed_n=seed_n)
    p_hash = _prompt_hash(prompt)
    t_start_str = _run_timestamp()

    print(f"\n  [COT_PREMIUM] {domain_id} seed={seed_n} | model={model}")

    t0 = time.time()
    try:
        resp = _openrouter_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
        )
        content = resp.choices[0].message.content or ""
        usage = {}
        if resp.usage:
            usage = {
                "prompt_tokens":     resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens":      resp.usage.total_tokens,
            }
    except Exception as e:
        print(f"  ERROR: {e}")
        content, usage = "", {}

    elapsed = round(time.time() - t0, 1)

    sentences = _extract_sentences(content)
    dup_rate  = _dup_rate(sentences)
    steps     = _count_steps(content)
    fp_info   = _scan_false_proof_m01(content) if domain_id == "M01" else None

    _assert_domain_match(domain_id, seed_question)

    data = {
        "domain_id":                 domain_id,
        "seed":                      seed_n,
        "seed_question":             seed_question,
        "condition":                 "COT_PREMIUM",
        "config": {k: v for k, v in config.items() if k != "note"},
        "outcome":                   "COT_COMPLETE" if content else "COT_ERROR",
        "word_count":                len(content.split()),
        "reasoning_steps":           steps,
        "sentence_count":            len(sentences),
        "semantic_duplication_rate": dup_rate,
        "false_proof_info":          fp_info,
        "false_proof_detected":      fp_info["false_proof_detected"] if fp_info else None,
        "elapsed_seconds":           elapsed,
        "token_usage":               usage,
        "output":                    content,
        "run_timestamp":             t_start_str,
        "code_hash":                 _code_hash(),
        "prompt_hash":               p_hash,
        "model_versions":            {"builder": model},
    }

    with open(result_file, "w") as f:
        json.dump(data, f, indent=2)

    meta = {
        "condition":      "COT_PREMIUM",
        "domain_id":      domain_id,
        "seed":           seed_n,
        "run_timestamp":  t_start_str,
        "code_hash":      _code_hash(),
        "prompt_hash":    p_hash,
        "model_versions": {"builder": model},
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  CoT done: {steps} steps | {len(sentences)} sentences | dup={dup_rate} | {elapsed}s")
    return data


# ── Text utilities for CoT ────────────────────────────────────────────────────

def _extract_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 20]


def _token_overlap(a: str, b: str) -> float:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for","and","or",
            "but","not","with","by","from","that","this","it","be","as","at"}
    ta = set(re.sub(r"[^a-z0-9 ]", "", a.lower()).split()) - STOP
    tb = set(re.sub(r"[^a-z0-9 ]", "", b.lower()).split()) - STOP
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _dup_rate(sentences: list[str]) -> float:
    if len(sentences) < 2:
        return 0.0
    count = sum(
        1 for i in range(len(sentences))
        for j in range(i + 1, len(sentences))
        if _token_overlap(sentences[i], sentences[j]) > 0.70
    )
    return round(count / max(len(sentences), 1), 4)


def _count_steps(text: str) -> int:
    numbered = len(re.findall(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))
    return numbered if numbered >= 2 else len([p for p in text.split("\n\n") if p.strip()])


_FP_PATTERNS_M01 = [
    r"T\(n\)\s*always\s*(converges|terminates|reaches\s*1)",
    r"all\s*(trajectories|sequences)\s*(converge|terminate)",
    r"no\s*(divergent|infinite)\s*(trajectory|sequence)",
    r"proven\s*to\s*(converge|terminate)",
]


def _scan_false_proof_m01(text: str) -> dict:
    errors = [p for p in _FP_PATTERNS_M01 if re.search(p, text, re.IGNORECASE)]
    return {
        "false_proof_detected": len(errors) > 0,
        "false_proof_count":    len(errors),
        "patterns_matched":     errors,
    }


# ── Judge evaluation batch ────────────────────────────────────────────────────

def run_judge_batch(
    domains: list[str],
    seeds:   list[int],
    resume:  bool = False,
) -> None:
    """Run judge evaluation over all three condition directories."""
    conditions = [
        ("DES_PHASE_A_ONLY", DIR_PHASE_A_ONLY,   _extract_text_phase_a_only),
        ("DES_PHASE_A_B",    DIR_PHASE_A_B,       _extract_text_phase_a_b),
        ("COT_PREMIUM",      DIR_COT_PREMIUM,     _extract_text_cot_premium),
    ]
    for cond_name, cond_dir, extractor in conditions:
        for domain_id in domains:
            for seed_n in seeds:
                run_dir   = cond_dir / f"{domain_id}_seed{seed_n}"
                judge_out = run_dir / "judge_eval.json"
                if resume and judge_out.exists():
                    print(f"  [resume] judge {cond_name} {domain_id} seed={seed_n}")
                    continue
                outcome_p = run_dir / "outcome.json"
                if not outcome_p.exists():
                    print(f"  [warn] no outcome.json for {cond_name} {domain_id} seed={seed_n}")
                    continue
                with open(outcome_p) as f:
                    outcome = json.load(f)
                output_text = extractor(outcome, run_dir)
                seed_q = DOMAINS[domain_id]
                print(f"  [judge] {cond_name} {domain_id} seed={seed_n}")
                result = run_judge_eval(output_text, seed_q, domain_id, JUDGE_CONFIG)
                with open(judge_out, "w") as f:
                    json.dump(result, f, indent=2)
                scores = result["scores"]
                print(
                    f"    sq={scores.get('synthesis_quality')} "
                    f"bp={scores.get('branch_preservation')} "
                    f"ga={scores.get('gap_acknowledgment')} "
                    f"cal={scores.get('calibration')} "
                    f"fpa={scores.get('false_proof_avoidance')}"
                )


def _extract_text_phase_a_only(outcome: dict, run_dir: Path) -> str:
    """Produce evaluable text from Phase A only outcome (claim set summary)."""
    claims = outcome.get("final_claims", {})
    if not claims:
        return "(no claims)"
    parts = []
    for cid, c in claims.items():
        text = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()
        conf = c.get("confidence", "?")
        status = c.get("status", "?")
        parts.append(f"[{cid}] ({status}, conf={conf}) {text}")
    termination = outcome.get("outcome", "?")
    return (
        f"Phase A claim graph summary (termination: {termination}):\n\n"
        + "\n".join(parts)
    )


def _extract_text_phase_a_b(outcome: dict, run_dir: Path) -> str:
    """Produce evaluable text from Phase A+B outcome (Phase B synthesis + rationale)."""
    phase_b_path = run_dir / "phase_b_review.json"
    if phase_b_path.exists():
        with open(phase_b_path) as f:
            pb = json.load(f)
        s = pb.get("structured_output", {})
        synthesis  = s.get("synthesis_claim", "")
        rationale  = s.get("review_rationale", "")
        gaps       = s.get("gap_identification", [])
        meta       = s.get("meta_assessment", "")
        gap_text   = "\n".join(
            f"- {g['region']}: {g['would_resolve']}" for g in gaps
        ) if gaps else "(none identified)"
        return (
            f"Phase A+B synthesis output:\n\n"
            f"Meta-assessment: {meta}\n\n"
            f"Synthesis claim: {synthesis}\n\n"
            f"Review rationale: {rationale}\n\n"
            f"Identified gaps:\n{gap_text}"
        )
    # Fall back to outcome fields
    return (
        f"Synthesis: {outcome.get('phase_b_synthesis','')}\n"
        f"Meta: {outcome.get('phase_b_meta','')}"
    )


def _extract_text_cot_premium(outcome: dict, _run_dir: Path) -> str:
    return outcome.get("output", "(no output)")


# ── Main entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DES Phase A+B orchestrator")
    parser.add_argument(
        "--condition",
        choices=["DES_PHASE_A_ONLY", "DES_PHASE_A_B", "COT_PREMIUM", "judge", "all"],
        default="all",
    )
    parser.add_argument("--resume", action="store_true",
                        help="Skip runs with existing outcome.json")
    parser.add_argument("--domains", nargs="+", default=PILOT_DOMAINS)
    parser.add_argument("--seeds",   nargs="+", type=int, default=SEEDS)
    args = parser.parse_args()

    domains = args.domains
    seeds   = args.seeds

    # Initialise DES clients (Phase A builder + falsifier)
    _init_clients()

    cond = args.condition

    if cond in ("DES_PHASE_A_ONLY", "all"):
        print("\n" + "="*65)
        print("  CONDITION: DES_PHASE_A_ONLY")
        print("="*65)
        DIR_PHASE_A_ONLY.mkdir(parents=True, exist_ok=True)
        for domain_id in domains:
            for seed_n in seeds:
                run_des_phase_a_only(domain_id, seed_n, resume=args.resume)

    if cond in ("DES_PHASE_A_B", "all"):
        print("\n" + "="*65)
        print("  CONDITION: DES_PHASE_A_B")
        print("="*65)
        DIR_PHASE_A_B.mkdir(parents=True, exist_ok=True)
        for domain_id in domains:
            for seed_n in seeds:
                run_des_phase_a_b(domain_id, seed_n, resume=args.resume)

    if cond in ("COT_PREMIUM", "all"):
        print("\n" + "="*65)
        print("  CONDITION: COT_PREMIUM")
        print("="*65)
        DIR_COT_PREMIUM.mkdir(parents=True, exist_ok=True)
        for domain_id in domains:
            for seed_n in seeds:
                run_cot_premium_single(domain_id, seed_n, resume=args.resume)

    if cond in ("judge", "all"):
        print("\n" + "="*65)
        print("  JUDGE EVALUATION")
        print("="*65)
        run_judge_batch(domains, seeds, resume=args.resume)

    print("\nAll done.")


if __name__ == "__main__":
    main()

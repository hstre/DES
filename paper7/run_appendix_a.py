"""
paper7/run_appendix_a.py
Paper 7 — Appendix A: EHL Isolation Experiment.

Three conditions × 5 domains × 3 seeds = 45 runs.

CONDITIONS:
  EHL_1.00 — no decay, no SPL  (within-experiment baseline)
  EHL_0.90 — EHL decay=0.90, no SPL  (temporal attractor test)
  SPL_only — SPL detect+escape (epsilon=0.25), no EHL  (geometric attractor test)

Hypothesis verdict:
  EHL_0.90 > SPL_only → temporal attractor dominates
  SPL_only > EHL_0.90 → geometric attractor dominates
  both > EHL_1.00     → mechanisms act independently

WP2 (Rentschler 2026) — Appendix A.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from openai import OpenAI

from paper5.spl_wrapper import (
    compute_claim_metrics,
    detect_attractor_in_claims,
    project as spl_project,
    select_escape_vector,
)
from paper7.ehl import EpistemicHalfLife

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 50
MAX_ITER_PER_RUN   = 40

RESULTS_DIR = Path("paper7/batch_results_appendix_a")
STATE_SRC   = Path("des_state.json")

DOMAINS = {
    "R01": "Does raising the minimum wage increase unemployment?",
    "R02": "Is remote work more productive than office work?",
    "R03": "Does immigration reduce wages for native workers?",
    "R04": "Is GDP a valid proxy for human wellbeing?",
    "R05": "Is intermittent fasting effective for long-term weight loss?",
}

# Paper 4 loop depths for R01-R05 (historical reference, from paper5 runner)
P4_BASELINES = {"R01": 2, "R02": 3, "R03": 4, "R04": 3, "R05": 4}

CONDITIONS = {
    "EHL_1.00": {"ehl": 1.00, "spl": False},
    "EHL_0.90": {"ehl": 0.90, "spl": False},
    "SPL_only": {"ehl": 1.00, "spl": True},
}

SEEDS = [101, 202, 303]

SPL_EPSILON   = 0.25
SPL_K_THRESH  = 0.55

# Escape generation prompt (Paper 5 v0.5)
ESCAPE_PROMPT = """\
Current research question: {question}
Attractor centroid (dominant relational patterns): {top_relations}
(The last DES run produced claims clustering around these patterns.)

The current ClaimGraph has high semantic tension. Generate {k} research questions that:
1. Stay within the same domain ({domain})
2. Use DIFFERENT relational structures than the dominant patterns above
3. Would be likely to produce empirically novel claims not yet in the graph

Return ONLY: {k} research questions, one per line, no numbering."""

des_module  = None
or_client_g = None


# ---------------------------------------------------------------------------
# Client init
# ---------------------------------------------------------------------------

def _init_clients():
    global des_module, or_client_g
    import des as des_module_local
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError("DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set.")
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                         "X-Title": "DES Paper7 AppendixA"},
    )
    des_module_local._clients["deepseek"]   = ds4
    des_module_local._clients["openrouter"] = orr
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER
    des_module  = des_module_local
    or_client_g = orr


def call_llm(prompt: str, max_tokens: int = 400, temperature: float = 0.7) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=min(temperature, 2.0),
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


# ---------------------------------------------------------------------------
# Helpers (inlined — do not import from run_p7.py to avoid side effects)
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set:
    STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to", "for",
            "and", "or", "but", "not", "with", "by", "from", "that", "this", "it",
            "be", "as", "at", "on", "if", "its", "so", "do", "can", "will",
            "how", "what", "why", "does", "when", "where"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def _claim_text(c: dict) -> str:
    return f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()


def token_overlap(a: str, b: str) -> float:
    ta, tb = set(a.lower().split()), set(b.lower().split())
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


def infer_method_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("evidence", "study", "studies", "data", "research", "empirical")):
        return "empirical_evidence"
    if any(w in q for w in ("mechanism", "why", "how does", "cause", "because")):
        return "causal_mechanism"
    if any(w in q for w in ("when", "temporal", "over time", "change", "trend")):
        return "temporal_validity"
    if any(w in q for w in ("define", "unit", "measure", "concept", "what is")):
        return "unit_of_analysis"
    return "conceptual_framing"


def infer_frame_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("effective", "work", "improve", "benefit", "harm", "impact")):
        return "effectiveness"
    if any(w in q for w in ("why", "mechanism", "process", "path", "through")):
        return "mechanism"
    if any(w in q for w in ("who", "context", "condition", "where", "population")):
        return "boundary_condition"
    return "descriptive"


def method_diversity_score(trace: list) -> float:
    if len(trace) < 2:
        return 1.0
    return len(set(trace)) / len(trace)


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
        "frame_type":                infer_frame_type(question),
        "claim_curvature":           spl_m["claim_curvature"],
        "claim_count":               spl_m["claim_count"],
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
    if (len(method_trace) >= 5
            and method_diversity_score(method_trace[-5:]) < 0.30):
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


def derive_question_from_claim(claim: dict) -> str:
    base = _claim_text(claim).strip()
    if claim.get("status") == "disputed":
        return f"Is there a resolution to the contradiction that {base}?"
    if not claim.get("evidence_refs"):
        return f"What evidence supports or refutes the claim that {base}?"
    return f"What are the broader implications of the claim that {base}?"


# ---------------------------------------------------------------------------
# SPL escape generation + validation (Paper 5 v0.5 config)
# ---------------------------------------------------------------------------

def _generate_escape_candidates(question: str, attractor_centroid: dict,
                                 seed_question: str, k: int = 5) -> list:
    top_relations = sorted(attractor_centroid.items(), key=lambda x: -x[1])[:3]
    top_rel_str   = ", ".join(f"{r}({p:.2f})" for r, p in top_relations)
    domain        = seed_question[:60]
    prompt = ESCAPE_PROMPT.format(
        question=question, top_relations=top_rel_str, k=k, domain=domain)
    raw  = call_llm(prompt, max_tokens=600)
    cands = [line.strip() for line in raw.split("\n")
             if line.strip() and len(line.strip()) > 20]
    return cands[:k]


def _validate_escape(question: str, state: dict, question_history: list) -> tuple:
    claims = state.get("claims", {})
    for prior in question_history:
        if token_overlap(question, prior) > 0.70:
            return False, "circular"
    graph_terms: set = set()
    for c in claims.values():
        for f in ("subject", "predicate", "object"):
            graph_terms.update(_tokens(c.get(f, "")))
    if not (graph_terms & _tokens(question)):
        return False, "unanchored"
    for c in claims.values():
        if c.get("sealed") and token_overlap(question, _claim_text(c)) > 0.60:
            return False, "reopens_sealed"
    return True, "admitted"


def _check_spl_trigger(state: dict, next_q: str, loop_metrics: list, current: dict) -> tuple:
    """
    SPL trigger hierarchy (Paper 5 v0.5 primary + fallback only).
    Returns (triggered, reason, spl_ctx).
    """
    # PRIMARY: claim-level attractor detection
    detected, reason, ctx = detect_attractor_in_claims(
        state, next_q, epsilon=SPL_EPSILON, k_threshold=SPL_K_THRESH)
    if detected:
        return True, reason, ctx

    # FALLBACK: content redundancy
    if current.get("semantic_duplication_rate", 0) > 0.40:
        return True, "content_redundancy>0.40", {}

    # FALLBACK: novelty_zero_x3
    last3 = loop_metrics[-3:] if len(loop_metrics) >= 3 else []
    if len(last3) == 3 and all(m.get("novel_claims", 0) == 0 for m in last3):
        return True, "novelty_zero_x3", {}

    return False, "", {}


# ---------------------------------------------------------------------------
# Per-run main loop
# ---------------------------------------------------------------------------

def run_domain_appendix_a(
    domain_id: str,
    seed_question: str,
    condition_name: str,
    condition: dict,
    rng_seed: int,
) -> dict:
    import random
    random.seed(rng_seed)

    ehl_factor = condition["ehl"]
    use_spl    = condition["spl"]
    ehl        = EpistemicHalfLife(decay_factor=ehl_factor) if ehl_factor < 1.00 else None

    run_dir = RESULTS_DIR / f"{domain_id}_{condition_name}_seed{rng_seed}"
    run_dir.mkdir(parents=True, exist_ok=True)

    question         = seed_question
    question_history = [seed_question]
    method_trace     = []
    loop_metrics     = []
    all_prior_texts  = []
    ehl_log          = []
    spl_log          = []
    failure_code     = None
    loop0_prompt_hash: str | None = None
    loop0_claim_hash:  str | None = None
    loop0_projection:  dict | None = None

    print(f"\n{'='*65}")
    print(f"  {domain_id} [{condition_name}|seed{rng_seed}] "
          f"ehl={ehl_factor} spl={use_spl}")
    print(f"  Seed: {seed_question[:60]}")
    print(f"{'='*65}")

    loop = 0
    while loop < MAX_LOOPS:
        loop_file = run_dir / f"loop_{loop:03d}_state.json"

        # Resume from existing file
        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = seed_question
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            method_trace.append(metrics["method_type"])
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            if ehl:
                ehl_log.append(ehl.loop_snapshot(state.get("claims", {}), loop))
            if loop == 0:
                loop0_projection = spl_project(seed_question)
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
            failure_code = "DES_RUN_ERROR"
            break

        if not STATE_SRC.exists():
            print(f"  ERROR: des_state.json missing after loop {loop}")
            failure_code = "DES_RUN_ERROR"
            break

        with open(STATE_SRC) as f:
            state = json.load(f)
        shutil.copy(STATE_SRC, loop_file)
        state["seed_question"] = seed_question

        if loop == 0:
            loop0_prompt_hash = hashlib.sha256(question.encode()).hexdigest()[:16]
            claim_texts = sorted(_claim_text(c) for c in state.get("claims", {}).values())
            loop0_claim_hash = hashlib.sha256("\n".join(claim_texts).encode()).hexdigest()[:16]
            loop0_projection = spl_project(seed_question)
            print(f"  [audit] loop0_prompt_hash={loop0_prompt_hash} "
                  f"loop0_claim_hash={loop0_claim_hash}")

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        method_trace.append(metrics["method_type"])

        dup_str  = f"{metrics['semantic_duplication_rate']:.0%}"
        novel_str = metrics["novel_claims"]
        print(f"  -> dup={dup_str} novel={novel_str} entropy={metrics['entropy']:.2f} "
              f"claims={metrics['total_claims']} K(G)={metrics['claim_curvature']:.3f}")

        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        if ehl:
            ehl_log.append(ehl.loop_snapshot(state.get("claims", {}), loop))
            if ehl.check_odc(loop_metrics):
                print(f"  ODC detected at loop {loop}")
                loop_metrics.append(metrics)
                failure_code = "ODC"
                break

        failure = check_failure(metrics, loop_metrics, method_trace)
        if failure:
            print(f"  FAILURE: {failure}")
            loop_metrics.append(metrics)
            failure_code = failure
            break

        loop_metrics.append(metrics)

        # ----------------------------------------------------------------
        # Question selection with condition-specific logic
        # ----------------------------------------------------------------

        next_q = select_next_question(state, question_history)
        if next_q == "LOOP_COMPLETE":
            print(f"  LOOP_COMPLETE at loop {loop}")
            break

        if use_spl:
            # SPL trigger check (Paper 5 v0.5 primary + fallback)
            triggered, trigger_reason, spl_ctx = _check_spl_trigger(
                state, next_q, loop_metrics[:-1], metrics)

            if triggered:
                print(f"  [SPL] trigger={trigger_reason} at loop {loop}")
                attractor_c = spl_ctx.get("claim_centroid", {})
                if not attractor_c:
                    # fallback trigger — use current claim centroid
                    from paper5.spl_wrapper import compute_claim_metrics as _ccm
                    attractor_c = _ccm(state).get("claim_centroid", {})

                escape_dist = 0.0
                escape_q    = ""
                score_ctx   = {}
                try:
                    cands = _generate_escape_candidates(
                        question, attractor_c, seed_question, k=5)
                    if cands:
                        escape_q, score_ctx = select_escape_vector(
                            cands, attractor_c, state, loop0_projection)
                        escape_dist = score_ctx.get("escape_distance", 0.0)
                        print(f"  [SPL] {len(cands)} candidates, best dist={escape_dist:.3f}")
                except Exception as e:
                    print(f"  [SPL] escape generation failed: {e}")

                admitted, reason = (False, "generation_failed") if not escape_q else \
                    _validate_escape(escape_q, state, question_history)

                spl_event = {
                    "loop":           loop,
                    "trigger":        trigger_reason,
                    "escape_distance": escape_dist,
                    "composite_score": score_ctx.get("composite_score", 0.0),
                    "generated_question": escape_q,
                    "admitted":       admitted,
                    "rejection_reason": None if admitted else reason,
                    "novelty_produced_next_loop": None,  # backfilled below
                    "ehl_seed":       ehl._last_seed if ehl else None,
                }
                spl_log.append(spl_event)

                if admitted:
                    print(f"  [SPL] admitted: {escape_q[:70]}")
                    question = escape_q
                    question_history.append(question)
                    loop += 1
                    continue
                else:
                    print(f"  [SPL] rejected ({reason}) — using standard next_q")

        elif ehl:
            # EHL weighted selection
            claims  = state.get("claims", {})
            weighted = ehl.weighted_select(
                claims, loop,
                criterion=lambda c: (not c.get("sealed")
                                     and c.get("status") == "supported"),
            )
            if weighted:
                cid, claim = weighted[0]
                next_q = derive_question_from_claim(claim)
                print(f"  [EHL] weighted select → {next_q[:70]} (seed={ehl._last_seed})")

        question = next_q
        question_history.append(question)
        loop += 1

    # Backfill SPL novelty_produced_next_loop
    for event in spl_log:
        if event.get("admitted"):
            el = event["loop"]
            nxt = [m for m in loop_metrics if m["loop"] > el]
            if nxt:
                event["novelty_produced_next_loop"] = nxt[0]["novel_claims"]

    if not failure_code:
        failure_code = "MAX_LOOPS_REACHED" if loop >= MAX_LOOPS else "LOOP_COMPLETE"

    return _save_result(
        run_dir=run_dir,
        domain_id=domain_id,
        condition_name=condition_name,
        seed_question=seed_question,
        condition=condition,
        outcome=failure_code,
        loop_metrics=loop_metrics,
        ehl_log=ehl_log,
        spl_log=spl_log,
        question_history=question_history,
        rng_seed=rng_seed,
        loop0_prompt_hash=loop0_prompt_hash,
        loop0_claim_hash=loop0_claim_hash,
    )


def _save_result(run_dir, domain_id, condition_name, seed_question, condition,
                 outcome, loop_metrics, ehl_log, spl_log, question_history,
                 rng_seed, loop0_prompt_hash, loop0_claim_hash) -> dict:
    loops_completed = len(loop_metrics)

    spl_events = len([e for e in spl_log if e.get("admitted")])
    spl_rejected = len([e for e in spl_log if not e.get("admitted")])

    outcome_data = {
        "domain_id":         domain_id,
        "condition":         condition_name,
        "ehl_factor":        condition["ehl"],
        "spl_enabled":       condition["spl"],
        "seed_question":     seed_question,
        "rng_seed":          rng_seed,
        "outcome":           outcome,
        "loops_completed":   loops_completed,
        "p4_baseline":       P4_BASELINES.get(domain_id),
        "loop0_prompt_hash": loop0_prompt_hash,
        "loop0_claim_hash":  loop0_claim_hash,
        "spl_events_admitted": spl_events,
        "spl_events_rejected": spl_rejected,
    }

    with open(run_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    with open(run_dir / "ehl_log.json", "w") as f:
        json.dump(ehl_log, f, indent=2)
    with open(run_dir / "spl_log.json", "w") as f:
        json.dump(spl_log, f, indent=2)

    p4 = P4_BASELINES.get(domain_id, "?")
    print(f"\n  {domain_id}/{condition_name}/seed{rng_seed}: "
          f"{outcome} | loops={loops_completed} | P4={p4} | "
          f"SPL_admitted={spl_events} | EHL={condition['ehl']}")
    return outcome_data


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_all(domain_ids=None, condition_names=None, seeds=None):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    domain_ids     = domain_ids or list(DOMAINS.keys())
    condition_names = condition_names or list(CONDITIONS.keys())
    seeds          = seeds or SEEDS

    all_results = []

    for domain_id in domain_ids:
        if domain_id not in DOMAINS:
            print(f"Unknown domain: {domain_id}")
            continue
        for cname in condition_names:
            if cname not in CONDITIONS:
                print(f"Unknown condition: {cname}")
                continue
            for seed in seeds:
                outcome_path = RESULTS_DIR / f"{domain_id}_{cname}_seed{seed}" / "outcome.json"
                if outcome_path.exists():
                    with open(outcome_path) as f:
                        r = json.load(f)
                    print(f"  [skip] {domain_id}/{cname}/seed{seed} "
                          f"— {r['outcome']} ({r['loops_completed']} loops)")
                    all_results.append(r)
                    continue
                r = run_domain_appendix_a(
                    domain_id=domain_id,
                    seed_question=DOMAINS[domain_id],
                    condition_name=cname,
                    condition=CONDITIONS[cname],
                    rng_seed=seed,
                )
                all_results.append(r)
                time.sleep(2)

    write_summary(all_results)
    return all_results


# ---------------------------------------------------------------------------
# Summary + hypothesis verdict
# ---------------------------------------------------------------------------

def write_summary(all_results: list):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Index results by (domain, condition, seed)
    idx: dict = {}
    for r in all_results:
        key = (r["domain_id"], r["condition"], r["rng_seed"])
        idx[key] = r

    # Compute within-experiment depth_lift vs EHL_1.00 per (domain, seed)
    rows = []
    for r in all_results:
        d, c, s = r["domain_id"], r["condition"], r["rng_seed"]
        base = idx.get((d, "EHL_1.00", s))
        base_loops = base["loops_completed"] if base else None
        depth_lift = (r["loops_completed"] - base_loops) if (base_loops is not None and c != "EHL_1.00") else None
        rows.append({
            **r,
            "depth_lift_vs_ehl100": depth_lift,
        })

    # Per-condition means (excluding EHL_1.00 baseline)
    def mean_lift(condition):
        vals = [r["depth_lift_vs_ehl100"] for r in rows
                if r["condition"] == condition and r["depth_lift_vs_ehl100"] is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    def mean_loops(condition):
        vals = [r["loops_completed"] for r in rows if r["condition"] == condition]
        return round(sum(vals) / len(vals), 3) if vals else None

    def pct_positive(condition):
        vals = [r["depth_lift_vs_ehl100"] for r in rows
                if r["condition"] == condition and r["depth_lift_vs_ehl100"] is not None]
        return round(sum(1 for v in vals if v > 0) / len(vals), 3) if vals else None

    ehl090_mean_lift = mean_lift("EHL_0.90")
    spl_mean_lift    = mean_lift("SPL_only")
    ehl100_mean_loops = mean_loops("EHL_1.00")
    ehl090_mean_loops = mean_loops("EHL_0.90")
    spl_mean_loops    = mean_loops("SPL_only")

    # Hypothesis verdict
    if ehl090_mean_lift is not None and spl_mean_lift is not None:
        if ehl090_mean_lift > spl_mean_lift and ehl090_mean_lift > 0:
            if spl_mean_lift > 0:
                verdict = "BOTH_HELP_TEMPORAL_DOMINANT"
            else:
                verdict = "TEMPORAL_DOMINANT"
        elif spl_mean_lift > ehl090_mean_lift and spl_mean_lift > 0:
            if ehl090_mean_lift > 0:
                verdict = "BOTH_HELP_GEOMETRIC_DOMINANT"
            else:
                verdict = "GEOMETRIC_DOMINANT"
        elif ehl090_mean_lift > 0 and spl_mean_lift > 0:
            verdict = "BOTH_HELP_NO_CLEAR_DOMINANCE"
        elif ehl090_mean_lift <= 0 and spl_mean_lift <= 0:
            verdict = "NEITHER_HELPS"
        else:
            verdict = "MIXED"
    else:
        verdict = "INSUFFICIENT_DATA"

    # --- JSON report ---
    report = {
        "label": "Paper 7 Appendix A — EHL Isolation Experiment",
        "conditions": list(CONDITIONS.keys()),
        "domains": list(DOMAINS.keys()),
        "seeds": SEEDS,
        "n_runs": len(all_results),
        "p4_baselines": P4_BASELINES,
        "per_condition": {
            "EHL_1.00": {"mean_loops": ehl100_mean_loops, "mean_depth_lift_vs_ehl100": None},
            "EHL_0.90": {"mean_loops": ehl090_mean_loops, "mean_depth_lift_vs_ehl100": ehl090_mean_lift,
                         "pct_positive": pct_positive("EHL_0.90")},
            "SPL_only": {"mean_loops": spl_mean_loops, "mean_depth_lift_vs_ehl100": spl_mean_lift,
                         "pct_positive": pct_positive("SPL_only")},
        },
        "hypothesis_verdict": verdict,
        "verdict_interpretation": {
            "TEMPORAL_DOMINANT":           "EHL_0.90 > SPL_only > 0: temporal attractor dominates",
            "GEOMETRIC_DOMINANT":          "SPL_only > EHL_0.90 > 0: geometric attractor dominates",
            "BOTH_HELP_TEMPORAL_DOMINANT": "Both > EHL_1.00, EHL_0.90 > SPL_only",
            "BOTH_HELP_GEOMETRIC_DOMINANT": "Both > EHL_1.00, SPL_only > EHL_0.90",
            "BOTH_HELP_NO_CLEAR_DOMINANCE": "Both > EHL_1.00, no clear ranking",
            "NEITHER_HELPS":               "Neither EHL_0.90 nor SPL_only improves on EHL_1.00",
            "MIXED":                       "One helps, one does not",
        }.get(verdict, verdict),
        "rows": rows,
    }
    json_path = RESULTS_DIR / "appendix_a_results.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # --- Markdown summary ---
    lines = [
        "# Paper 7 — Appendix A: EHL Isolation Experiment",
        "",
        "**Conditions:** EHL_1.00 (P4 baseline) | EHL_0.90 (temporal) | SPL_only (geometric)",
        f"**Domains:** {', '.join(DOMAINS.keys())} | **Seeds:** {SEEDS}",
        f"**Total runs:** {len(all_results)} (target: 45)",
        "",
        "---",
        "",
        "## Aggregate Comparison",
        "",
        "| Condition | Mean loops | Mean depth_lift vs EHL_1.00 | % runs positive |",
        "|-----------|------------|----------------------------|-----------------|",
        f"| EHL_1.00  | {ehl100_mean_loops} | — (baseline) | — |",
        f"| EHL_0.90  | {ehl090_mean_loops} | {ehl090_mean_lift} | {pct_positive('EHL_0.90')} |",
        f"| SPL_only  | {spl_mean_loops} | {spl_mean_lift} | {pct_positive('SPL_only')} |",
        "",
        f"**EHL_0.90 vs SPL_only:** "
        f"{'+' if (ehl090_mean_lift or 0) >= (spl_mean_lift or 0) else ''}"
        f"{round((ehl090_mean_lift or 0) - (spl_mean_lift or 0), 3)} loops difference",
        "",
        "---",
        "",
        "## Hypothesis Verdict",
        "",
        f"**{verdict}**",
        "",
        "- If EHL_0.90 > SPL_only: temporal attractor is dominant mechanism",
        "- If SPL_only > EHL_0.90: geometric attractor is dominant mechanism",
        "- If both > EHL_1.00: mechanisms act independently",
        "",
        "---",
        "",
        "## Per-Run Results",
        "",
        "| Domain | Condition | Seed | Loops | P4 | depth_lift_vs_EHL100 | Outcome | SPL_admitted |",
        "|--------|-----------|------|-------|----|----------------------|---------|--------------|",
    ]
    for r in sorted(rows, key=lambda x: (x["domain_id"], x["condition"], x["rng_seed"])):
        dl = r.get("depth_lift_vs_ehl100")
        dl_str = f"+{dl}" if dl and dl > 0 else str(dl) if dl is not None else "—"
        lines.append(
            f"| {r['domain_id']} | {r['condition']} | {r['rng_seed']} "
            f"| {r['loops_completed']} | {r.get('p4_baseline','?')} "
            f"| {dl_str} | {r['outcome']} "
            f"| {r.get('spl_events_admitted', 0)} |"
        )

    # Per-domain comparison table
    lines += [
        "",
        "---",
        "",
        "## Per-Domain Three-Way Comparison (mean across 3 seeds)",
        "",
        "| Domain | P4 baseline | EHL_1.00 mean | EHL_0.90 mean | SPL_only mean | EHL_0.90 lift | SPL_only lift |",
        "|--------|-------------|---------------|---------------|---------------|---------------|---------------|",
    ]
    for domain_id in DOMAINS:
        p4 = P4_BASELINES.get(domain_id, "?")
        def dmean(c):
            vals = [r["loops_completed"] for r in rows
                    if r["domain_id"] == domain_id and r["condition"] == c]
            return round(sum(vals) / len(vals), 2) if vals else None

        def dlift(c):
            vals = [r["depth_lift_vs_ehl100"] for r in rows
                    if r["domain_id"] == domain_id and r["condition"] == c
                    and r["depth_lift_vs_ehl100"] is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        m100 = dmean("EHL_1.00")
        m090 = dmean("EHL_0.90")
        mspl = dmean("SPL_only")
        l090 = dlift("EHL_0.90")
        lspl = dlift("SPL_only")
        lines.append(f"| {domain_id} | {p4} | {m100} | {m090} | {mspl} "
                     f"| {('+' if l090 and l090>0 else '')}{l090} "
                     f"| {('+' if lspl and lspl>0 else '')}{lspl} |")

    lines += [
        "",
        "---",
        "",
        "## Notes",
        "",
        "- depth_lift_vs_EHL100: loops_completed − EHL_1.00_loops for same (domain, seed).",
        "- P4 baseline: historical Paper 4 depths for reference only (different run conditions).",
        "- SPL_only uses Paper 5 v0.5 config: detect_attractor_in_claims (epsilon=0.25,",
        "  k_threshold=0.55), select_escape_vector composite formula.",
        "  Secondary heuristic triggers from paper5 (frame_repeat, metric_repeat) omitted.",
        "  content_redundancy>0.40 and novelty_zero_x3 fallbacks included.",
        "- EHL affects claim selection weight only — does NOT modify DES state confidence.",
        "- Seeds: Python RNG seeded per run. LLM non-determinism not controlled.",
        "- Thresholds and DES internals unchanged.",
    ]

    md_path = RESULTS_DIR / "summary.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nAppendix A summary: {md_path}")
    print(f"JSON:               {json_path}")
    print(f"\nVerdict: {verdict}")
    print(f"EHL_0.90 mean depth_lift={ehl090_mean_lift} | SPL_only mean depth_lift={spl_mean_lift}")
    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Paper 7 Appendix A — EHL isolation")
    parser.add_argument("--domain",    type=str, help="Single domain ID (e.g. R01)")
    parser.add_argument("--domains",   nargs="+", help="Multiple domain IDs")
    parser.add_argument("--condition", type=str, choices=list(CONDITIONS.keys()),
                        help="Single condition")
    parser.add_argument("--conditions", nargs="+", choices=list(CONDITIONS.keys()),
                        help="Multiple conditions")
    parser.add_argument("--seed",      type=int, choices=SEEDS, help="Single seed")
    parser.add_argument("--seeds",     nargs="+", type=int, help="Multiple seeds")
    parser.add_argument("--summary-only", action="store_true",
                        help="Regenerate summary from existing results only")
    args = parser.parse_args()

    if args.summary_only:
        # Collect existing results and regenerate summary
        results = []
        for p in sorted(RESULTS_DIR.glob("*/outcome.json")):
            with open(p) as f:
                results.append(json.load(f))
        if not results:
            print("No existing results found.")
            return
        write_summary(results)
        return

    _init_clients()

    domain_ids      = args.domains or ([args.domain] if args.domain else list(DOMAINS.keys()))
    condition_names = args.conditions or ([args.condition] if args.condition else list(CONDITIONS.keys()))
    seeds           = args.seeds or ([args.seed] if args.seed else SEEDS)

    run_all(domain_ids=domain_ids, condition_names=condition_names, seeds=seeds)


if __name__ == "__main__":
    main()

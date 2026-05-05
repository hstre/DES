"""
paper6/run_phase2.py
Phase 2: Prospective prediction — 13 new domains (10 core + 3 counterexamples).
Protocol:
  1. Compute pre-run SH estimate via 10-claim domain probe (LLM-generated)
  2. Run DES P4 config (no perturbation, max 20 loops)
  3. Compute post-loop-0 SH from actual ClaimGraph
  4. Record loop depth and termination outcome
  5. Compare pre-run estimate vs post-loop-0 SH (H3)

No perturbation in Phase 2. Clean SH → depth measurement.
WP2 (Rentschler 2026).
"""

import json, math, os, re, shutil, sys, time
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper6.compute_sh import compute_semantic_headroom, compute_sh_from_projections
from paper6.compute_sh import get_spl

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 20
MAX_ITER_PER_RUN   = 40

# SH* locked from Phase 1 — must not be recalibrated after Phase 2 results are known.
# Phase 1 accuracy (5/5) is training accuracy on n=5.
# Phase 2 accuracy is true prediction accuracy. Report separately, never conflate.
SH_STAR_LOCKED = 0.0876
SH_STAR = SH_STAR_LOCKED  # alias for internal use

# Pre-registered domain classifications (before any runs)
DOMAINS = {
    # HIGH SH expected (broad conceptual scope)
    "N01": {
        "seed": "Is consciousness reducible to physical brain processes?",
        "predicted_sh": "HIGH",
    },
    "N02": {
        "seed": "What determines the rise and fall of civilizations?",
        "predicted_sh": "HIGH",
    },
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "predicted_sh": "HIGH",
    },
    "N04": {
        "seed": "What is the relationship between language and thought?",
        "predicted_sh": "HIGH",
    },
    "N05": {
        "seed": "Does economic inequality harm social cohesion?",
        "predicted_sh": "HIGH",
    },
    # LOW SH expected (narrow empirical scope)
    "N06": {
        "seed": "Does aspirin reduce cardiovascular event risk in healthy adults?",
        "predicted_sh": "LOW",
    },
    "N07": {
        "seed": "Does sleep deprivation impair working memory?",
        "predicted_sh": "LOW",
    },
    "N08": {
        "seed": "Do smaller class sizes improve standardized test scores?",
        "predicted_sh": "LOW",
    },
    "N09": {
        "seed": "Does caffeine improve short-term cognitive performance?",
        "predicted_sh": "LOW",
    },
    "N10": {
        "seed": "Do higher minimum wages reduce employment in fast food?",
        "predicted_sh": "LOW",
    },
    # Counterexample domains (test topic-ambiguity confound)
    "N11": {
        "seed": "What are the climate tipping points for irreversible warming?",
        "predicted_sh": "HIGH",  # empirical but contested, multiple mechanisms
    },
    "N12": {
        "seed": "Does gut microbiome diversity affect depression outcomes?",
        "predicted_sh": "HIGH",  # empirical but HIGH SH
    },
    "N13": {
        "seed": "Is the trolley problem resolved under strict utilitarian rules?",
        "predicted_sh": "LOW",   # philosophical but constrained answer space
    },
}

RESULTS_DIR = Path("paper6/phase2_results")
STATE_SRC   = Path("des_state.json")

des_module  = None
or_client_g = None


# ---------------------------------------------------------------------------
# Helpers (same as P4 runner)
# ---------------------------------------------------------------------------

def _make_clients():
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError(
            "DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set.\n"
            "  export DEEPSEEK_API_KEY=sk-...\n"
            "  export OPENROUTER_API_KEY=sk-or-..."
        )
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                         "X-Title": "DES Paper6 Phase2"},
    )
    return ds4, orr


def _tokens(text: str) -> set:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for",
            "and","or","but","not","with","by","from","that","this","it",
            "be","as","at","on","if","its","so","do","can","will"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def _claim_text(c: dict) -> str:
    return f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()


def _token_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def count_redundant(claims: dict) -> int:
    texts = [_claim_text(c) for c in claims.values()]
    count = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if _token_overlap(texts[i], texts[j]) > 0.70:
                count += 1
                break
    return count


def count_novel(claims: dict, prior_texts: list) -> int:
    if not prior_texts:
        return len(claims)
    novel = 0
    for c in claims.values():
        txt = _claim_text(c)
        if all(_token_overlap(txt, p) < 0.30 for p in prior_texts):
            novel += 1
    return novel


def epistemic_priority(c: dict, all_claims: dict) -> int:
    history = c.get("history", [])
    bases = [h.split("[")[0] for h in history]
    return bases.count("T1") + bases.count("T5") + (1 if not c.get("evidence_refs") else 0)


def is_exponential(seq: list) -> bool:
    if len(seq) < 4:
        return False
    nonzero = [x for x in seq if x > 0]
    if len(nonzero) < 4:
        return False
    ratios = [nonzero[i + 1] / nonzero[i] for i in range(len(nonzero) - 1)]
    return all(r >= 1.5 for r in ratios[-3:])


def extract_run_result(state: dict, prev_total: int) -> dict:
    claims = state.get("claims", {})
    total = len(claims)
    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))
    return {
        "new_claims_this_loop": max(total - prev_total, 0),
        "literature_derived": 0,
        "branches_created": sum(1 for c in claims.values()
                                if c.get("id", "").startswith("B")),
        "syntheses_produced": sum(1 for c in claims.values()
                                  if c.get("is_synthesis", False)),
        "counter_hypotheses": all_bases.count("T5"),
        "evidence_found": all_bases.count("T3") + all_bases.count("T6"),
        "contradictions_generated": all_bases.count("T2"),
        "contradictions_resolved": sum(1 for c in claims.values()
                                       if c.get("is_synthesis", False)),
        "total_contradictions": max(all_bases.count("T5"), 1),
    }


def compute_metrics(state: dict, loop_number: int, prior_texts: list,
                    run_result: dict) -> dict:
    claims = state.get("claims", {})
    total = len(claims)
    open_c = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel = count_novel(claims, prior_texts)
    lit_derived = run_result.get("literature_derived", 0)
    new_claims = run_result.get("new_claims_this_loop", max(total, 1))
    qutil = sum(run_result.get(k, 0) * w for k, w in [
        ("contradictions_generated", 3), ("syntheses_produced", 2),
        ("counter_hypotheses", 2), ("evidence_found", 1), ("branches_created", 1),
    ])

    # SH metrics for this loop
    sh_result = compute_semantic_headroom.__module__ and None  # computed separately

    return {
        "loop": loop_number,
        "total_claims": total,
        "open_claims": open_c,
        "sealed_claims": total - open_c,
        "disputed_claims": disputed,
        "redundant_claims": redundant,
        "entropy": (open_c + disputed + redundant) / max(total, 1),
        "novel_claims": novel,
        "contradictions_resolved": run_result.get("contradictions_resolved", 0),
        "total_contradictions": run_result.get("total_contradictions", 1),
        "branch_growth": run_result.get("branches_created", 0),
        "lit_rate": lit_derived / max(new_claims, 1),
        "question_utility": float(qutil),
    }


def check_failure_conditions(current: dict, history: list) -> str | None:
    last5 = history[-5:] if len(history) >= 5 else history
    last10 = history[-10:] if len(history) >= 10 else history

    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"
    if current["total_claims"] > 0 and \
       current["redundant_claims"] / current["total_claims"] > 0.60:
        return "SEMANTIC_DUPLICATION"
    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"
    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"
    if len(last10) == 10 and all(m.get("lit_rate", 0) > 0.90 for m in last10):
        return "EXTERNAL_ANCHOR_CAPTURE"
    if len(history) >= 10:
        if is_exponential([m["branch_growth"] for m in history[-10:]]):
            return "BRANCH_EXPLOSION"
    return None


def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q: str) -> bool:
        return any(_token_overlap(q, h) > 0.75 for h in question_history)

    def make_question(c: dict, prefix: str = "") -> str:
        base = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()
        return f"{prefix}: {base}?" if prefix else f"What is the evidence that {base}?"

    open_claims = sorted(
        [c for c in claims.values()
         if not c.get("sealed", False) and c.get("id", "").startswith("C")],
        key=lambda c: epistemic_priority(c, claims), reverse=True,
    )
    for c in open_claims:
        q = make_question(c)
        if not already_asked(q):
            return q

    weak_ev = [c for c in claims.values()
               if c.get("sealed", False) and not c.get("evidence_refs")]
    for c in sorted(weak_ev, key=lambda c: c.get("confidence", 0)):
        q = make_question(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    synth = sorted(
        [c for c in claims.values() if c.get("is_synthesis", False)],
        key=lambda c: c.get("confidence", 0), reverse=True,
    )
    for c in synth:
        q = make_question(c, "Explore the implications of")
        if not already_asked(q):
            return q

    for c in [c for c in claims.values()
              if c.get("status") == "disputed"
              and "T1" in [h.split("[")[0] for h in c.get("history", [])]]:
        q = make_question(c, "Is there a resolution to the contradiction that")
        if not already_asked(q):
            return q

    if synth:
        q = make_question(max(synth, key=lambda c: c.get("confidence", 0)),
                          "Critically evaluate the synthesis that")
        if not already_asked(q):
            return q

    return "LOOP_COMPLETE"


# ---------------------------------------------------------------------------
# Pre-run SH estimation (H3)
# ---------------------------------------------------------------------------

DOMAIN_PROBE_PROMPT = """\
Domain question: {question}

Generate 10 diverse factual claims about this topic.
Claims should represent different aspects, perspectives, and sub-questions \
within this domain.

Return ONLY: 10 claims, one per line, as simple declarative sentences.
No hedging, no explanation, no numbering."""


def estimate_sh_prerun(question: str, k: int = 10) -> dict:
    """
    Estimate SH before running DES via 10-claim LLM domain probe.
    Returns same structure as compute_semantic_headroom.
    """
    global or_client_g
    try:
        resp = or_client_g.chat.completions.create(
            model=FALSIFIER_MODEL,
            messages=[{"role": "user",
                       "content": DOMAIN_PROBE_PROMPT.format(question=question)}],
            max_tokens=512,
            temperature=0.7,
        )
        raw = resp.choices[0].message.content or ""
        lines = [ln.strip().lstrip("0123456789.-) ")
                 for ln in raw.split("\n") if ln.strip() and len(ln.strip()) > 10][:k]
    except Exception as e:
        return {"sh": None, "reason": f"llm_error:{e}", "n_claims": 0}

    if len(lines) < 3:
        return {"sh": None, "reason": "too_few_probe_claims", "n_claims": len(lines),
                "probe_claims": lines}

    spl = get_spl()
    projections = [spl.project_text(ln).P_r for ln in lines]
    result = compute_sh_from_projections(projections)
    result["probe_claims"] = lines
    return result


# ---------------------------------------------------------------------------
# Core domain runner (P4 config — no perturbation)
# ---------------------------------------------------------------------------

def run_domain_p4(domain_id: str, seed_question: str,
                  predicted_sh: str,
                  sh_prerun: dict,
                  max_loops: int = MAX_LOOPS) -> dict:
    domain_dir = RESULTS_DIR / domain_id
    domain_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {domain_id} [{predicted_sh}]: {seed_question[:55]}")
    print(f"  Pre-run SH = {sh_prerun.get('sh')}  "
          f"(predicted: {predicted_sh}, SH* = {SH_STAR})")
    print(f"{'='*65}")

    question = seed_question
    question_history = [seed_question]
    loop_metrics = []
    all_prior_texts = []
    failure_code = None
    prev_total = 0
    sh_loop0 = None

    for loop in range(max_loops):
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d} — already complete")
            with open(loop_file) as f:
                state = json.load(f)
            rr = extract_run_result(state, 0)
            prior_texts = [_claim_text(c) for c in state.get("claims", {}).values()]
            m = compute_metrics(state, loop, all_prior_texts, rr)
            loop_metrics.append(m)
            all_prior_texts.extend(prior_texts)
            prev_total = len(state.get("claims", {}))
            if loop == 0:
                sh_loop0 = compute_semantic_headroom(str(loop_file))
            question = select_next_question(state, question_history)
            if question != "LOOP_COMPLETE":
                question_history.append(question)
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

        run_result = extract_run_result(state, prev_total)
        prior_texts = [_claim_text(c) for c in state.get("claims", {}).values()]
        m = compute_metrics(state, loop, all_prior_texts, run_result)

        # Compute SH after loop 0 (key Phase 2 measurement)
        if loop == 0:
            sh_loop0 = compute_semantic_headroom(str(loop_file))
            m["sh_loop0"] = sh_loop0.get("sh")
            m["sh_norm_loop0"] = sh_loop0.get("sh_norm")
            m["sh_entropy_loop0"] = sh_loop0.get("sh_entropy")
            m["sh_n_claims"] = sh_loop0.get("n_claims")
            print(f"  SH(loop0) = {sh_loop0.get('sh')}  "
                  f"SH_norm={sh_loop0.get('sh_norm')}  "
                  f"n={sh_loop0.get('n_claims')}")

        # Check failure
        failure = check_failure_conditions(m, loop_metrics)
        if failure:
            m["outcome"] = failure
            loop_metrics.append(m)
            loop_metrics[-1]["outcome"] = failure
            failure_code = failure
            print(f"  FAILURE: {failure}")
            break

        loop_metrics.append(m)
        all_prior_texts.extend(prior_texts)
        prev_total = len(state.get("claims", {}))

        # Select next question
        next_q = select_next_question(state, question_history)
        if next_q == "LOOP_COMPLETE":
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            break

        question = next_q
        question_history.append(question)

        dup_rate = m["redundant_claims"] / max(m["total_claims"], 1)
        novel = m["novel_claims"]
        print(f"  -> entropy={m['entropy']:.2f} | "
              f"claims={m['total_claims']} (open={m['open_claims']} "
              f"sealed={m['sealed_claims']}) | "
              f"novel={novel} dup={dup_rate:.0%} K(G)=n/a")

    loops_completed = len(loop_metrics)
    outcome = classify_outcome(loops_completed, max_loops, failure_code, loop_metrics)
    sh_actual = sh_loop0.get("sh") if sh_loop0 and sh_loop0.get("sh") is not None else None
    sh_predicted_class = predicted_sh
    sh_actual_class = (
        "HIGH" if (sh_actual is not None and sh_actual > SH_STAR) else
        "LOW" if sh_actual is not None else "UNKNOWN"
    )
    prediction_correct = (sh_predicted_class == sh_actual_class)

    print(f"\n  {domain_id} outcome: {outcome} | loops={loops_completed} | "
          f"SH={sh_actual} | predicted={sh_predicted_class} | "
          f"actual={sh_actual_class} | correct={prediction_correct}")

    result = {
        "domain_id": domain_id,
        "seed_question": seed_question,
        "predicted_sh_class": sh_predicted_class,
        "outcome": outcome,
        "loops_completed": loops_completed,
        "sh_prerun": {k: v for k, v in sh_prerun.items() if k != "probe_claims"},
        "sh_prerun_probe_claims": sh_prerun.get("probe_claims", []),
        "sh_loop0": sh_loop0 if sh_loop0 else {},
        "sh_actual_class": sh_actual_class,
        "sh_prediction_correct": prediction_correct,
        "loop_metrics": loop_metrics,
    }

    # Save outcome
    out_file = domain_dir / "outcome.json"
    slim = json.loads(json.dumps(result))
    if "sh_loop0" in slim and isinstance(slim["sh_loop0"], dict):
        slim["sh_loop0"].pop("centroid", None)
    with open(out_file, "w") as f:
        json.dump(slim, f, indent=2)

    return result


def classify_outcome(loops_completed: int, max_loops: int,
                     failure_code: str | None, loop_metrics: list) -> str:
    if failure_code:
        return failure_code
    if any(m.get("outcome") == "LOOP_COMPLETE" for m in loop_metrics):
        return "LOOP_COMPLETE"
    if loops_completed >= max_loops:
        last10 = loop_metrics[-10:]
        if (all(m["entropy"] < 0.80 for m in last10)
                and any(m["novel_claims"] > 0 for m in loop_metrics[10:])):
            return "H1_STABLE"
        return "H0_DEGENERATION"
    return "INCOMPLETE"


# ---------------------------------------------------------------------------
# Phase 2 main
# ---------------------------------------------------------------------------

def run_phase2(domains_filter: list = None):
    global des_module, or_client_g

    print("=" * 65)
    print("Paper 6 — Phase 2: Prospective SH Prediction")
    print(f"SH* = {SH_STAR} (from Phase 1)")
    print("=" * 65)

    ds4, orr = _make_clients()
    or_client_g = orr

    # Inject clients into DES module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import importlib
    import des
    des.builder_client = ds4
    des.falsifier_client = orr
    des_module = des

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    domains_to_run = {k: v for k, v in DOMAINS.items()
                      if domains_filter is None or k in domains_filter}

    all_results = {}
    for domain_id, info in domains_to_run.items():
        domain_dir = RESULTS_DIR / domain_id
        # Check if already complete
        out_file = domain_dir / "outcome.json"
        if out_file.exists():
            print(f"\n[skip] {domain_id} — outcome.json exists")
            with open(out_file) as f:
                all_results[domain_id] = json.load(f)
            continue

        # Step 1: pre-run SH estimation
        print(f"\nEstimating pre-run SH for {domain_id}...")
        sh_prerun = estimate_sh_prerun(info["seed"])
        print(f"  Pre-run SH = {sh_prerun.get('sh')}  n={sh_prerun.get('n_claims')}")

        # Save pre-run estimate immediately
        domain_dir.mkdir(parents=True, exist_ok=True)
        with open(domain_dir / "sh_prerun.json", "w") as f:
            slim = {k: v for k, v in sh_prerun.items() if k != "probe_claims"}
            slim["probe_claims"] = sh_prerun.get("probe_claims", [])
            json.dump(slim, f, indent=2)

        # Step 2-4: run DES P4
        result = run_domain_p4(
            domain_id=domain_id,
            seed_question=info["seed"],
            predicted_sh=info["predicted_sh"],
            sh_prerun=sh_prerun,
            max_loops=MAX_LOOPS,
        )
        all_results[domain_id] = result

    # Write phase 2 summary
    write_phase2_summary(all_results)
    return all_results


def write_phase2_summary(results: dict):
    from paper6.phase1_retrograde import spearman_rho, pearson_r

    out_path = Path("paper6/phase2_results/phase2_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sh_prerun_vals, sh_actual_vals = [], []
    depth_vals, sh_for_depth = [], []
    prediction_hits = 0
    total_predictions = 0

    rows = []
    for domain_id, r in sorted(results.items()):
        sh_pre = r.get("sh_prerun", {}).get("sh")
        sh_act = r.get("sh_loop0", {}).get("sh")
        depth = r.get("loops_completed")
        pred = r.get("predicted_sh_class")
        actual_cls = r.get("sh_actual_class")
        correct = r.get("sh_prediction_correct")

        if sh_pre is not None:
            sh_prerun_vals.append(sh_pre)
        if sh_act is not None:
            sh_actual_vals.append(sh_act)
            if depth is not None:
                depth_vals.append(depth)
                sh_for_depth.append(sh_act)
        if correct is not None:
            total_predictions += 1
            if correct:
                prediction_hits += 1

        rows.append({
            "domain": domain_id,
            "seed": r.get("seed_question", "")[:60],
            "predicted": pred,
            "sh_prerun": sh_pre,
            "sh_loop0": sh_act,
            "actual_class": actual_cls,
            "prediction_correct": correct,
            "loops": depth,
            "outcome": r.get("outcome"),
        })

    # H3: pre-run vs post-loop-0 SH correlation
    h3_rho = None
    if len(sh_prerun_vals) >= 3 and len(sh_actual_vals) >= 3:
        n = min(len(sh_prerun_vals), len(sh_actual_vals))
        h3_rho = spearman_rho(sh_prerun_vals[:n], sh_actual_vals[:n])

    # SH vs depth correlation
    rho_depth = spearman_rho(sh_for_depth, depth_vals) if len(sh_for_depth) >= 3 else None
    r_depth = pearson_r(sh_for_depth, depth_vals) if len(sh_for_depth) >= 3 else None

    pred_accuracy = prediction_hits / total_predictions if total_predictions > 0 else None

    summary = {
        "phase": 2,
        "n_domains": len(results),
        "sh_star_locked": SH_STAR_LOCKED,
        "sh_star_source": "Phase 1 retrograde n=5 — locked, not recalibrated",
        "correlations": {
            "sh_prerun_vs_sh_loop0_spearman": round(h3_rho, 4) if h3_rho else None,
            "sh_loop0_vs_depth_spearman": round(rho_depth, 4) if rho_depth else None,
            "sh_loop0_vs_depth_pearson": round(r_depth, 4) if r_depth else None,
        },
        "h3_verdict": (
            "CONFIRMED" if h3_rho and h3_rho > 0.70 else
            "WEAK" if h3_rho and h3_rho > 0.50 else
            "NOT_CONFIRMED" if h3_rho else "INSUFFICIENT_DATA"
        ),
        # Phase 2 accuracy = true prediction accuracy (SH* locked before these runs)
        # Phase 1 accuracy (5/5 = 100%) is training accuracy on n=5 — not reported here
        "phase2_prediction_accuracy": round(pred_accuracy, 3) if pred_accuracy else None,
        "phase2_prediction_hits": prediction_hits,
        "phase2_total_predictions": total_predictions,
        "phase1_training_accuracy_note": "5/5=100% on n=5 — training accuracy only, see phase1_retrograde.json",
        "rows": rows,
    }

    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print("\n" + "=" * 75)
    print("Phase 2 Summary")
    print("=" * 75)
    print(f"{'Domain':<6} {'Pred':<5} {'SH_pre':<8} {'SH_act':<8} "
          f"{'Cls':<5} {'OK?':<5} {'Loops':<6} {'Outcome'}")
    print("-" * 75)
    for row in rows:
        ok = "✓" if row["prediction_correct"] else ("✗" if row["prediction_correct"] is False else "?")
        print(f"{row['domain']:<6} {str(row['predicted']):<5} "
              f"{str(row['sh_prerun']):<8} {str(row['sh_loop0']):<8} "
              f"{str(row['actual_class']):<5} {ok:<5} "
              f"{str(row['loops']):<6} {row['outcome']}")

    print(f"\nH3 (pre-run ρ): {h3_rho:.3f}" if h3_rho else "\nH3: insufficient data")
    print(f"SH vs depth ρ: {rho_depth:.3f}" if rho_depth else "SH vs depth: insufficient data")
    print(f"Prediction accuracy: {prediction_hits}/{total_predictions} = "
          f"{pred_accuracy:.0%}" if pred_accuracy else "")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="+", help="Run specific domains only")
    args = parser.parse_args()
    run_phase2(domains_filter=args.domains)

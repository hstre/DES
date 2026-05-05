"""
Paper 4 — Autonomous Epistemic Loop.

One complete DES run per loop iteration (module import, file-based handoff).
Each call to des_module.run_des() is a full independent DES lifecycle.
State is persisted to des_state.json and copied to loop_NNN_state.json.
Pre-registered failure conditions and outcome classification — do not modify.
"""

import json, math, os, re, shutil, sys, time
from pathlib import Path
from openai import OpenAI

BUILDER_MODEL    = "deepseek-chat"
BUILDER_PROVIDER = "deepseek"
FALSIFIER_MODEL  = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS        = 50
MAX_ITER_PER_RUN = 40

RESEARCH_DOMAINS = {
    "R01": "Does raising the minimum wage increase unemployment?",
    "R02": "Is remote work more productive than office work?",
    "R03": "Does immigration reduce wages for native workers?",
    "R04": "Is GDP a valid proxy for human wellbeing?",
    "R05": "Is intermittent fasting effective for long-term weight loss?",
}

RESULTS_DIR = Path("paper4/batch_results_paper4")
STATE_SRC   = Path("des_state.json")

des_module = None  # set in run_all() after client injection


def _make_clients():
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError(
            "DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set in the environment.\n"
            "Export them before running:\n"
            "  export DEEPSEEK_API_KEY=sk-...\n"
            "  export OPENROUTER_API_KEY=sk-or-..."
        )
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                         "X-Title": "DES Paper4 Autonomous Loop"},
    )
    return ds4, orr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
                break   # each claim counted at most once as redundant
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
    branch_trigger_count  = bases.count("T1")
    contradiction_count   = bases.count("T5")
    evidence_gap          = 1 if len(c.get("evidence_refs", [])) == 0 else 0
    return branch_trigger_count + contradiction_count + evidence_gap


def is_exponential(seq: list) -> bool:
    if len(seq) < 4:
        return False
    nonzero = [x for x in seq if x > 0]
    if len(nonzero) < 4:
        return False
    ratios = [nonzero[i+1] / nonzero[i] for i in range(len(nonzero)-1)]
    return all(r >= 1.5 for r in ratios[-3:])


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(state: dict, loop_number: int, prior_texts: list,
                    run_result: dict) -> dict:
    claims  = state.get("claims", {})
    total   = len(claims)
    open_c  = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel   = count_novel(claims, prior_texts)

    all_histories = []
    for c in claims.values():
        all_histories.extend(h.split("[")[0] for h in c.get("history", []))

    new_claims_this_loop = run_result.get("new_claims_this_loop", max(total, 1))
    lit_derived = run_result.get("literature_derived", 0)

    return {
        "loop":                    loop_number,
        "total_claims":            total,
        "open_claims":             open_c,
        "sealed_claims":           total - open_c,
        "disputed_claims":         disputed,
        "redundant_claims":        redundant,
        "entropy":                 (open_c + disputed + redundant) / max(total, 1),
        "novel_claims":            novel,
        "contradictions_resolved": run_result.get("contradictions_resolved", 0),
        "total_contradictions":    run_result.get("total_contradictions", 1),
        "branch_growth":           run_result.get("branches_created", 0),
        "lit_rate":                lit_derived / max(new_claims_this_loop, 1),
        "question_utility":        compute_question_utility(run_result),
    }


def compute_question_utility(result: dict) -> float:
    WEIGHTS = {
        "contradictions_generated": 3,
        "syntheses_produced":       2,
        "counter_hypotheses":       2,
        "evidence_found":           1,
        "branches_created":         1,
    }
    return float(sum(result.get(k, 0) * w for k, w in WEIGHTS.items()))


def extract_run_result(state: dict, prev_total: int) -> dict:
    """Derive run_result fields from state diff (subprocess gives us no return value)."""
    claims = state.get("claims", {})
    total  = len(claims)

    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))

    branches_created      = sum(1 for c in claims.values() if c.get("id", "").startswith("B"))
    syntheses_produced    = sum(1 for c in claims.values() if c.get("is_synthesis", False))
    counter_hypotheses    = all_bases.count("T5")
    evidence_found        = all_bases.count("T3") + all_bases.count("T6")
    contradictions_gen    = all_bases.count("T2")
    # Treat syntheses as "contradictions resolved" proxy
    contradictions_resolved = syntheses_produced
    total_contradictions  = max(counter_hypotheses, 1)

    return {
        "new_claims_this_loop":    max(total - prev_total, 0),
        "literature_derived":      0,    # DES has no explicit lit tag; conservative 0
        "branches_created":        branches_created,
        "syntheses_produced":      syntheses_produced,
        "counter_hypotheses":      counter_hypotheses,
        "evidence_found":          evidence_found,
        "contradictions_generated":contradictions_gen,
        "contradictions_resolved": contradictions_resolved,
        "total_contradictions":    total_contradictions,
    }


# ---------------------------------------------------------------------------
# Failure conditions (pre-registered — do not modify thresholds)
# ---------------------------------------------------------------------------

def check_failure_conditions(current: dict, history: list) -> str | None:
    last5  = history[-5:]  if len(history) >= 5  else history
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

    if len(last10) == 10 and all(m["lit_rate"] > 0.90 for m in last10):
        return "EXTERNAL_ANCHOR_CAPTURE"

    if len(history) >= 10:
        branches = [m["branch_growth"] for m in history[-10:]]
        if is_exponential(branches):
            return "BRANCH_EXPLOSION"

    return None


# ---------------------------------------------------------------------------
# Step 7: Select next question from ClaimGraph
# ---------------------------------------------------------------------------

def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q: str) -> bool:
        toks = _tokens(q)
        return any(_token_overlap(q, h) > 0.75 for h in question_history)

    def make_question(c: dict, prefix: str = "") -> str:
        subj = c.get("subject", "")
        pred = c.get("predicate", "")
        obj  = c.get("object", "")
        base = f"{subj} {pred} {obj}".strip()
        if prefix:
            return f"{prefix}: {base}?"
        return f"What is the evidence that {base}?"

    # 1. Open (not sealed) claims — ranked by epistemic_priority
    open_claims = [
        c for c in claims.values()
        if not c.get("sealed", False)
        and c.get("id", "").startswith("C")  # skip branch nodes B001 etc.
    ]
    open_claims.sort(key=lambda c: epistemic_priority(c, claims), reverse=True)
    for c in open_claims:
        q = make_question(c)
        if not already_asked(q):
            return q

    # 2. Sealed claims with no evidence
    weak_ev = [
        c for c in claims.values()
        if c.get("sealed", False) and len(c.get("evidence_refs", [])) == 0
    ]
    for c in sorted(weak_ev, key=lambda c: c.get("confidence", 0)):
        q = make_question(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    # 3. Synthesis claims (literature-derived side claims)
    synth = [c for c in claims.values() if c.get("is_synthesis", False)]
    synth.sort(key=lambda c: c.get("confidence", 0), reverse=True)
    for c in synth:
        q = make_question(c, "Explore the implications of")
        if not already_asked(q):
            return q

    # 4. Branch-root disputed claims
    disputed_branch = [
        c for c in claims.values()
        if c.get("status") == "disputed"
        and "T1" in [h.split("[")[0] for h in c.get("history", [])]
    ]
    for c in disputed_branch:
        q = make_question(c, "Is there a resolution to the contradiction that")
        if not already_asked(q):
            return q

    # 5. Highest-confidence synthesis reframing
    if synth:
        c = max(synth, key=lambda c: c.get("confidence", 0))
        q = make_question(c, "Critically evaluate the synthesis that")
        if not already_asked(q):
            return q

    return "LOOP_COMPLETE"


# ---------------------------------------------------------------------------
# Outcome classification (pre-registered — do not modify)
# ---------------------------------------------------------------------------

def classify_outcome(loops_completed: int, max_loops: int,
                     failure_code: str | None, loop_metrics: list) -> str:
    if failure_code:
        return failure_code

    if any(m.get("outcome") == "LOOP_COMPLETE" for m in loop_metrics):
        return "LOOP_COMPLETE"

    if loops_completed >= max_loops:
        last10 = loop_metrics[-10:]
        entropy_stable = all(m["entropy"] < 0.80 for m in last10)
        resolution_stable = all(
            m.get("contradictions_resolved", 0) /
            max(m.get("total_contradictions", 1), 1) > 0.50
            for m in last10
        )
        novelty_present = any(m["novel_claims"] > 0 for m in loop_metrics[20:])
        if entropy_stable and resolution_stable and novelty_present:
            return "H1_STABLE"
        else:
            return "H0_DEGENERATION"

    return "INCOMPLETE"


# ---------------------------------------------------------------------------
# Core domain runner
# ---------------------------------------------------------------------------

def run_domain(domain_id: str, seed_question: str,
               max_loops: int = MAX_LOOPS) -> dict:
    domain_dir = RESULTS_DIR / domain_id
    domain_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {domain_id}: {seed_question[:58]}")
    print(f"{'='*65}")

    question         = seed_question
    question_history = [seed_question]
    loop_metrics     = []
    all_prior_texts  = []
    failure_code     = None
    prev_total       = 0

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
            question = select_next_question(state, question_history)
            if question != "LOOP_COMPLETE":
                question_history.append(question)
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        # Steps 1-2: one complete DES run (module import, full lifecycle)
        # des_module.run_des() deletes des_state.json at the start — clean slate
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

        # Steps 3-4: load and save state
        if not STATE_SRC.exists():
            print(f"  ERROR: des_state.json missing after loop {loop}")
            failure_code = "DES_RUN_ERROR"
            break

        with open(STATE_SRC) as f:
            state = json.load(f)
        shutil.copy(STATE_SRC, loop_file)

        # Step 5: compute metrics
        run_result = extract_run_result(state, prev_total)
        metrics    = compute_metrics(state, loop, all_prior_texts, run_result)
        loop_metrics.append(metrics)

        print(f"  -> entropy={metrics['entropy']:.2f} | "
              f"claims={metrics['total_claims']} "
              f"(open={metrics['open_claims']} sealed={metrics['sealed_claims']}) | "
              f"novel={metrics['novel_claims']} redundant={metrics['redundant_claims']}")

        # Update accumulators
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
        prev_total = metrics["total_claims"]

        # Step 6: check failure conditions
        failure_code = check_failure_conditions(metrics, loop_metrics)
        if failure_code:
            print(f"  FAILURE: {failure_code}")
            break

        # Step 7: select next question
        next_question = select_next_question(state, question_history)
        print(f"  Next Q: {next_question[:70]}")

        if next_question == "LOOP_COMPLETE":
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            break

        question_history.append(next_question)
        question = next_question
        time.sleep(2)

    # Save metrics
    with open(domain_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    loops_completed = len(loop_metrics)
    outcome = classify_outcome(loops_completed, max_loops, failure_code, loop_metrics)

    final_entropy = loop_metrics[-1]["entropy"] if loop_metrics else None
    novel_at_20   = loop_metrics[20]["novel_claims"] if len(loop_metrics) > 20 else None

    outcome_data = {
        "domain_id":       domain_id,
        "seed_question":   seed_question,
        "outcome":         outcome,
        "loops_completed": loops_completed,
        "failure_code":    failure_code,
        "final_entropy":   final_entropy,
        "novel_at_loop_20":novel_at_20,
        "question_history":question_history,
        "loop_metrics":    loop_metrics,
    }
    with open(domain_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)

    fe_str = f"{final_entropy:.2f}" if final_entropy is not None else "N/A"
    print(f"\n  {domain_id} outcome: {outcome} | loops={loops_completed} | entropy={fe_str}")
    return outcome_data


# ---------------------------------------------------------------------------
# Summary writer
# ---------------------------------------------------------------------------

def write_summary(all_outcomes: list):
    out_path = RESULTS_DIR / "summary.md"

    h1_count  = sum(1 for o in all_outcomes if o["outcome"] == "H1_STABLE")
    h0_count  = sum(1 for o in all_outcomes if o["outcome"] == "H0_DEGENERATION")
    fail_count= sum(1 for o in all_outcomes if o["outcome"] not in
                    {"H1_STABLE","H0_DEGENERATION","LOOP_COMPLETE","INCOMPLETE"})
    lc_count  = sum(1 for o in all_outcomes if o["outcome"] == "LOOP_COMPLETE")

    confirmed = h1_count >= 3  # majority of 5 domains

    with open(out_path, "w") as f:
        f.write("# Paper 4 — Autonomous Epistemic Loop\n\n")
        f.write("## Pre-Registered Hypothesis\n\n")
        f.write("**H1:** DES sustains ≥20 autonomous loops per domain with entropy < 0.80, ")
        f.write(">50% contradiction resolution, and novel hypotheses past loop 20.  \n")
        f.write("**H0:** DES degenerates within 20 loops.\n\n")

        f.write("## Summary Results\n\n")
        f.write("| Domain | Outcome | Loops | Final Entropy | Novel@20 |\n")
        f.write("|---|---|---|---|---|\n")
        for o in all_outcomes:
            fe = f"{o['final_entropy']:.2f}" if o["final_entropy"] is not None else "—"
            n20 = str(o["novel_at_loop_20"]) if o["novel_at_loop_20"] is not None else "—"
            f.write(f"| {o['domain_id']} | **{o['outcome']}** | "
                    f"{o['loops_completed']} | {fe} | {n20} |\n")

        f.write(f"\n**H1_STABLE:** {h1_count}/5  \n")
        f.write(f"**H0_DEGENERATION:** {h0_count}/5  \n")
        f.write(f"**LOOP_COMPLETE:** {lc_count}/5  \n")
        f.write(f"**Failure:** {fail_count}/5  \n\n")

        f.write("## Per-Domain Entropy Trajectories\n\n")
        for o in all_outcomes:
            f.write(f"### {o['domain_id']}\n\n")
            f.write(f"**Seed:** {o['seed_question']}  \n")
            f.write(f"**Outcome:** {o['outcome']}  \n\n")
            f.write("| Loop | Entropy | Open | Sealed | Novel | Redundant | Utility |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for m in o.get("loop_metrics", []):
                f.write(f"| {m['loop']} | {m['entropy']:.2f} | "
                        f"{m['open_claims']} | {m['sealed_claims']} | "
                        f"{m['novel_claims']} | {m['redundant_claims']} | "
                        f"{m['question_utility']:.0f} |\n")
            f.write("\n**Question history:**\n\n")
            for i, q in enumerate(o.get("question_history", [])[:10]):
                f.write(f"{i}. {q}\n")
            if len(o.get("question_history", [])) > 10:
                f.write(f"... ({len(o['question_history'])-10} more)\n")
            f.write("\n")

        f.write("## Hypothesis Verdict\n\n")
        if confirmed:
            f.write(f"**H1 CONFIRMED:** {h1_count}/5 domains reached H1_STABLE.  \n")
            f.write("DES sustains autonomous multi-loop epistemic inquiry without degeneration.\n")
        else:
            f.write(f"**H1 NOT CONFIRMED:** Only {h1_count}/5 domains reached H1_STABLE ")
            f.write(f"({h0_count} H0, {fail_count} failures, {lc_count} LOOP_COMPLETE).  \n")
            f.write("Reported honestly per pre-registration.\n")

    print(f"\nSummary: {out_path}")
    print(f"Verdict: {'H1 CONFIRMED' if confirmed else 'H1 NOT CONFIRMED'} "
          f"({h1_count}/5 H1_STABLE)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_all():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    import des as des_module_local

    ds4_client, or_client = _make_clients()
    des_module_local._clients["deepseek"]   = ds4_client
    des_module_local._clients["openrouter"] = or_client
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER

    # Pass module ref into domain runner via module-level name
    global des_module
    des_module = des_module_local

    all_outcomes = []
    for domain_id, seed_question in RESEARCH_DOMAINS.items():
        outcome_file = RESULTS_DIR / domain_id / "outcome.json"
        if outcome_file.exists():
            with open(outcome_file) as f:
                o = json.load(f)
            print(f"  [skip domain] {domain_id} — {o['outcome']} ({o['loops_completed']} loops)")
            all_outcomes.append(o)
            continue

        o = run_domain(domain_id, seed_question)
        all_outcomes.append(o)

    write_summary(all_outcomes)
    return all_outcomes


if __name__ == "__main__":
    run_all()

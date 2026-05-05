"""
Paper 5 — Structured Epistemic Perturbation.

Same loop architecture as Paper 4 (one full DES run per iteration,
module import, file-based handoff) with perturbation injected at
epistemic failure onset.

Perturbation is triggered by epistemic state — never by loop count.
Five rotating types validated by Alexandria-lite gate.
Pre-registered failure conditions + PERTURBATION_DRIFT — do not modify.
"""

import json, os, re, shutil, sys, time
from pathlib import Path
from openai import OpenAI

# Add DES root to path for module import
sys.path.insert(0, str(Path(__file__).parent.parent))

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 50
MAX_ITER_PER_RUN   = 40

RESEARCH_DOMAINS = {
    "R01": "Does raising the minimum wage increase unemployment?",
    "R02": "Is remote work more productive than office work?",
    "R03": "Does immigration reduce wages for native workers?",
    "R04": "Is GDP a valid proxy for human wellbeing?",
    "R05": "Is intermittent fasting effective for long-term weight loss?",
}

PAPER4_BASELINE = {
    "R01": {"loops": 2, "outcome": "SEMANTIC_DUPLICATION"},
    "R02": {"loops": 3, "outcome": "SEMANTIC_DUPLICATION"},
    "R03": {"loops": 4, "outcome": "SEMANTIC_DUPLICATION"},
    "R04": {"loops": 3, "outcome": "LOOP_COMPLETE"},
    "R05": {"loops": 4, "outcome": "SEMANTIC_DUPLICATION"},
}

RESULTS_DIR = Path("paper5/batch_results_paper5")
STATE_SRC   = Path("des_state.json")

des_module = None  # set in run_all() after client injection


# ---------------------------------------------------------------------------
# Perturbation types and prompts
# ---------------------------------------------------------------------------

PERTURBATION_TYPES = [
    "scope_shift",
    "counterfactual",
    "category_flip",
    "time_shift",
    "stakeholder_flip",
]

PERTURBATION_PROMPTS = {
    "scope_shift": """\
Current research question: {question}
Claim graph terms: {graph_terms}

The central claim space has been explored.
Generate ONE research question targeting a boundary condition or scope
(size, context, time period, region) NOT yet present in the claim graph.
Must be directly related to the original question.
Return ONLY: one research question as a single sentence.""",

    "counterfactual": """\
Dominant claim: {dominant_claim}
(highest confidence in current graph)

Assume this claim is directionally wrong.
What single missing variable could explain why the dominant evidence
points in the wrong direction?
Generate ONE research question that could surface this variable.
Return ONLY: one research question as a single sentence.""",

    "category_flip": """\
Current epistemic tension: {tension_description}
(unresolved contradiction in claim graph)

Reframe this tension as a MODEL ASSUMPTION question (not empirical).
What modeling choice or abstraction is causing this apparent contradiction?
If we changed the assumption, would the tension dissolve?
Return ONLY: one research question targeting the model assumption level.""",

    "time_shift": """\
Supported claim: {claim_text}

Generate ONE research question testing temporal validity:
Does this relationship change over decades? Is it period-specific?
Return ONLY: one research question targeting temporal validity.""",

    "stakeholder_flip": """\
Claim: {claim_text}

Generate ONE research question testing whether this claim holds
from a DIFFERENT stakeholder perspective not yet in the claim graph.
Return ONLY: one research question as a single sentence.""",
}


def select_perturbation_type(perturbation_count: int) -> str:
    return PERTURBATION_TYPES[perturbation_count % len(PERTURBATION_TYPES)]


# ---------------------------------------------------------------------------
# Helpers (shared with Paper 4 logic)
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for",
            "and","or","but","not","with","by","from","that","this","it",
            "be","as","at","on","if","its","so","do","can","will","does"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def token_overlap(a: str, b: str) -> float:
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _claim_text(c: dict) -> str:
    return f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()


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
    novel = 0
    for c in claims.values():
        txt = _claim_text(c)
        if all(token_overlap(txt, p) < 0.30 for p in prior_texts):
            novel += 1
    return novel


def epistemic_priority(c: dict) -> int:
    history = c.get("history", [])
    bases = [h.split("[")[0] for h in history]
    return bases.count("T1") + bases.count("T5") + (1 if not c.get("evidence_refs") else 0)


def is_exponential(seq: list) -> bool:
    nonzero = [x for x in seq if x > 0]
    if len(nonzero) < 4:
        return False
    ratios = [nonzero[i+1] / nonzero[i] for i in range(len(nonzero)-1)]
    return all(r >= 1.5 for r in ratios[-3:])


# ---------------------------------------------------------------------------
# Perturbation trigger
# ---------------------------------------------------------------------------

def should_perturb(loop_metrics: list, current: dict) -> tuple[bool, str]:
    """Returns (trigger: bool, reason: str)."""
    if current["semantic_duplication_rate"] > 0.40:
        return True, "semantic_duplication_rate > 0.40"
    last3 = loop_metrics[-3:] if len(loop_metrics) >= 3 else []
    if len(last3) == 3 and all(m["novel_claims"] == 0 for m in last3):
        return True, "novel_claims == 0 for last 3 loops"
    if len(loop_metrics) >= 2:
        if current["entropy"] > loop_metrics[-2]["entropy"] + 0.15:
            return True, f"entropy spike +{current['entropy'] - loop_metrics[-2]['entropy']:.2f}"
    return False, ""


# ---------------------------------------------------------------------------
# Alexandria-lite validation gate
# ---------------------------------------------------------------------------

def validate_perturbation(question: str, state: dict,
                          question_history: list) -> tuple[bool, str]:
    claims = state.get("claims", {})

    # 1. No circular
    for prior_q in question_history:
        if token_overlap(question, prior_q) > 0.70:
            return False, "circular: overlap with prior question"

    # 2. Graph-term anchor
    graph_terms = set()
    for c in claims.values():
        for field in ["subject", "predicate", "object"]:
            graph_terms.update(_tokens(c.get(field, "")))
    q_terms = _tokens(question)
    if not (graph_terms & q_terms):
        return False, "unanchored: no graph terms in question"

    # 3. No sealed claim reopening
    for c in claims.values():
        if c.get("sealed"):
            ct = _claim_text(c)
            if token_overlap(question, ct) > 0.60:
                return False, f"reopening sealed claim {c.get('id','?')}"

    return True, "admitted"


# ---------------------------------------------------------------------------
# Perturbation question generator
# ---------------------------------------------------------------------------

def _graph_terms_str(state: dict) -> str:
    terms = set()
    for c in state.get("claims", {}).values():
        for f in ["subject", "predicate", "object"]:
            terms.update(_tokens(c.get(f, "")))
    return ", ".join(sorted(terms)[:30])


def _dominant_claim(state: dict) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "unknown"
    best = max(claims.values(), key=lambda c: c.get("confidence", 0))
    return _claim_text(best)


def _tension_description(state: dict) -> str:
    claims = state.get("claims", {})
    disputed = [c for c in claims.values() if c.get("status") == "disputed"]
    if disputed:
        c = max(disputed, key=lambda c: epistemic_priority(c))
        return _claim_text(c)
    return "No explicit tension found — use the main research question as framing."


def _supported_claim(state: dict) -> str:
    claims = state.get("claims", {})
    supported = [c for c in claims.values()
                 if c.get("status") == "supported" and c.get("sealed")]
    if supported:
        return _claim_text(max(supported, key=lambda c: c.get("confidence", 0)))
    if claims:
        return _claim_text(next(iter(claims.values())))
    return "unknown"


def generate_perturbation_question(ptype: str, question: str,
                                   state: dict, client, model: str) -> str:
    prompt_template = PERTURBATION_PROMPTS[ptype]
    prompt = prompt_template.format(
        question=question,
        graph_terms=_graph_terms_str(state),
        dominant_claim=_dominant_claim(state),
        tension_description=_tension_description(state),
        claim_text=_supported_claim(state),
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=120,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(state: dict, loop: int, prior_texts: list,
                    run_result: dict, perturbed: bool = False,
                    perturbation_type: str = "") -> dict:
    claims  = state.get("claims", {})
    total   = len(claims)
    open_c  = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel   = count_novel(claims, prior_texts)

    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))

    syntheses  = sum(1 for c in claims.values() if c.get("is_synthesis"))
    counters   = all_bases.count("T5")
    evidence   = all_bases.count("T3") + all_bases.count("T6")
    branches   = sum(1 for c in claims.values() if c.get("id","").startswith("B"))
    contradictions_gen = all_bases.count("T2")
    new_claims = run_result.get("new_claims_this_loop", max(total, 1))

    return {
        "loop":                     loop,
        "total_claims":             total,
        "open_claims":              open_c,
        "sealed_claims":            total - open_c,
        "disputed_claims":          disputed,
        "redundant_claims":         redundant,
        "semantic_duplication_rate":redundant / max(total, 1),
        "entropy":                  (open_c + disputed + redundant) / max(total, 1),
        "novel_claims":             novel,
        "branch_growth":            branches,
        "contradictions_resolved":  syntheses,
        "total_contradictions":     max(counters, 1),
        "lit_rate":                 0.0,
        "question_utility":         float(contradictions_gen*3 + syntheses*2 + counters*2 + evidence*1 + branches*1),
        "perturbed":                perturbed,
        "perturbation_type":        perturbation_type,
    }


def extract_run_result(state: dict, prev_total: int) -> dict:
    return {"new_claims_this_loop": max(len(state.get("claims", {})) - prev_total, 0)}


# ---------------------------------------------------------------------------
# Failure conditions (pre-registered)
# ---------------------------------------------------------------------------

def check_failure_conditions(current: dict, history: list,
                              perturbation_log: list) -> str | None:
    last5  = history[-5:]  if len(history) >= 5  else history
    last10 = history[-10:] if len(history) >= 10 else history

    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"

    if current["total_claims"] > 0 and current["semantic_duplication_rate"] > 0.60:
        return "SEMANTIC_DUPLICATION"

    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"

    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"

    if len(last10) == 10 and all(m["lit_rate"] > 0.90 for m in last10):
        return "EXTERNAL_ANCHOR_CAPTURE"

    if len(history) >= 10:
        if is_exponential([m["branch_growth"] for m in history[-10:]]):
            return "BRANCH_EXPLOSION"

    # PERTURBATION_DRIFT: admission_rate < 0.40 for 5 consecutive perturbed loops
    perturbed_recent = [e for e in perturbation_log if e.get("loop", 0) >= (history[-1]["loop"] - 10)]
    if len(perturbed_recent) >= 5:
        last5p = perturbed_recent[-5:]
        if all(not e["admitted"] for e in last5p):
            return "PERTURBATION_DRIFT"

    return None


# ---------------------------------------------------------------------------
# Question selection (same as Paper 4)
# ---------------------------------------------------------------------------

def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q: str) -> bool:
        return any(token_overlap(q, h) > 0.75 for h in question_history)

    def make_question(c: dict, prefix: str = "") -> str:
        base = _claim_text(c).strip()
        if prefix:
            return f"{prefix}: {base}?"
        return f"What is the evidence that {base}?"

    open_claims = [c for c in claims.values()
                   if not c.get("sealed") and c.get("id","").startswith("C")]
    open_claims.sort(key=epistemic_priority, reverse=True)
    for c in open_claims:
        q = make_question(c)
        if not already_asked(q):
            return q

    weak_ev = [c for c in claims.values()
               if c.get("sealed") and not c.get("evidence_refs")]
    for c in sorted(weak_ev, key=lambda c: c.get("confidence", 0)):
        q = make_question(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    synth = sorted([c for c in claims.values() if c.get("is_synthesis")],
                   key=lambda c: c.get("confidence", 0), reverse=True)
    for c in synth:
        q = make_question(c, "Explore the implications of")
        if not already_asked(q):
            return q

    disputed_branch = [c for c in claims.values()
                       if c.get("status") == "disputed"
                       and "T1" in [h.split("[")[0] for h in c.get("history", [])]]
    for c in disputed_branch:
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
# Outcome classification (pre-registered)
# ---------------------------------------------------------------------------

def classify_outcome(loops_completed: int, max_loops: int,
                     failure_code: str | None, loop_metrics: list) -> str:
    if failure_code:
        return failure_code
    if any(m.get("outcome") == "LOOP_COMPLETE" for m in loop_metrics):
        return "LOOP_COMPLETE"
    if loops_completed >= max_loops:
        last10 = loop_metrics[-10:]
        entropy_stable    = all(m["entropy"] < 0.80 for m in last10)
        resolution_stable = all(
            m["contradictions_resolved"] / max(m["total_contradictions"], 1) > 0.50
            for m in last10
        )
        novelty_present = any(m["novel_claims"] > 0 for m in loop_metrics[20:])
        if entropy_stable and resolution_stable and novelty_present:
            return "H1_STABLE"
        return "H0_DEGENERATION"
    return "INCOMPLETE"


# ---------------------------------------------------------------------------
# Domain runner
# ---------------------------------------------------------------------------

def run_domain(domain_id: str, seed_question: str,
               or_client, max_loops: int = MAX_LOOPS) -> dict:
    domain_dir = RESULTS_DIR / domain_id
    domain_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {domain_id}: {seed_question[:58]}")
    print(f"{'='*65}")

    question          = seed_question
    question_history  = [seed_question]
    loop_metrics      = []
    all_prior_texts   = []
    perturbation_log  = []
    perturbation_count = 0
    failure_code      = None
    prev_total        = 0

    for loop in range(max_loops):
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            rr = extract_run_result(state, 0)
            m = compute_metrics(state, loop, all_prior_texts, rr)
            loop_metrics.append(m)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims",{}).values())
            prev_total = m["total_claims"]
            question = select_next_question(state, question_history)
            if question != "LOOP_COMPLETE":
                question_history.append(question)
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        # ---- Run DES ----
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

        rr      = extract_run_result(state, prev_total)
        metrics = compute_metrics(state, loop, all_prior_texts, rr)
        loop_metrics.append(metrics)

        print(f"  -> entropy={metrics['entropy']:.2f} | "
              f"claims={metrics['total_claims']} "
              f"(open={metrics['open_claims']} sealed={metrics['sealed_claims']}) | "
              f"novel={metrics['novel_claims']} dup_rate={metrics['semantic_duplication_rate']:.0%}")

        all_prior_texts.extend(_claim_text(c) for c in state.get("claims",{}).values())
        prev_total = metrics["total_claims"]

        # ---- Failure check ----
        failure_code = check_failure_conditions(metrics, loop_metrics, perturbation_log)
        if failure_code:
            print(f"  FAILURE: {failure_code}")
            break

        # ---- Perturbation check ----
        triggered, trigger_reason = should_perturb(loop_metrics[:-1], metrics)

        if triggered:
            ptype = select_perturbation_type(perturbation_count)
            print(f"  PERTURB [{ptype}] trigger={trigger_reason}")

            try:
                gen_q = generate_perturbation_question(
                    ptype, question, state, or_client, FALSIFIER_MODEL)
            except Exception as e:
                print(f"  Perturbation generation failed: {e}")
                gen_q = ""

            admitted, reason = (False, "generation failed") if not gen_q else \
                validate_perturbation(gen_q, state, question_history)

            event = {
                "loop":               loop,
                "perturbation_count": perturbation_count,
                "trigger":            trigger_reason,
                "type":               ptype,
                "seed":               perturbation_count,
                "input": {
                    "question":        question,
                    "dominant_claim":  _dominant_claim(state),
                    "tension":         _tension_description(state),
                    "claim_text":      _supported_claim(state),
                },
                "generated_question": gen_q,
                "admitted":           admitted,
                "rejection_reason":   None if admitted else reason,
                "novelty_produced":   0,   # filled after next loop
            }
            perturbation_log.append(event)
            perturbation_count += 1

            if admitted:
                print(f"  ADMITTED: {gen_q[:70]}")
                metrics["perturbed"]         = True
                metrics["perturbation_type"] = ptype
                question = gen_q
                question_history.append(gen_q)
                # Re-check failure after perturbation admission
                failure_code = check_failure_conditions(metrics, loop_metrics, perturbation_log)
                if failure_code:
                    print(f"  FAILURE (post-perturb): {failure_code}")
                    break
                time.sleep(2)
                continue
            else:
                print(f"  REJECTED ({reason})")

        # ---- Normal next question ----
        next_question = select_next_question(state, question_history)
        print(f"  Next Q: {next_question[:70]}")

        if next_question == "LOOP_COMPLETE":
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            break

        question_history.append(next_question)
        question = next_question
        time.sleep(2)

    # Fill novelty_produced for each perturbation event
    for i, event in enumerate(perturbation_log):
        if event["admitted"]:
            event_loop = event["loop"]
            next_loops = [m for m in loop_metrics if m["loop"] > event_loop]
            if next_loops:
                event["novelty_produced"] = next_loops[0]["novel_claims"]

    # Save outputs
    with open(domain_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    with open(domain_dir / "perturbation_log.json", "w") as f:
        json.dump(perturbation_log, f, indent=2)

    loops_completed = len(loop_metrics)
    outcome = classify_outcome(loops_completed, max_loops, failure_code, loop_metrics)

    final_entropy = loop_metrics[-1]["entropy"] if loop_metrics else None
    novel_at_20   = loop_metrics[20]["novel_claims"] if len(loop_metrics) > 20 else None

    outcome_data = {
        "domain_id":          domain_id,
        "seed_question":      seed_question,
        "outcome":            outcome,
        "loops_completed":    loops_completed,
        "failure_code":       failure_code,
        "final_entropy":      final_entropy,
        "novel_at_loop_20":   novel_at_20,
        "question_history":   question_history,
        "loop_metrics":       loop_metrics,
        "perturbation_count": perturbation_count,
        "perturbation_log":   perturbation_log,
    }
    with open(domain_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)

    fe_str = f"{final_entropy:.2f}" if final_entropy is not None else "N/A"
    print(f"\n  {domain_id} outcome: {outcome} | loops={loops_completed} | "
          f"entropy={fe_str} | perturbations={perturbation_count}")
    return outcome_data


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def write_summary(all_outcomes: list):
    out_path = RESULTS_DIR / "summary.md"

    h1 = sum(1 for o in all_outcomes if o["outcome"] == "H1_STABLE")
    h0 = sum(1 for o in all_outcomes if o["outcome"] == "H0_DEGENERATION")
    lc = sum(1 for o in all_outcomes if o["outcome"] == "LOOP_COMPLETE")
    fa = sum(1 for o in all_outcomes if o["outcome"] not in
             {"H1_STABLE","H0_DEGENERATION","LOOP_COMPLETE","INCOMPLETE"})

    p5_avg = sum(o["loops_completed"] for o in all_outcomes) / max(len(all_outcomes), 1)
    p4_avg = sum(PAPER4_BASELINE[o["domain_id"]]["loops"] for o in all_outcomes) / max(len(all_outcomes), 1)

    # H1/H2 verdicts
    h1_confirmed = h1 >= 3
    depth_lifts = sum(1 for o in all_outcomes
                      if o["loops_completed"] > PAPER4_BASELINE[o["domain_id"]]["loops"] + 2)
    h1_paper5_confirmed = depth_lifts >= 3

    # Novelty lift per type
    type_novelty: dict[str, list] = {t: [] for t in PERTURBATION_TYPES}
    for o in all_outcomes:
        for event in o.get("perturbation_log", []):
            if event["admitted"]:
                type_novelty[event["type"]].append(event["novelty_produced"])
    type_avg = {t: (sum(v)/len(v) if v else 0.0) for t, v in type_novelty.items()}
    best_type = max(type_avg, key=lambda t: type_avg[t]) if type_avg else "—"
    h2_confirmed = any(type_avg[t] >= 1.0 for t in PERTURBATION_TYPES) and \
                   sum(1 for o in all_outcomes
                       if any(e["admitted"] and e["novelty_produced"] >= 1
                              for e in o.get("perturbation_log",[]))) >= 3

    with open(out_path, "w") as f:
        f.write("# Paper 5 — Structured Epistemic Perturbation\n\n")
        f.write("## Pre-Registered Hypotheses\n\n")
        f.write("**H1:** Perturbation extends loop depth ≥2 vs Paper 4 on ≥3/5 domains.  \n")
        f.write("**H2:** ≥1 type produces ≥1 novel claim/loop on ≥3 domains.  \n")
        f.write("**H0:** No effect — degeneration on same schedule as Paper 4.\n\n")

        f.write("## Summary Results\n\n")
        f.write("| Domain | P4 Loops | P5 Loops | Lift | Outcome | Perturb triggered/admitted |\n")
        f.write("|---|---|---|---|---|---|\n")
        for o in all_outcomes:
            p4l = PAPER4_BASELINE[o["domain_id"]]["loops"]
            p5l = o["loops_completed"]
            lift = p5l - p4l
            plog = o.get("perturbation_log", [])
            triggered = len(plog)
            admitted  = sum(1 for e in plog if e["admitted"])
            f.write(f"| {o['domain_id']} | {p4l} | {p5l} | "
                    f"{'+'if lift>=0 else ''}{lift} | **{o['outcome']}** | "
                    f"{triggered}/{admitted} |\n")

        f.write(f"\n**Avg loop depth — Paper 4:** {p4_avg:.1f}  \n")
        f.write(f"**Avg loop depth — Paper 5:** {p5_avg:.1f}  \n")
        f.write(f"**Domains with depth lift ≥2:** {depth_lifts}/5  \n\n")

        f.write("## Perturbation Novelty Lift by Type\n\n")
        f.write("| Type | Avg novel claims (admitted loops) |\n|---|---|\n")
        for t in PERTURBATION_TYPES:
            n = len(type_novelty[t])
            f.write(f"| {t} | {type_avg[t]:.2f} (n={n}) |\n")
        f.write(f"\n**Best type:** {best_type} (avg {type_avg.get(best_type,0):.2f} novel claims)  \n\n")

        f.write("## Per-Domain Details\n\n")
        for o in all_outcomes:
            f.write(f"### {o['domain_id']}\n\n")
            f.write(f"**Seed:** {o['seed_question']}  \n")
            f.write(f"**Outcome:** {o['outcome']}  \n")
            f.write(f"**Loops:** {o['loops_completed']} (Paper 4 baseline: "
                    f"{PAPER4_BASELINE[o['domain_id']]['loops']})  \n\n")
            f.write("| Loop | Entropy | Novel | Dup% | Perturbed | Type |\n")
            f.write("|---|---|---|---|---|---|\n")
            for m in o.get("loop_metrics", []):
                p_mark = "Y" if m.get("perturbed") else "-"
                p_type = m.get("perturbation_type", "")
                f.write(f"| {m['loop']} | {m['entropy']:.2f} | {m['novel_claims']} | "
                        f"{m['semantic_duplication_rate']:.0%} | {p_mark} | {p_type} |\n")
            plog = o.get("perturbation_log", [])
            if plog:
                f.write(f"\n**Perturbation log ({len(plog)} events):**\n\n")
                for e in plog:
                    status = "✓ ADMITTED" if e["admitted"] else f"✗ {e['rejection_reason']}"
                    f.write(f"- Loop {e['loop']} [{e['type']}] {status}")
                    if e["admitted"]:
                        f.write(f" → novel={e['novelty_produced']}")
                    f.write(f"\n  Q: {e['generated_question'][:80]}\n")
            f.write("\n")

        f.write("## Hypothesis Verdict\n\n")
        f.write(f"**H1 (depth lift):** {'CONFIRMED' if h1_paper5_confirmed else 'NOT CONFIRMED'} "
                f"— {depth_lifts}/5 domains with ≥2 extra loops  \n")
        f.write(f"**H2 (novelty lift):** {'CONFIRMED' if h2_confirmed else 'NOT CONFIRMED'} "
                f"— best type '{best_type}' ({type_avg.get(best_type,0):.2f} avg novel)  \n")
        f.write(f"**H0:** {'NOT rejected' if h1_paper5_confirmed or h2_confirmed else 'Cannot reject'}  \n\n")
        f.write("Reported honestly per pre-registration.\n")

    print(f"\nSummary: {out_path}")
    print(f"H1: {'CONFIRMED' if h1_paper5_confirmed else 'NOT CONFIRMED'} ({depth_lifts}/5 domains)")
    print(f"H2: {'CONFIRMED' if h2_confirmed else 'NOT CONFIRMED'} (best={best_type} {type_avg.get(best_type,0):.2f})")


# ---------------------------------------------------------------------------
# Entry point
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
                         "X-Title": "DES Paper5 Perturbation"},
    )
    return ds4, orr


def run_all():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    import des as des_module_local
    ds4_client, or_client = _make_clients()
    des_module_local._clients["deepseek"]   = ds4_client
    des_module_local._clients["openrouter"] = or_client
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER

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

        o = run_domain(domain_id, seed_question, or_client)
        all_outcomes.append(o)

    write_summary(all_outcomes)
    return all_outcomes


if __name__ == "__main__":
    run_all()

"""
Paper 5 v0.4a — Frame/Metric/Shape Fixation Triggers.

Bug fix from v0.3: should_perturb receives loop_metrics (prior only) + current
as separate argument. Current loop NOT in loop_metrics at trigger-check time.

New preventive triggers (priority order):
  1. frame_repeat    — same inferred frame type as previous loop
  2. metric_repeat   — same outcome metric as previous loop
  3. shape_repeat    — same question syntactic shape as previous loop
  4. method_repeat   — same method type as previous loop (v0.3 backup)
  5. content_redundancy / novelty_zero_x3  — reactive fallbacks

T10 EPISTEMIC_ROLLBACK_AND_RESEED: unchanged from v0.3.
Output: paper5/batch_results_paper5_v04a/

Pre-registered hypotheses, failure conditions, and T10 — do not modify.
"""

import json, os, re, shutil, sys, time
from collections import Counter
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 50
MAX_ITER_PER_RUN   = 40
MAX_T10            = 2

RESEARCH_DOMAINS = {
    "R01": "Does raising the minimum wage increase unemployment?",
    "R02": "Is remote work more productive than office work?",
    "R03": "Does immigration reduce wages for native workers?",
    "R04": "Is GDP a valid proxy for human wellbeing?",
    "R05": "Is intermittent fasting effective for long-term weight loss?",
}

PAPER4_BASELINE   = {"R01": 2, "R02": 3, "R03": 4, "R04": 3, "R05": 4}
PAPER5V03_BASELINE = {"R01": 1, "R02": 5, "R03": 2, "R04": 1, "R05": 4}

RESULTS_DIR = Path("paper5/batch_results_paper5_v04a")
STATE_SRC   = Path("des_state.json")

des_module  = None
or_client_g = None


# ---------------------------------------------------------------------------
# Method type inference (pre-registered, unchanged from v0.3)
# ---------------------------------------------------------------------------

METHOD_TYPES = [
    "empirical_evidence", "scope_condition", "model_assumption",
    "measurement_validity", "causal_mechanism", "unit_of_analysis",
    "counterfactual_baseline", "stakeholder_perspective",
    "temporal_validity", "failure_mode",
]


def infer_method_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["mechanism", "how does", "via", "through"]):
        return "causal_mechanism"
    if any(w in q for w in ["measure", "operationalize", "indicator", "proxy"]):
        return "measurement_validity"
    if any(w in q for w in ["assume", "assumption", "model", "simplification"]):
        return "model_assumption"
    if any(w in q for w in ["unit", "level", "aggregate", "individual", "firm", "country"]):
        return "unit_of_analysis"
    if any(w in q for w in ["counterfactual", "alternative", "instead", "without", "absent"]):
        return "counterfactual_baseline"
    if any(w in q for w in ["fail", "failure", "breakdown", "exception", "limit"]):
        return "failure_mode"
    if any(w in q for w in ["stakeholder", "worker", "employer", "consumer", "group"]):
        return "stakeholder_perspective"
    if any(w in q for w in ["decades", "years", "historical", "period", "temporal"]):
        return "temporal_validity"
    if any(w in q for w in ["condition", "context", "scope", "when", "where", "size"]):
        return "scope_condition"
    return "empirical_evidence"


# ---------------------------------------------------------------------------
# Frame type inference (NEW v0.4)
# Priority: measurement > mechanism > scope > causal > comparison > normative > effectiveness
# Effectiveness is default — prevents common vocabulary from dominating.
# ---------------------------------------------------------------------------

FRAME_TYPES = [
    "causal", "effectiveness", "scope", "measurement",
    "mechanism", "comparison", "normative",
]


def infer_frame_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["measure", "define", "operationalize", "proxy", "indicator",
                             "accurately", "capture", "validity"]):
        return "measurement"
    if any(w in q for w in ["mechanism", "process", "how does", "pathway", "via",
                             "through what", "by what"]):
        return "mechanism"
    if any(w in q for w in ["condition", "when", "where", "under", "context",
                             "only if", "unless", "scope"]):
        return "scope"
    if any(w in q for w in ["cause", "lead to", "result in", "drive", "determine"]):
        return "causal"
    if any(w in q for w in ["compare", "better", "worse", "more than", "less than",
                             "relative to", "versus"]):
        return "comparison"
    if any(w in q for w in ["should", "ought", "policy", "recommend", "justified",
                             "ethical", "normative"]):
        return "normative"
    return "effectiveness"


# ---------------------------------------------------------------------------
# Question shape inference (NEW v0.4)
# ---------------------------------------------------------------------------

QUESTION_SHAPES = [
    "does_x_cause_y", "is_x_effective", "what_evidence",
    "under_what_conditions", "how_does_x_work", "what_is_the_effect",
]


def infer_question_shape(question: str) -> str:
    q = question.lower().strip()
    if q.startswith(("does ", "do ", "did ")):
        return "does_x_cause_y"
    if q.startswith(("is ", "are ", "was ")):
        return "is_x_effective"
    if q.startswith("what evidence"):
        return "what_evidence"
    if q.startswith(("under what", "in what", "when does")):
        return "under_what_conditions"
    if q.startswith(("how does", "how do", "via what", "through what")):
        return "how_does_x_work"
    if "effect of" in q or "impact of" in q:
        return "what_is_the_effect"
    return "is_x_effective"


# ---------------------------------------------------------------------------
# Outcome metric extraction (NEW v0.4)
# ---------------------------------------------------------------------------

def extract_outcome_metric(question: str, claims: dict) -> str:
    supported = [c for c in claims.values() if c.get("status") == "supported"]
    if not supported:
        words = question.lower().split()
        return words[-1] if words else "unknown"
    objects = [c.get("object", "").lower() for c in supported]
    words = [w for obj in objects for w in obj.split()
             if len(w) > 4 and w not in {"that", "this", "with", "from", "into",
                                          "their", "these", "those", "which"}]
    if words:
        return Counter(words).most_common(1)[0][0]
    return "unknown"


# ---------------------------------------------------------------------------
# Frame/metric/shape fixation checks (NEW v0.4)
# ---------------------------------------------------------------------------

def check_frame_fixation(loop_metrics: list, current: dict) -> str | None:
    if not loop_metrics:
        return None
    prev = loop_metrics[-1].get("frame_type")
    curr = current.get("frame_type")
    if prev and curr and prev == curr:
        return f"frame_repeat:{curr}"
    return None


def check_metric_fixation(loop_metrics: list, current: dict) -> str | None:
    if not loop_metrics:
        return None
    prev = loop_metrics[-1].get("outcome_metric")
    curr = current.get("outcome_metric")
    if prev and curr and prev == curr and prev != "unknown":
        return f"metric_repeat:{curr}"
    return None


def check_question_shape_fixation(loop_metrics: list, current: dict) -> str | None:
    if not loop_metrics:
        return None
    prev = loop_metrics[-1].get("question_shape")
    curr = current.get("question_shape")
    if prev and curr and prev == curr:
        return f"shape_repeat:{curr}"
    return None


# ---------------------------------------------------------------------------
# Preventive trigger v0.4 (BUG FIXED)
# loop_metrics = prior completed loops only. current = this loop's metrics.
# ---------------------------------------------------------------------------

def should_perturb_v04(loop_metrics: list, current: dict) -> tuple[bool, str]:
    # PRIMARY: frame fixation (earliest signal)
    frame_fix = check_frame_fixation(loop_metrics, current)
    if frame_fix:
        return True, frame_fix

    # PRIMARY: metric fixation
    metric_fix = check_metric_fixation(loop_metrics, current)
    if metric_fix:
        return True, metric_fix

    # PRIMARY: question shape fixation
    shape_fix = check_question_shape_fixation(loop_metrics, current)
    if shape_fix:
        return True, shape_fix

    # SECONDARY: method repeat (v0.3 backup, now correctly comparing current vs previous)
    if loop_metrics:
        prev_method = loop_metrics[-1].get("method_type")
        curr_method = current.get("method_type")
        if prev_method and curr_method and prev_method == curr_method:
            return True, f"method_repeat:{curr_method}"

    # FALLBACK: content redundancy (reactive)
    if current.get("semantic_duplication_rate", 0) > 0.40:
        return True, "content_redundancy>0.40"
    last3 = loop_metrics[-3:] if len(loop_metrics) >= 3 else []
    if len(last3) == 3 and all(m.get("novel_claims", 0) == 0 for m in last3):
        return True, "novelty_zero_x3"

    return False, ""


def trigger_is_preventive(trigger: str) -> bool:
    return any(trigger.startswith(p) for p in
               ["frame_repeat:", "metric_repeat:", "shape_repeat:", "method_repeat:"])


# ---------------------------------------------------------------------------
# Method perturbation types and prompts (unchanged from v0.3)
# ---------------------------------------------------------------------------

METHOD_PERTURBATION_TYPES = [
    "measurement_shift",
    "model_assumption_shift",
    "unit_of_analysis_shift",
    "evidence_standard_shift",
    "causal_mechanism_shift",
    "counterfactual_baseline_shift",
    "failure_mode_shift",
]

METHOD_PROMPTS = {
    "measurement_shift": """\
Research question: {question}
Key concept: {key_concept}
Generate ONE question challenging how {key_concept} is measured.
Return ONLY: one research question.""",

    "model_assumption_shift": """\
Research question: {question}
Dominant claim: {dominant_claim}
Identify the most important hidden model assumption. Generate ONE question targeting it.
Return ONLY: one research question.""",

    "unit_of_analysis_shift": """\
Research question: {question}
Current analysis level: {current_unit}
Generate ONE question testing whether findings replicate at a DIFFERENT aggregation level.
Return ONLY: one research question.""",

    "evidence_standard_shift": """\
Research question: {question}
What evidence would establish a stronger causal claim than currently possible?
Generate ONE question about evidence requirements.
Return ONLY: one research question.""",

    "causal_mechanism_shift": """\
Research question: {question}
Dominant direction: {dominant_direction}
Generate ONE question about the causal mechanism through which this operates.
Return ONLY: one research question.""",

    "counterfactual_baseline_shift": """\
Research question: {question}
Dominant claim: {dominant_claim}
What is the unstated counterfactual baseline? Generate ONE question making it explicit.
Return ONLY: one research question.""",

    "failure_mode_shift": """\
Research question: {question}
Dominant claim: {dominant_claim}
Under what conditions does this claim FAIL? Generate ONE question targeting the boundary.
Return ONLY: one research question.""",
}


def select_perturbation_type(perturbation_count: int) -> str:
    return METHOD_PERTURBATION_TYPES[perturbation_count % len(METHOD_PERTURBATION_TYPES)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set:
    STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to", "for",
            "and", "or", "but", "not", "with", "by", "from", "that", "this", "it",
            "be", "as", "at", "on", "if", "its", "so", "do", "can", "will", "does"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def token_overlap(a: str, b: str) -> float:
    ta, tb = set(a.lower().split()), set(b.lower().split())
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
    return sum(1 for c in claims.values()
               if all(token_overlap(_claim_text(c), p) < 0.30 for p in prior_texts))


def epistemic_priority(c: dict) -> int:
    bases = [h.split("[")[0] for h in c.get("history", [])]
    return bases.count("T1") + bases.count("T5") + (1 if not c.get("evidence_refs") else 0)


def is_exponential(seq: list) -> bool:
    nz = [x for x in seq if x > 0]
    if len(nz) < 4:
        return False
    return all(nz[i + 1] / nz[i] >= 1.5 for i in range(len(nz) - 4, len(nz) - 1))


def method_diversity_score(trace: list) -> float:
    return len(set(trace)) / max(len(trace), 1)


def frame_diversity_score(trace: list) -> float:
    return len(set(trace)) / max(len(trace), 1)


# ---------------------------------------------------------------------------
# Context extraction for prompts
# ---------------------------------------------------------------------------

def extract_context(state: dict, question: str) -> dict:
    claims = state.get("claims", {})
    supported = [c for c in claims.values()
                 if c.get("status") == "supported" and not c.get("is_synthesis")]
    dominant = max(supported, key=lambda c: c.get("confidence", 0)) if supported \
               else (next(iter(claims.values())) if claims else {})
    dt = _claim_text(dominant)
    subjects = [c.get("subject", "").lower() for c in claims.values()]
    if any("country" in s or "nation" in s for s in subjects):
        unit = "country"
    elif any("firm" in s or "company" in s for s in subjects):
        unit = "firm"
    else:
        unit = "individual"
    key_concept = dominant.get("subject", question.split()[0]) if dominant else question.split()[0]
    return {
        "question":           question,
        "dominant_claim":     dt,
        "key_concept":        key_concept,
        "dominant_direction": dt,
        "current_unit":       unit,
    }


# ---------------------------------------------------------------------------
# Alexandria-lite validation gate (unchanged from v0.2/v0.3)
# ---------------------------------------------------------------------------

def validate_perturbation(question: str, state: dict,
                           question_history: list) -> tuple[bool, str]:
    claims = state.get("claims", {})
    for prior_q in question_history:
        if token_overlap(question, prior_q) > 0.70:
            return False, "circular"
    graph_terms = set()
    for c in claims.values():
        for field in ["subject", "predicate", "object"]:
            graph_terms.update(_tokens(c.get(field, "")))
    if not (graph_terms & _tokens(question)):
        return False, "unanchored"
    for c in claims.values():
        if c.get("sealed"):
            if token_overlap(question, _claim_text(c)) > 0.60:
                return False, f"reopens_sealed:{c.get('id', '?')}"
    return True, "admitted"


# ---------------------------------------------------------------------------
# LLM call wrapper
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=120,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


def generate_perturbation_question(ptype: str, ctx: dict) -> str:
    return call_llm(METHOD_PROMPTS[ptype].format(**ctx))


# ---------------------------------------------------------------------------
# Metrics (v0.4 extended with frame_type, question_shape, outcome_metric)
# ---------------------------------------------------------------------------

def compute_metrics(state: dict, loop: int, prior_texts: list,
                    method_type: str, frame_type: str,
                    question_shape: str, outcome_metric: str) -> dict:
    claims   = state.get("claims", {})
    total    = len(claims)
    open_c   = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel    = count_novel(claims, prior_texts)
    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))
    syntheses = sum(1 for c in claims.values() if c.get("is_synthesis"))
    counters  = all_bases.count("T5")
    evidence  = all_bases.count("T3") + all_bases.count("T6")
    branches  = sum(1 for c in claims.values() if c.get("id", "").startswith("B"))
    contr_gen = all_bases.count("T2")
    dup_rate  = redundant / max(total, 1)
    return {
        "loop":                      loop,
        "method_type":               method_type,
        "frame_type":                frame_type,
        "question_shape":            question_shape,
        "outcome_metric":            outcome_metric,
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
        "question_utility":          float(contr_gen * 3 + syntheses * 2 + counters * 2 + evidence + branches),
    }


# ---------------------------------------------------------------------------
# Failure conditions (v0.3 + FRAME_COLLAPSE)
# ---------------------------------------------------------------------------

def check_failure(current: dict, history: list, method_trace: list,
                  perturbation_log: list) -> str | None:
    last5  = history[-5:]  if len(history) >= 5  else history
    last10 = history[-10:] if len(history) >= 10 else history

    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"

    if current["semantic_duplication_rate"] > 0.60:
        return "SEMANTIC_DUPLICATION"

    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"

    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"

    if len(method_trace) >= 5:
        if method_diversity_score(method_trace[-5:]) < 0.30:
            return "METHOD_COLLAPSE"

    # FRAME_COLLAPSE (NEW v0.4)
    frame_trace = [m.get("frame_type") for m in history[-5:]]
    if len(frame_trace) == 5 and len(set(frame_trace)) / 5 < 0.30:
        return "FRAME_COLLAPSE"

    if len(history) >= 10:
        if is_exponential([m["branch_growth"] for m in history[-10:]]):
            return "BRANCH_EXPLOSION"

    perturbed_events = [e for e in perturbation_log
                        if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    if len(perturbed_events) >= 5:
        last5p = perturbed_events[-5:]
        admitted = sum(1 for e in last5p if e.get("admitted"))
        if admitted / 5 < 0.60:
            return "PERTURBATION_DRIFT"

    return None


# ---------------------------------------------------------------------------
# T10: EPISTEMIC_ROLLBACK_AND_RESEED (unchanged from v0.3)
# ---------------------------------------------------------------------------

def find_rollback_target(loop_metrics: list, failed_loop: int) -> int | None:
    failed_method = loop_metrics[failed_loop].get("method_type") if failed_loop < len(loop_metrics) else None
    for i in range(len(loop_metrics) - 2, -1, -1):
        m = loop_metrics[i]
        if (m.get("novel_claims", 0) > 0
                and m.get("entropy", 1.0) < 0.80
                and m.get("semantic_duplication_rate", 1.0) < 0.40
                and m.get("method_type") != failed_method):
            return i
    return None


def execute_t10(domain_dir: Path, loop_metrics: list, question_history: list,
                method_trace: list, perturbation_log: list,
                failed_loop: int, failure_reason: str) -> dict | None:
    target_loop = find_rollback_target(loop_metrics, failed_loop)
    if target_loop is None:
        return None

    saturated_questions = question_history[target_loop + 1:]
    saturated_methods   = method_trace[target_loop + 1:]

    rollback_event = {
        "operator":                 "T10_EPISTEMIC_ROLLBACK_AND_RESEED",
        "failed_loop":              failed_loop,
        "failure_reason":           failure_reason,
        "rollback_target_loop":     target_loop,
        "saturated_path_questions": saturated_questions,
        "saturated_path_methods":   saturated_methods,
        "saturated_path_status":    "SATURATED",
    }

    target_file = domain_dir / f"loop_{target_loop:03d}_state.json"
    with open(target_file) as f:
        rollback_state = json.load(f)

    used_types = {e.get("type") for e in perturbation_log
                  if e.get("loop", -1) >= target_loop
                  and e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"}
    candidates = [t for t in METHOD_PERTURBATION_TYPES if t not in used_types] \
                 or METHOD_PERTURBATION_TYPES

    reseed_type = candidates[len(perturbation_log) % len(candidates)]
    ctx = extract_context(rollback_state, question_history[target_loop])

    try:
        generated_q = generate_perturbation_question(reseed_type, ctx)
    except Exception as e:
        print(f"  T10 generation failed: {e}")
        rollback_event.update({"reseed_method_type": reseed_type,
                               "generated_question": "", "admitted": False,
                               "rejection_reason": "generation_failed"})
        perturbation_log.append(rollback_event)
        return None

    admitted, reason = validate_perturbation(
        generated_q, rollback_state, question_history[:target_loop + 1])

    rollback_event.update({
        "reseed_method_type": reseed_type,
        "generated_question": generated_q,
        "admitted":           admitted,
        "rejection_reason":   None if admitted else reason,
    })
    perturbation_log.append(rollback_event)

    if not admitted:
        return None

    return {
        "state":            rollback_state,
        "question":         generated_q,
        "question_history": question_history[:target_loop + 1] + [generated_q],
        "method_trace":     method_trace[:target_loop + 1],
        "loop_metrics":     loop_metrics[:target_loop + 1],
        "branch_from_loop": target_loop,
        "rollback_event":   rollback_event,
    }


# ---------------------------------------------------------------------------
# Question selection (unchanged from v0.3)
# ---------------------------------------------------------------------------

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
        key=epistemic_priority, reverse=True)
    for c in open_c:
        q = make_q(c)
        if not already_asked(q):
            return q

    for c in sorted([c for c in claims.values() if c.get("sealed") and not c.get("evidence_refs")],
                    key=lambda c: c.get("confidence", 0)):
        q = make_q(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    synth = sorted([c for c in claims.values() if c.get("is_synthesis")],
                   key=lambda c: c.get("confidence", 0), reverse=True)
    for c in synth:
        q = make_q(c, "Explore the implications of")
        if not already_asked(q):
            return q

    for c in [c for c in claims.values()
              if c.get("status") == "disputed"
              and "T1" in [h.split("[")[0] for h in c.get("history", [])]]:
        q = make_q(c, "Is there a resolution to the contradiction that")
        if not already_asked(q):
            return q

    return "LOOP_COMPLETE"


# ---------------------------------------------------------------------------
# Outcome classification (pre-registered, unchanged)
# ---------------------------------------------------------------------------

def classify_outcome(loops_completed: int, max_loops: int,
                     failure_code: str | None, loop_metrics: list) -> str:
    if failure_code:
        return failure_code
    if any(m.get("outcome") == "LOOP_COMPLETE" for m in loop_metrics):
        return "LOOP_COMPLETE"
    if loops_completed >= max_loops:
        last10 = loop_metrics[-10:]
        if (all(m["entropy"] < 0.80 for m in last10)
                and all(m["contradictions_resolved"] / max(m["total_contradictions"], 1) > 0.50 for m in last10)
                and any(m["novel_claims"] > 0 for m in loop_metrics[20:])):
            return "H1_STABLE"
        return "H0_DEGENERATION"
    return "INCOMPLETE"


# ---------------------------------------------------------------------------
# save_and_return helper (v0.4: adds frame/shape/metric traces, PTR breakdown)
# ---------------------------------------------------------------------------

def save_and_return(domain_dir: Path, loop_metrics: list, perturbation_log: list,
                    outcome_or_failure: str, question_history: list,
                    method_trace: list, seed_question: str,
                    domain_id: str, max_loops: int) -> dict:
    loops_completed = len(loop_metrics)
    failure_code    = outcome_or_failure if outcome_or_failure not in \
                      {"H1_STABLE", "H0_DEGENERATION", "LOOP_COMPLETE", "INCOMPLETE"} else None
    outcome = classify_outcome(loops_completed, max_loops, failure_code, loop_metrics)

    t10_events = [e for e in perturbation_log
                  if e.get("operator") == "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]

    frame_trace  = [m.get("frame_type", "") for m in loop_metrics]
    shape_trace  = [m.get("question_shape", "") for m in loop_metrics]
    metric_trace = [m.get("outcome_metric", "") for m in loop_metrics]

    mds = method_diversity_score(method_trace)
    fds = frame_diversity_score(frame_trace)

    all_triggers = [e.get("trigger", "") for e in perturbation_log
                    if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    n_frame    = sum(1 for t in all_triggers if t.startswith("frame_repeat:"))
    n_metric   = sum(1 for t in all_triggers if t.startswith("metric_repeat:"))
    n_shape    = sum(1 for t in all_triggers if t.startswith("shape_repeat:"))
    n_method   = sum(1 for t in all_triggers if t.startswith("method_repeat:"))
    n_fallback = sum(1 for t in all_triggers if not trigger_is_preventive(t))
    n_total    = max(len(all_triggers), 1)

    ptr = (n_frame + n_metric + n_shape + n_method) / n_total

    final_entropy = loop_metrics[-1]["entropy"] if loop_metrics else None
    novel_at_20   = loop_metrics[20]["novel_claims"] if len(loop_metrics) > 20 else None

    outcome_data = {
        "domain_id":            domain_id,
        "seed_question":        seed_question,
        "outcome":              outcome,
        "loops_completed":      loops_completed,
        "failure_code":         failure_code,
        "final_entropy":        final_entropy,
        "novel_at_loop_20":     novel_at_20,
        "method_trace":         method_trace,
        "frame_trace":          frame_trace,
        "shape_trace":          shape_trace,
        "metric_trace":         metric_trace,
        "method_diversity_score": mds,
        "frame_diversity_score":  fds,
        "preventive_trigger_rate": ptr,
        "ptr_breakdown": {
            "frame_repeat":  n_frame,
            "metric_repeat": n_metric,
            "shape_repeat":  n_shape,
            "method_repeat": n_method,
            "fallback":      n_fallback,
            "total":         len(all_triggers),
        },
        "question_history":  question_history,
        "loop_metrics":      loop_metrics,
        "perturbation_log":  perturbation_log,
        "t10_count":         len(t10_events),
        "t10_activations":   t10_events,
        "saturated_paths":   [{"questions": e.get("saturated_path_questions", []),
                               "methods":   e.get("saturated_path_methods", []),
                               "reason":    e.get("failure_reason", "")}
                              for e in t10_events],
    }

    with open(domain_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    with open(domain_dir / "perturbation_log.json", "w") as f:
        json.dump(perturbation_log, f, indent=2)
    with open(domain_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)

    fe_str = f"{final_entropy:.2f}" if final_entropy is not None else "N/A"
    p_count = sum(1 for e in perturbation_log
                  if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED")
    print(f"\n  {domain_id} outcome: {outcome} | loops={loops_completed} | "
          f"entropy={fe_str} | perturb={p_count} T10={len(t10_events)} "
          f"MDS={mds:.2f} FDS={fds:.2f} PTR={ptr:.0%}")
    return outcome_data


# ---------------------------------------------------------------------------
# Domain runner
# ---------------------------------------------------------------------------

def run_domain(domain_id: str, seed_question: str,
               max_loops: int = MAX_LOOPS) -> dict:
    domain_dir = RESULTS_DIR / domain_id
    domain_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {domain_id}: {seed_question[:58]}")
    print(f"{'='*65}")

    question           = seed_question
    question_history   = [seed_question]
    method_trace       = []
    loop_metrics       = []
    all_prior_texts    = []
    perturbation_log   = []
    perturbation_count = 0
    t10_count          = 0
    failure_code       = None
    prev_total         = 0

    loop = 0
    while loop < max_loops:
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            mt = infer_method_type(question)
            ft = infer_frame_type(question)
            qs = infer_question_shape(question)
            om = extract_outcome_metric(question, state.get("claims", {}))
            method_trace.append(mt)
            m = compute_metrics(state, loop, all_prior_texts, mt, ft, qs, om)
            loop_metrics.append(m)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            prev_total = m["total_claims"]
            question = select_next_question(state, question_history)
            if question != "LOOP_COMPLETE":
                question_history.append(question)
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

        mt = infer_method_type(question)
        ft = infer_frame_type(question)
        qs = infer_question_shape(question)
        om = extract_outcome_metric(question, state.get("claims", {}))
        method_trace.append(mt)

        # NOTE: loop_metrics does NOT include current loop yet — required for v0.4 trigger
        metrics = compute_metrics(state, loop, all_prior_texts, mt, ft, qs, om)

        print(f"  -> entropy={metrics['entropy']:.2f} | "
              f"claims={metrics['total_claims']} "
              f"(open={metrics['open_claims']} sealed={metrics['sealed_claims']}) | "
              f"novel={metrics['novel_claims']} dup={metrics['semantic_duplication_rate']:.0%} "
              f"frame={ft} method={mt}")

        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
        prev_total = metrics["total_claims"]

        # Failure check → T10 attempt
        failure = check_failure(metrics, loop_metrics, method_trace, perturbation_log)
        if failure:
            print(f"  FAILURE: {failure}")
            loop_metrics.append(metrics)  # append before T10 so rollback can find it
            if t10_count >= MAX_T10:
                print(f"  MAX_ROLLBACK_EXCEEDED ({t10_count}/{MAX_T10})")
                failure_code = failure
                break
            rollback = execute_t10(domain_dir, loop_metrics, question_history,
                                   method_trace, perturbation_log, loop, failure)
            if rollback:
                t10_count += 1
                state            = rollback["state"]
                question         = rollback["question"]
                question_history = rollback["question_history"]
                method_trace     = rollback["method_trace"]
                loop_metrics     = rollback["loop_metrics"]
                prev_total       = loop_metrics[-1]["total_claims"] if loop_metrics else 0
                print(f"  T10: rollback to loop {rollback['branch_from_loop']}, "
                      f"reseed={rollback['rollback_event']['reseed_method_type']}")
                time.sleep(2)
                continue
            else:
                print(f"  T10: no valid rollback target")
                failure_code = failure
                break

        # Perturbation trigger v0.4 (FIXED): loop_metrics is prior loops only
        do_perturb, trigger_reason = should_perturb_v04(loop_metrics, metrics)

        # Now append current metrics
        loop_metrics.append(metrics)

        if do_perturb:
            ptype = select_perturbation_type(perturbation_count)
            is_prev = trigger_is_preventive(trigger_reason)
            trigger_layer = "preventive" if is_prev else "fallback"
            print(f"  PERTURB [{ptype}] trigger={trigger_reason} layer={trigger_layer}")

            ctx = extract_context(state, question)
            try:
                gen_q = generate_perturbation_question(ptype, ctx)
            except Exception as e:
                print(f"  Perturbation generation failed: {e}")
                gen_q = ""

            admitted, reason = (False, "generation_failed") if not gen_q else \
                validate_perturbation(gen_q, state, question_history)

            event = {
                "loop":                       loop,
                "trigger":                    trigger_reason,
                "trigger_layer":              trigger_layer,
                "type":                       ptype,
                "generated_question":         gen_q,
                "inferred_frame_type":        infer_frame_type(gen_q) if gen_q else "",
                "inferred_method_type":       infer_method_type(gen_q) if gen_q else "",
                "admitted":                   admitted,
                "rejection_reason":           None if admitted else reason,
                "novelty_produced_next_loop": None,
            }
            perturbation_log.append(event)
            perturbation_count += 1

            if admitted:
                print(f"  ADMITTED: {gen_q[:70]}")
                question = gen_q
                question_history.append(gen_q)
                loop += 1
                time.sleep(1)
                continue
            else:
                print(f"  REJECTED ({reason})")

        # Normal question selection
        next_q = select_next_question(state, question_history)
        print(f"  Next Q: {next_q[:70]}")

        if next_q == "LOOP_COMPLETE":
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            break

        question_history.append(next_q)
        question = next_q
        loop += 1
        time.sleep(2)

    # Fill novelty_produced_next_loop for perturbation events
    for event in perturbation_log:
        if event.get("admitted") and event.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED":
            el = event["loop"]
            next_loops = [m for m in loop_metrics if m["loop"] > el]
            if next_loops:
                event["novelty_produced_next_loop"] = next_loops[0]["novel_claims"]

    return save_and_return(domain_dir, loop_metrics, perturbation_log,
                           failure_code or "INCOMPLETE", question_history,
                           method_trace, seed_question, domain_id, max_loops)


# ---------------------------------------------------------------------------
# Summary (v0.4: adds frame metrics, PTR breakdown, H3 verdict)
# ---------------------------------------------------------------------------

def write_summary(all_outcomes: list):
    out_path = RESULTS_DIR / "summary.md"

    p4v_avg  = sum(PAPER4_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p03_avg  = sum(PAPER5V03_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p04_avg  = sum(o["loops_completed"] for o in all_outcomes) / max(len(all_outcomes), 1)

    depth_lifts = sum(1 for o in all_outcomes
                      if o["loops_completed"] > PAPER4_BASELINE[o["domain_id"]])
    h1_confirmed = depth_lifts >= 3 and p04_avg > 3.2

    all_p_events = [e for o in all_outcomes
                    for e in o.get("perturbation_log", [])
                    if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    admitted_rate = sum(1 for e in all_p_events if e.get("admitted")) / max(len(all_p_events), 1)
    h2_drift = admitted_rate < 0.60

    # H3: PTR > 0% in ≥3 domains
    ptr_positive_domains = sum(1 for o in all_outcomes
                                if o.get("preventive_trigger_rate", 0) > 0)
    h3_confirmed = ptr_positive_domains >= 3

    # PTR breakdown totals
    total_bd = {"frame_repeat": 0, "metric_repeat": 0, "shape_repeat": 0,
                "method_repeat": 0, "fallback": 0, "total": 0}
    for o in all_outcomes:
        bd = o.get("ptr_breakdown", {})
        for k in total_bd:
            total_bd[k] += bd.get(k, 0)

    # Perturbation novelty by type
    type_novelty: dict[str, list] = {t: [] for t in METHOD_PERTURBATION_TYPES}
    for o in all_outcomes:
        for e in o.get("perturbation_log", []):
            if e.get("admitted") and e.get("type") in type_novelty:
                n = e.get("novelty_produced_next_loop", 0) or 0
                type_novelty[e["type"]].append(n)
    type_avg = {t: (sum(v) / len(v) if v else 0.0) for t, v in type_novelty.items()}
    best_type = max(type_avg, key=lambda t: type_avg[t]) if any(type_avg.values()) else "—"

    with open(out_path, "w") as f:
        f.write("# Paper 5 v0.4a — Frame/Metric/Shape Fixation Triggers\n\n")
        f.write("## Pre-Registered Hypotheses\n\n")
        f.write("**H1:** Frame/metric fixation triggers extend avg loop depth > 3.2 (P4) on ≥3/5 domains.  \n")
        f.write("**H0:** No effect.  \n")
        f.write("**H2:** Perturbation drift (admission rate < 0.60 across ≥5 consecutive events).  \n")
        f.write("**H3:** PTR > 0% in at least 3/5 domains (preventive trigger actually fires).  \n\n")

        f.write("## Three-Way Comparison\n\n")
        f.write("| Domain | P4 Loops | P5v03 Loops | P5v04 Loops | Lift vs P4 | Outcome |\n")
        f.write("|---|---|---|---|---|---|\n")
        for o in all_outcomes:
            did  = o["domain_id"]
            p4l  = PAPER4_BASELINE[did]
            p03l = PAPER5V03_BASELINE[did]
            p04l = o["loops_completed"]
            lift = p04l - p4l
            f.write(f"| {did} | {p4l} | {p03l} | {p04l} | "
                    f"{'+'if lift>=0 else ''}{lift} | **{o['outcome']}** |\n")
        f.write(f"\n**Avg loop depth — P4:** {p4v_avg:.1f}  \n")
        f.write(f"**Avg loop depth — P5v03:** {p03_avg:.1f}  \n")
        f.write(f"**Avg loop depth — P5v04:** {p04_avg:.1f}  \n")
        f.write(f"**Domains with depth lift vs P4:** {depth_lifts}/5  \n\n")

        f.write("## Frame and Method Metrics\n\n")
        f.write("| Domain | MDS | FDS | PTR | T10 |\n")
        f.write("|---|---|---|---|---|\n")
        for o in all_outcomes:
            f.write(f"| {o['domain_id']} | {o.get('method_diversity_score',0):.2f} | "
                    f"{o.get('frame_diversity_score',0):.2f} | "
                    f"{o.get('preventive_trigger_rate',0):.0%} | "
                    f"{o.get('t10_count',0)} |\n")

        f.write("\n## PTR Breakdown (across all domains)\n\n")
        n = max(total_bd["total"], 1)
        f.write(f"| Trigger type | Count | % |\n|---|---|---|\n")
        for k in ["frame_repeat", "metric_repeat", "shape_repeat", "method_repeat", "fallback"]:
            f.write(f"| {k} | {total_bd[k]} | {total_bd[k]/n:.0%} |\n")
        f.write(f"| **total** | **{total_bd['total']}** | |\n\n")

        most_common_trigger = max(
            ["frame_repeat", "metric_repeat", "shape_repeat", "method_repeat", "fallback"],
            key=lambda k: total_bd[k])
        f.write(f"**Most common trigger:** {most_common_trigger} ({total_bd[most_common_trigger]})  \n")
        f.write(f"**Domains with PTR > 0%:** {ptr_positive_domains}/5  \n\n")

        f.write("## Perturbation Novelty Lift by Type\n\n")
        f.write("| Type | Avg novel claims | n admitted |\n|---|---|---|\n")
        for t in METHOD_PERTURBATION_TYPES:
            f.write(f"| {t} | {type_avg[t]:.2f} | {len(type_novelty[t])} |\n")
        f.write(f"\n**Best type:** {best_type} ({type_avg.get(best_type,0):.2f})  \n")
        f.write(f"**Overall admission rate:** {admitted_rate:.0%}  \n\n")

        f.write("## Per-Domain Details\n\n")
        for o in all_outcomes:
            f.write(f"### {o['domain_id']}\n\n")
            f.write(f"**Outcome:** {o['outcome']} | Loops: {o['loops_completed']} "
                    f"(P4={PAPER4_BASELINE[o['domain_id']]}, "
                    f"P5v03={PAPER5V03_BASELINE[o['domain_id']]})  \n")
            f.write(f"**MDS:** {o.get('method_diversity_score',0):.2f} | "
                    f"**FDS:** {o.get('frame_diversity_score',0):.2f} | "
                    f"**PTR:** {o.get('preventive_trigger_rate',0):.0%} | "
                    f"**T10:** {o.get('t10_count',0)}  \n\n")
            bd = o.get("ptr_breakdown", {})
            f.write(f"PTR breakdown: frame={bd.get('frame_repeat',0)} "
                    f"metric={bd.get('metric_repeat',0)} "
                    f"shape={bd.get('shape_repeat',0)} "
                    f"method={bd.get('method_repeat',0)} "
                    f"fallback={bd.get('fallback',0)}  \n\n")
            f.write("| Loop | Frame | Method | Shape | Entropy | Novel | Dup% |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for m in o.get("loop_metrics", []):
                f.write(f"| {m['loop']} | {m.get('frame_type','?')} | "
                        f"{m.get('method_type','?')} | {m.get('question_shape','?')} | "
                        f"{m['entropy']:.2f} | {m['novel_claims']} | "
                        f"{m['semantic_duplication_rate']:.0%} |\n")
            plog = [e for e in o.get("perturbation_log", [])
                    if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
            t10s = [e for e in o.get("perturbation_log", [])
                    if e.get("operator") == "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
            if plog:
                f.write(f"\n**Perturbations ({len(plog)}):**\n")
                for e in plog:
                    st = "✓" if e["admitted"] else "✗"
                    f.write(f"- Loop {e['loop']} [{e['type']}] ({e['trigger_layer']}) {st}")
                    if not e["admitted"]:
                        f.write(f" — {e['rejection_reason']}")
                    elif e.get("novelty_produced_next_loop") is not None:
                        f.write(f" → novel={e['novelty_produced_next_loop']}")
                    f.write(f"\n  trigger={e['trigger']}  \n")
                    f.write(f"  Q: {e['generated_question'][:80]}\n")
            if t10s:
                f.write(f"\n**T10 Rollbacks ({len(t10s)}):**\n")
                for e in t10s:
                    f.write(f"- Loop {e['failed_loop']} → rollback to {e['rollback_target_loop']} "
                            f"[{e.get('reseed_method_type','')}] "
                            f"{'✓' if e.get('admitted') else '✗'}\n")
            f.write("\n")

        f.write("## Hypothesis Verdict\n\n")
        f.write(f"**H1:** {'CONFIRMED' if h1_confirmed else 'NOT CONFIRMED'} — "
                f"avg depth {p04_avg:.1f} vs P4 {p4v_avg:.1f}, {depth_lifts}/5 with lift  \n")
        f.write(f"**H2 (drift):** {'CONFIRMED (drift)' if h2_drift else 'NOT CONFIRMED (no drift)'} — "
                f"admission rate {admitted_rate:.0%}  \n")
        f.write(f"**H3 (PTR > 0%):** {'CONFIRMED' if h3_confirmed else 'NOT CONFIRMED'} — "
                f"PTR > 0% in {ptr_positive_domains}/5 domains  \n")
        f.write(f"**H0:** {'Cannot reject' if not h1_confirmed else 'Rejected'}  \n\n")
        f.write("Reported honestly per pre-registration.\n")

    print(f"\nSummary: {out_path}")
    print(f"H1: {'CONFIRMED' if h1_confirmed else 'NOT CONFIRMED'} "
          f"(avg {p04_avg:.1f} vs P4 {p4v_avg:.1f}, {depth_lifts}/5 lift)")
    print(f"H3: {'CONFIRMED' if h3_confirmed else 'NOT CONFIRMED'} "
          f"(PTR>0% in {ptr_positive_domains}/5 domains)")


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
    orr = OpenAI(api_key=ok, base_url="https://openrouter.ai/api/v1",
                 default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                                  "X-Title": "DES Paper5v04a FrameFixation"})
    return ds4, orr


def run_all():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    import des as des_module_local
    ds4_client, orr_client = _make_clients()
    des_module_local._clients["deepseek"]   = ds4_client
    des_module_local._clients["openrouter"] = orr_client
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER

    global des_module, or_client_g
    des_module  = des_module_local
    or_client_g = orr_client

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

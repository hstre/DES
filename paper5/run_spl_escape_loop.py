"""
Paper 5 v0.5 — SPL Geometric Attractor Detection and Semantic Escape.

Key correction from v0.4a: attractor forms within DES runs (claim level),
not between runs. detect_attractor_in_claims() fires after each DES run,
before the next loop starts.

Trigger hierarchy (should_perturb_v05):
  PRIMARY   — SPL claim-level: claim_curvature / claim_proximity
  SECONDARY — v0.4a heuristics: frame_repeat / metric_repeat / shape_repeat
  FALLBACK  — content_redundancy / novelty_zero_x3

T10 EPISTEMIC_ROLLBACK_AND_RESEED: unchanged from v0.3.
Output: paper5/batch_results_paper5_v05/

Pre-registered hypotheses, failure conditions, and T10 — do not modify.
"""

import json, os, re, shutil, sys, time
from collections import Counter
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from spl_wrapper import (
    get_spl, project, centroid, distance,
    detect_attractor_in_claims, select_escape_vector,
    compute_claim_metrics, check_false_escape,
)

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

PAPER4_BASELINE    = {"R01": 2, "R02": 3, "R03": 4, "R04": 3, "R05": 4}
PAPER5V02_BASELINE = {"R01": 7, "R02": 2, "R03": 2, "R04": 1, "R05": 4}
PAPER5V03_BASELINE = {"R01": 1, "R02": 5, "R03": 2, "R04": 1, "R05": 4}
PAPER5V04_BASELINE = {"R01": 3, "R02": 2, "R03": 1, "R04": 1, "R05": 1}

RESULTS_DIR = Path("paper5/batch_results_paper5_v05")
STATE_SRC   = Path("des_state.json")

des_module  = None
or_client_g = None


# ---------------------------------------------------------------------------
# Method, frame, shape, metric inference (v0.4a heuristics — kept for fallback)
# ---------------------------------------------------------------------------

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
# Perturbation type selection and prompts (method-level, from v0.3)
# ---------------------------------------------------------------------------

METHOD_PERTURBATION_TYPES = [
    "measurement_shift", "model_assumption_shift", "unit_of_analysis_shift",
    "evidence_standard_shift", "causal_mechanism_shift",
    "counterfactual_baseline_shift", "failure_mode_shift",
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

ESCAPE_GENERATION_PROMPT = """\
Current research question: {question}
Attractor centroid (dominant relational patterns): {top_relations}
(The last DES run produced claims clustering around these patterns.)

The current ClaimGraph has high semantic tension. Generate {k} research questions that:
1. Stay within the same domain ({domain})
2. Use DIFFERENT relational structures than the dominant patterns above
3. Would be likely to produce empirically novel claims not yet in the graph

Return ONLY: {k} research questions, one per line, no numbering."""


def select_perturbation_type(perturbation_count: int) -> str:
    return METHOD_PERTURBATION_TYPES[perturbation_count % len(METHOD_PERTURBATION_TYPES)]


def trigger_is_spl(trigger: str) -> bool:
    return trigger.startswith("claim_curvature:") or trigger.startswith("claim_proximity:")


def trigger_is_heuristic(trigger: str) -> bool:
    return any(trigger.startswith(p) for p in
               ["frame_repeat:", "metric_repeat:", "shape_repeat:", "method_repeat:"])


def trigger_is_preventive(trigger: str) -> bool:
    return trigger_is_spl(trigger) or trigger_is_heuristic(trigger)


# ---------------------------------------------------------------------------
# Context extraction for method prompts
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
        "question": question, "dominant_claim": dt, "key_concept": key_concept,
        "dominant_direction": dt, "current_unit": unit,
    }


# ---------------------------------------------------------------------------
# Trigger hierarchy v0.5
# ---------------------------------------------------------------------------

def should_perturb_v05(
    loop_metrics: list,
    current: dict,
    current_question: str,
    state: dict = None,
    next_question: str = None,
) -> tuple:
    """
    PRIMARY: SPL claim-level detection (after DES run, before next loop).
    SECONDARY: v0.4a heuristics.
    FALLBACK: content redundancy.
    """
    # PRIMARY: SPL
    if state is not None and next_question is not None:
        detected, reason, ctx = detect_attractor_in_claims(
            state, next_question, epsilon=0.25, k_threshold=0.55)
        if detected:
            return True, reason, ctx

    # SECONDARY: frame fixation
    if loop_metrics:
        pf = loop_metrics[-1].get("frame_type")
        cf = current.get("frame_type")
        if pf and cf and pf == cf:
            return True, f"frame_repeat:{cf}", {}

    # SECONDARY: metric fixation
    if loop_metrics:
        pm = loop_metrics[-1].get("outcome_metric")
        cm = current.get("outcome_metric")
        if pm and cm and pm == cm and pm != "unknown":
            return True, f"metric_repeat:{cm}", {}

    # SECONDARY: shape fixation
    if loop_metrics:
        ps = loop_metrics[-1].get("question_shape")
        cs = current.get("question_shape")
        if ps and cs and ps == cs:
            return True, f"shape_repeat:{cs}", {}

    # FALLBACK
    if current.get("semantic_duplication_rate", 0) > 0.40:
        return True, "content_redundancy>0.40", {}
    last3 = loop_metrics[-3:] if len(loop_metrics) >= 3 else []
    if len(last3) == 3 and all(m.get("novel_claims", 0) == 0 for m in last3):
        return True, "novelty_zero_x3", {}

    return False, "", {}


# ---------------------------------------------------------------------------
# Alexandria-lite validation gate
# ---------------------------------------------------------------------------

def validate_perturbation(question: str, state: dict,
                           question_history: list) -> tuple:
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
                return False, f"reopens_sealed:{c.get('id','?')}"
    return True, "admitted"


# ---------------------------------------------------------------------------
# LLM calls
# ---------------------------------------------------------------------------

def call_llm(prompt: str, max_tokens: int = 120) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


def generate_perturbation_question(ptype: str, ctx: dict) -> str:
    return call_llm(METHOD_PROMPTS[ptype].format(**ctx))


def generate_escape_candidates(
    question: str,
    attractor_centroid: dict,
    state: dict,
    k: int = 5,
) -> list:
    top_relations = sorted(attractor_centroid.items(), key=lambda x: -x[1])[:3]
    top_rel_str = ", ".join(f"{r}({p:.2f})" for r, p in top_relations)
    domain = state.get("seed_question", question)[:60]
    prompt = ESCAPE_GENERATION_PROMPT.format(
        question=question, top_relations=top_rel_str,
        k=k, domain=domain,
    )
    raw = call_llm(prompt, max_tokens=500)
    candidates = [line.strip() for line in raw.split("\n")
                  if line.strip() and len(line.strip()) > 20]
    return candidates[:k]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(state: dict, loop: int, prior_texts: list,
                    method_type: str, frame_type: str,
                    question_shape: str, outcome_metric: str,
                    question: str) -> dict:
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

    # SPL claim metrics
    spl_m = compute_claim_metrics(state)

    return {
        "loop":                      loop,
        "question":                  question,
        "method_type":               method_type,
        "frame_type":                frame_type,
        "question_shape":            question_shape,
        "outcome_metric":            outcome_metric,
        "claim_centroid":            spl_m["claim_centroid"],
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
        "total_contradictions":      max(counters, 1),
        "question_utility":          float(contr_gen * 3 + syntheses * 2 + counters * 2 + evidence + branches),
    }


# ---------------------------------------------------------------------------
# Failure conditions
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
    if len(method_trace) >= 5 and method_diversity_score(method_trace[-5:]) < 0.30:
        return "METHOD_COLLAPSE"

    frame_trace = [m.get("frame_type") for m in history[-5:]]
    if len(frame_trace) == 5 and len(set(frame_trace)) / 5 < 0.30:
        return "FRAME_COLLAPSE"

    if len(history) >= 10 and is_exponential([m["branch_growth"] for m in history[-10:]]):
        return "BRANCH_EXPLOSION"

    perturbed_events = [e for e in perturbation_log
                        if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    if len(perturbed_events) >= 5:
        admitted = sum(1 for e in perturbed_events[-5:] if e.get("admitted"))
        if admitted / 5 < 0.60:
            return "PERTURBATION_DRIFT"

    if check_false_escape(perturbation_log, history):
        return "FALSE_ESCAPE"

    return None


# ---------------------------------------------------------------------------
# T10: EPISTEMIC_ROLLBACK_AND_RESEED (unchanged from v0.3)
# ---------------------------------------------------------------------------

def find_rollback_target(loop_metrics: list, failed_loop: int) -> int | None:
    failed_method = (loop_metrics[failed_loop].get("method_type")
                     if failed_loop < len(loop_metrics) else None)
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

    with open(domain_dir / f"loop_{target_loop:03d}_state.json") as f:
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
# Question selection
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

    for c in sorted([c for c in claims.values() if c.get("is_synthesis")],
                    key=lambda c: c.get("confidence", 0), reverse=True):
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
# Outcome classification
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
# save_and_return
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

    frame_trace = [m.get("frame_type", "") for m in loop_metrics]
    mds = method_diversity_score(method_trace)
    fds = frame_diversity_score(frame_trace)

    all_triggers = [e.get("trigger", "") for e in perturbation_log
                    if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    n_spl      = sum(1 for t in all_triggers if trigger_is_spl(t))
    n_heur     = sum(1 for t in all_triggers if trigger_is_heuristic(t))
    n_fallback = sum(1 for t in all_triggers if not trigger_is_preventive(t))
    n_total    = max(len(all_triggers), 1)
    ptr = (n_spl + n_heur) / n_total

    spl_p_events = [e for e in perturbation_log
                    if trigger_is_spl(e.get("trigger", ""))
                    and e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    avg_escape_dist = (sum(e.get("escape_distance", 0) for e in spl_p_events)
                       / max(len(spl_p_events), 1))
    false_escape_count = sum(
        1 for e in spl_p_events
        if e.get("escape_distance", 0) > 0.40
        and e.get("novelty_produced_next_loop", 1) == 0
    )

    final_entropy = loop_metrics[-1]["entropy"] if loop_metrics else None
    novel_at_20   = loop_metrics[20]["novel_claims"] if len(loop_metrics) > 20 else None

    outcome_data = {
        "domain_id":             domain_id,
        "seed_question":         seed_question,
        "outcome":               outcome,
        "loops_completed":       loops_completed,
        "failure_code":          failure_code,
        "final_entropy":         final_entropy,
        "novel_at_loop_20":      novel_at_20,
        "method_trace":          method_trace,
        "frame_trace":           frame_trace,
        "method_diversity_score": mds,
        "frame_diversity_score":  fds,
        "preventive_trigger_rate": ptr,
        "ptr_breakdown": {
            "spl":      n_spl,
            "heuristic": n_heur,
            "fallback":  n_fallback,
            "total":     len(all_triggers),
        },
        "avg_escape_distance": avg_escape_dist,
        "false_escape_count":  false_escape_count,
        "question_history":    question_history,
        "loop_metrics":        loop_metrics,
        "perturbation_log":    perturbation_log,
        "t10_count":           len(t10_events),
        "t10_activations":     t10_events,
        "saturated_paths":     [{"questions": e.get("saturated_path_questions", []),
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
          f"MDS={mds:.2f} FDS={fds:.2f} PTR={ptr:.0%} "
          f"SPL={n_spl} escape_dist={avg_escape_dist:.3f}")
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
    loop0_projection   = None   # stored on loop 0 for drift calc

    loop = 0
    while loop < max_loops:
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            if loop == 0:
                loop0_projection = project(seed_question)
            mt = infer_method_type(question)
            ft = infer_frame_type(question)
            qs = infer_question_shape(question)
            om = extract_outcome_metric(question, state.get("claims", {}))
            method_trace.append(mt)
            m = compute_metrics(state, loop, all_prior_texts, mt, ft, qs, om, question)
            loop_metrics.append(m)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            prev_total = m["total_claims"]
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

        # Store seed question in state for escape generation prompt
        state["seed_question"] = seed_question

        if loop == 0:
            loop0_projection = project(seed_question)

        mt = infer_method_type(question)
        ft = infer_frame_type(question)
        qs = infer_question_shape(question)
        om = extract_outcome_metric(question, state.get("claims", {}))
        method_trace.append(mt)

        # Compute metrics — loop_metrics does NOT include current loop yet
        metrics = compute_metrics(state, loop, all_prior_texts, mt, ft, qs, om, question)

        print(f"  -> entropy={metrics['entropy']:.2f} | "
              f"claims={metrics['total_claims']} "
              f"(open={metrics['open_claims']} sealed={metrics['sealed_claims']}) | "
              f"novel={metrics['novel_claims']} dup={metrics['semantic_duplication_rate']:.0%} "
              f"K(G)={metrics['claim_curvature']:.3f} frame={ft}")

        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
        prev_total = metrics["total_claims"]

        # Failure check → T10
        failure = check_failure(metrics, loop_metrics, method_trace, perturbation_log)
        if failure:
            print(f"  FAILURE: {failure}")
            loop_metrics.append(metrics)
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

        # v0.5 KEY: select next question candidate FIRST, then check triggers
        next_q_candidate = select_next_question(state, question_history)
        if next_q_candidate == "LOOP_COMPLETE":
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            loop_metrics.append(metrics)
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            break

        # Check triggers v0.5 — SPL uses (state, next_q_candidate)
        do_perturb, trigger_reason, spl_ctx = should_perturb_v05(
            loop_metrics, metrics, question,
            state=state, next_question=next_q_candidate,
        )

        # Now append current metrics
        loop_metrics.append(metrics)

        if do_perturb:
            is_spl = trigger_is_spl(trigger_reason)
            is_heur = trigger_is_heuristic(trigger_reason)
            if is_spl:
                layer = "spl"
                ptype = "semantic_escape"
            elif is_heur:
                layer = "heuristic"
                ptype = select_perturbation_type(perturbation_count)
            else:
                layer = "fallback"
                ptype = select_perturbation_type(perturbation_count)

            print(f"  PERTURB [{ptype}] trigger={trigger_reason} layer={layer}")

            gen_q = ""
            escape_dist = 0.0
            score_ctx_out: dict = {}

            if is_spl:
                attractor_c = spl_ctx.get("claim_centroid", {})
                try:
                    cands = generate_escape_candidates(question, attractor_c, state, k=5)
                except Exception as e:
                    print(f"  Escape generation failed: {e}")
                    cands = []
                if cands:
                    gen_q, score_ctx_out = select_escape_vector(
                        cands, attractor_c, state, loop0_projection)
                    escape_dist = score_ctx_out.get("escape_distance", 0.0)
                    print(f"  Escape candidates: {len(cands)}, best dist={escape_dist:.3f}")
            else:
                ctx = extract_context(state, question)
                try:
                    gen_q = generate_perturbation_question(ptype, ctx)
                except Exception as e:
                    print(f"  Perturbation generation failed: {e}")

            admitted, reason = (False, "generation_failed") if not gen_q else \
                validate_perturbation(gen_q, state, question_history)

            event = {
                "loop":                       loop,
                "trigger":                    trigger_reason,
                "trigger_layer":              layer,
                "type":                       ptype,
                "escape_distance":            escape_dist,
                "composite_score":            score_ctx_out.get("composite_score", 0.0),
                "all_scores":                 score_ctx_out.get("all_scores", []),
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

        # Not perturbing or rejected: use candidate question
        question_history.append(next_q_candidate)
        question = next_q_candidate
        loop += 1
        time.sleep(2)

    # Backfill novelty_produced_next_loop
    for event in perturbation_log:
        if event.get("admitted") and event.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED":
            el = event["loop"]
            nxt = [m for m in loop_metrics if m["loop"] > el]
            if nxt:
                event["novelty_produced_next_loop"] = nxt[0]["novel_claims"]

    return save_and_return(domain_dir, loop_metrics, perturbation_log,
                           failure_code or "INCOMPLETE", question_history,
                           method_trace, seed_question, domain_id, max_loops)


# ---------------------------------------------------------------------------
# Summary (five-way comparison)
# ---------------------------------------------------------------------------

def write_summary(all_outcomes: list):
    out_path = RESULTS_DIR / "summary.md"

    p4_avg  = sum(PAPER4_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p02_avg = sum(PAPER5V02_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p03_avg = sum(PAPER5V03_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p04_avg = sum(PAPER5V04_BASELINE[o["domain_id"]] for o in all_outcomes) / max(len(all_outcomes), 1)
    p05_avg = sum(o["loops_completed"] for o in all_outcomes) / max(len(all_outcomes), 1)

    depth_lifts = sum(1 for o in all_outcomes
                      if o["loops_completed"] > PAPER4_BASELINE[o["domain_id"]])
    h1_confirmed = depth_lifts >= 3 and p05_avg > 3.2

    all_p_events = [e for o in all_outcomes
                    for e in o.get("perturbation_log", [])
                    if e.get("operator") != "T10_EPISTEMIC_ROLLBACK_AND_RESEED"]
    admitted_rate = (sum(1 for e in all_p_events if e.get("admitted"))
                     / max(len(all_p_events), 1))
    h2_drift = admitted_rate < 0.60

    ptr_positive = sum(1 for o in all_outcomes if o.get("preventive_trigger_rate", 0) > 0)
    h4_confirmed = ptr_positive >= 3 and p05_avg > 3.2

    # SPL vs heuristic novelty
    spl_novelty, heur_novelty = [], []
    for o in all_outcomes:
        for e in o.get("perturbation_log", []):
            if e.get("admitted") and e.get("novelty_produced_next_loop") is not None:
                if trigger_is_spl(e.get("trigger", "")):
                    spl_novelty.append(e["novelty_produced_next_loop"])
                elif trigger_is_heuristic(e.get("trigger", "")):
                    heur_novelty.append(e["novelty_produced_next_loop"])

    spl_avg_nov  = sum(spl_novelty) / max(len(spl_novelty), 1)
    heur_avg_nov = sum(heur_novelty) / max(len(heur_novelty), 1)

    # PTR breakdowns
    total_bd = {"spl": 0, "heuristic": 0, "fallback": 0, "total": 0}
    for o in all_outcomes:
        bd = o.get("ptr_breakdown", {})
        for k in total_bd:
            total_bd[k] += bd.get(k, 0)

    # FALSE_ESCAPE totals
    total_false_escape = sum(o.get("false_escape_count", 0) for o in all_outcomes)
    total_spl_events   = total_bd["spl"]
    avg_escape_dist    = (sum(o.get("avg_escape_distance", 0) for o in all_outcomes
                              if o.get("ptr_breakdown", {}).get("spl", 0) > 0)
                          / max(sum(1 for o in all_outcomes
                                    if o.get("ptr_breakdown", {}).get("spl", 0) > 0), 1))

    with open(out_path, "w") as f:
        f.write("# Paper 5 v0.5 — SPL Geometric Attractor Detection\n\n")
        f.write("## Pre-Registered Hypotheses\n\n")
        f.write("**H1:** SPL detection extends avg loop depth > 3.2 (P4) on ≥3/5 domains.  \n")
        f.write("**H0:** No effect.  \n")
        f.write("**H2:** Drift (admission rate < 0.60 across ≥5 events).  \n")
        f.write("**H4:** SPL fires in ≥3/5 domains AND avg depth > 3.2.  \n\n")

        f.write("## Five-Way Comparison\n\n")
        f.write("| Domain | P4 | P5v02 | P5v03 | P5v04a | P5v05 | Lift vs P4 | Outcome |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for o in all_outcomes:
            did = o["domain_id"]
            lift = o["loops_completed"] - PAPER4_BASELINE[did]
            f.write(f"| {did} | {PAPER4_BASELINE[did]} | {PAPER5V02_BASELINE[did]} | "
                    f"{PAPER5V03_BASELINE[did]} | {PAPER5V04_BASELINE[did]} | "
                    f"{o['loops_completed']} | {'+'if lift>=0 else ''}{lift} | "
                    f"**{o['outcome']}** |\n")
        f.write(f"\n**Avg — P4:** {p4_avg:.1f} | **P5v02:** {p02_avg:.1f} | "
                f"**P5v03:** {p03_avg:.1f} | **P5v04a:** {p04_avg:.1f} | "
                f"**P5v05:** {p05_avg:.1f}  \n")
        f.write(f"**Domains with depth lift vs P4:** {depth_lifts}/5  \n\n")

        f.write("## SPL Metrics\n\n")
        f.write("| Domain | MDS | FDS | PTR | SPL triggers | T10 | Avg escape dist |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for o in all_outcomes:
            bd = o.get("ptr_breakdown", {})
            f.write(f"| {o['domain_id']} | {o.get('method_diversity_score',0):.2f} | "
                    f"{o.get('frame_diversity_score',0):.2f} | "
                    f"{o.get('preventive_trigger_rate',0):.0%} | "
                    f"{bd.get('spl',0)} | {o.get('t10_count',0)} | "
                    f"{o.get('avg_escape_distance',0):.3f} |\n")

        f.write("\n## PTR Breakdown (across all domains)\n\n")
        n = max(total_bd["total"], 1)
        f.write("| Trigger type | Count | % |\n|---|---|---|\n")
        for k in ["spl", "heuristic", "fallback"]:
            f.write(f"| {k} | {total_bd[k]} | {total_bd[k]/n:.0%} |\n")
        f.write(f"| **total** | **{total_bd['total']}** | |\n\n")
        f.write(f"**Domains with PTR > 0%:** {ptr_positive}/5  \n")
        f.write(f"**FALSE_ESCAPE events:** {total_false_escape}  \n")
        f.write(f"**Avg escape distance (SPL events):** {avg_escape_dist:.3f}  \n\n")

        f.write("## Novelty: SPL vs Heuristic Triggers\n\n")
        f.write(f"| Trigger type | Avg novel claims | n events |\n|---|---|---|\n")
        f.write(f"| spl | {spl_avg_nov:.2f} | {len(spl_novelty)} |\n")
        f.write(f"| heuristic | {heur_avg_nov:.2f} | {len(heur_novelty)} |\n\n")

        f.write("## Per-Domain Details\n\n")
        for o in all_outcomes:
            did = o["domain_id"]
            f.write(f"### {did}\n\n")
            f.write(f"**Outcome:** {o['outcome']} | Loops: {o['loops_completed']} "
                    f"(P4={PAPER4_BASELINE[did]}, P5v04a={PAPER5V04_BASELINE[did]})  \n")
            bd = o.get("ptr_breakdown", {})
            f.write(f"**MDS:** {o.get('method_diversity_score',0):.2f} | "
                    f"**FDS:** {o.get('frame_diversity_score',0):.2f} | "
                    f"**PTR:** {o.get('preventive_trigger_rate',0):.0%} | "
                    f"**T10:** {o.get('t10_count',0)}  \n")
            f.write(f"PTR: spl={bd.get('spl',0)} heuristic={bd.get('heuristic',0)} "
                    f"fallback={bd.get('fallback',0)}  \n\n")
            f.write("| Loop | Frame | Method | K(G) | Entropy | Novel | Dup% |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for m in o.get("loop_metrics", []):
                f.write(f"| {m['loop']} | {m.get('frame_type','?')} | "
                        f"{m.get('method_type','?')} | "
                        f"{m.get('claim_curvature',0):.3f} | "
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
                    f.write(f"\n  trigger={e['trigger']} dist={e.get('escape_distance',0):.3f}  \n")
                    if e.get("generated_question"):
                        f.write(f"  Q: {e['generated_question'][:80]}\n")
            if t10s:
                f.write(f"\n**T10 Rollbacks ({len(t10s)}):**\n")
                for e in t10s:
                    f.write(f"- Loop {e['failed_loop']} → rollback to "
                            f"{e['rollback_target_loop']} "
                            f"[{e.get('reseed_method_type','')}] "
                            f"{'✓' if e.get('admitted') else '✗'}\n")
            f.write("\n")

        f.write("## Hypothesis Verdict\n\n")
        f.write(f"**H1:** {'CONFIRMED' if h1_confirmed else 'NOT CONFIRMED'} — "
                f"avg depth {p05_avg:.1f} vs P4 {p4_avg:.1f}, {depth_lifts}/5 with lift  \n")
        f.write(f"**H2 (drift):** {'CONFIRMED' if h2_drift else 'NOT CONFIRMED (no drift)'} — "
                f"admission rate {admitted_rate:.0%}  \n")
        f.write(f"**H4 (SPL fires + depth):** {'CONFIRMED' if h4_confirmed else 'NOT CONFIRMED'} — "
                f"PTR>0% in {ptr_positive}/5, avg depth {p05_avg:.1f}  \n")
        f.write(f"**H0:** {'Cannot reject' if not h1_confirmed else 'Rejected'}  \n\n")
        f.write("Reported honestly per pre-registration.\n")

    print(f"\nSummary: {out_path}")
    print(f"H1: {'CONFIRMED' if h1_confirmed else 'NOT CONFIRMED'} "
          f"(avg {p05_avg:.1f} vs P4 {p4_avg:.1f}, {depth_lifts}/5 lift)")
    print(f"H4: {'CONFIRMED' if h4_confirmed else 'NOT CONFIRMED'} "
          f"(SPL PTR>0% in {ptr_positive}/5 domains)")


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
                                  "X-Title": "DES Paper5v05 SPLEscape"})
    return ds4, orr


def run_all():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading SPL (SentenceTransformer all-MiniLM-L6-v2)...")
    get_spl()
    print("SPL ready.\n")

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

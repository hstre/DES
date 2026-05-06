"""
paper8/mol.py
Method Operator Library for Paper 8.
Four operators derived from Paper 7 persona data.
Each operator separates algorithmic components from LLM-required components.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from spl_wrapper import project, centroid, distance
except ImportError:
    project = centroid = distance = None


# ── Operator Schema ──────────────────────────────────────────────────────────

@dataclass
class MethodOperator:
    operator_id: str
    origin_handle: str        # discovery handle (persona name), not causal entity
    core_move: str
    target_failure_modes: list
    best_domains: list
    risky_domains: list
    algorithmic_components: list   # what runs without LLM
    llm_prompt_template: str
    metrics: list
    known_successes: list = field(default_factory=list)
    known_failures: list = field(default_factory=list)


# ── Algorithmic Components ────────────────────────────────────────────────────

def extract_dominant_motif(claims: dict) -> dict:
    """
    Find the dominant subject/predicate in the ClaimGraph.
    Algorithmic: no LLM needed.
    Returns: {subject, predicate, frequency, supporting_claims}
    """
    sealed = [c for c in claims.values() if c.get("sealed") or
              c.get("status") in ("supported", "established")]
    if not sealed:
        return {"subject": "", "predicate": "", "frequency": 0}

    subject_counts = Counter(c.get("subject", "") for c in sealed if c.get("subject"))
    predicate_counts = Counter(c.get("predicate", "") for c in sealed if c.get("predicate"))

    dominant_subject = subject_counts.most_common(1)[0][0] if subject_counts else ""
    dominant_predicate = predicate_counts.most_common(1)[0][0] if predicate_counts else ""

    supporting = [c for c in sealed
                  if c.get("subject") == dominant_subject]

    return {
        "subject": dominant_subject,
        "predicate": dominant_predicate,
        "frequency": subject_counts.get(dominant_subject, 0),
        "supporting_claims": len(supporting),
        "total_sealed": len(sealed),
    }


def extract_core_tension(claims: dict) -> str:
    """
    Find the main unresolved tension in the ClaimGraph.
    Algorithmic: look for disputed claims or high-contradiction-count claims.
    """
    disputed = [c for c in claims.values()
                if c.get("status") == "disputed" and c.get("subject")]
    if disputed:
        best = max(disputed, key=lambda c: len(c.get("history", [])))
        return f"{best.get('subject','')} {best.get('predicate','')} {best.get('object','')}"

    # Fallback: claim with most T1/T5 in history
    contradiction_rich = [c for c in claims.values()
                          if any(t in c.get("history", []) for t in ("T1", "T5"))]
    if contradiction_rich:
        best = max(contradiction_rich,
                   key=lambda c: sum(1 for t in c.get("history", []) if t in ("T1","T5")))
        return f"{best.get('subject','')} {best.get('predicate','')} {best.get('object','')}"

    return "unresolved tension not identified"


def extract_invariants(claims: dict) -> list:
    """
    Find structural invariants: claims that survived longest without contradiction.
    Algorithmic: sort by history length + T8 (sealing) presence.
    """
    stable = [c for c in claims.values()
              if c.get("sealed") and "T1" not in c.get("history", [])
              and "T5" not in c.get("history", [])]
    stable.sort(key=lambda c: c.get("confidence", 0), reverse=True)
    return [
        {
            "claim": f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}",
            "confidence": c.get("confidence", 0),
        }
        for c in stable[:3]
    ]


def classify_trajectories(claims: dict) -> dict:
    """
    Classify claims into growth (increasing confidence) vs contraction classes.
    Algorithmic: based on confidence and history pattern.
    """
    growth = []
    contraction = []
    for c in claims.values():
        if not c.get("sealed"):
            continue
        history = c.get("history", [])
        conf = c.get("confidence", 0.5)
        # Growth: high confidence + evidence gathering (T3) dominant
        if conf >= 0.70 and history.count("T3") > history.count("T5"):
            growth.append(f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}")
        # Contraction: low confidence or contradiction-heavy
        elif conf < 0.50 or history.count("T5") > history.count("T3"):
            contraction.append(f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}")

    return {
        "growth_class": growth[:2] if growth else ["no growth trajectories identified"],
        "contraction_class": contraction[:2] if contraction else ["no contraction trajectories identified"],
    }


def extract_dominant_claim(claims: dict) -> dict:
    """Extract the highest-confidence supported claim."""
    supported = [c for c in claims.values()
                 if c.get("status") in ("supported", "established") and c.get("sealed")]
    if not supported:
        return {"claim": "", "confidence": 0}
    best = max(supported, key=lambda c: c.get("confidence", 0))
    return {
        "claim": f"{best.get('subject','')} {best.get('predicate','')} {best.get('object','')}",
        "confidence": best.get("confidence", 0),
        "category": best.get("modality", "empirical"),
    }


def compute_graph_term_set(claims: dict) -> set:
    """Extract all meaningful terms from claim graph for anchoring check."""
    stop = {"the","a","an","is","are","of","in","to","for","and","or","not",
            "with","by","that","this","it","does","do","can","be","has","have"}
    terms = set()
    for c in claims.values():
        for field in ["subject","predicate","object"]:
            terms.update(c.get(field,"").lower().split())
    return terms - stop


def validate_candidate(candidate: str, claims: dict,
                       question_history: list) -> tuple[bool, str]:
    """Alexandria-lite gate -- unchanged from Paper 5/6/7."""
    graph_terms = compute_graph_term_set(claims)
    stop = {"the","a","an","is","are","of","in","to","for","and","or","not"}
    q_terms = set(candidate.lower().split()) - stop
    if not (graph_terms & q_terms):
        return False, "unanchored: no graph terms in candidate"
    for prior in question_history:
        ta = set(candidate.lower().split())
        tb = set(prior.lower().split())
        if len(ta & tb) / max(len(ta), len(tb), 1) > 0.70:
            return False, "circular: overlap with prior question"
    for c in claims.values():
        if c.get("sealed"):
            ct = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}"
            ta = set(candidate.lower().split())
            tb = set(ct.lower().split())
            if len(ta & tb) / max(len(ta), len(tb), 1) > 0.60:
                return False, f"reopens sealed claim"
    return True, "admitted"


def _spl_available() -> bool:
    """Check if spl_wrapper is importable."""
    try:
        from spl_wrapper import project, centroid, distance
        return True
    except ImportError:
        return False


def compute_eni_components(candidate: str, claims: dict,
                           seed_question: str,
                           question_history: list) -> dict:
    """
    ENI as separate components (not product -- preserves variance).
    Falls back to keyword-overlap novelty if SPL is unavailable.
    """
    sealed = [c for c in claims.values() if c.get("sealed")]
    admitted, reason = validate_candidate(candidate, claims, question_history)

    if not sealed:
        return {"eni_novelty": 0.0, "eni_admissibility": 1.0 if admitted else 0.0,
                "eni_non_drift": 0.0, "eni_composite": 0.0, "admitted": admitted,
                "spl_used": False}

    if _spl_available():
        from spl_wrapper import project, centroid, distance
        projs = [project(f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}")
                 for c in sealed]
        claim_cen = centroid(projs)
        cand_proj = project(candidate)
        seed_proj = project(seed_question)
        novelty = distance(cand_proj, claim_cen)
        non_drift = max(0.0, 1.0 - distance(cand_proj, seed_proj))
        spl_used = True
    else:
        # Fallback: keyword-overlap novelty (no SPL required)
        graph_terms = compute_graph_term_set(claims)
        stop = {"the","a","an","is","are","of","in","to"}
        q_terms = set(candidate.lower().split()) - stop
        graph_terms -= stop
        novelty = 1.0 - (len(q_terms & graph_terms) / max(len(q_terms), 1))
        non_drift = 0.5  # neutral when SPL unavailable
        spl_used = False
    composite = 0.5 * novelty + 0.3 * non_drift + 0.2 * float(admitted)
    return {
        "eni_novelty": round(novelty, 4),
        "eni_admissibility": 1.0 if admitted else 0.0,
        "eni_non_drift": round(non_drift, 4),
        "eni_composite": round(composite, 4),
        "admitted": admitted,
        "rejection_reason": None if admitted else reason,
        "spl_used": spl_used,
    }


# ── Operator Definitions ──────────────────────────────────────────────────────

OPERATOR_LIBRARY = {

    "recursive_modulation": MethodOperator(
        operator_id="recursive_modulation_v1",
        origin_handle="mozart",
        core_move="Identify dominant thematic motif in ClaimGraph, transpose to "
                  "adjacent conceptual register, return transformed under coherence "
                  "constraint.",
        target_failure_modes=["SEMANTIC_DUPLICATION", "novelty_starvation"],
        best_domains=["argumentative", "empirical", "social_science", "policy"],
        risky_domains=["formal_mathematics", "logical_derivation"],
        algorithmic_components=[
            "extract_dominant_motif",
            "extract_core_tension",
            "compute_eni_components",
            "validate_candidate",
        ],
        llm_prompt_template="""Dominant motif in current ClaimGraph: {dominant_motif}
Core tension: {core_tension}

Generate ONE research question that:
1. Transposes the dominant motif to a different conceptual register
2. Preserves the core tension as the organizing theme
3. Returns transformed -- does not simply restate the original question
4. Contains at least one noun phrase from the claim graph

Return ONLY: one research question as a single sentence.""",
        metrics=["eni_novelty", "eni_non_drift", "nov_next", "motif_recurrence"],
        known_successes=[("N03_AGI", 3, 5.0), ("N05_inequality", 3, 4.67)],
        known_failures=[("M01_T(n)", 3, -1.0)],
    ),

    "boundary_condition_analysis": MethodOperator(
        operator_id="boundary_condition_analysis_v1",
        origin_handle="kant",
        core_move="Extract necessary preconditions for the dominant claim. Ask what "
                  "structural conditions are required, not what content follows.",
        target_failure_modes=["METHOD_COLLAPSE", "scope_fixation"],
        best_domains=["formal_mathematics", "structural_analysis", "logic"],
        risky_domains=["creative", "open_narrative"],
        algorithmic_components=[
            "extract_invariants",
            "extract_dominant_claim",
            "validate_candidate",
        ],
        llm_prompt_template="""Dominant claim: {dominant_claim}
Confidence: {confidence}
Epistemic category: {category}

Generate ONE research question that asks:
What are the necessary structural conditions for this claim to hold?
Focus on invariants, boundary cases, and preconditions -- not what follows from the claim.

Return ONLY: one research question as a single sentence.""",
        metrics=["eni_novelty", "false_proof_rate", "on_domain_rate"],
        known_successes=[("M01_T(n)", 3, 2.0)],
        known_failures=[],
    ),

    "adaptive_variation_selection": MethodOperator(
        operator_id="adaptive_variation_selection_v1",
        origin_handle="darwin",
        core_move="Identify competing trajectory classes. Ask which survives under "
                  "selection pressure. Maps growing and contracting trajectories as "
                  "fitness landscapes.",
        target_failure_modes=["SEMANTIC_DUPLICATION", "early_saturation"],
        best_domains=["empirical", "social_science", "economics", "biology"],
        risky_domains=[],
        algorithmic_components=[
            "classify_trajectories",
            "extract_dominant_claim",
            "validate_candidate",
        ],
        llm_prompt_template="""Growth trajectories: {growth_class}
Contraction trajectories: {contraction_class}

Generate ONE research question that asks:
Under what selection conditions does one trajectory type dominate?
What is the fitness landscape determining survival?

Return ONLY: one research question as a single sentence.""",
        metrics=["eni_novelty", "eni_non_drift", "nov_next"],
        known_successes=[("N03_AGI", 1, 6.0), ("M01_T(n)", 2, 2.0)],
        known_failures=[("N03_AGI_seed202", 1, -5.0)],
    ),

    "counterexample_search": MethodOperator(
        operator_id="counterexample_search_v1",
        origin_handle="popper",
        core_move="Generate the strongest plausible counterexample to the dominant "
                  "supported claim. One specific case where the claim fails.",
        target_failure_modes=["confirmation_bias", "premature_sealing"],
        best_domains=["empirical", "formal_mathematics", "causal_analysis"],
        risky_domains=["open_normative"],
        algorithmic_components=[
            "extract_dominant_claim",
            "extract_invariants",
            "validate_candidate",
        ],
        llm_prompt_template="""Dominant supported claim: {dominant_claim}
Confidence: {confidence}
Known invariants: {invariants}

Generate ONE research question that asks:
What is the strongest plausible scenario where this claim fails?
Give a specific boundary condition, not general skepticism.

Return ONLY: one research question as a single sentence.""",
        metrics=["eni_novelty", "nov_next", "false_proof_rate"],
        known_successes=[],
        known_failures=[],
    ),
}


# ── Logging ──────────────────────────────────────────────────────────────────

def log_operator_invocation(result: dict, log_path: str) -> None:
    """Append operator invocation result to JSONL log file."""
    import json
    from pathlib import Path
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


# ── Operator Invocation ───────────────────────────────────────────────────────

def invoke_operator(operator_id: str, state: dict,
                    seed_question: str, question_history: list,
                    call_llm_fn) -> dict:
    """
    Invoke a method operator on the current state.
    Runs algorithmic components first, then LLM for generation.
    Returns: {question, eni, admitted, operator_id, context}
    """
    op = OPERATOR_LIBRARY[operator_id]
    claims = state.get("claims", {})

    # Run algorithmic components
    context = {}
    if "extract_dominant_motif" in op.algorithmic_components:
        motif = extract_dominant_motif(claims)
        context["dominant_motif"] = f"{motif['subject']} {motif['predicate']}"
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
        context["category"] = dom["category"]

    # LLM generation
    prompt = op.llm_prompt_template.format(**context)
    candidate = call_llm_fn(prompt)

    # Score
    eni = compute_eni_components(candidate, claims, seed_question, question_history)
    admitted, reason = validate_candidate(candidate, claims, question_history)

    return {
        "question": candidate,
        "operator_id": operator_id,
        "admitted": admitted,
        "rejection_reason": None if admitted else reason,
        "context": context,
        **eni,
    }


def select_operator(state: dict, loop: int,
                    loop_metrics: list, domain_type: str = "empirical") -> str:
    """
    Select the most appropriate operator given current state.
    Algorithmic selection based on domain type and current failure signals.
    """
    claims = state.get("claims", {})
    current_dup = (loop_metrics[-1].get("semantic_duplication_rate", 0)
                   if loop_metrics else 0)

    # Domain-type routing (Paper 8 extended homology hypothesis)
    if domain_type == "formal_mathematics":
        return "boundary_condition_analysis"

    # State-based routing for empirical domains
    tension = extract_core_tension(claims)
    if "not identified" not in tension and current_dup > 0.30:
        return "recursive_modulation"  # mozart: use when tension exists + dup rising

    traj = classify_trajectories(claims)
    # Robust check: classify_trajectories() returns placeholder strings when empty
    has_growth = not traj["growth_class"][0].startswith("no ")
    has_contraction = not traj["contraction_class"][0].startswith("no ")
    if has_growth and has_contraction:
        return "adaptive_variation_selection"  # darwin: competing trajectories exist

    dom = extract_dominant_claim(claims)
    if dom["confidence"] > 0.80:
        return "counterexample_search"  # popper: challenge strong claims

    return "recursive_modulation"  # default fallback

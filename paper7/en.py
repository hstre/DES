"""
paper7/en.py
Exogenous Noise injection: persona, adjacent-domain, temperature.
ENI reported as 4 separate components — not a pure product.
WP2 (Rentschler 2026).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from paper5.spl_wrapper import project, centroid, distance


# ---------------------------------------------------------------------------
# ENI: 4 separate components + weighted composite
# Pure multiplication collapses to 0 when admissibility=0.
# Composite = weighted mean (novelty 0.5, non_drift 0.3, admissibility 0.2).
# ---------------------------------------------------------------------------

def compute_eni(candidate: str, state: dict, seed_question: str) -> dict:
    """
    Compute ENI for a noise candidate question.
    Returns dict with all 4 components + admitted flag.
    """
    claims = state.get("claims", {})
    sealed = [c for c in claims.values() if c.get("sealed")]

    if not sealed:
        return {
            "eni_novelty": 0.0,
            "eni_admissibility": 0.0,
            "eni_non_drift": 0.0,
            "eni_composite": 0.0,
            "admitted": False,
            "rejection_reason": "no_sealed_claims",
        }

    projs = [
        project(f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}")
        for c in sealed
    ]
    claim_cen = centroid(projs)
    cand_proj = project(candidate)
    seed_proj = project(seed_question)

    novelty = distance(cand_proj, claim_cen)
    admitted, rejection_reason = _validate(candidate, state)
    non_drift = max(0.0, 1.0 - distance(cand_proj, seed_proj))

    composite = 0.5 * novelty + 0.3 * non_drift + 0.2 * float(admitted)

    return {
        "eni_novelty": round(novelty, 4),
        "eni_admissibility": 1.0 if admitted else 0.0,
        "eni_non_drift": round(non_drift, 4),
        "eni_composite": round(composite, 4),
        "admitted": admitted,
        "rejection_reason": rejection_reason,
    }


def _tokens(text: str) -> set:
    STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to",
            "for", "and", "or", "but", "not", "with", "by", "from", "that",
            "this", "it", "be", "as", "at", "on", "if", "its", "so", "do",
            "can", "will", "how", "what", "why", "does", "do", "when", "where"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def _validate(question: str, state: dict) -> tuple[bool, str | None]:
    """Alexandria-lite gate (unchanged from Paper 5/6)."""
    claims = state.get("claims", {})
    graph_terms: set = set()
    for c in claims.values():
        for f in ("subject", "predicate", "object"):
            graph_terms.update(_tokens(c.get(f, "")))

    q_terms = _tokens(question)
    if not (graph_terms & q_terms):
        return False, "no_graph_overlap"

    for c in claims.values():
        if c.get("sealed"):
            ct = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}"
            ta = set(question.lower().split())
            tb = set(ct.lower().split())
            if len(ta & tb) / max(len(ta), len(tb), 1) > 0.60:
                return False, "high_overlap_with_sealed_claim"

    return True, None


# ---------------------------------------------------------------------------
# Noise prompt templates
# ---------------------------------------------------------------------------

PERSONA_PROMPTS = [
    (
        "popper",
        "Karl Popper",
        "Apply Karl Popper's falsificationism: what is the strongest testable prediction "
        "this implies, and how could it be falsified?\nDomain: {question}\nReturn ONE research question only.",
    ),
    (
        "shannon",
        "Claude Shannon",
        "Apply information-theoretic framing: what is the channel capacity or entropy of this system?\n"
        "Domain: {question}\nReturn ONE research question only.",
    ),
    (
        "darwin",
        "Charles Darwin",
        "Apply evolutionary dynamics: what selection pressures, variation sources, and fitness "
        "landscapes are implied?\nDomain: {question}\nReturn ONE research question only.",
    ),
    (
        "mozart",
        "W.A. Mozart",
        "Apply Mozart's compositional logic — thematic variation, modulation, and transformed return:\n"
        "1. Identify the dominant motif (the central taken-for-granted assumption).\n"
        "2. Invert, augment, or modulate it: transpose the same structure into a completely different "
        "conceptual register or domain.\n"
        "3. Return to the original domain with this transformed theme as a new question.\n"
        "Domain: {question}\nReturn ONE research question that represents a structural recombination "
        "of the domain's central motif in a new key.",
    ),
    (
        "picasso",
        "Pablo Picasso",
        "Apply Picasso's cubist method — fracture perspective, superimpose incompatible views:\n"
        "Simultaneously decompose this domain from four viewpoints at once:\n"
        "- Micro (mechanism, substrate, implementation detail)\n"
        "- Macro (systemic, emergent, civilizational arc)\n"
        "- Temporal (100-year historical trajectory and long-run attractor)\n"
        "- Adversarial (who benefits structurally if the conventional answer is wrong?)\n"
        "Hold all four at once. What research question only becomes visible when these "
        "incompatible perspectives are fractured and superimposed?\n"
        "Domain: {question}\nReturn ONE research question that cannot be asked from any single viewpoint.",
    ),
]

ADJACENT_PROMPTS = [
    (
        "ecology",
        "Reframe as an ecosystem: if the entities in this domain were species competing for resources, "
        "what dynamics emerge?\nDomain: {question}\nReturn ONE research question only.",
    ),
    (
        "network",
        "Reframe as a network protocol: what are the nodes, edges, failure modes, and redundancy "
        "mechanisms?\nDomain: {question}\nReturn ONE research question only.",
    ),
    (
        "evolution",
        "Reframe as an evolutionary process: what are the replicators, selection mechanisms, and "
        "drift factors?\nDomain: {question}\nReturn ONE research question only.",
    ),
]

TEMP_PROMPT = (
    "Generate a novel, unexpected research question that explores an underexamined angle of: {question}\n"
    "The question should be related but distinct from the obvious framing.\nReturn ONE research question only."
)


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def generate_en_candidates(
    question: str,
    state: dict,
    en_type: str,
    call_llm_fn,
    k: int = 3,
    persona_filter: str | None = None,
) -> list[dict]:
    """
    Generate k EN candidates of the specified type.
    call_llm_fn(prompt, temperature=0.7) -> str
    Returns list of dicts with question, en_type, ENI scores, and all metadata.
    All candidates logged (admitted AND rejected).
    persona_filter: if set, restricts persona en_type to a single persona key
                    ("popper", "shannon", "darwin"). Ignored for other en_types.
    """
    seed_q = state.get("seed_question", question)
    results = []

    if en_type == "persona":
        prompts = PERSONA_PROMPTS[:k]
        if persona_filter:
            prompts = [(n, l, t) for n, l, t in PERSONA_PROMPTS if n == persona_filter]
        for name, label, tmpl in prompts:
            prompt = tmpl.format(question=question)
            q = call_llm_fn(prompt)
            eni = compute_eni(q, state, seed_q)
            results.append({
                "question": q,
                "en_type": "persona",
                "persona": label,
                "persona_key": name,
                **eni,
            })

    elif en_type == "adjacent":
        for domain, tmpl in ADJACENT_PROMPTS[:k]:
            prompt = tmpl.format(question=question)
            q = call_llm_fn(prompt)
            eni = compute_eni(q, state, seed_q)
            results.append({
                "question": q,
                "en_type": "adjacent",
                "adjacent_domain": domain,
                **eni,
            })

    elif en_type == "temp":
        prompt_base = TEMP_PROMPT.format(question=question)
        for _ in range(k):
            q = call_llm_fn(prompt_base, temperature=1.9)
            eni = compute_eni(q, state, seed_q)
            results.append({
                "question": q,
                "en_type": "temperature",
                **eni,
            })

    return results


def select_best_en(candidates: list[dict]) -> dict | None:
    """Select admitted candidate with highest eni_composite. Returns None if none admitted."""
    admitted = [c for c in candidates if c.get("admitted")]
    if not admitted:
        return None
    return max(admitted, key=lambda c: c.get("eni_composite", 0.0))


# ---------------------------------------------------------------------------
# Early saturation detection (H4: preventive trigger)
# ---------------------------------------------------------------------------

def early_saturation_detected(loop_metrics: list, current: dict) -> bool:
    """
    Forward-looking signal — fires before SEMANTIC_DUPLICATION.
    Triggers EN preventively, not as a rescue from an already-failed state.
    """
    dup = current.get("semantic_duplication_rate", 0)
    novel = current.get("novel_claims", 0)

    # Very early warning (loops 0–1)
    if len(loop_metrics) < 2 and dup > 0.30:
        return True
    if not loop_metrics:
        return False

    prev = loop_metrics[-1]
    prev_novel = prev.get("novel_claims", 1)
    prev_dup = prev.get("semantic_duplication_rate", 0)

    # Novelty halved vs previous loop
    if prev_novel > 0 and novel < prev_novel * 0.50:
        return True
    # Two consecutive zero-novelty loops
    if prev_novel == 0 and novel == 0 and len(loop_metrics) >= 2:
        return True
    # Duplication spike: Δdup > 0.15
    if dup - prev_dup > 0.15:
        return True

    return False


# ---------------------------------------------------------------------------
# SH scheduler (EXPLORATORY arm only)
# ---------------------------------------------------------------------------

SH_STAR = 0.0876  # locked from Paper 6 Phase 1


def sh_schedule(sh: float) -> dict:
    """
    EXPLORATORY ONLY — not default architecture.
    Paper 6 did not confirm SH as monotone intervention selector.
    Run as one arm alongside non-SH-conditioned arms.
    """
    if sh < SH_STAR:
        return {"en": None, "ehl": 0.90}       # low headroom → EHL only
    else:
        return {"en": "persona", "ehl": 1.00}  # high headroom → EN only

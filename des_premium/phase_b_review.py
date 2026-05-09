"""
des_premium/phase_b_review.py
Phase B review pass — single-shot convergent synthesis by an external reviewer.
Called once per run after Phase A terminates, regardless of termination cause.
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI

from des_premium.config import PHASE_B_VARIANTS, REVIEW_CONFIG, JUDGE_CONFIG

_clients: dict = {}


def _init_review_clients() -> None:
    global _clients
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not ok:
        raise EnvironmentError("OPENROUTER_API_KEY must be set for Phase B.")
    _clients["openrouter"] = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/hstre/DES",
            "X-Title": "DES-phase-b-review",
        },
    )


def _client() -> OpenAI:
    if "openrouter" not in _clients:
        _init_review_clients()
    return _clients["openrouter"]


# ── Claim graph serialisation ─────────────────────────────────────────────────

def serialize_claim_graph(loop_states: list[dict], final_state: dict | None) -> dict:
    """
    Produce a compact but complete JSON representation of the Phase A claim graph
    for use as Phase B context. Works from the last available loop state.
    """
    state = final_state or (loop_states[-1] if loop_states else {})
    if not state:
        return {"claims": [], "open_branches": [], "contradictions": [], "stats": {}}

    claims_raw = state.get("claims", {})
    op_history = state.get("operation_history", [])

    claims_out = []
    open_branches = []
    contradictions = []

    for cid, c in claims_raw.items():
        claim_text = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}"
        entry = {
            "id":          cid,
            "text":        claim_text.strip(),
            "status":      c.get("status", "unknown"),
            "confidence":  c.get("confidence", 0.5),
            "modality":    c.get("modality", ""),
            "parent_id":   c.get("parent_id"),
            "sealed":      c.get("sealed", False),
            "branch_open": c.get("branch_open", False),
            "conflict":    c.get("conflict", False),
            "is_synthesis":c.get("is_synthesis", False),
            "t_history":   _summarise_history(c.get("history", [])),
        }
        claims_out.append(entry)
        if c.get("branch_open"):
            open_branches.append(cid)
        if c.get("conflict"):
            contradictions.append(cid)

    # Aggregate T-transition counts from operation history
    # Items may be strings like "T3 on C001" or dicts
    t_counts: dict[str, int] = {}
    for op in op_history:
        if isinstance(op, str):
            op_type = op.split()[0] if op else "unknown"
        elif isinstance(op, dict):
            op_type = op.get("type") or op.get("operator_id") or "unknown"
        else:
            op_type = str(op)
        t_counts[op_type] = t_counts.get(op_type, 0) + 1

    stats = {
        "total_claims":      len(claims_out),
        "open_branches":     len(open_branches),
        "contradiction_count": len(contradictions),
        "loops_in_state":    state.get("iteration", 0),
        "reframing_count":   state.get("reframing_count", 0),
        "t_transition_counts": t_counts,
    }

    # SPL metadata if present
    spl_meta = _extract_spl_meta(state)

    return {
        "claims":        claims_out,
        "open_branches": open_branches,
        "contradictions": contradictions,
        "stats":         stats,
        "spl_metadata":  spl_meta,
    }


def _summarise_history(history: list) -> list[str]:
    """Compact history into operator names only. Items may be strings or dicts."""
    result = []
    for h in history[-5:]:
        if isinstance(h, str):
            result.append(h)
        elif isinstance(h, dict):
            result.append(h.get("operator") or h.get("type") or str(h))
        else:
            result.append(str(h))
    return result


def _extract_spl_meta(state: dict) -> dict | None:
    """Extract SPL geometry metadata from state if available."""
    for key in ("spl_clusters", "spl_geometry", "jsd_distances"):
        if key in state:
            return {key: state[key]}
    return None


def graph_hash(graph: dict) -> str:
    """SHA256 of the serialised graph — used for Phase A→B handoff integrity."""
    return hashlib.sha256(
        json.dumps(graph, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


# ── Prompt construction ───────────────────────────────────────────────────────

_VARIANT_INSTRUCTIONS = {
    "standard_review": (
        "Phase A completed its full loop sequence and terminated naturally.\n"
        "Perform standard synthesis review:\n"
        "1. Identify the strongest integrating claim across branches.\n"
        "2. Assess cluster coherence and recalibrate confidence where warranted.\n"
        "3. Provide an overall meta-assessment of the epistemic state."
    ),
    "premature_review": (
        "Phase A terminated EARLY due to semantic duplication — branches converged\n"
        "before natural saturation. Give extra emphasis to gap identification:\n"
        "1. Identify semantic regions not explored due to premature termination.\n"
        "2. Specify what evidence or argument would distinguish between converged branches.\n"
        "3. Note whether the duplication reflects genuine convergence or premature collapse."
    ),
    "unsaturated_review": (
        "Phase A reached MAX_LOOPS without natural saturation — the exploration\n"
        "is ongoing and no clean termination signal was reached.\n"
        "1. Synthesise what CAN be said from the available claim graph.\n"
        "2. Mark the output as preliminary in meta_assessment.\n"
        "3. Identify the highest-priority semantic regions for continued exploration."
    ),
    "contradiction_review": (
        "Phase A terminated with an UNRESOLVED CONTRADICTION in the claim graph.\n"
        "Force a synthesis attempt across the contradiction:\n"
        "1. Propose a bridging claim that contextualises (not necessarily resolves) the contradiction.\n"
        "2. Assess whether the contradiction is empirical (resolvable by evidence) or definitional.\n"
        "3. Identify what would be needed to resolve it."
    ),
}

_PHASE_B_SYSTEM = (
    "You are an external epistemic reviewer. You did not produce the following "
    "claim graph; your task is to assess it as a coherent epistemic state and "
    "identify what synthesis, recalibration, or further work is needed. "
    "Do not extend the inner loop's reasoning; evaluate it."
)

_OUTPUT_SCHEMA_INSTRUCTIONS = """
Respond with a single valid JSON object matching this schema exactly:
{
  "synthesis_claim": "<string — bridging claim that resolves or contextualises branches>",
  "cluster_assessment": [
    {"cluster_id": "<string>", "coherence": "<coherent|fragmented|contested>", "rationale": "<string>"}
  ],
  "confidence_recalibration": {
    "<claim_id>": {"original": <float>, "revised": <float>, "rationale": "<string>"}
  },
  "gap_identification": [
    {"region": "<description of semantic gap>", "would_resolve": "<what evidence would close it>"}
  ],
  "meta_assessment": "<settled|contested|incoherent|preliminary>",
  "review_rationale": "<free-text explanation of overall assessment>"
}

Recalibrate only claims where confidence adjustment is clearly warranted.
Do not add claims outside the provided graph. Assess the graph as-is.
"""


def build_phase_b_prompt(
    seed_question:     str,
    graph:             dict,
    termination_reason: str,
    variant:           str,
    seed_n:            int,
) -> str:
    variant_instr = _VARIANT_INSTRUCTIONS.get(variant, _VARIANT_INSTRUCTIONS["standard_review"])
    graph_json = json.dumps(graph, indent=2, ensure_ascii=False)

    return (
        f"## Seed question\n\n{seed_question}\n\n"
        f"## Phase A termination\n\n"
        f"Reason: {termination_reason}\n"
        f"Variant: {variant}\n\n"
        f"## Review instructions\n\n{variant_instr}\n\n"
        f"## Claim graph (Phase A output)\n\n```json\n{graph_json}\n```\n\n"
        f"## Output format\n{_OUTPUT_SCHEMA_INSTRUCTIONS}\n\n"
        f"# run_seed: {seed_n}"
    )


# ── Reviewer API call ─────────────────────────────────────────────────────────

def call_reviewer(
    prompt: str,
    config: dict,
) -> tuple[str, dict]:
    """Single-shot call to reviewer model. Returns (content, usage)."""
    resp = _client().chat.completions.create(
        model=config["reviewer_model"],
        messages=[
            {"role": "system", "content": _PHASE_B_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=config.get("reviewer_temperature", 0.2),
        max_tokens=config.get("reviewer_max_tokens", 4000),
    )
    content = resp.choices[0].message.content or ""
    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens":     resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens":      resp.usage.total_tokens,
        }
    return content, usage


def parse_phase_b_output(content: str) -> dict:
    """
    Extract structured JSON from Phase B response.
    Handles markdown code-fenced JSON blocks and bare JSON.
    Returns schema-conforming dict; logs parse errors without raising.
    """
    # Strip markdown fences
    stripped = re.sub(r"```json\s*", "", content)
    stripped = re.sub(r"```\s*", "", stripped)
    stripped = stripped.strip()

    # Try direct parse
    for candidate in [stripped, content]:
        try:
            parsed = json.loads(candidate)
            return _normalise_phase_b(parsed)
        except json.JSONDecodeError:
            pass

    # Extract first {...} block
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
            return _normalise_phase_b(parsed)
        except json.JSONDecodeError:
            pass

    # Fallback: return raw in an error wrapper
    return {
        "parse_error": True,
        "raw_content":  content,
        "synthesis_claim": "",
        "cluster_assessment": [],
        "confidence_recalibration": {},
        "gap_identification": [],
        "meta_assessment": "incoherent",
        "review_rationale": f"[PARSE ERROR] Raw: {content[:500]}",
    }


def _normalise_phase_b(d: dict) -> dict:
    """Ensure all required keys are present."""
    return {
        "synthesis_claim":          d.get("synthesis_claim", ""),
        "cluster_assessment":       d.get("cluster_assessment", []),
        "confidence_recalibration": d.get("confidence_recalibration", {}),
        "gap_identification":       d.get("gap_identification", []),
        "meta_assessment":          d.get("meta_assessment", "contested"),
        "review_rationale":         d.get("review_rationale", ""),
        "parse_error":              d.get("parse_error", False),
    }


# ── Phase B orchestration ─────────────────────────────────────────────────────

def run_phase_b(
    seed_question:       str,
    termination_reason:  str,
    loop_states:         list[dict],
    final_state:         dict | None,
    seed_n:              int,
    config:              dict | None = None,
) -> dict:
    """
    Full Phase B run. Returns a dict with structured output + provenance.
    """
    cfg = config or REVIEW_CONFIG

    variant  = PHASE_B_VARIANTS.get(termination_reason, "standard_review")
    graph    = serialize_claim_graph(loop_states, final_state)
    g_hash   = graph_hash(graph)
    prompt   = build_phase_b_prompt(seed_question, graph, termination_reason, variant, seed_n)
    p_hash   = hashlib.sha256(prompt.encode()).hexdigest()

    t_start  = time.time()
    content, usage = call_reviewer(prompt, cfg)
    elapsed  = round(time.time() - t_start, 1)

    structured = parse_phase_b_output(content)

    return {
        "phase_b_variant":        variant,
        "phase_a_termination":    termination_reason,
        "phase_a_graph_hash":     g_hash,
        "reviewer_model":         cfg["reviewer_model"],
        "prompt_hash":            p_hash,
        "elapsed_seconds":        elapsed,
        "token_usage":            usage,
        "structured_output":      structured,
        "raw_content":            content,
    }


# ── Judge evaluation ──────────────────────────────────────────────────────────

_JUDGE_SYSTEM = (
    "You are an impartial epistemic quality assessor. "
    "Score the provided output on the rubric below. "
    "Do not infer which system produced the output — assess only the artifact."
)

_JUDGE_RUBRIC = """
Rubric (score each applicable metric):

1. synthesis_quality (1-5):
   5 = Output integrates competing considerations into a coherent bridging claim.
   3 = Output lists considerations but does not integrate them.
   1 = Output is a single unqualified assertion or incoherent.

2. branch_preservation (1-5):
   5 = Output retains and names distinct positions that remain in tension.
   3 = Output acknowledges some positions but collapses most.
   1 = Output presents a single answer with no acknowledged alternatives.

3. gap_acknowledgment (1-5):
   5 = Output explicitly identifies what is unresolved and what evidence would help.
   3 = Output acknowledges uncertainty but does not specify gaps.
   1 = Output claims completeness or ignores open questions.

4. calibration (1-5):
   5 = Confidence claims are proportionate to evidence strength shown.
   3 = Some claims are over- or under-confident but mostly reasonable.
   1 = Confidence claims are grossly misaligned with evidence.

5. false_proof_avoidance (binary, M01 only):
   1 = Output avoids claiming proof of an open conjecture.
   0 = Output claims proof of a conjecture that remains open.
   null = Not applicable (non-M01 domain).
"""


def build_judge_prompt(output_text: str, seed_question: str, domain_id: str) -> str:
    is_m01 = domain_id == "M01"
    m01_note = (
        "\nThis is a mathematics domain (M01). Apply false_proof_avoidance scoring."
        if is_m01 else
        "\nThis is not M01. Set false_proof_avoidance to null."
    )
    return (
        f"## Seed question\n\n{seed_question}\n\n"
        f"## Output to assess\n\n{output_text}\n\n"
        f"{_JUDGE_RUBRIC}\n{m01_note}\n\n"
        "Respond with a single JSON object:\n"
        "{\n"
        '  "synthesis_quality": <1-5>,\n'
        '  "branch_preservation": <1-5>,\n'
        '  "gap_acknowledgment": <1-5>,\n'
        '  "calibration": <1-5>,\n'
        '  "false_proof_avoidance": <0|1|null>,\n'
        '  "rationale": {"sq": "...", "bp": "...", "ga": "...", "cal": "...", "fpa": "..."}\n'
        "}"
    )


def call_judge(prompt: str, judge_config: dict | None = None) -> tuple[str, dict]:
    cfg = judge_config or JUDGE_CONFIG
    resp = _client().chat.completions.create(
        model=cfg["judge_model"],
        messages=[
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=cfg.get("judge_temperature", 0.1),
        max_tokens=cfg.get("judge_max_tokens", 2000),
    )
    content = resp.choices[0].message.content or ""
    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens":     resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens":      resp.usage.total_tokens,
        }
    return content, usage


def parse_judge_output(content: str) -> dict:
    stripped = re.sub(r"```json\s*", "", content)
    stripped = re.sub(r"```\s*", "", stripped).strip()
    for candidate in [stripped, content]:
        try:
            d = json.loads(candidate)
            return {
                "synthesis_quality":    d.get("synthesis_quality"),
                "branch_preservation":  d.get("branch_preservation"),
                "gap_acknowledgment":   d.get("gap_acknowledgment"),
                "calibration":          d.get("calibration"),
                "false_proof_avoidance":d.get("false_proof_avoidance"),
                "rationale":            d.get("rationale", {}),
                "parse_error":          False,
            }
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            return {
                "synthesis_quality":    d.get("synthesis_quality"),
                "branch_preservation":  d.get("branch_preservation"),
                "gap_acknowledgment":   d.get("gap_acknowledgment"),
                "calibration":          d.get("calibration"),
                "false_proof_avoidance":d.get("false_proof_avoidance"),
                "rationale":            d.get("rationale", {}),
                "parse_error":          False,
            }
        except json.JSONDecodeError:
            pass
    return {
        "synthesis_quality":    None,
        "branch_preservation":  None,
        "gap_acknowledgment":   None,
        "calibration":          None,
        "false_proof_avoidance":None,
        "rationale":            {},
        "parse_error":          True,
        "raw_content":          content[:1000],
    }


def run_judge_eval(
    output_text:  str,
    seed_question: str,
    domain_id:    str,
    judge_config: dict | None = None,
) -> dict:
    """Evaluate one output with the external judge. Returns scores + provenance."""
    cfg    = judge_config or JUDGE_CONFIG
    prompt = build_judge_prompt(output_text, seed_question, domain_id)
    p_hash = hashlib.sha256(prompt.encode()).hexdigest()

    t_start = time.time()
    content, usage = call_judge(prompt, cfg)
    elapsed = round(time.time() - t_start, 1)

    scores = parse_judge_output(content)

    return {
        "judge_model":   cfg["judge_model"],
        "prompt_hash":   p_hash,
        "elapsed_seconds": elapsed,
        "token_usage":   usage,
        "scores":        scores,
        "raw_content":   content,
    }

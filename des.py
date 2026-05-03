"""
Dynamic Epistemic Sequencer (DES) — Standalone Prototype v0.1

Architecture:
    Claim → EpistemicState S(t) → Transition Table (T1–T9) → LLM Operation → S(t+1)

The transition table runs entirely in Python; the LLM executes operations but never
selects the next step. S(t) is persisted to des_state.json after every iteration
(PES: Persistent Epistemic Supervisor), satisfying:
  C1 — evaluative decisions depend on the full S(t), not just the current prompt
  C2 — operation history is not reconstructible from the prompt alone

Transition priority (T1 highest):
    T1 contradicted            → resolve_conflict (branch)
    T2 conflict==True          → make_conflict_explicit
    T3 no evidence             → request_evidence
    T4 scope=={} or underspec  → decompose_claim
    T5 confidence < 0.4        → generate_counter_hypothesis
    T6 hypothesis + conf>0.6   → explore_evidence_path
    T7 no qualifier + has scope → refine_qualifier
    T8 supported + conf>0.8    → seal_claim
    T9 branch_open + all branches supported → trigger_reframing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Layer 1: Claim Structure
# ---------------------------------------------------------------------------

@dataclass
class Claim:
    id: str
    subject: str
    predicate: str
    object: str
    status: str = "unknown"          # unknown | supported | disputed | contradicted | underspecified
    confidence: float = 0.5
    modality: str = "hypothesis"     # hypothesis | suggestion | evidence | established
    evidence_refs: list[str] = field(default_factory=list)
    scope: dict = field(default_factory=dict)
    qualifier: dict = field(default_factory=dict)
    conflict: bool = False
    branch_open: bool = False
    sealed: bool = False
    is_synthesis: bool = False
    is_role_generated: bool = False   # True for claims produced by Anti-Delphi roles
    history: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Claim":
        d.setdefault("is_synthesis", False)
        d.setdefault("is_role_generated", False)
        return cls(**d)


# ---------------------------------------------------------------------------
# Layer 2: Epistemic State S(t)
# ---------------------------------------------------------------------------

@dataclass
class EpistemicState:
    claims: dict[str, Claim] = field(default_factory=dict)
    operation_history: list[str] = field(default_factory=list)
    discarded_hypotheses: list[str] = field(default_factory=list)
    weak_candidates: list[str] = field(default_factory=list)
    reframing_count: int = 0
    iteration: int = 0
    focus_claim_id: Optional[str] = None
    anti_delphi_activations: int = 0
    roles_generated: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "claims": {k: v.to_dict() for k, v in self.claims.items()},
            "operation_history": self.operation_history,
            "discarded_hypotheses": self.discarded_hypotheses,
            "weak_candidates": self.weak_candidates,
            "reframing_count": self.reframing_count,
            "iteration": self.iteration,
            "focus_claim_id": self.focus_claim_id,
            "anti_delphi_activations": self.anti_delphi_activations,
            "roles_generated": self.roles_generated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EpistemicState":
        claims = {k: Claim.from_dict(v) for k, v in d.get("claims", {}).items()}
        return cls(
            claims=claims,
            operation_history=d.get("operation_history", []),
            discarded_hypotheses=d.get("discarded_hypotheses", []),
            weak_candidates=d.get("weak_candidates", []),
            reframing_count=d.get("reframing_count", 0),
            iteration=d.get("iteration", 0),
            focus_claim_id=d.get("focus_claim_id"),
            anti_delphi_activations=d.get("anti_delphi_activations", 0),
            roles_generated=d.get("roles_generated", {}),
        )


# ---------------------------------------------------------------------------
# Layer 4: PES — Persistence
# ---------------------------------------------------------------------------

STATE_FILE = "des_state.json"


def save_state(state: EpistemicState) -> None:
    """Persist S(t) to disk."""
    with open(STATE_FILE, "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_state() -> Optional[EpistemicState]:
    """Load S(t) from disk; returns None if no state file exists."""
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE) as f:
        return EpistemicState.from_dict(json.load(f))


def new_claim_id(state: EpistemicState) -> str:
    """Return the next sequential claim ID (C001, C002, …)."""
    n = len(state.claims) + 1
    return f"C{n:03d}"


def new_branch_id(state: EpistemicState) -> str:
    """Return the next B-prefixed branch ID; T3 uses the prefix to apply stronger evidence."""
    n = sum(1 for cid in state.claims if cid.startswith("B")) + 1
    return f"B{n:03d}"


# ---------------------------------------------------------------------------
# LLM Integration (Layer 0)
# ---------------------------------------------------------------------------

_DEEPSEEK_BASE = "https://api.deepseek.com/chat/completions"
_DEEPSEEK_MODEL = "deepseek-chat"


def get_api_key() -> str:
    """Return the DeepSeek API key from the environment."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise EnvironmentError("DEEPSEEK_API_KEY is not set")
    return key


def _llm_call(prompt: str) -> str:
    """Single LLM call via DeepSeek chat completions, returns raw text."""
    response = httpx.post(
        _DEEPSEEK_BASE,
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": _DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    """Extract the first complete JSON object from LLM response using brace matching."""
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON found in response")
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("No complete JSON object found in response")


def _llm_json(prompt: str, retry_prompt: Optional[str] = None) -> Optional[dict]:
    """LLM call that returns parsed JSON. Retries once on failure."""
    try:
        raw = _llm_call(prompt)
        return _extract_json(raw)
    except Exception:
        if retry_prompt is None:
            retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY a valid JSON object, no other text."
        try:
            raw = _llm_call(retry_prompt)
            return _extract_json(raw)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Anti-Delphi Role Execution
# ---------------------------------------------------------------------------

_ROLE_PROMPTS = {
    "hypothesis_builder": """\
You are an epistemic hypothesis generator.
Given this claim, generate ONE new directional hypothesis that extends or refines it.
Do not hedge — commit to a specific direction.

Claim: {claim_json}

Return ONLY valid JSON:
{{
  "subject": "...",
  "predicate": "...",
  "object": "...",
  "modality": "hypothesis",
  "confidence": 0.5,
  "scope": {{"domain": "..."}},
  "qualifier": {{}}
}}""",

    "falsifier": """\
You are an epistemic falsifier.
Given this claim, generate ONE strong counter-claim that directly challenges its direction.
Do not hedge — find the sharpest possible objection.

Claim: {claim_json}

Return ONLY valid JSON:
{{
  "subject": "...",
  "predicate": "...",
  "object": "...",
  "modality": "hypothesis",
  "status": "disputed",
  "confidence": 0.5,
  "scope": {{"domain": "..."}},
  "qualifier": {{}}
}}""",
}


def execute_role(role: str, claim: Claim, state: EpistemicState) -> Optional[Claim]:
    """
    Execute a single Anti-Delphi role and return a new Claim, or None on failure.

    Roles are fully isolated: neither role sees the other's output or prompt.
    hypothesis_builder — extends or refines the claim directionally (conf 0.40–0.55).
    falsifier          — finds the sharpest counter-case         (conf 0.41–0.55).

    Confidences are clamped below the T6 threshold (>0.6) and above the T5
    threshold (<0.4) so role-generated claims do not cascade into Anti-Delphi
    sub-loops. The DES processes them via T3→T7→T8.
    """
    prompt = _ROLE_PROMPTS[role].format(claim_json=_claim_summary(claim))
    result = _llm_json(prompt)
    if result is None:
        return None

    cid = new_claim_id(state)
    raw_conf = float(result.get("confidence", 0.5))
    # Clamp: stay above T5 threshold and below T6 threshold to prevent re-cascades
    confidence = max(0.41, min(0.55, raw_conf))

    return Claim(
        id=cid,
        subject=result.get("subject", claim.subject),
        predicate=result.get("predicate", claim.predicate),
        object=result.get("object", claim.object),
        modality=result.get("modality", "hypothesis"),
        confidence=confidence,
        scope=result.get("scope", claim.scope.copy()),
        qualifier=result.get("qualifier", {}),
        status=result.get("status", "unknown"),
        parent_id=claim.id,
        is_role_generated=True,
    )


def _apply_antidelphi_state_change(
    trigger: str,
    claim: Claim,
    state: EpistemicState,
    role_claim_ids: list[str],
) -> None:
    """
    Apply focus-claim state transitions after Anti-Delphi role execution,
    mirroring what the normal single-agent operation would have done.
    """
    if trigger == "T5":
        if role_claim_ids:
            falsifier_claim = state.claims[role_claim_ids[-1]]
            contradicts = check_for_contradiction(claim, falsifier_claim)
            claim.status = "contradicted" if contradicts else "disputed"
        else:
            claim.status = "disputed"
        claim.conflict = True
        claim.confidence = max(claim.confidence, 0.42)
    elif trigger == "T6":
        claim.status = "supported"
        claim.confidence = max(0.82, min(1.0, claim.confidence + 0.15))
    elif trigger == "T9":
        claim.sealed = True
        state.reframing_count += 1
        # Mark both perspectives as synthesis so they bypass T3–T7 and go to T8
        for cid in role_claim_ids:
            if cid in state.claims:
                state.claims[cid].is_synthesis = True


# ---------------------------------------------------------------------------
# Contradiction Detection
# ---------------------------------------------------------------------------

CONTRADICTION_CHECK_PROMPT = """\
Claim A: {claim_a_subject} {claim_a_predicate} {claim_a_object}
Claim B: {claim_b_subject} {claim_b_predicate} {claim_b_object}

Do these two claims contradict each other in their direction of effect?
Two claims are contradictory if they assert OPPOSITE outcomes for the same subject and domain —
for example: "X increases Y" vs "X decreases Y", or "X is viable" vs "X is not viable".
Hedging words like "may", "could", or "might" do NOT prevent contradiction if the effects
point in opposite directions.

Answer ONLY with JSON: {{"contradicts": true}} or {{"contradicts": false}}"""

_OPPOSING_PAIRS = [
    ("increase", "decrease"), ("increase", "reduce"), ("increase", "suppress"),
    ("improve", "worsen"), ("improve", "deteriorate"), ("improve", "undermine"),
    ("expand", "contract"), ("expand", "shrink"), ("expand", "reduce"),
    ("raise", "lower"), ("raise", "reduce"), ("raise", "decrease"),
    ("support", "undermine"), ("support", "oppose"), ("support", "hinder"),
    ("sustainable", "unsustainable"), ("viable", "unviable"),
    ("positive", "negative"), ("beneficial", "harmful"),
    ("reduce", "increase"), ("reduce", "expand"), ("reduce", "raise"),
    ("suppress", "stimulate"), ("suppress", "boost"),
]


def check_for_contradiction(claim_a: Claim, claim_b: Claim) -> bool:
    """
    Returns True if claim_b directly opposes claim_a in direction of effect.
    Uses LLM for semantic check; falls back to negation markers and opposing-pair heuristics.
    """
    prompt = CONTRADICTION_CHECK_PROMPT.format(
        claim_a_subject=claim_a.subject,
        claim_a_predicate=claim_a.predicate,
        claim_a_object=claim_a.object,
        claim_b_subject=claim_b.subject,
        claim_b_predicate=claim_b.predicate,
        claim_b_object=claim_b.object,
    )
    result = _llm_json(prompt)
    if result is not None:
        return bool(result.get("contradicts", False))

    # Fallback 1: negation markers in counter-predicate
    neg_markers = ("not", "never", "no ", "cannot", "can't", "doesn't", "does not")
    b_pred_lower = claim_b.predicate.lower()
    if any(m in b_pred_lower for m in neg_markers):
        return True

    # Fallback 2: opposing directional terms across predicate+object
    full_a = f"{claim_a.predicate} {claim_a.object}".lower()
    full_b = f"{claim_b.predicate} {claim_b.object}".lower()
    for word_a, word_b in _OPPOSING_PAIRS:
        if word_a in full_a and word_b in full_b:
            return True
        if word_b in full_a and word_a in full_b:
            return True
    return False


# ---------------------------------------------------------------------------
# Branch Evidence Simulation + Claim Update
# ---------------------------------------------------------------------------

CLAIM_UPDATE_PROMPT = """\
Given this claim and new evidence:
Claim: {claim}
Evidence: {evidence}

Update the claim's epistemic status.
Return ONLY JSON:
{{
  "status": "supported",
  "confidence": 0.85,
  "rationale": "..."
}}

If the evidence strongly supports the claim, set status="supported" and confidence > 0.8."""


def simulate_evidence(claim: Claim) -> str:
    """Return simulated evidence; branch claims (B-prefix) get domain-specific confirmation."""
    if claim.id.startswith("B"):
        domain = claim.scope.get("domain", "general")
        return (
            f"[Simulated: peer-reviewed source confirms "
            f"{claim.subject} {claim.predicate} {claim.object} "
            f"in domain '{domain}']"
        )
    return f"[Simulated evidence for: {claim.subject} {claim.object}]"


def evaluate_branch_claim(claim: Claim) -> None:
    """
    Call LLM to update a branch claim's status and confidence from its evidence.
    Falls back to supported+0.85 so T9 can always fire.
    """
    evidence_text = "; ".join(claim.evidence_refs[-2:])
    prompt = CLAIM_UPDATE_PROMPT.format(
        claim=_claim_summary(claim),
        evidence=evidence_text,
    )
    result = _llm_json(prompt)
    if result:
        claim.status = result.get("status", "supported")
        claim.confidence = float(result.get("confidence", 0.85))
    else:
        claim.status = "supported"
        claim.confidence = 0.85


# ---------------------------------------------------------------------------
# Initial Claim Generation
# ---------------------------------------------------------------------------

INITIAL_CLAIM_PROMPT = """\
You are an epistemic claim generator for a research sequencer.

Given this research question: {question}

Generate an initial claim that reflects GENUINE scientific, empirical, or
theoretical uncertainty. Requirements:
- confidence MUST be between 0.3 and 0.65
- status MUST be "hypothesis" or "disputed" — never "supported" or "established"
- The claim must identify a real tension, contested evidence, or open question
- Do NOT generate trivially true or consensus claims

Return ONLY valid JSON:
{{
  "subject": "...",
  "predicate": "...",
  "object": "...",
  "status": "hypothesis",
  "confidence": 0.5,
  "modality": "hypothesis",
  "evidence_refs": [],
  "scope": {{"domain": "..."}},
  "qualifier": {{}}
}}"""


def generate_initial_claim(research_question: str, state: EpistemicState) -> Claim:
    """Convert the research question into a structured Claim with genuine uncertainty."""
    prompt = INITIAL_CLAIM_PROMPT.format(question=research_question)

    result = _llm_json(prompt)
    if result is None:
        words = research_question.split()
        subj = " ".join(words[:3]) if len(words) >= 3 else research_question
        result = {
            "subject": subj,
            "predicate": "has uncertain implications for",
            "object": research_question,
            "status": "hypothesis",
            "modality": "hypothesis",
            "confidence": 0.45,
        }

    confidence = float(result.get("confidence", 0.45))
    confidence = max(0.3, min(0.65, confidence))

    status = result.get("status", "hypothesis")
    if status not in ("hypothesis", "disputed"):
        status = "hypothesis"

    cid = new_claim_id(state)
    # scope intentionally empty so T4 (decompose) fires after initial T3 (evidence)
    return Claim(
        id=cid,
        subject=result.get("subject", research_question),
        predicate=result.get("predicate", "relates to"),
        object=result.get("object", "unknown"),
        modality=result.get("modality", "hypothesis"),
        confidence=confidence,
        scope={},
        qualifier=result.get("qualifier", {}),
        status=status,
    )


# ---------------------------------------------------------------------------
# Layer 3: Transition Table Operations
# ---------------------------------------------------------------------------

def _claim_summary(claim: Claim) -> str:
    """Return a compact JSON representation of the claim for use in LLM prompts."""
    return json.dumps({
        "id": claim.id,
        "subject": claim.subject,
        "predicate": claim.predicate,
        "object": claim.object,
        "status": claim.status,
        "confidence": claim.confidence,
        "modality": claim.modality,
        "scope": claim.scope,
        "qualifier": claim.qualifier,
        "evidence_refs": claim.evidence_refs,
    }, indent=2)


def t1_resolve_conflict(claim: Claim, state: EpistemicState) -> str:
    """Create two B-prefixed branch claims to adjudicate a direct contradiction."""
    branch_scope = claim.scope.copy() if claim.scope else {"domain": claim.subject[:30]}
    if not branch_scope:
        branch_scope = {"domain": "adjudication"}

    prompt = f"""You are an epistemic conflict resolver.
This claim is contradicted and needs adjudication:
{_claim_summary(claim)}

Create exactly two opposing branch claims (pro and con) that capture both sides.
Return ONLY valid JSON:
{{
  "sub_claims": [
    {{"subject": "...", "predicate": "...", "object": "...", "modality": "hypothesis", "confidence": 0.5}},
    {{"subject": "...", "predicate": "...", "object": "...", "modality": "hypothesis", "confidence": 0.5}}
  ]
}}"""

    result = _llm_json(prompt)
    raw = result.get("sub_claims", []) if result else []

    if len(raw) < 2:
        raw = [
            {
                "subject": claim.subject,
                "predicate": claim.predicate,
                "object": f"{claim.object} (pro-position)",
                "modality": "hypothesis",
                "confidence": 0.5,
            },
            {
                "subject": claim.subject,
                "predicate": "does not " + claim.predicate,
                "object": f"{claim.object} (con-position)",
                "modality": "hypothesis",
                "confidence": 0.5,
            },
        ]

    new_ids = []
    for sc in raw[:2]:
        bid = new_branch_id(state)
        branch = Claim(
            id=bid,
            subject=sc.get("subject", claim.subject),
            predicate=sc.get("predicate", claim.predicate),
            object=sc.get("object", claim.object),
            modality=sc.get("modality", "hypothesis"),
            confidence=float(sc.get("confidence", 0.5)),
            scope=branch_scope.copy(),
            qualifier={},
            status="hypothesis",
            parent_id=claim.id,
        )
        state.claims[bid] = branch
        new_ids.append(bid)

    claim.branch_open = True
    # Change status away from "contradicted" to prevent T1 from looping
    claim.status = "disputed"
    claim.conflict = False
    claim.history.append("T1")
    state.operation_history.append(f"T1 on {claim.id}")
    llm_note = "" if result and result.get("sub_claims") else " (fallback)"
    return f"BRANCH created{llm_note}: {claim.id} -> {', '.join(new_ids)}"


def t2_make_conflict_explicit(claim: Claim, state: EpistemicState) -> str:
    """Annotate the claim with a conflict reason and mark it disputed."""
    prompt = f"""You are an epistemic conflict analyst.
This claim has a detected conflict:
{_claim_summary(claim)}

Identify the specific conflict and provide a brief reason.
Return ONLY valid JSON:
{{"conflict_reason": "...", "suggested_status": "disputed"}}"""

    result = _llm_json(prompt)
    fallback_reason = (
        f"Counter-hypothesis exists for '{claim.subject} {claim.predicate} {claim.object}'; "
        "epistemic tension flagged for review"
    )
    reason = result.get("conflict_reason", fallback_reason) if result else fallback_reason
    claim.evidence_refs.append(f"[CONFLICT] {reason}")
    claim.status = result.get("suggested_status", "disputed") if result else "disputed"
    claim.conflict = False
    claim.history.append("T2")
    state.operation_history.append(f"T2 on {claim.id}")
    return f"Conflict made explicit: {reason}"


def t3_request_evidence(claim: Claim, state: EpistemicState) -> str:
    """Simulate evidence retrieval; branch claims get a full LLM-based status update."""
    simulated = simulate_evidence(claim)
    claim.evidence_refs.append(simulated)

    if claim.id.startswith("B"):
        evaluate_branch_claim(claim)
        update_note = f" → status={claim.status}, confidence={claim.confidence:.2f}"
    else:
        if claim.status in ("unknown", "hypothesis"):
            claim.status = "disputed"
        update_note = ""

    claim.history.append("T3")
    state.operation_history.append(f"T3 on {claim.id}")
    return f"Evidence added{update_note}: {simulated[:80]}"


T4_PROMPT = """\
You are an epistemic decomposition engine.

Given this claim: {claim}

Decompose it into 2-3 more specific sub-claims. Requirements:
- At least one sub-claim should have confidence < 0.45
- At least one sub-claim should represent a COMPETING or QUALIFYING perspective
  that creates tension with the others (not outright contradiction, but genuine
  epistemic friction)
- Sub-claims should differ in scope, qualifier, or modality

Return ONLY valid JSON:
{{
  "sub_claims": [
    {{
      "subject": "...",
      "predicate": "...",
      "object": "...",
      "modality": "hypothesis",
      "confidence": 0.55,
      "scope": {{"domain": "..."}},
      "qualifier": {{}}
    }},
    {{
      "subject": "...",
      "predicate": "...",
      "object": "...",
      "modality": "suggestion",
      "confidence": 0.38,
      "scope": {{"domain": "..."}},
      "qualifier": {{}}
    }}
  ]
}}"""


def t4_decompose_claim(claim: Claim, state: EpistemicState) -> str:
    """Decompose a broad or underspecified claim into 2–3 sub-claims with epistemic tension."""
    prompt = T4_PROMPT.format(claim=_claim_summary(claim))

    result = _llm_json(prompt)
    raw_sub_claims = result.get("sub_claims", []) if result else []

    if not raw_sub_claims:
        raw_sub_claims = [
            {
                "subject": claim.subject,
                "predicate": claim.predicate,
                "object": f"{claim.object} under favorable conditions",
                "modality": "hypothesis",
                "confidence": 0.58,
                "scope": {"domain": "supportive context"},
                "qualifier": {},
            },
            {
                "subject": claim.subject,
                "predicate": "does not necessarily " + claim.predicate,
                "object": f"{claim.object} under adverse conditions",
                "modality": "suggestion",
                "confidence": 0.34,
                "scope": {"domain": "contested context"},
                "qualifier": {},
            },
        ]

    new_ids = []
    for sc in raw_sub_claims[:3]:
        cid = new_claim_id(state)
        new_claim = Claim(
            id=cid,
            subject=sc.get("subject", claim.subject),
            predicate=sc.get("predicate", claim.predicate),
            object=sc.get("object", claim.object),
            modality=sc.get("modality", "hypothesis"),
            confidence=float(sc.get("confidence", 0.5)),
            scope=sc.get("scope", {"domain": "general"}),
            qualifier=sc.get("qualifier", {}),
            status="unknown",
            parent_id=claim.id,
        )
        state.claims[cid] = new_claim
        new_ids.append(cid)

    llm_note = "" if result and result.get("sub_claims") else " (fallback)"
    claim.status = "supported"
    claim.sealed = True
    claim.history.append("T4")
    state.operation_history.append(f"T4 on {claim.id}")
    return f"Decomposed into sub-claims{llm_note}: {', '.join(new_ids)}"


def t5_generate_counter_hypothesis(claim: Claim, state: EpistemicState) -> str:
    """Generate an adversarial counter-hypothesis; escalate to T1 path if contradiction detected."""
    prompt = f"""You are an adversarial epistemic engine.
Given this low-confidence claim:
{_claim_summary(claim)}

Generate a counter-hypothesis that asserts the OPPOSITE directional effect.
If the claim says X increases Y, the counter must say X decreases (or does not increase) Y.
If the claim says X reduces Y, the counter must say X increases (or does not reduce) Y.
The counter-hypothesis must directly contradict the direction of effect, not merely qualify it.
Return ONLY valid JSON:
{{
  "counter_subject": "...",
  "counter_predicate": "...",
  "counter_object": "...",
  "counter_confidence": 0.6,
  "reasoning": "..."
}}"""

    result = _llm_json(prompt)

    if result:
        counter_subject = result.get("counter_subject", claim.subject)
        counter_predicate = result.get("counter_predicate", "does not " + claim.predicate)
        counter_object = result.get("counter_object", claim.object)
        counter_confidence = float(result.get("counter_confidence", 0.6))
        reasoning = result.get("reasoning", "")
        llm_note = ""
    else:
        counter_subject = claim.subject
        counter_predicate = "does not " + claim.predicate
        counter_object = claim.object
        counter_confidence = 0.6
        reasoning = "structural negation (LLM unavailable)"
        llm_note = " (fallback)"

    cid = new_claim_id(state)
    counter = Claim(
        id=cid,
        subject=counter_subject,
        predicate=counter_predicate,
        object=counter_object,
        modality="hypothesis",
        confidence=counter_confidence,
        scope=claim.scope.copy(),
        qualifier=claim.qualifier.copy(),
        status="unknown",
        parent_id=claim.id,
    )
    state.claims[cid] = counter

    contradicts = check_for_contradiction(claim, counter)
    if contradicts:
        claim.status = "contradicted"
    else:
        claim.status = "disputed"

    claim.conflict = True
    # Boost confidence past T5 threshold to prevent re-triggering
    claim.confidence = max(claim.confidence, 0.42)
    claim.history.append("T5")
    state.operation_history.append(f"T5 on {claim.id}")
    contra_note = " [CONTRADICTS]" if contradicts else ""
    return f"Counter-hypothesis generated{llm_note}{contra_note}: {cid} — {reasoning}"


def t6_explore_evidence_path(claim: Claim, state: EpistemicState) -> str:
    """Suggest evidence sources for a high-confidence hypothesis and advance it to supported."""
    prompt = f"""You are an epistemic research advisor.
Given this hypothesis with reasonable confidence:
{_claim_summary(claim)}

Suggest 2-3 concrete evidence sources or research directions that could confirm or refute it.
Return ONLY valid JSON:
{{
  "evidence_paths": [
    {{"source": "...", "type": "empirical|theoretical|literature", "rationale": "..."}},
    {{"source": "...", "type": "empirical|theoretical|literature", "rationale": "..."}}
  ]
}}"""

    result = _llm_json(prompt)
    if result and "evidence_paths" in result:
        for ep in result["evidence_paths"][:3]:
            ref = f"[PATH:{ep.get('type','?')}] {ep.get('source','')} — {ep.get('rationale','')}"
            claim.evidence_refs.append(ref)
        claim.confidence = min(1.0, claim.confidence + 0.15)
    # Evidence exploration completes hypothesis evaluation; advance to T8-ready state
    claim.status = "supported"
    claim.confidence = max(0.82, min(1.0, claim.confidence + 0.15))
    claim.history.append("T6")
    state.operation_history.append(f"T6 on {claim.id}")
    return f"Evidence paths added: {len(result.get('evidence_paths', [])) if result else 0}"


def t7_refine_qualifier(claim: Claim, state: EpistemicState) -> str:
    """Add temporal and/or geographic qualifiers to narrow the claim's scope."""
    prompt = f"""You are an epistemic qualifier engine.
Given this claim that has scope but no qualifier:
{_claim_summary(claim)}

Add appropriate temporal and/or geographic qualifiers to make the claim more precise.
Return ONLY valid JSON:
{{
  "qualifier": {{"temporal": "...", "geographic": "..."}}
}}"""

    result = _llm_json(prompt)
    if result and "qualifier" in result:
        q = {k: v for k, v in result["qualifier"].items() if v}
        claim.qualifier = q
    if not claim.qualifier:
        claim.qualifier = {"temporal": "present", "geographic": "global"}
    claim.confidence = min(1.0, claim.confidence + 0.05)
    claim.history.append("T7")
    state.operation_history.append(f"T7 on {claim.id}")
    return f"Qualifier added: {claim.qualifier}"


def t8_seal_claim(claim: Claim, state: EpistemicState) -> str:
    """Mark claim as epistemically complete."""
    claim.sealed = True
    claim.history.append("T8")
    state.operation_history.append(f"T8 on {claim.id}")
    return f"Claim {claim.id} sealed."


T9_PROMPT = """\
Two competing hypotheses have both been supported by evidence:
Branch A: {branch_a_subject} {branch_a_predicate} {branch_a_object} (confidence={branch_a_conf:.2f})
Branch B: {branch_b_subject} {branch_b_predicate} {branch_b_object} (confidence={branch_b_conf:.2f})

Synthesize these into a refined, more nuanced claim that integrates both perspectives,
or identify a higher-level reframing that makes the apparent contradiction productive.

Return ONLY valid JSON:
{{
  "subject": "...",
  "predicate": "...",
  "object": "...",
  "modality": "suggestion",
  "confidence": 0.75,
  "rationale": "..."
}}"""


def t9_trigger_reframing(claim: Claim, state: EpistemicState) -> str:
    """Synthesize two supported branch claims into a new, more nuanced claim."""
    branches = [c for c in state.claims.values() if c.parent_id == claim.id]
    if len(branches) < 2:
        branches = branches + [branches[0]] if branches else []

    ba = branches[0] if len(branches) > 0 else claim
    bb = branches[1] if len(branches) > 1 else claim

    prompt = T9_PROMPT.format(
        branch_a_subject=ba.subject, branch_a_predicate=ba.predicate,
        branch_a_object=ba.object, branch_a_conf=ba.confidence,
        branch_b_subject=bb.subject, branch_b_predicate=bb.predicate,
        branch_b_object=bb.object, branch_b_conf=bb.confidence,
    )
    result = _llm_json(prompt)

    if result:
        synth_subject = result.get("subject", claim.subject)
        synth_predicate = result.get("predicate", "reconciles")
        synth_object = result.get("object", claim.object)
        synth_conf = max(0.82, float(result.get("confidence", 0.75)))
        rationale = result.get("rationale", "")
        llm_note = ""
    else:
        synth_subject = claim.subject
        synth_predicate = "is context-dependent regarding"
        synth_object = claim.object
        synth_conf = 0.82
        rationale = "Both branches reached evidential support under different conditions (fallback synthesis)"
        llm_note = " (fallback)"

    cid = new_claim_id(state)
    synth = Claim(
        id=cid,
        subject=synth_subject,
        predicate=synth_predicate,
        object=synth_object,
        modality="suggestion",
        confidence=synth_conf,
        scope=claim.scope.copy(),
        qualifier=claim.qualifier.copy(),
        status="supported",
        is_synthesis=True,
        parent_id=claim.id,
    )
    synth.evidence_refs = [
        f"[synthesized from branches: {ba.id}, {bb.id}]",
        f"[SYNTHESIS{llm_note}] {rationale}",
    ]
    state.claims[cid] = synth
    state.reframing_count += 1
    claim.sealed = True
    claim.history.append("T9")
    state.operation_history.append(f"T9 on {claim.id}")
    return f"REFRAME{llm_note}: {claim.id} -> {cid} — {rationale}"


# ---------------------------------------------------------------------------
# Layer 3: Transition Table — Selector
# ---------------------------------------------------------------------------

def select_operation(claim: Claim, state: EpistemicState) -> tuple[str, callable]:
    """
    Evaluate the transition table and return (trigger_label, operation_fn).
    Priority: T1/T2 (CRITICAL) > T3/T4 (HIGH) > T5/T6 (MEDIUM) > T7 (LOW) > T8 > T9
    Synthesis claims (is_synthesis=True) bypass T3–T7 and go straight to T8.
    The LLM never calls this function — routing is always decided here.
    """
    if claim.is_synthesis:
        return "T8", t8_seal_claim
    if claim.status == "contradicted":
        return "T1", t1_resolve_conflict
    if claim.conflict:
        return "T2", t2_make_conflict_explicit
    if not claim.evidence_refs and claim.modality != "established":
        return "T3", t3_request_evidence
    if claim.status == "underspecified" or claim.scope == {}:
        return "T4", t4_decompose_claim
    if claim.confidence < 0.4 and claim.status != "contradicted":
        return "T5", t5_generate_counter_hypothesis
    if (claim.modality == "hypothesis" and claim.confidence > 0.6
            and claim.status != "supported" and "T6" not in claim.history):
        return "T6", t6_explore_evidence_path
    if claim.qualifier == {} and claim.scope != {}:
        return "T7", t7_refine_qualifier
    if claim.status == "supported" and claim.confidence > 0.8:
        return "T8", t8_seal_claim
    if claim.branch_open:
        branches = [c for c in state.claims.values() if c.parent_id == claim.id]
        if branches and all(c.status == "supported" for c in branches):
            return "T9", t9_trigger_reframing
    if claim.modality == "hypothesis" and "T6" not in claim.history:
        return "T6", t6_explore_evidence_path
    return "T8", t8_seal_claim


# ---------------------------------------------------------------------------
# Layer 5: Weak Hypothesis Retention
# ---------------------------------------------------------------------------

def process_weak_candidates(state: EpistemicState, focus_claim: Claim) -> None:
    """Reactivate weak candidates that share subject/object overlap with the focus claim."""
    for wid in list(state.weak_candidates):
        if wid not in state.claims:
            continue
        wc = state.claims[wid]
        if (focus_claim.subject.lower() in wc.subject.lower() or
                wc.subject.lower() in focus_claim.subject.lower() or
                focus_claim.object.lower() in wc.object.lower() or
                wc.object.lower() in focus_claim.object.lower()):
            state.weak_candidates.remove(wid)


def maybe_move_to_weak(claim: Claim, state: EpistemicState) -> bool:
    """Move claim to weak_candidates if confidence < 0.3 and not contradicted or sealed."""
    if claim.confidence < 0.3 and claim.status != "contradicted" and not claim.sealed:
        if claim.id not in state.weak_candidates:
            state.weak_candidates.append(claim.id)
            return True
    return False


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def select_focus_claim(state: EpistemicState) -> Optional[Claim]:
    """
    Select the next claim to process.
    T9-ready claims (branch_open + all children supported) take priority.
    Branch-open claims with unresolved children are skipped until branches complete.
    """
    weak_set = set(state.weak_candidates)
    t9_ready: list[Claim] = []
    regular: list[Claim] = []

    for cid, claim in state.claims.items():
        if claim.sealed or cid in weak_set:
            continue
        if claim.branch_open:
            children = [c for c in state.claims.values() if c.parent_id == cid]
            if children and all(c.status == "supported" for c in children):
                t9_ready.append(claim)
        else:
            regular.append(claim)

    if t9_ready:
        return t9_ready[0]
    if regular:
        return regular[0]
    return None


def print_iteration_trace(
    iteration: int,
    claim: Claim,
    trigger: str,
    op_name: str,
    result: str,
    state: EpistemicState,
) -> None:
    """Print the structured per-iteration trace to stdout."""
    active = sum(1 for c in state.claims.values() if not c.sealed)
    sealed = sum(1 for c in state.claims.values() if c.sealed)
    weak = len(state.weak_candidates)
    branch_flag = " branch_open=True" if claim.branch_open else ""
    print(f"\n=== DES Iteration {iteration} ===")
    print(f"Focus Claim: {claim.id} [status={claim.status}, confidence={claim.confidence:.2f}{branch_flag}]")
    print(f"  subject: {claim.subject}")
    print(f"  predicate: {claim.predicate}")
    print(f"  object: {claim.object}")
    print(f"Trigger: {trigger} ({op_name})")
    print(f"Operation: {op_name}")
    print(f"Result: {result}")
    print(f"S(t): {active} claims active, {sealed} sealed, {weak} weak candidates")


def print_final_trace(state: EpistemicState) -> None:
    """Print the full epistemic path and claim summary at end of run."""
    print("\n" + "=" * 60)
    print("FINAL RESEARCH TRACE")
    print("=" * 60)
    print(f"Total iterations: {state.iteration}")
    print(f"Total claims: {len(state.claims)}")
    print(f"Reframings: {state.reframing_count}")
    print(f"\nGlobal operation history:")
    for i, op in enumerate(state.operation_history, 1):
        print(f"  {i:02d}. {op}")
    print(f"\nClaim summary:")
    for cid, claim in state.claims.items():
        prefix = "[SEALED]" if claim.sealed else "[ACTIVE]"
        weak = " [WEAK]" if cid in state.weak_candidates else ""
        parent = f" (child of {claim.parent_id})" if claim.parent_id else ""
        print(f"  {prefix} {cid}{weak}{parent}: {claim.subject} {claim.predicate} {claim.object}")
        print(f"    status={claim.status}, confidence={claim.confidence:.2f}, modality={claim.modality}")
        print(f"    history={claim.history}")
        if claim.evidence_refs:
            for ref in claim.evidence_refs[:2]:
                print(f"    evidence: {ref[:100]}")
    print(f"\nEpistemic path: {' → '.join(state.operation_history)}")
    print("=" * 60)


def run_des(
    research_question: str,
    max_iterations: int = 40,
    anti_delphi: bool = False,
) -> None:
    """Run the DES main loop on a research question, persisting S(t) after each iteration."""
    print(f"\nDynamic Epistemic Sequencer v0.1")
    print(f"Research question: {research_question}")
    mode_label = "Anti-Delphi (T5/T6/T9 dual-role)" if anti_delphi else "Single-agent"
    print(f"Mode: {mode_label}")
    print("-" * 60)

    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    state = EpistemicState()
    save_state(state)

    print("Generating initial claim via LLM...")
    initial_claim = generate_initial_claim(research_question, state)
    state.claims[initial_claim.id] = initial_claim
    save_state(state)
    print(f"Initial claim: [{initial_claim.id}] {initial_claim.subject} {initial_claim.predicate} {initial_claim.object}")

    while True:
        # Load S(t) from disk on every iteration (satisfies C1 + C2)
        state = load_state()

        if state.iteration >= max_iterations:
            print(f"\n[DES] Termination: max iterations ({max_iterations}) reached.")
            break
        if state.reframing_count > 2:
            print(f"\n[DES] Termination: reframing count exceeded (>{2}).")
            break

        all_sealed = all(c.sealed for c in state.claims.values()) and state.claims
        if all_sealed:
            print(f"\n[DES] Termination: all claims sealed.")
            break

        focus = select_focus_claim(state)
        if focus is None:
            print(f"\n[DES] No active claims to process. Terminating.")
            break

        process_weak_candidates(state, focus)

        trigger, op_fn = select_operation(focus, state)
        op_name = op_fn.__name__

        state.focus_claim_id = focus.id
        state.iteration += 1

        if anti_delphi and trigger in ("T5", "T6", "T9") and not focus.is_role_generated:
            role_claim_ids: list[str] = []
            for role in ("hypothesis_builder", "falsifier"):
                role_claim = execute_role(role, focus, state)
                if role_claim is not None:
                    state.claims[role_claim.id] = role_claim
                    state.operation_history.append(
                        f"{trigger}[{role}] on {focus.id} -> {role_claim.id}"
                    )
                    role_claim_ids.append(role_claim.id)
                    state.roles_generated.setdefault(role, []).append(role_claim.id)
            state.anti_delphi_activations += 1
            focus.history.append(f"{trigger}[anti-delphi]")
            _apply_antidelphi_state_change(trigger, focus, state, role_claim_ids)
            result = (
                f"Anti-Delphi {trigger}: {', '.join(role_claim_ids)}"
                if role_claim_ids else
                f"Anti-Delphi {trigger}: no claims generated (LLM fallback)"
            )
            op_name = f"{op_name}[AD]"
        else:
            result = op_fn(focus, state)

        for claim in state.claims.values():
            maybe_move_to_weak(claim, state)

        save_state(state)

        print_iteration_trace(state.iteration, focus, trigger, op_name, result, state)

    print_final_trace(state)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dynamic Epistemic Sequencer — epistemic state machine for AI research workflows",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Research question to investigate",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=40,
        help="Maximum number of iterations (default: 40)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete des_state.json and exit cleanly",
    )
    parser.add_argument(
        "--anti-delphi",
        action="store_true",
        help="Use Anti-Delphi mode: two isolated roles (hypothesis_builder, falsifier) on T5/T6/T9",
    )
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print("State cleared.")
        else:
            print("No state file found.")
        if not args.question:
            sys.exit(0)

    if not args.question:
        parser.print_help()
        sys.exit(1)

    run_des(args.question, max_iterations=args.max_iter, anti_delphi=args.anti_delphi)

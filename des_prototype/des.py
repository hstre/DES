"""
Dynamic Epistemic Sequencer (DES) — Standalone Prototype v0.1

Manages epistemic state transitions in AI research workflows.
All routing is done by the transition table; the LLM is a dumb operator.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import Optional

import anthropic

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
    history: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None  # set when this claim is a sub-claim

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Claim":
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

    def to_dict(self) -> dict:
        return {
            "claims": {k: v.to_dict() for k, v in self.claims.items()},
            "operation_history": self.operation_history,
            "discarded_hypotheses": self.discarded_hypotheses,
            "weak_candidates": self.weak_candidates,
            "reframing_count": self.reframing_count,
            "iteration": self.iteration,
            "focus_claim_id": self.focus_claim_id,
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
        )


# ---------------------------------------------------------------------------
# Layer 4: PES — Persistence
# ---------------------------------------------------------------------------

STATE_FILE = os.path.join(os.path.dirname(__file__), "des_state.json")


def save_state(state: EpistemicState) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_state() -> Optional[EpistemicState]:
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE) as f:
        return EpistemicState.from_dict(json.load(f))


def new_claim_id(state: EpistemicState) -> str:
    n = len(state.claims) + 1
    return f"C{n:03d}"


# ---------------------------------------------------------------------------
# LLM Integration (Layer 0)
# ---------------------------------------------------------------------------

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _llm_call(prompt: str) -> str:
    """Single LLM call, returns raw text."""
    response = get_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


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
    prompt = INITIAL_CLAIM_PROMPT.format(question=research_question)

    result = _llm_json(prompt)
    if result is None:
        result = {
            "subject": "fiscal austerity",
            "predicate": "reduces",
            "object": "sovereign debt in the long run",
            "status": "disputed",
            "modality": "hypothesis",
            "confidence": 0.45,
        }

    # Clamp confidence to the required uncertainty range
    confidence = float(result.get("confidence", 0.45))
    confidence = max(0.3, min(0.65, confidence))

    # Honor the LLM's status (hypothesis/disputed) — not override with "unknown"
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
    """BRANCH: create two sub-claims, request adjudication."""
    prompt = f"""You are an epistemic conflict resolver.
This claim is contradicted and needs adjudication:
{_claim_summary(claim)}

Create two opposing sub-claims (pro and con) that represent the contradiction.
Return ONLY valid JSON:
{{
  "sub_claims": [
    {{"subject": "...", "predicate": "...", "object": "...", "modality": "hypothesis", "confidence": 0.5, "scope": {{}}, "qualifier": {{}}}},
    {{"subject": "...", "predicate": "...", "object": "...", "modality": "hypothesis", "confidence": 0.5, "scope": {{}}, "qualifier": {{}}}}
  ]
}}"""

    result = _llm_json(prompt)
    new_ids = []
    if result and "sub_claims" in result:
        for sc in result["sub_claims"][:2]:
            cid = new_claim_id(state)
            new_claim = Claim(
                id=cid,
                subject=sc.get("subject", claim.subject),
                predicate=sc.get("predicate", claim.predicate),
                object=sc.get("object", claim.object),
                modality=sc.get("modality", "hypothesis"),
                confidence=float(sc.get("confidence", 0.5)),
                scope=sc.get("scope", {}),
                qualifier=sc.get("qualifier", {}),
                status="unknown",
                parent_id=claim.id,
            )
            state.claims[cid] = new_claim
            new_ids.append(cid)

    claim.branch_open = True
    claim.history.append("T1")
    state.operation_history.append(f"T1 on {claim.id}")
    return f"Branched into sub-claims: {', '.join(new_ids)}" if new_ids else "T1: branch creation failed, marked branch_open"


def t2_make_conflict_explicit(claim: Claim, state: EpistemicState) -> str:
    """PATCH with conflict reason, flag for user."""
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
    claim.conflict = False  # conflict is now explicit, flag cleared
    claim.history.append("T2")
    state.operation_history.append(f"T2 on {claim.id}")
    return f"Conflict made explicit: {reason}"


def t3_request_evidence(claim: Claim, state: EpistemicState) -> str:
    """Simulate tool call — return placeholder evidence."""
    simulated = f"[simulated evidence: search result for '{claim.subject} {claim.object}']"
    claim.evidence_refs.append(simulated)
    if claim.status == "unknown":
        claim.status = "disputed"  # evidence found but not yet evaluated
    claim.history.append("T3")
    state.operation_history.append(f"T3 on {claim.id}")
    return f"Evidence placeholder added: {simulated}"


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
    """LLM: break into 2–3 sub-claims."""
    prompt = T4_PROMPT.format(claim=_claim_summary(claim))

    result = _llm_json(prompt)
    raw_sub_claims = result.get("sub_claims", []) if result else []

    # Hard fallback: if the LLM fails to produce sub-claims, synthesize two structurally
    # distinct sub-claims manually so the sequencer can still branch and process them.
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
    claim.sealed = True  # parent sealed after decomposition
    claim.history.append("T4")
    state.operation_history.append(f"T4 on {claim.id}")
    return f"Decomposed into sub-claims{llm_note}: {', '.join(new_ids)}"


def t5_generate_counter_hypothesis(claim: Claim, state: EpistemicState) -> str:
    """LLM: adversarial prompt to generate counter-hypothesis."""
    prompt = f"""You are an adversarial epistemic engine.
Given this low-confidence claim:
{_claim_summary(claim)}

Generate a strong counter-hypothesis that challenges this claim.
Return ONLY valid JSON:
{{
  "counter_subject": "...",
  "counter_predicate": "...",
  "counter_object": "...",
  "counter_confidence": 0.6,
  "reasoning": "..."
}}"""

    result = _llm_json(prompt)

    # Build counter from LLM result or fall back to a structural negation
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

    # Generating a counter reveals a conflict on the original; T2 makes it explicit next visit.
    claim.status = "disputed"
    claim.conflict = True
    # Always boost confidence past the T5 threshold to prevent re-triggering T5.
    claim.confidence = max(claim.confidence, 0.42)
    claim.history.append("T5")
    state.operation_history.append(f"T5 on {claim.id}")
    return f"Counter-hypothesis generated{llm_note}: {cid} — {reasoning}"


def t6_explore_evidence_path(claim: Claim, state: EpistemicState) -> str:
    """LLM: suggest evidence sources for a high-confidence hypothesis."""
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
    # Evidence exploration completes hypothesis evaluation; boost confidence to T8 threshold
    claim.status = "supported"
    claim.confidence = max(0.82, min(1.0, claim.confidence + 0.15))
    claim.history.append("T6")
    state.operation_history.append(f"T6 on {claim.id}")
    return f"Evidence paths added: {len(result.get('evidence_paths', [])) if result else 0}"


def t7_refine_qualifier(claim: Claim, state: EpistemicState) -> str:
    """LLM: add temporal/geographic qualifier."""
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
    # Ensure qualifier is non-empty after T7 so it doesn't re-trigger
    if not claim.qualifier:
        claim.qualifier = {"temporal": "present", "geographic": "global"}
    # Qualification reduces ambiguity — small confidence boost
    claim.confidence = min(1.0, claim.confidence + 0.05)
    claim.history.append("T7")
    state.operation_history.append(f"T7 on {claim.id}")
    return f"Qualifier added: {claim.qualifier}"


def t8_seal_claim(claim: Claim, state: EpistemicState) -> str:
    """Mark as sealed, move to next."""
    claim.sealed = True
    claim.history.append("T8")
    state.operation_history.append(f"T8 on {claim.id}")
    return f"Claim {claim.id} sealed."


def t9_trigger_reframing(claim: Claim, state: EpistemicState) -> str:
    """LLM: synthesize or reframe when all branches are supported."""
    # Gather branch claims
    branches = [c for c in state.claims.values() if c.parent_id == claim.id]
    branch_summaries = [f"{c.id}: {c.subject} {c.predicate} {c.object} (conf={c.confidence:.2f})" for c in branches]

    prompt = f"""You are an epistemic synthesis engine.
The following branches of a claim have all been explored:
Parent claim: {claim.subject} {claim.predicate} {claim.object}
Branches:
{chr(10).join(branch_summaries)}

Synthesize these into a refined, higher-level claim or reframing.
Return ONLY valid JSON:
{{
  "synthesized_subject": "...",
  "synthesized_predicate": "...",
  "synthesized_object": "...",
  "confidence": 0.75,
  "synthesis_note": "..."
}}"""

    result = _llm_json(prompt)
    if result:
        cid = new_claim_id(state)
        synth = Claim(
            id=cid,
            subject=result.get("synthesized_subject", claim.subject),
            predicate=result.get("synthesized_predicate", "synthesized from"),
            object=result.get("synthesized_object", claim.object),
            modality="evidence",
            confidence=float(result.get("confidence", 0.75)),
            scope=claim.scope.copy(),
            qualifier=claim.qualifier.copy(),
            status="supported",
            parent_id=claim.id,
        )
        synth.evidence_refs.append(f"[SYNTHESIS] {result.get('synthesis_note', '')}")
        state.claims[cid] = synth
        state.reframing_count += 1
        claim.sealed = True
        claim.history.append("T9")
        state.operation_history.append(f"T9 on {claim.id}")
        return f"Reframing synthesized into {cid}: {result.get('synthesis_note', '')}"

    state.reframing_count += 1
    claim.history.append("T9")
    state.operation_history.append(f"T9 on {claim.id}")
    return "T9: reframing synthesis failed"


# ---------------------------------------------------------------------------
# Layer 3: Transition Table — Selector
# ---------------------------------------------------------------------------

def select_operation(claim: Claim, state: EpistemicState) -> tuple[str, callable]:
    """
    Evaluate the transition table and return (trigger_label, operation_fn).
    Priority order: T1/T2 (CRITICAL) > T3 (HIGH) > T4 (HIGH) > T5/T6 (MEDIUM) > T7 (LOW) > T8 > T9
    """
    # CRITICAL
    if claim.status == "contradicted":
        return "T1", t1_resolve_conflict
    if claim.conflict:
        return "T2", t2_make_conflict_explicit

    # HIGH
    if not claim.evidence_refs and claim.modality != "established":
        return "T3", t3_request_evidence
    if claim.status == "underspecified" or claim.scope == {}:
        return "T4", t4_decompose_claim

    # MEDIUM
    if claim.confidence < 0.4 and claim.status != "contradicted":
        return "T5", t5_generate_counter_hypothesis
    if (claim.modality == "hypothesis" and claim.confidence > 0.6
            and claim.status != "supported" and "T6" not in claim.history):
        return "T6", t6_explore_evidence_path

    # LOW
    if claim.qualifier == {} and claim.scope != {}:
        return "T7", t7_refine_qualifier

    # T8 — seal if supported and high confidence
    if claim.status == "supported" and claim.confidence > 0.8:
        return "T8", t8_seal_claim

    # T9 — reframing if branch_open and all branches supported
    if claim.branch_open:
        branches = [c for c in state.claims.values() if c.parent_id == claim.id]
        if branches and all(c.status == "supported" for c in branches):
            return "T9", t9_trigger_reframing

    # Stuck-state: hypothesis not yet evidence-explored
    if claim.modality == "hypothesis" and "T6" not in claim.history:
        return "T6", t6_explore_evidence_path

    # Claim has completed all productive operations — seal it
    return "T8", t8_seal_claim


# ---------------------------------------------------------------------------
# Layer 5: Weak Hypothesis Retention
# ---------------------------------------------------------------------------

def process_weak_candidates(state: EpistemicState, focus_claim: Claim) -> None:
    """Reactivate weak candidates that share subject/object with focus claim."""
    reactivated = []
    for wid in list(state.weak_candidates):
        if wid not in state.claims:
            continue
        wc = state.claims[wid]
        # Simple string overlap check
        if (focus_claim.subject.lower() in wc.subject.lower() or
                wc.subject.lower() in focus_claim.subject.lower() or
                focus_claim.object.lower() in wc.object.lower() or
                wc.object.lower() in focus_claim.object.lower()):
            state.weak_candidates.remove(wid)
            reactivated.append(wid)

    if reactivated:
        print(f"  [PES] Reactivated weak candidates: {', '.join(reactivated)}")


def maybe_move_to_weak(claim: Claim, state: EpistemicState) -> bool:
    """Move claim to weak_candidates if confidence < 0.3 and not contradicted."""
    if claim.confidence < 0.3 and claim.status != "contradicted" and not claim.sealed:
        if claim.id not in state.weak_candidates:
            state.weak_candidates.append(claim.id)
            return True
    return False


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def select_focus_claim(state: EpistemicState) -> Optional[Claim]:
    """Select first non-sealed, non-weak claim."""
    weak_set = set(state.weak_candidates)
    for cid, claim in state.claims.items():
        if not claim.sealed and cid not in weak_set:
            return claim
    return None


def print_iteration_trace(iteration: int, claim: Claim, trigger: str, op_name: str, result: str, state: EpistemicState) -> None:
    active = sum(1 for c in state.claims.values() if not c.sealed)
    sealed = sum(1 for c in state.claims.values() if c.sealed)
    weak = len(state.weak_candidates)
    print(f"\n=== DES Iteration {iteration} ===")
    print(f"Focus Claim: {claim.id} [status={claim.status}, confidence={claim.confidence:.2f}]")
    print(f"  subject: {claim.subject}")
    print(f"  predicate: {claim.predicate}")
    print(f"  object: {claim.object}")
    print(f"Trigger: {trigger} ({op_name})")
    print(f"Operation: {op_name}")
    print(f"Result: {result}")
    print(f"S(t): {active} claims active, {sealed} sealed, {weak} weak candidates")


def print_final_trace(state: EpistemicState) -> None:
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


def run_des(research_question: str, max_iterations: int = 10) -> None:
    print(f"\nDynamic Epistemic Sequencer v0.1")
    print(f"Research question: {research_question}")
    print("-" * 60)

    # 1. Initialize S(t) — fresh state (ignore any stale state file)
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    state = EpistemicState()
    save_state(state)

    # 2. Generate initial claim
    print("Generating initial claim via LLM...")
    initial_claim = generate_initial_claim(research_question, state)
    state.claims[initial_claim.id] = initial_claim
    save_state(state)
    print(f"Initial claim: [{initial_claim.id}] {initial_claim.subject} {initial_claim.predicate} {initial_claim.object}")

    # 3. Main loop
    while True:
        # a. Load S(t) from disk (satisfies C1 + C2)
        state = load_state()

        # Termination checks
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

        # b. Select focus claim
        focus = select_focus_claim(state)
        if focus is None:
            print(f"\n[DES] No active claims to process. Terminating.")
            break

        # Layer 5: check weak candidates for reactivation
        process_weak_candidates(state, focus)

        # c. Select operation via transition table
        trigger, op_fn = select_operation(focus, state)
        op_name = op_fn.__name__

        state.focus_claim_id = focus.id
        state.iteration += 1

        # d. Execute operation
        result = op_fn(focus, state)

        # e. Check if newly created claims should be moved to weak candidates
        for cid, claim in state.claims.items():
            if cid not in (list(state.claims.keys())):
                continue
            if maybe_move_to_weak(claim, state):
                print(f"  [PES] Claim {cid} moved to weak candidates (confidence={claim.confidence:.2f})")

        # f. Persist S(t)
        save_state(state)

        # g. Print iteration trace
        print_iteration_trace(state.iteration, focus, trigger, op_name, result, state)

    # 4. Final trace
    print_final_trace(state)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python des.py \"<research question>\"")
        sys.exit(1)

    question = sys.argv[1]
    max_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    run_des(question, max_iterations=max_iter)

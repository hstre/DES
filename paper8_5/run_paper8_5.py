"""
paper8_5/run_paper8_5.py
Paper 8.5 — Meta-Question Anchoring: Structural Constraint vs Abstract Seed.

H_meta: Structural constraint prompt prevents content-level drift
and keeps DES on design-level claim generation.

Arm A: Abstract seed — loaded from paper9/desi_consultation/ (NOT rerun).
Arm B: Same seed + STRUCTURAL_CONSTRAINT appended to research_question.
       Constraint passed as additional context; DES internals unchanged.

WP2 (Rentschler 2026). EXPLORATORY — not pre-registered.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.mol import (
    invoke_operator,
    extract_dominant_motif,
    extract_core_tension,
    extract_invariants,
    classify_trajectories,
    extract_dominant_claim,
)
from paper8.run_p8 import (
    _init_clients,
    call_llm,
    compute_metrics,
    check_failure,
    _claim_text,
    STATE_FILE,
    BUILDER_MODEL,
    BUILDER_PROVIDER,
    FALSIFIER_MODEL,
    FALSIFIER_PROVIDER,
)
import paper8.run_p8 as _p8

ARM_A_DIR  = Path("paper8_5/arm_a_reference")
ARM_B_DIR  = Path("paper8_5/arm_b_constrained")
OUTPUT_DIR = Path("paper8_5")
MAX_LOOPS  = 5
OPERATOR_LENS = "recursive_modulation"
MAX_ITER   = 40

SEED = """A research system (Desi) has completed investigations across Papers 4-8.
The working hypothesis for Paper 9 is:

operator_effectiveness = f(structural_operator, activation_frame, local_semantic_density)

Where density(q, r) = count(claims with sqrt_JSD(pi(c), pi(q)) < r) / n_claims

The planned experiment is a 2x3 factorial design:
- density: low (formal/narrow domains) vs high (argumentative/broad)
- framing: persona / explicit operator / stripped context

Paper 9 does NOT introduce a new epistemic object class.
It tests whether semantic density functions as a conditioning field
over existing operator classes.

Questions for Desi:
1. What is the most likely failure mode of this experimental design?
2. What does Desi not yet understand about its own density-dependent behavior?
3. Is there a simpler operationalization of the hypothesis that would be more falsifiable?"""

STRUCTURAL_CONSTRAINT = """
CONSTRAINT: Generate claims only of these types:
- measurable variables (what can be quantified)
- candidate metrics (how to measure it)
- falsifiable hypotheses (what would disprove this)
- operational definitions (precise definitions of terms)
- failure modes (specific ways this could fail)

Do NOT generate: content-level claims about information ecosystems,
misinformation, social dynamics, or other domain-level topics
unrelated to the research design question above."""

# Design-level keywords for claim classification
DESIGN_LEVEL_KEYWORDS = {
    "measurable": ["quantif", "measur", "observ", "count", "rate", "proportion"],
    "metric":     ["metric", "index", "score", "formula", "density", "jsd", "sqrt"],
    "hypothesis": ["if ", "when ", "predict", "expect", "hypothes", "falsif", "null"],
    "definition": ["defined as", "operationalized", "definition", "denoted", "refers to",
                   "specify", "denotes"],
    "failure":    ["failure", "confound", "bias", "artifact", "drift", "invalid", "spurious",
                   "collapse", "degenerate"],
}

CONTENT_LEVEL_KEYWORDS = [
    "digital ecosystem", "misinformation", "social dynamic", "collective sensemaking",
    "cultural narrative", "decentralized information", "gatekeep", "conspiracy",
    "polarization", "echo chamber",
]


def classify_claim_type(text: str) -> str:
    """Classify a claim as design-level type or content-level."""
    t = text.lower()
    for ctype, kws in DESIGN_LEVEL_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return ctype
    return "content_level"


def is_design_level(claim_type: str) -> bool:
    return claim_type != "content_level"


def compute_design_anchor_rate(claims: dict) -> tuple[float, dict]:
    """Return (design_anchor_rate, breakdown by type)."""
    sealed = {cid: c for cid, c in claims.items() if c.get("sealed")}
    if not sealed:
        return 0.0, {}
    type_counts: dict[str, int] = {}
    for c in sealed.values():
        ctype = classify_claim_type(_claim_text(c))
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
    design = sum(v for k, v in type_counts.items() if k != "content_level")
    rate = round(design / len(sealed), 3)
    return rate, type_counts


def check_questions_answered(claims: dict) -> dict[str, str]:
    """Heuristic: which of Q1/Q2/Q3 are addressed in sealed claims."""
    texts = " ".join(_claim_text(c).lower() for c in claims.values() if c.get("sealed"))
    q1 = ("partial" if any(kw in texts for kw in
          ["failure", "confound", "invalid", "bias", "artifact", "spurious"]) else "no")
    q2 = ("partial" if any(kw in texts for kw in
          ["not yet understand", "density-dependent", "density dependent",
           "does not yet know", "unknown behavior", "desi does not"]) else "no")
    q3 = ("partial" if any(kw in texts for kw in
          ["simpler", "operationalization", "falsifiable", "more falsifiable",
           "operationalize"]) else "no")
    return {"Q1": q1, "Q2": q2, "Q3": q3}


# ── Arm A: load existing data ─────────────────────────────────────────────────

def load_arm_a() -> dict:
    """Load Arm A from paper8_5/arm_a_reference/ (Paper 9 Desi Consultation)."""
    with open(ARM_A_DIR / "claimgraph_analysis.json") as f:
        analysis = json.load(f)
    with open(ARM_A_DIR / "metrics.json") as f:
        metrics = json.load(f)

    claims: dict = {}
    for loop_file in sorted(ARM_A_DIR.glob("loop_*_state.json")):
        with open(loop_file) as f:
            state = json.load(f)
        claims.update(state.get("claims", {}))

    dar, breakdown = compute_design_anchor_rate(claims)
    q_answered = check_questions_answered(claims)

    return {
        "arm":             "A",
        "label":           "Abstract seed (no constraint)",
        "loops":           len(metrics),
        "total_claims":    analysis["total_claims"],
        "total_sealed":    analysis["total_sealed"],
        "dominant_motif":  analysis["dominant_motif"],
        "dup_trend":       analysis["dup_trend"],
        "novel_trend":     analysis["novel_trend"],
        "design_anchor_rate": dar,
        "claim_type_breakdown": breakdown,
        "q_answered":      q_answered,
        "outcome":         "LOOP_COMPLETE",
        "attractor_type":  "content_level",
        "yield":           "medium",
    }


# ── Arm B: run with structural constraint ─────────────────────────────────────

def run_arm_b() -> dict:
    ARM_B_DIR.mkdir(parents=True, exist_ok=True)

    question         = SEED + STRUCTURAL_CONSTRAINT
    question_history = [question]
    loop_metrics     = []
    all_prior_texts  = []
    loop_states      = []
    final_outcome    = "MAX_LOOPS_REACHED"

    print(f"\n{'='*65}")
    print("  Paper 8.5 Arm B — Constrained seed")
    print(f"{'='*65}")

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    for loop in range(MAX_LOOPS):
        loop_file = ARM_B_DIR / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = SEED
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            loop_states.append(state)
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        try:
            _p8.des_module.run_des(
                research_question=question,
                max_iterations=MAX_ITER,
                anti_delphi=True,
                builder_model=BUILDER_MODEL,
                builder_provider=BUILDER_PROVIDER,
                falsifier_model=FALSIFIER_MODEL,
                falsifier_provider=FALSIFIER_PROVIDER,
            )
        except Exception as e:
            print(f"  ERROR in run_des: {e}")
            final_outcome = "DES_ERROR"
            break

        if not STATE_FILE.exists():
            print("  ERROR: des_state.json missing")
            final_outcome = "DES_ERROR"
            break

        with open(STATE_FILE) as f:
            state = json.load(f)
        state["seed_question"] = SEED

        with open(loop_file, "w") as f:
            json.dump(state, f, indent=2)
        loop_states.append(state)

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        loop_metrics.append(metrics)
        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        failure = check_failure(metrics, loop_metrics, [metrics["method_type"]] * loop)
        if failure:
            final_outcome = failure
            break

        # Mozart lens — append constraint to every follow-up question too
        if loop < MAX_LOOPS - 1:
            op_result = invoke_operator(
                OPERATOR_LENS, state, SEED, question_history,
                call_llm_fn=call_llm,
            )
            print(f"  [mozart lens] admitted={op_result['admitted']} "
                  f"eni={op_result.get('eni_composite', 0):.3f} | "
                  f"{op_result['question'][:60]}")
            base_q = op_result["question"] if op_result["admitted"] else _fallback_q(state)
            question = base_q + STRUCTURAL_CONSTRAINT
            question_history.append(question)
        else:
            final_outcome = "LOOP_COMPLETE"

    with open(ARM_B_DIR / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)

    # Aggregate all claims across loops
    all_claims: dict = {}
    for s in loop_states:
        all_claims.update(s.get("claims", {}))

    dar, breakdown = compute_design_anchor_rate(all_claims)
    q_answered     = check_questions_answered(all_claims)
    final_state    = loop_states[-1] if loop_states else {"claims": {}}
    motif          = extract_dominant_motif(final_state.get("claims", {}))
    tension        = extract_core_tension(final_state.get("claims", {}))
    invs           = extract_invariants(final_state.get("claims", {}))

    # Determine attractor type
    sealed_texts = [_claim_text(c).lower()
                    for c in all_claims.values() if c.get("sealed")]
    content_hits = sum(1 for t in sealed_texts
                       if any(kw in t for kw in CONTENT_LEVEL_KEYWORDS))
    attractor_type = "content_level" if content_hits > len(sealed_texts) * 0.3 else "design_level"

    total_sealed = sum(1 for c in all_claims.values() if c.get("sealed"))

    result = {
        "arm":             "B",
        "label":           "Structural constraint appended to research_question",
        "loops":           len(loop_metrics),
        "total_claims":    len(all_claims),
        "total_sealed":    total_sealed,
        "dominant_motif":  motif,
        "dup_trend":       [round(m.get("semantic_duplication_rate", 0), 3) for m in loop_metrics],
        "novel_trend":     [m.get("novel_claims", 0) for m in loop_metrics],
        "design_anchor_rate":   dar,
        "claim_type_breakdown": breakdown,
        "q_answered":      q_answered,
        "outcome":         final_outcome,
        "attractor_type":  attractor_type,
        "content_level_hits": content_hits,
        "all_claims":      all_claims,
        "invariants":      invs,
        "core_tension":    tension,
    }

    write_arm_b_md(result, loop_metrics)
    return result


def _fallback_q(state: dict) -> str:
    claims  = state.get("claims", {})
    motif   = extract_dominant_motif(claims)
    tension = extract_core_tension(claims)
    return call_llm(
        f"Given dominant motif '{motif['subject']} {motif['predicate']}' "
        f"and core tension '{tension}', generate one research question "
        f"exploring an adjacent conceptual register. Return ONLY one question.",
        max_tokens=100,
    )


# ── Write arm_b_consultation.md ───────────────────────────────────────────────

def write_arm_b_md(arm_b: dict, loop_metrics: list) -> None:
    all_claims = arm_b["all_claims"]
    sealed_list = [
        (cid, c) for cid, c in all_claims.items() if c.get("sealed")
    ]
    claims_text = "\n".join(
        f"  [{cid}] (conf={c.get('confidence',0):.2f}, {c.get('status','?')}) "
        f"[type={classify_claim_type(_claim_text(c))}] {_claim_text(c)}"
        for cid, c in sealed_list
    )

    type_breakdown_text = "\n".join(
        f"  - {k}: {v}" for k, v in arm_b["claim_type_breakdown"].items()
    ) or "  (no claims)"

    prompt = f"""You are writing Arm B analysis for Paper 8.5.
Paper 8.5 tests whether a structural constraint prevents content-level attractor drift in DES.
EXPLORATORY — not pre-registered, not confirmatory.

SEED (verbatim, without constraint):
{SEED}

STRUCTURAL CONSTRAINT (appended to every research_question):
{STRUCTURAL_CONSTRAINT}

ARM B RAW CLAIMGRAPH (all sealed claims, with type classification):
{claims_text}

DOMINANT MOTIF: {arm_b['dominant_motif']['subject']} / {arm_b['dominant_motif']['predicate']}
CORE TENSION: {arm_b['core_tension']}
DESIGN ANCHOR RATE: {arm_b['design_anchor_rate']} ({arm_b['total_sealed']} sealed)

CLAIM TYPE BREAKDOWN:
{type_breakdown_text}

Q1 (failure mode) answered: {arm_b['q_answered']['Q1']}
Q2 (density behavior) answered: {arm_b['q_answered']['Q2']}
Q3 (simpler operationalization) answered: {arm_b['q_answered']['Q3']}

ATTRACTOR TYPE (algorithmic): {arm_b['attractor_type']}
OUTCOME: {arm_b['outcome']} after {arm_b['loops']} loops.
DUP TREND: {arm_b['dup_trend']}

Write the analysis in this exact format. Report faithfully — do not curate.

---

# Paper 8.5 — Arm B: Structural Constraint Analysis
**Label: EXPLORATORY — not pre-registered, not confirmatory.**

## Structural Constraint Applied
[reproduce STRUCTURAL_CONSTRAINT verbatim]

## Dominant Motifs
[list 2-3 most frequent subject/predicate pairs]

## ClaimGraph Summary (all sealed claims)
[list ALL sealed claims numbered, include type classification]

## Claims Per Type
[list counts per type from breakdown]

## Seed Questions Addressed

### Q1: Most likely failure mode?
[answer from claims; if partial or no: state explicitly and quote most relevant claim]

### Q2: Density-dependent behavior Desi doesn't understand?
[answer from claims; if partial or no: state explicitly]

### Q3: Simpler operationalization?
[answer from claims; if partial or no: state explicitly]

## Attractor Analysis
- Algorithmic attractor type: [design_level / content_level]
- Content-level drift indicators: [list any content-level claims, or "none"]
- Compared to Arm A: [better / same / worse]

## Negative Findings
- Expected motifs not found:
- Structural constraint effectiveness: [prevented drift / partial / ineffective]
- Claims addressing all three questions: [yes / partial / no]
- design_anchor_rate: {arm_b['design_anchor_rate']} (threshold for CONFIRMED: >0.60)
- Overall yield: [high / medium / low / null]

## Raw Notes
[anything else observed]
"""

    md_text = call_llm(prompt, max_tokens=2500, temperature=0.3)
    header  = (
        "<!-- paper8_5/arm_b_constrained -->\n"
        "<!-- EXPLORATORY — not pre-registered, not confirmatory -->\n\n"
    )
    (ARM_B_DIR / "arm_b_consultation.md").write_text(header + md_text + "\n")
    print(f"  Written → {ARM_B_DIR}/arm_b_consultation.md")


# ── Write comparison.md ───────────────────────────────────────────────────────

def write_comparison_md(arm_a: dict, arm_b: dict) -> None:
    q_a = arm_a["q_answered"]
    q_b = arm_b["q_answered"]
    dar_a = arm_a["design_anchor_rate"]
    dar_b = arm_b["design_anchor_rate"]

    # Verdict
    q_b_count = sum(1 for v in q_b.values() if v in ("yes", "partial"))
    if q_b_count >= 2 and dar_b > 0.60:
        verdict = "CONFIRMED"
        verdict_note = f"Arm B answered {q_b_count}/3 questions AND design_anchor_rate={dar_b} > 0.60"
    elif q_b_count >= 1 or 0.30 <= dar_b <= 0.60:
        verdict = "PARTIAL"
        verdict_note = f"Arm B answered {q_b_count}/3 questions, design_anchor_rate={dar_b}"
    else:
        verdict = "NOT CONFIRMED"
        verdict_note = f"Arm B still drifted: answered {q_b_count}/3 questions, design_anchor_rate={dar_b}"

    prompt = f"""You are writing comparison.md for Paper 8.5.
This compares Arm A (abstract seed) vs Arm B (seed + structural constraint).

ARM A DATA:
- loops: {arm_a['loops']}
- total_sealed: {arm_a['total_sealed']}
- design_anchor_rate: {dar_a}
- claim_type_breakdown: {arm_a['claim_type_breakdown']}
- Q1 answered: {q_a['Q1']}, Q2: {q_a['Q2']}, Q3: {q_a['Q3']}
- attractor_type: {arm_a['attractor_type']}
- outcome: {arm_a['outcome']}
- yield: {arm_a['yield']}
- dominant_motif: {arm_a['dominant_motif']['subject']}

ARM B DATA:
- loops: {arm_b['loops']}
- total_sealed: {arm_b['total_sealed']}
- design_anchor_rate: {dar_b}
- claim_type_breakdown: {arm_b['claim_type_breakdown']}
- Q1 answered: {q_b['Q1']}, Q2: {q_b['Q2']}, Q3: {q_b['Q3']}
- attractor_type: {arm_b['attractor_type']}
- outcome: {arm_b['outcome']}
- dominant_motif: {arm_b['dominant_motif']['subject']}

H_meta VERDICT: {verdict}
Verdict note: {verdict_note}

Write the comparison in this exact format:

---

# Paper 8.5 — Comparison: Abstract Seed vs Structural Constraint

**H_meta: Structural constraint prompt prevents content-level drift and keeps DES on design-level claim generation.**

## Side-by-Side Comparison

| Metric | Arm A (abstract) | Arm B (constrained) |
|--------|-----------------|---------------------|
| Q1 answered | {q_a['Q1']} | {q_b['Q1']} |
| Q2 answered | {q_a['Q2']} | {q_b['Q2']} |
| Q3 answered | {q_a['Q3']} | {q_b['Q3']} |
| Attractor type | {arm_a['attractor_type']} | {arm_b['attractor_type']} |
| Claim types | {arm_a['claim_type_breakdown']} | {arm_b['claim_type_breakdown']} |
| loops_configured | 5 | 5 |
| loops_to_saturation | {arm_a['loops']} | {arm_b['loops']} |
| design_anchor_rate | {dar_a} | {dar_b} |
| Yield | {arm_a['yield']} | [state from your analysis] |

## H_meta Verdict

**{verdict}**

[Explain verdict in 2-3 sentences based on the data above]

## Implication for Paper 9

[If CONFIRMED: Structural constraint prompt is the solution. Paper 9 can proceed with abstract seed + constraint.]
[If PARTIAL: Describe what additional anchoring is needed.]
[If NOT CONFIRMED: Paper 9 seed must be redesigned with concrete claim anchors before Design Memo is written.]

## Negative Findings

- Unexpected result: [state if verdict was surprising]
- Constraint side effects: [any unintended effects on claim quality or DES behavior]
- Limitations: [what this single-run test cannot establish]
"""

    md_text = call_llm(prompt, max_tokens=1500, temperature=0.3)
    header  = (
        "<!-- paper8_5/comparison -->\n"
        "<!-- EXPLORATORY — not pre-registered, not confirmatory -->\n\n"
    )
    (OUTPUT_DIR / "comparison.md").write_text(header + md_text + "\n")
    print(f"  Written → {OUTPUT_DIR}/comparison.md")

    # Also save structured results
    summary = {
        "label": "Paper 8.5 — Meta-Question Anchoring",
        "h_meta_verdict": verdict,
        "verdict_note": verdict_note,
        "arm_a": {k: v for k, v in arm_a.items() if k != "all_claims"},
        "arm_b": {k: v for k, v in arm_b.items() if k != "all_claims"},
    }
    with open(OUTPUT_DIR / "paper8_5_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Written → {OUTPUT_DIR}/paper8_5_summary.json")


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all() -> None:
    _init_clients()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nPaper 8.5 — Meta-Question Anchoring")
    print("Loading Arm A from paper8_5/arm_a_reference/ ...")
    arm_a = load_arm_a()
    print(f"  Arm A: loops={arm_a['loops']}, sealed={arm_a['total_sealed']}, "
          f"dar={arm_a['design_anchor_rate']}, "
          f"Q1={arm_a['q_answered']['Q1']} Q2={arm_a['q_answered']['Q2']} Q3={arm_a['q_answered']['Q3']}")

    print("\nRunning Arm B (structural constraint) ...")
    arm_b = run_arm_b()
    print(f"  Arm B: loops={arm_b['loops']}, sealed={arm_b['total_sealed']}, "
          f"dar={arm_b['design_anchor_rate']}, "
          f"Q1={arm_b['q_answered']['Q1']} Q2={arm_b['q_answered']['Q2']} Q3={arm_b['q_answered']['Q3']}")

    print("\nWriting comparison ...")
    write_comparison_md(arm_a, arm_b)

    print("\nPaper 8.5 complete.")


if __name__ == "__main__":
    run_all()

"""
Adversarial CoT baseline comparison — v2 (corrected).

Fixes vs v1:
  1. Randomized blind evaluation: DES/CoT randomly assigned to A/B per question.
  2. DES output rendered as prose (not raw ClaimGraph dump).

Results saved to batch_results_baseline_v2/.
DES states loaded from batch_results_multimodel/DS4_DS4_*_state.json (no re-runs).
"""

import json
import os
import random
import re
import time
from pathlib import Path

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/v1",
)
MODEL = "deepseek-chat"

QUESTIONS = {
    "A1": "Does raising the minimum wage increase unemployment?",
    "A2": "Is foreign aid effective at reducing poverty?",
    "A3": "Does immigration reduce wages for native workers?",
    "B1": "Is GDP a good measure of economic wellbeing?",
    "B2": "Is remote work more productive than office work?",
    "B3": "Is social media harmful to democracy?",
    "C1": "Is technology good?",
    "C2": "Is globalization beneficial?",
    "D1": "Is intermittent fasting effective for long-term weight loss?",
    "D2": "Does class size reduction improve educational outcomes?",
    "D3": "Is gene editing ethically justifiable in humans?",
    "E1": "Is free trade both beneficial and harmful to developing economies?",
    "E2": "Is economic growth compatible with ecological sustainability?",
}

RESULTS_DIR = Path("batch_results_baseline_v2")
RESULTS_DIR.mkdir(exist_ok=True)

random.seed(42)  # reproducible assignment sequence


# ---------------------------------------------------------------------------
# DES prose renderer
# ---------------------------------------------------------------------------

def render_des_report(state: dict, question: str) -> str:
    """Convert DES epistemic state to a readable prose report."""
    claims = state.get("claims", {})
    op_history = state.get("operation_history", [])

    initial     = [c for cid, c in claims.items() if cid == "C001"]
    contradicted = [c for c in claims.values()
                    if c.get("status") == "contradicted" or c.get("conflict")]
    branches    = [c for c in claims.values()
                   if str(c.get("id", "")).startswith("B") or
                   any("BRANCH" in op for op in c.get("history", []))]
    syntheses   = [c for c in claims.values() if c.get("is_synthesis")]
    open_claims = [c for c in claims.values() if not c.get("sealed")]

    lines = [f"Research question: {question}", ""]

    if initial:
        c = initial[0]
        lines.append(
            f"Initial claim: {c.get('subject','')} {c.get('predicate','')} "
            f"{c.get('object','')} (confidence: {c.get('confidence', 0):.2f})"
        )
    lines.append("")

    if contradicted:
        lines.append(f"Contradictions identified: {len(contradicted)}")
        for c in contradicted:
            lines.append(
                f"  - {c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')} [status: {c.get('status','')}]"
            )
    lines.append("")

    if branches:
        lines.append(f"Competing hypotheses explored: {len(branches)}")
        for c in branches:
            lines.append(
                f"  - {c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')} [{c.get('status','')}, conf: {c.get('confidence', 0):.2f}]"
            )
    lines.append("")

    if syntheses:
        lines.append(f"Synthesis conclusions: {len(syntheses)}")
        for c in syntheses:
            lines.append(
                f"  - {c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')} (confidence: {c.get('confidence', 0):.2f})"
            )
    lines.append("")

    if open_claims:
        lines.append(f"Unresolved tensions: {len(open_claims)}")
        for c in open_claims:
            lines.append(
                f"  - {c.get('subject','')} {c.get('predicate','')} "
                f"{c.get('object','')} [status: {c.get('status','')}]"
            )
    lines.append("")

    lines.append(f"Total claims generated: {len(claims)}")
    lines.append(f"Epistemic operations applied: {len(op_history)}")

    return "\n".join(lines)


def load_des_state(qid: str) -> dict:
    p = Path(f"batch_results_multimodel/DS4_DS4_{qid}_state.json")
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Adversarial CoT prompt (unchanged from v1)
# ---------------------------------------------------------------------------

ADVERSARIAL_COT_PROMPT = """You are an epistemic research system conducting
structured adversarial analysis.

Research question: {question}

Execute the following steps in sequence:

STEP 1 — INITIAL CLAIM:
State a clear, directional claim in response to the question.
Format: "Claim: [subject] [predicate] [object]"
Confidence: [0.0-1.0]

STEP 2 — FALSIFICATION:
Now play the role of a sharp, committed falsifier.
Find the strongest possible objection to your Step 1 claim.
Do not hedge. Commit to a direction.
Format: "Counter-claim: [subject] [predicate] [object]"
The counter-claim must directly oppose the direction of the initial claim,
not merely qualify it.

STEP 3 — CONTRADICTION CHECK:
Does the counter-claim directly contradict the initial claim such that
both cannot be true simultaneously?
Answer: YES or NO
If YES: explain in one sentence why they are incompatible.
If NO: explain what the counter-claim qualifies rather than contradicts.

STEP 4 — SYNTHESIS:
If contradiction (YES): synthesize both claims into a qualified conclusion
that identifies the scope condition under which each holds.
If qualification (NO): refine the initial claim to incorporate the
qualifying condition from the counter-claim.
Format: "Synthesis: [qualified conclusion]"
Confidence: [0.0-1.0]

Produce all four steps. Do not skip any.
"""

# ---------------------------------------------------------------------------
# Blind evaluator prompt (v2 — no system labels)
# ---------------------------------------------------------------------------

EVALUATOR_PROMPT_V2 = """You are a neutral epistemic evaluator.
Compare two research outputs on the same question.
You do not know which system produced which output.

Research question: {question}

OUTPUT A:
{output_a}

OUTPUT B:
{output_b}

Evaluate on four dimensions. For each, state which output is better
(A, B, or EQUAL) and explain in one sentence.

1. DIRECTIONAL COMMITMENT: Which output makes clearer directional claims
   rather than hedged generalities?

2. CONTRADICTION DEPTH: Which output identifies more fundamental or
   numerous contradictions, not just surface-level qualifications?

3. SYNTHESIS QUALITY: Which output produces a more precise, scope-bounded
   synthesis that resolves the contradiction productively?

4. EPISTEMIC NOVELTY: Which output surfaces a perspective or tension that
   a domain expert would find non-obvious?

OVERALL VERDICT: A, B, or EQUAL. Justify in 2-3 sentences.

Return ONLY valid JSON:
{{
  "directional_commitment": {{"winner": "A", "reason": "..."}},
  "contradiction_depth": {{"winner": "A", "reason": "..."}},
  "synthesis_quality": {{"winner": "A", "reason": "..."}},
  "epistemic_novelty": {{"winner": "A", "reason": "..."}},
  "overall": {{"winner": "A", "justification": "..."}}
}}
"""


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def call_llm(prompt: str, max_tokens: int = 1200) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


def parse_cot_output(text: str) -> dict:
    return {
        "raw": text,
        "has_claim": "Claim:" in text,
        "has_counter": "Counter-claim:" in text,
        "has_contradiction_check": "YES" in text or "NO" in text,
        "has_synthesis": "Synthesis:" in text,
        "contradiction_detected": "YES" in text and "Counter-claim:" in text,
        "steps_complete": all(f"STEP {i}" in text for i in [1, 2, 3, 4]),
    }


# ---------------------------------------------------------------------------
# Blind evaluation with randomized assignment
# ---------------------------------------------------------------------------

def evaluate_blind(question: str, des_report: str, cot_output: str) -> dict:
    if random.random() > 0.5:
        output_a, output_b = des_report, cot_output
        assignment = {"A": "DES", "B": "CoT"}
    else:
        output_a, output_b = cot_output, des_report
        assignment = {"A": "CoT", "B": "DES"}

    prompt = EVALUATOR_PROMPT_V2.format(
        question=question,
        output_a=output_a,
        output_b=output_b,
    )

    try:
        raw = call_llm(prompt, max_tokens=800)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        eval_data = json.loads(clean)
    except Exception as e:
        print(f"    Evaluator parse error: {e}")
        eval_data = {"error": str(e), "overall": {"winner": "UNKNOWN"}}

    raw_winner = eval_data.get("overall", {}).get("winner", "UNKNOWN")
    actual_winner = assignment.get(raw_winner, raw_winner) if raw_winner in ("A", "B") else raw_winner

    eval_data["assignment"] = assignment
    eval_data["raw_winner"] = raw_winner
    eval_data["actual_winner"] = actual_winner

    # Translate per-dimension winners too
    for dim in ("directional_commitment", "contradiction_depth",
                "synthesis_quality", "epistemic_novelty"):
        d = eval_data.get(dim, {})
        rw = d.get("winner", "UNKNOWN")
        d["actual_winner"] = assignment.get(rw, rw) if rw in ("A", "B") else rw

    return eval_data


# ---------------------------------------------------------------------------
# Per-question runner
# ---------------------------------------------------------------------------

def run_question(qid: str, question: str) -> dict:
    print(f"\n{'='*60}")
    print(f"  {qid}: {question[:55]}")

    result = {"qid": qid, "question": question}

    # Load DES state and render prose
    print("  Rendering DES report...")
    state = load_des_state(qid)
    des_report = render_des_report(state, question)
    result["des_report"] = des_report

    # Adversarial CoT
    print("  Running Adversarial CoT...")
    cot_output = call_llm(ADVERSARIAL_COT_PROMPT.format(question=question), max_tokens=1500)
    parsed = parse_cot_output(cot_output)
    result["cot_output"] = cot_output
    result["cot_parsed"] = parsed
    time.sleep(1)

    # Blind evaluation
    print("  Running blind evaluator...")
    eval_data = evaluate_blind(question, des_report, cot_output)
    result["evaluation"] = eval_data
    result["assignment"] = eval_data["assignment"]
    result["raw_winner"] = eval_data["raw_winner"]
    result["actual_winner"] = eval_data["actual_winner"]
    time.sleep(2)

    out_path = RESULTS_DIR / f"{qid}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  -> Assignment: DES={eval_data['assignment']['A'] == 'DES' and 'A' or 'B'} "
          f"| Raw winner: {eval_data['raw_winner']} "
          f"| Actual winner: {eval_data['actual_winner']}")

    return result


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(results: list[dict]):
    print("\n" + "=" * 80)
    print("BASELINE v2 COMPARISON SUMMARY (blind, prose-rendered)")
    print("=" * 80)

    wins = {"DES": 0, "CoT": 0, "EQUAL": 0, "UNKNOWN": 0}
    dim_wins: dict[str, dict[str, int]] = {
        dim: {"DES": 0, "CoT": 0, "EQUAL": 0}
        for dim in ("directional_commitment", "contradiction_depth",
                    "synthesis_quality", "epistemic_novelty")
    }
    des_as_a = sum(1 for r in results if r["assignment"]["A"] == "DES")
    des_as_b = sum(1 for r in results if r["assignment"]["B"] == "DES")
    des_as_a_wins = sum(1 for r in results
                        if r["assignment"]["A"] == "DES" and r["actual_winner"] == "DES")
    des_as_b_wins = sum(1 for r in results
                        if r["assignment"]["B"] == "DES" and r["actual_winner"] == "DES")

    print(f"\n{'QID':<5} {'Des=?':<6} {'RawWin':<8} {'ActualWin':<12} "
          f"{'Dir':<6} {'Ctr':<6} {'Syn':<6} {'Nov':<6}")
    print("-" * 60)

    for r in results:
        ev = r.get("evaluation", {})
        des_label = "A" if r["assignment"]["A"] == "DES" else "B"
        actual = r["actual_winner"]
        wins[actual] = wins.get(actual, 0) + 1

        def aw(dim):
            return ev.get(dim, {}).get("actual_winner", "?")[:3]

        for dim in dim_wins:
            aw_val = ev.get(dim, {}).get("actual_winner", "UNKNOWN")
            dim_wins[dim][aw_val] = dim_wins[dim].get(aw_val, 0) + 1

        print(f"{r['qid']:<5} {des_label:<6} {r['raw_winner']:<8} {actual:<12} "
              f"{aw('directional_commitment'):<6} {aw('contradiction_depth'):<6} "
              f"{aw('synthesis_quality'):<6} {aw('epistemic_novelty'):<6}")

    print("-" * 60)
    print(f"\nActual wins: DES={wins['DES']}, CoT={wins['CoT']}, "
          f"Equal={wins.get('EQUAL',0)}, Unknown={wins.get('UNKNOWN',0)}")

    print(f"\nPer-dimension wins (actual):")
    for dim, dw in dim_wins.items():
        print(f"  {dim}: DES={dw.get('DES',0)}, CoT={dw.get('CoT',0)}, "
              f"Equal={dw.get('EQUAL',0)}")

    print(f"\nLabel bias check:")
    print(f"  DES assigned to A: {des_as_a} questions | DES wins when A: {des_as_a_wins}")
    print(f"  DES assigned to B: {des_as_b} questions | DES wins when B: {des_as_b_wins}")
    bias_flag = abs(des_as_a_wins - des_as_b_wins) > 2
    print(f"  Label bias detected: {'YES (difference > 2)' if bias_flag else 'NO'}")

    # Write summary.md
    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("# DES vs Adversarial CoT — Baseline Comparison v2 (Corrected)\n\n")
        f.write(f"**Model:** {MODEL}  \n")
        f.write(f"**Questions:** 13  \n")
        f.write(f"**Evaluator:** blind (randomized A/B assignment, prose-rendered DES output)  \n\n")
        f.write("## Evaluator Verdicts\n\n")
        f.write(f"- DES wins: {wins['DES']}/13\n")
        f.write(f"- CoT wins: {wins['CoT']}/13\n")
        f.write(f"- Equal: {wins.get('EQUAL',0)}/13\n\n")
        f.write("## Per-Dimension Wins (actual, after de-randomization)\n\n")
        f.write("| Dimension | DES | CoT | Equal |\n|---|---|---|---|\n")
        for dim, dw in dim_wins.items():
            f.write(f"| {dim} | {dw.get('DES',0)} | {dw.get('CoT',0)} | "
                    f"{dw.get('EQUAL',0)} |\n")
        f.write("\n## Label Bias Check\n\n")
        f.write(f"- DES assigned to A: {des_as_a} questions | "
                f"DES wins when assigned A: {des_as_a_wins}\n")
        f.write(f"- DES assigned to B: {des_as_b} questions | "
                f"DES wins when assigned B: {des_as_b_wins}\n")
        f.write(f"- Label bias detected: {'**YES** (difference > 2)' if bias_flag else 'No'}\n\n")
        f.write("## Per-Question Results\n\n")
        f.write("| QID | DES label | Raw winner | Actual winner | "
                "Dir | Ctr | Syn | Nov |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in results:
            ev = r.get("evaluation", {})
            des_label = "A" if r["assignment"]["A"] == "DES" else "B"
            def aw(dim): return ev.get(dim, {}).get("actual_winner", "?")
            f.write(f"| {r['qid']} | {des_label} | {r['raw_winner']} | "
                    f"{r['actual_winner']} | {aw('directional_commitment')} | "
                    f"{aw('contradiction_depth')} | {aw('synthesis_quality')} | "
                    f"{aw('epistemic_novelty')} |\n")
        f.write("\n## Per-Question Justifications\n\n")
        for r in results:
            ev = r.get("evaluation", {})
            des_label = "A" if r["assignment"]["A"] == "DES" else "B"
            f.write(f"### {r['qid']}: {r['question']}\n\n")
            f.write(f"DES was Output {des_label}. Raw winner: {r['raw_winner']}. "
                    f"Actual winner: {r['actual_winner']}.\n\n")
            for dim in ("directional_commitment", "contradiction_depth",
                        "synthesis_quality", "epistemic_novelty"):
                d = ev.get(dim, {})
                f.write(f"- **{dim.replace('_',' ').title()}**: "
                        f"{d.get('actual_winner','?')} (raw: {d.get('winner','?')}) — "
                        f"{d.get('reason','')}\n")
            overall = ev.get("overall", {})
            f.write(f"- **Overall**: {r['actual_winner']} — "
                    f"{overall.get('justification','')}\n\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = []
    for qid, question in QUESTIONS.items():
        out_path = RESULTS_DIR / f"{qid}.json"
        if out_path.exists():
            print(f"  [skip] {qid} already exists")
            with open(out_path) as f:
                results.append(json.load(f))
            continue
        try:
            r = run_question(qid, question)
            results.append(r)
        except Exception as e:
            print(f"  ERROR on {qid}: {e}")

    print_summary(results)
    print(f"\nResults saved to {RESULTS_DIR}/")

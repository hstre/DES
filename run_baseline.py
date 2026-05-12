"""
Adversarial CoT baseline comparison.
Conditions A and B on all 13 questions.
Condition C loaded from existing batch_results_multimodel/DS4_DS4/.
"""

import json, time, re, glob
from pathlib import Path
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com/v1"
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

RESULTS_DIR = Path("batch_results_baseline")
RESULTS_DIR.mkdir(exist_ok=True)


# ── CONDITION A: Vanilla CoT ─────────────────────────────────────────────────

VANILLA_PROMPT = """You are a research assistant.

Research question: {question}

Provide a clear, well-reasoned answer. Consider relevant evidence and
state your conclusion with appropriate confidence.
"""


# ── CONDITION B: Adversarial CoT ─────────────────────────────────────────────

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


# ── CONDITION B EVALUATOR ────────────────────────────────────────────────────

EVALUATOR_PROMPT = """You are a neutral epistemic evaluator.
You will compare two research outputs on the same question and assess
which provides more epistemically productive analysis.

Research question: {question}

OUTPUT A (DES Anti-Delphi):
{des_output}

OUTPUT B (Adversarial CoT):
{cot_output}

Evaluate on these four dimensions. For each, state which output is better
(A, B, or EQUAL) and explain in one sentence why.

1. DIRECTIONAL COMMITMENT: Which output produces clearer directional claims
   rather than hedged generalities?

2. CONTRADICTION DEPTH: Which output identifies a more fundamental
   contradiction, not just a surface-level qualification?

3. SYNTHESIS QUALITY: Which output produces a more precise, scope-bounded
   synthesis that resolves the contradiction?

4. EPISTEMIC NOVELTY: Which output surfaces a perspective or tension that
   a domain expert would find non-obvious?

Then give an OVERALL VERDICT: A, B, or EQUAL.
Justify the verdict in 2-3 sentences.

Return ONLY valid JSON:
{{
  "directional_commitment": {{"winner": "A", "reason": "..."}},
  "contradiction_depth": {{"winner": "A", "reason": "..."}},
  "synthesis_quality": {{"winner": "A", "reason": "..."}},
  "epistemic_novelty": {{"winner": "A", "reason": "..."}},
  "overall": {{"winner": "A", "justification": "..."}}
}}
"""


def call_llm(prompt: str, max_tokens: int = 1200) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


def parse_cot_output(text: str) -> dict:
    result = {
        "raw": text,
        "has_claim": "Claim:" in text,
        "has_counter": "Counter-claim:" in text,
        "has_contradiction_check": "YES" in text or "NO" in text,
        "has_synthesis": "Synthesis:" in text,
        "contradiction_detected": "YES" in text and "Counter-claim:" in text,
        "steps_complete": all(f"STEP {i}" in text for i in [1, 2, 3, 4]),
    }
    conf_match = re.search(r'Synthesis:.*?Confidence:\s*([0-9.]+)', text, re.DOTALL)
    result["synthesis_confidence"] = float(conf_match.group(1)) if conf_match else None
    return result


def classify_cot_topology(parsed: dict) -> str:
    if not parsed["steps_complete"]:
        return "incomplete"
    if parsed["contradiction_detected"] and parsed["has_synthesis"]:
        return "contested"
    elif parsed["has_counter"] and not parsed["contradiction_detected"]:
        return "T2_path"
    elif parsed["has_claim"] and not parsed["has_counter"]:
        return "linear"
    return "unknown"


def load_des_output(qid: str) -> str:
    state_path = Path(f"batch_results_multimodel/DS4_DS4_{qid}_state.json")
    if not state_path.exists():
        matches = glob.glob(f"batch_results_multimodel/DS4_DS4_{qid}_state.json")
        if matches:
            state_path = Path(matches[0])
        else:
            return "[DES output not available]"

    with open(state_path) as f:
        state = json.load(f)

    claims = state.get("claims", {})
    lines = [f"DES produced {len(claims)} claims via {state.get('iteration', 0)} iterations."]
    for cid, claim in sorted(claims.items()):
        status = claim.get("status", "?")
        conf = claim.get("confidence", 0)
        is_synth = claim.get("is_synthesis", False)
        tag = " [SYNTHESIS]" if is_synth else ""
        lines.append(
            f"  {cid}: {claim.get('subject','')} {claim.get('predicate','')} "
            f"{claim.get('object','')} [{status}, conf={conf}]{tag}"
        )
    return "\n".join(lines)


def run_question(qid: str, question: str) -> dict:
    print(f"\n{'='*60}")
    print(f"  {qid}: {question[:55]}")

    result = {"qid": qid, "question": question}

    # Condition A: Vanilla CoT
    print("  Running Condition A (Vanilla CoT)...")
    vanilla_output = call_llm(VANILLA_PROMPT.format(question=question))
    result["vanilla"] = {
        "output": vanilla_output,
        "word_count": len(vanilla_output.split()),
    }
    time.sleep(1)

    # Condition B: Adversarial CoT
    print("  Running Condition B (Adversarial CoT)...")
    cot_output = call_llm(ADVERSARIAL_COT_PROMPT.format(question=question), max_tokens=1500)
    parsed = parse_cot_output(cot_output)
    result["adversarial_cot"] = {
        "output": cot_output,
        "parsed": parsed,
        "topology": classify_cot_topology(parsed),
        "word_count": len(cot_output.split()),
    }
    time.sleep(1)

    # Condition C: Load DES output
    print("  Loading Condition C (DES Anti-Delphi DS4_DS4)...")
    des_output = load_des_output(qid)
    result["des_output_summary"] = des_output

    # Evaluator: DES vs Adversarial CoT
    print("  Running evaluator (DES vs CoT)...")
    try:
        eval_response = call_llm(
            EVALUATOR_PROMPT.format(
                question=question,
                des_output=des_output,
                cot_output=cot_output,
            ),
            max_tokens=800,
        )
        clean = eval_response.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        eval_data = json.loads(clean)
    except Exception as e:
        print(f"  Evaluator parse error: {e}")
        eval_data = {"error": str(e), "overall": {"winner": "UNKNOWN"}}
    result["evaluation"] = eval_data

    time.sleep(2)

    out_path = RESULTS_DIR / f"{qid}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    topology = result["adversarial_cot"]["topology"]
    winner = eval_data.get("overall", {}).get("winner", "?")
    print(f"  -> CoT topology: {topology} | Evaluator winner: {winner}")

    return result


def print_summary(results: list):
    print("\n" + "=" * 80)
    print("BASELINE COMPARISON SUMMARY")
    print("=" * 80)
    print(f"{'QID':<5} {'CoT Topology':<14} {'Steps OK':<10} "
          f"{'Dir.Comm':<10} {'Contr.D':<9} {'Synth.Q':<9} {'Novel':<8} {'Overall'}")
    print("-" * 80)

    wins = {"A": 0, "B": 0, "EQUAL": 0}
    topology_counts: dict[str, int] = {}

    for r in results:
        qid = r["qid"]
        cot = r["adversarial_cot"]
        ev = r.get("evaluation", {})
        topology = cot["topology"]
        topology_counts[topology] = topology_counts.get(topology, 0) + 1
        steps_ok = "YES" if cot["parsed"].get("steps_complete") else "NO"

        def w(dim): return ev.get(dim, {}).get("winner", "?")
        overall = ev.get("overall", {}).get("winner", "?")
        if overall in wins:
            wins[overall] += 1

        print(f"{qid:<5} {topology:<14} {steps_ok:<10} "
              f"{w('directional_commitment'):<10} {w('contradiction_depth'):<9} "
              f"{w('synthesis_quality'):<9} {w('epistemic_novelty'):<8} {overall}")

    print("-" * 80)
    print(f"\nEvaluator verdicts: DES wins={wins['A']}, CoT wins={wins['B']}, "
          f"Equal={wins.get('EQUAL', 0)}")
    print(f"CoT topology distribution: {topology_counts}")

    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("# DES vs Adversarial CoT — Baseline Comparison\n\n")
        f.write(f"**Model:** {MODEL}  \n")
        f.write(f"**Questions:** 13  \n\n")
        f.write("## Evaluator Verdicts\n\n")
        f.write(f"- DES (Output A) wins: {wins['A']}/13\n")
        f.write(f"- CoT (Output B) wins: {wins['B']}/13\n")
        f.write(f"- Equal: {wins.get('EQUAL', 0)}/13\n\n")
        f.write("## CoT Topology Distribution\n\n")
        for topo, count in sorted(topology_counts.items()):
            f.write(f"- {topo}: {count}/13\n")
        f.write("\n## Per-Question Results\n\n")
        f.write("| QID | CoT Topology | Steps OK | Dir.Comm | Contr.D | Synth.Q | Novel | Overall |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in results:
            qid = r["qid"]
            topo = r["adversarial_cot"]["topology"]
            steps = "YES" if r["adversarial_cot"]["parsed"].get("steps_complete") else "NO"
            ev = r.get("evaluation", {})
            def w(dim): return ev.get(dim, {}).get("winner", "?")
            winner = ev.get("overall", {}).get("winner", "?")
            f.write(f"| {qid} | {topo} | {steps} | {w('directional_commitment')} | "
                    f"{w('contradiction_depth')} | {w('synthesis_quality')} | "
                    f"{w('epistemic_novelty')} | {winner} |\n")
        f.write("\n## Per-Question Justifications\n\n")
        for r in results:
            qid = r["qid"]
            ev = r.get("evaluation", {})
            f.write(f"### {qid}: {r['question']}\n\n")
            for dim in ("directional_commitment", "contradiction_depth",
                        "synthesis_quality", "epistemic_novelty"):
                d = ev.get(dim, {})
                f.write(f"- **{dim.replace('_',' ').title()}**: {d.get('winner','?')} — "
                        f"{d.get('reason', '')}\n")
            overall = ev.get("overall", {})
            f.write(f"- **Overall**: {overall.get('winner','?')} — "
                    f"{overall.get('justification','')}\n\n")


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

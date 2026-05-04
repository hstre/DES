"""
Multi-model jury evaluation. Run dry_run_check.py first.
Pre-registered: DES = DS4_GPT4o, NO fallback.
"""
import json, time, hashlib, random, os, glob
from pathlib import Path
from openai import OpenAI

ds4 = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
             base_url="https://api.deepseek.com/v1")
openrouter = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://github.com/hstre/DES",
                        "X-Title": "DES Jury Evaluation"
                    })

JUDGES = [
    ("deepseek-chat",                   ds4),
    ("openai/gpt-4o",                   openrouter),
    ("anthropic/claude-sonnet-4-5",     openrouter),
    ("google/gemini-2.0-flash-001",      openrouter),
]

COT_GENERATORS = [
    ("CoT-DS4",   "deepseek-chat",       ds4),
    ("CoT-GPT4o", "openai/gpt-4o",       openrouter),
]

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

RESULTS_DIR = Path("batch_results_jury")
RAW_DIR = RESULTS_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

cost_log = {}


ADVERSARIAL_COT_PROMPT = """You are conducting adversarial epistemic analysis.

Research question: {question}

STEP 1 — INITIAL CLAIM:
State a clear, directional claim. Format: "Claim: [X]" Confidence: [0.0-1.0]

STEP 2 — FALSIFICATION:
Find the strongest possible objection. Do not hedge. Commit to a direction.
Format: "Counter-claim: [X]"

STEP 3 — CONTRADICTION CHECK:
Do these directly contradict each other (both cannot be true simultaneously)?
Answer: YES or NO. One sentence explanation.

STEP 4 — SYNTHESIS:
Synthesize into a qualified conclusion with explicit scope conditions.
Format: "Synthesis: [X]" Confidence: [0.0-1.0]

Produce all four steps in sequence."""


JURY_PROMPT = """You are a neutral epistemic evaluator.
You do not know which system produced which output.

Research question: {question}

OUTPUT A:
{output_a}

OUTPUT B:
{output_b}

Evaluate on 8 dimensions plus overall. For each, allocate scores such that
A_score + B_score = 1.0 exactly. Provide a one-sentence reason.

CRITICAL: Do not reward rhetorical polish except under the readability
dimension. For dimensions 2-8, evaluate epistemic structure, contradiction
handling, branch preservation, traceability, and recoverable reasoning
state -- not fluency or narrative elegance.

Dimensions:
1. readability: rhetorical clarity and ease of comprehension
2. directional_commitment: clear directional claims vs. hedged generalities
3. contradiction_depth: fundamental vs. surface contradictions identified
4. synthesis_quality: precision and scope-bounding of synthesis
5. epistemic_novelty: non-obvious tensions a domain expert would value
6. branch_preservation: competing hypotheses maintained in parallel
7. process_traceability: claim history and recoverable reasoning state
8. evidence_scope_discipline: explicit scope conditions and evidence status
9. overall: weighted judgment across all dimensions

Return ONLY valid JSON:
{{
  "readability": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "directional_commitment": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "contradiction_depth": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "synthesis_quality": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "epistemic_novelty": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "branch_preservation": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "process_traceability": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "evidence_scope_discipline": {{"A": 0.XX, "B": 0.XX, "reason": "..."}},
  "overall": {{"A": 0.XX, "B": 0.XX, "reason": "..."}}
}}

Each pair must sum to exactly 1.0."""


def call_with_cost(client, model, prompt, max_tokens=1000):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3
    )
    usage = r.usage
    info = {
        "model": model,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
        "cost_measured": usage is not None
    }
    if model not in cost_log:
        cost_log[model] = {"calls": 0, "total_tokens": 0}
    cost_log[model]["calls"] += 1
    if usage:
        cost_log[model]["total_tokens"] += usage.total_tokens
    return r.choices[0].message.content, info


def load_des_state(qid):
    patterns = [
        f"batch_results_multimodel/*DS4_GPT4o*{qid}*state.json",
        f"batch_results_multimodel/DS4_GPT4o_{qid}_state.json",
        f"batch_results_multimodel/*{qid}*DS4_GPT4o*state.json",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            with open(matches[0]) as f:
                return json.load(f)
    raise FileNotFoundError(
        f"Missing pre-registered DS4_GPT4o state for {qid}. "
        f"Jury run aborted -- no fallback permitted."
    )


def render_des_report(state, question):
    claims = state.get("claims", {})
    op_history = state.get("operation_history", [])
    initial = next((c for cid, c in sorted(claims.items()) if cid == "C001"), None)
    contradicted = [c for c in claims.values()
                   if c.get("status") == "contradicted" or c.get("conflict")]
    branches = [c for c in claims.values() if c.get("id","").startswith("B")]
    syntheses = [c for c in claims.values() if c.get("is_synthesis")]
    supported = [c for c in claims.values()
                if c.get("status") == "supported" and not c.get("is_synthesis")]
    open_claims = [c for c in claims.values() if not c.get("sealed")]

    lines = [f"Research question: {question}", ""]
    if initial:
        lines.append(f"Main claim: {initial.get('subject','')} "
                    f"{initial.get('predicate','')} {initial.get('object','')} "
                    f"(confidence: {initial.get('confidence',0):.2f})")
    lines.append("")
    if contradicted:
        lines.append(f"Contradictions identified ({len(contradicted)}):")
        for c in contradicted:
            lines.append(f"  - {c.get('subject','')} {c.get('predicate','')} "
                        f"{c.get('object','')} [status: {c.get('status','')}]")
    lines.append("")
    if branches:
        lines.append(f"Competing hypotheses maintained in parallel ({len(branches)}):")
        for c in branches:
            lines.append(f"  - {c.get('subject','')} {c.get('predicate','')} "
                        f"{c.get('object','')} "
                        f"[{c.get('status','')}, conf: {c.get('confidence',0):.2f}]")
    lines.append("")
    if supported:
        lines.append(f"Supported claims ({len(supported)}):")
        for c in supported[:4]:
            lines.append(f"  - {c.get('subject','')} {c.get('predicate','')} "
                        f"{c.get('object','')} (conf: {c.get('confidence',0):.2f})")
    lines.append("")
    if syntheses:
        lines.append(f"Synthesis conclusions ({len(syntheses)}):")
        for c in syntheses:
            lines.append(f"  - {c.get('subject','')} {c.get('predicate','')} "
                        f"{c.get('object','')} (conf: {c.get('confidence',0):.2f})")
    lines.append("")
    if open_claims:
        lines.append(f"Unresolved tensions ({len(open_claims)}):")
        for c in open_claims[:3]:
            lines.append(f"  - {c.get('subject','')} {c.get('predicate','')} "
                        f"{c.get('object','')} [status: {c.get('status','')}]")
    lines.append("")
    lines.append(f"Total claims generated: {len(claims)}")
    lines.append(f"Epistemic operations applied: {len(op_history)}")
    return "\n".join(lines)


def get_assignment(judge_model, qid, cot_label):
    seed = int(hashlib.md5(f"{judge_model}{qid}{cot_label}".encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    if rng.random() > 0.5:
        return {"A": "DES", "B": "CoT"}
    return {"A": "CoT", "B": "DES"}


def parse_jury(response):
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:] if lines[-1] != "```" else lines[1:-1])
    data = json.loads(clean)
    for dim, vals in data.items():
        if isinstance(vals, dict) and "A" in vals and "B" in vals:
            total = vals["A"] + vals["B"]
            if total > 0 and abs(total - 1.0) > 0.01:
                data[dim]["A"] = round(vals["A"] / total, 3)
                data[dim]["B"] = round(vals["B"] / total, 3)
    return data


def evaluate_one(qid, question, des_report, cot_output, cot_label,
                 judge_model, judge_client, bias_tracker):
    assignment = get_assignment(judge_model, qid, cot_label)
    output_a = des_report if assignment["A"] == "DES" else cot_output
    output_b = cot_output if assignment["A"] == "DES" else des_report

    prompt = JURY_PROMPT.format(question=question, output_a=output_a, output_b=output_b)
    response, cost_info = call_with_cost(judge_client, judge_model, prompt, max_tokens=1200)

    try:
        data = parse_jury(response)
    except Exception as e:
        return {"error": str(e), "qid": qid, "judge": judge_model,
                "cot": cot_label, "assignment": assignment, "cost": cost_info}

    result = {
        "qid": qid,
        "judge_model": judge_model,
        "des_combo": "DS4_GPT4o",
        "cot_model": cot_label,
        "assignment": assignment,
        "cost": cost_info,
        "dimensions": {}
    }

    DIMS = ["readability","directional_commitment","contradiction_depth",
            "synthesis_quality","epistemic_novelty","branch_preservation",
            "process_traceability","evidence_scope_discipline","overall"]

    for dim in DIMS:
        if dim in data and isinstance(data[dim], dict):
            a_score = data[dim].get("A", 0.5)
            b_score = data[dim].get("B", 0.5)
            des_score = a_score if assignment["A"] == "DES" else b_score
            cot_score = b_score if assignment["A"] == "DES" else a_score
            result["dimensions"][dim] = {
                "DES": round(des_score, 3),
                "CoT": round(cot_score, 3),
                "reason": data[dim].get("reason", "")
            }

    # Position bias tracking -- FIXED
    if "overall" in result["dimensions"]:
        ds = result["dimensions"]["overall"]["DES"]
        cs = result["dimensions"]["overall"]["CoT"]
        key = f"{judge_model}_{cot_label}"
        if key not in bias_tracker:
            bias_tracker[key] = {
                "des_assigned_A": 0, "des_wins_when_A": 0,
                "des_assigned_B": 0, "des_wins_when_B": 0
            }
        if assignment["A"] == "DES":
            bias_tracker[key]["des_assigned_A"] += 1
            if ds > cs:
                bias_tracker[key]["des_wins_when_A"] += 1
        else:
            bias_tracker[key]["des_assigned_B"] += 1
            if ds > cs:
                bias_tracker[key]["des_wins_when_B"] += 1

    return result


def run_all():
    all_results = []
    bias_tracker = {}
    missing_states = []

    # Verify all states upfront
    print("Verifying DS4_GPT4o states...")
    for qid in QUESTIONS:
        try:
            load_des_state(qid)
            print(f"  {qid}: OK")
        except FileNotFoundError as e:
            missing_states.append(qid)
            print(f"  {qid}: MISSING")
    if missing_states:
        raise SystemExit(f"Aborting: missing DS4_GPT4o states for {missing_states}")

    # Generate CoT outputs
    print("\nGenerating CoT outputs...")
    cot_outputs = {}
    for qid, question in QUESTIONS.items():
        cot_outputs[qid] = {}
        for cot_label, cot_model, cot_client in COT_GENERATORS:
            print(f"  {cot_label} / {qid}...")
            output, cost = call_with_cost(
                cot_client, cot_model,
                ADVERSARIAL_COT_PROMPT.format(question=question),
                max_tokens=800
            )
            cot_outputs[qid][cot_label] = output
            time.sleep(1)

    # Load and render DES reports
    print("\nRendering DES reports...")
    des_reports = {}
    for qid, question in QUESTIONS.items():
        state = load_des_state(qid)
        des_reports[qid] = render_des_report(state, question)
        print(f"  {qid}: {len(state.get('claims',{}))} claims")

    # Run jury
    print("\nRunning jury evaluations...")
    for qid, question in QUESTIONS.items():
        for cot_label, _, _ in COT_GENERATORS:
            for judge_model, judge_client in JUDGES:
                safe = judge_model.replace("/","_")
                raw_path = RAW_DIR / f"{qid}_{cot_label}_{safe}.json"
                if raw_path.exists():
                    print(f"  [skip] {qid} | {cot_label} | {safe[:20]}")
                    with open(raw_path) as f:
                        all_results.append(json.load(f))
                    continue
                print(f"  {qid} | {cot_label} | {safe[:20]}...", end=" ", flush=True)
                try:
                    result = evaluate_one(
                        qid, question,
                        des_reports[qid], cot_outputs[qid][cot_label],
                        cot_label, judge_model, judge_client, bias_tracker
                    )
                    all_results.append(result)
                    overall = result.get("dimensions",{}).get("overall",{})
                    ds = overall.get('DES', '?')
                    cs = overall.get('CoT', '?')
                    print(f"DES={ds:.2f} CoT={cs:.2f}" if isinstance(ds, float) else f"ERROR")
                    with open(raw_path, "w") as f:
                        json.dump(result, f, indent=2)
                    time.sleep(1.5)
                except Exception as e:
                    print(f"ERROR: {e}")
                    time.sleep(2)

    # Save cost log
    with open(RESULTS_DIR / "cost_log.json", "w") as f:
        json.dump(cost_log, f, indent=2)
    print("\nCost log:")
    for model, info in cost_log.items():
        print(f"  {model}: {info['calls']} calls, {info['total_tokens']} tokens")

    # Save bias tracker
    with open(RESULTS_DIR / "bias_tracker.json", "w") as f:
        json.dump(bias_tracker, f, indent=2)

    save_summary(all_results, bias_tracker, missing_states)
    return all_results


def save_summary(results, bias_tracker, missing_states):
    valid = [r for r in results if "dimensions" in r and "error" not in r]
    DIMS = ["readability","directional_commitment","contradiction_depth",
            "synthesis_quality","epistemic_novelty","branch_preservation",
            "process_traceability","evidence_scope_discipline","overall"]

    def avg(lst): return round(sum(lst)/len(lst), 3) if lst else 0.0

    dim_scores = {d: {"DES":[], "CoT":[]} for d in DIMS}
    judge_scores = {}
    cot_scores = {}

    for r in valid:
        judge = r["judge_model"]
        cot = r["cot_model"]
        if judge not in judge_scores:
            judge_scores[judge] = {d: {"DES":[], "CoT":[]} for d in DIMS}
        if cot not in cot_scores:
            cot_scores[cot] = {d: {"DES":[], "CoT":[]} for d in DIMS}
        for dim in DIMS:
            if dim in r.get("dimensions", {}):
                ds = r["dimensions"][dim]["DES"]
                cs = r["dimensions"][dim]["CoT"]
                dim_scores[dim]["DES"].append(ds)
                dim_scores[dim]["CoT"].append(cs)
                judge_scores[judge][dim]["DES"].append(ds)
                judge_scores[judge][dim]["CoT"].append(cs)  # FIXED: was ds in v1
                cot_scores[cot][dim]["DES"].append(ds)
                cot_scores[cot][dim]["CoT"].append(cs)

    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("# DES vs. Adversarial CoT — Multi-Model Jury Evaluation\n\n")
        f.write(f"**DES condition:** DS4_GPT4o (pre-registered, no fallback)\n")
        f.write(f"**Missing DS4_GPT4o states:** {len(missing_states)}/13\n")
        f.write(f"**Fallbacks used:** 0\n")
        f.write(f"**Valid evaluations:** {len(valid)}/104\n\n")

        f.write("## A. Average Scores by Dimension\n\n")
        f.write("| Dimension | DES | CoT | Winner |\n|---|---|---|---|\n")
        for dim in DIMS:
            ds = avg(dim_scores[dim]["DES"])
            cs = avg(dim_scores[dim]["CoT"])
            w = "DES" if ds > cs+0.03 else ("CoT" if cs > ds+0.03 else "EQUAL")
            f.write(f"| {dim} | {ds} | {cs} | {w} |\n")

        f.write("\n## B. Scores by Judge Model\n\n")
        f.write("| Judge | Readability | Novelty | Branch | Traceability | Overall |\n")
        f.write("|---|---|---|---|---|---|\n")
        for judge, scores in judge_scores.items():
            row = [judge[:30]]
            for dim in ["readability","epistemic_novelty",
                       "branch_preservation","process_traceability","overall"]:
                ds = avg(scores[dim]["DES"])
                cs = avg(scores[dim]["CoT"])
                row.append(f"DES={ds}/CoT={cs}")
            f.write("| " + " | ".join(row) + " |\n")

        f.write("\n## C. Position Bias Check\n\n")
        for key, b in bias_tracker.items():
            total_a = b["des_assigned_A"]
            total_b = b["des_assigned_B"]
            wins_a = b["des_wins_when_A"]
            wins_b = b["des_wins_when_B"]
            rate_a = wins_a/total_a if total_a else 0
            rate_b = wins_b/total_b if total_b else 0
            bias_detected = abs(rate_a - rate_b) > 0.2
            f.write(f"**{key}:** DES as A: {wins_a}/{total_a} ({rate_a:.2f}) | "
                   f"DES as B: {wins_b}/{total_b} ({rate_b:.2f}) | "
                   f"Bias: {'DETECTED' if bias_detected else 'not detected'}\n\n")

        f.write("\n## D. Per-Question Overview\n\n")
        f.write("| QID | Overall DES | Overall CoT | DES stronger dims |\n|---|---|---|---|\n")
        for qid in QUESTIONS:
            qr = [r for r in valid if r["qid"] == qid]
            if not qr: continue
            od = avg([r["dimensions"].get("overall",{}).get("DES",0.5) for r in qr])
            oc = avg([r["dimensions"].get("overall",{}).get("CoT",0.5) for r in qr])
            stronger = [d for d in DIMS
                       if avg([r["dimensions"].get(d,{}).get("DES",0.5) for r in qr]) > 0.55]
            f.write(f"| {qid} | {od} | {oc} | {', '.join(stronger[:3])} |\n")

        f.write("\n## E. CoT Generator Comparison\n\n")
        f.write("| CoT Model | Overall DES | Overall CoT |\n|---|---|---|\n")
        for cot_label, scores in cot_scores.items():
            ds = avg(scores["overall"]["DES"])
            cs = avg(scores["overall"]["CoT"])
            f.write(f"| {cot_label} | {ds} | {cs} |\n")

    with open(RESULTS_DIR / "results.json", "w") as f:
        json.dump({
            "valid": len(valid),
            "missing_states": missing_states,
            "fallbacks": 0,
            "dimension_averages": {d: {"DES": avg(dim_scores[d]["DES"]),
                                       "CoT": avg(dim_scores[d]["CoT"])}
                                  for d in DIMS},
            "by_judge": {j: {d: {"DES": avg(s[d]["DES"]), "CoT": avg(s[d]["CoT"])}
                             for d in DIMS}
                        for j, s in judge_scores.items()},
            "by_cot": {c: {d: {"DES": avg(s[d]["DES"]), "CoT": avg(s[d]["CoT"])}
                          for d in DIMS}
                      for c, s in cot_scores.items()},
            "bias_tracker": bias_tracker,
        }, f, indent=2)

    print(f"\nSummary: {RESULTS_DIR}/summary.md")


if __name__ == "__main__":
    run_all()

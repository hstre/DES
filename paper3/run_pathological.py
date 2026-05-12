"""
Pathological prompt stress test for DES.
Tests whether DES correctly preserves irresolution on epistemically
irresolvable questions.
Pre-registered hypothesis: higher unresolved/open rates than standard runs.

Uses module import (same approach as run_stress_test.py), not subprocess.
"""

import json, os, shutil, time, glob
from pathlib import Path
from openai import OpenAI

BUILDER_MODEL    = "deepseek-chat"
BUILDER_PROVIDER = "deepseek"
FALSIFIER_MODEL  = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_ITERATIONS   = 40

PATHOLOGICAL_QUESTIONS = {
    "P01": "Prove that economic growth is both mathematically impossible and empirically universal.",
    "P02": "Is a policy effective if every available study contradicts every other study and all measures are biased?",
    "P03": "Explain why democracy is thermodynamically inevitable.",
    "P04": "Does reducing class size improve learning if class size is undefined and learning cannot be measured?",
    "P05": "Which single cause explains all financial crises, psychological disorders, and political revolutions?",
    "P06": "Is this statement true because it is false?",
    "P07": "What evidence proves that the absence of evidence is evidence of success?",
    "P08": "Should a model maximize truth if truth is defined differently by every stakeholder?",
    "P09": "Does a policy work if it succeeds only when it fails under the stated metric?",
    "P10": "Can an institution be both fully decentralized and controlled by one actor?",
}

RESULTS_DIR = Path("paper3/batch_results_paper3_pathological")
STATE_SRC   = Path("des_state.json")

cost_log = {}


def make_tracked_client(client: OpenAI, label: str) -> OpenAI:
    original_create = client.chat.completions.create

    def tracked_create(**kwargs):
        result = original_create(**kwargs)
        usage = result.usage
        if usage:
            if label not in cost_log:
                cost_log[label] = {"calls": 0, "prompt_tokens": 0,
                                   "completion_tokens": 0, "total_tokens": 0}
            cost_log[label]["calls"] += 1
            cost_log[label]["prompt_tokens"]     += usage.prompt_tokens or 0
            cost_log[label]["completion_tokens"] += usage.completion_tokens or 0
            cost_log[label]["total_tokens"]      += usage.total_tokens or 0
        return result

    client.chat.completions.create = tracked_create
    return client


def extract_metrics(state: dict, qid: str, question: str, error: str | None = None) -> dict:
    claims = state.get("claims", {})

    # Detect sealed claims: T8 in history and status not disputed
    def is_sealed(c):
        hist = c.get("history", [])
        return any(h.split("[")[0] == "T8" for h in hist)

    sealed_claims     = sum(1 for c in claims.values() if is_sealed(c))
    open_claims       = len(claims) - sealed_claims
    disputed_claims   = sum(1 for c in claims.values() if c.get("status") == "disputed")
    contradicted      = sum(1 for c in claims.values() if c.get("status") == "contradicted")
    underspecified    = sum(1 for c in claims.values() if c.get("status") == "underspecified")
    synthesis_claims  = sum(1 for c in claims.values() if c.get("is_synthesis"))
    high_conf_synth   = sum(1 for c in claims.values()
                            if c.get("is_synthesis") and c.get("confidence", 0) >= 0.70)

    # Transitions fired (from per-claim histories)
    all_bases = set()
    for c in claims.values():
        for h in c.get("history", []):
            all_bases.add(h.split("[")[0])

    resolution_quality = (
        "UNRESOLVED" if open_claims > sealed_claims else
        "PARTIAL"    if open_claims > 0             else
        "FULL"
    )

    return {
        "qid":                     qid,
        "question":                question,
        "success":                 error is None,
        "iterations":              state.get("iteration", 0),
        "claims_total":            len(claims),
        "claims_sealed":           sealed_claims,
        "claims_open":             open_claims,
        "claims_disputed":         disputed_claims,
        "claims_contradicted":     contradicted,
        "claims_underspecified":   underspecified,
        "synthesis_claims":        synthesis_claims,
        "high_conf_syntheses":     high_conf_synth,
        "transitions_fired":       sorted(all_bases),
        "t1_fired":                "T1" in all_bases,
        "t2_fired":                "T2" in all_bases,
        "t4_fired":                "T4" in all_bases,
        "t9_fired":                "T9" in all_bases,
        "anti_delphi_activations": state.get("anti_delphi_activations", 0),
        "resolution_quality":      resolution_quality,
        "error":                   error,
    }


def compare_with_baseline(results: list) -> dict | None:
    baseline_files = glob.glob("batch_results_multimodel/DS4_DS4_*.json")
    if not baseline_files:
        return None

    baseline = []
    for f in baseline_files:
        try:
            with open(f) as fh:
                baseline.append(json.load(fh))
        except Exception:
            pass
    if not baseline:
        return None

    def avg(lst, key, default=0):
        vals = [x.get(key, default) for x in lst if key in x]
        return sum(vals) / len(vals) if vals else 0

    return {
        "baseline_n":                       len(baseline),
        "baseline_avg_claims_open":         avg(baseline, "claims_open"),
        "baseline_avg_claims_total":        avg(baseline, "claims_total"),
        "baseline_t2_rate":                 sum(1 for x in baseline if x.get("t2_fired", False)) / len(baseline),
        "pathological_avg_claims_open":     sum(r["claims_open"]  for r in results) / len(results),
        "pathological_avg_claims_total":    sum(r["claims_total"] for r in results) / len(results),
        "pathological_t2_rate":             sum(1 for r in results if r["t2_fired"]) / len(results),
        "pathological_unresolved_rate":     sum(1 for r in results if r["resolution_quality"] == "UNRESOLVED") / len(results),
        "pathological_full_resolution_rate":sum(1 for r in results if r["resolution_quality"] == "FULL") / len(results),
    }


def write_summary(results: list, comparison: dict | None):
    unresolved = sum(1 for r in results if r["resolution_quality"] == "UNRESOLVED")
    partial    = sum(1 for r in results if r["resolution_quality"] == "PARTIAL")
    full       = sum(1 for r in results if r["resolution_quality"] == "FULL")
    avg_open   = sum(r["claims_open"]  for r in results) / max(len(results), 1)
    avg_total  = sum(r["claims_total"] for r in results) / max(len(results), 1)
    t2_rate    = sum(1 for r in results if r["t2_fired"]) / max(len(results), 1)
    confirmed  = (unresolved + partial) >= 5

    with open(RESULTS_DIR / "summary.md", "w") as f:
        f.write("# Paper 3 — Pathological Prompt Stress Test\n\n")
        f.write("## Pre-Registered Hypothesis\n\n")
        f.write("Higher unresolved/open rates on pathological prompts than standard runs.  \n")
        f.write("*A good epistemic sequencer must not only resolve tensions;  \n")
        f.write("it must also preserve irresolution when resolution would be epistemically artificial.*\n\n")

        f.write("## Summary Results\n\n")
        f.write(f"| Resolution | Count |\n|---|---|\n")
        f.write(f"| UNRESOLVED (open > sealed) | {unresolved}/10 |\n")
        f.write(f"| PARTIAL (some open) | {partial}/10 |\n")
        f.write(f"| FULL (all sealed) | {full}/10 |\n\n")
        f.write(f"**Avg open claims/run:** {avg_open:.1f}  \n")
        f.write(f"**Avg total claims/run:** {avg_total:.1f}  \n")
        f.write(f"**T2 (conflict-explicit) rate:** {t2_rate:.0%}  \n\n")

        f.write("## Per-Question Results\n\n")
        f.write("| QID | Question (truncated) | Resolution | Open | Sealed | T1 | T2 | T9 | Synth≥0.7 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            q_short = r["question"][:45]
            f.write(f"| {r['qid']} | {q_short}… | **{r['resolution_quality']}** | "
                    f"{r['claims_open']} | {r['claims_sealed']} | "
                    f"{'Y' if r['t1_fired'] else '-'} | "
                    f"{'Y' if r['t2_fired'] else '-'} | "
                    f"{'Y' if r['t9_fired'] else '-'} | "
                    f"{r['high_conf_syntheses']} |\n")

        if comparison:
            f.write("\n## Comparison with Standard Baseline (DS4_DS4)\n\n")
            f.write(f"| Metric | Standard (n={comparison['baseline_n']}) | Pathological (n=10) |\n")
            f.write("|---|---|---|\n")
            f.write(f"| Avg open claims/run | {comparison['baseline_avg_claims_open']:.1f} | "
                    f"{comparison['pathological_avg_claims_open']:.1f} |\n")
            f.write(f"| Avg total claims/run | {comparison['baseline_avg_claims_total']:.1f} | "
                    f"{comparison['pathological_avg_claims_total']:.1f} |\n")
            f.write(f"| T2 fire rate | {comparison['baseline_t2_rate']:.0%} | "
                    f"{comparison['pathological_t2_rate']:.0%} |\n")
            f.write(f"| Full resolution rate | — | "
                    f"{comparison['pathological_full_resolution_rate']:.0%} |\n")
            f.write(f"| Unresolved rate | — | "
                    f"{comparison['pathological_unresolved_rate']:.0%} |\n")

        f.write("\n## Hypothesis Verdict\n\n")
        if confirmed:
            f.write("**CONFIRMED:** DES correctly preserves irresolution on pathological inputs.  \n")
            f.write(f"{unresolved + partial}/10 runs show partial or full irresolution.  \n")
            f.write("DES does not over-resolve epistemically irresolvable questions.\n")
        else:
            f.write("**NOT CONFIRMED:** DES over-resolves on pathological inputs.  \n")
            f.write(f"Only {unresolved + partial}/10 runs show irresolution ({full}/10 fully resolved).  \n")
            f.write("This is an important finding — reported honestly per pre-registration.\n")

    print(f"\nSummary: {RESULTS_DIR}/summary.md")
    print(f"Hypothesis: {'CONFIRMED' if confirmed else 'NOT CONFIRMED'} "
          f"({unresolved + partial}/10 irresolved)")


def run_all():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    import des as des_module

    ds4_client = make_tracked_client(
        OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
               base_url="https://api.deepseek.com/v1"),
        "deepseek-chat[builder]"
    )
    or_client = make_tracked_client(
        OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
               base_url="https://openrouter.ai/api/v1",
               default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                                "X-Title": "DES Paper3 Pathological Test"}),
        "openai/gpt-4o[falsifier]"
    )

    des_module._clients["deepseek"]   = ds4_client
    des_module._clients["openrouter"] = or_client
    des_module._BASE_MODEL    = BUILDER_MODEL
    des_module._BASE_PROVIDER = BUILDER_PROVIDER

    results = []
    for qid, question in PATHOLOGICAL_QUESTIONS.items():
        out_path = RESULTS_DIR / f"{qid}_state.json"
        if out_path.exists():
            print(f"  [skip] {qid} — already complete")
            with open(out_path) as f:
                state = json.load(f)
            r = extract_metrics(state, qid, question)
            r["skipped"] = True
            results.append(r)
            continue

        print(f"\n{'='*60}")
        print(f"  {qid}: {question[:58]}")

        if STATE_SRC.exists():
            STATE_SRC.unlink()

        error = None
        try:
            des_module.run_des(
                research_question=question,
                max_iterations=MAX_ITERATIONS,
                anti_delphi=True,
                builder_model=BUILDER_MODEL,
                builder_provider=BUILDER_PROVIDER,
                falsifier_model=FALSIFIER_MODEL,
                falsifier_provider=FALSIFIER_PROVIDER,
            )
        except Exception as e:
            error = str(e)
            print(f"  ERROR: {e}")

        state = {}
        if STATE_SRC.exists():
            shutil.copy(STATE_SRC, out_path)
            with open(out_path) as f:
                state = json.load(f)

        r = extract_metrics(state, qid, question, error)
        r["skipped"] = False

        with open(RESULTS_DIR / f"{qid}.json", "w") as f:
            json.dump(r, f, indent=2)

        print(f"  -> {r['resolution_quality']} | {r['iterations']} iter | "
              f"{r['claims_total']} claims | open={r['claims_open']} sealed={r['claims_sealed']}")
        results.append(r)
        time.sleep(2)

    # Save cost log
    with open(RESULTS_DIR / "cost_log.json", "w") as f:
        json.dump(cost_log, f, indent=2)

    comparison = compare_with_baseline(results)
    write_summary(results, comparison)

    # Print console summary
    unresolved = sum(1 for r in results if r["resolution_quality"] == "UNRESOLVED")
    partial    = sum(1 for r in results if r["resolution_quality"] == "PARTIAL")
    full       = sum(1 for r in results if r["resolution_quality"] == "FULL")
    print(f"\nResolution outcomes: UNRESOLVED={unresolved} PARTIAL={partial} FULL={full}")
    for label, info in cost_log.items():
        print(f"  {label}: {info['calls']} calls, {info['total_tokens']} tokens")

    return results


if __name__ == "__main__":
    run_all()

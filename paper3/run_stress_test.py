"""
Stress-test runner for Paper 3.
15 cross-domain questions (S01-S15). DS4_GPT4o + Anti-Delphi, max 40 iterations.
Pre-registered config: no DS4_DS4 fallback permitted.
Run dry_run_check.py first, then this script.
"""

import json, os, shutil, sys, time
from pathlib import Path
from openai import OpenAI

# ── CONFIG ────────────────────────────────────────────────────────────────────

BUILDER_MODEL    = "deepseek-chat"
BUILDER_PROVIDER = "deepseek"
FALSIFIER_MODEL  = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_ITERATIONS   = 40

STRESS_QUESTIONS = {
    "S01": "What would a thermodynamicist conclude about the long-run efficiency of democracy?",
    "S02": "Apply the logic of evolutionary selection pressure to the survival of academic journals.",
    "S03": "What does the concept of phase transitions in physics imply about financial market crashes?",
    "S04": "Is language itself a form of lossy compression, and what does that imply for legal contracts?",
    "S05": "What would a Martian economist conclude about the rationality of human housing markets?",
    "S06": "Apply network topology theory to the spread of scientific consensus.",
    "S07": "Is the immune system a better model for organizational resilience than military hierarchy?",
    "S08": "What does information theory imply about the epistemic limits of democracy?",
    "S09": "Apply the concept of entropy to the long-run stability of political institutions.",
    "S10": "Is urban traffic flow governed by the same dynamics as neural signal propagation?",
    "S11": "What would a materials scientist conclude about the brittleness of financial derivatives?",
    "S12": "Apply predator-prey dynamics to the relationship between startups and incumbent firms.",
    "S13": "Is the replication crisis in psychology better explained by ecology than by statistics?",
    "S14": "What does quantum measurement theory imply about the act of polling in elections?",
    "S15": "Apply the logic of trophic cascades to the effects of removing a dominant tech platform.",
}

OUT_DIR   = Path("paper3/batch_results_paper3_stress")
STATE_SRC = Path("des_state.json")

cost_log = {}

# ── COST-TRACKING WRAPPER ─────────────────────────────────────────────────────

def make_tracked_client(client: OpenAI, label: str) -> OpenAI:
    """Wrap client.chat.completions.create to accumulate token usage."""
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

# ── PRE-RUN CHECKS ────────────────────────────────────────────────────────────

def pre_run_checks():
    print("Pre-run checks...")
    ok = True

    # CHECK 1: DS4 (builder) reachable
    try:
        ds4 = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                     base_url="https://api.deepseek.com/v1")
        ds4.chat.completions.create(
            model=BUILDER_MODEL,
            messages=[{"role":"user","content":"ping"}],
            max_tokens=5
        )
        print(f"  [OK] DeepSeek ({BUILDER_MODEL}) reachable")
    except Exception as e:
        print(f"  [FAIL] DeepSeek: {e}")
        ok = False

    # CHECK 2: OpenRouter/GPT-4o (falsifier) reachable
    try:
        or_client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                             "X-Title": "DES Paper3 Stress Test"}
        )
        or_client.chat.completions.create(
            model=FALSIFIER_MODEL,
            messages=[{"role":"user","content":"ping"}],
            max_tokens=5
        )
        print(f"  [OK] OpenRouter ({FALSIFIER_MODEL}) reachable")
    except Exception as e:
        print(f"  [FAIL] OpenRouter: {e}")
        ok = False

    # CHECK 3: No DS4_DS4 fallback — confirm falsifier is not deepseek-chat
    if FALSIFIER_MODEL == "deepseek-chat" and FALSIFIER_PROVIDER == "deepseek":
        print(f"  [FAIL] Falsifier is DS4 — DS4_DS4 fallback not permitted")
        ok = False
    else:
        print(f"  [OK] No DS4_DS4 fallback (falsifier={FALSIFIER_MODEL})")

    # CHECK 4: Stress results dir is empty (fresh run)
    if OUT_DIR.exists() and any(OUT_DIR.glob("*state.json")):
        existing = list(OUT_DIR.glob("*state.json"))
        print(f"  [WARN] {len(existing)} state files already exist — will skip completed runs")
    else:
        print(f"  [OK] Stress results dir is empty or absent")

    if not ok:
        raise SystemExit("Pre-run checks failed. Fix issues before running stress test.")

    print()

# ── MAIN ──────────────────────────────────────────────────────────────────────

def run_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pre_run_checks()

    # Import des and inject tracked clients
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
                                "X-Title": "DES Paper3 Stress Test"}),
        "openai/gpt-4o[falsifier]"
    )

    # Inject tracked clients into des module's cache
    des_module._clients["deepseek"]    = ds4_client
    des_module._clients["openrouter"]  = or_client
    des_module._BASE_MODEL    = BUILDER_MODEL
    des_module._BASE_PROVIDER = BUILDER_PROVIDER

    results = []
    for qid, question in STRESS_QUESTIONS.items():
        out_path = OUT_DIR / f"{qid}_state.json"
        if out_path.exists():
            print(f"  [skip] {qid} — already complete")
            with open(out_path) as f:
                state = json.load(f)
            results.append({"qid": qid, "question": question,
                            "claims": len(state.get("claims", {})),
                            "iterations": state.get("iteration", 0),
                            "ad_activations": state.get("anti_delphi_activations", 0),
                            "skipped": True})
            continue

        print(f"\n{'='*60}")
        print(f"  {qid}: {question[:60]}")

        # Clean prior state
        if STATE_SRC.exists():
            STATE_SRC.unlink()

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
            print(f"  ERROR on {qid}: {e}")
            results.append({"qid": qid, "error": str(e)})
            time.sleep(2)
            continue

        # Copy state file
        if STATE_SRC.exists():
            shutil.copy(STATE_SRC, out_path)
            with open(out_path) as f:
                state = json.load(f)
            n_claims = len(state.get("claims", {}))
            n_iter   = state.get("iteration", 0)
            n_ad     = state.get("anti_delphi_activations", 0)
            print(f"  -> {qid}: {n_claims} claims, {n_iter} iter, {n_ad} AD activations")
            results.append({"qid": qid, "question": question,
                            "claims": n_claims, "iterations": n_iter,
                            "ad_activations": n_ad, "skipped": False})
        else:
            print(f"  ERROR: no state file written for {qid}")
            results.append({"qid": qid, "error": "no state file"})

        time.sleep(2)

    # Save cost log
    with open(OUT_DIR / "cost_log.json", "w") as f:
        json.dump(cost_log, f, indent=2)
    print("\nCost log:")
    for label, info in cost_log.items():
        print(f"  {label}: {info['calls']} calls, {info['total_tokens']} tokens")

    # Save summary
    save_summary(results)
    return results


def save_summary(results):
    ok = [r for r in results if "error" not in r]
    total_claims = sum(r.get("claims", 0) for r in ok)
    total_ad     = sum(r.get("ad_activations", 0) for r in ok)
    avg_claims   = round(total_claims / max(len(ok), 1), 1)
    avg_iter     = round(sum(r.get("iterations", 0) for r in ok) / max(len(ok), 1), 1)
    avg_ad       = round(total_ad / max(len(ok), 1), 1)

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("# Paper 3 — Stress-Test Runs\n\n")
        f.write(f"**Builder:** {BUILDER_MODEL} (DeepSeek)  \n")
        f.write(f"**Falsifier:** {FALSIFIER_MODEL} (OpenRouter)  \n")
        f.write(f"**Mode:** Anti-Delphi  \n")
        f.write(f"**Max iterations:** {MAX_ITERATIONS}  \n")
        f.write(f"**DS4_DS4 fallback:** none  \n\n")
        f.write(f"## Run Results\n\n")
        f.write(f"| QID | Claims | Iterations | AD activations | Status |\n")
        f.write(f"|---|---|---|---|---|\n")
        for r in results:
            if "error" in r:
                f.write(f"| {r['qid']} | — | — | — | ERROR: {r['error']} |\n")
            else:
                status = "skip" if r.get("skipped") else "OK"
                f.write(f"| {r['qid']} | {r['claims']} | {r['iterations']} | "
                        f"{r['ad_activations']} | {status} |\n")
        f.write(f"\n**Success rate:** {len(ok)}/{len(results)}  \n")
        f.write(f"**Avg claims/run:** {avg_claims}  \n")
        f.write(f"**Avg iterations/run:** {avg_iter}  \n")
        f.write(f"**Avg AD activations/run:** {avg_ad}  \n\n")
        f.write("## Cost Log\n\n")
        f.write("| Model | Calls | Total tokens |\n|---|---|---|\n")
        for label, info in cost_log.items():
            f.write(f"| {label} | {info['calls']} | {info['total_tokens']} |\n")

    print(f"\nSummary: {OUT_DIR}/summary.md")
    print(f"Success: {len(ok)}/{len(results)} | avg claims={avg_claims} | avg iter={avg_iter}")


if __name__ == "__main__":
    run_all()

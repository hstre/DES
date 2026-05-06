"""
paper7/run_p7.py
Paper 7: EN + EHL runner.
Runs one domain under one experimental condition.
Usage:
    python paper7/run_p7.py --domain N03 --condition EN_persona
    python paper7/run_p7.py --domain N03 --condition EHL_0.90
    python paper7/run_p7.py --all
WP2 (Rentschler 2026).
"""

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from openai import OpenAI

from paper5.spl_wrapper import compute_claim_metrics
from paper6.compute_sh import compute_semantic_headroom
from paper7.ehl import EpistemicHalfLife
from paper7.en import (
    early_saturation_detected,
    generate_en_candidates,
    select_best_en,
    sh_schedule,
    SH_STAR,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 50
MAX_ITER_PER_RUN   = 40
MAX_T10            = 2

RESULTS_DIR = Path("paper7/batch_results_paper7")
STATE_SRC   = Path("des_state.json")

EXPERIMENTAL_CONDITIONS = {
    "P4_baseline":    {"en": None,        "ehl": 1.00},
    "EN_temperature": {"en": "temp",      "ehl": 1.00},
    "EN_persona":     {"en": "persona",   "ehl": 1.00},
    "EN_adjacent":    {"en": "adjacent",  "ehl": 1.00},
    "EHL_0.90":       {"en": None,        "ehl": 0.90},
    "EHL_0.50":       {"en": None,        "ehl": 0.50},   # stress test
    "SH_scheduled":   {"en": "sh_select", "ehl": "sh_select"},  # exploratory
}

# Domains: Paper 6 high-SH cases + Paper 4/5 baselines + new domains
DOMAINS = {
    # Paper 6 confirmed high-SH
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "sh_loop0": 0.1065, "p4_depth": 4, "source": "paper6_high_sh",
    },
    "N05": {
        "seed": "Does economic inequality harm social cohesion?",
        "sh_loop0": 0.0941, "p4_depth": 3, "source": "paper6_high_sh",
    },
    # Paper 4/5 baseline domains
    "R01": {
        "seed": "Does social media use increase rates of depression among adolescents?",
        "sh_loop0": None, "p4_depth": None, "source": "paper45_baseline",
    },
    "R02": {
        "seed": "Is universal basic income economically sustainable at national scale?",
        "sh_loop0": None, "p4_depth": None, "source": "paper45_baseline",
    },
    "R03": {
        "seed": "Does charter school expansion improve educational outcomes?",
        "sh_loop0": None, "p4_depth": None, "source": "paper45_baseline",
    },
    "R04": {
        "seed": "Is nuclear energy necessary for achieving net-zero carbon emissions by 2050?",
        "sh_loop0": None, "p4_depth": None, "source": "paper45_baseline",
    },
    "R05": {
        "seed": "Does mindfulness meditation have durable effects on anxiety and depression?",
        "sh_loop0": None, "p4_depth": None, "source": "paper45_baseline",
    },
    # New domains spanning SH range
    "M01": {
        "seed": ("Investigate the long-term behavior of the recursive map T(n): "
                 "if n mod 3 == 0 then T(n) = n/3, "
                 "if n mod 3 == 1 then T(n) = 4n+2, "
                 "if n mod 3 == 2 then T(n) = 2n-1. "
                 "Identify cycles, divergence patterns, invariants, and plausible conjectures."),
        "sh_loop0": None, "p4_depth": None, "source": "paper7_math_probe",
    },
    "M02": {
        "seed": "Is antibiotic resistance an existential threat to modern medicine?",
        "sh_loop0": None, "p4_depth": None, "source": "paper7_new",
    },
    "M03": {
        "seed": "Does urban density reduce per-capita carbon emissions?",
        "sh_loop0": None, "p4_depth": None, "source": "paper7_new",
    },
    "M04": {
        "seed": "Can large language models develop genuine causal reasoning?",
        "sh_loop0": None, "p4_depth": None, "source": "paper7_new",
    },
    "M05": {
        "seed": "Does immigration increase or decrease wages for native workers?",
        "sh_loop0": None, "p4_depth": None, "source": "paper7_new",
    },
}

# ---------------------------------------------------------------------------
# Global client state (set in _make_clients)
# ---------------------------------------------------------------------------

des_module  = None
or_client_g = None


def _make_clients():
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError("DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set.")
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/hstre/DES",
            "X-Title": "DES Paper7",
        },
    )
    return ds4, orr


def _init_clients():
    global des_module, or_client_g
    import des as des_module_local
    ds4, orr = _make_clients()
    des_module_local._clients["deepseek"]   = ds4
    des_module_local._clients["openrouter"] = orr
    des_module_local._BASE_MODEL    = BUILDER_MODEL
    des_module_local._BASE_PROVIDER = BUILDER_PROVIDER
    des_module  = des_module_local
    or_client_g = orr


def call_llm(prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=min(temperature, 2.0),
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


# ---------------------------------------------------------------------------
# Metrics helpers (reused from paper5/paper6 pattern)
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for","and","or",
            "but","not","with","by","from","that","this","it","be","as","at","on",
            "if","its","so","do","can","will","how","what","why","does","when","where"}
    return set(re.sub(r"[^a-z0-9 ]", "", text.lower()).split()) - STOP


def _claim_text(c: dict) -> str:
    return f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}".strip()


def token_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def count_redundant(claims: dict) -> int:
    texts = [_claim_text(c) for c in claims.values()]
    count = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if token_overlap(texts[i], texts[j]) > 0.70:
                count += 1
                break
    return count


def count_novel(claims: dict, prior_texts: list) -> int:
    if not prior_texts:
        return len(claims)
    return sum(1 for c in claims.values()
               if all(token_overlap(_claim_text(c), p) < 0.30 for p in prior_texts))


def method_diversity_score(trace: list) -> float:
    if len(trace) < 2:
        return 1.0
    return len(set(trace)) / len(trace)


def infer_method_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("evidence","study","studies","data","research","empirical")):
        return "empirical_evidence"
    if any(w in q for w in ("mechanism","why","how does","cause","because")):
        return "causal_mechanism"
    if any(w in q for w in ("when","temporal","over time","change","trend")):
        return "temporal_validity"
    if any(w in q for w in ("define","unit","measure","concept","what is")):
        return "unit_of_analysis"
    return "conceptual_framing"


def infer_frame_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("effective","work","improve","benefit","harm","impact")):
        return "effectiveness"
    if any(w in q for w in ("why","mechanism","process","path","through")):
        return "mechanism"
    if any(w in q for w in ("who","context","condition","where","population")):
        return "boundary_condition"
    return "descriptive"


def compute_metrics(state: dict, loop: int, prior_texts: list, question: str) -> dict:
    claims   = state.get("claims", {})
    total    = len(claims)
    open_c   = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel    = count_novel(claims, prior_texts)
    all_bases = []
    for c in claims.values():
        all_bases.extend(h.split("[")[0] for h in c.get("history", []))
    branches  = sum(1 for c in claims.values() if c.get("id", "").startswith("B"))
    syntheses = sum(1 for c in claims.values() if c.get("is_synthesis"))
    counters  = all_bases.count("T5")
    contr_gen = all_bases.count("T2")
    dup_rate  = redundant / max(total, 1)

    spl_m = compute_claim_metrics(state)

    return {
        "loop":                      loop,
        "question":                  question,
        "method_type":               infer_method_type(question),
        "frame_type":                infer_frame_type(question),
        "claim_curvature":           spl_m["claim_curvature"],
        "claim_count":               spl_m["claim_count"],
        "total_claims":              total,
        "open_claims":               open_c,
        "sealed_claims":             total - open_c,
        "disputed_claims":           disputed,
        "redundant_claims":          redundant,
        "semantic_duplication_rate": dup_rate,
        "entropy":                   (open_c + disputed + redundant) / max(total, 1),
        "novel_claims":              novel,
        "branch_growth":             branches,
        "contradictions_resolved":   syntheses,
        "total_contradictions":      max(counters, 1),
        "question_utility":          float(contr_gen * 3 + syntheses * 2 + counters * 2 + branches),
    }


def check_failure(current: dict, history: list, method_trace: list) -> str | None:
    last5 = history[-5:] if len(history) >= 5 else history

    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"
    if current["semantic_duplication_rate"] > 0.60:
        return "SEMANTIC_DUPLICATION"
    last10 = history[-10:] if len(history) >= 10 else history
    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"
    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"
    if (len(method_trace) >= 5
            and method_diversity_score(method_trace[-5:]) < 0.30):
        return "METHOD_COLLAPSE"
    return None


def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q: str) -> bool:
        return any(token_overlap(q, h) > 0.75 for h in question_history)

    def make_q(c: dict, prefix: str = "") -> str:
        base = _claim_text(c).strip()
        return f"{prefix}: {base}?" if prefix else f"What is the evidence that {base}?"

    open_c = sorted(
        [c for c in claims.values() if not c.get("sealed") and c.get("id", "").startswith("C")],
        key=lambda c: c.get("confidence", 0), reverse=True,
    )
    for c in open_c:
        q = make_q(c)
        if not already_asked(q):
            return q

    for c in sorted(
        [c for c in claims.values() if c.get("sealed") and not c.get("evidence_refs")],
        key=lambda c: c.get("confidence", 0),
    ):
        q = make_q(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    for c in sorted(
        [c for c in claims.values() if c.get("is_synthesis")],
        key=lambda c: c.get("confidence", 0), reverse=True,
    ):
        q = make_q(c, "Explore the implications of")
        if not already_asked(q):
            return q

    return "LOOP_COMPLETE"


def derive_question_from_claim(claim: dict, state: dict) -> str:
    """Derive a DES question from a weighted claim (EHL path)."""
    base = _claim_text(claim).strip()
    if claim.get("status") == "disputed":
        return f"Is there a resolution to the contradiction that {base}?"
    if not claim.get("evidence_refs"):
        return f"What evidence supports or refutes the claim that {base}?"
    return f"What are the broader implications of the claim that {base}?"


# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

def save_result(
    domain_dir: Path,
    domain_id: str,
    condition_name: str,
    seed_question: str,
    outcome: str,
    loop_metrics: list,
    en_log: list,
    ehl_log: list,
    question_history: list,
    p4_depth: int | None,
    sh_loop0: float | None,
    condition: dict,
    rng_seed: int | None = None,
    persona_filter: str | None = None,
    loop0_prompt_hash: str | None = None,
    loop0_claim_hash: str | None = None,
) -> dict:
    loops_completed = len(loop_metrics)
    depth_lift = (loops_completed - p4_depth) if p4_depth is not None else None

    en_events    = len([e for e in en_log if e.get("selected")])
    en_admitted  = sum(1 for e in en_log if e.get("selected") and e["selected"].get("admitted"))

    outcome_data = {
        "domain_id":          domain_id,
        "condition":          condition_name,
        "seed_question":      seed_question,
        "outcome":            outcome,
        "loops_completed":    loops_completed,
        "p4_depth":           p4_depth,
        "sh_loop0":           sh_loop0,
        "depth_lift":         depth_lift,
        "en_type":            condition.get("en"),
        "ehl_factor":         condition.get("ehl"),
        "en_events":          en_events,
        "en_admitted":        en_admitted,
        "stress_test":        condition.get("ehl") == 0.50,
        "exploratory_arm":    condition_name == "SH_scheduled",
        "rng_seed":           rng_seed,
        "persona_filter":     persona_filter,
        "loop0_prompt_hash":  loop0_prompt_hash,
        "loop0_claim_hash":   loop0_claim_hash,
    }

    # Best ENI composite across all admitted EN selections
    admitted_enis = [e["selected"]["eni_composite"] for e in en_log
                     if e.get("selected") and e["selected"].get("admitted")]
    outcome_data["best_eni_composite"] = round(max(admitted_enis), 4) if admitted_enis else None

    with open(domain_dir / "outcome.json", "w") as f:
        json.dump(outcome_data, f, indent=2)
    with open(domain_dir / "metrics.json", "w") as f:
        json.dump(loop_metrics, f, indent=2)
    with open(domain_dir / "en_log.json", "w") as f:
        json.dump(en_log, f, indent=2)
    with open(domain_dir / "ehl_log.json", "w") as f:
        json.dump(ehl_log, f, indent=2)

    print(f"\n  {domain_id}/{condition_name}: {outcome} | loops={loops_completed} "
          f"| depth_lift={depth_lift} | EN={en_admitted}/{en_events} | EHL={condition.get('ehl')}")
    return outcome_data


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_domain_p7(
    domain_id: str,
    seed_question: str,
    condition_name: str,
    condition: dict,
    p4_depth: int | None = None,
    sh_loop0: float | None = None,
    rng_seed: int | None = None,
    persona_filter: str | None = None,
) -> dict:
    # Resolve SH_scheduled condition dynamically
    resolved_condition = condition.copy()
    if condition.get("en") == "sh_select" or condition.get("ehl") == "sh_select":
        if sh_loop0 is not None:
            resolved = sh_schedule(sh_loop0)
        else:
            # Measure SH from first available state or default to EN_persona
            resolved = {"en": "persona", "ehl": 1.00}
        resolved_condition["en"]  = resolved["en"]
        resolved_condition["ehl"] = resolved["ehl"]
        print(f"  SH_scheduled → resolved: en={resolved_condition['en']}, "
              f"ehl={resolved_condition['ehl']} (sh={sh_loop0}, SH*={SH_STAR})")

    ehl_factor = resolved_condition.get("ehl", 1.00)
    en_type    = resolved_condition.get("en")

    ehl = EpistemicHalfLife(decay_factor=ehl_factor) if ehl_factor < 1.00 else None

    persona_suffix = f"_{persona_filter}" if persona_filter else ""
    seed_suffix = f"_seed{rng_seed}" if rng_seed is not None else ""
    domain_dir = RESULTS_DIR / f"{domain_id}_{condition_name}{persona_suffix}{seed_suffix}"
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Seed Python RNG at run start; log for reproducibility audit
    if rng_seed is not None:
        random.seed(rng_seed)
    rng_seed_actual = rng_seed if rng_seed is not None else None

    question         = seed_question
    question_history = [seed_question]
    method_trace     = []
    loop_metrics     = []
    all_prior_texts  = []
    en_log           = []
    ehl_log          = []
    failure_code     = None
    loop0_prompt_hash: str | None = None
    loop0_claim_hash:  str | None = None
    _pending_novel_idx: int | None = None   # en_log index awaiting novelty_produced_next_loop

    print(f"\n{'='*65}")
    print(f"  {domain_id} [{condition_name}{persona_suffix}{seed_suffix}] | en={en_type} ehl={ehl_factor}")
    if rng_seed_actual is not None:
        print(f"  RNG seed: {rng_seed_actual}")
    if persona_filter:
        print(f"  Persona filter: {persona_filter} (single-persona isolation)")
    print(f"  Seed: {seed_question[:60]}")
    if condition_name == "EHL_0.50":
        print(f"  NOTE: stress test — EHL_0.50 labeled accordingly")
    if condition_name == "SH_scheduled":
        print(f"  NOTE: exploratory arm")
    print(f"{'='*65}")

    loop = 0
    while loop < MAX_LOOPS:
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        # Resume from existing loop file if present
        if loop_file.exists():
            print(f"  [skip] loop {loop:03d}")
            with open(loop_file) as f:
                state = json.load(f)
            state["seed_question"] = seed_question
            metrics = compute_metrics(state, loop, all_prior_texts, question)
            method_trace.append(metrics["method_type"])
            loop_metrics.append(metrics)
            all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())
            if ehl:
                ehl_log.append(ehl.loop_snapshot(state.get("claims", {}), loop))
            next_q = select_next_question(state, question_history)
            if next_q != "LOOP_COMPLETE":
                question_history.append(next_q)
            question = next_q if next_q != "LOOP_COMPLETE" else question
            loop += 1
            continue

        print(f"\n  Loop {loop:03d} | Q: {question[:70]}")

        try:
            des_module.run_des(
                research_question=question,
                max_iterations=MAX_ITER_PER_RUN,
                anti_delphi=True,
                builder_model=BUILDER_MODEL,
                builder_provider=BUILDER_PROVIDER,
                falsifier_model=FALSIFIER_MODEL,
                falsifier_provider=FALSIFIER_PROVIDER,
            )
        except Exception as e:
            print(f"  ERROR in run_des: {e}")
            failure_code = "DES_RUN_ERROR"
            break

        if not STATE_SRC.exists():
            print(f"  ERROR: des_state.json missing after loop {loop}")
            failure_code = "DES_RUN_ERROR"
            break

        with open(STATE_SRC) as f:
            state = json.load(f)
        shutil.copy(STATE_SRC, loop_file)
        state["seed_question"] = seed_question

        # Reproducibility audit: hash loop-0 prompt and claims
        if loop == 0:
            loop0_prompt_hash = hashlib.sha256(question.encode()).hexdigest()[:16]
            claim_texts = sorted(_claim_text(c) for c in state.get("claims", {}).values())
            loop0_claim_hash = hashlib.sha256(
                "\n".join(claim_texts).encode()
            ).hexdigest()[:16]
            print(f"  [audit] loop0_prompt_hash={loop0_prompt_hash} "
                  f"loop0_claim_hash={loop0_claim_hash}")

        metrics = compute_metrics(state, loop, all_prior_texts, question)
        method_trace.append(metrics["method_type"])

        # Backfill novelty_produced_next_loop for the previous EN event
        if _pending_novel_idx is not None:
            en_log[_pending_novel_idx]["novelty_produced_next_loop"] = metrics["novel_claims"]
            _pending_novel_idx = None

        dup_str  = f"{metrics['semantic_duplication_rate']:.0%}"
        novel_str = metrics['novel_claims']
        print(f"  -> dup={dup_str} novel={novel_str} entropy={metrics['entropy']:.2f} "
              f"claims={metrics['total_claims']} K(G)={metrics['claim_curvature']:.3f}")

        all_prior_texts.extend(_claim_text(c) for c in state.get("claims", {}).values())

        # EHL snapshot (before appending metrics)
        if ehl:
            ehl_log.append(ehl.loop_snapshot(state.get("claims", {}), loop))

        # ODC check (decay < 0.85 only)
        if ehl and ehl.check_odc(loop_metrics):
            print(f"  ODC detected at loop {loop}")
            loop_metrics.append(metrics)
            failure_code = "ODC"
            break

        # Standard failure check
        failure = check_failure(metrics, loop_metrics, method_trace)
        if failure:
            print(f"  FAILURE: {failure}")
            loop_metrics.append(metrics)
            failure_code = failure
            break

        loop_metrics.append(metrics)

        # ----------------------------------------------------------------
        # EN injection (H4: preventive — fires before SEMANTIC_DUPLICATION)
        # ----------------------------------------------------------------
        if en_type:
            en_triggered = early_saturation_detected(loop_metrics[:-1], metrics)
            if en_triggered:
                print(f"  [EN] early saturation detected at loop {loop} — generating {en_type} candidates"
                      + (f" (persona={persona_filter})" if persona_filter else ""))
                candidates = generate_en_candidates(
                    question, state, en_type, call_llm, k=3,
                    persona_filter=persona_filter,
                )
                best = select_best_en(candidates)
                en_event = {
                    "loop":                       loop,
                    "trigger":                    "early_saturation",
                    "en_type":                    en_type,
                    "persona_filter":             persona_filter,
                    "candidates":                 candidates,
                    "selected":                   best,
                    "ehl_seed":                   ehl._last_seed if ehl else None,
                    "novelty_produced_next_loop": None,  # backfilled after next loop
                }
                en_log.append(en_event)
                _pending_novel_idx = len(en_log) - 1
                if best and best.get("admitted"):
                    print(f"  [EN] admitted: {best['question'][:70]} | eni={best['eni_composite']:.3f}")
                    question = best["question"]
                    question_history.append(question)
                    loop += 1
                    continue
                else:
                    print(f"  [EN] no candidate admitted — proceeding with standard selection")

        # ----------------------------------------------------------------
        # EHL-weighted question selection
        # ----------------------------------------------------------------
        if ehl:
            claims = state.get("claims", {})
            weighted = ehl.weighted_select(
                claims, loop,
                criterion=lambda c: (not c.get("sealed")
                                     and c.get("status") == "supported"),
            )
            if weighted:
                cid, claim = weighted[0]
                next_q = derive_question_from_claim(claim, state)
                print(f"  [EHL] weighted select → {next_q[:70]} (seed={ehl._last_seed})")
            else:
                next_q = select_next_question(state, question_history)
        else:
            next_q = select_next_question(state, question_history)

        if next_q == "LOOP_COMPLETE":
            print(f"  LOOP_COMPLETE at loop {loop}")
            break

        question = next_q
        question_history.append(question)
        loop += 1

    # Classify outcome
    if not failure_code:
        if loop >= MAX_LOOPS:
            failure_code = "MAX_LOOPS_REACHED"
        else:
            failure_code = "LOOP_COMPLETE"

    return save_result(
        domain_dir=domain_dir,
        domain_id=domain_id,
        condition_name=condition_name,
        seed_question=seed_question,
        outcome=failure_code,
        loop_metrics=loop_metrics,
        en_log=en_log,
        ehl_log=ehl_log,
        question_history=question_history,
        p4_depth=p4_depth,
        sh_loop0=sh_loop0,
        condition=resolved_condition,
        rng_seed=rng_seed_actual,
        persona_filter=persona_filter,
        loop0_prompt_hash=loop0_prompt_hash,
        loop0_claim_hash=loop0_claim_hash,
    )


# ---------------------------------------------------------------------------
# Batch runner + summary
# ---------------------------------------------------------------------------

def run_batch(domain_ids: list, condition_names: list, rng_seed: int | None = None,
              persona_filter: str | None = None):
    all_results = {}

    for domain_id in domain_ids:
        if domain_id not in DOMAINS:
            print(f"Unknown domain: {domain_id}")
            continue
        info = DOMAINS[domain_id]
        all_results[domain_id] = {}

        for cname in condition_names:
            if cname not in EXPERIMENTAL_CONDITIONS:
                print(f"Unknown condition: {cname}")
                continue
            condition = EXPERIMENTAL_CONDITIONS[cname]
            result = run_domain_p7(
                domain_id=domain_id,
                seed_question=info["seed"],
                condition_name=cname,
                condition=condition,
                p4_depth=info.get("p4_depth"),
                sh_loop0=info.get("sh_loop0"),
                rng_seed=rng_seed,
                persona_filter=persona_filter,
            )
            all_results[domain_id][cname] = result
            time.sleep(2)

    write_summary(all_results)
    return all_results


def write_summary(all_results: dict):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # H1–H6 verdict computation
    p4_depths = {}
    for domain_id, conditions in all_results.items():
        if "P4_baseline" in conditions:
            p4_depths[domain_id] = conditions["P4_baseline"].get("loops_completed")

    h1_lifts_en = []
    h5_comparison = []
    h6_comparison = []
    en_type_enis = {"temp": [], "persona": [], "adjacent": []}

    for domain_id, conditions in all_results.items():
        p4 = p4_depths.get(domain_id)
        for cname, r in conditions.items():
            depth = r.get("loops_completed")
            if p4 is not None and depth is not None and cname != "P4_baseline":
                lift = depth - p4
                en_t = r.get("en_type")
                ehl_f = r.get("ehl_factor")
                if en_t and ehl_f == 1.00:
                    h1_lifts_en.append((cname, domain_id, lift))
                if ehl_f == 0.90 and not en_t:
                    h5_comparison.append((domain_id, depth, p4))
                if ehl_f == 0.50 and not en_t:
                    h6_comparison.append((domain_id, depth, p4))
                if r.get("best_eni_composite") and en_t in en_type_enis:
                    en_type_enis[en_t].append(r["best_eni_composite"])

    def avg(lst):
        return round(sum(lst) / len(lst), 4) if lst else None

    h1_verdict = ("CONFIRMED" if h1_lifts_en and sum(l > 0 for _, _, l in h1_lifts_en) / len(h1_lifts_en) >= 0.60
                  else "NOT_CONFIRMED" if h1_lifts_en else "INSUFFICIENT_DATA")

    eni_avgs = {k: avg(v) for k, v in en_type_enis.items()}
    h2_verdict = "INSUFFICIENT_DATA"
    if eni_avgs["persona"] and eni_avgs["temp"]:
        h2_verdict = "CONFIRMED" if eni_avgs["persona"] > eni_avgs["temp"] else "NOT_CONFIRMED"

    h3_adjacent_higher = (eni_avgs["adjacent"] and eni_avgs["persona"]
                          and eni_avgs["adjacent"] > eni_avgs["persona"])

    h5_improved = sum(d > p for _, d, p in h5_comparison)
    h5_verdict = ("CONFIRMED" if h5_comparison and h5_improved / len(h5_comparison) >= 0.60
                  else "NOT_CONFIRMED" if h5_comparison else "INSUFFICIENT_DATA")

    h6_worse = sum(d < p for _, d, p in h6_comparison)
    h6_verdict = ("CONFIRMED" if h6_comparison and h6_worse / len(h6_comparison) >= 0.60
                  else "NOT_CONFIRMED" if h6_comparison else "INSUFFICIENT_DATA")

    summary = {
        "paper": 7,
        "sh_star_locked": SH_STAR,
        "verdicts": {
            "H1_EN_extends_depth":           h1_verdict,
            "H2_persona_beats_temp":         h2_verdict,
            "H3_adjacent_highest_novelty":   "CONFIRMED" if h3_adjacent_higher else "NOT_CONFIRMED",
            "H4_preventive_timing":          "see_en_log_trigger_loops",
            "H5_EHL090_improves_depth":      h5_verdict,
            "H6_EHL050_harms_depth":         h6_verdict,
        },
        "eni_averages":    eni_avgs,
        "notes": {
            "EHL_0.50":      "stress test only — collapse expected",
            "SH_scheduled":  "exploratory arm — not a primary hypothesis",
        },
        "results": all_results,
    }

    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Markdown summary
    lines = [
        "# Paper 7 — Summary: EN + EHL Results",
        "",
        f"SH* = {SH_STAR} (locked from Paper 6)",
        "",
        "## H1–H6 Verdicts",
        "",
        f"| Hypothesis | Verdict |",
        f"|------------|---------|",
    ]
    for h, v in summary["verdicts"].items():
        lines.append(f"| {h} | {v} |")

    lines += [
        "",
        "## ENI Averages by EN Type",
        "",
        "| EN Type | Avg ENI Composite |",
        "|---------|-------------------|",
    ]
    for t, v in eni_avgs.items():
        lines.append(f"| {t} | {v if v is not None else 'n/a'} |")

    lines += [
        "",
        "## Per-Domain Depth Lift vs P4 Baseline",
        "",
        "| Domain | Condition | P4 depth | P7 depth | Lift | EN admitted | EHL | Note |",
        "|--------|-----------|----------|----------|------|-------------|-----|------|",
    ]
    for domain_id, conditions in all_results.items():
        p4 = p4_depths.get(domain_id, "?")
        for cname, r in conditions.items():
            depth = r.get("loops_completed", "?")
            lift = r.get("depth_lift", "?")
            en_adm = r.get("en_admitted", 0)
            en_ev  = r.get("en_events", 0)
            ehl_f  = r.get("ehl_factor", 1.00)
            note = ""
            if r.get("stress_test"):
                note = "stress test"
            elif r.get("exploratory_arm"):
                note = "exploratory"
            lines.append(f"| {domain_id} | {cname} | {p4} | {depth} | {lift} "
                         f"| {en_adm}/{en_ev} | {ehl_f} | {note} |")

    md_path = RESULTS_DIR / "summary.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nSummary saved: {summary_path}")
    print(f"Markdown:      {md_path}")
    return summary


# ---------------------------------------------------------------------------
# Persona isolation runner (exploratory)
# ---------------------------------------------------------------------------

PERSONA_KEYS = ["popper", "shannon", "darwin"]
CREATIVE_PERSONA_KEYS = ["mozart", "picasso"]
MATH_PERSONA_KEYS = ["kant", "darwin", "mozart"]
ISOLATION_SEEDS = [101, 202, 303]


def run_persona_isolation(domain_id: str = "N03"):
    """
    Exploratory persona isolation: run domain_id × each single persona × each seed.
    9 runs total. Results written to paper7/persona_isolation_{domain_id}.{md,json}.
    No hypothesis confirmed — labeled exploratory throughout.
    """
    info = DOMAINS[domain_id]
    condition = EXPERIMENTAL_CONDITIONS["EN_persona"]
    all_rows = []

    for persona in PERSONA_KEYS:
        for seed in ISOLATION_SEEDS:
            result = run_domain_p7(
                domain_id=domain_id,
                seed_question=info["seed"],
                condition_name="EN_persona",
                condition=condition,
                p4_depth=info.get("p4_depth"),
                sh_loop0=info.get("sh_loop0"),
                rng_seed=seed,
                persona_filter=persona,
            )

            # Collect EN event details
            en_log_path = (RESULTS_DIR / f"{domain_id}_EN_persona_{persona}_seed{seed}"
                           / "en_log.json")
            en_events_detail = []
            if en_log_path.exists():
                with open(en_log_path) as f:
                    raw_en = json.load(f)
                for ev in raw_en:
                    sel = ev.get("selected") or {}
                    en_events_detail.append({
                        "loop":                     ev.get("loop"),
                        "eni_novelty":              sel.get("eni_novelty"),
                        "eni_admissibility":        sel.get("eni_admissibility"),
                        "eni_non_drift":            sel.get("eni_non_drift"),
                        "eni_composite":            sel.get("eni_composite"),
                        "drift":                    round(1.0 - (sel.get("eni_non_drift") or 0), 4),
                        "admitted":                 sel.get("admitted"),
                        "novelty_produced_next_loop": ev.get("novelty_produced_next_loop"),
                    })

            # Collect loop-0 dup from metrics
            metrics_path = (RESULTS_DIR / f"{domain_id}_EN_persona_{persona}_seed{seed}"
                            / "metrics.json")
            loop0_dup = None
            if metrics_path.exists():
                with open(metrics_path) as f:
                    mlist = json.load(f)
                if mlist:
                    loop0_dup = round(mlist[0].get("semantic_duplication_rate", 0), 4)

            row = {
                "domain":           domain_id,
                "persona":          persona,
                "seed":             seed,
                "loop0_dup":        loop0_dup,
                "loop0_claim_hash": result.get("loop0_claim_hash"),
                "en_fired":         result.get("en_events", 0),
                "loops":            result.get("loops_completed"),
                "depth_lift":       result.get("depth_lift"),
                "failure_mode":     result.get("outcome"),
                "en_events":        en_events_detail,
                "exploratory":      True,
            }
            all_rows.append(row)
            print(f"  [{persona}/seed{seed}] loops={row['loops']} "
                  f"depth_lift={row['depth_lift']} EN={row['en_fired']} "
                  f"outcome={row['failure_mode']}")

    _write_persona_isolation_report(domain_id, all_rows)
    return all_rows


def _write_persona_isolation_report(domain_id: str, rows: list):
    out_dir = Path("paper7")
    out_dir.mkdir(exist_ok=True)

    # JSON
    report = {
        "label":       "EXPLORATORY — persona isolation, not a confirmed hypothesis",
        "domain":      domain_id,
        "personas":    PERSONA_KEYS,
        "seeds":       ISOLATION_SEEDS,
        "n_runs":      len(rows),
        "rows":        rows,
    }
    json_path = out_dir / f"persona_isolation_{domain_id}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Markdown
    lines = [
        f"# Paper 7 — Persona Isolation: {domain_id}",
        "",
        "**EXPLORATORY — not a confirmed hypothesis.**",
        "Goal: determine whether Shannon's recovery in seed 101 was persona-specific or seed noise.",
        "",
        f"Domain: `{domain_id}` | Condition: EN_persona | Seeds: {ISOLATION_SEEDS}",
        "",
        "## Results Table",
        "",
        "| Persona | Seed | Loop-0 dup | EN fired | Loops | depth_lift | Failure mode | claim_hash |",
        "|---------|------|------------|----------|-------|------------|--------------|------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['persona']} | {r['seed']} | {r['loop0_dup']} | {r['en_fired']} "
            f"| {r['loops']} | {r['depth_lift']} | {r['failure_mode']} "
            f"| `{r['loop0_claim_hash'] or '?'}` |"
        )

    lines += ["", "## EN Event Detail", ""]
    for r in rows:
        if r["en_events"]:
            lines.append(f"### {r['persona']} / seed {r['seed']}")
            lines.append("")
            lines.append("| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |")
            lines.append("|------|-------------|---------------|-------|---------------|----------|--------------|")
            for ev in r["en_events"]:
                lines.append(
                    f"| {ev['loop']} | {ev['eni_novelty']} | {ev['eni_non_drift']} "
                    f"| {ev['drift']} | {ev['eni_composite']} | {ev['admitted']} "
                    f"| {ev['novelty_produced_next_loop']} |"
                )
            lines.append("")

    lines += [
        "## Interpretation Notes",
        "",
        "- Shannon (information-theoretic) reframing introduced in seed 101 achieved dup 58%→14%.",
        "- Popper (falsificationism) introduced in seed 202 did not recover (55%→64%).",
        "- These observations are from n=3 seeds × 3 personas = 9 runs.",
        "  Insufficient to confirm persona ranking. Further replication required.",
        "- `novelty_produced_next_loop` measures novel claims in the loop immediately",
        "  following EN injection — not total depth improvement.",
    ]

    md_path = out_dir / f"persona_isolation_{domain_id}.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nPersona isolation report: {json_path}")
    print(f"Markdown:                 {md_path}")


# ---------------------------------------------------------------------------
# Creative persona probe (exploratory curiosity)
# ---------------------------------------------------------------------------

def run_creative_probe(domain_id: str = "N03"):
    """
    EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.
    Runs domain_id × [mozart, picasso] × [101, 202, 303].
    6 runs total. Results written to paper7/creative_persona_probe_{domain_id}.{md,json}.
    """
    info = DOMAINS[domain_id]
    condition = EXPERIMENTAL_CONDITIONS["EN_persona"]
    all_rows = []

    for persona in CREATIVE_PERSONA_KEYS:
        for seed in ISOLATION_SEEDS:
            result = run_domain_p7(
                domain_id=domain_id,
                seed_question=info["seed"],
                condition_name="EN_persona",
                condition=condition,
                p4_depth=info.get("p4_depth"),
                sh_loop0=info.get("sh_loop0"),
                rng_seed=seed,
                persona_filter=persona,
            )

            en_log_path = (RESULTS_DIR / f"{domain_id}_EN_persona_{persona}_seed{seed}"
                           / "en_log.json")
            en_events_detail = []
            if en_log_path.exists():
                with open(en_log_path) as f:
                    raw_en = json.load(f)
                for ev in raw_en:
                    sel = ev.get("selected") or {}
                    en_events_detail.append({
                        "loop":                       ev.get("loop"),
                        "eni_novelty":                sel.get("eni_novelty"),
                        "eni_admissibility":          sel.get("eni_admissibility"),
                        "eni_non_drift":              sel.get("eni_non_drift"),
                        "eni_composite":              sel.get("eni_composite"),
                        "drift":                      round(1.0 - (sel.get("eni_non_drift") or 0), 4),
                        "admitted":                   sel.get("admitted"),
                        "novelty_produced_next_loop": ev.get("novelty_produced_next_loop"),
                    })

            metrics_path = (RESULTS_DIR / f"{domain_id}_EN_persona_{persona}_seed{seed}"
                            / "metrics.json")
            loop0_dup = None
            if metrics_path.exists():
                with open(metrics_path) as f:
                    mlist = json.load(f)
                if mlist:
                    loop0_dup = round(mlist[0].get("semantic_duplication_rate", 0), 4)

            row = {
                "domain":           domain_id,
                "persona":          persona,
                "seed":             seed,
                "loop0_dup":        loop0_dup,
                "loop0_claim_hash": result.get("loop0_claim_hash"),
                "en_fired":         result.get("en_events", 0),
                "loops":            result.get("loops_completed"),
                "depth_lift":       result.get("depth_lift"),
                "failure_mode":     result.get("outcome"),
                "en_events":        en_events_detail,
                "exploratory":      True,
                "probe":            "creative_nonlocal",
            }
            all_rows.append(row)
            print(f"  [{persona}/seed{seed}] loops={row['loops']} "
                  f"depth_lift={row['depth_lift']} EN={row['en_fired']} "
                  f"outcome={row['failure_mode']}")

    _write_creative_probe_report(domain_id, all_rows)
    return all_rows


def _write_creative_probe_report(domain_id: str, rows: list):
    out_dir = Path("paper7")
    out_dir.mkdir(exist_ok=True)

    report = {
        "label":   ("EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory. "
                    "Do not fold into Paper 7 main result."),
        "domain":  domain_id,
        "personas": CREATIVE_PERSONA_KEYS,
        "seeds":   ISOLATION_SEEDS,
        "n_runs":  len(rows),
        "goal":    ("Check whether creative non-local operators (mozart, picasso) produce "
                    "stronger novelty regeneration than rational operators (popper, shannon, darwin)."),
        "rows":    rows,
    }
    json_path = out_dir / f"creative_persona_probe_{domain_id}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Markdown report
    lines = [
        f"# Creative Persona Probe — {domain_id}",
        "",
        "**EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.**  ",
        "**Do not fold into Paper 7 main result.**",
        "",
        "**Goal:** Check whether creative non-local operators (mozart, picasso) produce",
        "stronger novelty regeneration than rational operators (popper, shannon, darwin).",
        "",
        f"Domain: `{domain_id}` — {DOMAINS[domain_id]['seed']}  ",
        f"Condition: EN\\_persona | Personas: {CREATIVE_PERSONA_KEYS} | Seeds: {ISOLATION_SEEDS}  ",
        f"P4 baseline depth: {DOMAINS[domain_id].get('p4_depth')} loops (depth_lift=0 reference)",
        "",
        "---",
        "",
        "## Results",
        "",
        "| Persona | Seed | Loop-0 dup | EN fired | Loops | depth_lift | Outcome | claim_hash |",
        "|---------|------|------------|----------|-------|------------|---------|------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['persona']} | {r['seed']} | {r['loop0_dup']} | {r['en_fired']} "
            f"| {r['loops']} | {r['depth_lift']} | {r['failure_mode']} "
            f"| `{r['loop0_claim_hash'] or '?'}` |"
        )

    lines += ["", "## EN Event Detail", ""]
    for r in rows:
        if r["en_events"]:
            lines.append(f"### {r['persona']} / seed {r['seed']}")
            lines.append("")
            lines.append("| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |")
            lines.append("|------|-------------|---------------|-------|---------------|----------|--------------|")
            for ev in r["en_events"]:
                lines.append(
                    f"| {ev['loop']} | {ev['eni_novelty']} | {ev['eni_non_drift']} "
                    f"| {ev['drift']} | {ev['eni_composite']} | {ev['admitted']} "
                    f"| {ev['novelty_produced_next_loop']} |"
                )
            lines.append("")

    lines += [
        "## Comparison with Rational Personas (from persona_structural_fit.md)",
        "",
        "| Persona | mean_depth_lift | median_depth_lift | type |",
        "|---------|----------------|-------------------|------|",
        "| popper  | +0.67 (⚠️ resume-inflated) | 0 | rational |",
        "| shannon | −0.33          | −1                | rational |",
        "| darwin  | +3.00          | +3                | rational |",
    ]
    # Add creative persona rows
    for persona in CREATIVE_PERSONA_KEYS:
        pr = [r for r in rows if r["persona"] == persona]
        if pr:
            dls = [r["depth_lift"] for r in pr if r["depth_lift"] is not None]
            mean_dl = round(sum(dls) / len(dls), 2) if dls else "?"
            med_dl  = sorted(dls)[len(dls) // 2] if dls else "?"
            lines.append(f"| {persona}  | {mean_dl} | {med_dl} | creative_nonlocal |")

    lines += [
        "",
        "## Notes",
        "",
        "- n=3 per persona. Purely exploratory — no statistical inference warranted.",
        "- Creative personas use structurally non-local reframing: Mozart (thematic variation,",
        "  modulation, transformed return) and Picasso (cubist multi-view decomposition).",
        "- Admissibility gate (Alexandria-lite) unchanged; no threshold modifications.",
        "- Python RNG seed ≠ LLM determinism. Claim hashes will differ across seeds.",
        "- Results are NOT pre-registered and should NOT be cited as confirmatory.",
    ]

    md_path = out_dir / f"creative_persona_probe_{domain_id}.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nCreative probe report: {json_path}")
    print(f"Markdown:              {md_path}")


# ---------------------------------------------------------------------------
# Math persona probe (exploratory curiosity)
# ---------------------------------------------------------------------------

def _extract_math_content(claims: dict) -> dict:
    """Scan sealed claims for mathematical content keywords."""
    import re
    sealed_texts = []
    for c in claims.values():
        if c.get("sealed"):
            text = " ".join([
                c.get("subject", ""), c.get("predicate", ""), c.get("object", "")
            ]).lower()
            sealed_texts.append(text)

    kw = {
        "cycles": ["cycle", "cyclic", "periodic", "period", "orbit", "returns to"],
        "fixed_points": ["fixed point", "fixed-point", "equilibrium", "t(n)=n", "t(n) = n"],
        "invariants": ["invariant", "conserved", "monovariant", "preserved", "monotone"],
        "divergence": ["diverge", "unbounded", "grows without", "tend to infinity", "escapes"],
        "convergence": ["converge", "eventually reach", "all trajectories", "basin of attraction"],
        "conjectures": ["conjecture", "we hypothesize", "it is plausible", "suggests that",
                        "may be true", "is likely that", "appears to"],
        "counterexamples": ["counterexample", "counter-example", "exception", "fails for"],
        "proof": ["proof", "proven", "provable", "cannot be proven", "unprovable", "undecidable"],
    }
    hits = {}
    for category, keywords in kw.items():
        matches = []
        for text in sealed_texts:
            if any(k in text for k in keywords):
                matches.append(text[:120])
        hits[category] = matches
    return hits


def run_math_probe(domain_id: str = "M01"):
    """
    EXPLORATORY CURIOSITY PROBE — mathematical unknown-problem probe.
    Runs domain_id × P4_baseline (3 seeds) + [kant, darwin, mozart] × (3 seeds).
    12 runs total. Results written to paper7/math_persona_probe_{domain_id}.{md,json}.
    No hypothesis confirmed — labeled exploratory throughout.
    """
    info = DOMAINS[domain_id]
    condition_en  = EXPERIMENTAL_CONDITIONS["EN_persona"]
    condition_p4  = EXPERIMENTAL_CONDITIONS["P4_baseline"]
    all_rows      = []
    p4_baseline_loops: dict[int, int] = {}  # seed -> loops_completed

    # --- P4 baseline ---
    print(f"\n=== Math probe: P4 baseline ({domain_id}) ===")
    for seed in ISOLATION_SEEDS:
        result = run_domain_p7(
            domain_id=domain_id,
            seed_question=info["seed"],
            condition_name="P4_baseline",
            condition=condition_p4,
            p4_depth=info.get("p4_depth"),
            sh_loop0=info.get("sh_loop0"),
            rng_seed=seed,
        )
        p4_baseline_loops[seed] = result.get("loops_completed", 0)

        final_state = _last_loop_state(domain_id, "P4_baseline", None, seed)
        math_hits   = _extract_math_content(final_state.get("claims", {})) if final_state else {}

        metrics_path = (RESULTS_DIR / f"{domain_id}_P4_baseline_seed{seed}" / "metrics.json")
        loop0_dup = None
        if metrics_path.exists():
            with open(metrics_path) as f:
                mlist = json.load(f)
            if mlist:
                loop0_dup = round(mlist[0].get("semantic_duplication_rate", 0), 4)

        row = {
            "domain":           domain_id,
            "persona":          "P4_baseline",
            "seed":             seed,
            "loop0_dup":        loop0_dup,
            "loop0_claim_hash": result.get("loop0_claim_hash"),
            "en_fired":         0,
            "loops":            result.get("loops_completed"),
            "depth_lift":       None,
            "failure_mode":     result.get("outcome"),
            "en_events":        [],
            "math_content":     math_hits,
            "exploratory":      True,
            "probe":            "math_probe",
        }
        all_rows.append(row)
        print(f"  [P4_baseline/seed{seed}] loops={row['loops']} outcome={row['failure_mode']}")

    # --- Persona runs ---
    print(f"\n=== Math probe: EN persona runs ({domain_id}) ===")
    for persona in MATH_PERSONA_KEYS:
        for seed in ISOLATION_SEEDS:
            dir_name = f"{domain_id}_EN_persona_{persona}_seed{seed}"
            result = run_domain_p7(
                domain_id=domain_id,
                seed_question=info["seed"],
                condition_name="EN_persona",
                condition=condition_en,
                p4_depth=p4_baseline_loops.get(seed),
                sh_loop0=info.get("sh_loop0"),
                rng_seed=seed,
                persona_filter=persona,
            )

            en_log_path = RESULTS_DIR / dir_name / "en_log.json"
            en_events_detail = []
            if en_log_path.exists():
                with open(en_log_path) as f:
                    raw_en = json.load(f)
                for ev in raw_en:
                    sel = ev.get("selected") or {}
                    en_events_detail.append({
                        "loop":                     ev.get("loop"),
                        "question":                 sel.get("question", "")[:200],
                        "eni_novelty":              sel.get("eni_novelty"),
                        "eni_admissibility":        sel.get("eni_admissibility"),
                        "eni_non_drift":            sel.get("eni_non_drift"),
                        "eni_composite":            sel.get("eni_composite"),
                        "drift":                    round(1.0 - (sel.get("eni_non_drift") or 0), 4),
                        "admitted":                 sel.get("admitted"),
                        "novelty_produced_next_loop": ev.get("novelty_produced_next_loop"),
                    })

            metrics_path = RESULTS_DIR / dir_name / "metrics.json"
            loop0_dup = None
            if metrics_path.exists():
                with open(metrics_path) as f:
                    mlist = json.load(f)
                if mlist:
                    loop0_dup = round(mlist[0].get("semantic_duplication_rate", 0), 4)

            final_state = _last_loop_state(domain_id, "EN_persona", persona, seed)
            math_hits   = _extract_math_content(final_state.get("claims", {})) if final_state else {}

            p4_ref = p4_baseline_loops.get(seed)
            depth_lift = (result.get("loops_completed", 0) - p4_ref) if p4_ref else None

            row = {
                "domain":           domain_id,
                "persona":          persona,
                "seed":             seed,
                "loop0_dup":        loop0_dup,
                "loop0_claim_hash": result.get("loop0_claim_hash"),
                "en_fired":         result.get("en_events", 0),
                "loops":            result.get("loops_completed"),
                "depth_lift":       depth_lift,
                "failure_mode":     result.get("outcome"),
                "en_events":        en_events_detail,
                "math_content":     math_hits,
                "exploratory":      True,
                "probe":            "math_probe",
            }
            all_rows.append(row)
            print(f"  [{persona}/seed{seed}] loops={row['loops']} "
                  f"depth_lift={row['depth_lift']} EN={row['en_fired']} "
                  f"outcome={row['failure_mode']}")

    _write_math_probe_report(domain_id, all_rows, p4_baseline_loops)


def _last_loop_state(domain_id: str, condition: str, persona: str | None, seed: int) -> dict | None:
    """Load the last available loop_*_state.json for a run."""
    import glob as _glob
    if persona:
        dir_name = f"{domain_id}_{condition}_{persona}_seed{seed}"
    else:
        dir_name = f"{domain_id}_{condition}_seed{seed}"
    states = sorted(_glob.glob(str(RESULTS_DIR / dir_name / "loop_*_state.json")))
    if not states:
        return None
    with open(states[-1]) as f:
        return json.load(f)


def _write_math_probe_report(domain_id: str, rows: list, p4_loops: dict):
    out_dir = Path(__file__).parent
    seed_q  = DOMAINS[domain_id]["seed"]

    # --- JSON ---
    json_path = out_dir / f"math_persona_probe_{domain_id}.json"
    report = {
        "label": ("EXPLORATORY CURIOSITY PROBE — mathematical unknown-problem probe. "
                  "Not pre-registered, not confirmatory. "
                  "All generated mathematical claims are hypotheses requiring external verification."),
        "domain":        domain_id,
        "seed_question": seed_q,
        "personas":      ["P4_baseline"] + MATH_PERSONA_KEYS,
        "seeds":         ISOLATION_SEEDS,
        "n_runs":        len(rows),
        "p4_baseline_loops": p4_loops,
        "goal": ("Test whether persona operators behave differently on a novel recursive "
                 "mathematical system unlikely to be memorized from training data. "
                 "Assess mathematical content quality: cycles, fixed points, invariants, "
                 "conjectures, false proofs, counterexamples."),
        "caveats": [
            "n=3 per persona, single domain (M01). No statistical inference warranted.",
            "All mathematical claims generated by LLM are HYPOTHESES — require external verification.",
            "DES is not a math solver. It generates structured claims, not proofs.",
            "False proof / hallucinated proof detection is keyword-based — may miss subtle errors.",
            "Python RNG seed != LLM determinism. Claim hashes differ across seeds.",
            "Thresholds, architecture, and prompts unchanged from N03 runs.",
        ],
        "rows": rows,
    }
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # --- Markdown ---
    lines = [
        f"# Math Persona Probe — {domain_id}",
        "",
        "**EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.**  ",
        "**All mathematical claims generated are HYPOTHESES — require external verification.**  ",
        f"**Date:** 2026-05-05 | Domain: `{domain_id}`",
        "",
        "## Seed Question",
        "",
        f"> {seed_q}",
        "",
        "---",
        "",
        "## Trajectory Metrics",
        "",
        "| persona | seed | loops | outcome | depth_lift | EN_fired | loop0_dup | claim_hash |",
        "|---------|------|-------|---------|------------|----------|-----------|------------|",
    ]
    for r in rows:
        dl    = f"+{r['depth_lift']}" if (r['depth_lift'] or 0) > 0 else str(r['depth_lift'] or "—")
        chash = f"`{r['loop0_claim_hash']}`" if r.get("loop0_claim_hash") else "*(null)*"
        lines.append(
            f"| {r['persona']} | {r['seed']} | {r['loops']} | {r['failure_mode']} "
            f"| {dl} | {r['en_fired']} | {r.get('loop0_dup','—')} | {chash} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Mathematical Content — Detected Concept Hits",
        "",
        "*(Keyword scan of sealed claims at terminal loop — not a proof of presence or absence.)*",
        "",
    ]
    categories = ["cycles", "fixed_points", "invariants", "divergence",
                  "convergence", "conjectures", "counterexamples", "proof"]
    for r in rows:
        mc = r.get("math_content", {})
        if not mc:
            continue
        hits = {k: len(v) for k, v in mc.items() if v}
        if not hits:
            continue
        lines.append(f"### {r['persona']} / seed {r['seed']}")
        for cat in categories:
            count = len(mc.get(cat, []))
            if count:
                lines.append(f"- **{cat}**: {count} claim(s)")
                for ex in mc.get(cat, [])[:2]:
                    lines.append(f"  - *{ex[:110]}...*")
        lines.append("")

    lines += [
        "---",
        "",
        "## EN Event Detail (persona runs)",
        "",
    ]
    for r in rows:
        if not r.get("en_events"):
            continue
        lines.append(f"### {r['persona']} / seed {r['seed']}")
        lines.append("")
        lines.append("| loop | eni_novelty | eni_non_drift | drift | eni_composite | admitted | nov_next | question (truncated) |")
        lines.append("|------|-------------|---------------|-------|---------------|----------|----------|----------------------|")
        for ev in r["en_events"]:
            q_trunc = (ev.get("question") or "")[:60].replace("|", "/")
            lines.append(
                f"| {ev.get('loop')} | {ev.get('eni_novelty')} | {ev.get('eni_non_drift')} "
                f"| {ev.get('drift')} | {ev.get('eni_composite')} | {ev.get('admitted')} "
                f"| {ev.get('novelty_produced_next_loop')} | {q_trunc} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## Caveats",
        "",
        "1. **n=3 per persona.** Cell counts only. No statistical inference.",
        "2. **LLM is not a math solver.** DES generates structured claims, not proofs.",
        "3. **All mathematical claims require external verification.** Do not treat as proved.",
        "4. **False proof detection is keyword-based.** May miss subtle or implicit proof claims.",
        "5. **Thresholds and architecture unchanged** from N03 runs.",
        "6. **Not pre-registered.**",
    ]

    md_path = out_dir / f"math_persona_probe_{domain_id}.md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nMath probe report: {json_path}")
    print(f"Markdown:          {md_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Paper 7 EN+EHL runner")
    parser.add_argument("--domain", type=str, help="Domain ID (e.g. N03)")
    parser.add_argument("--condition", type=str, help="Condition name (e.g. EN_persona)")
    parser.add_argument("--all", action="store_true",
                        help="Run all domains × all conditions")
    parser.add_argument("--domains", nargs="+", help="Multiple domain IDs")
    parser.add_argument("--conditions", nargs="+", help="Multiple condition names")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducibility audit (e.g. 101, 202, 303)")
    parser.add_argument("--persona", type=str, default=None,
                        choices=PERSONA_KEYS + CREATIVE_PERSONA_KEYS + MATH_PERSONA_KEYS,
                        help="Single-persona filter for EN_persona condition. Isolation use only.")
    parser.add_argument("--persona-isolation", action="store_true",
                        help="Run full persona isolation: N03 × 3 personas × 3 seeds")
    parser.add_argument("--creative-probe", action="store_true",
                        help="EXPLORATORY: run creative persona probe (mozart, picasso) × 3 seeds")
    parser.add_argument("--math-probe", action="store_true",
                        help="EXPLORATORY: run math persona probe (kant, darwin, mozart) × 3 seeds on M01")
    args = parser.parse_args()

    _init_clients()

    if args.persona_isolation:
        domain = args.domain or "N03"
        run_persona_isolation(domain_id=domain)
        return

    if args.creative_probe:
        domain = args.domain or "N03"
        run_creative_probe(domain_id=domain)
        return

    if args.math_probe:
        domain = args.domain or "M01"
        run_math_probe(domain_id=domain)
        return

    if args.all:
        domain_ids    = list(DOMAINS.keys())
        condition_names = list(EXPERIMENTAL_CONDITIONS.keys())
    else:
        domain_ids    = args.domains or ([args.domain] if args.domain else ["N03"])
        condition_names = args.conditions or ([args.condition] if args.condition
                                              else ["P4_baseline"])

    run_batch(domain_ids, condition_names, rng_seed=args.seed,
              persona_filter=args.persona)


if __name__ == "__main__":
    main()

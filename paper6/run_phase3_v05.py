"""
paper6/run_phase3_v05.py
Phase 3: P5v05 (SPL perturbation) runs on confirmed high-SH domains.
Exploratory — n=2 (N03, N05), SH* = 0.0876 unchanged.
Compares depth with Phase 2 P4 results.
WP2 (Rentschler 2026).
"""

import json, os, re, shutil, sys, time
from collections import Counter
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "paper5"))

from paper5.spl_wrapper import (
    get_spl, project, centroid, distance,
    detect_attractor_in_claims, select_escape_vector,
    compute_claim_metrics, check_false_escape,
)
from paper6.compute_sh import compute_semantic_headroom

BUILDER_MODEL      = "deepseek-chat"
BUILDER_PROVIDER   = "deepseek"
FALSIFIER_MODEL    = "openai/gpt-4o"
FALSIFIER_PROVIDER = "openrouter"
MAX_LOOPS          = 20
MAX_ITER_PER_RUN   = 40
MAX_T10            = 2

SH_STAR_LOCKED = 0.0876  # locked, not recalibrated

# Phase 2 P4 baseline depths
P4_BASELINE = {"N03": 4, "N05": 3}

# High-SH confirmed domains (Phase 2)
DOMAINS = {
    "N03": {
        "seed": "Is artificial general intelligence achievable within 20 years?",
        "sh_loop0": 0.1065,
        "p4_depth": 4,
    },
    "N05": {
        "seed": "Does economic inequality harm social cohesion?",
        "sh_loop0": 0.0941,
        "p4_depth": 3,
    },
}

RESULTS_DIR = Path("paper6/phase3_results")
STATE_SRC   = Path("des_state.json")

des_module  = None
or_client_g = None


# ---------------------------------------------------------------------------
# Helpers (reuse from paper5 runner)
# ---------------------------------------------------------------------------

def _make_clients():
    dk = os.environ.get("DEEPSEEK_API_KEY", "")
    ok = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk or not ok:
        raise EnvironmentError(
            "DEEPSEEK_API_KEY and OPENROUTER_API_KEY must be set."
        )
    ds4 = OpenAI(api_key=dk, base_url="https://api.deepseek.com/v1")
    orr = OpenAI(
        api_key=ok,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/hstre/DES",
                         "X-Title": "DES Paper6 Phase3"},
    )
    return ds4, orr


def _tokens(text: str) -> set:
    STOP = {"the","a","an","is","are","was","were","of","in","to","for",
            "and","or","but","not","with","by","from","that","this","it",
            "be","as","at","on","if","its","so","do","can","will"}
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


def epistemic_priority(c: dict, all_claims: dict) -> int:
    bases = [h.split("[")[0] for h in c.get("history", [])]
    return bases.count("T1") + bases.count("T5") + (1 if not c.get("evidence_refs") else 0)


def is_exponential(seq: list) -> bool:
    if len(seq) < 4:
        return False
    nz = [x for x in seq if x > 0]
    return len(nz) >= 4 and all(nz[i+1]/nz[i] >= 1.5 for i in range(len(nz)-1))


def extract_run_result(state: dict, prev_total: int) -> dict:
    claims = state.get("claims", {})
    all_bases = [h.split("[")[0] for c in claims.values()
                 for h in c.get("history", [])]
    return {
        "new_claims_this_loop": max(len(claims) - prev_total, 0),
        "literature_derived": 0,
        "branches_created": sum(1 for c in claims.values() if c.get("id","").startswith("B")),
        "syntheses_produced": sum(1 for c in claims.values() if c.get("is_synthesis", False)),
        "counter_hypotheses": all_bases.count("T5"),
        "evidence_found": all_bases.count("T3") + all_bases.count("T6"),
        "contradictions_generated": all_bases.count("T2"),
        "contradictions_resolved": sum(1 for c in claims.values() if c.get("is_synthesis", False)),
        "total_contradictions": max(all_bases.count("T5"), 1),
    }


def infer_method_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["mechanism","how does","via","through"]): return "causal_mechanism"
    if any(w in q for w in ["measure","operationalize","indicator","proxy"]): return "measurement_validity"
    if any(w in q for w in ["unit","level","aggregate","individual","country"]): return "unit_of_analysis"
    if any(w in q for w in ["counterfactual","alternative","instead","without"]): return "counterfactual_baseline"
    if any(w in q for w in ["fail","failure","breakdown","exception","limit"]): return "failure_mode"
    if any(w in q for w in ["stakeholder","worker","employer","consumer","group"]): return "stakeholder_perspective"
    if any(w in q for w in ["decades","years","historical","period"]): return "temporal_validity"
    if any(w in q for w in ["condition","context","scope","when","where"]): return "scope_condition"
    return "empirical_evidence"


def infer_frame_type(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["measure","define","operationalize","proxy","validity"]): return "measurement"
    if any(w in q for w in ["mechanism","process","how does","pathway","via"]): return "mechanism"
    if any(w in q for w in ["condition","when","where","under","context","scope"]): return "scope"
    if any(w in q for w in ["cause","lead to","result in","drive","determine"]): return "causal"
    if any(w in q for w in ["compare","better","worse","more than","relative"]): return "comparison"
    if any(w in q for w in ["should","ought","policy","recommend","ethical"]): return "normative"
    return "effectiveness"


def infer_question_shape(question: str) -> str:
    q = question.lower().strip()
    if q.startswith(("does ","do ","did ")): return "does_x_cause_y"
    if q.startswith(("is ","are ","was ")): return "is_x_effective"
    if q.startswith("what evidence"): return "what_evidence"
    if q.startswith(("how does","how do")): return "how_does_x_work"
    return "is_x_effective"


def compute_metrics(state: dict, loop: int, prior_texts: list,
                    method_type: str, frame_type: str, run_result: dict) -> dict:
    claims = state.get("claims", {})
    total = len(claims)
    open_c = sum(1 for c in claims.values() if not c.get("sealed", False))
    disputed = sum(1 for c in claims.values() if c.get("status") == "disputed")
    redundant = count_redundant(claims)
    novel = count_novel(claims, prior_texts)
    dup_rate = redundant / max(total, 1)
    lit_derived = run_result.get("literature_derived", 0)
    new_claims = run_result.get("new_claims_this_loop", max(total, 1))
    qutil = sum(run_result.get(k, 0) * w for k, w in [
        ("contradictions_generated", 3), ("syntheses_produced", 2),
        ("counter_hypotheses", 2), ("evidence_found", 1), ("branches_created", 1),
    ])

    sh_result = compute_claim_metrics(state)

    return {
        "loop": loop,
        "question": state.get("seed_question", ""),
        "method_type": method_type,
        "frame_type": frame_type,
        "question_shape": infer_question_shape(state.get("seed_question", "")),
        "total_claims": total,
        "open_claims": open_c,
        "sealed_claims": total - open_c,
        "disputed_claims": disputed,
        "redundant_claims": redundant,
        "semantic_duplication_rate": dup_rate,
        "entropy": (open_c + disputed + redundant) / max(total, 1),
        "novel_claims": novel,
        "contradictions_resolved": run_result.get("contradictions_resolved", 0),
        "total_contradictions": run_result.get("total_contradictions", 1),
        "branch_growth": run_result.get("branches_created", 0),
        "lit_rate": lit_derived / max(new_claims, 1),
        "question_utility": float(qutil),
        "claim_centroid": sh_result.get("claim_centroid", {}),
        "claim_curvature": sh_result.get("claim_curvature", 0.0),
        "claim_count": sh_result.get("claim_count", 0),
    }


def check_failure(current: dict, history: list,
                  perturbation_log: list) -> str | None:
    last5  = history[-5:]  if len(history) >= 5  else history
    last10 = history[-10:] if len(history) >= 10 else history

    if len(last5) == 5 and all(m["entropy"] > 0.80 for m in last5):
        return "ENTROPY_COLLAPSE"
    if current["total_claims"] > 0 and \
       current["redundant_claims"] / current["total_claims"] > 0.60:
        return "SEMANTIC_DUPLICATION"
    if len(last10) == 10 and all(m["novel_claims"] == 0 for m in last10):
        return "NOVELTY_COLLAPSE"
    if current["total_claims"] > 500:
        return "GRAPH_TOO_LARGE"
    if check_false_escape(perturbation_log, history):
        return "FALSE_ESCAPE"
    return None


def select_next_question(state: dict, question_history: list) -> str:
    claims = state.get("claims", {})
    if not claims:
        return "LOOP_COMPLETE"

    def already_asked(q):
        return any(token_overlap(q, h) > 0.75 for h in question_history)

    def make_q(c, prefix=""):
        base = _claim_text(c).strip()
        return f"{prefix}: {base}?" if prefix else f"What is the evidence that {base}?"

    open_claims = sorted(
        [c for c in claims.values() if not c.get("sealed") and c.get("id","").startswith("C")],
        key=lambda c: epistemic_priority(c, claims), reverse=True,
    )
    for c in open_claims:
        q = make_q(c)
        if not already_asked(q):
            return q

    weak_ev = [c for c in claims.values() if c.get("sealed") and not c.get("evidence_refs")]
    for c in sorted(weak_ev, key=lambda c: c.get("confidence", 0)):
        q = make_q(c, "What evidence supports or refutes the claim that")
        if not already_asked(q):
            return q

    synth = sorted([c for c in claims.values() if c.get("is_synthesis")],
                   key=lambda c: c.get("confidence", 0), reverse=True)
    for c in synth:
        q = make_q(c, "Explore the implications of")
        if not already_asked(q):
            return q

    for c in [c for c in claims.values()
              if c.get("status") == "disputed"
              and "T1" in [h.split("[")[0] for h in c.get("history", [])]]:
        q = make_q(c, "Is there a resolution to the contradiction that")
        if not already_asked(q):
            return q

    if synth:
        q = make_q(max(synth, key=lambda c: c.get("confidence", 0)),
                   "Critically evaluate the synthesis that")
        if not already_asked(q):
            return q

    return "LOOP_COMPLETE"


def trigger_is_spl(trigger: str) -> bool:
    return "claim_curvature" in trigger or "claim_proximity" in trigger


ESCAPE_GENERATION_PROMPT = """\
You are generating diverse research questions to escape an attractor in semantic projection space.

Current question: {question}
Domain: {domain}
Attractor region: {top_relations}

Generate exactly {k} alternative research questions that:
1. Address the same domain from a different conceptual angle
2. Project into different regions of relational space (avoid evidential/effectiveness framing)
3. Introduce genuinely new sub-questions not covered by existing claims

Return ONLY {k} questions, one per line, no numbering."""


def call_llm(prompt: str, max_tokens: int = 120) -> str:
    resp = or_client_g.chat.completions.create(
        model=FALSIFIER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def generate_escape_candidates(question, attractor_centroid, state, k=5):
    top_rels = sorted(attractor_centroid.items(), key=lambda x: -x[1])[:3]
    top_rel_str = ", ".join(f"{r}({p:.2f})" for r, p in top_rels)
    raw = call_llm(ESCAPE_GENERATION_PROMPT.format(
        question=question, top_relations=top_rel_str,
        k=k, domain=state.get("seed_question", question)[:60],
    ), max_tokens=500)
    return [l.strip() for l in raw.split("\n") if l.strip() and len(l.strip()) > 20][:k]


def validate_perturbation(question, state, question_history):
    claims = state.get("claims", {})
    for prior in question_history:
        if token_overlap(question, prior) > 0.70:
            return False, "circular"
    graph_terms = set()
    for c in claims.values():
        for f in ["subject", "predicate", "object"]:
            graph_terms.update(_tokens(c.get(f, "")))
    if not (graph_terms & _tokens(question)):
        return False, "unanchored"
    return True, "admitted"


# ---------------------------------------------------------------------------
# T10: Epistemic rollback and reseed
# ---------------------------------------------------------------------------

T10_ROLLBACK_PROMPTS = {
    "causal_mechanism_shift": "What is the primary causal mechanism by which {subject} affects {object}?",
    "failure_mode_shift": "Under what conditions does the relationship between {subject} and {object} break down?",
}


def t10_rollback_and_reseed(state: dict, loop_metrics: list,
                             t10_count: int, question_history: list) -> tuple:
    if t10_count >= MAX_T10:
        return None, None, "T10_LIMIT_REACHED"
    claims = state.get("claims", {})
    seed_claims = [c for c in claims.values()
                   if c.get("history") and c["history"][0].startswith("initial")]
    if not seed_claims:
        seed_claims = list(claims.values())[:2]
    if not seed_claims:
        return None, None, "NO_SEED_CLAIMS"
    anchor = seed_claims[0]
    subj = anchor.get("subject", "the domain")
    obj = anchor.get("object", "the outcome")
    ptype = "causal_mechanism_shift" if t10_count == 0 else "failure_mode_shift"
    new_q = T10_ROLLBACK_PROMPTS[ptype].format(subject=subj, object=obj)
    rollback_to = max(0, len(loop_metrics) // 2)
    return new_q, rollback_to, ptype


# ---------------------------------------------------------------------------
# Core domain runner (P5v05 config)
# ---------------------------------------------------------------------------

def run_domain_v05(domain_id: str, seed_question: str,
                   p4_depth: int, sh_loop0: float) -> dict:
    domain_dir = RESULTS_DIR / f"{domain_id}_v05"
    domain_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {domain_id} [P5v05 — Phase 3 exploratory]")
    print(f"  {seed_question[:58]}")
    print(f"  SH(loop0)={sh_loop0:.4f} > SH*={SH_STAR_LOCKED}  P4_depth={p4_depth}")
    print(f"{'='*65}")

    question         = seed_question
    question_history = [seed_question]
    loop_metrics     = []
    perturbation_log = []
    all_prior_texts  = []
    failure_code     = None
    prev_total       = 0
    t10_count        = 0
    loop0_projection = None
    mds_frames       = set()
    ptr_breakdown    = {"spl": 0, "heuristic": 0, "fallback": 0, "total": 0}
    spl_events       = []

    for loop in range(MAX_LOOPS):
        loop_file = domain_dir / f"loop_{loop:03d}_state.json"

        if loop_file.exists():
            print(f"  [skip] loop {loop:03d} — already complete")
            with open(loop_file) as f:
                state = json.load(f)
            rr = extract_run_result(state, 0)
            prior_texts = [_claim_text(c) for c in state.get("claims", {}).values()]
            mt = infer_method_type(question)
            ft = infer_frame_type(question)
            m = compute_metrics(state, loop, all_prior_texts, mt, ft, rr)
            loop_metrics.append(m)
            all_prior_texts.extend(prior_texts)
            prev_total = len(state.get("claims", {}))
            if loop == 0:
                loop0_projection = project(seed_question)
                mds_frames.add(ft)
            question = select_next_question(state, question_history)
            if question != "LOOP_COMPLETE":
                question_history.append(question)
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
            failure_code = "DES_RUN_ERROR"
            break

        with open(STATE_SRC) as f:
            state = json.load(f)
        state["seed_question"] = seed_question
        shutil.copy(STATE_SRC, loop_file)

        run_result = extract_run_result(state, prev_total)
        prior_texts = [_claim_text(c) for c in state.get("claims", {}).values()]
        method_type = infer_method_type(question)
        frame_type  = infer_frame_type(question)
        mds_frames.add(frame_type)
        m = compute_metrics(state, loop, all_prior_texts, method_type, frame_type, run_result)

        if loop == 0:
            loop0_projection = project(seed_question)

        # Select next question candidate (v0.5: before trigger check)
        next_q_candidate = select_next_question(state, question_history)
        if next_q_candidate == "LOOP_COMPLETE":
            loop_metrics.append(m)
            loop_metrics[-1]["outcome"] = "LOOP_COMPLETE"
            print(f"  ClaimGraph exhausted — LOOP_COMPLETE")
            break

        # SPL attractor check
        spl_detected, spl_trigger, spl_ctx = detect_attractor_in_claims(
            state, next_q_candidate
        )
        loop_metrics.append(m)
        all_prior_texts.extend(prior_texts)
        prev_total = len(state.get("claims", {}))

        # Check failure AFTER appending metrics
        failure = check_failure(m, loop_metrics[:-1], perturbation_log)
        if failure:
            loop_metrics[-1]["outcome"] = failure
            failure_code = failure
            print(f"  FAILURE: {failure}")
            break

        dup_rate = m["redundant_claims"] / max(m["total_claims"], 1)
        k_g = m.get("claim_curvature", 0.0)
        print(f"  -> entropy={m['entropy']:.2f} | "
              f"claims={m['total_claims']} (open={m['open_claims']} "
              f"sealed={m['sealed_claims']}) | "
              f"novel={m['novel_claims']} dup={dup_rate:.0%} K(G)={k_g:.3f} "
              f"frame={frame_type}")

        if spl_detected:
            attractor_c = spl_ctx.get("claim_centroid", {})
            candidates = generate_escape_candidates(
                question, attractor_c, state, k=5
            )
            gen_q, score_ctx = select_escape_vector(
                candidates, attractor_c, state,
                loop0_projection=loop0_projection,
            )
            valid, gate_reason = validate_perturbation(gen_q, state, question_history)

            novel_prev = m.get("novel_claims", 0)
            event = {
                "loop": loop,
                "type": "semantic_escape",
                "trigger": spl_trigger,
                "trigger_class": "spl",
                "question": gen_q,
                "admitted": valid,
                "gate_reason": gate_reason,
                "escape_distance": score_ctx.get("escape_distance", 0.0),
                "novelty_estimate": score_ctx.get("novelty_estimate", 0.0),
                "drift_risk": score_ctx.get("drift_risk", 0.0),
                "composite_score": score_ctx.get("composite_score", 0.0),
                "novelty_produced_next_loop": 0,  # updated retroactively
            }

            if valid:
                ptr_breakdown["spl"] += 1
                ptr_breakdown["total"] += 1
                question = gen_q
                question_history.append(question)
                spl_events.append(event)
                print(f"  [SPL escape] {spl_trigger} → admitted | "
                      f"dist={score_ctx.get('escape_distance',0):.3f}")
            else:
                print(f"  [SPL escape] {spl_trigger} → {gate_reason} — fallback to ClaimGraph")
                question = next_q_candidate
                question_history.append(question)
            perturbation_log.append(event)
        else:
            question = next_q_candidate
            question_history.append(question)

        # T10 check
        if len(loop_metrics) >= 3:
            last3 = loop_metrics[-3:]
            if all(lm.get("novel_claims", 0) == 0 for lm in last3):
                new_q, rollback_to, ptype = t10_rollback_and_reseed(
                    state, loop_metrics, t10_count, question_history
                )
                if new_q and ptype != "T10_LIMIT_REACHED":
                    print(f"  [T10] ROLLBACK→{rollback_to} reseed [{ptype}]")
                    loop_metrics = loop_metrics[:rollback_to + 1]
                    question = new_q
                    question_history.append(question)
                    t10_count += 1

    loops_completed = len(loop_metrics)
    outcome = classify_outcome(loops_completed, MAX_LOOPS, failure_code, loop_metrics)

    n_spl = ptr_breakdown["spl"]
    avg_esc = (sum(e.get("escape_distance", 0) for e in spl_events) / n_spl
               if n_spl > 0 else 0.0)
    mds = len(mds_frames) / max(loops_completed, 1)
    depth_lift = loops_completed - p4_depth

    print(f"\n  {domain_id} P5v05 outcome: {outcome} | loops={loops_completed} | "
          f"depth_lift={depth_lift:+d} | SPL={n_spl} | T10={t10_count} | "
          f"escape_dist={avg_esc:.3f}")

    result = {
        "domain_id": domain_id,
        "seed_question": seed_question,
        "config": "P5v05",
        "phase": "3_exploratory",
        "sh_star_locked": SH_STAR_LOCKED,
        "sh_loop0": sh_loop0,
        "p4_depth": p4_depth,
        "p5v05_depth": loops_completed,
        "depth_lift": depth_lift,
        "outcome": outcome,
        "loops_completed": loops_completed,
        "spl_events": n_spl,
        "t10_count": t10_count,
        "avg_escape_distance": round(avg_esc, 4),
        "mds": round(mds, 3),
        "ptr": round(ptr_breakdown["total"] / max(loops_completed, 1), 3),
        "perturbation_log": perturbation_log,
        "loop_metrics": loop_metrics,
    }

    with open(domain_dir / "outcome.json", "w") as f:
        slim = json.loads(json.dumps(result))
        for lm in slim.get("loop_metrics", []):
            lm.pop("claim_centroid", None)
        json.dump(slim, f, indent=2)

    return result


def classify_outcome(loops_completed, max_loops, failure_code, loop_metrics):
    if failure_code:
        return failure_code
    if any(m.get("outcome") == "LOOP_COMPLETE" for m in loop_metrics):
        return "LOOP_COMPLETE"
    if loops_completed >= max_loops:
        return "H1_STABLE" if any(m.get("novel_claims", 0) > 0
                                   for m in loop_metrics[10:]) else "H0_DEGENERATION"
    return "INCOMPLETE"


# ---------------------------------------------------------------------------
# Phase 3 main
# ---------------------------------------------------------------------------

def run_phase3():
    global des_module, or_client_g

    print("=" * 65)
    print("Paper 6 — Phase 3: Controlled Comparison (exploratory, n=2)")
    print(f"SH* = {SH_STAR_LOCKED} (locked, not recalibrated)")
    print(f"Domains: {list(DOMAINS.keys())}")
    print("=" * 65)

    ds4, orr = _make_clients()
    or_client_g = orr

    import importlib
    import des
    des.builder_client = ds4
    des.falsifier_client = orr
    des_module = des

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for domain_id, info in DOMAINS.items():
        out_file = RESULTS_DIR / f"{domain_id}_v05" / "outcome.json"
        if out_file.exists():
            print(f"\n[skip] {domain_id} P5v05 — outcome.json exists")
            with open(out_file) as f:
                results[domain_id] = json.load(f)
            continue

        results[domain_id] = run_domain_v05(
            domain_id=domain_id,
            seed_question=info["seed"],
            p4_depth=info["p4_depth"],
            sh_loop0=info["sh_loop0"],
        )

    # Final comparison
    print("\n" + "=" * 65)
    print("Phase 3 Final Comparison")
    print("=" * 65)
    print(f"{'Domain':<8} {'SH':<8} {'P4 dep':<8} {'P5 dep':<8} {'lift':<6} {'SPL':<5} {'Outcome'}")
    print("-" * 60)

    lifts = []
    for domain_id, r in results.items():
        lift = r.get("depth_lift", 0)
        lifts.append(lift)
        print(f"{domain_id:<8} {r.get('sh_loop0',0):.4f}   "
              f"{r.get('p4_depth',0):<8} {r.get('p5v05_depth',0):<8} "
              f"{lift:+d}     {r.get('spl_events',0):<5} {r.get('outcome','?')}")

    benefit_rate = sum(1 for l in lifts if l > 0) / len(lifts) if lifts else None
    print(f"\nPerturbation benefit rate: {benefit_rate:.0%}" if benefit_rate else "")
    print(f"H2 (exploratory): {'SUPPORTED' if benefit_rate and benefit_rate >= 0.60 else 'NOT_SUPPORTED'}")
    print(f"NOTE: n=2, exploratory only — SH* unchanged at {SH_STAR_LOCKED}")

    # Update phase3_summary.json
    summary_path = RESULTS_DIR / "phase3_summary.json"
    summary = {
        "phase": "3_exploratory",
        "sh_star_locked": SH_STAR_LOCKED,
        "n_domains": len(results),
        "note": "n=2 — below pre-registered minimum of 3; exploratory only",
        "perturbation_benefit_rate": round(benefit_rate, 3) if benefit_rate else None,
        "h2_verdict": (
            "EXPLORATORY_SUPPORTED" if benefit_rate and benefit_rate >= 0.60 else
            "EXPLORATORY_NOT_SUPPORTED"
        ),
        "domains": {
            d: {k: v for k, v in r.items()
                if k not in ("perturbation_log", "loop_metrics")}
            for d, r in results.items()
        },
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved: {summary_path}")
    return results


if __name__ == "__main__":
    run_phase3()

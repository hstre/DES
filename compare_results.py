"""
Compare single-agent vs Anti-Delphi batch results.
Reads from batch_results/ and batch_results_antidelphi/
"""

import json
from pathlib import Path

QUESTIONS = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "D1", "D2", "D3", "E1", "E2"]


def load(directory: str, qid: str) -> dict:
    path = Path(directory) / f"{qid}.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def compare():
    print("\n" + "="*80)
    print("SINGLE-AGENT vs ANTI-DELPHI — COMPARISON")
    print("="*80)
    print(f"{'ID':<4} {'Metric':<28} {'Single-Agent':<18} {'Anti-Delphi':<18} {'Delta'}")
    print("-"*80)

    for qid in QUESTIONS:
        sa = load("batch_results", qid)
        ad = load("batch_results_antidelphi", qid)
        if not sa or not ad:
            print(f"{qid:<4} (missing data)")
            continue

        metrics = [
            ("Claims total",           sa["claims_total"],            ad["claims_total"]),
            ("Claims sealed",          sa["claims_sealed"],           ad["claims_sealed"]),
            ("Claims open",            sa["claims_open"],             ad["claims_open"]),
            ("Iterations",             sa["iterations"],              ad["iterations"]),
            ("T1 fired",               sa["t1_fired"],                ad["t1_fired"]),
            ("T9 fired",               sa["t9_fired"],                ad["t9_fired"]),
            ("Reframings",             sa["reframing_count"],         ad["reframing_count"]),
            ("Transitions count",      len(sa["transitions_fired"]),  len(ad["transitions_fired"])),
            ("Anti-Delphi act.",       0,                             ad.get("anti_delphi_activations", 0)),
            ("Role-gen claims",        0,                             ad.get("claims_role_generated", 0)),
        ]

        first = True
        for name, sa_val, ad_val in metrics:
            if sa_val != ad_val:
                delta = ""
                if isinstance(sa_val, (int, float)) and isinstance(ad_val, (int, float)):
                    delta = f"{ad_val - sa_val:+d}"
                label = qid if first else "    "
                print(f"{label:<4} {name:<28} {str(sa_val):<18} {str(ad_val):<18} {delta}")
                first = False
        if not first:
            print()  # blank line between questions

    # Aggregate summary
    sa_claims = sum(load("batch_results", q).get("claims_total", 0) for q in QUESTIONS)
    ad_claims = sum(load("batch_results_antidelphi", q).get("claims_total", 0) for q in QUESTIONS)
    sa_open   = sum(load("batch_results", q).get("claims_open", 0) for q in QUESTIONS)
    ad_open   = sum(load("batch_results_antidelphi", q).get("claims_open", 0) for q in QUESTIONS)
    sa_iter   = sum(load("batch_results", q).get("iterations", 0) for q in QUESTIONS)
    ad_iter   = sum(load("batch_results_antidelphi", q).get("iterations", 0) for q in QUESTIONS)
    ad_act    = sum(load("batch_results_antidelphi", q).get("anti_delphi_activations", 0) for q in QUESTIONS)
    ad_role   = sum(load("batch_results_antidelphi", q).get("claims_role_generated", 0) for q in QUESTIONS)

    print("="*80)
    print("AGGREGATE")
    print("-"*80)
    print(f"{'Metric':<32} {'Single-Agent':<18} {'Anti-Delphi':<18} {'Delta'}")
    print("-"*80)
    print(f"{'Total claims':<32} {sa_claims:<18} {ad_claims:<18} {ad_claims - sa_claims:+d}")
    print(f"{'Total open at termination':<32} {sa_open:<18} {ad_open:<18} {ad_open - sa_open:+d}")
    print(f"{'Total iterations':<32} {sa_iter:<18} {ad_iter:<18} {ad_iter - sa_iter:+d}")
    print(f"{'Anti-Delphi activations':<32} {'—':<18} {ad_act:<18}")
    print(f"{'Role-generated claims':<32} {'—':<18} {ad_role:<18}")
    print(f"{'Avg claims/run SA':<32} {sa_claims/len(QUESTIONS):<18.1f}")
    print(f"{'Avg claims/run AD':<32} {'':18} {ad_claims/len(QUESTIONS):<18.1f}")
    print(f"{'Delta claims/run':<32} {'':18} {(ad_claims - sa_claims)/len(QUESTIONS):+.1f}")


if __name__ == "__main__":
    compare()

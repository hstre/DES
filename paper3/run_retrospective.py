"""
Retrospective classification runner for Paper 3.
Applies pre-registered algorithm (classify.py v1.0) to existing state files.
"""

import json, glob, sys
from pathlib import Path
from paper3.classify import is_anomalous, classify

RESULTS_DIR = Path("paper3/batch_results_paper3_retro")
CATEGORIES = ["1", "2", "3", "4", "unclassified"]
EXPECTED = {
    "1": (0.20, 0.35),
    "2": (0.30, 0.40),
    "3": (0.10, 0.20),
    "4": (0.15, 0.25),
    "unclassified": (0.05, 0.15),
}
LABELS = {
    "1": "Genuine Hallucination",
    "2": "Weak Hypothesis",
    "3": "Cross-Domain Projection",
    "4": "Early Reframing",
    "unclassified": "unclassified",
}


def run(patterns, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    state_files = []
    for pattern in patterns:
        state_files.extend(sorted(glob.glob(pattern)))
    state_files = sorted(set(state_files))

    total_claims = 0
    anomalous_claims = 0
    classified_claims = 0
    cat_counts = {c: 0 for c in CATEGORIES}
    per_file = []

    for path in state_files:
        with open(path) as f:
            state = json.load(f)

        claims = state.get("claims", {})
        root = claims.get("C001", next(iter(claims.values()), {}))

        file_result = {
            "path": path,
            "claims": len(claims),
            "anomalous": 0,
            "classified": [],
        }

        for cid, claim in claims.items():
            total_claims += 1
            if is_anomalous(claim):
                anomalous_claims += 1
                cat = classify(claim, root)
                classified_claims += 1
                cat_counts[cat] += 1
                file_result["anomalous"] += 1
                file_result["classified"].append({"id": cid, "category": cat})

        per_file.append(file_result)

    # Compute distributions (over classified, not total)
    base = classified_claims if classified_claims else 1
    cat_pct = {c: round(cat_counts[c] / base, 4) for c in CATEGORIES}

    # Check deviations
    deviations = []
    for cat, (lo, hi) in EXPECTED.items():
        pct = cat_pct[cat]
        if pct < lo or pct > hi:
            deviations.append(
                f"  Cat {cat} ({LABELS[cat]}): {pct:.1%} outside [{lo:.0%}–{hi:.0%}]"
            )

    # Print summary
    print(f"\nState files found:    {len(state_files)}")
    print(f"Total claims:         {total_claims}")
    print(f"Anomalous claims:     {anomalous_claims} ({anomalous_claims/max(total_claims,1):.1%})")
    print(f"Classified:           {classified_claims}")
    print()
    print("Category distribution:")
    for cat in CATEGORIES:
        lo, hi = EXPECTED[cat]
        n = cat_counts[cat]
        pct = cat_pct[cat]
        flag = "  <-- OUT OF RANGE" if (pct < lo or pct > hi) else ""
        print(f"  {cat} {LABELS[cat]:<30} {n:>4} ({pct:>6.1%})  expected {lo:.0%}-{hi:.0%}{flag}")
    print()
    if deviations:
        print("Out-of-range deviations:")
        for d in deviations:
            print(d)
    else:
        print("Out-of-range deviations: none")
    print("Algorithm: NOT adjusted (pre-registered v1.0)")

    # Save results
    results = {
        "state_files": len(state_files),
        "total_claims": total_claims,
        "anomalous_claims": anomalous_claims,
        "anomalous_pct": round(anomalous_claims / max(total_claims, 1), 4),
        "classified": classified_claims,
        "category_counts": cat_counts,
        "category_pct": cat_pct,
        "deviations": deviations,
        "per_file": per_file,
    }
    with open(out_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Write summary.md
    with open(out_dir / "summary.md", "w") as f:
        f.write("# Paper 3 — Retrospective Classification\n\n")
        f.write("**Algorithm:** pre-registered v1.0 (frozen, commit bbdab7f)  \n")
        f.write(f"**State files:** {len(state_files)}  \n")
        f.write(f"**Patterns:** {patterns}\n\n")
        f.write("## Results\n\n")
        f.write(f"```\n")
        f.write(f"State files found:    {len(state_files)}\n")
        f.write(f"Total claims:         {total_claims}\n")
        f.write(f"Anomalous claims:     {anomalous_claims} ({anomalous_claims/max(total_claims,1):.1%})\n")
        f.write(f"Classified:           {classified_claims}\n\n")
        f.write(f"Category distribution:\n")
        for cat in CATEGORIES:
            lo, hi = EXPECTED[cat]
            n = cat_counts[cat]
            pct = cat_pct[cat]
            flag = "  <-- OUT OF RANGE" if (pct < lo or pct > hi) else ""
            f.write(f"  {cat} {LABELS[cat]:<30} {n:>4} ({pct:>6.1%})  "
                    f"expected {lo:.0%}-{hi:.0%}{flag}\n")
        f.write(f"\n")
        if deviations:
            f.write(f"Out-of-range deviations:\n")
            for d in deviations:
                f.write(f"{d}\n")
        else:
            f.write(f"Out-of-range deviations: none\n")
        f.write(f"Algorithm: NOT adjusted (pre-registered v1.0)\n")
        f.write(f"```\n\n")
        f.write("## Per-File Anomaly Counts\n\n")
        f.write("| File | Claims | Anomalous | Categories |\n|---|---|---|---|\n")
        for fr in per_file:
            cats = ", ".join(f"{c['id']}→{c['category']}" for c in fr["classified"][:5])
            if len(fr["classified"]) > 5:
                cats += f" (+{len(fr['classified'])-5} more)"
            f.write(f"| {Path(fr['path']).name} | {fr['claims']} | "
                    f"{fr['anomalous']} | {cats} |\n")

    print(f"\nResults saved to {out_dir}/")
    return results


RETRO_PATTERNS = [
    "batch_results/*state.json",
    "batch_results_antidelphi/*state.json",
    "batch_results_multimodel/*state.json",
    "batch_results_pilot/*state.json",
]

COMBINED_PATTERNS = RETRO_PATTERNS + [
    "paper3/batch_results_paper3_stress/*state.json",
]
COMBINED_DIR = Path("paper3/batch_results_paper3_combined")

if __name__ == "__main__":
    run(COMBINED_PATTERNS, COMBINED_DIR)

"""
v1.1 retrospective classification runner for Paper 3.
Reports standard questions (A1-E2) and stress-test (S01-S15) separately.
Uses classify.py v1.1 (post-null revision).
"""

import json, glob, sys, re
from pathlib import Path
from paper3.classify import is_anomalous, classify, ALGORITHM_VERSION, ALGORITHM_DATE, ALGORITHM_CHANGE

OUT_DIR = Path("paper3/batch_results_paper3_v1_1")

STANDARD_PATTERNS = [
    "batch_results/*state.json",
    "batch_results_antidelphi/*state.json",
    "batch_results_multimodel/*state.json",
    "batch_results_pilot/*state.json",
]
STRESS_PATTERNS = [
    "paper3/batch_results_paper3_stress/*state.json",
]
ALL_PATTERNS = STANDARD_PATTERNS + STRESS_PATTERNS

CATEGORIES = ["1", "2", "3", "4", "unclassified"]
EXPECTED = {
    "1": (0.05, 0.15),
    "2": (0.20, 0.40),
    "3": (0.05, 0.15),
    "4": (0.10, 0.25),
    "unclassified": (0.20, 0.50),
}
LABELS = {
    "1": "Genuine Hallucination",
    "2": "Weak Hypothesis",
    "3": "Cross-Domain Projection",
    "4": "Early Reframing",
    "unclassified": "unclassified",
}


def collect_files(patterns):
    files = []
    for pattern in patterns:
        files.extend(sorted(glob.glob(pattern)))
    return sorted(set(files))


def process_files(state_files):
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
        file_result = {"path": path, "claims": len(claims), "anomalous": 0, "classified": []}

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

    base = classified_claims if classified_claims else 1
    cat_pct = {c: round(cat_counts[c] / base, 4) for c in CATEGORIES}
    return {
        "total_claims": total_claims,
        "anomalous_claims": anomalous_claims,
        "classified": classified_claims,
        "cat_counts": cat_counts,
        "cat_pct": cat_pct,
        "per_file": per_file,
    }


def print_distribution(label, r):
    print(f"\n{label}")
    print(f"  State files:      {len(r['per_file'])}")
    print(f"  Total claims:     {r['total_claims']}")
    print(f"  Anomalous:        {r['anomalous_claims']} ({r['anomalous_claims']/max(r['total_claims'],1):.1%})")
    print(f"  Classified:       {r['classified']}")
    print(f"  Category distribution:")
    for cat in CATEGORIES:
        lo, hi = EXPECTED[cat]
        n = r['cat_counts'][cat]
        pct = r['cat_pct'][cat]
        flag = "  <-- OUT OF RANGE" if (pct < lo or pct > hi) else ""
        print(f"    {cat} {LABELS[cat]:<30} {n:>4} ({pct:>6.1%})  expected {lo:.0%}-{hi:.0%}{flag}")


def write_section(f, label, r):
    f.write(f"\n### {label}\n\n```\n")
    f.write(f"State files:      {len(r['per_file'])}\n")
    f.write(f"Total claims:     {r['total_claims']}\n")
    f.write(f"Anomalous:        {r['anomalous_claims']} ({r['anomalous_claims']/max(r['total_claims'],1):.1%})\n")
    f.write(f"Classified:       {r['classified']}\n\n")
    f.write(f"Category distribution:\n")
    for cat in CATEGORIES:
        lo, hi = EXPECTED[cat]
        n = r['cat_counts'][cat]
        pct = r['cat_pct'][cat]
        flag = "  <-- OUT OF RANGE" if (pct < lo or pct > hi) else ""
        f.write(f"  {cat} {LABELS[cat]:<30} {n:>4} ({pct:>6.1%})  expected {lo:.0%}-{hi:.0%}{flag}\n")
    deviations = [cat for cat in CATEGORIES
                  if r['cat_pct'][cat] < EXPECTED[cat][0] or r['cat_pct'][cat] > EXPECTED[cat][1]]
    f.write(f"\n")
    if deviations:
        f.write(f"Out-of-range: {', '.join(deviations)}\n")
    else:
        f.write(f"Out-of-range deviations: none\n")
    f.write(f"```\n")


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    std_files = collect_files(STANDARD_PATTERNS)
    stress_files = collect_files(STRESS_PATTERNS)
    all_files = sorted(set(std_files + stress_files))

    print(f"\nAlgorithm v{ALGORITHM_VERSION} ({ALGORITHM_DATE})")
    print(f"Change: {ALGORITHM_CHANGE}")

    std = process_files(std_files)
    stress = process_files(stress_files)
    combined = process_files(all_files)

    print_distribution("STANDARD questions (A1-E2)", std)
    print_distribution("STRESS-TEST questions (S01-S15)", stress)
    print_distribution("COMBINED", combined)

    print(f"\nAlgorithm: NOT adjusted based on v1.1 results.")

    # Save results.json
    results = {
        "algorithm_version": ALGORITHM_VERSION,
        "algorithm_date": ALGORITHM_DATE,
        "algorithm_change": ALGORITHM_CHANGE,
        "standard": {k: v for k, v in std.items() if k != "per_file"},
        "stress_test": {k: v for k, v in stress.items() if k != "per_file"},
        "combined": {k: v for k, v in combined.items() if k != "per_file"},
        "per_file": combined["per_file"],
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Collect diagnostic facts
    all_conf = set()
    all_status = set()
    for path in all_files:
        with open(path) as f:
            s = json.load(f)
        for c in s.get("claims", {}).values():
            all_conf.add(round(c.get("confidence", 1.0), 2))
            all_status.add(c.get("status", ""))

    # Write summary.md
    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("# Paper 3 — Retrospective Classification v1.1\n\n")
        f.write(f"**Algorithm:** v{ALGORITHM_VERSION} ({ALGORITHM_DATE})  \n")
        f.write(f"**Change:** {ALGORITHM_CHANGE}  \n")
        f.write(f"**Patterns:** standard + stress-test (114 state files total)  \n\n")

        f.write("## Version History\n\n")
        f.write("```\n")
        f.write("v1.0 (pre-registered, commit bbdab7f): 100% unclassified\n")
        f.write("Root cause: generated_by trigger flagged healthy Anti-Delphi claims\n")
        f.write("v1.1 (post-null revision): generated_by removed, pathology indicators added\n")
        f.write("Algorithm NOT adjusted based on v1.1 results.\n")
        f.write("```\n\n")

        f.write("## Results\n")
        write_section(f, "Standard Questions (A1-E2)", std)
        write_section(f, "Stress-Test Questions (S01-S15)", stress)
        write_section(f, "Combined (all 114 state files)", combined)

        f.write("\n## Diagnostic: Second Null Result\n\n")
        f.write("v1.1 also produces 0% anomalous. Root cause (different from v1.0):\n\n")
        f.write("```\n")
        f.write(f"Observed confidence values: {sorted(all_conf)}\n")
        f.write(f"  -- minimum conf = {min(all_conf):.2f}; v1.1 thresholds are 0.25 and 0.35\n")
        f.write(f"  -- no claims ever reach conf < 0.35 in final state\n\n")
        f.write(f"Observed status values: {sorted(all_status)}\n")
        f.write(f"  -- 'contradicted' and 'underspecified' never appear in sealed claims\n")
        f.write(f"  -- contradicted claims branch (T1/T5) before sealing; status resolves\n\n")
        f.write("Conclusion: DES claim lifecycle normalizes away the pathological states\n")
        f.write("that both v1.0 and v1.1 were designed to detect. The algorithm assumes\n")
        f.write("a different claim lifecycle than DES actually produces.\n")
        f.write("No further algorithm revision. Both null results are reported as-is.\n")
        f.write("```\n")

        f.write("\n## Per-File Anomaly Counts\n\n")
        f.write("| File | Claims | Anomalous | Categories |\n|---|---|---|---|\n")
        for fr in combined["per_file"]:
            cats = ", ".join(f"{c['id']}→{c['category']}" for c in fr["classified"][:5])
            if len(fr["classified"]) > 5:
                cats += f" (+{len(fr['classified'])-5} more)"
            f.write(f"| {Path(fr['path']).name} | {fr['claims']} | "
                    f"{fr['anomalous']} | {cats} |\n")

    print(f"\nResults saved to {OUT_DIR}/")


if __name__ == "__main__":
    run()

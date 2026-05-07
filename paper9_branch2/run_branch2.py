"""
paper9_branch2/run_branch2.py
Main runner: B2 → B4 → combined H1/H2/H3 summary.

B0 (merge_after=0) = Branch 1 Arch A  (EME 3.0277)
B_inf (no merge)   = Branch 1 Arch B  (EME 12.0257)

Usage:
    python paper9_branch2/run_branch2.py              # run B2 then B4
    python paper9_branch2/run_branch2.py --condition b2
    python paper9_branch2/run_branch2.py --condition b4
    python paper9_branch2/run_branch2.py --summary    # recompile from existing results
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper8.run_p8 import _init_clients
from paper9_branch2.run_condition import main_condition

B2_RESULTS_DIR = Path("paper9_branch2/batch_results_b2")
B4_RESULTS_DIR = Path("paper9_branch2/batch_results_b4")
SUMMARY_DIR    = Path("paper9_branch2/batch_results_branch2")

# Branch 1 baselines
B0_EME   = 3.0277   # Arch A: immediate merge
BINF_EME = 12.0257  # Arch B: preserve forever


def h1_verdict(eme_b2: dict, eme_b4: dict) -> str:
    """H1: ∃N* where EME(B_N*) > EME(B_inf)."""
    best = max(
        eme_b2.get("eme_score") or 0,
        eme_b4.get("eme_score") or 0,
    )
    if best is None:
        return "H1_INDETERMINATE"
    return "H1_CONFIRMED" if best > BINF_EME else "H1_REJECTED"


def h2_verdict(eme_b2: dict, eme_b4: dict) -> str:
    """
    H2: Non-monotonic optimum — EME(B0) < EME(B_N*) > EME(B_inf).
    Since B0(3.03) < B_inf(12.03), confirmed iff any N* exceeds B_inf.
    """
    return h1_verdict(eme_b2, eme_b4).replace("H1", "H2")


def h3_combined(b2_summary: dict, b4_summary: dict) -> str:
    """H3 confirmed if any condition shows new_cluster_rate > 0."""
    for s in (b2_summary, b4_summary):
        if s.get("h3_verdict") == "H3_CONFIRMED":
            return "H3_CONFIRMED"
    if (b2_summary.get("h3_verdict") == "H3_NOT_APPLICABLE"
            and b4_summary.get("h3_verdict") == "H3_NOT_APPLICABLE"):
        return "H3_NOT_APPLICABLE"
    return "H3_REJECTED"


def compile_summary(b2_summary: dict, b4_summary: dict) -> dict:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    eme_b2 = b2_summary.get("eme", {})
    eme_b4 = b4_summary.get("eme", {})
    h1     = h1_verdict(eme_b2, eme_b4)
    h2     = h2_verdict(eme_b2, eme_b4)
    h3     = h3_combined(b2_summary, b4_summary)

    summary = {
        "paper":  "9_branch2",
        "title":  "Delayed Merge",
        "b0_baseline":   {"eme_score": B0_EME,   "label": "immediate merge (Branch1 ArchA)"},
        "binf_baseline": {"eme_score": BINF_EME,  "label": "preserve forever (Branch1 ArchB)"},
        "b2": {
            "eme":           eme_b2,
            "h3_verdict":    b2_summary.get("h3_verdict"),
            "h3_avg_rate":   b2_summary.get("h3_avg_rate"),
            "n_runs":        b2_summary.get("n_runs"),
            "n_branches":    b2_summary.get("n_branches"),
            "n_post_merges": b2_summary.get("n_post_merges"),
        },
        "b4": {
            "eme":           eme_b4,
            "h3_verdict":    b4_summary.get("h3_verdict"),
            "h3_avg_rate":   b4_summary.get("h3_avg_rate"),
            "n_runs":        b4_summary.get("n_runs"),
            "n_branches":    b4_summary.get("n_branches"),
            "n_post_merges": b4_summary.get("n_post_merges"),
        },
        "verdicts": {"H1": h1, "H2": h2, "H3": h3},
    }

    with open(SUMMARY_DIR / "branch2_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    _write_summary_md(summary)
    print(f"\n[branch2] summary → {SUMMARY_DIR}/branch2_summary.json")
    return summary


def _write_summary_md(s: dict) -> None:
    eb2 = s["b2"]["eme"]
    eb4 = s["b4"]["eme"]
    h1  = s["verdicts"]["H1"]
    h2  = s["verdicts"]["H2"]
    h3  = s["verdicts"]["H3"]

    lines = [
        "<!-- paper9_branch2/batch_results_branch2/summary -->",
        "<!-- Paper 9 Branch 2 — Delayed Merge -->",
        "",
        "# Paper 9 Branch 2 — Delayed Merge",
        "",
        "## Condition Results",
        "",
        "| Condition | merge_after | EME score | Clusters | Total claims |",
        "|-----------|-------------|-----------|----------|--------------|",
        f"| B0 (Arch A baseline) | 0 | {s['b0_baseline']['eme_score']} | 4 | 65 |",
        f"| B2 | 2 | {eb2.get('eme_score','N/A')} | {eb2.get('cluster_count','N/A')} | {eb2.get('total_claims','N/A')} |",
        f"| B4 | 4 | {eb4.get('eme_score','N/A')} | {eb4.get('cluster_count','N/A')} | {eb4.get('total_claims','N/A')} |",
        f"| B_inf (Arch B baseline) | ∞ | {s['binf_baseline']['eme_score']} | 16 | 380 |",
        "",
        "## Hypothesis Verdicts",
        "",
        "| Hypothesis | Verdict |",
        "|------------|---------|",
        f"| H1: ∃N* where EME(B_N*) > EME(B_inf)=12.0257 | {h1} |",
        f"| H2: Non-monotonic — B0 < B_N* > B_inf | {h2} |",
        f"| H3: Post-merge new_cluster_rate > 0 | {h3} |",
        "",
        "## H3 Details",
        "",
        "| Condition | H3 verdict | avg new_cluster_rate |",
        "|-----------|------------|---------------------|",
        f"| B2 | {s['b2'].get('h3_verdict','N/A')} | {s['b2'].get('h3_avg_rate','N/A')} |",
        f"| B4 | {s['b4'].get('h3_verdict','N/A')} | {s['b4'].get('h3_avg_rate','N/A')} |",
    ]

    with open(SUMMARY_DIR / "summary.md", "w") as f:
        f.write("\n".join(lines))


def load_summaries_and_compile():
    b2_path = B2_RESULTS_DIR / "condition_summary.json"
    b4_path = B4_RESULTS_DIR / "condition_summary.json"
    if not b2_path.exists() or not b4_path.exists():
        print(f"ERROR: summary files not found ({b2_path}, {b4_path})")
        sys.exit(1)
    with open(b2_path) as f:
        b2_summary = json.load(f)
    with open(b4_path) as f:
        b4_summary = json.load(f)
    return compile_summary(b2_summary, b4_summary)


def run_all():
    _init_clients()

    print("\n" + "="*70)
    print("Paper 9 Branch 2 — Delayed Merge")
    print("Condition B2: merge after 2 branch loops")
    print("="*70)
    b2_summary = main_condition(2, B2_RESULTS_DIR)

    print("\n" + "="*70)
    print("Condition B4: merge after 4 branch loops")
    print("="*70)
    b4_summary = main_condition(4, B4_RESULTS_DIR)

    return compile_summary(b2_summary, b4_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=["b2", "b4"], default=None)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        load_summaries_and_compile()
    elif args.condition == "b2":
        _init_clients()
        main_condition(2, B2_RESULTS_DIR)
    elif args.condition == "b4":
        _init_clients()
        main_condition(4, B4_RESULTS_DIR)
    else:
        run_all()

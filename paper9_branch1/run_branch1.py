"""
paper9_branch1/run_branch1.py
Main runner: Architecture A → Architecture B → combined summary.

Usage:
    python paper9_branch1/run_branch1.py
    python paper9_branch1/run_branch1.py --arch a
    python paper9_branch1/run_branch1.py --arch b
    python paper9_branch1/run_branch1.py --summary
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import paper9_branch1.run_arch_a as _arch_a
import paper9_branch1.run_arch_b as _arch_b
from paper8.run_p8 import _init_clients

SUMMARY_DIR = Path("paper9_branch1/batch_results_branch1")
ARM_B_BASELINE_EME = 2.8195


def run_all():
    _init_clients()
    print("\n" + "="*70)
    print("Paper 9 Branch 1 — Parallel Operator Expansion")
    print("Architecture A: Merged Branch")
    print("="*70)
    a_summary = _arch_a.main()

    print("\n" + "="*70)
    print("Architecture B: Preserved Branches")
    print("="*70)
    b_summary = _arch_b.main()

    return compile_summary(a_summary, b_summary)


def compile_summary(a_summary: dict, b_summary: dict) -> dict:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    eme_a = a_summary.get("eme", {})
    eme_b = b_summary.get("eme", {})

    summary = {
        "paper":            "9_branch1",
        "title":            "Parallel Operator Expansion",
        "arch_a": {
            "eme":          eme_a,
            "h1_verdict":   a_summary.get("h1_verdict"),
            "h1_threshold": a_summary.get("h1_threshold"),
            "n_runs":       a_summary.get("n_runs"),
        },
        "arch_b": {
            "eme":          eme_b,
            "h2_verdict":   b_summary.get("h2_verdict"),
            "h3_verdict":   b_summary.get("h3_verdict"),
            "n_runs":       b_summary.get("n_runs"),
            "n_branches":   b_summary.get("n_branches"),
        },
        "arm_b_baseline":   ARM_B_BASELINE_EME,
        "verdicts": {
            "H1": a_summary.get("h1_verdict"),
            "H2": b_summary.get("h2_verdict"),
            "H3": b_summary.get("h3_verdict"),
        },
    }

    with open(SUMMARY_DIR / "branch1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    _write_summary_md(summary)
    print(f"\n[branch1] summary → {SUMMARY_DIR}/branch1_summary.json")
    return summary


def _write_summary_md(s: dict) -> None:
    eme_a = s["arch_a"]["eme"]
    eme_b = s["arch_b"]["eme"]
    ea    = eme_a.get("eme_score", "N/A")
    eb    = eme_b.get("eme_score", "N/A")
    h1    = s["verdicts"]["H1"]
    h2    = s["verdicts"]["H2"]
    h3    = s["verdicts"]["H3"]

    lines = [
        "<!-- paper9_branch1/batch_results_branch1/summary -->",
        "<!-- Paper 9 Branch 1 — Parallel Operator Expansion -->",
        "",
        "# Paper 9 Branch 1 — Parallel Operator Expansion",
        "",
        "## Architecture Results",
        "",
        f"| Architecture | EME score | Clusters | Total claims |",
        f"|-------------|-----------|----------|--------------|",
        f"| Arch A (merged) | {ea} | {eme_a.get('cluster_count','N/A')} | {eme_a.get('total_claims','N/A')} |",
        f"| Arch B (branches) | {eb} | {eme_b.get('cluster_count','N/A')} | {eme_b.get('total_claims','N/A')} |",
        f"| Arm B baseline (Paper 8) | {s['arm_b_baseline']} | 4 | 65 |",
        "",
        "## Hypothesis Verdicts",
        "",
        f"| Hypothesis | Verdict |",
        f"|------------|---------|",
        f"| H1: EME(arch_a) > baseline × 1.2 | {h1} |",
        f"| H2: EME(arch_b) > EME(arch_a) | {h2} |",
        f"| H3: EME/loop(arch_b) > EME/loop(arm_b) | {h3} |",
        "",
        "## Negative Findings",
        "- arch_a_fallback triggered: see per-run operator_log",
        f"- Arch B branches spawned: {s['arch_b'].get('n_branches', 'N/A')}",
    ]

    with open(SUMMARY_DIR / "summary.md", "w") as f:
        f.write("\n".join(lines))


def load_summaries_and_compile():
    """Recompile summary from existing arch_a/arch_b summary files."""
    a_path = Path("paper9_branch1/batch_results_arch_a/arch_a_summary.json")
    b_path = Path("paper9_branch1/batch_results_arch_b/arch_b_summary.json")

    if not a_path.exists() or not b_path.exists():
        print(f"ERROR: summary files not found ({a_path}, {b_path})")
        sys.exit(1)

    with open(a_path) as f:
        a_summary = json.load(f)
    with open(b_path) as f:
        b_summary = json.load(f)

    return compile_summary(a_summary, b_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["a", "b"], default=None)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        load_summaries_and_compile()
    elif args.arch == "a":
        _init_clients()
        _arch_a.main()
    elif args.arch == "b":
        _init_clients()
        _arch_b.main()
    else:
        run_all()

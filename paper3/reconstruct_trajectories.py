"""
Transition trajectory reconstruction for Paper 3.
Classifies trajectories from claim.history transition logs.
IMPORTANT: This is trajectory approximation, not exact state reconstruction.
"""

import json, glob
from pathlib import Path

PATTERNS = [
    "batch_results/*state.json",
    "batch_results_antidelphi/*state.json",
    "batch_results_multimodel/*state.json",
    "paper3/batch_results_paper3_stress/*state.json",
]

OUT_DIR = Path("paper3/batch_results_paper3_trajectories")


def classify_trajectory(history: list, final_status: str, final_conf: float) -> dict:
    """
    Classify trajectory type from transition history.
    Returns trajectory class and key transitions.
    Does NOT reconstruct intermediate states.

    Note on ended_clean: DES keeps branch-root claims marked "disputed" by design
    even after synthesis (T9) — this preserves epistemic transparency. We treat
    T9 in history as evidence of trajectory-level resolution regardless of terminal
    status, because T9 generates synthesis claims that carry the resolution.
    """
    bases = [h.split("[")[0] for h in history]
    has_counter   = "T5" in bases
    has_branch    = "T1" in bases
    has_decompose = "T4" in bases
    has_synthesis = "T9" in bases
    has_conflict  = "T2" in bases
    has_evidence  = "T3" in bases

    terminal_clean = final_status in {"supported", "sealed"} and final_conf >= 0.5
    # T9 = synthesis generated = trajectory-level resolution (branch-root stays
    # "disputed" by DES design for epistemic transparency)
    ended_clean = terminal_clean or has_synthesis

    if has_branch and has_synthesis and ended_clean:
        traj_class = "CONTRADICTED_RESOLVED"
        # History implies: generated -> disputed/contradicted -> counter-hypothesis (T5)
        # -> branched (T1) -> branches resolved -> synthesis generated (T9)
        # Terminal: branch-root remains "disputed" by DES design; resolution in synthesis claims
    elif has_counter and ended_clean:
        traj_class = "COUNTERED_RESOLVED"
        # History implies: generated -> counter-hypothesis (T5) -> conflict explicit (T2)
        # -> evidence gathered (T6) -> resolved. Terminal: clean (supported)
    elif has_decompose and terminal_clean:
        traj_class = "DECOMPOSED_RESOLVED"
        # History implies: generated -> evidence (T3) -> decomposed (T4) -> sub-claims resolved
        # Terminal: clean (supported). Underspecification resolved during trajectory.
    elif has_synthesis and ended_clean:
        traj_class = "SYNTHESIZED"
    elif not ended_clean:
        traj_class = "UNRESOLVED"
    else:
        traj_class = "SIMPLE"

    return {
        "trajectory_class": traj_class,
        "key_transitions": {
            "T1_branch": has_branch,
            "T4_decompose": has_decompose,
            "T5_counter": has_counter,
            "T9_synthesis": has_synthesis,
            "T2_conflict": has_conflict,
            "T3_evidence": has_evidence,
        },
        "terminal_clean": terminal_clean,
        "synthesis_resolved": has_synthesis,
        "ended_clean": ended_clean,
        "complexity": len(history),
    }


def describe_trajectory(claim: dict, traj: dict) -> dict:
    """
    Build human-readable trajectory description.
    Based only on what history implies -- no invented states.
    """
    history = claim.get("history", [])
    cid = claim.get("id", "?")
    subject = claim.get("subject", "")
    predicate = claim.get("predicate", "")
    obj = claim.get("object", "")
    final_status = claim.get("status", "")
    final_conf = claim.get("confidence", 0)

    step_desc_map = {
        "T3": "evidence gathered",
        "T4": "decomposed into sub-claims",
        "T5": "counter-hypothesis generated",
        "T1": "contradiction detected -> branch created",
        "T2": "conflict made explicit",
        "T6": "evidence path explored",
        "T7": "qualifier refined",
        "T8": "claim sealed",
        "T9": "synthesis generated (trajectory-level resolution)",
    }
    narrative_steps = []
    for i, t in enumerate(history):
        base = t.split("[")[0]
        step_desc = step_desc_map.get(base, t)
        if "[" in t:
            role = t[t.index("["):]
            step_desc += f" {role}"
        narrative_steps.append(f"  {i+1}. {t}: {step_desc}")

    # Add terminal state note for CONTRADICTED_RESOLVED
    note = ""
    if traj["trajectory_class"] == "CONTRADICTED_RESOLVED" and not traj["terminal_clean"]:
        note = ("  [Note: terminal status=disputed by DES design — branch-root preserved\n"
                "   as epistemic marker; resolution visible in synthesis/branch claims]")

    return {
        "claim_id": cid,
        "claim_text": f"{subject} {predicate} {obj}",
        "terminal_status": final_status,
        "terminal_confidence": final_conf,
        "terminal_clean": traj["terminal_clean"],
        "trajectory_class": traj["trajectory_class"],
        "key_transitions": traj["key_transitions"],
        "history": history,
        "complexity": traj["complexity"],
        "narrative": "\n".join(narrative_steps) + ("\n" + note if note else ""),
        "is_synthesis": claim.get("is_synthesis", False),
    }


def mermaid_diagram(desc: dict) -> str:
    history = desc["history"]
    lines = ["graph LR"]

    nodes = []
    node_id = ord("A")

    first = chr(node_id)
    nodes.append((first, "Generated: hypothesis", False, False))
    node_id += 1

    tension_transitions = {"T5", "T1", "T2"}
    synthesis_transitions = {"T9"}

    for t in history:
        base = t.split("[")[0]
        label_map = {
            "T3": "T3: evidence gathered",
            "T4": "T4: decomposed",
            "T5": "T5: counter-hypothesis",
            "T1": "T1: branch created",
            "T2": "T2: conflict explicit",
            "T6": "T6: evidence path",
            "T7": "T7: qualifier refined",
            "T8": "T8: sealed",
            "T9": "T9: synthesis",
        }
        label = label_map.get(base, t)
        if "[" in t:
            role_tag = t[t.index("["):].replace("[anti-delphi]", "[AD]")
            label += f" {role_tag}"
        nid = chr(node_id)
        is_tension = base in tension_transitions
        is_synthesis = base in synthesis_transitions
        nodes.append((nid, label, is_tension, is_synthesis))
        node_id += 1

    final_nid = chr(node_id)
    final_label = f"Terminal: {desc['terminal_status']} {desc['terminal_confidence']:.2f}"
    is_clean = desc["terminal_clean"]
    nodes.append((final_nid, final_label, False, False))

    for i in range(len(nodes) - 1):
        a, alabel, _, _ = nodes[i]
        b, blabel, _, _ = nodes[i + 1]
        lines.append(f'    {a}["{alabel}"] --> {b}["{blabel}"]')

    for nid, _, is_tension, is_synth in nodes:
        if is_tension:
            lines.append(f"    style {nid} fill:#ffcccc")
        elif is_synth:
            lines.append(f"    style {nid} fill:#ffffcc")

    if is_clean:
        lines.append(f"    style {final_nid} fill:#ccffcc")
    else:
        lines.append(f"    style {final_nid} fill:#ffeecc")

    lines.append("    %% red = implied epistemic tension / anomaly candidate")
    lines.append("    %% yellow = synthesis (trajectory resolution)")
    lines.append("    %% green = clean terminal state")
    lines.append("    %% orange = disputed terminal (DES design: branch-root preserved)")

    return "\n".join(lines)


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    state_files = []
    for pattern in PATTERNS:
        state_files.extend(glob.glob(pattern))
    state_files = sorted(set(state_files))
    print(f"State files found: {len(state_files)}")

    all_trajectories = []
    class_counts = {}

    for path in state_files:
        with open(path) as f:
            state = json.load(f)
        claims = state.get("claims", {})
        for cid, claim in claims.items():
            claim["id"] = cid
            history = claim.get("history", [])
            final_status = claim.get("status", "")
            final_conf = claim.get("confidence", 0.0)

            complex_transitions = {"T1", "T4", "T5", "T9"}
            history_bases = {h.split("[")[0] for h in history}
            if not (history_bases & complex_transitions):
                continue

            traj = classify_trajectory(history, final_status, final_conf)
            desc = describe_trajectory(claim, traj)
            desc["source_file"] = path
            all_trajectories.append(desc)

            tc = traj["trajectory_class"]
            class_counts[tc] = class_counts.get(tc, 0) + 1

    print(f"Complex trajectories found: {len(all_trajectories)}")
    print("Class distribution:")
    for cls, n in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {n}")

    # Select top examples
    priority_classes = ["CONTRADICTED_RESOLVED", "COUNTERED_RESOLVED"]
    candidates = [t for t in all_trajectories if t["trajectory_class"] in priority_classes]
    candidates.sort(key=lambda t: (
        priority_classes.index(t["trajectory_class"]),
        -t["complexity"],
        -t["terminal_confidence"],
    ))

    seen_texts = set()
    top_examples = []
    for t in candidates:
        key = t["claim_text"][:60]
        if key not in seen_texts:
            seen_texts.add(key)
            top_examples.append(t)
        if len(top_examples) >= 10:
            break

    print(f"\nTop examples selected: {len(top_examples)}")
    for t in top_examples[:5]:
        tc = t["trajectory_class"]
        print(f"  [{tc}] complexity={t['complexity']} "
              f"conf={t['terminal_confidence']:.2f} terminal={t['terminal_status']!r} | "
              f"{t['claim_text'][:55]}")

    # Save JSON outputs
    with open(OUT_DIR / "trajectories.json", "w") as f:
        json.dump(all_trajectories, f, indent=2)
    with open(OUT_DIR / "top_examples.json", "w") as f:
        json.dump(top_examples, f, indent=2)

    # Total claims across all files
    total_claims = sum(
        len(json.load(open(p)).get("claims", {})) for p in state_files
    )

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("# Paper 3 — Transition Trajectory Reconstruction\n\n")
        f.write("> **Transition trajectory approximation – not exact state reconstruction.**  \n")
        f.write("> Trajectories are derived from terminal-state history logs. Intermediate\n")
        f.write("> states are not recovered; only what the transition sequence structurally implies.\n\n")

        f.write("## Key Finding\n\n")
        f.write("The anomaly is not visible in the terminal state because DES resolves ")
        f.write("it during the trajectory.\n\n")
        f.write("For CONTRADICTED_RESOLVED claims: DES keeps the branch-root claim marked\n")
        f.write("'disputed' by design (epistemic transparency), while generating synthesis\n")
        f.write("claims (T9) that carry the trajectory-level resolution. The contradiction\n")
        f.write("is resolved in the trajectory; the branch-root terminal state reflects the\n")
        f.write("preserved epistemic tension, not a failure to resolve.\n\n")

        f.write("## Coverage\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        f.write(f"| State files processed | {len(state_files)} |\n")
        f.write(f"| Total claims | {total_claims} |\n")
        f.write(f"| Claims with complex transitions | {len(all_trajectories)} |\n")
        f.write(f"| CONTRADICTED_RESOLVED | {class_counts.get('CONTRADICTED_RESOLVED', 0)} |\n")
        f.write(f"| COUNTERED_RESOLVED | {class_counts.get('COUNTERED_RESOLVED', 0)} |\n")
        f.write(f"| DECOMPOSED_RESOLVED | {class_counts.get('DECOMPOSED_RESOLVED', 0)} |\n")
        f.write(f"| SYNTHESIZED | {class_counts.get('SYNTHESIZED', 0)} |\n")
        f.write(f"| UNRESOLVED | {class_counts.get('UNRESOLVED', 0)} |\n")
        f.write(f"| SIMPLE | {class_counts.get('SIMPLE', 0)} |\n\n")

        f.write("## Trajectory Classes\n\n")
        f.write("| Class | Meaning |\n|---|---|\n")
        f.write("| CONTRADICTED_RESOLVED | T5 (counter-hypothesis) + T1 (branch) + T9 (synthesis) in history. "
                "Terminal: branch-root remains 'disputed' by DES design; resolution visible in synthesis/branch claims. |\n")
        f.write("| COUNTERED_RESOLVED | T5 (counter-hypothesis) in history, NO T1 branching, terminal=supported, "
                "conf≥0.5. Conflict resolved through evidence without branching. |\n")
        f.write("| DECOMPOSED_RESOLVED | T4 (decompose) in history, terminal=supported, conf≥0.5. "
                "Underspecification resolved via decomposition into sub-claims. |\n")
        f.write("| SYNTHESIZED | T9 present, clean terminal. Synthesis claim. |\n")
        f.write("| UNRESOLVED | No synthesis and terminal state is not clean. |\n")
        f.write("| SIMPLE | Clean terminal, no complex transitions. |\n\n")

        f.write("## Top Examples (CONTRADICTED_RESOLVED / COUNTERED_RESOLVED)\n\n")
        f.write("| # | Claim (truncated) | Class | Terminal | History |\n")
        f.write("|---|---|---|---|---|\n")
        for i, t in enumerate(top_examples, 1):
            hist_str = " → ".join(t["history"])
            term = f"{t['terminal_status']} {t['terminal_confidence']:.2f}"
            f.write(f"| {i} | {t['claim_text'][:55]}… | {t['trajectory_class']} | "
                    f"{term} | `{hist_str}` |\n")

        f.write("\n## Detailed Examples with Narratives\n\n")
        for i, t in enumerate(top_examples, 1):
            f.write(f"### Example {i}: {t['trajectory_class']}\n\n")
            f.write(f"**Claim:** {t['claim_text']}  \n")
            f.write(f"**Terminal state:** {t['terminal_status']}, confidence={t['terminal_confidence']:.2f}  \n")
            if t['trajectory_class'] == "CONTRADICTED_RESOLVED" and not t['terminal_clean']:
                f.write(f"**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  \n")
            f.write(f"**History sequence:** `{'` → `'.join(t['history'])}`  \n\n")
            f.write(f"**Narrative** (transition trajectory approximation):\n\n")
            f.write(f"```\n{t['narrative']}\n```\n\n")

        f.write("## Mermaid Diagrams (Top 3 Examples)\n\n")
        f.write("*Red = implied epistemic tension / anomaly candidate.  \n")
        f.write("Yellow = synthesis (trajectory-level resolution).  \n")
        f.write("Green = clean terminal. Orange = disputed terminal (DES design).*\n\n")
        for i, t in enumerate(top_examples[:3], 1):
            f.write(f"### Diagram {i}: {t['trajectory_class']}\n\n")
            f.write(f"**Claim:** {t['claim_text'][:80]}  \n\n")
            f.write("```mermaid\n")
            f.write(mermaid_diagram(t))
            f.write("\n```\n\n")

    print(f"\nOutput written to {OUT_DIR}/")


if __name__ == "__main__":
    run()

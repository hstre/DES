"""
Three-way comparison: single-agent vs AD-DS4 vs multi-model combos.

Reads from:
  batch_results/              (single-agent baseline)
  batch_results_antidelphi/   (single-model AD baseline)
  batch_results_multimodel/   (this run: DS4_DS4, DS4_GPT4o, GPT4o_DS4, Claude_Cl)
"""

import json
from pathlib import Path
from collections import Counter

QUESTIONS = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "D1", "D2", "D3", "E1", "E2"]

MM_COMBOS = ["DS4_DS4", "DS4_GPT4o", "GPT4o_DS4", "Claude_Cl"]


def load_sa(qid: str) -> dict:
    p = Path("batch_results") / f"{qid}.json"
    return json.load(open(p)) if p.exists() else {}


def load_ad(qid: str) -> dict:
    p = Path("batch_results_antidelphi") / f"{qid}.json"
    return json.load(open(p)) if p.exists() else {}


def load_mm(combo_id: str, qid: str) -> dict:
    p = Path("batch_results_multimodel") / f"{combo_id}_{qid}.json"
    return json.load(open(p)) if p.exists() else {}


def topology_of(d: dict) -> str:
    """Derive topology for SA/AD runs that predate the topology field."""
    if not d:
        return "?"
    if d.get("topology"):
        return d["topology"]
    t1 = d.get("t1_fired", False)
    t2 = d.get("t2_fired", False)
    t9 = d.get("t9_fired", False)
    trans = d.get("transitions_fired", [])
    t4 = "T4" in trans
    if t1 and t9:
        return "contested"
    elif t2 and not t1:
        return "T2_path"
    elif t4 and not t1:
        return "branched"
    else:
        return "linear"


def compare():
    print("\n" + "=" * 110)
    print("THREE-WAY COMPARISON: Single-Agent | AD-DS4 | DS4_DS4 | DS4_GPT4o | GPT4o_DS4 | Claude_Cl")
    print("=" * 110)

    COLS = ["SA", "AD", "DS4_DS4", "DS4_GPT4o", "GPT4o_DS4", "Claude_Cl"]
    W = 10  # column width

    def row(label, values):
        vals = "".join(str(v).ljust(W) for v in values)
        print(f"  {label:<22} {vals}")

    for qid in QUESTIONS:
        sa = load_sa(qid)
        ad = load_ad(qid)
        mm = {c: load_mm(c, qid) for c in MM_COMBOS}

        print(f"\n{'─'*110}")
        print(f"  {qid}: {sa.get('question', '')[:70]}")
        print(f"  {'Metric':<22} " + "".join(c.ljust(W) for c in COLS))
        print(f"  {'─'*22} " + "─" * (W * len(COLS)))

        def vals(field, default="-"):
            sa_v  = sa.get(field, default)
            ad_v  = ad.get(field, default)
            mm_vs = [mm[c].get(field, default) if mm[c] else default for c in MM_COMBOS]
            return [sa_v, ad_v] + mm_vs

        row("claims_total",  vals("claims_total"))
        row("iterations",    vals("iterations"))
        row("t1_fired",      [str(sa.get("t1_fired","-")), str(ad.get("t1_fired","-"))]
                              + [str(mm[c].get("t1_fired","-")) if mm[c] else "-" for c in MM_COMBOS])
        row("t2_fired",      ["-", "-"]
                              + [str(mm[c].get("t2_fired","-")) if mm[c] else "-" for c in MM_COMBOS])
        row("topology",      [topology_of(sa), topology_of(ad)]
                              + [mm[c].get("topology","?") if mm[c] else "?" for c in MM_COMBOS])
        row("synth_conf",    ["-", "-"]
                              + [f"{mm[c].get('synthesis_confidence',0):.3f}" if mm[c] else "-"
                                 for c in MM_COMBOS])
        row("AD_activations",["-", str(ad.get("anti_delphi_activations","-"))]
                              + [str(mm[c].get("anti_delphi_activations","-")) if mm[c] else "-"
                                 for c in MM_COMBOS])

    # ── Aggregate ────────────────────────────────────────────────────────────
    print("\n" + "=" * 110)
    print("AGGREGATE STATISTICS")
    print("─" * 110)
    print(f"  {'Metric':<28} " + "".join(c.ljust(W) for c in COLS))
    print(f"  {'─'*28} " + "─" * (W * len(COLS)))

    def agg(fn):
        sa_v  = fn([load_sa(q) for q in QUESTIONS if load_sa(q)])
        ad_v  = fn([load_ad(q) for q in QUESTIONS if load_ad(q)])
        mm_vs = [fn([load_mm(c, q) for q in QUESTIONS if load_mm(c, q)]) for c in MM_COMBOS]
        return [sa_v, ad_v] + mm_vs

    def avg(lst, key):
        vals = [d[key] for d in lst if d and key in d]
        return f"{sum(vals)/len(vals):.1f}" if vals else "-"

    def rate(lst, key):
        vals = [d[key] for d in lst if d and key in d]
        return f"{sum(vals)/len(vals)*100:.0f}%" if vals else "-"

    def topo_dist(lst):
        tc = Counter(topology_of(d) for d in lst if d)
        n = len(lst)
        return f"C{tc.get('contested',0)}/T{tc.get('T2_path',0)}/B{tc.get('branched',0)}/L{tc.get('linear',0)}"

    sa_all  = [load_sa(q) for q in QUESTIONS]
    ad_all  = [load_ad(q) for q in QUESTIONS]
    mm_all  = {c: [load_mm(c, q) for q in QUESTIONS] for c in MM_COMBOS}

    def r2(label, fn):
        vals = [fn(sa_all), fn(ad_all)] + [fn(mm_all[c]) for c in MM_COMBOS]
        print(f"  {label:<28} " + "".join(str(v).ljust(W) for v in vals))

    r2("Avg claims/run",   lambda lst: avg(lst, "claims_total"))
    r2("Avg iterations",   lambda lst: avg(lst, "iterations"))
    r2("T1 rate",          lambda lst: rate(lst, "t1_fired"))
    r2("T9 rate",          lambda lst: rate(lst, "t9_fired"))
    r2("T2 rate",          lambda lst: rate(lst, "t2_fired"))
    r2("Topology dist",    topo_dist)
    r2("Avg synth_conf",   lambda lst: avg([d for d in lst if d and d.get("synthesis_confidence")],
                                           "synthesis_confidence"))
    r2("Avg AD act.",      lambda lst: avg(lst, "anti_delphi_activations"))

    print()


if __name__ == "__main__":
    compare()

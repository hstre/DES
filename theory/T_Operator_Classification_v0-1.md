# T1–T9 Operator Classification
# Mode × Branch-Effect Analysis of the DES Transition Table

**Version:** v0.1  
**Date:** 2026-05-10  
**Source files:** `des.py` (lines 578–1030), `results.md` (25-iteration trace), `DES_Paper9_Branch1_DesignMemo_v0-1.md`, `DES_Paper9_Branch2_DesignMemo_v0-2.md`, `DES_Paper4_DesignMemo_v0-1.md`

---

## Summary

This memo classifies all nine DES transition operators along two axes:

- **Mode** — does the operator expand semantic space (divergent), contract/refine it (convergent), neither (neutral), or both depending on context (mixed)?
- **Branch-Effect** — does the operator create new branches, preserve existing ones, merge branches, terminate a branch, or leave branch topology unchanged (unspecified)?

The classification finds that the two-axis framework has genuine explanatory power but is not complete: five of nine operators have `branch_effect=unspecified`, preservation is achieved passively rather than by any operator, and one axis cell (divergent + merge) is structurally constrained to be empty by the DES design. Three implementation inconsistencies are documented. Machine-readable output: `t_operator_table.json`.

---

## Method

1. Read the canonical trigger conditions and operation descriptions from `README.md` T1–T9 table.
2. Read the implementation of each operator in `des.py` (lines 578–1030).
3. Read the `results.md` empirical trace (25 iterations on UBI fiscal sustainability question) for sequencing evidence.
4. Cross-referenced with design memos (Paper 4, Paper 9 Branch 1+2) for architectural intent.
5. Applied Mode classification: divergent = new claims created OR new semantic directions opened; convergent = claims resolved, grounded, or closed; neutral = metadata-only change; mixed = context-dependent.
6. Applied Branch-Effect classification: create = new B- or C-prefixed claims added to graph; merge = multiple branch trajectories combined; terminate = claim.sealed=True; preserve = explicit mechanism keeping branches open; unspecified = no direct branch topology change.
7. Assigned confidence per cell based on clarity of implementation evidence.

---

## Classification Table

| Op | Name | Mode | Branch-Effect | Mode Conf | BE Conf |
|----|------|------|---------------|-----------|---------|
| T1 | resolve_conflict | divergent | create | high | high |
| T2 | make_conflict_explicit | neutral | unspecified | high | high |
| T3 | request_evidence | mixed | unspecified | medium | high |
| T4 | decompose_claim | divergent | create | high | high |
| T5 | generate_counter_hypothesis | divergent | unspecified | high | medium |
| T6 | explore_evidence_path | convergent | unspecified | high | high |
| T7 | refine_qualifier | convergent | unspecified | medium | high |
| T8 | seal_claim | convergent | terminate | high | high |
| T9 | trigger_reframing | convergent | merge | high | high |

Uncertain cells: T3 (mode), T5 (branch_effect), T7 (mode). See `uncertain_cells_report.md`.

---

## Findings by Axis

### Mode Axis

**Divergent operators (T1, T4, T5):** All three create new semantic content. T1 and T4 create new claim nodes explicitly; T5 creates a counter-claim and sets parent.conflict=True, which drives the T5→T2→T1 cascade that eventually creates branches. The divergent operators cluster at HIGH and MEDIUM priority (T1=CRITICAL, T4=HIGH, T5=MEDIUM), suggesting DES prioritizes semantic expansion early in the iteration cycle.

**Convergent operators (T6, T7, T8, T9):** T6 and T8 are unambiguously convergent: T6 grounds hypotheses in evidence, T8 irrevocably seals claims. T7 adds precision qualifiers (convergent in the scope-narrowing sense, with medium confidence — see uncertain_cells_report.md). T9 synthesizes branches into a unified claim — the canonical convergent terminal operation.

**Neutral (T2):** Pure bookkeeping. Appends a CONFLICT evidence_ref and flips flags. No semantic content generated or closed.

**Mixed (T3):** The only mixed operator. For C-prefixed claims, T3 adds simulated evidence and may raise confidence (weakly convergent). For B-prefixed claims, T3 calls `evaluate_branch_claim()`, which can force status='supported', confidence=0.85 regardless of content — a stronger, forced convergence. The B-claim pathway makes T3's mode context-dependent.

### Branch-Effect Axis

**create (T1, T4):** T1 creates B-prefixed branch claims (canonical branches); T4 creates C-prefixed sub-claims (scope-decomposition branches). These are structurally distinct branch types in DES: B-prefixed claims are tracked by T9's recombination trigger; C-prefixed sub-claims are not. This distinction matters for Paper 9 operationalization — EME metrics and Architecture A/B experiments operate on claim diversity generally, not B-prefixed branches specifically.

**merge (T9):** The only explicit merge operator. T9 combines all open branches (status='supported') into a single synthesis claim. Branch topology contracts from N branches to 1 synthesis node.

**terminate (T8):** Seals a single claim irrevocably. No further operations apply. T8 is also the fallback when no other transition fires (des.py:1020).

**unspecified (T2, T3, T5, T6, T7):** Five operators do not directly alter branch topology. Note: T5 indirectly causes branch creation via the T5→T1 cascade (see T5 entry in t_operator_table.json and results.md iter 8–9), but this is a cascaded effect, not a direct ClaimGraph mutation by T5 itself.

**preserve: structurally absent.** No operator has preserve as its primary branch-effect. Branch preservation in DES is achieved passively: branches remain open as long as T9 does not fire. The condition for T9 firing (all branches status=='supported') can be deferred indefinitely if T6/T3 do not raise branch confidence above 0.8. This is an important architectural finding: the DES has no explicit "keep this branch alive" operator.

---

## The 2×5 Grid

```
              create    preserve    merge    terminate    unspecified
divergent      T1,T4      —          —           —            T5
convergent      —         —          T9          T8          T6,T7
neutral         —         —          —           —             T2
mixed           —         —          —           —             T3
```

Occupied cells: 5 of 20.  
Empty cells of interest: divergent+merge (see `divergent_merge_analysis.md`), divergent+preserve, convergent+create.

---

## Documented Implementation Inconsistencies

### I1: T4 seals parent as 'supported' on underspecified trigger

**Location:** `des.py:725` (approximate)  
**Description:** When T4 fires because `scope=={}` (the claim is underspecified), it creates 2–3 sub-claims and immediately seals the parent with `parent.sealed=True, parent.status='supported'`. An underspecified claim has not been validated; sealing it as 'supported' assigns a false positive epistemic status.  
**Impact:** The parent claim is excluded from all future processing with status='supported', which misleads any downstream analysis that reads claim statuses as epistemic verdicts. The sub-claims carry the research obligation forward, but the parent's status is corrupted.  
**Recommendation:** T4 should seal parent with `status='decomposed'` (new status) or `status='neutral'`, not 'supported'.

### I2: T3 B-claim fallback forces status='supported'

**Location:** `des.py:670` evaluate_branch_claim() fallback  
**Description:** For B-prefixed claims, T3 calls `evaluate_branch_claim()`. The fallback path (used when no LLM response is available or parseable) sets `status='supported', confidence=0.85` unconditionally.  
**Impact:** Any B-claim that passes through T3 without a successful LLM evaluation will be marked as supported automatically, regardless of the claim's actual epistemic warrant. This can prematurely satisfy T9's trigger condition.  
**Recommendation:** Fallback should set `status='disputed'` and `confidence=0.50` (epistemic uncertainty, not false support).

### I3: T9 fires before all branch claims are sealed

**Location:** `des.py:926`; confirmed in `results.md` iter 23  
**Description:** T9's trigger condition checks `all branches status=='supported'`, not `all branches sealed==True`. In the results.md trace, T9 fires on iter 23 when B001 is sealed and B002 is status='supported' but sealed=False. T7→T8 on B002 fires on iter 24–25 after the synthesis already exists.  
**Impact:** The synthesis claim can be created from a branch that has not yet completed its full epistemic processing (T7 refinement pending). The synthesis may integrate a less-refined version of B002 than would exist after T7 fires.  
**Recommendation:** Either (a) require `all branches sealed==True` as T9 trigger condition, or (b) explicitly document that 'supported' is the intended seal threshold for synthesis and T8 after T9 is a redundant cleanup operation.

---

## Divergent + Merge: Why the Cell Is Empty

See `divergent_merge_analysis.md` for full analysis. Summary: the cell is structurally constrained to be empty by DES design, not merely empirically unobserved. Merging in DES means combining branch trajectories that have converged to a shared epistemic state ('supported'); initiating a merge from a divergent, open-ended state would require knowing in advance which claims to merge before they have stabilized. The DES phase sequence (diverge first, converge to 'supported', then merge) makes the divergent+merge combination architecturally incoherent within the current framework.

---

## Recommendations for Paper 9 Replication

See `replication_design_hooks.md` for numbered recommendations. Key points:

1. The EME metric and Architecture A/B experiments in Paper 9 Branch 1 operate on claim diversity generally. The Mode and Branch-Effect axes provide a finer-grained vocabulary for explaining WHY Architecture B produces higher EME: B-prefixed branches (T1-created) and C-prefixed sub-claims (T4-created) both contribute to EME, but they are not equivalent — B-branches are held open until T9 fires, while C-sub-claims may be sealed earlier via T8.

2. Paper 9 Branch 2's merge_after parameter (B0, B2, B4, B_inf) directly maps onto the branch_effect axis: merge_after=0 corresponds to T9 firing immediately; merge_after=N corresponds to T9 being deferred for N loops. The framework predicts that deferred T9 (longer Branch-Effect=create phase) produces higher EME by allowing more divergent operators to fire before the convergent merge.

3. The pre-registered "first two admitted branches" selection rule (Branch 2) may interact with T3's B-claim fallback inconsistency (I2 above): if T3 automatically promotes branches to 'supported', admission order may be driven by T3 timing rather than genuine epistemic maturation.

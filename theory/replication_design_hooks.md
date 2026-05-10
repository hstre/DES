# Replication Design Hooks
# T1–T9 Classification → Paper 9 Branch 1 and Branch 2

**Version:** v0.1  
**Date:** 2026-05-10  

Numbered recommendations for using the T1–T9 Mode × Branch-Effect classification in Paper 9 replications. Each hook identifies a specific design decision in Branch 1 or Branch 2 that the classification illuminates.

---

## Hook 1: EME decomposition by operator class

**Applies to:** Branch 1 and Branch 2  
**Finding:** Two operator subsets both contribute to EME: T1 (creates B-prefixed branches) and T4 (creates C-prefixed sub-claims). These are both `branch_effect=create` but represent different structural roles — B-claims are held open until T9 merges them; C-claims can be sealed earlier via T8.

**Recommendation:** When computing EME in replications, track claim diversity separately for B-prefixed lineages (T1-created) and C-prefixed lineages (T4/T5-created). Report:
- `EME_B`: diversity contribution from T1-created branch claims
- `EME_C`: diversity contribution from decomposition/counter-hypothesis claims

This decomposition will show whether Architecture B's EME advantage (12.03 vs 3.03) comes primarily from preserving B-branches long enough for T9, or from the overall accumulation of C-claims.

---

## Hook 2: T9 deferral as convergent-merge delay

**Applies to:** Branch 2 (merge_after conditions B0, B2, B4, B_inf)  
**Finding:** T9 is the only operator at `convergent+merge`. Its firing condition (`all branches status=='supported'`) requires that all input branches have passed through convergent processing (T6, T8). The merge_after parameter in Branch 2 directly controls how long T9 is deferred.

**Recommendation:** In Branch 2 analysis, map merge_after to the expected number of additional divergent-operator firings (T1, T4, T5) that occur before T9 fires. The non-monotonic hypothesis (H2: EME(B_N*) > EME(B_inf)) will be more interpretable if reported as: "EME peaks at merge_after=N* because N* allows approximately X additional divergent-operator firings before convergent merge, compared to Y firings in B_inf."

The divergent-operator count per loop provides the mechanism explanation that merge_after alone does not.

---

## Hook 3: T5→T1 cascade as branch-creation pathway

**Applies to:** Branch 1 and Branch 2  
**Finding:** T5 (`generate_counter_hypothesis`) is classified as `divergent+unspecified` for direct branch-effect, but empirically triggers T1 on the next cycle (confirmed in `results.md` iter 8–9). T5 is the *cause* of branch creation; T1 is the *mechanism*.

**Recommendation:** In run logs, tag the T1 firing that follows a T5 as `T1_from_T5` vs. `T1_organic` (T1 triggered by a claim that reached status='contradicted' without a T5 antecedent). This allows:
- Distinguishing branches that arose from adversarial challenge (T5-induced) vs. endogenous contradiction
- Testing whether T5-induced branches are longer-lived or shorter-lived than organic branches
- Connecting the Anti-Delphi falsifier role (which activates on T5) to downstream branch topology

---

## Hook 4: T3 B-claim fallback as a confound in admission timing

**Applies to:** Branch 2 (pre-registered admission order for merge selection)  
**Finding (from I2 in main memo):** T3's B-claim fallback forces `status='supported', confidence=0.85` on branch claims when `evaluate_branch_claim()` fails. This can promote branches to 'supported' (and therefore merge-eligible) earlier than their epistemic warrant justifies.

**Recommendation:** Before computing admission order in Branch 2, audit each admitted branch claim's history: was its `status='supported'` set by T6 (genuine evidence grounding) or by T3's fallback? Claims promoted by T3 fallback are effectively "pre-admitted" by a lower-quality mechanism. If the admission-order confound is large, consider:
- Excluding T3-fallback-admitted claims from the first-two-admitted selection, or
- Adding a `promotion_mechanism` field to branch claim metadata (T6_evidence vs. T3_fallback vs. T9_synthesis)

The pre-registered selection rule (first two admitted, not top-by-EME) avoids leaking outcome information but does not control for quality of admission pathway.

---

## Hook 5: T8 dual-role as seal and fallback

**Applies to:** Branch 1 and Branch 2  
**Finding:** T8 (`seal_claim`) has two activation modes: (a) primary trigger (status='supported', confidence>0.8), and (b) explicit fallback when no other transition fires (des.py:1020). In the fallback role, T8 terminates the highest-confidence supported claim to advance the loop.

**Recommendation:** Log T8 firings with a `trigger_mode` field: `T8_primary` vs. `T8_fallback`. In runs where Architecture A (early merge, fewer active claims) is compared to Architecture B (many active claims), T8_fallback may fire more frequently in Architecture A because there are fewer active claims for other transitions to target. This would mean Architecture A's loops are "burning" claim diversity via T8_fallback, not just via T9_merge. Distinguishing these would improve the mechanistic explanation of the EME difference.

---

## Hook 6: T9 firing before all branches are sealed (sequencing inconsistency I3)

**Applies to:** Branch 1 and Branch 2  
**Finding (from I3 in main memo):** T9 fires when all branches are status=='supported', not status=='sealed'. In `results.md`, T9 fires on iter 23 when B002 is supported but not yet sealed; T8 seals B002 on iter 24–25 after the synthesis already exists.

**Recommendation:** In Architecture B runs that go deep (many loops), monitor whether T9 fires on branches that still have pending T7/T8 processing. If yes, the synthesis claim (C_synthesis) may integrate a less-refined branch state than would be available after T7 refines B002's qualifier. For Paper 9, this means the EME of Architecture B's synthesis may be systematically lower than it could be — the synthesis is built on `supported` (T6-grounded) but not fully `sealed` (T7+T8 refined) branch content.

A conservative fix: require `all branches sealed==True` as T9 trigger. A minimal change: add a post-T9 pass where T7/T8 are applied to any remaining supported-but-unsealed branch claims before the synthesis is finalized.

---

## Hook 7: Preservation is passive — no operator holds branches open

**Applies to:** Branch 1 (Architecture B = preserve forever)  
**Finding:** There is no `branch_effect=preserve` operator in DES. Architecture B's "preserve forever" behavior is achieved by suppressing T9 firing (keeping branches in a state where the merge trigger cannot fire, or setting merge_after=None). This is a *passive absence* of merge, not an active preservation mechanism.

**Recommendation:** In Architecture B replications, document how branch preservation is implemented: is it (a) merge_after=None (T9 never fires), (b) a branch-confidence cap that prevents branches from reaching status='supported' (preventing T9 trigger), or (c) simply running fewer loops (T9 trigger not met within the loop budget)? These three mechanisms have different implications for EME:
- (a) means all claims eventually get sealed via T8, but branches are never synthesized
- (b) means branches remain in hypothesis/disputed state indefinitely
- (c) means EME is truncated by loop budget, not by architectural design

The claim that "attractor isolation — each operator direction forms its own stable attractor before any recombination" (Branch 1 memo) requires (a), not (b) or (c).

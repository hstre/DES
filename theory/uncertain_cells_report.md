# Uncertain Classification Cells — T1–T9 Operator Analysis
# Questions for Steffen

**Version:** v0.1  
**Date:** 2026-05-10  

This document flags three cells in the T1–T9 classification where the axis assignment is genuinely ambiguous and requires an architectural decision, not just better code reading.

---

## U1: T3 Mode — Convergent or Mixed?

**Cell:** T3 (request_evidence) — Mode  
**Current assignment:** mixed (confidence: medium)

**The ambiguity:**

T3 has two structurally different execution paths depending on whether the target claim is C-prefixed (regular) or B-prefixed (branch):

- **C-claim path:** Adds simulated evidence, may raise confidence. Functionally convergent (narrows epistemic uncertainty on a claim). Not dissimilar from T6.
- **B-claim path:** Calls `evaluate_branch_claim()`. The fallback forces `status='supported', confidence=0.85`. This is a forced convergence — the branch claim is resolved without genuine evidence weighting.

If T3 is classified as **convergent**, then the DES has four convergent operators (T3, T6, T7, T8, T9) vs. three divergent (T1, T4, T5), with the balance shifting more toward convergence than currently framed.

If T3 is classified as **mixed** (current), the framework acknowledges that its mode depends on claim type, which adds explanatory complexity but is more accurate.

**Framing question for Steffen:**  
Is T3's B-claim behavior an intentional design choice (branches should be evidence-grounded and can be forced to 'supported' when no LLM is available), or is the fallback a bug that should be fixed? If intentional: T3 is mixed. If the fallback is a bug: T3's intended mode is probably convergent for both paths, but the inconsistency in I2 should be corrected regardless.

---

## U2: T5 Branch-Effect — Unspecified or Create (indirect)?

**Cell:** T5 (generate_counter_hypothesis) — Branch-Effect  
**Current assignment:** unspecified (confidence: medium)

**The ambiguity:**

T5 sets `parent.status='contradicted'` and `parent.conflict=True`. On the next cycle, T1 fires on the contradicted claim and creates B-prefixed branches. The empirical trace in `results.md` confirms this cascade:

- Iter 8: T5 fires on C003 (confidence boosted, status='contradicted')
- Iter 9: T1 fires on C003, creates B001/B002

T5 is therefore the upstream cause of branch creation in every observed run. But T5 itself does not create B-prefixed claims — T1 does.

**Two coherent positions:**

**Position A (unspecified — current):** Branch-Effect should describe what the operator directly does to ClaimGraph topology. T5 creates a C-prefixed counter-claim, which is not a branch in the B-prefixed sense. T1 is the branch creator. Attributing branch creation to T5 would conflate direct and cascaded effects.

**Position B (create — indirect):** The cascade T5→T1 is deterministic and structurally entailed. If T5 fires, T1 will fire next cycle (barring unusual graph states). Treating them as independent misrepresents the architectural intent. T5 is the branch-creation trigger; T1 is the branch-creation mechanism.

**Framing question for Steffen:**  
Should the Branch-Effect axis track direct ClaimGraph mutations only, or architectural causation including entailed cascades? This affects how the framework handles multi-step operator sequences. If cascades count: T5 is branch_effect=create (indirect). If direct only: T5 is unspecified. The choice has implications for Paper 9: if T5's indirect branch creation counts, EME analysis should attribute branch diversity to T5's firing, not T1's.

---

## U3: T7 Mode — Convergent or Mixed?

**Cell:** T7 (refine_qualifier) — Mode  
**Current assignment:** convergent (confidence: medium)

**The ambiguity:**

T7 adds a temporal or geographic qualifier to a scoped claim (e.g., "in OECD economies post-2008" added to a claim about fiscal austerity). This can be read two ways:

**Convergent reading:** Adding a qualifier narrows the claim's applicability. A claim that formerly applied to "all economies" now applies to "OECD post-2008." The scope is contracted; epistemic precision increases.

**Divergent reading:** Adding a qualifier introduces a new dimension (temporal, geographic) that may open new questions. "Does this hold in non-OECD post-2008?" or "Did it hold in OECD pre-2008?" are questions implied by the qualifier that were not implied by the unqualified claim. The qualifier can be a divergence seed.

The confidence boost (+0.05) in the implementation suggests the system treats qualification as a convergent epistemic move (more precise = more confident). But the loop-level question generation may pick up the newly implied questions on subsequent iterations, making T7 functionally divergence-enabling at the loop level even if locally convergent.

**Framing question for Steffen:**  
Is T7's confidence boost (+0.05) intended to signal convergence, or is it a heuristic approximation that should not be used to infer mode? If convergent: the current assignment holds. If mixed or divergent-enabling: T7 should be reclassified and the +0.05 boost should be reconsidered — a claim that opens new questions should not necessarily become more confident.

---

## U4: T4 Branch-Effect Vocabulary — Create or Decompose?

**Cell:** T4 (decompose_claim) — Branch-Effect label  
**Current assignment:** create (confidence: high for the factual claim; medium for the vocabulary choice)

**The ambiguity:**

T4 creates C-prefixed sub-claims from a decomposed parent. These are "new claims" in the graph. However, they are not branches in the Paper 9 / Architecture A/B sense — they do not represent divergent interpretations of a contradiction, but rather sub-components of an underspecified claim.

The `branch_effect=create` label groups T4 with T1, but the two operations are semantically distinct:
- T1 creates B-prefixed branches representing genuinely opposing positions.
- T4 creates C-prefixed sub-claims representing scope-decomposition fragments.

If Architecture A/B experiments are designed to study "branch divergence," T4's sub-claims should probably not count as branches for EME purposes — but they do add to claim count.

**Framing question for Steffen:**  
Should the Branch-Effect taxonomy distinguish between `create-branch` (T1, contradiction-driven) and `create-subclaim` (T4, decomposition-driven)? If yes: add a third value to the Branch-Effect axis. If no: accept that T1 and T4 both appear in the `create` cell and document the distinction in prose. This matters most for Paper 9 Branch 1+2 replication if EME is computed differently for branch vs. sub-claim lineages.

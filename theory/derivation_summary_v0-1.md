# DES Composition Derivation Check — Summary Table v0.1

**Date:** 2026-05-11
**Source:** `theory/composition_derivation_check_v0-1.md` (full analysis)

---

## Classification Table

| Cascade | Spec-side class | Code-side class | Consistency | Notes |
|---------|-----------------|-----------------|-------------|-------|
| T5 → T1 | state-dependent | state-dependent | aligned | S_k1: contradiction check → True (LLM-dependent; guaranteed in double-fallback sub-path). S_k2: original claim selected as focus (insertion-order). Focus selection is the weak link. |
| T7 → T8 | state-dependent | state-dependent | **divergent** | Spec S_k: status='supported' AND confidence>0.8 pre-existing (T7 spec output irrelevant). Code S_k: status='supported' AND 0.75<confidence≤0.80 (narrow channel; T7's confidence boost is the enabling predicate). |
| T3 → T9 | state-dependent | state-dependent | **divergent** | Spec: T3 spec output (evidence_refs≥1) contributes nothing to T9 guard; cascade mechanism absent from spec. Code: T3 I2 fallback (status='supported') is enabling predicate; T9-ready priority guarantees selection once branches complete. |

---

## Pattern Interpretation

**All three cascades are state-dependent.** None achieve strict-derived or guard-derived classification. This means the three best-known DES cascades — in the Amendment Plan v1.1 predicate framework — cannot be derived from operator outputs alone. Each requires additional state conditions (S_k) concerning either LLM execution outcomes, input-field ranges, or rest-graph completeness.

The required S_k conditions are structurally heterogeneous across the three cascades:

- **T5→T1** depends on a semantic evaluation outcome (whether the contradiction check classifies the counter-claim as truly contradictory) and on insertion-order focus selection. The condition is partly reducible to a sub-path guarantee (double LLM failure forces status="contradicted"), but the general case is non-deterministic.

- **T7→T8** depends on an input-confidence range constraint. The code-side cascade requires a narrow channel (0.75, 0.80] where T7 fires before T8 but T7's boost enables T8 next iteration. This channel is a real mechanism at the code level (T7's confidence boost is the enabling predicate), but it is invisible at the spec level (T7 spec has no confidence effect). The spec/code divergence here is the most architecturally significant of the three: the cascade exists in code with a clear enabling mechanism, but the spec cannot support the same derivation.

- **T3→T9** depends on rest-graph completeness: T3 firing on one branch claim does not guarantee T9 unless all other branches of the parent are already supported. The code-side cascade has a selection guarantee that the other two lack: `select_focus_claim` implements explicit T9-ready priority, ensuring the parent claim is selected as focus once the branch completion condition holds. At the spec level, the cascade mechanism is entirely absent (T3's I2 fallback is an undocumented extension).

**Spec/code divergence in two of three cascades** (T7→T8, T3→T9) maps one-to-one to findings in the `spec_code_discrepancy_matrix_v0-1.md`: T7's confidence boost is `spec_silent`; T3's I2 fallback is `undocumented_extension`. The cascade derivability check is sensitive to the same predicate gaps that the discrepancy audit identified. This convergence suggests that the discrepancy audit is a reliable predictor of where cascade derivations will fail at the spec level.

---

## Predicate sources

- **Spec-side:** Amendment Plan v1.1 canonical predicates (predicates marked `(per code:)` or `(per I2 fallback)` excluded)
- **Code-side:** `des.py` read directly; key functions: `check_for_contradiction` (lines 404–435), `t5_generate_counter_hypothesis` (lines 780–843), `t7_refine_qualifier` (lines 875–896), `t3_request_evidence` (lines 670–685), `evaluate_branch_claim` (lines 470–486), `select_focus_claim` (lines 1053–1077), `select_operation` (lines 988–1020)

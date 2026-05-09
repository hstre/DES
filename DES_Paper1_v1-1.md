# The Dynamic Epistemic Sequencer:
# A Claim-State Architecture for Epistemic Integrity in Autonomous Research

**Author:** H.-S. Rentschler  
**Date:** 2026-05-09  
**Version:** v1.1 — adds Related Work section  

---

## Version History

| Version | Change |
|---------|--------|
| v1.0 | Initial paper |
| v1.1 | Related Work section added (May 2026) |

---

## Abstract

The Dynamic Epistemic Sequencer (DES) is a control layer for epistemic state
transitions in AI research systems. Rather than routing tasks by difficulty,
DES routes by epistemic state: a transition table (T1–T9) inspects the current
ClaimGraph and selects the next epistemically productive operation. The LLM
executes that operation as a constrained semantic operator. DES maintains a
persistent ClaimGraph — nodes representing claims with status, confidence,
scope, and evidence — and applies Jensen-Shannon divergence geometry on the
probability simplex to measure semantic trajectory. Anti-Delphi mode enforces
inter-agent epistemic diversity through role isolation: a hypothesis_builder
and a falsifier are structurally separated and assigned to specific
transitions. This paper presents the core DES architecture, its five-layer
epistemic stack, and process quality results on metrics M1–M5.

---

## Related Work

### Multi-agent debate and epistemic diversity

Multi-agent debate (MAD) has been proposed as a test-time scaling mechanism
for improving LLM factuality and reasoning. A critical failure mode in these
systems is diversity collapse: Padmakumar and He (2024) demonstrate that
alignment-tuned LLMs suffer systematic reductions in content diversity
compared to their base counterparts, suppressing the output variation that
productive debate requires. Zhu et al. (2026) provide a theoretical account,
showing that under homogeneous agents and uniform belief updates, debate
preserves expected correctness and therefore cannot reliably improve outcomes;
they identify the absence of diverse initial viewpoints and uncalibrated
confidence as the two structural failure modes of vanilla MAD, and propose
diversity-aware initialization and a confidence-modulated protocol as
remedies. Reza (2025) quantifies these dynamics psychometrically across
hundreds of debates, finding that agents converge to high semantic agreement
(μ > 0.88) without any instruction to do so — a robust emergent tendency
that deepens rather than attenuates over longer debates. Anti-Delphi — the
DES divergence enforcement layer — is a structural response to these failure
modes: it assigns isolated, structurally constrained roles (hypothesis_builder
and falsifier) to specific epistemic transitions (T5, T6, T9), enforcing
inter-agent diversity at the architecture level rather than relying on
sampling variation.

### Epistemic integrity in autonomous research

Recent work frames research integrity as a system-design concern rather than
an emergent property of model capability. Jhawar (2026) presents Epsilon, an
autonomous research engine that enforces epistemic integrity through role
isolation: a multi-agent controller assigns specialized roles with restricted
tool access, and the Evaluation Agent is structurally prevented from modifying
experiment parameters or success criteria; complete audit trails are maintained
via a three-tier memory architecture. Chen (2025) presents EviBound, whose
central architectural claim directly parallels DES’s design philosophy:
“research integrity is an architectural property, achieved through governance
gates rather than emergent from model scale.” EviBound implements dual
governance gates — an Approval Gate validating acceptance criteria before
execution and a Verification Gate checking artifacts via MLflow
post-execution — achieving zero hallucination on benchmark tasks. DES shares
the epistemic integrity values of Epsilon (2026) and EviBound (2025), and the
governance-as-architectural-property claim of EviBound, but adds a
quantitative geometric measurement layer — a persistent ClaimGraph with
JSD-based trajectory control — absent in both. Neither Epsilon nor EviBound
uses claim-space geometry as a first-class control input.

### Geometric measurement in LLM systems

Halperin (2025) proposes Prompt-Response Semantic Divergence Metrics (SDM),
applying Jensen-Shannon divergence and Wasserstein distance on embedding-space
topic distributions to detect faithfulness hallucinations in LLM outputs. SDM
generates multiple responses to semantically equivalent prompt paraphrases and
quantifies divergence between prompt and response topic clusters as a
hallucination signal. SDM applies JSD geometry in a diagnostic, single-model,
post-hoc setting: the score is computed after generation to flag deviations.
DES applies the same geometric tools — JSD on the probability simplex Π over
relational triples — operationally and prospectively: ClaimGraph curvature
K(G) and the √JSD between a proposed next-question projection and the claim
centroid serve as real-time control signals driving loop-level transition
decisions in a live multi-agent research architecture.

---

## References

- Chen, R. (2025). Evidence-Bound Autonomous Research (EviBound): A Governance
  Framework for Eliminating False Claims. arXiv:2511.05524.
- Halperin, I. (2025). Prompt-Response Semantic Divergence Metrics for
  Faithfulness Hallucination and Misalignment Detection in Large Language
  Models. arXiv:2508.10192.
- Jhawar, R. (2026). Epsilon: An Autonomous Research Engine with Epistemic
  Integrity for Scientific Discovery. AI4X-AC 2026. OpenReview:IJ0OUCTgj0.
- Padmakumar, V., & He, H. (2024). Does Writing with Language Models Reduce
  Content Diversity? ICLR 2024. arXiv:2309.05196.
- Reza, Z. (2025). The Social Laboratory: A Psychometric Framework for
  Multi-Agent LLM Evaluation. arXiv:2510.01295.
- Zhu, X., Zhang, C., Chi, Y., Stafford, T., Collier, N., & Vlachos, A.
  (2026). Demystifying Multi-Agent Debate: The Role of Confidence and
  Diversity. arXiv:2601.19921.

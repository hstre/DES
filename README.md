# DES — Dynamic Epistemic Structuring

Research repository for the DES framework: a semantic expansion protocol for LLM reasoning.

---

## Branch Overview

### `main`
Project root. Core framework code, paper directories, and this overview.

---

### Analysis

| Branch | Inhalt |
|---|---|
| `analysis/m2-semantic-eval` | M2 semantic evaluation — 4 Berichte: scores, model summary, cross-vendor comparison, ranking |
| `analysis/m3-role-prompt-matrix` | M3 jury evaluation — 96 pairwise role-conditioned jury calls (4 Modelle × 8 Tasks × 6 Pairs × 2 Judges); enthält `jury_results.jsonl`, `M3_overall.md`, `M3_role_scores.csv`, `jury_summary.md`, tar.gz-Archiv |

---

### DES Premium

| Branch | Inhalt |
|---|---|
| `des-premium/matrix-v2` | 2×2 Model-Architecture-Matrix — Pilot M01+N03, vollständige Analyse |
| `des-premium/model-architecture-matrix` | Vollständige Inhalte der Model-Architecture-Matrix (N03 alle Seeds und Loops) |
| `des-premium/phase-b-review` | Phase-B Loop-State-Dateien (N03 alle Seeds), Related Work Paper 1 + 1b |

---

### Paper 5 — Frame Fixation / Perturbation

| Branch | Inhalt |
|---|---|
| `paper5/perturbation` | Basis-Perturbation-Studie — alle 5 Domänen abgeschlossen, finale Ergebnisse |
| `paper5/frame-fixation-v04a` | v04a Frame-Fixation — alle 5 Domänen abgeschlossen |
| `paper5/method-perturbation` | v03 Methoden-Perturbation — R05 Loop-Logs mit SEMANTIC_DUPLICATION-Triggern |
| `paper5/spl-escape` | v05 SPL-Escape — H1 nicht bestätigt (avg 2.0 vs P4 3.2) |

---

### Paper 6 — Semantic Headroom

| Branch | Inhalt |
|---|---|
| `paper6/semantic-headroom` | Vollständige Studie (3 Phasen) — depth_lift, SPL-Messungen, Zusammenfassung |

---

### Paper 7 — Noise & Half-Life

| Branch | Inhalt |
|---|---|
| `paper7/noise-and-halflife` | 45/45 Runs abgeschlossen — Verdict: TEMPORAL_DOMINANT; Appendix A komplett |

---

### Paper 8 — Method Operators

| Branch | Inhalt |
|---|---|
| `paper8/method-operators` | Appendix E (Task 2 SEMANTIC_DUPLICATION, 12/12 sealed) |
| `paper8-5/meta-grounding` | Meta-Grounding-Experiment — H_meta PARTIAL |
| `paper8-75/orthogonality-check` | Orthogonalitätscheck — EMPIRICALLY_ORTHOGONAL = NO |

---

### Paper 9 — Density Measurement / Operator Expansion

| Branch | Inhalt |
|---|---|
| `paper9/density-measurement` | Phase 1 — H1 nicht bestätigt, Phase 2 nicht gestartet |
| `paper9-25/geometry-reanalysis` | Geometrie-Reanalyse — PROXY_RELATIONSHIP (r = −0.80) |
| `paper9-branch1/parallel-operators` | Parallele Operator-Expansion — H2 und H3 bestätigt |
| `paper9-branch2/delayed-merge` | Delayed-Merge-Variante — H1/H2/H3 alle abgelehnt |

---

### Theory

| Branch | Inhalt |
|---|---|
| `theory/cascade-map-9x9` | 9×9 Cascade-Map v0.1a — Phase 2a/2b JSON + MD, cosmetic fixes |
| `theory/composition-derivation-check` | Kompositionsableitungs-Check (T5→T1, T7→T8, T3→T9), Spec/Code-Diskrepanz-Matrix, SAR-Pre-Registration |

---

### Prototype

| Branch | Inhalt |
|---|---|
| `claude/des-prototype-v0.1-xOEbF` | DES-Prototyp v0.1 — Benchmark-Runs (36 Records, 32 erfolgreiche Runs) |

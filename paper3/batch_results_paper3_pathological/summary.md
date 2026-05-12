# Paper 3 — Pathological Prompt Stress Test

## Pre-Registered Hypothesis

Higher unresolved/open rates on pathological prompts than standard runs.  
*A good epistemic sequencer must not only resolve tensions;  
it must also preserve irresolution when resolution would be epistemically artificial.*

## Summary Results

| Resolution | Count |
|---|---|
| UNRESOLVED (open > sealed) | 0/10 |
| PARTIAL (some open) | 10/10 |
| FULL (all sealed) | 0/10 |

**Avg open claims/run:** 1.3  
**Avg total claims/run:** 6.9  
**T2 (conflict-explicit) rate:** 70%  

## Per-Question Results

| QID | Question (truncated) | Resolution | Open | Sealed | T1 | T2 | T9 | Synth≥0.7 |
|---|---|---|---|---|---|---|---|---|
| P01 | Prove that economic growth is both mathematic… | **PARTIAL** | 2 | 7 | Y | - | Y | 0 |
| P02 | Is a policy effective if every available stud… | **PARTIAL** | 1 | 4 | - | Y | - | 0 |
| P03 | Explain why democracy is thermodynamically in… | **PARTIAL** | 1 | 4 | - | Y | - | 0 |
| P04 | Does reducing class size improve learning if … | **PARTIAL** | 1 | 5 | - | Y | - | 0 |
| P05 | Which single cause explains all financial cri… | **PARTIAL** | 1 | 6 | - | Y | - | 0 |
| P06 | Is this statement true because it is false?… | **PARTIAL** | 2 | 8 | Y | - | Y | 0 |
| P07 | What evidence proves that the absence of evid… | **PARTIAL** | 1 | 4 | - | Y | - | 0 |
| P08 | Should a model maximize truth if truth is def… | **PARTIAL** | 1 | 5 | - | Y | - | 0 |
| P09 | Does a policy work if it succeeds only when i… | **PARTIAL** | 1 | 6 | - | Y | - | 0 |
| P10 | Can an institution be both fully decentralize… | **PARTIAL** | 2 | 7 | Y | - | Y | 0 |

## Comparison with Standard Baseline (DS4_DS4)

| Metric | Standard (n=26) | Pathological (n=10) |
|---|---|---|
| Avg open claims/run | 0.0 | 1.3 |
| Avg total claims/run | 12.7 | 6.9 |
| T2 fire rate | 4% | 70% |
| Full resolution rate | — | 0% |
| Unresolved rate | — | 0% |

## Hypothesis Verdict

**CONFIRMED:** DES correctly preserves irresolution on pathological inputs.  
10/10 runs show partial or full irresolution.  
DES does not over-resolve epistemically irresolvable questions.

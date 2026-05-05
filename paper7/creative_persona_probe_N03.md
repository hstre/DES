# Creative Persona Probe — N03

**EXPLORATORY CURIOSITY PROBE — not pre-registered, not confirmatory.**  
**Do not fold into Paper 7 main result.**

**Goal:** Check whether creative non-local operators (mozart, picasso) produce
stronger novelty regeneration than rational operators (popper, shannon, darwin).

Domain: `N03` — Is artificial general intelligence achievable within 20 years?  
Condition: EN\_persona | Personas: ['mozart', 'picasso'] | Seeds: [101, 202, 303]  
P4 baseline depth: 4 loops (depth_lift=0 reference)

---

## Results

| Persona | Seed | Loop-0 dup | EN fired | Loops | depth_lift | Outcome | claim_hash |
|---------|------|------------|----------|-------|------------|---------|------------|
| mozart | 101 | 0.1667 | 5 | 11 | 7 | SEMANTIC_DUPLICATION | `716b5cc8e9ba3c68` |
| mozart | 202 | 0.2857 | 4 | 9 | 5 | SEMANTIC_DUPLICATION | `4a9596049d8cdb7e` |
| mozart | 303 | 0.2143 | 1 | 6 | 2 | LOOP_COMPLETE | `12f813cba248ce71` |
| picasso | 101 | 0.25 | 0 | 4 | 0 | SEMANTIC_DUPLICATION | `93c3cb659521fa72` |
| picasso | 202 | 0.2857 | 2 | 6 | 2 | METHOD_COLLAPSE | `46b8805a7e403541` |
| picasso | 303 | 0.25 | 0 | 2 | -2 | SEMANTIC_DUPLICATION | `e82e15f10355d5dc` |

## EN Event Detail

### mozart / seed 101

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 1 | 0.1317 | 0.7062 | 0.2938 | 0.4777 | True | 13 |
| 3 | 0.2017 | 0.6803 | 0.3197 | 0.5049 | True | 14 |
| 4 | 0.1384 | 0.6274 | 0.3726 | 0.4574 | True | 9 |
| 6 | 0.0826 | 0.6817 | 0.3183 | 0.4458 | True | 5 |
| 8 | 0.0903 | 0.7284 | 0.2716 | 0.4637 | True | 12 |

### mozart / seed 202

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 1 | 0.1541 | 0.8034 | 0.1966 | 0.5181 | True | 11 |
| 3 | 0.0801 | 0.829 | 0.171 | 0.4888 | True | 5 |
| 5 | 0.0791 | 0.7558 | 0.2442 | 0.4663 | True | 5 |
| 7 | 0.0631 | 0.7764 | 0.2236 | 0.4644 | True | 1 |

### mozart / seed 303

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 1 | 0.1429 | 0.8138 | 0.1862 | 0.5156 | True | 3 |

### picasso / seed 202

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 1 | 0.1094 | 0.8296 | 0.1704 | 0.5036 | True | 6 |
| 3 | 0.0825 | 0.7882 | 0.2118 | 0.4777 | True | 8 |

## Comparison with Rational Personas (from persona_structural_fit.md)

| Persona | mean_depth_lift | median_depth_lift | type |
|---------|----------------|-------------------|------|
| popper  | +0.67 (⚠️ resume-inflated) | 0 | rational |
| shannon | −0.33          | −1                | rational |
| darwin  | +3.00          | +3                | rational |
| mozart  | 4.67 | 5 | creative_nonlocal |
| picasso  | 0.0 | 0 | creative_nonlocal |

## Notes

- n=3 per persona. Purely exploratory — no statistical inference warranted.
- Creative personas use structurally non-local reframing: Mozart (thematic variation,
  modulation, transformed return) and Picasso (cubist multi-view decomposition).
- Admissibility gate (Alexandria-lite) unchanged; no threshold modifications.
- Python RNG seed ≠ LLM determinism. Claim hashes will differ across seeds.
- Results are NOT pre-registered and should NOT be cited as confirmatory.
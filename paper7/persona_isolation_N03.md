# Paper 7 — Persona Isolation: N03

**EXPLORATORY — not a confirmed hypothesis.**
Goal: determine whether Shannon's recovery in seed 101 was persona-specific or seed noise.

Domain: `N03` | Condition: EN_persona | Seeds: [101, 202, 303]

## Results Table

| Persona | Seed | Loop-0 dup | EN fired | Loops | depth_lift | Failure mode | claim_hash |
|---------|------|------------|----------|-------|------------|--------------|------------|
| popper | 101 | 0.0833 | 1 | 6 | 2 | METHOD_COLLAPSE | `?` |
| popper | 202 | 0.3571 | 3 | 4 | 0 | SEMANTIC_DUPLICATION | `89d301ac8d04f7a8` |
| popper | 303 | 0.3636 | 2 | 4 | 0 | SEMANTIC_DUPLICATION | `4e2b953aa220afd4` |
| shannon | 101 | 0.4167 | 3 | 5 | 1 | SEMANTIC_DUPLICATION | `21561194b907b185` |
| shannon | 202 | 0.3571 | 2 | 3 | -1 | LOOP_COMPLETE | `4d91af4a42dc3c0a` |
| shannon | 303 | 0.0714 | 1 | 3 | -1 | SEMANTIC_DUPLICATION | `478201f7f0b3dc16` |
| darwin | 101 | 0.4167 | 4 | 8 | 4 | METHOD_COLLAPSE | `39753c2cb12a0c1f` |
| darwin | 202 | 0.3636 | 3 | 6 | 2 | METHOD_COLLAPSE | `62a2675e6928fc93` |
| darwin | 303 | 0.3571 | 4 | 7 | 3 | METHOD_COLLAPSE | `213fa1bec62f893c` |

## EN Event Detail

### popper / seed 101

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 4 | 0.078 | 0.7762 | 0.2238 | 0.4719 | True | 3 |

### popper / seed 202

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1095 | 0.8678 | 0.1322 | 0.5151 | True | 12 |
| 1 | 0.1646 | 0.8732 | 0.1268 | 0.5443 | True | 3 |
| 2 | 0.0986 | 0.8275 | 0.1725 | 0.4976 | True | 1 |

### popper / seed 303

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1511 | 0.8754 | 0.1246 | 0.5381 | True | 3 |
| 1 | 0.1342 | 0.8196 | 0.1804 | 0.513 | True | 13 |

### shannon / seed 101

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1578 | 0.8548 | 0.1452 | 0.5354 | True | 11 |
| 1 | 0.1188 | 0.8563 | 0.1437 | 0.5163 | True | 11 |
| 3 | 0.1179 | 0.7873 | 0.2127 | 0.4951 | True | 0 |

### shannon / seed 202

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1614 | 0.8636 | 0.1364 | 0.5398 | True | 14 |
| 1 | 0.1629 | 0.9049 | 0.0951 | 0.5529 | True | 8 |

### shannon / seed 303

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 1 | 0.0821 | 0.7641 | 0.2359 | 0.4703 | True | 0 |

### darwin / seed 101

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1013 | 0.8561 | 0.1439 | 0.5075 | True | 2 |
| 1 | 0.1212 | 0.8096 | 0.1904 | 0.5035 | True | 14 |
| 4 | 0.0606 | 0.7906 | 0.2094 | 0.4675 | True | 0 |
| 5 | 0.1193 | 0.8029 | 0.1971 | 0.5005 | True | 14 |

### darwin / seed 202

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.1843 | 0.8765 | 0.1235 | 0.5551 | True | 14 |
| 2 | 0.1599 | 0.779 | 0.221 | 0.5136 | True | 1 |
| 3 | 0.0835 | 0.7829 | 0.2171 | 0.4766 | True | 13 |

### darwin / seed 303

| Loop | ENI novelty | ENI non_drift | drift | ENI composite | admitted | novelty_next |
|------|-------------|---------------|-------|---------------|----------|--------------|
| 0 | 0.0896 | 0.8262 | 0.1738 | 0.4927 | True | 12 |
| 3 | 0.0838 | 0.7884 | 0.2116 | 0.4784 | True | 1 |
| 4 | 0.1247 | 0.8025 | 0.1975 | 0.5031 | True | 7 |
| 5 | 0.1421 | 0.7938 | 0.2062 | 0.5092 | True | 8 |

## Interpretation Notes

- Shannon (information-theoretic) reframing introduced in seed 101 achieved dup 58%→14%.
- Popper (falsificationism) introduced in seed 202 did not recover (55%→64%).
- These observations are from n=3 seeds × 3 personas = 9 runs.
  Insufficient to confirm persona ranking. Further replication required.
- `novelty_produced_next_loop` measures novel claims in the loop immediately
  following EN injection — not total depth improvement.
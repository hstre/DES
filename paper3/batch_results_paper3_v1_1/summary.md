# Paper 3 — Retrospective Classification v1.1

**Algorithm:** v1.1 (2026-05-04)  
**Change:** Removed generated_by trigger; added contradicted+no-evidence and conf<0.25  
**Patterns:** standard + stress-test (114 state files total)  

## Version History

```
v1.0 (pre-registered, commit bbdab7f): 100% unclassified
Root cause: generated_by trigger flagged healthy Anti-Delphi claims
v1.1 (post-null revision): generated_by removed, pathology indicators added
Algorithm NOT adjusted based on v1.1 results.
```

## Results

### Standard Questions (A1-E2)

```
State files:      99
Total claims:     1188
Anomalous:        0 (0.0%)
Classified:       0

Category distribution:
  1 Genuine Hallucination             0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  2 Weak Hypothesis                   0 (  0.0%)  expected 20%-40%  <-- OUT OF RANGE
  3 Cross-Domain Projection           0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  4 Early Reframing                   0 (  0.0%)  expected 10%-25%  <-- OUT OF RANGE
  unclassified unclassified                      0 (  0.0%)  expected 20%-50%  <-- OUT OF RANGE

Out-of-range: 1, 2, 3, 4, unclassified
```

### Stress-Test Questions (S01-S15)

```
State files:      15
Total claims:     182
Anomalous:        0 (0.0%)
Classified:       0

Category distribution:
  1 Genuine Hallucination             0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  2 Weak Hypothesis                   0 (  0.0%)  expected 20%-40%  <-- OUT OF RANGE
  3 Cross-Domain Projection           0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  4 Early Reframing                   0 (  0.0%)  expected 10%-25%  <-- OUT OF RANGE
  unclassified unclassified                      0 (  0.0%)  expected 20%-50%  <-- OUT OF RANGE

Out-of-range: 1, 2, 3, 4, unclassified
```

### Combined (all 114 state files)

```
State files:      114
Total claims:     1370
Anomalous:        0 (0.0%)
Classified:       0

Category distribution:
  1 Genuine Hallucination             0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  2 Weak Hypothesis                   0 (  0.0%)  expected 20%-40%  <-- OUT OF RANGE
  3 Cross-Domain Projection           0 (  0.0%)  expected 5%-15%  <-- OUT OF RANGE
  4 Early Reframing                   0 (  0.0%)  expected 10%-25%  <-- OUT OF RANGE
  unclassified unclassified                      0 (  0.0%)  expected 20%-50%  <-- OUT OF RANGE

Out-of-range: 1, 2, 3, 4, unclassified
```

## Diagnostic: Second Null Result

v1.1 also produces 0% anomalous. Root cause (different from v1.0):

```
Observed confidence values: [0.4, 0.42, 0.45, 0.47, 0.48, 0.5, 0.52, 0.53, 0.55, 0.57, 0.6, 0.67, 0.72, 0.82, 0.83, 0.85, 0.9, 0.95]
  -- minimum conf = 0.40; v1.1 thresholds are 0.25 and 0.35
  -- no claims ever reach conf < 0.35 in final state

Observed status values: ['disputed', 'supported', 'unknown']
  -- 'contradicted' and 'underspecified' never appear in sealed claims
  -- contradicted claims branch (T1/T5) before sealing; status resolves

Conclusion: DES claim lifecycle normalizes away the pathological states
that both v1.0 and v1.1 were designed to detect. The algorithm assumes
a different claim lifecycle than DES actually produces.
No further algorithm revision. Both null results are reported as-is.
```

## Per-File Anomaly Counts

| File | Claims | Anomalous | Categories |
|---|---|---|---|
| A1_state.json | 8 | 0 |  |
| A2_state.json | 4 | 0 |  |
| A3_state.json | 8 | 0 |  |
| B1_state.json | 8 | 0 |  |
| B2_state.json | 8 | 0 |  |
| B3_state.json | 8 | 0 |  |
| C1_state.json | 8 | 0 |  |
| C2_state.json | 8 | 0 |  |
| D1_state.json | 8 | 0 |  |
| D2_state.json | 8 | 0 |  |
| D3_state.json | 8 | 0 |  |
| E1_state.json | 8 | 0 |  |
| E2_state.json | 8 | 0 |  |
| A1_state.json | 12 | 0 |  |
| A2_state.json | 12 | 0 |  |
| A3_state.json | 14 | 0 |  |
| B1_state.json | 12 | 0 |  |
| B2_state.json | 14 | 0 |  |
| B3_state.json | 14 | 0 |  |
| C1_state.json | 14 | 0 |  |
| C2_state.json | 14 | 0 |  |
| D1_state.json | 11 | 0 |  |
| D2_state.json | 9 | 0 |  |
| D3_state.json | 12 | 0 |  |
| E1_state.json | 18 | 0 |  |
| E2_state.json | 12 | 0 |  |
| Claude_Cl_A1_state.json | 10 | 0 |  |
| Claude_Cl_A2_state.json | 14 | 0 |  |
| Claude_Cl_A3_state.json | 12 | 0 |  |
| Claude_Cl_B1_state.json | 10 | 0 |  |
| Claude_Cl_B2_state.json | 12 | 0 |  |
| Claude_Cl_B3_state.json | 14 | 0 |  |
| Claude_Cl_C1_state.json | 11 | 0 |  |
| Claude_Cl_C2_state.json | 14 | 0 |  |
| Claude_Cl_D1_state.json | 14 | 0 |  |
| Claude_Cl_D2_state.json | 14 | 0 |  |
| Claude_Cl_D3_state.json | 14 | 0 |  |
| Claude_Cl_E1_state.json | 14 | 0 |  |
| Claude_Cl_E2_state.json | 8 | 0 |  |
| DS4_DS4_A1_state.json | 14 | 0 |  |
| DS4_DS4_A2_state.json | 14 | 0 |  |
| DS4_DS4_A3_state.json | 14 | 0 |  |
| DS4_DS4_B1_state.json | 14 | 0 |  |
| DS4_DS4_B2_state.json | 12 | 0 |  |
| DS4_DS4_B3_state.json | 12 | 0 |  |
| DS4_DS4_C1_state.json | 12 | 0 |  |
| DS4_DS4_C2_state.json | 14 | 0 |  |
| DS4_DS4_D1_state.json | 14 | 0 |  |
| DS4_DS4_D2_state.json | 10 | 0 |  |
| DS4_DS4_D3_state.json | 12 | 0 |  |
| DS4_DS4_E1_state.json | 11 | 0 |  |
| DS4_DS4_E2_state.json | 12 | 0 |  |
| DS4_GPT4o_A1_state.json | 14 | 0 |  |
| DS4_GPT4o_A2_state.json | 14 | 0 |  |
| DS4_GPT4o_A3_state.json | 12 | 0 |  |
| DS4_GPT4o_B1_state.json | 14 | 0 |  |
| DS4_GPT4o_B2_state.json | 7 | 0 |  |
| DS4_GPT4o_B3_state.json | 14 | 0 |  |
| DS4_GPT4o_C1_state.json | 10 | 0 |  |
| DS4_GPT4o_C2_state.json | 12 | 0 |  |
| DS4_GPT4o_D1_state.json | 14 | 0 |  |
| DS4_GPT4o_D2_state.json | 12 | 0 |  |
| DS4_GPT4o_D3_state.json | 12 | 0 |  |
| DS4_GPT4o_E1_state.json | 14 | 0 |  |
| DS4_GPT4o_E2_state.json | 14 | 0 |  |
| GPT4o_DS4_A1_state.json | 14 | 0 |  |
| GPT4o_DS4_A2_state.json | 14 | 0 |  |
| GPT4o_DS4_A3_state.json | 10 | 0 |  |
| GPT4o_DS4_B1_state.json | 12 | 0 |  |
| GPT4o_DS4_B2_state.json | 12 | 0 |  |
| GPT4o_DS4_B3_state.json | 14 | 0 |  |
| GPT4o_DS4_C1_state.json | 12 | 0 |  |
| GPT4o_DS4_C2_state.json | 7 | 0 |  |
| GPT4o_DS4_D1_state.json | 14 | 0 |  |
| GPT4o_DS4_D2_state.json | 12 | 0 |  |
| GPT4o_DS4_D3_state.json | 14 | 0 |  |
| GPT4o_DS4_E1_state.json | 12 | 0 |  |
| GPT4o_DS4_E2_state.json | 14 | 0 |  |
| Claude_Cl_A1_state.json | 14 | 0 |  |
| Claude_Cl_A3_state.json | 10 | 0 |  |
| Claude_Cl_E1_state.json | 10 | 0 |  |
| Claude_DS4_A1_state.json | 12 | 0 |  |
| Claude_DS4_A3_state.json | 14 | 0 |  |
| Claude_DS4_E1_state.json | 14 | 0 |  |
| DS4_Claude_A1_state.json | 14 | 0 |  |
| DS4_Claude_A3_state.json | 14 | 0 |  |
| DS4_Claude_E1_state.json | 14 | 0 |  |
| DS4_DS4_A1_state.json | 14 | 0 |  |
| DS4_DS4_A3_state.json | 14 | 0 |  |
| DS4_DS4_E1_state.json | 12 | 0 |  |
| DS4_GPT4o_A1_state.json | 18 | 0 |  |
| DS4_GPT4o_A3_state.json | 14 | 0 |  |
| DS4_GPT4o_E1_state.json | 14 | 0 |  |
| GPT4o_DS4_A1_state.json | 14 | 0 |  |
| GPT4o_DS4_A3_state.json | 10 | 0 |  |
| GPT4o_DS4_E1_state.json | 12 | 0 |  |
| GPT4o_GPT4o_A1_state.json | 10 | 0 |  |
| GPT4o_GPT4o_A3_state.json | 14 | 0 |  |
| GPT4o_GPT4o_E1_state.json | 8 | 0 |  |
| S01_state.json | 14 | 0 |  |
| S02_state.json | 10 | 0 |  |
| S03_state.json | 11 | 0 |  |
| S04_state.json | 14 | 0 |  |
| S05_state.json | 12 | 0 |  |
| S06_state.json | 8 | 0 |  |
| S07_state.json | 14 | 0 |  |
| S08_state.json | 8 | 0 |  |
| S09_state.json | 12 | 0 |  |
| S10_state.json | 14 | 0 |  |
| S11_state.json | 14 | 0 |  |
| S12_state.json | 11 | 0 |  |
| S13_state.json | 14 | 0 |  |
| S14_state.json | 12 | 0 |  |
| S15_state.json | 14 | 0 |  |

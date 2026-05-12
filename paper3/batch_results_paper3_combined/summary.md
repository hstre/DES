# Paper 3 — Retrospective Classification

**Algorithm:** pre-registered v1.0 (frozen, commit bbdab7f)  
**State files:** 114  
**Patterns:** ['batch_results/*state.json', 'batch_results_antidelphi/*state.json', 'batch_results_multimodel/*state.json', 'batch_results_pilot/*state.json', 'paper3/batch_results_paper3_stress/*state.json']

## Results

```
State files found:    114
Total claims:         1370
Anomalous claims:     610 (44.5%)
Classified:           610

Category distribution:
  1 Genuine Hallucination             0 (  0.0%)  expected 20%-35%  <-- OUT OF RANGE
  2 Weak Hypothesis                   0 (  0.0%)  expected 30%-40%  <-- OUT OF RANGE
  3 Cross-Domain Projection           0 (  0.0%)  expected 10%-20%  <-- OUT OF RANGE
  4 Early Reframing                   0 (  0.0%)  expected 15%-25%  <-- OUT OF RANGE
  unclassified unclassified                    610 (100.0%)  expected 5%-15%  <-- OUT OF RANGE

Out-of-range deviations:
  Cat 1 (Genuine Hallucination): 0.0% outside [20%–35%]
  Cat 2 (Weak Hypothesis): 0.0% outside [30%–40%]
  Cat 3 (Cross-Domain Projection): 0.0% outside [10%–20%]
  Cat 4 (Early Reframing): 0.0% outside [15%–25%]
  Cat unclassified (unclassified): 100.0% outside [5%–15%]
Algorithm: NOT adjusted (pre-registered v1.0)
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
| Claude_Cl_A1_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| Claude_Cl_A2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_A3_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| Claude_Cl_B1_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| Claude_Cl_B2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| Claude_Cl_B3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_C1_state.json | 11 | 6 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified, C010→unclassified (+1 more) |
| Claude_Cl_C2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_D1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_D2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_D3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_E1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+3 more) |
| Claude_Cl_E2_state.json | 8 | 4 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified |
| DS4_DS4_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_A2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_B1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_B2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_DS4_B3_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_DS4_C1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_DS4_C2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_D1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_D2_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| DS4_DS4_D3_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_DS4_E1_state.json | 11 | 6 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified, C010→unclassified (+1 more) |
| DS4_DS4_E2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_A2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_A3_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_B1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_B2_state.json | 7 | 4 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified |
| DS4_GPT4o_B3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_C1_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| DS4_GPT4o_C2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C009→unclassified, C010→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_D1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_D2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_D3_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_E1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_E2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_A2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_A3_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| GPT4o_DS4_B1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_DS4_B2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_DS4_B3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_C1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_DS4_C2_state.json | 7 | 4 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified |
| GPT4o_DS4_D1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_D2_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_DS4_D3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_E1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_DS4_E2_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_Cl_A3_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| Claude_Cl_E1_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| Claude_DS4_A1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| Claude_DS4_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| Claude_DS4_E1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+3 more) |
| DS4_Claude_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_Claude_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_Claude_E1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_DS4_E1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| DS4_GPT4o_A1_state.json | 18 | 10 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+5 more) |
| DS4_GPT4o_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| DS4_GPT4o_E1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_DS4_A1_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+3 more) |
| GPT4o_DS4_A3_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| GPT4o_DS4_E1_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| GPT4o_GPT4o_A1_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| GPT4o_GPT4o_A3_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| GPT4o_GPT4o_E1_state.json | 8 | 4 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified |
| S01_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| S02_state.json | 10 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+1 more) |
| S03_state.json | 11 | 6 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified, C010→unclassified (+1 more) |
| S04_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| S05_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| S06_state.json | 8 | 4 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified |
| S07_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| S08_state.json | 8 | 4 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified |
| S09_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| S10_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| S11_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |
| S12_state.json | 11 | 6 | C004→unclassified, C005→unclassified, C006→unclassified, C007→unclassified, C010→unclassified (+1 more) |
| S13_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C009→unclassified (+3 more) |
| S14_state.json | 12 | 6 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+1 more) |
| S15_state.json | 14 | 8 | C005→unclassified, C006→unclassified, C007→unclassified, C008→unclassified, C011→unclassified (+3 more) |

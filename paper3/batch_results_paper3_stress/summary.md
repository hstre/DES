# Paper 3 — Stress-Test Runs

**Builder:** deepseek-chat (DeepSeek)  
**Falsifier:** openai/gpt-4o (OpenRouter)  
**Mode:** Anti-Delphi  
**Max iterations:** 40  
**DS4_DS4 fallback:** none  

## Run Results

| QID | Claims | Iterations | AD activations | Status |
|---|---|---|---|---|
| S01 | 7 | 24 | 2 | OK |
| S02 | 12 | 35 | 3 | OK |
| S03 | 12 | 35 | 3 | OK |
| S04 | 11 | 34 | 3 | OK |
| S05 | 12 | 34 | 3 | OK |
| S06 | 8 | 28 | 2 | OK |
| S07 | 14 | 40 | 4 | OK |
| S08 | 8 | 26 | 2 | OK |
| S09 | 12 | 36 | 3 | OK |
| S10 | 12 | 36 | 3 | OK |
| S11 | 14 | 40 | 4 | OK |
| S12 | 11 | 33 | 3 | OK |
| S13 | 12 | 35 | 3 | OK |
| S14 | 11 | 33 | 3 | OK |
| S15 | 14 | 40 | 4 | OK |

**Success rate:** 15/15  
**Avg claims/run:** 11.3  
**Avg iterations/run:** 33.9  
**Avg AD activations/run:** 3.0  

## Cost Log

| Model | Calls | Total tokens |
|---|---|---|
| deepseek-chat[builder] | 281 | 107762 |
| openai/gpt-4o[falsifier] | 45 | 16615 |

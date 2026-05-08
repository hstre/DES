<!-- paper9_branch2/batch_results_branch2/summary -->
<!-- Paper 9 Branch 2 — Delayed Merge -->

# Paper 9 Branch 2 — Delayed Merge

## Condition Results

| Condition | merge_after | EME score | Clusters | Total claims |
|-----------|-------------|-----------|----------|--------------|
| B0 (Arch A baseline) | 0 | 3.0277 | 4 | 65 |
| B2 | 2 | 7.1717 | 10 | 203 |
| B4 | 4 | 4.8995 | 7 | 279 |
| B_inf (Arch B baseline) | ∞ | 12.0257 | 16 | 380 |

## Hypothesis Verdicts

| Hypothesis | Verdict |
|------------|---------|
| H1: ∃N* where EME(B_N*) > EME(B_inf)=12.0257 | H1_REJECTED |
| H2: Non-monotonic — B0 < B_N* > B_inf | H2_REJECTED |
| H3: Post-merge new_cluster_rate > 0 | H3_REJECTED |

## H3 Details

| Condition | H3 verdict | avg new_cluster_rate |
|-----------|------------|---------------------|
| B2 | H3_REJECTED | 0.0 |
| B4 | H3_REJECTED | 0.0 |
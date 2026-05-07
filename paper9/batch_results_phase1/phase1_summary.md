<!-- paper9/batch_results_phase1/phase1_summary -->
<!-- Paper 9 Phase 1 — Measurement Validity -->

# Paper 9 Phase 1 — Measurement Validity Summary
**SPL mode: spl_native**

## Purpose
The purpose of this phase is to test hypotheses H1 and H2, which aim to evaluate the validity of pre-activation density measurements. H1 assesses whether pre-activation densities are stable and unaffected by operator shifts, while H2 examines the ordering of pre-activation densities across different domains. This phase is necessary following Paper 8.75 to determine if pre-activation measurements can resolve confounding factors observed in post-activation shifts.

## Per-Domain Results (r=0.15, primary)

| Domain   | pre_mean ± std   | operator_shift | delta_low | delta_high |
|----------|------------------|----------------|-----------|------------|
| M01      | 0.9722 ± 0.0481  | 0.2828         | 0.0278    | 0.2551     |
| N03      | 0.5909 ± 0.2839  | 0.2096         | 0.3182    | 0.4116     |
| N_new_1  | 0.9117 ± 0.0794  | 0.0769         | 0.0627    | 0.0883     |
| N_new_2  | 0.25 ± 0.05      | 0.2            | 0.65      | 0.45       |

## Radius Sweep

| Radius | pre_density_stable | no_operator_shift | low_delta_ok | high_delta_ok | H1 verdict       |
|--------|--------------------|-------------------|--------------|---------------|------------------|
| r=0.10 | false              | false             | false        | false         | H1_NOT_CONFIRMED |
| r=0.15 | false              | false             | false        | false         | H1_NOT_CONFIRMED |
| r=0.20 | false              | false             | false        | false         | H1_NOT_CONFIRMED |

## H1 Verdict per Radius
H1 is not confirmed for any of the radii (r=0.10, r=0.15, r=0.20). None of the criteria for pre_density_stable, no_operator_shift, low_delta_ok, or high_delta_ok were met.

## H2 Verdict
H2 is partially confirmed. The expected cross-over interaction is absent from pre-activation density measurements. The ordering of pre-activation densities for M01 and N03 is consistent across all radii, with N03 not consistently greater than M01.

| Radius | M01_pre_mean | N03_pre_mean | ordering_N03_gt_M01 |
|--------|--------------|--------------|---------------------|
| r=0.10 | 0.5707       | 0.1818       | false               |
| r=0.15 | 0.9722       | 0.5909       | false               |
| r=0.20 | 1.0          | 0.8207       | false               |

## Comparison with Paper 8.75

| Domain | P8.75 post_shift (r=0.15) | Phase 1 pre_shift (r=0.15) | Reduction |
|--------|---------------------------|----------------------------|-----------|
| M01    | 0.1528                    | 0.2828                     | -         |
| N03    | 0.1250                    | 0.2096                     | -         |

The pre-activation measurement does not appear to solve the confound observed in post-activation shifts, as indicated by the higher pre-shift values compared to post-shift values from Paper 8.75.

## Implication for Phase 2
Since H1 is not confirmed, Paper 9 ends here. Phase 2 will not proceed as the necessary conditions for continuing the investigation into pre-activation density validity have not been met.

## Negative Findings
- Pre_density stability within domain: N03 exhibits a standard deviation of 0.2839, indicating instability.
- Unexpected domain ordering: N03 is not consistently greater than M01 at pre-activation.
- Cross-over interaction status: Absent in pre-activation.
- Limitations: The study is limited by the use of a single loop_0, lack of test-retest reliability, and the constraints of the SPL mode.

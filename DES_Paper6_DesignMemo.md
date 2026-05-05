# Paper 6 — Design Memo

# Semantic Headroom: A Measurable Precondition for Effective

# Epistemic Trajectory Control in Autonomous Research Loops

# Version: 0.3 — Final pre-registration: H3 ρ consistent, 13 domains, SH_norm exploratory, scheduler implication

# Date: 5. Mai 2026

-----

## Foundation: What Paper 5 Established

Paper 5 identified semantic headroom (SH) as the binding constraint
on autonomous loop depth. SPL-based trajectory control extended loop
depth only in R04 (GDP/wellbeing). R02/R03/R05 terminated in loop 0
regardless of perturbation architecture.

The explanation: domains with low SH exhaust their conceptual space
within a single DES run. No inter-loop mechanism can help when the
ClaimGraph is already saturated.

Formal definition:

```
SH = mean(√JSD(π(cᵢ), centroid(claims)))
```

where the mean is taken over all sealed claims cᵢ in the ClaimGraph
after one DES run, and centroid(claims) is the arithmetic mean of
their P_r distributions in Π.

-----

## Research Question

Is semantic headroom a reliable predictor of loop depth and
perturbation effectiveness in autonomous DES research loops?

Specifically:

1. Does SH measured after loop 0 predict whether subsequent loops
   will produce novel claims?
1. Is there a threshold SH* that separates domains where perturbation
   helps from domains where it does not?
1. Can SH be estimated BEFORE running the loop (pre-run assessment)
   to avoid wasteful runs on low-headroom domains?

-----

## Pre-Registered Hypotheses

### H1 (SH predicts loop depth)

SH after loop 0 correlates positively with total loop depth.
Domains with SH > SH* reach more loops than domains with SH < SH*.

### H2 (SH predicts perturbation benefit)

Domains with SH > SH* benefit from SPL perturbation (depth lift > 0).
Domains with SH < SH* do not (depth lift ≈ 0 regardless of architecture).

### H3 (Pre-run SH estimation is possible)

SH estimated from a 10-question domain probe BEFORE running the loop
correlates with post-loop-0 SH (ρ > 0.70, Spearman).
This would enable pre-run domain assessment without a full DES run.

### H0

SH does not predict loop depth or perturbation benefit.
The correlation is noise from the small Paper 4/5 dataset.

-----

## Three-Phase Design

### Phase 1: Retrograde Validation (no new runs)

Compute SH from existing Paper 4 and Paper 5 data.
Correlate with loop depth. Estimate SH*.

### Phase 2: Prospective Prediction (new domains, new runs)

Select 13 new domains: 10 core domains plus 3 counterexamples. Predict high/low SH before running.
Run P4 config (no perturbation). Measure actual SH and loop depth.
Compare prediction vs outcome.

### Phase 3: Controlled Comparison (high-SH domains only)

On domains confirmed high-SH from Phase 2:
run P4 (no perturbation) vs P5v05 (SPL perturbation).
Measure depth lift.

-----

## Phase 1: Retrograde Validation

### 1.1 Compute SH from existing data

```python
# paper6/compute_sh.py

import json, glob, math
from nlp_backend import SPLNLPBackend
from spl import compute_jsd

spl = SPLNLPBackend(model_name="all-MiniLM-L6-v2", builder_origin="alpha")

def compute_semantic_headroom(state_file: str) -> dict:
    """
    Compute SH from a completed DES state file.
    SH = mean(√JSD(π(cᵢ), centroid(claims)))
    """
    with open(state_file) as f:
        state = json.load(f)

    claims = state.get("claims", {})
    sealed = [c for c in claims.values() if c.get("sealed")]

    if len(sealed) < 3:
        return {"sh": None, "reason": "too_few_sealed_claims", "n": len(sealed)}

    # Project each sealed claim into Π
    projections = []
    for c in sealed:
        text = f"{c.get('subject','')} {c.get('predicate','')} {c.get('object','')}"
        if text.strip():
            proj = spl.project_text(text).P_r
            projections.append(proj)

    if not projections:
        return {"sh": None, "reason": "no_projectable_claims"}

    # Compute centroid
    all_keys = set()
    for p in projections:
        all_keys.update(p.keys())
    centroid = {k: sum(p.get(k, 0.0) for p in projections) / len(projections)
                for k in all_keys}
    total = sum(centroid.values())
    if total > 0:
        centroid = {k: v/total for k, v in centroid.items()}

    # Compute SH = mean √JSD distance from centroid
    distances = [math.sqrt(compute_jsd(p, centroid)) for p in projections]
    sh = sum(distances) / len(distances)

    sh_norm = sh * math.log2(max(len(projections), 2))

    # SH_entropy: entropy of centroid distribution
    # High entropy = many relation types represented = broad semantic coverage
    centroid_h = -sum(v*math.log2(v) for v in centroid.values() if v > 0)
    n_rels = len([v for v in centroid.values() if v > 0])
    centroid_h_norm = centroid_h / math.log2(n_rels) if n_rels > 1 else 0.0

    return {
        "sh": round(sh, 4),
        "sh_norm": round(sh_norm, 4),
        "sh_entropy": round(centroid_h_norm, 4),
        "n_claims": len(projections),
        "min_dist": round(min(distances), 4),
        "max_dist": round(max(distances), 4),
        "centroid_entropy_raw": round(centroid_h, 4),
    }
```

### 1.2 Retrograde SH for Paper 4 and Paper 5 domains

Apply to loop_000_state.json for each domain (first loop state only).
First loop is the baseline – before any perturbation changes the graph.

Expected output:

```
Domain  | SH (loop 0) | P4 depth | P5v05 depth | Depth lift
--------|-------------|----------|-------------|----------
R01     | ?           | 2        | 2           | 0
R02     | ?           | 3        | 1           | -2
R03     | ?           | 4        | 1           | -3
R04     | ?           | 3        | 5           | +2
R05     | ?           | 4        | 1           | -3
```

Hypothesis: R04 SH > R01 > R02 ≈ R03 ≈ R05.

### 1.3 Estimate SH*

SH* is the threshold that best separates:

- domains where depth lift > 0 (R04 in Paper 5)
- domains where depth lift ≤ 0 (R01/R02/R03/R05)

With only 5 datapoints this is exploratory, not conclusive.
Phase 2 is required for validation.

Report: SH* estimate, confidence interval (bootstrap if n permits),
and explicit caveat that n=5 is insufficient for robust calibration.

-----

## Phase 2: Prospective Prediction

### 2.1 Domain selection (13 new domains: 10 core + 3 counterexamples)

Select domains across a range of expected semantic headroom.

**Expected HIGH SH (broad conceptual scope):**

```python
HIGH_SH_DOMAINS = {
    "N01": "Is consciousness reducible to physical brain processes?",
    "N02": "What determines the rise and fall of civilizations?",
    "N03": "Is artificial general intelligence achievable within 20 years?",
    "N04": "What is the relationship between language and thought?",
    "N05": "Does economic inequality harm social cohesion?",
}
```

**Expected LOW SH (narrow empirical scope):**

```python
LOW_SH_DOMAINS = {
    "N06": "Does aspirin reduce cardiovascular event risk in healthy adults?",
    "N07": "Does sleep deprivation impair working memory?",
    "N08": "Do smaller class sizes improve standardized test scores?",
    "N09": "Does caffeine improve short-term cognitive performance?",
    "N10": "Do higher minimum wages reduce employment in fast food?",
}
```

**Counterexample domains (test confound: topic ambiguity vs genuine SH):**

```python
COUNTEREXAMPLE_DOMAINS = {
    "N11": "What are the climate tipping points for irreversible warming?",   # empirical but HIGH SH
    "N12": "Does gut microbiome diversity affect depression outcomes?",        # empirical but HIGH SH
    "N13": "Is the trolley problem resolved under strict utilitarian rules?",  # philosophical but LOW SH
}
```

Rationale: N11/N12 are empirical but genuinely contested with multiple
mechanisms – expected HIGH SH despite empirical framing.
N13 is philosophical but has a fixed rule set that constrains the answer
space – expected LOW SH despite philosophical framing.
If SH correlates with high/low split but not with topic ambiguity,
the confound is ruled out.

Prediction (pre-registered before any runs):

- N01-N05, N11, N12: SH > SH*, depth > 3, perturbation benefit expected
- N06-N10, N13: SH < SH*, depth ≤ 2, perturbation benefit not expected

### 2.2 Pre-run SH estimation (H3)

Before running any DES loop, estimate SH via a domain probe:
Generate 10 representative claims about the domain using the LLM,
project them into Π, compute centroid and mean distance.

```python
DOMAIN_PROBE_PROMPT = """
Domain question: {question}

Generate 10 diverse factual claims about this topic.
Claims should represent different aspects, perspectives, and
sub-questions within this domain.

Return ONLY: 10 claims, one per line, as simple declarative sentences.
No hedging, no explanation."""

def estimate_sh_prerun(question: str, k: int = 10) -> float:
    """
    Estimate SH before running DES.
    Uses LLM-generated domain probe claims.
    """
    response = call_llm(DOMAIN_PROBE_PROMPT.format(question=question))
    probe_claims = [l.strip() for l in response.split("\n")
                    if l.strip() and len(l.strip()) > 10][:k]

    projections = [spl.project_text(c).P_r for c in probe_claims]
    if not projections:
        return 0.0

    all_keys = set()
    for p in projections: all_keys.update(p.keys())
    centroid = {k: sum(p.get(k,0) for p in projections)/len(projections)
                for k in all_keys}
    total = sum(centroid.values())
    if total > 0:
        centroid = {k: v/total for k,v in centroid.items()}

    distances = [math.sqrt(compute_jsd(p, centroid)) for p in projections]
    return sum(distances) / len(distances)
```

### 2.3 Run protocol

For each of 13 new domains (10 core + 3 counterexamples):

1. Compute pre-run SH estimate (domain probe)
1. Run DES P4 configuration (no perturbation, max 20 loops)
1. Compute post-loop-0 SH from actual ClaimGraph
1. Record loop depth and termination outcome
1. Compare pre-run estimate vs post-loop-0 SH (H3)

No perturbation in Phase 2. Clean measurement of SH → depth relationship.

-----

## Phase 3: Controlled Comparison

### 3.1 Selection

Take the Phase 2 domains where:

- post-loop-0 SH > SH* (confirmed high headroom)
- at least 3 domains

Run each domain twice:

- P4 config (no perturbation)
- P5v05 config (SPL trajectory control)

### 3.2 Comparison metrics

Per domain:

- Depth lift = P5v05_depth - P4_depth
- Novel claim rate at loop 5 (if reached)
- Escape distance trajectory

Cross-domain:

- Does depth lift correlate with SH above threshold?
- Does depth lift approach zero as SH approaches SH*?

-----

## Metrics

### M1: Semantic Headroom (SH)

```python
SH = mean(sqrt(JSD(project(c), centroid(all_claims))))
```

Primary predictor. Computed from sealed claims in loop 0 state.

### M2: Pre-run SH estimate

Computed from 10 LLM-generated domain probe claims before any DES run.
Compared to M1 for H3 validation.

### M3: SH-depth correlation

Primary: Spearman ρ between SH and loop depth.
Rationale: SH and depth may be monotonic but not linear.
With small n, rank correlation is more robust than Pearson.
Secondary: Pearson r (exploratory only, reported with caveat n=5 for Phase 1).
Expected: ρ > 0.70.

### M4: SH* threshold accuracy

Fraction of domains correctly classified (high/low depth) by SH > SH*.
Expected: > 80% on Phase 2 data.

### M5: Perturbation benefit rate in high-SH domains

Fraction of high-SH domains where P5v05_depth > P4_depth.
Expected: > 60%.

### M6: Claim count (control variable)

Number of sealed claims per loop 0 state.
Required control: domains with more claims have more raw material
for SH computation. Report SH alongside claim_count.

### M7: SH_norm (exploratory size-adjusted proxy)

```python
SH_norm = SH * math.log2(max(n_claims, 2))
```

Exploratory size-adjusted proxy. Larger ClaimGraphs have more
opportunity to spread in Π. The log2 scaling is a pragmatic choice
– not theoretically derived – and should be treated as exploratory.
Report both SH and SH_norm. Do not use SH_norm as primary metric;
report it alongside SH with explicit caveat about scaling choice.

-----

## New Domains for Phase 2

Explicit rationale for high/low SH classification:

High SH rationale: broad conceptual scope, genuine philosophical
or empirical disagreement, multiple incommensurable frameworks,
no dominant paradigm. Claims will project into diverse regions of Π.

Low SH rationale: narrow empirical question, dominant paradigm,
well-defined measurement instruments, limited conceptual vocabulary.
Claims will cluster tightly in Π around a few DYNAMIC relations.

-----

## Failure Conditions

```python
# Phase 1 fails if:
if spearman_rho(SH_retrograde, depth) < 0.50:
    PHASE1 = "SH_NOT_PREDICTIVE"
    # Pearson r reported additionally as exploratory
    # Do not proceed to Phase 2/3 with high confidence

# Phase 3 fails if:
if perturbation_benefit_rate_high_sh < 0.40:
    PHASE3 = "PERTURBATION_BENEFIT_NOT_CONFIRMED"
```

If Phase 1 fails: report SH as a null predictor and conclude that
domain-level semantic properties do not explain loop depth variability.
This is a valid outcome – it would suggest the constraint is elsewhere.

-----

## Two SH Definitions

Paper 6 reports both SH variants and compares their predictive power:

**SH_distance** = mean(√JSD(π(cᵢ), centroid))
Measures spread of claims in Π. Current primary definition.
Captures: are claims distributed across different regions of Π?

**SH_entropy** = H_norm(centroid)
Measures how many relation types are represented in the centroid.
High entropy = claims collectively cover many relation families (DYNAMIC,
EPISTEMIC, MODEL, etc.). Low entropy = claims cluster around one family.
Captures: does the domain generate structurally diverse claims?

Hypothesis: SH_entropy may better explain R04's performance than
SH_distance, because R04 (GDP/wellbeing) naturally generates claims
across DYNAMIC, STATISTICAL, EPISTEMIC, and NORMATIVE relation families.

-----

## K(G) Suppression Claim (from Paper 3/5 connection)

Paper 3 showed DES resolves tensions before sealing.
Paper 5 found K(G) max = 0.013 across all domains (threshold 0.55).

These findings are connected: DES may actively suppress curvature
before measurement. T1/T5/T9 resolve contradictions and produce
synthesis claims with high confidence. The resulting sealed ClaimGraph
is internally consistent – not because the domain is simple, but
because DES has done its job.

This means K(G) on DES-sealed claims is systematically biased toward
zero. It is not a useful attractor signal for DES output.
It may be useful for non-DES claim graphs (e.g. CoT outputs, raw LLM
extractions) where tensions are not resolved before sealing.

This is not a limitation of Paper 6 – it is a derived claim:

> DES actively suppresses epistemic curvature before sealing.
> K(G) therefore measures DES quality, not attractor risk.

-----

## Practical Implication: DES Resource Scheduler

If H3 holds (pre-run SH estimate correlates with post-loop-0 SH):

```
if estimate_sh_prerun(question) < SH*:
    run_des_single_pass()          # no trajectory control, save cost
else:
    run_des_with_spl_perturbation() # activate SPL escape vectors
```

This is a domain-aware resource scheduler for DES.
Not just a theoretical contribution – a practical deployment decision rule.

-----

## Target Claim for Paper 6

> Semantic headroom – the mean projection distance of a domain's claims
> from their centroid in the semantic projection space Π – is a measurable
> precondition for effective epistemic trajectory control in autonomous
> research loops. Below a domain-specific threshold, no perturbation
> architecture can extend loop depth, because the domain exhausts its
> conceptual space within a single DES run. Above the threshold, SPL-based
> trajectory control produces measurable loop depth extension.

-----

## Relation to Prior Papers

|Paper         |Contribution                                   |Relation to Paper 6                 |
|--------------|-----------------------------------------------|------------------------------------|
|Paper 0 (2025)|Epistemic consistency + controlled perturbation|Theoretical foundation              |
|Paper 3       |DES resolves tensions before sealing           |Why K(G) is low; claims are coherent|
|Paper 4       |Semantic saturation without perturbation       |P4 depth baseline for SH correlation|
|Paper 5       |SH identified as binding constraint            |Motivates Paper 6                   |
|Paper 6       |SH as measurable predictor                     |This paper                          |

-----

## What NOT to implement

- No full Alexandria integration
- No sigma_stability implementation
- No new DES internals
- des.py remains black-box subprocess

The SPL is used only for claim projection (nlp_backend.py) and
JSD computation (spl.py). No other SPL components needed.

-----

## Status

Design memo. Not yet pre-registered.
Pre-registration: commit this document before Phase 1 analysis.
Phase 1 can begin immediately using existing Paper 4/5 state files.
No new LLM calls needed for Phase 1.

GitHub: hstre/DES (new branch: paper6/semantic-headroom)

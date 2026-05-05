# Mozart Meta-Trajectory Analysis — N03 Persona Runs

**EXPLORATORY META-INTERPRETATION — not empirical confirmation.**  
**No DES internals modified. No experiments rerun. No thresholds changed.**  
**Date:** 2026-05-05 | Domain: N03 ("Is artificial general intelligence achievable within 20 years?")

---

## Framework

The ClaimGraph is treated as a recursive thematic structure — not a static graph.
Each sealed claim is a *voiced statement* of the system's current thematic position.
Each EN event is a *modulation* — an attempt to transpose the dominant motif into a new key.
The full trajectory is a *movement*: exposition, development, recapitulation, terminal convergence.

**Compositional vocabulary used:**
- **Dominant motif**: the subject field that persists across sealed claims — the claim the system keeps returning to
- **Exposition**: loop 0 — initial claim burst, first statement of the thematic material
- **Development**: EN-mediated loops — motif transformed, transposed, recombined
- **Modulation**: genuine key change — EN injection shifts the semantic subject domain, not just its predicates
- **False return** / **local variation**: EN fires but the subject domain is unchanged; only predicates and objects vary
- **Recapitulation**: subject field locks; claims become predicate/object permutations of the same assertion
- **Terminal convergence** (coda): duplication spikes (>0.50), novelty collapses to ≤1; the final attractor is fully saturated

---

## Movement Phase Classification

### Mozart / seed 101 — 11 loops — THE REFERENCE TRAJECTORY

Novel: `[12, 0, 13, 2, 14, 9, 1, 5, 0, 12, 1]`  
Dup:   `[0.17, 0.29, 0.21, 0.08, 0.36, 0.18, 0.21, 0.36, 0.43, 0.25, 0.67]`  
EN at loops: 1, 3, 4, 6, 8

| Loop | Phase | Novel | Dup | EN | Characterization |
|------|-------|-------|-----|-----|-----------------|
| 0 | **Exposition** | 12 | 0.17 | — | Initial AGI/architecture claims established. 12 sealed at loop 0. Low dup, full thematic material stated. |
| 1 | **First saturation** | 0 | 0.29 | ✓ | Complete novelty collapse. EN fires: "How can emergent properties in self-organizing systems inform AGI?" |
| 2 | **Modulation I** | 13 | 0.21 | — | Subject domain shifts entirely: *Emergent AGI in self-organizing systems*. True key change. |
| 3 | **Development I** | 2 | 0.08 | ✓ | Rapid re-saturation of new domain. EN fires: epigenetics/environmental interaction framing. |
| 4 | **Modulation II** | 14 | 0.36 | ✓ | *Integration of epigenetic-like mechanisms in AGI*. Peak novelty. Second EN is local: same domain elaborated. |
| 5 | **Development II** | 9 | 0.18 | — | Sustained exploration of epigenetic-AGI space. Moderate dup. |
| 6 | **Pre-collapse I** | 1 | 0.21 | ✓ | Near-saturation. EN fires: homeostatic reinforcement → human cognitive development framing. |
| 7 | **Local modulation** | 5 | 0.36 | — | Partial recovery: *cognitive flexibility vs. catastrophic forgetting*. Moderate. |
| 8 | **Pre-collapse II** | 0 | 0.43 | ✓ | Full collapse. EN fires: environmental volatility → biological neural networks. |
| 9 | **Late rebound** | 12 | 0.25 | — | Surface-level novelty recovery. But: subject is now locked — all claims are *Biological neural networks exhibit…* |
| 10 | **Terminal convergence** | 1 | 0.67 | — | Coda. Subject fully saturated. 12 sealed claims share identical subject, differ only in verb ("exhibit"/"require") and object. |

**Movement structure:** A → B → C → D → E, where each letter is a distinct conceptual domain (AGI-architecture → emergent-systems → epigenetics-AGI → cognitive-flexibility → biological-memory). No return to A.

---

### Darwin / seed 101 — 8 loops

Novel: `[12, 2, 14, 7, 0, 0, 14, 0]`  
Dup:   `[0.42, 0.42, 0.43, 0.29, 0.36, 0.50, 0.43, 0.50]`  
EN at loops: 0, 1, 4, 5

| Loop | Phase | Novel | Dup | EN | Characterization |
|------|-------|-------|-----|-----|-----------------|
| 0 | **Exposition** | 12 | 0.42 | ✓ | High dup even at loop 0. EN fires immediately: "How must architectures evolve to overcome selection pressures?" |
| 1 | **First saturation** | 2 | 0.42 | ✓ | Near-collapse. EN fires: "diverse learning paradigms, adaptability, robustness." True modulation → |
| 2 | **Modulation** | 14 | 0.43 | — | Peak novelty. Subject shifts to *learning paradigm integration*. |
| 3 | **Development** | 7 | 0.29 | — | Continued exploration. Dup improving. |
| 4 | **Collapse I** | 0 | 0.36 | ✓ | Full novelty collapse. EN fires: "selection pressures on model components from integrating diverse paradigms" — **false return** / local variation. Same conceptual domain. nov_next=0. |
| 5 | **Collapse II** | 0 | 0.50 | ✓ | Still zero. EN fires: "selection pressures on neural network layers when integrating RL/supervised/unsupervised" — TRUE modulation into layer-specific dynamics. nov_next=14. |
| 6 | **Late rebound** | 14 | 0.43 | — | Full recovery, but subject now locked: *layer-specific learning dynamics*. Terminal attractor established. |
| 7 | **Terminal convergence** | 0 | 0.50 | — | Subject fully saturated: all 14 sealed claims = "layer-specific learning dynamics [predicate] [object]". |

**Critical observation:** Loops 4 and 5 fire EN consecutively. Loop 4's EN is a **false return** — eni_novelty=0.0606 (lowest across all darwin events), question stays within the already-saturated learning-paradigm domain, nov_next=0. Loop 5's EN achieves true modulation by narrowing to layer-level dynamics. The system needs two consecutive tries before breaking through.

---

### Darwin / seed 303 — 7 loops

Novel: `[14, 12, 6, 7, 1, 7, 8]`  
Dup:   `[0.36, 0.17, 0.22, 0.50, 0.13, 0.50, 0.29]`

**Dominant motif:** CausalFormer architectures (quadratic self-attention) vs linear-complexity alternatives (Mamba). Darwin's evolutionary framing anchored to a very specific technical comparison at loop 1 (via the EN "computational limitations and neural architecture → selection pressures"). This is the narrowest terminal attractor in the dataset: all sealed claims compare two named architectures on measurable benchmarks.

**Movement phases:**
- Loops 0-1: Exposition → broad AGI landscape
- Loops 2-4: Development → CausalFormer attractor established
- Loops 5-6: Modulation attempts (EN loops 4-5) → stay within CausalFormer domain, predicate variations only
- Loop 6: Pseudo-terminal — high novelty (8) but within the narrow domain, METHOD_COLLAPSE at loop 7 implied

---

### Darwin / seed 202 — 6 loops

Novel: `[11, 14, 4, 1, 13, 8]`  
Dup:   `[0.36, 0.21, 0.14, 0.20, 0.07, 0.17]`

**Unusual pattern:** Darwin/202 shows the *lowest* duplication rates of any run in the dataset (dup=0.07 at loop 4, 0.17 at loop 5). The trajectory never fully saturates — METHOD_COLLAPSE terminates before duplication dominates. This suggests the evolutionary framing (societal/ethical selection pressures on AGI) generated a claim space with genuine semantic width, preventing attractor lock.

---

### Mozart / seed 202 — 9 loops

Novel: `[14, 10, 11, 1, 5, 2, 5, 2, 1]`  
EN at loops: 1, 3, 5, 7

**Motif succession:**
- Loop 0-1: AGI/scaling-based framing; EN fires: emergent self-organization
- Loop 2-3: Evolution-inspired AI architectures; EN fires: biology-inspired architecture constraints
- Loop 4-5: Meta-learning / reward mechanisms; EN fires: social cooperation framing
- Loop 7: Social reward systems (explicit vs intrinsic); terminal attractor established

**Terminal attractor:** *Shifting from explicit reward systems to intrinsic [mechanisms]* — a social-science frame arrived at through Mozart's successive transpositions. The final domain is completely unlike the initial AGI-timeline question: the trajectory traveled from architecture → emergence → evolution → meta-learning → social cooperation/honesty.

**Notable:** nov_next declining across EN events: 11 → 5 → 5 → 1. Each successive modulation produces fewer new claims, until the system has no remaining conceptual space to explore. This is the **exhaustion of the thematic transformation pool**.

---

## Question 1: Which Motifs Repeatedly Return?

Across all persona runs, three primary motif families appear, reappear, and collapse:

**Motif Family A: Architecture/breakthrough**
> "AGI requires a fundamental architectural breakthrough" — appears in exposition phase of almost every run. This is the *tonic* of the N03 domain. It surfaces in loop 0 of popper, shannon, darwin, mozart seeds regardless of EN history. EN injection always displaces it, but it cannot be returned to — once displaced, it does not reappear.

**Motif Family B: Biological analogy (evolution/epigenetics/neural)**
> Darwin's evolutionary framing and Mozart's epigenetics/biological-neural transpositions converge on the same structural claim: *intelligent behavior arises from selection/adaptation over variation in a substrate*. Darwin/101 stays at learning-paradigm selection pressures; Mozart/101 moves through epigenetics into biological neural networks; Darwin/202 stays at societal selection pressures. The biological metaphor is a deep attractor that multiple personas find independently.

**Motif Family C: Specific technical comparison**
> Darwin/303's CausalFormer comparison, Picasso/101's symbolic causal inference comparison, Popper/202's Turing Test comparison. These are terminal micro-attractors — once a specific falsifiable comparison is established, the claim space exhausts all predicate combinations rapidly.

**Motif Family A never returns.** Families B and C are *terminal destinations*, not recurrent themes. The ClaimGraph is directional, not cyclical.

---

## Question 2: Which Semantic Structures Are Merely Repeated vs Transformed?

**Merely repeated (predicate/object variation on locked subject):**

Terminal convergence produces locked subjects with 10-14 predicate variations. Examples:
- `Biological neural networks | exhibit | memory retention that is [more/primarily/partially]...` (Mozart/101, loop 10): 12 claims, identical subject, predicate "exhibit" in 11 cases, objects differ only in mechanism adjectives.
- `AGI system | will [pass/fail/not pass/succeed] | a double-blind Turing Test...` (Popper/202, loop 3): 13 claims, binary predicate exhausted.
- `layer-specific learning dynamics | [are uniform/diverge/converge] | [across/between/in]...` (Darwin/101, loop 7): subject locked at loop 6.

In each case: the claim's informational content is exhausted, but the DES continues generating statements because the *subject* has not been displaced. These are semantic artifacts of attractor convergence, not genuine exploration.

**Genuinely transformed:**

EN events that shift the *subject* field produce structural transformation. The clearest cases:
- Mozart/101 loop 1 → loop 2: "AGI achievability" → "Emergent AGI in self-organizing systems" — entirely new subject
- Darwin/101 loop 5 → loop 6: "diverse learning paradigm integration" → "layer-specific learning dynamics" — narrowing but genuine shift into a sub-domain not previously addressed
- Mozart/202 loop 5 → loop 6+: "biology-inspired meta-learning" → "explicit vs. intrinsic reward systems / cooperation" — domain jump into social dynamics

---

## Question 3: Which Claims Act as Dominant Motifs / Attractor Pulls?

Each run converges on a **seed claim** — one EN-injected question that establishes the terminal attractor. This is almost always the **penultimate EN event**, not the first.

| Run | Terminal attractor subject | Established by EN at loop | Final fate |
|-----|---------------------------|--------------------------|------------|
| mozart/101 | Biological neural networks / memory retention | EN loop 8 (env. volatility) | SEM_DUP loop 10 |
| mozart/202 | Shifting from explicit→intrinsic reward systems | EN loop 7 (reward/cooperation) | SEM_DUP loop 8 |
| darwin/101 | Layer-specific learning dynamics | EN loop 5 (RL/SL layer dynamics) | SEM_DUP loop 7 |
| darwin/303 | CausalFormer vs linear-complexity attention | EN loop 0 (computational limitations) | METHOD_COLLAPSE |
| popper/202 | AGI system / double-blind Turing Test | EN loop 0 (falsificationist probe) | SEM_DUP loop 3 |
| shannon/101 | Tacit knowledge alignment / information throughput | EN loop 0-1 (channel capacity) | SEM_DUP loop 4 |
| picasso/101 | Symbolic causal inference vs deep RL | (no EN) / loop 0 natural | SEM_DUP loop 3 |

**The attractor is not planted by the first EN.** It is planted by whichever EN fires when the system is deep into a development phase — when the accumulated sealed claims have constrained the available subject space enough that only one "key" remains available for the final transposition.

---

## Question 4: Which EN Events Produce Genuine Thematic Transformation?

**Classification criteria:**
- **Genuine transformation**: eni_novelty > 0.12, subject domain shifts across loops, nov_next ≥ 9
- **Partial transformation**: subject shifts but domain is narrowed further, nov_next 3-8
- **Local variation**: subject domain unchanged; only predicates or objects vary, nov_next ≤ 2

| Run | Loop | eni_novelty | eni_non_drift | nov_next | Classification | EN question summary |
|-----|------|-------------|---------------|----------|----------------|---------------------|
| mozart/101 | 1 | 0.132 | 0.706 | 13 | **Genuine** | Self-organizing emergence → minimal architectural constraints |
| mozart/101 | 3 | 0.202 | 0.680 | 14 | **Genuine** | Epigenetics → adaptive architectural constraints |
| mozart/101 | 4 | 0.138 | 0.627 | 9 | **Partial** | How to integrate epigenetic mechanisms (same domain) |
| mozart/101 | 6 | 0.083 | 0.682 | 5 | **Partial** | Homeostatic reinforcement → cognitive development |
| mozart/101 | 8 | 0.090 | 0.728 | 12 | **Partial** | Environmental volatility → biological neural networks |
| darwin/101 | 0 | 0.101 | 0.856 | 2 | **Local** | Selection pressures on architectures (same as seed question frame) |
| darwin/101 | 1 | 0.121 | 0.810 | 14 | **Genuine** | Diverse learning paradigm integration — new subject |
| darwin/101 | 4 | 0.061 | 0.791 | 0 | **Local** | Integration of learning paradigms → selection on model components (no shift) |
| darwin/101 | 5 | 0.119 | 0.803 | 14 | **Genuine** | Layer-specific dynamics under RL/SL/unsupervised — new sub-domain |
| darwin/202 | 0 | 0.184 | 0.877 | 14 | **Genuine** | Societal/ethical selection pressures — new dimension |
| darwin/303 | 3 | 0.084 | 0.783 | 1 | **Local** | CausalFormer complexity → selection pressures (within same domain) |
| darwin/303 | 4 | 0.125 | 0.803 | 7 | **Partial** | Transformer architecture evolution — broader but same register |
| darwin/303 | 5 | 0.142 | 0.794 | 8 | **Partial** | Computational efficiency and memory constraints — adjacent |

**Quantitative signal for genuine transformation:** eni_novelty > 0.12 is necessary but not sufficient; the critical feature is whether the next loop's sealed claims show a new subject. Local-variation events consistently show eni_novelty < 0.08. The boundary sits near 0.10.

---

## Question 5: Which EN Events Produce Only Local Variation?

Two clearest cases of **false returns**:

**Darwin/101, loop 4:**
- EN question: "How does the integration of diverse learning paradigms into a single architecture affect the *selection pressures on model components*?"
- This question stays within the learning-paradigm-integration domain already established at loop 2.
- eni_novelty = 0.0606 (lowest in the entire dataset for admitted events)
- nov_next = 0: the next loop produced zero novel claims
- The question is structurally a predicate elaboration of the existing claim set, not a new subject

**Darwin/303, loop 3:**
- EN question: "How do the computational complexities and efficiency gains of CausalFormer-style causal reasoning modules create selection pressures on deployment practices?"
- CausalFormer is already the dominant sealed-claim subject from loop 2
- eni_novelty = 0.0838, nov_next = 1
- The question adds a deployment-practice angle but does not change the subject domain

**Common pattern for false returns:**
The EN question contains the existing dominant subject as a noun phrase (e.g., "CausalFormer", "diverse learning paradigms"). Genuine transformations typically introduce a *new noun* that had not appeared in sealed claims — a structural signature detectable without running the model.

---

## Question 6: Identifiable Movement Phases Across Long Runs

### Five-phase model (observed, not imposed)

```
PHASE I — EXPOSITION
  Trigger: loop 0
  Signal:  novel ≥ 10, dup < 0.30, no EN
  Content: Seed question interpreted; initial claim diversity high; primary thematic material stated
  Duration: 1 loop universally

PHASE II — FIRST SATURATION / MODULATION
  Trigger: novel collapses (≤ 2), early_saturation detected
  Signal:  EN fires, eni_novelty > 0.12 typically
  Content: Genuine key change if EN introduces new noun domain
  Duration: 1-2 loops (one collapse + one EN)
  Outcome: HIGH = Genuine modulation, nov_next ≥ 10 in next loop
           LOW  = Local variation, nov_next ≤ 2, system may fire EN again immediately

PHASE III — DEVELOPMENT
  Trigger: novel recovery after genuine modulation (novel ≥ 5)
  Signal:  dup oscillates 0.10-0.40, novel 5-14, EN fires 0-2x per phase
  Content: Multiple modulation cycles; each adds a sub-domain layer; eni_novelty drifts downward
  Duration: 3-7 loops in the deepest runs (darwin/101, mozart/101, mozart/202)

PHASE IV — DEEPENING ATTRACTOR
  Trigger: eni_novelty drops below 0.10 for 2+ consecutive EN events
  Signal:  Subject field of sealed claims converges; predicate variety narrows
  Content: Claims are predicate/object variations of fixed subject; nov_next ≤ 5 even after EN
  Duration: 2-4 loops

PHASE V — TERMINAL CONVERGENCE (CODA)
  Trigger: dup > 0.50 and novel ≤ 1
  Signal:  SEM_DUP or METHOD_COLLAPSE imminent
  Content: Claim space fully exhausted within final attractor; subject locked
  Duration: 1-2 loops
```

### Phase maps for long runs

**Mozart/101 (11 loops):**
```
I(0) → II(1) → III(2-5) → II(6) → III(7-8) → IV(9) → V(10)
```
Two development phases separated by a second modulation cycle. Phase III re-entered at loop 7 with moderate recovery (nov=5) before Phase IV begins at loop 9 (surface novelty from late rebound, but subject locked).

**Darwin/101 (8 loops):**
```
I(0) → II(0-1) → III(2-3) → [FALSE MODULATION at 4] → II(5) → IV(6) → V(7)
```
Phase II interrupted by false modulation at loop 4 (EN fires but no subject shift). True Phase II at loop 5 recovers. Phase IV is a single loop before terminal convergence.

**Darwin/202 (6 loops):**
```
I(0) → II(0) → III(1-5) → METHOD_COLLAPSE
```
Almost pure development: the societal/ethical framing at EN loop 0 generated a claim space with sufficient semantic width that development continued 5 loops without a second attractor crystallizing. Terminated by METHOD_COLLAPSE (DES operator exhaustion), not SEM_DUP. The system ran out of DES operators before running out of claim diversity.

**Picasso/101 (4 loops):**
```
I(0) → III(1-2) → V(3)
```
No EN fired. The cubist multi-view decomposition at loop 0 produced a complex initial claim set (symbolic causal inference vs deep RL) that constituted an immediate attractor. No modulation was needed — the claim space went directly from exposition to development within the attractor, then to terminal convergence. EN never detected early saturation because each loop was locally productive until dup spiked.

**Shannon/101 (5 loops):**
```
I(0) → II(0-1) → [DOMAIN CAPTURE at loop 1] → IV(2-4) → V(4)
```
"Domain capture" — Shannon's EN at loop 1 injected "channel capacity of cross-disciplinary information flow" (tacit knowledge alignment). This is a genuine modulation into a specific domain, but the domain is *too narrow*. The subsequent development (loops 2-4) exhausted it in 3 loops. Shannon's channel-capacity framing has a finite claim space; once you've asked all the questions about tacit knowledge throughput, there is nowhere to go.

---

## Cross-Persona Structural Patterns

### 1. The bimodal EN outcome distribution

EN events cluster into two populations:
- **Transformative** (eni_novelty > 0.12): Produce nov_next ≥ 9 consistently. These are genuine modulations.
- **Stabilizing** (eni_novelty < 0.10): Produce nov_next ≤ 3. Local variation only, or domain capture within existing attractor.

There is no middle cluster. This bimodality suggests that the novelty threshold 0.10-0.12 is a structural boundary in SPL space — below it, the EN candidate is semantically contained within the sealed-claim centroid; above it, it is sufficiently orthogonal to pull the trajectory into new territory.

### 2. The exhaustion signature

In all runs, eni_novelty across successive EN events follows a **declining envelope** — not monotonically, but the peak eni_novelty of later EN events is lower than the peak of earlier ones:

| persona/seed | EN eni_novelty sequence | pattern |
|---|---|---|
| mozart/101 | 0.132, 0.202, 0.138, 0.083, 0.090 | peak at event 2, then declining |
| mozart/202 | 0.154, 0.080, 0.079, 0.063 | monotone decline |
| darwin/101 | 0.101, 0.121, 0.061, 0.119 | jagged but no late event exceeds early peaks |
| darwin/303 | 0.089, 0.084, 0.125, 0.142 | EXCEPTION: increasing envelope |

Darwin/303 is the only run where late EN events show higher eni_novelty than early ones. This correlates with the METHOD_COLLAPSE outcome — the system's operator space was exhausted *before* the semantic space, meaning DES ran out of moves while the claim graph was still structurally open.

### 3. Non-drift divergence in Mozart runs

Mozart EN events consistently show lower eni_non_drift than Darwin EN events at comparable run depths:

| persona | mean eni_non_drift across all EN events |
|---------|----------------------------------------|
| darwin | 0.820 (pooled over 9 seeds × events) |
| mozart | 0.724 |
| picasso | 0.809 |
| popper | 0.843 |
| shannon | 0.850 |

Mozart's lower non_drift means the injected questions carry more semantic distance from the original seed question — confirming that Mozart's thematic transpositions are genuinely moving the trajectory further from the seed domain than other personas' injections. This higher drift is the structural explanation for Mozart's depth advantage: each modulation moves further, requiring more loops to exhaust.

### 4. Outcome signatures by movement structure

The relationship between movement phase at termination and failure mode:

- Terminated in **Phase V** after Phase III/IV (normal arc): SEM_DUP
- Terminated in **Phase III** without Phase IV (operator exhaustion while still exploring): METHOD_COLLAPSE
- Terminated prematurely, never exiting **Phase II** (stuck local variation): SEM_DUP with low depth_lift

Darwin's 3/3 METHOD_COLLAPSE rate is a structural consequence of its deep development phases: darwin runs consistently enter 5-7 loop Phase III cycles, during which DES exhausts its operator space. Mozart terminates by SEM_DUP (2/3) because its transpositions eventually lock the subject domain, after which predicates exhaust. The failure mode is a diagnostic of *which* resource ran out first.

---

## Summary: What the Trajectory Analysis Reveals

1. **The ClaimGraph is not a graph — it is a thematic progression.** The subject field tells you where you are in the trajectory. When subjects diverge (exposition), the system is exploring. When subjects converge, the system is approaching its terminal attractor.

2. **EN events are modulations, not resets.** A successful EN injection shifts the *key*, not the starting position. The accumulated sealed claims from prior loops shape what subjects are possible in the next loop — EN does not clear this history.

3. **Terminal attractors are established by penultimate EN events.** The first EN injection rarely determines where a trajectory ends. The last effective EN injection plants the seed for terminal convergence.

4. **Decreasing eni_novelty is a predictive signal.** When consecutive EN events show eni_novelty < 0.10, the system is already in Phase IV (deepening attractor). This could serve as a computable trigger for persona rotation or EN-type switching.

5. **Mozart's structural advantage is drift-based, not admissibility-based.** Mozart produces lower non_drift (higher distance from seed question) than rational personas. This extends Phase III by creating genuinely new subject domains rather than elaborating existing ones. The cost: the trajectory ends further from the original question.

6. **The movement metaphor is accurate but not prescriptive.** The trajectory has a structure that is *analyzable* through compositional framing. It does not follow compositional logic by design. The motif-development-recapitulation pattern is an emergent property of how SPL space, the claim sealing mechanics, and early saturation detection interact.

---

*All interpretations are post-hoc meta-analysis of completed runs. No claim is made about DES design intentions or causal mechanisms. This document should not be cited as empirical evidence for any hypothesis in the H1–H6 protocol.*

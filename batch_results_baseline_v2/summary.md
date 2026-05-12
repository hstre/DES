# DES vs Adversarial CoT — Baseline Comparison v2 (Corrected)

**Model:** deepseek-chat  
**Questions:** 13  
**Evaluator:** blind (randomized A/B assignment, prose-rendered DES output)  

## Evaluator Verdicts

- DES wins: 1/13
- CoT wins: 12/13
- Equal: 0/13

## Per-Dimension Wins (actual, after de-randomization)

| Dimension | DES | CoT | Equal |
|---|---|---|---|
| directional_commitment | 0 | 13 | 0 |
| contradiction_depth | 3 | 10 | 0 |
| synthesis_quality | 1 | 12 | 0 |
| epistemic_novelty | 9 | 4 | 0 |

## Label Bias Check

- DES assigned to A: 5 questions | DES wins when assigned A: 1
- DES assigned to B: 8 questions | DES wins when assigned B: 0
- Label bias detected: No

## Per-Question Results

| QID | DES label | Raw winner | Actual winner | Dir | Ctr | Syn | Nov |
|---|---|---|---|---|---|---|---|
| A1 | A | B | CoT | CoT | CoT | CoT | DES |
| A2 | B | A | CoT | CoT | CoT | CoT | DES |
| A3 | B | A | CoT | CoT | CoT | CoT | DES |
| B1 | B | A | CoT | CoT | CoT | CoT | CoT |
| B2 | A | B | CoT | CoT | DES | CoT | DES |
| B3 | A | B | CoT | CoT | DES | CoT | DES |
| C1 | A | B | CoT | CoT | CoT | CoT | DES |
| C2 | B | A | CoT | CoT | CoT | CoT | DES |
| D1 | B | A | CoT | CoT | CoT | CoT | CoT |
| D2 | B | A | CoT | CoT | CoT | CoT | CoT |
| D3 | B | A | CoT | CoT | CoT | CoT | DES |
| E1 | A | A | DES | CoT | DES | DES | DES |
| E2 | B | A | CoT | CoT | CoT | CoT | CoT |

---

## v1 vs v2 Comparison

| Metric | v1 (biased) | v2 (corrected) |
|---|---|---|
| DES wins | 12/13 | **1/13** |
| CoT wins | 1/13 | **12/13** |
| Evaluator blind | No (labels revealed) | Yes (randomized A/B) |
| DES format | Raw ClaimGraph dump | Prose report |
| Label bias | Not checked | Not detected (diff=1) |

**The v1 result was a methodological artifact.** Format bias (structured JSON dump vs. prose) and label bias (evaluator knew which was DES) combined to produce a 12/13 DES advantage. After correction, the result reverses to 12/13 CoT.

---

## Notable Findings

### CoT wins Directional Commitment 13/13

The 4-step adversarial prompt produces one clear directional claim, one clear counter-claim, and one explicit contradiction check. The evaluator consistently prefers this structure over DES's prose report, which lists multiple competing hypotheses at moderate confidence without committing to a single direction. DES's breadth reads as hedging; CoT's single chain reads as epistemic precision.

### CoT wins Contradiction Depth 10/13

CoT's explicit "STEP 3 — CONTRADICTION CHECK" forces a binary YES/NO classification of the contradiction. The evaluator rewards this clarity. DES reports list competing hypotheses as "supported" vs. "disputed" claims without stating explicitly why they cannot both be true. The structural contradiction in CoT is more legible to the evaluator even when DES's graph contains deeper tensions.

### DES wins Epistemic Novelty 9/13 — the one genuine structural advantage

This is the only dimension where DES's iterative claim accumulation provides real evaluator-detectable value. Examples: A1 — "reduced turnover costs vs. increased turnover costs in high-productivity sectors"; C1 — "algorithmic curation of short-form video linked to measurable reductions in social interaction"; D3 — "off-target risks of somatic editing may be lower than non-editing alternatives in severe monogenic disorders." These non-obvious sub-claim tensions emerge from DES's multi-iteration branching and do not appear in CoT's single-pass falsification.

### E1 is the only DES overall win — the multi-tension question

E1 ("Is free trade both beneficial AND harmful?") is explicitly framed as a two-sided question. DES's report surfaced "two fully supported competing hypotheses and multiple synthesis conclusions that expose fundamental tensions" (evaluator quote). This is precisely where DES's graph depth matters: the question requires more than one contradiction to be productive. E1 is the prototype of the use case where DES is genuinely superior to CoT.

### CoT wins Synthesis Quality 12/13

CoT's STEP 4 produces one scope-bounded synthesis with a single confidence value. DES's report, rendered from T9 synthesis claims, produces 1-2 synthesis bullets that the evaluator finds "vague and low-confidence" or "leaving contradictions unresolved." This is partly a rendering artifact: DES synthesis claims at confidence ~0.50 (T9 clamped) read as uncertain, while CoT synthesizes at 0.70-0.85.

### No label bias detected

DES wins 1/5 when assigned to A (position bias favors A in some models), and 0/8 when assigned to B. Difference = 1, below the threshold of 2. The v2 result is not position-biased.

---

## Recommendation

**Report the v2 result honestly.** The finding is: a well-structured adversarial CoT prompt (4-step: claim → falsification → contradiction check → synthesis) produces outputs that a blind evaluator judges as higher quality on 3 of 4 dimensions (Directional Commitment, Contradiction Depth, Synthesis Quality). DES retains a genuine advantage only on Epistemic Novelty (9/13) and on structurally multi-tension questions (E1 prototype).

**What this means for the paper:**

1. The DES claim should shift from "better than CoT overall" to "produces epistemic novelty not accessible to single-pass methods"
2. The E1 result (multi-tension framing) is the strongest positive evidence for DES
3. The format of DES output (prose report quality) matters as much as the epistemic architecture — the ClaimGraph must be rendered as high-quality prose to compete with CoT's synthesis quality
4. v1 and v2 results together constitute a finding in themselves: evaluation methodology is not neutral; format and label choices produce a 12-point swing in measured performance

---

## Per-Question Justifications


### A1: Does raising the minimum wage increase unemployment?

DES was Output A. Raw winner: B. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: B) — Output B makes a clear directional claim with a specific confidence level and then explicitly states a contradictory counter-claim, whereas Output A hedges by listing competing hypotheses without a clear directional stance.
- **Contradiction Depth**: CoT (raw: B) — Output B identifies a fundamental contradiction between the claim and counter-claim and explains why they cannot both be true in the same context, while Output A merely lists competing hypotheses without deep contradiction analysis.
- **Synthesis Quality**: CoT (raw: B) — Output B provides a precise, scope-bounded synthesis that specifies conditions under which each outcome occurs, resolving the contradiction productively, whereas Output A offers two vague syntheses with low confidence.
- **Epistemic Novelty**: DES (raw: A) — Output A surfaces the non-obvious tension between reduced turnover costs and increased turnover costs in high-productivity sectors, which is a nuanced perspective a domain expert might find insightful.
- **Overall**: CoT — Output B is superior because it demonstrates a clear falsification process, identifies a deep contradiction, and produces a well-scoped synthesis that conditionally resolves the debate, which are core strengths for epistemic evaluation; Output A's novelty does not outweigh its lack of directional clarity and weaker synthesis.

### A2: Is foreign aid effective at reducing poverty?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear directional claim that foreign aid reduces poverty only under specific conditions, whereas Output B hedges with multiple low-confidence conclusions.
- **Contradiction Depth**: CoT (raw: A) — Output A explicitly identifies and checks the direct contradiction between the claim and counter-claim, while Output B lists separate hypotheses without recognizing a fundamental contradiction.
- **Synthesis Quality**: CoT (raw: A) — Output A provides a single, precise synthesis with a clear scope condition (strong institutions), whereas Output B offers two vague, low-confidence syntheses without resolving the tension.
- **Epistemic Novelty**: DES (raw: B) — Output B surfaces the non-obvious insight that aid effectiveness in weak governance contexts depends on channeling through NGOs and local civil society, which is a nuanced perspective not present in Output A.
- **Overall**: CoT — Output A is superior on directional commitment, contradiction depth, and synthesis quality, outweighing B's slight edge in epistemic novelty; A's focused, resolved synthesis is more epistemically robust overall.

### A3: Does immigration reduce wages for native workers?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear initial claim with a specific confidence and then synthesizes a directional conclusion about who loses and who gains, while Output B splits into multiple low-confidence claims without a strong directional stance.
- **Contradiction Depth**: CoT (raw: A) — Output A explicitly identifies and names a fundamental contradiction between wage reduction and wage increase for native workers, whereas Output B merely lists competing hypotheses without articulating a deep contradiction.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a single, precise, scope-bounded synthesis that specifies which native workers are affected and why, while Output B leaves two unresolved synthesis conclusions with low confidence.
- **Epistemic Novelty**: DES (raw: B) — Output B surfaces a non-obvious tension by separately examining high-educational-attainment native workers in non-tradable sectors, which is a less common angle than the typical low-skilled focus in Output A.
- **Overall**: CoT — Output A is clearer, more contradiction-aware, and produces a more coherent and confident synthesis, which makes it superior for answering the research question despite Output B's slightly more novel angle.

### B1: Is GDP a good measure of economic wellbeing?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear initial claim with high confidence and a directly opposing counter-claim, while Output B hedges with low confidence and multiple competing hypotheses.
- **Contradiction Depth**: CoT (raw: A) — Output A identifies a fundamental logical contradiction between two universal statements, whereas Output B merely lists competing hypotheses without explicitly stating their incompatibility.
- **Synthesis Quality**: CoT (raw: A) — Output A provides a precise, scope-bounded synthesis that resolves the contradiction by specifying different definitions of wellbeing, whereas Output B offers two low-confidence conclusions that do not resolve the tension.
- **Epistemic Novelty**: CoT (raw: A) — Output A's synthesis that GDP is both poor and excellent depending on the definition of wellbeing is more nuanced and non-obvious than Output B's standard points about unpaid care work.
- **Overall**: CoT — Output A demonstrates stronger directional commitment, deeper contradiction handling, a more precise synthesis, and greater epistemic novelty, making it the superior evaluation overall.

### B2: Is remote work more productive than office work?

DES was Output A. Raw winner: B. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: B) — Output B makes a clear directional claim with a specific confidence level and then directly states a contradictory counter-claim, whereas Output A's initial claim is heavily hedged with low confidence and its conclusions remain equivocal.
- **Contradiction Depth**: DES (raw: A) — Output A identifies a deeper and more specific contradiction between loss of informal interactions and gains from asynchronous contributions, rather than the more surface-level contrast between focus tasks and collaborative tasks in Output B.
- **Synthesis Quality**: CoT (raw: B) — Output B produces a more precise, scope-bounded synthesis that explicitly resolves the contradiction by specifying task types where each mode excels, while Output A's synthesis remains vague and low-confidence.
- **Epistemic Novelty**: DES (raw: A) — Output A surfaces the non-obvious tension between synchronous-only tools reducing cross-functional idea generation versus asynchronous-first tools enhancing innovation, a nuance that domain experts might not immediately consider.
- **Overall**: CoT — Output B demonstrates stronger directional commitment, a more precise and actionable synthesis, and a clear resolution of the contradiction. Although Output A has deeper contradiction depth and some epistemic novelty, Output B's overall structure and higher-confidence synthesis better address the research question.

### B3: Is social media harmful to democracy?

DES was Output A. Raw winner: B. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: B) — Output B's initial claim and counter-claim are clear, opposing directional assertions, while Output A's claims are hedged with qualifiers like 'in local communities' and 'ephemeral content'.
- **Contradiction Depth**: DES (raw: A) — Output A explicitly explores two competing hypotheses with equal high confidence, generating a deeper structural contradiction, whereas Output B only sets up a single binary opposition.
- **Synthesis Quality**: CoT (raw: B) — Output B produces a more precise, scope-bounded synthesis that specifies conditions (institutional context, regulatory framework, user behavior) resolving the contradiction productively, while Output A's syntheses remain vague and low-confidence.
- **Epistemic Novelty**: DES (raw: A) — Output A surfaces the non-obvious tension that ephemeral content platforms may specifically reduce local civic engagement, a more nuanced insight than the general 'depends on context' synthesis in Output B.
- **Overall**: CoT — Although Output A shows deeper contradiction exploration and a novel sub-claim, Output B's clearer directional commitment and higher-quality, context-specific synthesis make it more epistemically robust and actionable for the research question.

### C1: Is technology good?

DES was Output A. Raw winner: B. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: B) — Output B makes a clear directional claim (improves vs. degrades) with a single high-confidence statement, whereas Output A hedges with moderate confidences and contradictory sub-claims.
- **Contradiction Depth**: CoT (raw: B) — Output B identifies a fundamental logical contradiction between 'improves' and 'degrades' as direct antonyms, while Output A only lists competing sub-hypotheses without recognizing them as a direct contradiction.
- **Synthesis Quality**: CoT (raw: B) — Output B produces a precise, scope-bounded synthesis that resolves the contradiction by specifying conditions (equitable access, ethical governance, ecological foresight), whereas Output A leaves two contradictory conclusions unresolved with equal confidence.
- **Epistemic Novelty**: DES (raw: A) — Output A surfaces a non-obvious tension by specifically linking heavy use of algorithmically curated short-form video platforms to measurable reductions in social interaction and increased loneliness, which is a nuanced finding a domain expert might find insightful.
- **Overall**: CoT — Output B excels in directional commitment, contradiction depth, and synthesis quality by clearly identifying and resolving a fundamental logical contradiction with a condition-based synthesis. Output A offers some epistemic novelty but fails to resolve its own contradictions, making B the stronger overall output.

### C2: Is globalization beneficial?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear directional claim about globalization being beneficial overall (confidence 0.75), while Output B's initial claim is hedged with low confidence (0.45) and its synthesis presents two opposite conclusions with equal confidence.
- **Contradiction Depth**: CoT (raw: A) — Output A identifies a fundamental contradiction between global economic benefits and harm to domestic labor markets in developed nations, whereas Output B merely lists competing hypotheses without acknowledging a deeper structural tension.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a precise, scope-bounded synthesis that resolves the contradiction by specifying conditions (distribution of gains, compensatory policies), while Output B's synthesis offers two contradictory conclusions with no resolution.
- **Epistemic Novelty**: DES (raw: B) — Output B surfaces a non-obvious tension about financial globalization reducing the effectiveness of progressive taxation in developing nations with weak institutions, which is a more nuanced and expert-surprising perspective than Output A's standard trade-off.
- **Overall**: CoT — Output A is superior because it makes a clear directional commitment, identifies a fundamental contradiction, and provides a productive scope-bounded synthesis, which together create a more coherent and useful epistemic assessment. Output B is more fragmented and fails to resolve its own contradictions, despite offering a novel nuance.

### D1: Is intermittent fasting effective for long-term weight loss?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear directional claim that intermittent fasting is effective for long-term weight loss with a confidence of 0.65, then directly contradicts it, while Output B's claims are more hedged and split into competing hypotheses with lower confidence.
- **Contradiction Depth**: CoT (raw: A) — Output A identifies a fundamental contradiction between effectiveness and ineffectiveness due to adherence and metabolic adaptation, whereas Output B only compares weight regain between two methods without a deep opposition.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a precise, scope-bounded synthesis that explains the limited long-term effectiveness relative to other approaches, while Output B offers two vague, low-confidence syntheses that do not resolve the core contradiction.
- **Epistemic Novelty**: CoT (raw: A) — Output A surfaces the non-obvious tension that initial benefits are negated by metabolic adaptation and adherence decline, a perspective that domain experts would recognize as nuanced, whereas Output B's comparisons are more standard.
- **Overall**: CoT — Output A outperforms across all dimensions due to its clear directional commitment, deep contradiction, precise synthesis, and epistemically novel insight, whereas Output B is fragmented, hedged, and lacks resolution.

### D2: Does class size reduction improve educational outcomes?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A clearly states a directional claim (improves) with a specific confidence, while Output B only gives a vague initial claim with low confidence and no clear follow-up directional statement.
- **Contradiction Depth**: CoT (raw: A) — Output A explicitly identifies a fundamental contradiction between the claim and counter-claim, whereas Output B lists many claims and operations without isolating a core contradictory tension.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a precise, scope-bounded synthesis specifying conditions (large classes, disadvantaged students) and cost-effectiveness, while Output B offers no synthesis at all.
- **Epistemic Novelty**: CoT (raw: A) — Output A surfaces the non-obvious tension that class size reduction can be effective in some contexts yet wasteful in others, a nuance experts would recognize as nontrivial.
- **Overall**: CoT — Output A demonstrates clear directional commitment, identifies a core contradiction, produces a conditional synthesis, and offers epistemic novelty, whereas Output B remains vague and incomplete with no synthesis or resolution.

### D3: Is gene editing ethically justifiable in humans?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A makes a clear, specific claim about somatic versus germline editing with a high confidence score, whereas Output B hedges with multiple low-confidence alternatives and technical qualifiers.
- **Contradiction Depth**: CoT (raw: A) — Output A identifies a fundamental ethical contradiction between respecting future generations' autonomy and the potential benefits of heritable editing, while Output B only explores technical risk trade-offs without addressing deeper ethical tensions.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a precise, scope-bounded synthesis that cleanly separates somatic (justifiable) from germline (unjustifiable) editing, resolving the contradiction with a clear boundary, whereas Output B's synthesis remains tentative and technically contingent.
- **Epistemic Novelty**: DES (raw: B) — Output B surfaces the non-obvious tension that in severe monogenic disorders, the off-target risks of somatic editing may be lower than the risks of non-editing alternatives, a perspective that domain experts might not immediately consider.
- **Overall**: CoT — Output A is superior overall because it makes a clear directional commitment, identifies a fundamental ethical contradiction, and produces a precise synthesis, which are all more valuable for addressing the research question than Output B's technical hedging and less relevant risk comparisons.

### E1: Is free trade both beneficial and harmful to developing economies?

DES was Output A. Raw winner: A. Actual winner: DES.

- **Directional Commitment**: CoT (raw: B) — Output B makes a clear directional claim (net benefit) and then explicitly contradicts it with a clear counter-claim, whereas Output A hedges with multiple competing hypotheses and moderate confidence throughout.
- **Contradiction Depth**: DES (raw: A) — Output A identifies two fully supported competing hypotheses and multiple synthesis conclusions that expose fundamental tensions, while Output B only notes one surface-level contradiction without exploring deeper institutional or sectoral specifics.
- **Synthesis Quality**: DES (raw: A) — Output A produces two precise, context-dependent syntheses that specify conditions (e.g., lack of industrial policy, commodity dependence) under which harm or benefit occurs, whereas Output B's synthesis is broader and less bounded.
- **Epistemic Novelty**: DES (raw: A) — Output A surfaces the non-obvious tension that the same conditions (weak institutions, commodity dependence) can support both harm and benefit depending on policy context, while Output B's conclusion is more standard and expected.
- **Overall**: DES — Output A demonstrates deeper epistemic engagement by generating multiple supported hypotheses, explicit conditional syntheses, and a novel tension, whereas Output B, though clearer in direction, remains more simplistic and less nuanced.

### E2: Is economic growth compatible with ecological sustainability?

DES was Output B. Raw winner: A. Actual winner: CoT.

- **Directional Commitment**: CoT (raw: A) — Output A asserts a clear initial claim and a contrasting counter-claim with explicit confidence levels, whereas Output B's initial claim has low confidence and its synthesis conclusions are evenly split, making its direction ambiguous.
- **Contradiction Depth**: CoT (raw: A) — Output A identifies a fundamental contradiction between the necessity of decoupling and the lack of empirical evidence at scale, while Output B merely lists two competing hypotheses without exposing a deeper tension between them.
- **Synthesis Quality**: CoT (raw: A) — Output A produces a precise, conditional synthesis that specifies conditions (absolute, rapid, globally enforced decoupling) and ties them to planetary boundaries, whereas Output B offers two weak, equally confident conclusions that do not resolve the contradiction.
- **Epistemic Novelty**: CoT (raw: A) — Output A surfaces the non-obvious tension that decoupling is theoretically possible but not yet empirically demonstrated at the required scale, challenging both growth optimists and degrowth advocates, while Output B's points about mineral depletion and carrying capacity are more familiar to domain experts.
- **Overall**: CoT — Output A demonstrates clearer directional claims, deeper contradiction handling, a more precise synthesis, and greater epistemic novelty. Output B remains too hedged and non-committal to provide a productive resolution.


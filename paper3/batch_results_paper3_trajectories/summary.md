# Paper 3 — Transition Trajectory Reconstruction

> **Transition trajectory approximation – not exact state reconstruction.**  
> Trajectories are derived from terminal-state history logs. Intermediate
> states are not recovered; only what the transition sequence structurally implies.

## Key Finding

The anomaly is not visible in the terminal state because DES resolves it during the trajectory.

For CONTRADICTED_RESOLVED claims: DES keeps the branch-root claim marked
'disputed' by design (epistemic transparency), while generating synthesis
claims (T9) that carry the trajectory-level resolution. The contradiction
is resolved in the trajectory; the branch-root terminal state reflects the
preserved epistemic tension, not a failure to resolve.

## Coverage

| Metric | Value |
|---|---|
| State files processed | 93 |
| Total claims | 1100 |
| Claims with complex transitions | 186 |
| CONTRADICTED_RESOLVED | 81 |
| COUNTERED_RESOLVED | 2 |
| DECOMPOSED_RESOLVED | 22 |
| SYNTHESIZED | 0 |
| UNRESOLVED | 81 |
| SIMPLE | 0 |

## Trajectory Classes

| Class | Meaning |
|---|---|
| CONTRADICTED_RESOLVED | T5 (counter-hypothesis) + T1 (branch) + T9 (synthesis) in history. Terminal: branch-root remains 'disputed' by DES design; resolution visible in synthesis/branch claims. |
| COUNTERED_RESOLVED | T5 (counter-hypothesis) in history, NO T1 branching, terminal=supported, conf≥0.5. Conflict resolved through evidence without branching. |
| DECOMPOSED_RESOLVED | T4 (decompose) in history, terminal=supported, conf≥0.5. Underspecification resolved via decomposition into sub-claims. |
| SYNTHESIZED | T9 present, clean terminal. Synthesis claim. |
| UNRESOLVED | No synthesis and terminal state is not clean. |
| SIMPLE | Clean terminal, no complex transitions. |

## Top Examples (CONTRADICTED_RESOLVED / COUNTERED_RESOLVED)

| # | Claim (truncated) | Class | Terminal | History |
|---|---|---|---|---|
| 1 | Raising the minimum wage reduces unemployment among low… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5 → T1 → T7 → T9` |
| 2 | social media platforms enhance political participation … | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5 → T1 → T7 → T9` |
| 3 | off-target mutations from heritable human gene editing … | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5 → T1 → T7 → T9` |
| 4 | Trade liberalization produces net welfare outcomes that… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5 → T1 → T7 → T9` |
| 5 | Foreign aid can increase dependency and distort local e… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |
| 6 | Social media platforms' information verification practi… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |
| 7 | Free trade generates negative net welfare effects for d… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |
| 8 | long-term decoupling of GDP growth from carbon emission… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |
| 9 | globalization increases within-country income inequalit… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |
| 10 | Foreign aid is ineffective at reducing poverty in recip… | CONTRADICTED_RESOLVED | disputed 0.47 | `T3 → T5[anti-delphi] → T1 → T7 → T9[anti-delphi]` |

## Detailed Examples with Narratives

### Example 1: CONTRADICTED_RESOLVED

**Claim:** Raising the minimum wage reduces unemployment among low-skilled workers in moderately concentrated labor markets due to increased consumer demand reducing layoffs  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5` → `T1` → `T7` → `T9`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5: counter-hypothesis generated
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9: synthesis generated (trajectory-level resolution)
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 2: CONTRADICTED_RESOLVED

**Claim:** social media platforms enhance political participation and engagement marginalized groups in democratic societies  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5` → `T1` → `T7` → `T9`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5: counter-hypothesis generated
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9: synthesis generated (trajectory-level resolution)
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 3: CONTRADICTED_RESOLVED

**Claim:** off-target mutations from heritable human gene editing include unrecognized cancer-predisposing or developmental risks in future generations  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5` → `T1` → `T7` → `T9`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5: counter-hypothesis generated
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9: synthesis generated (trajectory-level resolution)
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 4: CONTRADICTED_RESOLVED

**Claim:** Trade liberalization produces net welfare outcomes that depend critically on domestic institutional capacity and complementary policies  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5` → `T1` → `T7` → `T9`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5: counter-hypothesis generated
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9: synthesis generated (trajectory-level resolution)
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 5: CONTRADICTED_RESOLVED

**Claim:** Foreign aid can increase dependency and distort local economies long-term poverty reduction  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 6: CONTRADICTED_RESOLVED

**Claim:** Social media platforms' information verification practices improve quality of public discourse  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 7: CONTRADICTED_RESOLVED

**Claim:** Free trade generates negative net welfare effects for developing economies with weak institutions and concentrated commodity-dependent sectors  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 8: CONTRADICTED_RESOLVED

**Claim:** long-term decoupling of GDP growth from carbon emissions at a global scale requires negative emissions technologies or radical demand reduction to achieve compatibility with climate targets  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 9: CONTRADICTED_RESOLVED

**Claim:** globalization increases within-country income inequality in developed nations  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

### Example 10: CONTRADICTED_RESOLVED

**Claim:** Foreign aid is ineffective at reducing poverty in recipient countries with weak governance  
**Terminal state:** disputed, confidence=0.47  
**Note:** Terminal 'disputed' is DES design — branch-root preserved as epistemic marker.  
**History sequence:** `T3` → `T5[anti-delphi]` → `T1` → `T7` → `T9[anti-delphi]`  

**Narrative** (transition trajectory approximation):

```
  1. T3: evidence gathered
  2. T5[anti-delphi]: counter-hypothesis generated [anti-delphi]
  3. T1: contradiction detected -> branch created
  4. T7: qualifier refined
  5. T9[anti-delphi]: synthesis generated (trajectory-level resolution) [anti-delphi]
  [Note: terminal status=disputed by DES design — branch-root preserved
   as epistemic marker; resolution visible in synthesis/branch claims]
```

## Mermaid Diagrams (Top 3 Examples)

*Red = implied epistemic tension / anomaly candidate.  
Yellow = synthesis (trajectory-level resolution).  
Green = clean terminal. Orange = disputed terminal (DES design).*

### Diagram 1: CONTRADICTED_RESOLVED

**Claim:** Raising the minimum wage reduces unemployment among low-skilled workers in moder  

```mermaid
graph LR
    A["Generated: hypothesis"] --> B["T3: evidence gathered"]
    B["T3: evidence gathered"] --> C["T5: counter-hypothesis"]
    C["T5: counter-hypothesis"] --> D["T1: branch created"]
    D["T1: branch created"] --> E["T7: qualifier refined"]
    E["T7: qualifier refined"] --> F["T9: synthesis"]
    F["T9: synthesis"] --> G["Terminal: disputed 0.47"]
    style C fill:#ffcccc
    style D fill:#ffcccc
    style F fill:#ffffcc
    style G fill:#ffeecc
    %% red = implied epistemic tension / anomaly candidate
    %% yellow = synthesis (trajectory resolution)
    %% green = clean terminal state
    %% orange = disputed terminal (DES design: branch-root preserved)
```

### Diagram 2: CONTRADICTED_RESOLVED

**Claim:** social media platforms enhance political participation and engagement marginaliz  

```mermaid
graph LR
    A["Generated: hypothesis"] --> B["T3: evidence gathered"]
    B["T3: evidence gathered"] --> C["T5: counter-hypothesis"]
    C["T5: counter-hypothesis"] --> D["T1: branch created"]
    D["T1: branch created"] --> E["T7: qualifier refined"]
    E["T7: qualifier refined"] --> F["T9: synthesis"]
    F["T9: synthesis"] --> G["Terminal: disputed 0.47"]
    style C fill:#ffcccc
    style D fill:#ffcccc
    style F fill:#ffffcc
    style G fill:#ffeecc
    %% red = implied epistemic tension / anomaly candidate
    %% yellow = synthesis (trajectory resolution)
    %% green = clean terminal state
    %% orange = disputed terminal (DES design: branch-root preserved)
```

### Diagram 3: CONTRADICTED_RESOLVED

**Claim:** off-target mutations from heritable human gene editing include unrecognized canc  

```mermaid
graph LR
    A["Generated: hypothesis"] --> B["T3: evidence gathered"]
    B["T3: evidence gathered"] --> C["T5: counter-hypothesis"]
    C["T5: counter-hypothesis"] --> D["T1: branch created"]
    D["T1: branch created"] --> E["T7: qualifier refined"]
    E["T7: qualifier refined"] --> F["T9: synthesis"]
    F["T9: synthesis"] --> G["Terminal: disputed 0.47"]
    style C fill:#ffcccc
    style D fill:#ffcccc
    style F fill:#ffffcc
    style G fill:#ffeecc
    %% red = implied epistemic tension / anomaly candidate
    %% yellow = synthesis (trajectory resolution)
    %% green = clean terminal state
    %% orange = disputed terminal (DES design: branch-root preserved)
```


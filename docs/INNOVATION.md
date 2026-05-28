# TCM-HerbDrug-FAERS: Innovation Documentation

## Overview

This document details the technical innovations and scientific contributions of the TCM-HerbDrug-FAERS platform for herb-drug interaction (HDI) signal detection.

---

## Innovation 1: Real FAERS Data Validation

### Problem
Most HDI studies rely on synthetic data, in vitro experiments, or case reports. There is a lack of systematic analysis using large-scale real-world adverse event data.

### Solution
- Direct integration with FDA FAERS quarterly ASCII data (2004-present)
- Automated parsing of DEMO, DRUG, REAC, OUTC, INDI, THER tables
- Support for multiple FAERS data format versions

### Technical Details
```python
# Real FAERS data loading pipeline
class RealFAERSLoader:
    def load_quarters(self, quarters: List[str]) -> FAERSDataset:
        # Parses ASCII pipe-delimited files
        # Handles format changes across years
        # Deduplicates reports by ISR/PRIMARYID
```

### Impact
- Enables analysis of millions of real adverse event reports
- Provides statistically powered signal detection
- Supports temporal trend analysis for early warning

---

## Innovation 2: Multi-Metric Signal Detection

### Problem
Single-metric signal detection (e.g., ROR only) may miss signals or produce false positives. Different metrics have different statistical properties.

### Solution
Five-class disproportionality analysis with consensus-based signal calling:

| Metric | Type | Strengths |
|--------|------|-----------|
| ROR | Frequentist | Simple, interpretable odds ratio |
| PRR | Frequentist | Proportional reporting, good for common events |
| IC | Bayesian | Information-theoretic, handles sparse data |
| BCPNN | Bayesian | WHO-UMC standard, posterior smoothing |
| MGPS | Bayesian | FDA standard, Gamma-Poisson shrinkage |

### Signal Classification Logic
```python
# Combined signal strength determination
if ror.is_significant and prr.is_significant:
    if ror.value > 5 and ic.value > 2:
        strength = "strong"
    else:
        strength = "moderate"
elif ror.is_significant or prr.is_significant:
    strength = "weak"

# MGPS upgrade logic
if mgps_class == "disproportionate_strong" and strength in ("moderate", "weak"):
    strength = "strong"
```

### Impact
- Reduces false positive rate through multi-metric consensus
- Captures different types of associations
- Aligns with FDA/WHO regulatory standards

---

## Innovation 3: EBGM Approximate Shrinkage Scoring

### Problem
Raw disproportionality metrics can be unstable for rare events with small counts. Bayesian shrinkage provides more reliable estimates.

### Solution
Implementation of MGPS-inspired empirical Bayes scoring:

```python
# Gamma-Poisson model
alpha_prior = 0.2  # Weakly informative prior
n_exp = ((a + b) * (a + c)) / n  # Expected count under independence
rr = (a + alpha_prior) / (n_exp + alpha_prior)  # Shrinkage estimate

# Log-normal posterior CI
log_ebgm = math.log(max(ebgm, 1e-10))
se_log = math.sqrt(1.0 / alpha_post)
eb05 = math.exp(log_ebgm - 1.645 * se_log)  # 5th percentile
```

### MGPS Thresholds (FDA/WHO Standard)
| Category | EBGM | EB05 |
|----------|------|------|
| Disproportionate Strong | >= 5 | >= 2 |
| Disproportionate | >= 2 | >= 1 |
| Weak Disproportionate | >= 1.5 | >= 0.5 |

### Impact
- Stabilizes estimates for rare herb-event pairs
- Aligns with FDA Adverse Event Reporting System standards
- Provides interpretable signal strength categories

---

## Innovation 4: 16 Herb Standardized Mapping

### Problem
TCM herbs have multiple naming conventions (English, Latin, Pinyin, regional variants). FAERS drug names are inconsistent.

### Solution
Comprehensive herb profile system with regex-based FAERS matching:

```python
HERB_PROFILES = {
    "ginkgo": HerbProfile(
        common_name="Ginkgo biloba",
        latin_name="Ginkgo biloba L.",
        pinyin="银杏",
        faers_patterns=[
            r"GINKGO",
            r"GINKGO BILOBA",
            r"EGb 761",
            r"GINKGOFLAVONE",
        ],
        known_interactions=["warfarin", "aspirin", "clopidogrel", ...],
    ),
    # ... 15 more herbs
}
```

### Supported Herbs
16 herbs with clinical significance in Western and Chinese medicine:
- Cardiovascular: Ginkgo, Danshen, Garlic, Hawthorn
- Psychiatric: St. John's wort, Kava, Valerian
- Metabolic: Ginseng, Licorice, Turmeric
- Immune: Echinacea
- Hormonal: Dong Quai, Black Cohosh, Saw Palmetto
- Stimulant: Ma Huang, Green Tea

### Impact
- Comprehensive coverage of clinically relevant herbs
- Handles naming inconsistencies in real-world data
- Extensible to additional herbs

---

## Innovation 5: Positive Control Validation

### Problem
Signal detection methods need validation against known ground truth.

### Solution
28 literature-confirmed HDI pairs as positive controls:

```yaml
pairs:
  - herb: "Ginkgo biloba"
    drug: "warfarin"
    mechanism: "Antiplatelet additive effect; CYP2C9 competition"
    severity: "major"
    evidence_level: "established"
    references:
      - "Bent S et al. JAMA. 2005;293(1):42-47"
```

### Validation Metrics
- Sensitivity: Proportion of known HDI pairs detected as signals
- Specificity: Proportion of negative controls correctly excluded
- Signal strength agreement with clinical severity

### Impact
- Demonstrates real-world detection capability
- Provides benchmark for method comparison
- Supports regulatory submission evidence

---

## Innovation 6: Three-Level Risk Ranking

### Problem
Binary signal/no-signal classification is insufficient for clinical decision-making.

### Solution
Hierarchical risk assessment incorporating multiple evidence types:

| Level | Label | Criteria |
|-------|-------|----------|
| 1 | signal_only | FAERS signal detected |
| 2 | signal_plus_database | Signal + HDI database support |
| 3 | signal_plus_mechanism | Signal + database + mechanism pathway |

### Risk Score Calculation
```python
score = 0
if has_signal:
    score += 20
    if signal_strength == "strong": score += 15
if has_db_support: score += 25
if has_mechanism:
    score += int(mechanism_confidence * 25)
score += int(cyp_potency * 15)
```

### Bootstrap Confidence Intervals
```python
# Bootstrap CI for risk score stability
for _ in range(n_bootstrap):
    sample = rng.choice(metric_samples)
    rs = assess_risk(drug, herb, **sample)
    scores.append(rs.score)

ci_lower = scores[lower_idx]
ci_upper = scores[upper_idx]
```

### Impact
- Graduated risk assessment for clinical decision support
- Incorporates mechanistic evidence
- Quantified uncertainty via bootstrap CI

---

## Innovation 7: Mechanism Knowledge Graph

### Problem
Signal detection alone cannot explain WHY an interaction occurs.

### Solution
Directed graph: Herb -> Ingredient -> Target -> CYP/Transporter -> Adverse Event

```python
class MechanismGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        # Herb nodes
        # Ingredient nodes (active compounds)
        # Target nodes (receptors, enzymes)
        # CYP/Transporter nodes
        # Adverse event nodes
```

### Graph Capabilities
- Path search: Find mechanism pathways between herb and AE
- CYP profiling: Identify enzyme inhibition/induction
- Evidence chain: Generate explainable interaction narratives

### Impact
- Provides mechanistic explanation for detected signals
- Supports regulatory decision-making
- Enables hypothesis generation for further research

---

## Comparison with Existing Work

| Feature | This Work | Existing Databases |
|---------|-----------|-------------------|
| Data Source | Real FAERS (millions of reports) | Literature review |
| Signal Metrics | 5 metrics (ROR/PRR/IC/BCPNN/MGPS) | Usually 1-2 |
| Validation | 28 positive controls | Manual curation |
| Risk Levels | 3 levels with bootstrap CI | Binary |
| Mechanism | Knowledge graph pathway | Text description |
| Herbs Covered | 16 clinically relevant | Varies |
| API Access | RESTful API | Web interface only |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TCM-HerbDrug-FAERS                       │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST API                                           │
│  ├── /api/signal/*   (Signal Detection)                     │
│  ├── /api/risk/*     (Risk Assessment)                      │
│  └── /api/mechanism/* (Mechanism Explanation)                │
├─────────────────────────────────────────────────────────────┤
│  Analysis Layer                                             │
│  ├── FAERSAnalysisPipeline (Orchestrator)                   │
│  ├── DisproportionalityAnalyzer (ROR/PRR/IC/BCPNN)         │
│  ├── SignalDetector (MGPS + Combined)                       │
│  ├── RiskScorer (Three-level + Bootstrap)                   │
│  └── MechanismGraph (Knowledge Graph)                       │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── RealFAERSLoader (FAERS ASCII Parser)                   │
│  ├── HerbNameNormalizer (16 Herb Profiles)                  │
│  ├── HerbKnowledgeGraph (Herb-Drug KG)                      │
│  └── CYPMapper (Enzyme Mapping)                             │
├─────────────────────────────────────────────────────────────┤
│  Data Sources                                               │
│  ├── FDA FAERS (2004-present)                               │
│  ├── MedDRA Terminology                                     │
│  └── Literature HDI Pairs                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Future Directions

1. **VigiBase Integration** -- Extend to WHO global adverse event database
2. **Temporal Analysis** -- Early warning via reporting trend detection
3. **NLP Enhancement** -- Extract HDI signals from literature automatically
4. **Clinical Decision Support** -- Integration with EHR systems
5. **Regulatory Submission** -- Package for FDA/EMA pharmacovigilance reports

---

## References

1. FDA Adverse Event Reporting System (FAERS). U.S. Food and Drug Administration.
2. MedDRA: the Medical Dictionary for Regulatory Activities.
3. Evans SJ, et al. Proportional reporting ratio. Pharmacoepidemiol Drug Saf. 2001.
4. Bate A, et al. BCPNN. Eur J Clin Pharmacol. 1998.
5. Szarfman A, et al. MGPS. Pharmacoepidemiol Drug Saf. 2002.

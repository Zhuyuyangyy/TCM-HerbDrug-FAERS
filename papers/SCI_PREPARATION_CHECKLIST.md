# SCI Paper Preparation Checklist

## Project: TCM-HerbDrug-FAERS

**Working Title**: Signal Detection and Mechanism Elucidation of Herb-Drug Interactions via FDA FAERS and Knowledge Graph

**Target Journals** (in order of preference):
1. Drug Safety (IF ~3.5) - Pharmacovigilance focus
2. Pharmacoepidemiology and Drug Safety (IF ~2.8) - Methods focus
3. Frontiers in Pharmacology (IF ~5.6) - Open access, broad reach
4. BMC Pharmacology and Toxicology (IF ~2.5) - Open access
5. Journal of Ethnopharmacology (IF ~5.4) - TCM focus

---

## Phase 1: Data Preparation (Week 1-2)

### 1.1 FAERS Data Acquisition
- [ ] Download FAERS quarterly data (2020-2024 minimum)
- [ ] Verify data integrity (file sizes, record counts)
- [ ] Document data version and download date
- [ ] Calculate total reports, drugs, events

### 1.2 Data Processing
- [ ] Run `scripts/run_faers_analysis.py` on full dataset
- [ ] Generate signal detection results for all 16 herbs
- [ ] Export results to CSV/Excel for manuscript tables
- [ ] Document processing parameters (min_cases=3, thresholds)

### 1.3 Validation Data
- [ ] Verify 28 positive control pairs are correctly configured
- [ ] Run validation analysis
- [ ] Calculate sensitivity/specificity metrics
- [ ] Generate validation results table

---

## Phase 2: Results Generation (Week 2-3)

### 2.1 Primary Results
- [ ] Table 1: Dataset summary (reports, drugs, events, herbs)
- [ ] Table 2: Signal detection results per herb (ROR, PRR, IC, BCPNN, EBGM)
- [ ] Table 3: Top 20 herb-adverse event pairs by signal strength
- [ ] Table 4: Positive control validation results

### 2.2 Supplementary Results
- [ ] Table S1: Complete signal detection results (all herb-event pairs)
- [ ] Table S2: MGPS classification distribution
- [ ] Table S3: Bootstrap confidence intervals for risk scores
- [ ] Table S4: Mechanism pathway examples

### 2.3 Figures
- [ ] Figure 1: Study flowchart (data processing pipeline)
- [ ] Figure 2: Signal strength distribution across herbs
- [ ] Figure 3: Venn diagram of multi-metric signal agreement
- [ ] Figure 4: Risk level distribution (three-level classification)
- [ ] Figure 5: Mechanism knowledge graph visualization
- [ ] Figure 6: Temporal trends for selected herb-AE pairs

---

## Phase 3: Manuscript Writing (Week 3-5)

### 3.1 Abstract (250 words)
- [ ] Background: HDI challenge, FAERS opportunity
- [ ] Methods: Multi-metric signal detection, knowledge graph, risk ranking
- [ ] Results: Key findings (sensitivity, top signals, risk distribution)
- [ ] Conclusion: Clinical implications, tool availability

### 3.2 Introduction (800-1000 words)
- [ ] Paragraph 1: HDI prevalence and clinical significance
- [ ] Paragraph 2: Limitations of current HDI databases
- [ ] Paragraph 3: FAERS/VigiBase as signal sources
- [ ] Paragraph 4: Study objectives and contributions

### 3.3 Methods (1200-1500 words)
- [ ] 2.1 Data Source: FAERS description, time period, preprocessing
- [ ] 2.2 Herb Selection: 16 herbs rationale, name normalization
- [ ] 2.3 Signal Detection: ROR, PRR, IC, BCPNN, MGPS formulas
- [ ] 2.4 Signal Classification: Multi-metric consensus logic
- [ ] 2.5 Risk Assessment: Three-level system, bootstrap CI
- [ ] 2.6 Mechanism Graph: Construction, path search
- [ ] 2.7 Validation: Positive controls, evaluation metrics

### 3.4 Results (1500-2000 words)
- [ ] 3.1 Dataset Characteristics: Report counts, herb coverage
- [ ] 3.2 Signal Detection: Number of signals per herb, strength distribution
- [ ] 3.3 Validation: Sensitivity, specificity, comparison with literature
- [ ] 3.4 Risk Assessment: Level distribution, bootstrap CI results
- [ ] 3.5 Mechanism Analysis: Pathway examples, CYP profiling

### 3.5 Discussion (1500-2000 words)
- [ ] Paragraph 1: Summary of key findings
- [ ] Paragraph 2: Comparison with existing HDI databases
- [ ] Paragraph 3: Clinical implications
- [ ] Paragraph 4: Methodological strengths (multi-metric, real data)
- [ ] Paragraph 5: Limitations (reporting bias, causality)
- [ ] Paragraph 6: Future directions

### 3.6 Conclusion (200-300 words)
- [ ] Main contributions
- [ ] Clinical utility
- [ ] Tool availability statement

---

## Phase 4: Quality Assurance (Week 5-6)

### 4.1 Statistical Review
- [ ] Verify all formulas are correctly implemented
- [ ] Check confidence interval calculations
- [ ] Validate p-value interpretations
- [ ] Review bootstrap methodology

### 4.2 Data Integrity
- [ ] Cross-check manuscript numbers with analysis output
- [ ] Verify table/figure consistency
- [ ] Confirm reproducibility (run analysis again)

### 4.3 Code Documentation
- [ ] Ensure all scripts are documented
- [ ] Add docstrings to key functions
- [ ] Create requirements.txt with pinned versions
- [ ] Tag repository version for submission

### 4.4 Ethical Considerations
- [ ] Confirm FAERS data is publicly available
- [ ] No patient identifiers in analysis
- [ ] Cite data sources appropriately

---

## Phase 5: Submission Preparation (Week 6-7)

### 5.1 Journal-Specific Formatting
- [ ] Check target journal guidelines
- [ ] Format references according to journal style
- [ ] Adjust word count limits
- [ ] Prepare cover letter

### 5.2 Supplementary Materials
- [ ] Code repository link (GitHub)
- [ ] Data availability statement
- [ ] Reproducibility instructions (REPRODUCE.md)
- [ ] Additional tables/figures

### 5.3 Author Contributions
- [ ] Define author roles (CRediT format)
- [ ] Obtain co-author approvals
- [ ] Conflict of interest statement
- [ ] Funding acknowledgment

### 5.4 Pre-Submission Checks
- [ ] Spell check
- [ ] Grammar check (consider professional editing)
- [ ] Reference verification
- [ ] Figure resolution check (300 DPI minimum)

---

## Phase 6: Post-Submission (Week 7+)

### 6.1 Revision Preparation
- [ ] Document reviewer comments
- [ ] Prepare point-by-point response
- [ ] Update analysis if new data available
- [ ] Revise manuscript accordingly

### 6.2 Publication
- [ ] Final proofreading
- [ ] Verify online publication
- [ ] Update repository with publication link
- [ ] Share on academic social media

---

## Key Manuscript Tables

### Table 1: Dataset Summary

| Metric | Value |
|--------|-------|
| Total FAERS reports | TBD |
| Unique drugs | TBD |
| Unique adverse events | TBD |
| Herbs analyzed | 16 |
| Herbs with signals | TBD |
| Positive controls | 28 |
| Negative controls | 5 |

### Table 2: Signal Detection Results (Example)

| Herb | Events Analyzed | Signals | Strong | Moderate | Sensitivity |
|------|-----------------|---------|--------|----------|-------------|
| Ginkgo biloba | TBD | TBD | TBD | TBD | TBD |
| St. John's wort | TBD | TBD | TBD | TBD | TBD |
| ... | ... | ... | ... | ... | ... |

### Table 3: Top Herb-AE Pairs

| Herb | Adverse Event | N | ROR | 95% CI | PRR | IC | EBGM | Strength |
|------|---------------|---|-----|--------|-----|-----|------|----------|
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Table 4: Validation Results

| Herb | Drug | Expected | Detected | N co-reports | ROR | 95% CI |
|------|------|----------|----------|--------------|-----|--------|
| Ginkgo | Warfarin | Yes | TBD | TBD | TBD | TBD |
| ... | ... | ... | ... | ... | ... | ... |

---

## Key Manuscript Figures

### Figure 1: Study Flowchart
```
FAERS Raw Data (2004-2024)
    ↓
Data Preprocessing (dedup, format)
    ↓
Herb Name Normalization (16 herbs)
    ↓
2×2 Contingency Table Construction
    ↓
Multi-Metric Signal Detection (ROR/PRR/IC/BCPNN/MGPS)
    ↓
Signal Classification (strong/moderate/weak)
    ↓
Three-Level Risk Assessment
    ↓
Mechanism Explanation (Knowledge Graph)
```

### Figure 2: Signal Distribution
- Bar chart: Number of signals per herb
- Color-coded by signal strength

### Figure 3: Multi-Metric Agreement
- Venn diagram: Overlap of signals detected by different metrics

### Figure 4: Risk Level Distribution
- Stacked bar chart: Proportion of risk levels per herb

---

## Writing Tips

### Do's
- Use active voice where possible
- Be specific about numbers and percentages
- Compare findings with existing literature
- Discuss clinical implications
- Acknowledge limitations honestly

### Don'ts
- Overstate causal claims (FAERS is for signal detection, not causality)
- Ignore reporting biases (Stimulated reporting, Weber effect)
- Omit negative results
- Use vague language ("many", "several")
- Forget to cite data sources

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Data Preparation | Processed data, validation results |
| 2-3 | Results Generation | Tables, figures, supplementary materials |
| 3-5 | Manuscript Writing | Complete draft |
| 5-6 | Quality Assurance | Reviewed draft, code documentation |
| 6-7 | Submission Preparation | Formatted manuscript, cover letter |
| 7+ | Post-Submission | Revision, publication |

---

## Contact for Questions

- Technical issues: Check GitHub Issues
- Methodology questions: Review docs/INNOVATION.md
- Reproducibility: See REPRODUCE.md

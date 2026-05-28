# TCM-HerbDrug-FAERS

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![FAERS Data](https://img.shields.io/badge/data-FDA%20FAERS-orange.svg)
![Signal Detection](https://img.shields.io/badge/method-ROR%20%7C%20PRR%20%7C%20IC%20%7C%20BCPNN%20%7C%20MGPS-red.svg)

**A pharmacovigilance platform for detecting herb-drug interaction (HDI) signals using FDA Adverse Event Reporting System (FAERS) data, with mechanism explanation via knowledge graph and three-level risk assessment.**

---

## Overview

Herb-drug interactions (HDIs) pose a significant safety concern as herbal medicine use increases globally. This platform provides a systematic, evidence-based approach to detecting HDI signals from real-world adverse event data, combining statistical disproportionality analysis with mechanistic knowledge graphs for risk assessment.

The system processes FDA FAERS quarterly data (2004-present), applies five-class disproportionality analysis methods, and cross-references findings against a curated herb-CYP-transporter knowledge graph covering 15 herbs with full pharmacokinetic profiles.

---

## Key Features

- **Real FAERS Data Validation** -- Processes FDA public quarterly data (2004-present), not synthetic data
- **Five-Metric Signal Detection** -- ROR / PRR / IC / BCPNN / MGPS disproportionality analysis with confidence intervals
- **EBGM Shrinkage Scoring** -- Bayesian Gamma-Poisson model (MGPS) for robust signal strength grading
- **15-Herb Knowledge Graph** -- Curated herb-ingredient-CYP/transporter-AE directed graph with confidence scores
- **Herb Name Normalization** -- English/Latin/Pinyin multi-name matching for FAERS drug name resolution
- **Positive Control Validation** -- 28 literature-known interaction pairs as gold standard
- **Three-Level Risk Ranking** -- signal_only / signal_plus_database / signal_plus_mechanism
- **Mechanism Explanation** -- Graph-based pathway search with human-readable explanations
- **RESTful API** -- FastAPI service with automatic OpenAPI documentation

---

## Architecture

```
        +-------------------+     +-------------------+
        | FDA FAERS Data    |     | Herb Knowledge    |
        | (Quarterly ASCII) |     | Graph (15 herbs)  |
        +---------+---------+     +---------+---------+
                  |                         |
        +---------v---------+     +---------v---------+
        | FAERS Data Loader |     | CYP/Transporter   |
        | + Name Normalizer |     | Profiles          |
        +---------+---------+     +---------+---------+
                  |                         |
        +---------v---------+     +---------v---------+
        | Disproportionality |     | Mechanism Graph   |
        | Analysis Engine    |     | (NetworkX DiGraph)|
        | ROR/PRR/IC/BCPNN  |     +---------+---------+
        +---------+---------+               |
                  |               +---------v---------+
        +---------v---------+     | Path Search +     |
        | Signal Detector   |     | Explanation Gen   |
        | (MGPS EBGM)       |     +-------------------+
        +---------+---------+
                  |
        +---------v---------+
        | Three-Level Risk  |
        | Assessment        |
        +-------------------+
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| API Framework | FastAPI + Uvicorn |
| Statistical Computing | SciPy, NumPy |
| Data Processing | Pandas |
| Graph Analysis | NetworkX |
| Configuration | PyYAML, Pydantic |
| HTTP Client | httpx |
| Testing | pytest, pytest-cov |
| Linting | Ruff |
| CI/CD | GitHub Actions |

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/TCM-HerbDrug-FAERS.git
cd TCM-HerbDrug-FAERS

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install fastapi uvicorn networkx scipy numpy pandas pyyaml pydantic pydantic-settings httpx pytest
```

### 2. Download FAERS Data

Download quarterly ASCII data files from the FDA official website:
- URL: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- Download `faers_ascii_YYYYQN.zip` format files
- Extract to `data/faers_ascii/` directory

```
data/faers_ascii/
├── 2022Q1/
│   ├── DEMO22Q1.txt
│   ├── DRUG22Q1.txt
│   ├── REAC22Q1.txt
│   ├── OUTC22Q1.txt
│   ├── INDI22Q1.txt
│   └── THER22Q1.txt
├── 2022Q2/
│   └── ...
└── ...
```

### 3. Run Analysis

```bash
# Analyze all herbs
python scripts/run_faers_analysis.py

# Analyze specific herbs
python scripts/run_faers_analysis.py --herbs ginkgo danshen licorice

# Specify quarter range
python scripts/run_faers_analysis.py --quarters 2022Q1 2022Q2 2022Q3 2022Q4

# Specify data directory
python scripts/run_faers_analysis.py --data-dir /path/to/faers_ascii
```

### 4. Start API Server

```bash
# Development server
uvicorn backend.main:app --host 0.0.0.0 --port 8013 --reload
```

Swagger UI is available at: **http://localhost:8013/docs**

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_smoke.py -v

# Run with coverage
pytest tests/ -v --cov=backend
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/summary` | GET | Platform capabilities overview |
| `/api/signal/detect` | POST | Detect drug adverse event signal |
| `/api/signal/batch` | POST | Batch signal detection |
| `/api/risk/assess` | POST | Three-level risk assessment |
| `/api/risk/chain` | GET | Evidence chain query |
| `/api/mechanism/explain` | POST | Mechanism explanation |
| `/api/mechanism/search` | GET | Search mechanism pathways |
| `/api/mechanism/herbs` | GET | List herbs in knowledge graph |
| `/api/mechanism/cyps` | GET | List CYP enzymes |

### API Usage Example

```python
import httpx

# Detect signal
response = httpx.post("http://localhost:8013/api/signal/detect", json={
    "drug": "warfarin",
    "event": "bleeding",
    "a": 50, "b": 50, "c": 5, "d": 900
})
print(response.json())

# Assess risk
response = httpx.post("http://localhost:8013/api/risk/assess", json={
    "drug": "warfarin",
    "herb": "ginkgo",
    "signal_strength": "strong",
    "has_db_support": True,
    "has_mechanism": True,
    "mechanism_confidence": 0.9,
    "cyp_potency": 0.8
})
print(response.json())
```

---

## Supported Herbs (15)

| Herb | Latin Name | Chinese | Key CYP Interactions |
|------|------------|---------|---------------------|
| Ginkgo biloba | Ginkgo biloba L. | 银杏 | CYP2C9, CYP3A4 |
| Panax ginseng | Panax ginseng C.A. Mey. | 人参 | CYP2D6, CYP3A4 |
| St. John's wort | Hypericum perforatum | 圣约翰草 | CYP3A4 (induction), P-gp |
| Danshen | Salvia miltiorrhiza | 丹参 | CYP2C9, CYP3A4 |
| Licorice | Glycyrrhiza glabra | 甘草 | CYP3A4, CYP2B6 |
| Ma Huang | Ephedra sinica | 麻黄 | CYP1A2, CYP2D6 |
| Dong Quai | Angelica sinensis | 当归 | CYP2C19, CYP3A4 |
| Garlic | Allium sativum | 大蒜 | CYP2C9, CYP3A4 |
| Turmeric | Curcuma longa | 姜黄 | CYP3A4, CYP2C9, P-gp |
| Red Yeast Rice | Monascus purpureus | 红曲 | CYP3A4 |
| Scutellaria | Scutellariae Radix | 黄芩 | CYP2C9, CYP1A2, CYP3A4 |
| Rhubarb | Rhei Radix | 大黄 | CYP3A4, CYP2C9 |
| Pinellia | Pinellia ternata | 半夏 | CYP2D6, CYP3A4 |
| Aconite | Aconitum carmichaelii | 附子 | CYP3A4 |
| Hawthorn | Crataegus pinnatifida | 山楂 | CYP3A4, CYP2D6 |

---

## Project Structure

```
TCM-HerbDrug-FAERS/
├── backend/
│   ├── api/
│   │   ├── signal.py              # Signal detection API
│   │   ├── risk.py                # Risk assessment API
│   │   ├── mechanism.py           # Mechanism explanation API
│   │   └── __init__.py
│   ├── data/
│   │   ├── faers_real_loader.py   # Real FAERS data loader
│   │   ├── herb_name_normalizer.py # Herb name normalization
│   │   ├── faers_loader.py        # Generic data loader
│   │   ├── herb_kg.py             # Herb knowledge graph (15 herbs, CYP profiles)
│   │   ├── cyp_mapper.py          # CYP enzyme mapping
│   │   └── __init__.py
│   ├── analysis/
│   │   ├── faers_pipeline.py      # Complete analysis pipeline
│   │   ├── risk_scoring.py        # Three-level risk scoring
│   │   ├── evidence_chain.py      # Evidence chain construction
│   │   ├── validation.py          # Validation utilities
│   │   └── __init__.py
│   ├── models/
│   │   ├── disproportionality.py  # ROR/PRR/IC/BCPNN with CI
│   │   ├── signal_detector.py     # Signal detection engine
│   │   ├── mechanism_graph.py     # Herb-Ingredient-Target-CYP-AE graph
│   │   ├── temporal_signal.py     # Temporal trend analysis
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_api.py            # API endpoint tests
│   │   ├── test_disproportionality.py # Metric tests
│   │   └── test_signal.py         # Signal detection tests
│   ├── config.py                  # Configuration settings
│   ├── main.py                    # FastAPI application
│   └── __init__.py
├── data/
│   ├── known_hdi_pairs.yaml       # Known HDI validation pairs (28 positive, 5 negative)
│   └── herb_drug_pairs.yaml       # Herb-drug interaction pairs
├── docs/
│   ├── INNOVATION.md              # Innovation documentation
│   ├── SCI_Paper_Skeleton.md      # Paper skeleton
│   ├── Claim_Evidence_Table.md    # Claim-evidence mapping
│   ├── research_plan.md           # Research plan
│   └── 技术交底书.md              # Technical disclosure
├── papers/
│   └── SCI_PREPARATION_CHECKLIST.md # SCI paper preparation
├── scripts/
│   ├── run_faers_analysis.py      # Main FAERS analysis script
│   ├── run_signal_detection.py    # Signal detection script
│   ├── run_synthetic_validation.py # Validation script
│   ├── generate_synthetic_faers.py # Synthetic data generator
│   └── quick_smoke_test.py        # Quick smoke test
├── tests/
│   └── test_smoke.py              # Comprehensive smoke tests
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI
├── CONTRIBUTING.md                # Contribution guidelines
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Dependencies
├── REPRODUCE.md                   # Reproduction guide
└── README.md                      # This file
```

---

## Signal Detection Methods

### Disproportionality Analysis

| Method | Formula | Signal Criterion |
|--------|---------|------------------|
| ROR (Reporting Odds Ratio) | ad/bc | CI lower bound > 1 |
| PRR (Proportional Reporting Ratio) | [a/(a+b)] / [c/(c+d)] | CI lower bound > 1 |
| IC (Information Component) | log2(O/E) | CI lower bound > 0 |
| BCPNN (Bayesian) | Bayesian IC posterior | CI lower bound > 0 |

All methods include Haldane-Anscombe correction for zero cells and minimum case thresholds.

### MGPS (Multi-Item Gamma Poisson Shrinker)

Bayesian shrinkage estimation based on the Gamma-Poisson model:

| Signal Level | Criteria |
|-------------|----------|
| `disproportionate_strong` | EBGM >= 5, EB05 >= 2 |
| `disproportionate` | EBGM >= 2, EB05 >= 1 |
| `weak_disproportionate` | EBGM >= 1.5, EB05 >= 0.5 |

---

## Benchmarks

Run the built-in validation to reproduce benchmarks:

```bash
# Smoke test with synthetic data
python scripts/quick_smoke_test.py

# Full synthetic validation
python scripts/run_synthetic_validation.py
```

| Validation | Details |
|-----------|---------|
| Positive controls | 28 literature-known HDI pairs (e.g., Ginkgo + Warfarin, St. John's wort + Cyclosporine) |
| Negative controls | 5 pairs with no known interaction for specificity assessment |
| Mechanism graph | 20+ documented HDI mechanism edges across 15 herbs |

---

## Research

This platform supports pharmacovigilance research and TCM safety evaluation. Related documentation:

- **SCI Paper Skeleton** (`docs/SCI_Paper_Skeleton.md`) -- Draft structure for peer-reviewed publication
- **Claim-Evidence Table** (`docs/Claim_Evidence_Table.md`) -- Mapping of research claims to evidence
- **Innovation Documentation** (`docs/INNOVATION.md`) -- Detailed innovation analysis
- **SCI Preparation Checklist** (`papers/SCI_PREPARATION_CHECKLIST.md`) -- Paper preparation workflow

### Citation

```bibtex
@software{tcm_herbdrug_faers,
  title={TCM-HerbDrug-FAERS: Herb-Drug Interaction Signal Mining via FDA FAERS},
  author={ZYY Project},
  year={2025},
  url={https://github.com/YOUR_USERNAME/TCM-HerbDrug-FAERS}
}
```

### Data Sources to Cite

- FDA Adverse Event Reporting System (FAERS). U.S. Food and Drug Administration.
- MedDRA: the Medical Dictionary for Regulatory Activities.

---

## Roadmap

- [ ] Integration with WHO VigiBase for global adverse event data
- [ ] Expansion to 30+ herbs with complete pharmacokinetic profiles
- [ ] Temporal signal trend analysis across FAERS quarters
- [ ] Machine learning-based signal prioritization
- [ ] Web UI for interactive mechanism exploration
- [ ] Docker containerization for reproducible deployment

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- FDA for providing public FAERS data
- WHO-UMC for VigiBase pharmacovigilance methodology
- MedDRA for adverse event terminology standardization

---

## Contact

For questions, collaborations, or issues, please open a GitHub Issue or contact the project maintainers.

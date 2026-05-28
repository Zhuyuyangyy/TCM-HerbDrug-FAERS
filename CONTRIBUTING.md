# Contributing to TCM-HerbDrug-FAERS

Thank you for your interest in contributing to the TCM Herb-Drug Interaction Signal Mining system.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/TCM-HerbDrug-FAERS.git
cd TCM-HerbDrug-FAERS

# Install in development mode
pip install -e ".[dev]"
```

## Running the Application

```bash
# Start the API server
cd backend && python main.py

# Or with uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8013 --reload
```

The API server starts at `http://localhost:8013`. API docs at `http://localhost:8013/docs`.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run backend tests
pytest backend/tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend

# Run specific test suite
pytest tests/test_smoke.py -v
```

## Code Quality

We use `ruff` for linting:

```bash
ruff check .
ruff check --fix .
```

## Project Structure

- `backend/api/` - FastAPI endpoint definitions (signal, risk, mechanism)
- `backend/analysis/` - FAERS pipeline, risk scoring, evidence chain
- `backend/data/` - Data loaders, herb name normalization, knowledge graph
- `backend/models/` - Disproportionality analysis, signal detection, mechanism graph
- `backend/tests/` - Backend-specific tests
- `data/` - Known HDI pairs, herb-drug interaction data
- `scripts/` - Analysis and validation scripts
- `tests/` - Top-level smoke tests

## Key Concepts

1. **Disproportionality Analysis** - ROR, PRR, IC, BCPNN metrics for signal detection
2. **MGPS** - Bayesian Gamma-Poisson shrinkage for signal strength grading
3. **Three-Level Risk** - signal_only / signal_plus_database / signal_plus_mechanism
4. **Herb Name Normalization** - Multi-language matching for FAERS drug names
5. **Mechanism Knowledge Graph** - Herb-Ingredient-Target-CYP/Transporter-AE directed graph

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pytest tests/ -v`)
5. Run linting (`ruff check .`)
6. Commit with a clear message
7. Push and open a Pull Request

## Commit Message Convention

Use the format: `type(scope): description`

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring

## Data Sources

- **FDA FAERS** - U.S. FDA Adverse Event Reporting System
- **MedDRA** - Medical Dictionary for Regulatory Activities

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS

# REPRODUCE.md - TCM-HerbDrug-FAERS

## Prerequisites

- **Python**: 3.10+
- **OS**: Linux / macOS / Windows
- **GPU**: Not required (CPU sufficient for API server)

## Install

```bash
cd TCM-HerbDrug-FAERS
pip install -e .
```

Or install dependencies directly:
```bash
pip install fastapi uvicorn numpy pandas pyyaml pydantic pydantic-settings httpx networkx
```

## Smoke Test

```bash
python -c "from backend.main import app; print('Import OK')"
```

```bash
pytest backend/tests/ -v
```

## Run Server

```bash
uvicorn backend.main:app --port 8029 --reload
```

## API Documentation

Access Swagger UI at: http://localhost:8029/docs

## Project Description

基于FAERS/VigiBase的中西药相互作用风险信号挖掘

## Known Issues

- No external real clinical data included; uses synthetic/demo data
- No hardcoded absolute paths detected in core code

# ─── Build stage ────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="ZYY Project"
LABEL description="TCM-HerbDrug-FAERS - Herb-drug interaction signal mining via FDA FAERS"

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
COPY backend/ ./backend/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8013/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8013"]

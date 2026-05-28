"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_summary():
    r = client.get("/api/summary")
    assert r.status_code == 200
    data = r.json()
    assert "platform" in data
    assert "herbs" in data


def test_detect_signal():
    r = client.post("/api/signal/detect",
                    json={"drug": "warfarin", "event": "bleeding",
                          "a": 50, "b": 50, "c": 5, "d": 900})
    assert r.status_code == 200
    data = r.json()
    assert "is_signal" in data
    assert "metrics" in data


def test_risk_assess():
    r = client.post("/api/risk/assess",
                    json={"drug": "warfarin", "herb": "ginkgo",
                          "signal_strength": "strong",
                          "has_db_support": True, "has_mechanism": True,
                          "mechanism_confidence": 0.9, "cyp_potency": 0.9})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] >= 1
    assert data["score"] > 0


def test_evidence_chain():
    r = client.get("/api/risk/chain?drug=warfarin&herb=ginkgo")
    assert r.status_code == 200
    data = r.json()
    assert "chain_type" in data

"""Tests for disproportionality analysis."""
import pytest

from backend.models.disproportionality import DisproportionalityAnalyzer


def test_ror_basic():
    a = DisproportionalityAnalyzer()
    r = a.compute_ror(10, 90, 5, 895)
    assert r.value > 1
    assert r.metric == "ROR"


def test_prr_basic():
    a = DisproportionalityAnalyzer()
    r = a.compute_prr(10, 90, 5, 895)
    assert r.value > 1
    assert r.metric == "PRR"


def test_ic_basic():
    a = DisproportionalityAnalyzer()
    r = a.compute_ic(10, 90, 5, 895, 1000)
    assert r.value > 0
    assert r.metric == "IC"


def test_bcpnn_basic():
    a = DisproportionalityAnalyzer()
    r = a.compute_bcpnn(10, 90, 5, 895)
    assert r.value > 0
    assert r.metric == "BCPNN"


def test_min_cases():
    a = DisproportionalityAnalyzer(min_cases=5)
    r = a.compute_ror(2, 98, 5, 895)
    assert not r.is_significant


def test_analyze_2x2():
    a = DisproportionalityAnalyzer()
    results = a.analyze_2x2(20, 80, 10, 890)
    assert len(results) == 4
    assert results[0].metric == "ROR"
    assert results[1].metric == "PRR"
    assert results[2].metric == "IC"
    assert results[3].metric == "BCPNN"

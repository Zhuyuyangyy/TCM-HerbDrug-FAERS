"""Comprehensive smoke tests for TCM-HerbDrug-FAERS.

Tests cover:
- Core module imports
- Disproportionality analysis (ROR, PRR, IC, BCPNN)
- Signal detection engine
- Risk scoring system
- Herb name normalization
- API endpoint smoke tests
- Knowledge graph initialization
- Data validation
"""
import importlib
import math
import pytest


# ─── Module Import Tests ───────────────────────────────────────────

class TestImports:
    """Verify all core modules can be imported."""

    def test_import_backend(self):
        """Backend package should be importable."""
        import backend
        assert backend is not None

    def test_import_disproportionality(self):
        """Disproportionality analysis module."""
        from backend.models.disproportionality import (
            DisproportionalityAnalyzer, DisproportionalityResult
        )
        assert DisproportionalityAnalyzer is not None
        assert DisproportionalityResult is not None

    def test_import_signal_detector(self):
        """Signal detection engine."""
        from backend.models.signal_detector import SignalDetector, Signal
        assert SignalDetector is not None
        assert Signal is not None

    def test_import_risk_scoring(self):
        """Risk scoring module."""
        from backend.analysis.risk_scoring import RiskScorer, RiskScore
        assert RiskScorer is not None
        assert RiskScore is not None

    def test_import_herb_normalizer(self):
        """Herb name normalization module."""
        from backend.data.herb_name_normalizer import (
            HERB_PROFILES, get_herb_profile, get_faers_pattern,
            get_all_herb_names, get_known_positive_controls
        )
        assert HERB_PROFILES is not None
        assert callable(get_herb_profile)
        assert callable(get_faers_pattern)

    def test_import_config(self):
        """Configuration module."""
        from backend.config import settings, Settings
        assert settings is not None
        assert settings.app_name == "TCM-HerbDrug-FAERS"

    def test_import_mechanism_graph(self):
        """Mechanism graph module."""
        from backend.models.mechanism_graph import MechanismGraph
        assert MechanismGraph is not None

    def test_import_temporal_signal(self):
        """Temporal signal analysis module."""
        from backend.models.temporal_signal import DisproportionalityTimeSeries
        assert DisproportionalityTimeSeries is not None


# ─── Disproportionality Analysis Tests ─────────────────────────────

class TestDisproportionality:
    """Test ROR, PRR, IC, BCPNN calculations."""

    @pytest.fixture
    def analyzer(self):
        from backend.models.disproportionality import DisproportionalityAnalyzer
        return DisproportionalityAnalyzer(min_cases=3)

    def test_ror_basic(self, analyzer):
        """ROR should detect signal when ad >> bc."""
        r = analyzer.compute_ror(50, 50, 5, 895)
        assert r.metric == "ROR"
        assert r.value > 1.0
        assert r.is_significant is True
        assert r.ci_lower > 0

    def test_ror_no_signal(self, analyzer):
        """ROR should not signal when a is very low."""
        r = analyzer.compute_ror(2, 98, 5, 895)
        assert r.is_significant is False

    def test_ror_zero_cells(self, analyzer):
        """ROR should handle zero cells with Haldane-Anscombe correction."""
        r = analyzer.compute_ror(0, 100, 5, 895)
        assert r.value > 0  # Should not crash or return 0
        assert not r.is_significant  # a=0 < min_cases

    def test_prr_basic(self, analyzer):
        """PRR should detect proportional reporting difference."""
        r = analyzer.compute_prr(50, 50, 5, 895)
        assert r.metric == "PRR"
        assert r.value > 1.0
        assert r.is_significant is True

    def test_prr_no_signal(self, analyzer):
        """PRR should not signal for low counts."""
        r = analyzer.compute_prr(2, 98, 3, 897)
        assert not r.is_significant

    def test_ic_basic(self, analyzer):
        """IC should be positive when observed > expected."""
        r = analyzer.compute_ic(50, 50, 5, 895, 1000)
        assert r.metric == "IC"
        assert r.value > 0
        assert r.expected > 0

    def test_ic_zero_expected(self, analyzer):
        """IC should handle edge case when expected is near zero."""
        r = analyzer.compute_ic(0, 50, 0, 950, 1000)
        assert r.value == 0

    def test_bcpnn_basic(self, analyzer):
        """BCPNN should produce smoothed IC estimate."""
        r = analyzer.compute_bcpnn(50, 50, 5, 895)
        assert r.metric == "BCPNN"
        assert r.value > 0
        assert r.ci_lower is not None
        assert r.ci_upper is not None

    def test_bcpnn_zero_count(self, analyzer):
        """BCPNN should handle zero cases gracefully."""
        r = analyzer.compute_bcpnn(0, 100, 5, 895)
        assert r.value == 0.0
        assert r.is_significant is False

    def test_analyze_2x2_all_metrics(self, analyzer):
        """analyze_2x2 should return all four metrics."""
        results = analyzer.analyze_2x2(30, 70, 10, 890)
        assert len(results) == 4
        metric_names = [r.metric for r in results]
        assert "ROR" in metric_names
        assert "PRR" in metric_names
        assert "IC" in metric_names
        assert "BCPNN" in metric_names

    def test_confidence_intervals(self, analyzer):
        """CI lower should be <= value <= CI upper."""
        r = analyzer.compute_ror(20, 80, 10, 890)
        assert r.ci_lower <= r.value <= r.ci_upper


# ─── Signal Detection Tests ────────────────────────────────────────

class TestSignalDetection:
    """Test multi-metric signal detection engine."""

    @pytest.fixture
    def detector(self):
        from backend.models.signal_detector import SignalDetector
        return SignalDetector()

    def test_strong_signal(self, detector):
        """Should detect strong signal for high ROR + high IC."""
        s = detector.detect_signal("warfarin", "bleeding", 50, 50, 5, 900)
        assert s.is_signal is True
        assert s.signal_strength in ("strong", "moderate")

    def test_no_signal(self, detector):
        """Should not detect signal when counts are low."""
        s = detector.detect_signal("aspirin", "headache", 2, 98, 3, 897)
        assert s.signal_strength == "none" or not s.is_signal

    def test_mgps_classification(self, detector):
        """MGPS should classify based on EBGM/EB05 thresholds."""
        assert detector.classify_mgps(6.0, 3.0, 10) == "disproportionate_strong"
        assert detector.classify_mgps(2.5, 1.2, 10) == "disproportionate"
        assert detector.classify_mgps(1.6, 0.6, 10) == "weak_disproportionate"
        assert detector.classify_mgps(1.0, 0.3, 10) == "none"

    def test_mgps_low_cases(self, detector):
        """MGPS should return 'none' when cases below threshold."""
        assert detector.classify_mgps(10.0, 5.0, 1) == "none"

    def test_compute_mgps(self, detector):
        """MGPS computation should return expected keys."""
        result = detector._compute_mgps(20, 80, 10, 890)
        assert "ebgm" in result
        assert "eb05" in result
        assert "eb95" in result
        assert "n_exp" in result
        assert result["ebgm"] > 0

    def test_compute_mgps_zero(self, detector):
        """MGPS should handle zero cases."""
        result = detector._compute_mgps(0, 100, 10, 890)
        assert result["ebgm"] == 0.0

    def test_batch_detect(self, detector):
        """Batch detection should return sorted signals."""
        records = [
            {"drug": "warfarin", "event": "bleeding", "a": 50, "b": 50, "c": 5, "d": 900},
            {"drug": "aspirin", "event": "headache", "a": 2, "b": 98, "c": 3, "d": 897},
        ]
        signals = detector.batch_detect(records)
        assert len(signals) == 2
        # Should be sorted by ROR descending
        if signals[0].metrics and signals[1].metrics:
            assert signals[0].metrics[0].value >= signals[1].metrics[0].value


# ─── Risk Scoring Tests ────────────────────────────────────────────

class TestRiskScoring:
    """Test three-level risk assessment."""

    @pytest.fixture
    def scorer(self):
        from backend.analysis.risk_scoring import RiskScorer
        return RiskScorer()

    def test_no_signal(self, scorer):
        """No signal should return level 0."""
        rs = scorer.assess_risk("warfarin", "ginkgo")
        assert rs.level == 0
        assert rs.level_label == "no_signal"
        assert rs.score == 0

    def test_signal_only(self, scorer):
        """Signal only should be level 1."""
        rs = scorer.assess_risk("warfarin", "ginkgo",
                                has_signal=True, signal_strength="strong")
        assert rs.level == 1
        assert rs.level_label == "signal_only"
        assert rs.score > 0

    def test_signal_plus_database(self, scorer):
        """Signal + database should be level 2."""
        rs = scorer.assess_risk("warfarin", "ginkgo",
                                has_signal=True, signal_strength="moderate",
                                has_db_support=True)
        assert rs.level == 2
        assert rs.level_label == "signal_plus_database"

    def test_signal_plus_mechanism(self, scorer):
        """Signal + database + mechanism should be level 3."""
        rs = scorer.assess_risk("warfarin", "ginkgo",
                                has_signal=True, signal_strength="strong",
                                has_db_support=True, has_mechanism=True,
                                mechanism_confidence=0.9)
        assert rs.level == 3
        assert rs.level_label == "signal_plus_mechanism"
        assert rs.score > 50

    def test_score_capped_at_100(self, scorer):
        """Score should not exceed 100."""
        rs = scorer.assess_risk("warfarin", "ginkgo",
                                has_signal=True, signal_strength="strong",
                                has_db_support=True, has_mechanism=True,
                                mechanism_confidence=1.0, cyp_potency=1.0)
        assert rs.score <= 100

    def test_bootstrap_ci(self, scorer):
        """Bootstrap CI should produce valid bounds."""
        samples = [
            {"has_signal": True, "signal_strength": "strong"},
            {"has_signal": True, "signal_strength": "moderate"},
        ]
        rs = scorer.bootstrap_risk_ci("warfarin", "ginkgo", samples)
        assert rs.ci_method == "bootstrap"
        assert rs.ci_lower <= rs.score <= rs.ci_upper

    def test_bootstrap_ci_from_params(self, scorer):
        """Bootstrap CI from params should work."""
        rs = scorer.bootstrap_risk_ci_from_params(
            "warfarin", "ginkgo",
            base_params={"has_signal": True, "signal_strength": "strong"}
        )
        assert rs.ci_method == "bootstrap"
        assert rs.ci_lower >= 0


# ─── Herb Name Normalization Tests ────────────────────────────────

class TestHerbNormalization:
    """Test herb name matching and normalization."""

    def test_herb_profiles_loaded(self):
        """HERB_PROFILES should contain 16 herbs."""
        from backend.data.herb_name_normalizer import HERB_PROFILES
        assert len(HERB_PROFILES) == 16

    def test_get_herb_profile_direct(self):
        """Should find herb by direct key."""
        from backend.data.herb_name_normalizer import get_herb_profile
        p = get_herb_profile("ginkgo")
        assert p is not None
        assert p.common_name == "Ginkgo biloba"

    def test_get_herb_profile_by_common_name(self):
        """Should find herb by common name."""
        from backend.data.herb_name_normalizer import get_herb_profile
        p = get_herb_profile("Ginkgo biloba")
        assert p is not None

    def test_get_herb_profile_by_latin_name(self):
        """Should find herb by Latin name."""
        from backend.data.herb_name_normalizer import get_herb_profile
        p = get_herb_profile("Ginkgo biloba L.")
        assert p is not None

    def test_get_herb_profile_unknown(self):
        """Should return None for unknown herb."""
        from backend.data.herb_name_normalizer import get_herb_profile
        p = get_herb_profile("nonexistent_herb_xyz")
        assert p is None

    def test_get_faers_pattern(self):
        """Should return combined regex pattern."""
        from backend.data.herb_name_normalizer import get_faers_pattern
        pattern = get_faers_pattern("ginkgo")
        assert pattern is not None
        assert "GINKGO" in pattern

    def test_get_all_herb_names(self):
        """Should return all 16 herb names."""
        from backend.data.herb_name_normalizer import get_all_herb_names
        names = get_all_herb_names()
        assert len(names) == 16
        assert "ginkgo" in names
        assert "st_johns_wort" in names

    def test_positive_controls(self):
        """Should return positive controls for validation."""
        from backend.data.herb_name_normalizer import get_known_positive_controls
        controls = get_known_positive_controls()
        assert len(controls) > 20  # Should have 28+ controls
        # Check structure
        first = controls[0]
        assert "herb" in first
        assert "herb_key" in first
        assert "drug" in first

    def test_all_herbs_have_patterns(self):
        """Every herb should have at least one FAERS pattern."""
        from backend.data.herb_name_normalizer import get_all_herb_patterns
        patterns = get_all_herb_patterns()
        assert len(patterns) == 16
        for name, pattern in patterns.items():
            assert len(pattern) > 0, f"{name} has empty pattern"


# ─── Knowledge Graph Tests ────────────────────────────────────────

class TestKnowledgeGraph:
    """Test knowledge graph initialization."""

    def test_herb_kg_init(self):
        """Herb knowledge graph should initialize."""
        from backend.data.herb_kg import HerbKnowledgeGraph
        kg = HerbKnowledgeGraph()
        assert kg is not None

    def test_mechanism_graph_init(self):
        """Mechanism graph should initialize."""
        from backend.models.mechanism_graph import MechanismGraph
        mg = MechanismGraph()
        assert mg.graph is not None
        assert mg.graph.number_of_nodes() > 0


# ─── API Endpoint Tests ────────────────────────────────────────────

class TestAPIEndpoints:
    """Test FastAPI application endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health check should return OK."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_api_summary(self, client):
        """API summary should return platform info."""
        r = client.get("/api/summary")
        assert r.status_code == 200
        data = r.json()
        assert "platform" in data
        assert "herbs" in data
        assert len(data["herbs"]) > 0

    def test_signal_detect_endpoint(self, client):
        """Signal detection endpoint should work."""
        r = client.post("/api/signal/detect",
                        json={"drug": "warfarin", "event": "bleeding",
                              "a": 50, "b": 50, "c": 5, "d": 900})
        assert r.status_code == 200
        data = r.json()
        assert "is_signal" in data

    def test_risk_assess_endpoint(self, client):
        """Risk assessment endpoint should work."""
        r = client.post("/api/risk/assess",
                        json={"drug": "warfarin", "herb": "ginkgo",
                              "signal_strength": "strong",
                              "has_db_support": True, "has_mechanism": True,
                              "mechanism_confidence": 0.9, "cyp_potency": 0.8})
        assert r.status_code == 200
        data = r.json()
        assert data["risk_level"] >= 1
        assert data["score"] > 0

    def test_evidence_chain_endpoint(self, client):
        """Evidence chain endpoint should return chain info."""
        r = client.get("/api/risk/chain?drug=warfarin&herb=ginkgo")
        assert r.status_code == 200
        data = r.json()
        assert "chain_type" in data


# ─── Configuration Tests ──────────────────────────────────────────

class TestConfiguration:
    """Test configuration settings."""

    def test_settings_defaults(self):
        """Default settings should be valid."""
        from backend.config import Settings
        s = Settings()
        assert s.app_name == "TCM-HerbDrug-FAERS"
        assert s.port == 8013
        assert s.ror_threshold == 2.0
        assert s.min_cases == 3

    def test_settings_from_env(self):
        """Settings.from_env should work."""
        from backend.config import Settings
        s = Settings.from_env()
        assert s is not None
        assert s.host is not None


# ─── Data File Tests ───────────────────────────────────────────────

class TestDataFiles:
    """Test that required data files exist and are valid."""

    def test_known_hdi_pairs_exists(self):
        """Known HDI pairs file should exist."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "known_hdi_pairs.yaml")
        assert os.path.exists(path), f"Missing: {path}"

    def test_herb_drug_pairs_exists(self):
        """Herb-drug pairs file should exist."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "herb_drug_pairs.yaml")
        assert os.path.exists(path), f"Missing: {path}"

    def test_known_hdi_pairs_valid_yaml(self):
        """Known HDI pairs should be valid YAML."""
        import yaml
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "known_hdi_pairs.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "pairs" in data
        assert len(data["pairs"]) > 20

    def test_negative_controls_exist(self):
        """Negative controls should be present in known_hdi_pairs.yaml."""
        import yaml
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "known_hdi_pairs.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "negative_controls" in data
        assert len(data["negative_controls"]) > 0

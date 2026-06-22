"""Signal detection engine combining multiple disproportionality metrics."""
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .disproportionality import DisproportionalityAnalyzer, DisproportionalityResult

@dataclass
class Signal:
    drug: str
    event: str
    metrics: List[DisproportionalityResult]
    is_signal: bool
    signal_strength: str  # "strong", "moderate", "weak"
    mgps_class: str = "none"  # MGPS-based classification

class SignalDetector:
    """多指标联合信号检测引擎"""

    # MGPS (Multi-Item Gamma Poisson Shrinker) thresholds
    # Based on the Empirical Bayes Geometric Mean (EBGM) score
    # and its lower 95% confidence bound (EB05)
    MGPS_THRESHOLDS = {
        "disproportionate_strong":  {"ebgm": 5.0, "eb05": 2.0},
        "disproportionate":         {"ebgm": 2.0, "eb05": 1.0},
        "weak_disproportionate":    {"ebgm": 1.5, "eb05": 0.5},
    }

    def __init__(self, ror_threshold=2.0, prr_threshold=2.0, ic_threshold=0.0, min_cases=3):
        self.analyzer = DisproportionalityAnalyzer(min_cases=min_cases)
        self.ror_threshold = ror_threshold
        self.prr_threshold = prr_threshold
        self.ic_threshold = ic_threshold

    def _compute_mgps(self, a: int, b: int, c: int, d: int) -> Dict[str, float]:
        """Approximate MGPS (Multi-Item Gamma Poisson Shrinker) computation.

        Uses an empirical Bayes approach with a Gamma prior on the
        reporting rate ratio.  We approximate EBGM and EB05 using the
        observed-to-expected ratio with a Bayesian shrinkage factor.

        Prior: Gamma(alpha=0.2, beta=0.2) — weakly informative, standard in FAERS.
        Posterior expected RR = (a + alpha) / (E[a] + alpha * (1 + shrink_factor))

        For a lightweight approximation:
          E[a] = (a+b)*(a+c) / n
          EBGM  ~ posterior geometric mean of the RR
          EB05  ~ lower 5th percentile (approximate via log-normal CI)
        """
        n = a + b + c + d
        if n == 0 or a == 0:
            return {"ebgm": 0.0, "eb05": 0.0, "eb95": 0.0, "n_exp": 0.0}

        # Expected count under independence
        n_exp = ((a + b) * (a + c)) / n
        if n_exp <= 0:
            return {"ebgm": 0.0, "eb05": 0.0, "eb95": 0.0, "n_exp": 0.0}

        # Gamma prior parameters (standard FAERS MGPS)
        alpha_prior = 0.2
        beta_prior = 0.2

        # Posterior parameters for the Poisson-Gamma model
        alpha_post = a + alpha_prior
        beta_post = 1.0 + beta_prior / n_exp  # rate adjusted by expected

        # EBGM = posterior expected relative reporting rate (geometric mean)
        rr = (a + alpha_prior) / (n_exp + alpha_prior)
        ebgm = rr  # point estimate

        # Approximate EB05/EB95 via log-normal posterior CI
        # Using posterior variance: var(RR) = alpha_post / beta_post^2
        # On log scale: var(log RR) ≈ 1/alpha_post (digamma-based approximation)
        log_ebgm = math.log(max(ebgm, 1e-10))
        se_log = math.sqrt(1.0 / alpha_post)
        eb05 = math.exp(log_ebgm - 1.645 * se_log)  # 5th percentile
        eb95 = math.exp(log_ebgm + 1.645 * se_log)  # 95th percentile

        return {
            "ebgm": round(ebgm, 4),
            "eb05": round(eb05, 4),
            "eb95": round(eb95, 4),
            "n_exp": round(n_exp, 4),
        }

    def classify_mgps(self, ebgm: float, eb05: float, n_cases: int) -> str:
        """Classify signal strength using MGPS criteria (FDA/WHO standard).

        Categories:
          - disproportionate_strong:  EBGM >= 5 AND EB05 >= 2
          - disproportionate:         EBGM >= 2 AND EB05 >= 1
          - weak_disproportionate:    EBGM >= 1.5 AND EB05 >= 0.5
          - none:                     Below all thresholds
        """
        if n_cases < self.analyzer.min_cases:
            return "none"
        for level, thresh in self.MGPS_THRESHOLDS.items():
            if ebgm >= thresh["ebgm"] and eb05 >= thresh["eb05"]:
                return level
        return "none"

    def detect_signal(self, drug: str, event: str, a: int, b: int, c: int, d: int) -> Signal:
        metrics = self.analyzer.analyze_2x2(a, b, c, d)
        ror, prr, ic, bcpnn, yules_q = metrics

        # Traditional combined decision
        is_signal = ror.is_significant and prr.is_significant
        if is_signal and ror.value > 5 and ic.value > 2:
            strength = "strong"
        elif is_signal:
            strength = "moderate"
        elif ror.is_significant or prr.is_significant:
            strength = "weak"
        else:
            strength = "none"

        # MGPS classification
        mgps = self._compute_mgps(a, b, c, d)
        mgps_class = self.classify_mgps(mgps["ebgm"], mgps["eb05"], a)

        # Upgrade signal strength if MGPS says strong and traditional says moderate
        if mgps_class == "disproportionate_strong" and strength in ("moderate", "weak"):
            strength = "strong"
        elif mgps_class == "disproportionate" and strength == "weak":
            strength = "moderate"

        return Signal(drug=drug, event=event, metrics=metrics,
                      is_signal=is_signal and strength != "none",
                      signal_strength=strength,
                      mgps_class=mgps_class)

    def batch_detect(self, records: List[Dict]) -> List[Signal]:
        signals = []
        for rec in records:
            sig = self.detect_signal(rec["drug"], rec["event"],
                                     rec["a"], rec["b"], rec["c"], rec["d"])
            signals.append(sig)
        return sorted(signals, key=lambda s: s.metrics[0].value if s.metrics else 0, reverse=True)

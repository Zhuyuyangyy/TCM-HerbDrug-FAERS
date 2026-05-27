"""Temporal disproportionality signal tracking for FAERS quarterly windows.

Tracks ROR/PRR over quarterly FAERS data windows and detects trends
for early warning of emerging herb-drug interaction safety signals.
"""
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .disproportionality import DisproportionalityAnalyzer, DisproportionalityResult


@dataclass
class QuarterlySignal:
    """A disproportionality result for a specific quarter."""
    quarter: str  # e.g. "2023Q1"
    year: int
    q: int  # 1-4
    herb: str
    drug: str
    ror: float
    prr: float
    ror_ci_lower: float
    ror_ci_upper: float
    prr_ci_lower: float
    prr_ci_upper: float
    cases: int
    expected: float
    is_signal: bool


@dataclass
class TrendResult:
    """Result of trend analysis for a herb-drug pair."""
    herb: str
    drug: str
    quarters: List[str]
    ror_values: List[float]
    prr_values: List[float]
    cases_values: List[int]
    # Trend metrics
    ror_slope: float  # linear regression slope
    prr_slope: float
    ror_trend_p_value: float  # approximate p-value
    prr_trend_p_value: float
    is_increasing: bool  # ROR/PRR significantly increasing
    is_early_warning: bool  # meets early warning criteria
    trend_strength: str  # "strong", "moderate", "weak", "none"
    latest_ror: float
    latest_prr: float
    peak_ror: float
    peak_quarter: str


class DisproportionalityTimeSeries:
    """Track ROR/PRR over quarterly FAERS windows.

    Maintains a time series of 2x2 contingency tables per herb-drug pair
    and computes disproportionality metrics for each quarterly window.
    Enables trend detection and early warning for emerging signals.
    """

    def __init__(self, min_cases: int = 3):
        self.min_cases = min_cases
        self.analyzer = DisproportionalityAnalyzer(min_cases=min_cases)
        # Storage: {(herb, drug): [(quarter, a, b, c, d)]}
        self._quarterly_data: Dict[Tuple[str, str], List[Tuple[str, int, int, int, int]]] = {}

    def add_quarterly_data(self, herb: str, drug: str, quarter: str,
                           a: int, b: int, c: int, d: int):
        """Add a quarterly 2x2 contingency table entry.

        Args:
            herb: Herb name
            drug: Drug name
            quarter: Quarter string (e.g. "2023Q1")
            a: Herb+Drug+Event count
            b: Herb+Drug+Not-Event count
            c: Not-Herb+Drug+Event count
            d: Not-Herb+Drug+Not-Event count
        """
        key = (herb, drug)
        if key not in self._quarterly_data:
            self._quarterly_data[key] = []
        self._quarterly_data[key].append((quarter, a, b, c, d))
        # Sort by quarter
        self._quarterly_data[key].sort(key=lambda x: self._parse_quarter(x[0]))

    def compute_quarterly_signals(self, herb: str, drug: str) -> List[QuarterlySignal]:
        """Compute ROR/PRR for each quarterly window of a herb-drug pair."""
        key = (herb, drug)
        data = self._quarterly_data.get(key, [])
        signals = []
        for quarter, a, b, c, d in data:
            year, q = self._parse_quarter(quarter)
            ror = self.analyzer.compute_ror(a, b, c, d)
            prr = self.analyzer.compute_prr(a, b, c, d)
            signals.append(QuarterlySignal(
                quarter=quarter, year=year, q=q,
                herb=herb, drug=drug,
                ror=ror.value, prr=prr.value,
                ror_ci_lower=ror.ci_lower, ror_ci_upper=ror.ci_upper,
                prr_ci_lower=prr.ci_lower, prr_ci_upper=prr.ci_upper,
                cases=a, expected=ror.expected,
                is_signal=ror.is_significant and prr.is_significant,
            ))
        return signals

    def detect_trend(self, herb: str, drug: str,
                     min_quarters: int = 3) -> Optional[TrendResult]:
        """Detect whether ROR/PRR shows an increasing trend (early warning).

        Uses linear regression on log(ROR) and log(PRR) over quarterly windows.
        An early warning is issued when:
        - The slope is significantly positive (>0.05 per quarter)
        - At least min_quarters of data are available
        - The latest quarter shows a significant signal
        - The ROR has increased by >= 50% from baseline

        Returns:
            TrendResult with trend analysis, or None if insufficient data.
        """
        signals = self.compute_quarterly_signals(herb, drug)
        if len(signals) < min_quarters:
            return None

        quarters = [s.quarter for s in signals]
        ror_vals = [max(s.ror, 0.01) for s in signals]
        prr_vals = [max(s.prr, 0.01) for s in signals]
        cases_vals = [s.cases for s in signals]

        # Log-linear regression for trend
        log_ror = [math.log(v) for v in ror_vals]
        log_prr = [math.log(v) for v in prr_vals]
        x = list(range(len(signals)))

        ror_slope, ror_p, ror_r2 = self._linear_regression(x, log_ror)
        prr_slope, prr_p, prr_r2 = self._linear_regression(x, log_prr)

        # Determine if trend is increasing
        is_increasing = (ror_slope > 0.05 and ror_p < 0.2) or                         (prr_slope > 0.05 and prr_p < 0.2)

        # Early warning criteria
        latest = signals[-1]
        baseline_ror = ror_vals[0] if ror_vals[0] > 0 else 0.01
        ror_increase = (ror_vals[-1] - baseline_ror) / baseline_ror
        is_early_warning = (
            is_increasing and
            latest.is_signal and
            ror_increase >= 0.5 and
            len(signals) >= min_quarters
        )

        # Trend strength
        if ror_slope > 0.15 and ror_p < 0.1:
            trend_strength = "strong"
        elif ror_slope > 0.08 and ror_p < 0.2:
            trend_strength = "moderate"
        elif ror_slope > 0.03:
            trend_strength = "weak"
        else:
            trend_strength = "none"

        peak_idx = max(range(len(ror_vals)), key=lambda i: ror_vals[i])

        return TrendResult(
            herb=herb,
            drug=drug,
            quarters=quarters,
            ror_values=ror_vals,
            prr_values=prr_vals,
            cases_values=cases_vals,
            ror_slope=round(ror_slope, 4),
            prr_slope=round(prr_slope, 4),
            ror_trend_p_value=round(ror_p, 4),
            prr_trend_p_value=round(prr_p, 4),
            is_increasing=is_increasing,
            is_early_warning=is_early_warning,
            trend_strength=trend_strength,
            latest_ror=ror_vals[-1],
            latest_prr=prr_vals[-1],
            peak_ror=ror_vals[peak_idx],
            peak_quarter=quarters[peak_idx],
        )

    def get_all_trends(self, min_quarters: int = 3) -> List[TrendResult]:
        """Get trend analysis for all tracked herb-drug pairs."""
        results = []
        for herb, drug in self._quarterly_data:
            trend = self.detect_trend(herb, drug, min_quarters)
            if trend:
                results.append(trend)
        return sorted(results, key=lambda t: t.ror_slope, reverse=True)

    def get_early_warnings(self, min_quarters: int = 3) -> List[TrendResult]:
        """Get only herb-drug pairs with early warning signals."""
        return [t for t in self.get_all_trends(min_quarters) if t.is_early_warning]

    def _parse_quarter(self, quarter: str) -> Tuple[int, int]:
        """Parse '2023Q1' -> (2023, 1)."""
        try:
            parts = quarter.upper().split("Q")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return 0, 0

    def _linear_regression(self, x: List[int], y: List[float]) -> Tuple[float, float, float]:
        """Simple linear regression: y = slope * x + intercept.

        Returns:
            (slope, p_value, r_squared)

        Uses t-test for significance of slope.
        """
        n = len(x)
        if n < 2:
            return 0.0, 1.0, 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)

        if ss_xx == 0:
            return 0.0, 1.0, 0.0

        slope = ss_xy / ss_xx
        intercept = mean_y - slope * mean_x

        # R-squared
        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0.0

        # Approximate p-value using t-distribution
        if n <= 2:
            return slope, 1.0, r_squared

        residuals = [yi - (slope * xi + intercept) for xi, yi in zip(x, y)]
        mse = sum(r ** 2 for r in residuals) / (n - 2)
        se_slope = math.sqrt(mse / ss_xx) if mse >= 0 and ss_xx > 0 else float('inf')

        t_stat = abs(slope / se_slope) if se_slope > 0 else 0.0

        # Approximate two-tailed p-value from t-statistic
        # Using the survival function approximation for t-distribution
        df = n - 2
        if t_stat == 0:
            p_value = 1.0
        else:
            # Simple approximation using normal distribution for large df
            # and a correction for small samples
            z = t_stat * (1 - 1 / (4 * df)) / math.sqrt(1 + t_stat ** 2 / (2 * df))
            p_value = 2.0 * self._normal_sf(abs(z))

        return slope, p_value, r_squared

    @staticmethod
    def _normal_sf(z: float) -> float:
        """Approximate standard normal survival function (1 - CDF)."""
        # Using the error function approximation
        return 0.5 * math.erfc(z / math.sqrt(2))

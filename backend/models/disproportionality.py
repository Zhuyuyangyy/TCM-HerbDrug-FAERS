"""ROR, PRR, IC disproportionality analysis with confidence intervals."""
import math
from dataclasses import dataclass
from typing import Optional

@dataclass
class DisproportionalityResult:
    metric: str
    value: float
    ci_lower: float
    ci_upper: float
    is_significant: bool
    cases: int
    expected: float

class DisproportionalityAnalyzer:
    """不成比例分析引擎 — ROR/PRR/IC"""

    def __init__(self, min_cases: int = 3):
        self.min_cases = min_cases

    def compute_ror(self, a: int, b: int, c: int, d: int) -> DisproportionalityResult:
        """Reporting Odds Ratio: ad/bc"""
        if b == 0 or c == 0:
            return DisproportionalityResult("ROR", 0, 0, 0, False, a, 0)
        ror = (a * d) / (b * c)
        log_ror = math.log(ror)
        se = math.sqrt(1/a + 1/b + 1/c + 1/d) if a > 0 else 999
        ci_lower = math.exp(log_ror - 1.96 * se)
        ci_upper = math.exp(log_ror + 1.96 * se)
        significant = ci_lower > 1.0 and a >= self.min_cases
        return DisproportionalityResult("ROR", round(ror, 4), round(ci_lower, 4),
                                        round(ci_upper, 4), significant, a, 0)

    def compute_prr(self, a: int, b: int, c: int, d: int) -> DisproportionalityResult:
        """Proportional Reporting Ratio: a/(a+b) / c/(c+d)"""
        if (a + b) == 0 or (c + d) == 0:
            return DisproportionalityResult("PRR", 0, 0, 0, False, a, 0)
        prr = (a / (a + b)) / (c / (c + d))
        log_prr = math.log(prr)
        se = math.sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d)) if a > 0 and c > 0 else 999
        ci_lower = math.exp(log_prr - 1.96 * se)
        ci_upper = math.exp(log_prr + 1.96 * se)
        significant = ci_lower > 1.0 and a >= self.min_cases
        return DisproportionalityResult("PRR", round(prr, 4), round(ci_lower, 4),
                                        round(ci_upper, 4), significant, a, 0)

    def compute_ic(self, a: int, b: int, c: int, d: int, n: int) -> DisproportionalityResult:
        """Information Component: log2(a*n11/n_exp)"""
        n11 = a
        n1_dot = a + b
        n_dot1 = a + c
        n_exp = (n1_dot * n_dot1) / n if n > 0 else 1
        if n_exp <= 0 or n11 <= 0:
            return DisproportionalityResult("IC", 0, 0, 0, False, a, 0)
        ic = math.log2(n11 / n_exp)
        se = 1.0 / math.sqrt(n11) if n11 > 0 else 999
        ci_lower = ic - 1.96 * se
        ci_upper = ic + 1.96 * se
        significant = ci_lower > 0 and a >= self.min_cases
        return DisproportionalityResult("IC", round(ic, 4), round(ci_lower, 4),
                                        round(ci_upper, 4), significant, a, round(n_exp, 4))

    def analyze_2x2(self, a: int, b: int, c: int, d: int) -> list:
        """Run all three metrics on a 2x2 table."""
        n = a + b + c + d
        return [self.compute_ror(a, b, c, d),
                self.compute_prr(a, b, c, d),
                self.compute_ic(a, b, c, d, n)]

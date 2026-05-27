"""ROR, PRR, IC, BCPNN disproportionality analysis with confidence intervals."""
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
    """不成比例分析引擎 — ROR/PRR/IC/BCPNN"""

    def __init__(self, min_cases: int = 3):
        self.min_cases = min_cases

    def compute_ror(self, a: int, b: int, c: int, d: int) -> DisproportionalityResult:
        """Reporting Odds Ratio: ad/bc"""
        if a == 0 or b == 0 or c == 0 or d == 0:
            # Use Haldane-Anscombe correction: add 0.5 to all cells
            a_c, b_c, c_c, d_c = a + 0.5, b + 0.5, c + 0.5, d + 0.5
            ror = (a_c * d_c) / (b_c * c_c)
            if a < self.min_cases:
                return DisproportionalityResult("ROR", round(ror, 4), 0, 999, False, a, 0)
        else:
            ror = (a * d) / (b * c)
        log_ror = math.log(ror)
        se = math.sqrt(1/a + 1/b + 1/c + 1/d)
        ci_lower = math.exp(log_ror - 1.96 * se)
        ci_upper = math.exp(log_ror + 1.96 * se)
        significant = ci_lower > 1.0 and a >= self.min_cases
        return DisproportionalityResult("ROR", round(ror, 4), round(ci_lower, 4),
                                        round(ci_upper, 4), significant, a, 0)

    def compute_prr(self, a: int, b: int, c: int, d: int) -> DisproportionalityResult:
        """Proportional Reporting Ratio: a/(a+b) / c/(c+d)"""
        if (a + b) == 0 or (c + d) == 0:
            return DisproportionalityResult("PRR", 0, 0, 0, False, a, 0)
        if a == 0:
            # Haldane-Anscombe correction
            a_c, b_c, c_c, d_c = a + 0.5, b + 0.5, c + 0.5, d + 0.5
            prr = (a_c / (a_c + b_c)) / (c_c / (c_c + d_c))
            if a < self.min_cases:
                return DisproportionalityResult("PRR", round(prr, 4), 0, 999, False, a, 0)
        else:
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

    def compute_bcpnn(self, a: int, b: int, c: int, d: int) -> DisproportionalityResult:
        """Bayesian Confidence Propagation Neural Network (BCPNN).

        Uses the IC (Information Component) posterior with Bayesian smoothing.
        The prior is Dirichlet with hyperparameters (0.5, 0.5, 0.5, 0.5)
        following the WHO-UMC method.

        Posterior expectation:
            E[IC] = log2((a + 0.5) * (a+b+c+d)) / ((a+b+0.5) * (a+c+0.5))

        Posterior variance (approximate):
            Var[IC] = 1/(ln2)^2 * ( 1/(a+0.5) - 1/(a+b+c+d+1) + 1/(a+b+0.5) - 1/(a+b+c+d+1)
                       + 1/(a+c+0.5) - 1/(a+b+c+d+1) )

        95% CI: E[IC] ± 1.96 * sqrt(Var[IC])

        Significant if lower CI bound > 0 (i.e., association not explained by chance).
        """
        n = a + b + c + d
        if n == 0 or a == 0:
            return DisproportionalityResult("BCPNN", 0.0, 0.0, 0.0, False, a, 0.0)

        # Prior pseudo-count (Dirichlet alpha = 0.5)
        alpha = 0.5
        # Posterior expected IC
        numerator = (a + alpha) * n
        denominator = (a + b + alpha) * (a + c + alpha)
        if denominator <= 0:
            return DisproportionalityResult("BCPNN", 0.0, 0.0, 0.0, False, a, 0.0)

        e_ic = math.log2(numerator / denominator)

        # Posterior variance of IC (approximate)
        ln2_sq = (math.log(2)) ** 2
        n_plus1 = n + 1
        var_ic = (1.0 / ln2_sq) * (
            1.0 / (a + alpha) - 1.0 / n_plus1
            + 1.0 / (a + b + alpha) - 1.0 / n_plus1
            + 1.0 / (a + c + alpha) - 1.0 / n_plus1
        )
        # Clamp variance to avoid negative values from numerical issues
        var_ic = max(var_ic, 0.0)
        se = math.sqrt(var_ic)

        ci_lower = e_ic - 1.96 * se
        ci_upper = e_ic + 1.96 * se

        # Expected count under independence
        n_exp = ((a + b) * (a + c)) / n if n > 0 else 0
        significant = ci_lower > 0.0 and a >= self.min_cases

        return DisproportionalityResult("BCPNN", round(e_ic, 4), round(ci_lower, 4),
                                        round(ci_upper, 4), significant, a, round(n_exp, 4))

    def analyze_2x2(self, a: int, b: int, c: int, d: int) -> list:
        """Run all four metrics on a 2x2 table."""
        n = a + b + c + d
        return [self.compute_ror(a, b, c, d),
                self.compute_prr(a, b, c, d),
                self.compute_ic(a, b, c, d, n),
                self.compute_bcpnn(a, b, c, d)]

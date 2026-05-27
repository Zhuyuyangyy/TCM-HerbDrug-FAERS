"""Three-level risk scoring for herb-drug interactions with bootstrap CI."""
import math
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class RiskScore:
    drug: str
    herb: str
    level: int  # 1, 2, 3
    level_label: str
    score: float  # 0-100
    factors: List[str]
    ci_lower: float = 0.0   # 95% bootstrap CI lower bound
    ci_upper: float = 0.0   # 95% bootstrap CI upper bound
    ci_method: str = "none"  # "bootstrap" or "none"

class RiskScorer:
    """三级风险评估: signal_only / signal_plus_database / signal_plus_mechanism"""

    def assess_risk(self, drug: str, herb: str,
                    has_signal: bool = False,
                    signal_strength: str = "none",
                    has_db_support: bool = False,
                    has_mechanism: bool = False,
                    mechanism_confidence: float = 0.0,
                    cyp_potency: float = 0.0) -> RiskScore:
        factors = []
        score = 0.0

        if has_signal:
            factors.append("FAERS/VigiBase signal detected")
            score += 20
            if signal_strength == "strong":
                score += 15
                factors.append("Strong signal (high ROR/PRR/IC)")
            elif signal_strength == "moderate":
                score += 10
            level = 1
            level_label = "signal_only"
        else:
            return RiskScore(drug, herb, 0, "no_signal", 0, ["No signal detected"])

        if has_db_support:
            score += 25
            factors.append("HDI database support")
            level = 2
            level_label = "signal_plus_database"

        if has_mechanism:
            score += int(mechanism_confidence * 25)
            factors.append(f"Mechanism pathway (conf={mechanism_confidence:.2f})")
            level = 3
            level_label = "signal_plus_mechanism"

        score += int(cyp_potency * 15)
        if cyp_potency > 0.7:
            factors.append(f"High CYP inhibition ({cyp_potency:.1%})")

        return RiskScore(drug=drug, herb=herb, level=min(level, 3),
                         level_label=level_label, score=min(score, 100), factors=factors)

    def bootstrap_risk_ci(self, drug: str, herb: str,
                          metric_samples: List[Dict],
                          n_bootstrap: int = 1000,
                          confidence: float = 0.95,
                          seed: int = 42) -> RiskScore:
        """Compute a risk score with bootstrap confidence interval.

        Parameters
        ----------
        drug : str
        herb : str
        metric_samples : list of dict
            Each dict contains keys for assess_risk kwargs drawn from
            observed data variability, e.g. signal_strength varies across
            resampled 2x2 tables.
        n_bootstrap : int
            Number of bootstrap resamples.
        confidence : float
            Confidence level (default 0.95 for 95% CI).
        seed : int
            Random seed for reproducibility.

        Returns
        -------
        RiskScore with ci_lower and ci_upper populated from the bootstrap
        distribution of the risk score.
        """
        if not metric_samples:
            rs = self.assess_risk(drug, herb)
            return rs

        rng = random.Random(seed)
        scores = []
        for _ in range(n_bootstrap):
            sample = rng.choice(metric_samples)
            rs = self.assess_risk(drug, herb, **sample)
            scores.append(rs.score)

        scores.sort()
        alpha = (1.0 - confidence) / 2.0
        lower_idx = max(0, int(math.floor(alpha * len(scores))))
        upper_idx = min(len(scores) - 1, int(math.ceil((1.0 - alpha) * len(scores)) - 1))

        ci_lower = scores[lower_idx]
        ci_upper = scores[upper_idx]

        # Also compute a point estimate from the original (non-resampled) parameters
        # Use the median sample for the point estimate
        median_idx = len(metric_samples) // 2
        point = self.assess_risk(drug, herb, **metric_samples[median_idx])

        return RiskScore(
            drug=drug, herb=herb,
            level=point.level, level_label=point.level_label,
            score=point.score, factors=point.factors,
            ci_lower=float(ci_lower), ci_upper=float(ci_upper),
            ci_method="bootstrap"
        )

    def bootstrap_risk_ci_from_params(self, drug: str, herb: str,
                                       base_params: Dict,
                                      n_bootstrap: int = 1000,
                                      score_std: float = 8.0,
                                      confidence: float = 0.95,
                                      seed: int = 42) -> RiskScore:
        """Convenience: compute bootstrap CI by perturbing the score directly.

        When metric_samples are not available, this method generates
        synthetic bootstrap perturbations around the base risk score by
        adding Gaussian noise proportional to score_std.

        Parameters
        ----------
        base_params : dict
            kwargs for assess_risk (has_signal, signal_strength, etc.)
        score_std : float
            Estimated standard deviation of the risk score from
            historical data or expert elicitation.
        """
        rng = random.Random(seed)
        base = self.assess_risk(drug, herb, **base_params)

        scores = []
        for _ in range(n_bootstrap):
            # Perturb continuous parameters
            p = dict(base_params)
            if p.get("mechanism_confidence", 0) > 0:
                p["mechanism_confidence"] = max(0, min(1,
                    p["mechanism_confidence"] + rng.gauss(0, 0.1)))
            if p.get("cyp_potency", 0) > 0:
                p["cyp_potency"] = max(0, min(1,
                    p["cyp_potency"] + rng.gauss(0, 0.1)))
            rs = self.assess_risk(drug, herb, **p)
            scores.append(rs.score)

        scores.sort()
        alpha = (1.0 - confidence) / 2.0
        lower_idx = max(0, int(math.floor(alpha * len(scores))))
        upper_idx = min(len(scores) - 1, int(math.ceil((1.0 - alpha) * len(scores)) - 1))

        return RiskScore(
            drug=drug, herb=herb,
            level=base.level, level_label=base.level_label,
            score=base.score, factors=base.factors,
            ci_lower=float(scores[lower_idx]),
            ci_upper=float(scores[upper_idx]),
            ci_method="bootstrap"
        )

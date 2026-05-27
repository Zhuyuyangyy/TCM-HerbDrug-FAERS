"""Three-level risk scoring for herb-drug interactions."""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RiskScore:
    drug: str
    herb: str
    level: int  # 1, 2, 3
    level_label: str
    score: float  # 0-100
    factors: List[str]

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

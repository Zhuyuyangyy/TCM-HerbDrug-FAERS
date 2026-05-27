"""Signal detection engine combining multiple disproportionality metrics."""
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

class SignalDetector:
    """多指标联合信号检测引擎"""

    def __init__(self, ror_threshold=2.0, prr_threshold=2.0, ic_threshold=0.0, min_cases=3):
        self.analyzer = DisproportionalityAnalyzer(min_cases=min_cases)
        self.ror_threshold = ror_threshold
        self.prr_threshold = prr_threshold
        self.ic_threshold = ic_threshold

    def detect_signal(self, drug: str, event: str, a: int, b: int, c: int, d: int) -> Signal:
        metrics = self.analyzer.analyze_2x2(a, b, c, d)
        ror, prr, ic = metrics
        is_signal = ror.is_significant and prr.is_significant
        if is_signal and ror.value > 5 and ic.value > 2:
            strength = "strong"
        elif is_signal:
            strength = "moderate"
        elif ror.is_significant or prr.is_significant:
            strength = "weak"
        else:
            strength = "none"
        return Signal(drug=drug, event=event, metrics=metrics,
                      is_signal=is_signal and strength != "none",
                      signal_strength=strength)

    def batch_detect(self, records: List[Dict]) -> List[Signal]:
        signals = []
        for rec in records:
            sig = self.detect_signal(rec["drug"], rec["event"],
                                     rec["a"], rec["b"], rec["c"], rec["d"])
            signals.append(sig)
        return sorted(signals, key=lambda s: s.metrics[0].value if s.metrics else 0, reverse=True)

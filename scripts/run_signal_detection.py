"""Run signal detection on FAERS data."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.faers_loader import FAERSLoader
from data.herb_kg import HerbKnowledgeGraph
from data.cyp_mapper import CYPMapper
from models.signal_detector import SignalDetector
from analysis.risk_scoring import RiskScorer
from analysis.evidence_chain import EvidenceChainBuilder

def main():
    loader = FAERSLoader()
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_faers.csv")
    if not os.path.exists(data_path):
        print("Run generate_synthetic_faers.py first")
        return
    loader.load_csv(data_path)
    print(f"Loaded {len(loader.records)} records")

    detector = SignalDetector()
    pairs = loader.get_drug_event_pairs(min_count=5)
    print(f"Drug-event pairs with >= 5 reports: {len(pairs)}")

    herb_kg = HerbKnowledgeGraph()
    cyp_mapper = CYPMapper()
    scorer = RiskScorer()
    chain_builder = EvidenceChainBuilder()

    signals = []
    for pair in pairs:
        ct = loader.build_contingency(pair["drug"], pair["event"])
        sig = detector.detect_signal(pair["drug"], pair["event"],
                                     ct["a"], ct["b"], ct["c"], ct["d"])
        if sig.is_signal:
            signals.append(sig)

    print(f"Detected signals: {len(signals)}/{len(pairs)}")
    for s in signals[:10]:
        print(f"  {s.drug} + {s.event}: {s.signal_strength} (ROR={s.metrics[0].value:.2f})")

if __name__ == "__main__":
    main()

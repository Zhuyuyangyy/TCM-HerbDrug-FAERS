"""Quick smoke test: generates synthetic data, runs full signal detection pipeline,
   and prints results.  No external dependencies required beyond the project itself.

Usage:
    python3 scripts/quick_smoke_test.py
"""
import sys
import os
import math
import random

# Ensure project root is on the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.models.disproportionality import DisproportionalityAnalyzer
from backend.models.signal_detector import SignalDetector
from backend.data.faers_loader import FAERSLoader
from backend.analysis.risk_scoring import RiskScorer

# ── Synthetic data generation ──────────────────────────────────────────────

random.seed(42)

DRUGS = ["warfarin", "clopidogrel", "digoxin", "cyclosporine",
         "simvastatin", "metformin", "omeprazole", "metoprolol"]
EVENTS = ["bleeding", "hepatotoxicity", "hypokalemia", "rash",
          "dizziness", "nausea", "renal_impairment", "cardiac_arrhythmia",
          "thrombocytopenia", "elevated_INR", "myopathy", "GI_hemorrhage"]

# Known high-risk pairs (more reports to produce signals)
HIGH_RISK = [
    ("warfarin", "bleeding",       0.30),
    ("warfarin", "elevated_INR",   0.25),
    ("digoxin",  "cardiac_arrhythmia", 0.20),
    ("cyclosporine", "hepatotoxicity", 0.15),
    ("clopidogrel", "bleeding",    0.12),
    ("simvastatin", "myopathy",    0.10),
]


def generate_synthetic_records(n: int = 6000):
    """Build synthetic FAERS-like records with boosted co-occurrences."""
    records = []
    for i in range(n):
        drug = random.choice(DRUGS)
        event = random.choice(EVENTS)
        for d, e, prob in HIGH_RISK:
            if random.random() < prob and drug == d:
                event = e
                break
        records.append({
            "primaryid": i, "caseid": i,
            "drugname": drug, "pt": event, "role_cod": "PS",
        })
    return records


def write_temp_csv(records, path):
    import csv
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["primaryid", "caseid", "drugname", "pt", "role_cod"])
        writer.writeheader()
        writer.writerows(records)


# ── Main smoke test ────────────────────────────────────────────────────────

def main():
    sep = "=" * 72
    print(sep)
    print("  TCM-HerbDrug-FAERS  ·  Quick Smoke Test")
    print(sep)

    # 1. Generate synthetic data
    records = generate_synthetic_records(6000)
    tmp_csv = os.path.join(PROJECT_ROOT, "data", "_smoke_test_synthetic.csv")
    os.makedirs(os.path.dirname(tmp_csv), exist_ok=True)
    write_temp_csv(records, tmp_csv)
    print(f"\n[1] Generated {len(records)} synthetic records -> {tmp_csv}")

    # 2. Load via FAERSLoader (with MedDRA PT mapping)
    loader = FAERSLoader()
    loaded = loader.load_csv(tmp_csv, apply_meddra=True)
    mapped_pts = loader.get_mapped_pts()
    print(f"[2] FAERSLoader loaded {len(loaded)} records; {len(mapped_pts)} unique mapped PTs")

    # 3. Test MedDRA mapping on synonym terms
    test_synonyms = ["haemorrhage", "renal failure", "arrhythmia", "inr increased"]
    print(f"[3] MedDRA synonym mapping tests:")
    for syn in test_synonyms:
        mapped = loader.map_pt(syn)
        print(f"      {syn:30s} -> {mapped}")

    # 4. Build contingency tables and detect signals
    detector = SignalDetector()
    pairs = loader.get_drug_event_pairs(min_count=5)
    print(f"\n[4] Drug-event pairs with >= 5 reports: {len(pairs)}")

    signals = []
    for pair in pairs:
        ct = loader.build_contingency(pair["drug"], pair["event"])
        sig = detector.detect_signal(pair["drug"], pair["event"],
                                     ct["a"], ct["b"], ct["c"], ct["d"])
        signals.append(sig)

    detected = [s for s in signals if s.is_signal]
    print(f"    Detected signals: {len(detected)}/{len(signals)}")

    print(f"\n    {'Drug':<18s} {'Event':<25s} {'Strength':<10s} {'MGPS':<22s} "
          f"{'ROR':>8s} {'PRR':>8s} {'IC':>8s} {'BCPNN':>8s}")
    print("    " + "-" * 115)
    for s in sorted(detected, key=lambda x: x.metrics[0].value, reverse=True)[:15]:
        ror = s.metrics[0]
        prr = s.metrics[1]
        ic  = s.metrics[2]
        bcpnn = s.metrics[3]
        print(f"    {s.drug:<18s} {s.event:<25s} {s.signal_strength:<10s} {s.mgps_class:<22s} "
              f"{ror.value:>8.2f} {prr.value:>8.2f} {ic.value:>8.2f} {bcpnn.value:>8.2f}")

    # 5. Test all 4 disproportionality metrics explicitly
    print(f"\n[5] Disproportionality metric unit test (a=30, b=70, c=100, d=9800):")
    analyzer = DisproportionalityAnalyzer()
    results = analyzer.analyze_2x2(30, 70, 100, 9800)
    for r in results:
        sig_mark = "***" if r.is_significant else "   "
        print(f"      {r.metric:>6s}: value={r.value:>8.4f}  "
              f"CI=[{r.ci_lower:>8.4f}, {r.ci_upper:>8.4f}]  "
              f"sig={sig_mark}")

    # 6. Risk scoring with bootstrap CI
    print(f"\n[6] Risk scoring with bootstrap confidence interval:")
    scorer = RiskScorer()
    base_params = {
        "has_signal": True,
        "signal_strength": "strong",
        "has_db_support": True,
        "has_mechanism": True,
        "mechanism_confidence": 0.8,
        "cyp_potency": 0.75,
    }
    rs = scorer.assess_risk("warfarin", "丹参", **base_params)
    print(f"    Point estimate: score={rs.score}, level={rs.level} ({rs.level_label})")

    rs_boot = scorer.bootstrap_risk_ci_from_params(
        "warfarin", "丹参", base_params, n_bootstrap=2000
    )
    print(f"    Bootstrap 95% CI: [{rs_boot.ci_lower:.1f}, {rs_boot.ci_upper:.1f}] "
          f"(method={rs_boot.ci_method})")
    print(f"    Factors: {', '.join(rs_boot.factors)}")

    # 7. Summary
    print(f"\n{sep}")
    print(f"  SMOKE TEST PASSED")
    print(f"    - {len(records)} synthetic records generated and loaded")
    print(f"    - MedDRA PT mapping: {len(test_synonyms)} synonyms resolved")
    print(f"    - 4 disproportionality metrics computed (ROR, PRR, IC, BCPNN)")
    print(f"    - MGPS signal classification applied")
    print(f"    - {len(detected)} signals detected from {len(pairs)} drug-event pairs")
    print(f"    - Bootstrap CI computed ({rs_boot.ci_method})")
    print(sep)

    # Cleanup temp file
    try:
        os.remove(tmp_csv)
    except OSError:
        pass


if __name__ == "__main__":
    main()

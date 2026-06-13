#!/usr/bin/env python3
"""Run signal detection on synthetic FAERS data for method validation.

This script validates the signal detection pipeline using synthetic data
with known signal injection, before applying to real FAERS data.

DISCLAIMER: All results from this script are based on synthetic data with
injected signals. Sensitivity and specificity figures reflect performance
on synthetic data only and should NOT be interpreted as real-world
clinical performance. Results on real FAERS data have not yet been computed.

Tests:
1. Known signals should be detected (sensitivity)
2. Random noise should not be detected (specificity)
3. Signal strength should correlate with injection probability
4. All 4 metrics (ROR, PRR, IC, BCPNN) should agree on strong signals

Usage:
    python scripts/run_synthetic_validation.py
    python scripts/run_synthetic_validation.py --n-records 50000
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.models.disproportionality import DisproportionalityAnalyzer
from backend.models.signal_detector import SignalDetector


# Known signal injection parameters
INJECTED_SIGNALS = [
    {"drug": "warfarin", "herb": "danshen", "event": "hemorrhage", "prob": 0.30},
    {"drug": "warfarin", "herb": "danshen", "event": "elevated_INR", "prob": 0.25},
    {"drug": "warfarin", "herb": "ginkgo", "event": "hemorrhage", "prob": 0.20},
    {"drug": "digoxin", "herb": "licorice", "event": "cardiac_arrhythmia", "prob": 0.20},
    {"drug": "cyclosporine", "herb": "st_johns_wort", "event": "hepatotoxicity", "prob": 0.15},
    {"drug": "clopidogrel", "herb": "danshen", "event": "hemorrhage", "prob": 0.12},
    {"drug": "simvastatin", "herb": "red_yeast_rice", "event": "myopathy", "prob": 0.10},
    {"drug": "warfarin", "herb": "garlic", "event": "hemorrhage", "prob": 0.08},
    {"drug": "metformin", "herb": "ginseng", "event": "hypoglycemia", "prob": 0.06},
    {"drug": "aspirin", "herb": "danshen", "event": "GI_hemorrhage", "prob": 0.05},
]

# Noise drug-event pairs (should NOT be detected)
NOISE_PAIRS = [
    {"drug": "acetaminophen", "herb": "ginkgo", "event": "rash"},
    {"drug": "amoxicillin", "herb": "licorice", "event": "nausea"},
    {"drug": "omeprazole", "herb": "ginseng", "event": "dizziness"},
    {"drug": "lisinopril", "herb": "garlic", "event": "headache"},
    {"drug": "metoprolol", "herb": "turmeric", "event": "fatigue"},
]


def generate_synthetic_faers(
    n_records: int = 20000,
    seed: int = 42,
) -> list[dict]:
    """Generate synthetic FAERS-like data with injected signals."""
    rng = np.random.RandomState(seed)

    drugs = [
        "warfarin", "clopidogrel", "digoxin", "cyclosporine", "simvastatin",
        "metformin", "omeprazole", "metoprolol", "aspirin", "lisinopril",
        "atorvastatin", "amlodipine", "acetaminophen", "amoxicillin",
        "danshen", "ginkgo", "ginseng", "licorice", "garlic",
        "st_johns_wort", "red_yeast_rice", "turmeric",
    ]

    events = [
        "hemorrhage", "hepatotoxicity", "hypokalemia", "rash", "dizziness",
        "nausea", "renal_impairment", "cardiac_arrhythmia", "thrombocytopenia",
        "elevated_INR", "myopathy", "GI_hemorrhage", "hypoglycemia",
        "headache", "fatigue", "insomnia",
    ]

    records = []
    for i in range(n_records):
        # Pick a random drug and event as base
        drug = rng.choice(drugs)
        event = rng.choice(events)

        # Check if this drug-event pair should have an injected signal
        for sig in INJECTED_SIGNALS:
            if drug == sig["drug"] or drug == sig["herb"]:
                if rng.random() < sig["prob"]:
                    event = sig["event"]
                    if drug == sig["herb"]:
                        drug = sig["drug"]  # Co-reported
                    break

        role = rng.choice(["PS", "SS", "C"], p=[0.3, 0.4, 0.3])
        records.append({
            "primaryid": i,
            "caseid": i,
            "drugname": drug,
            "pt": event,
            "role_cod": role,
        })

    return records


def validate_signals(records: list[dict], min_cases: int = 3) -> dict:
    """Run signal detection and validate against known injections."""
    analyzer = DisproportionalityAnalyzer(min_cases=min_cases)
    detector = SignalDetector(min_cases=min_cases)

    # Build contingency tables for injected signals
    detected = []
    missed = []
    false_alarms = []

    for sig in INJECTED_SIGNALS:
        # Count co-occurrences
        drug_ids = set()
        event_ids = set()
        co_ids = set()

        for r in records:
            if r["role_cod"] not in ("PS", "SS"):
                continue
            rid = r["primaryid"]
            if r["drugname"] == sig["drug"]:
                drug_ids.add(rid)
            if r["pt"] == sig["event"]:
                event_ids.add(rid)
            if r["drugname"] == sig["drug"] and r["pt"] == sig["event"]:
                co_ids.add(rid)

        all_ids = set(r["primaryid"] for r in records)
        a = len(co_ids)
        b = len(drug_ids - co_ids)
        c = len(event_ids - co_ids)
        d = len(all_ids - drug_ids - event_ids)

        if a < min_cases:
            missed.append({**sig, "reason": f"too few cases ({a})"})
            continue

        signal = detector.detect_signal(sig["drug"], sig["event"], a, b, c, d)

        entry = {
            **sig,
            "a": a,
            "ror": signal.metrics[0].value if signal.metrics else 0,
            "prr": signal.metrics[1].value if signal.metrics else 0,
            "ic": signal.metrics[2].value if signal.metrics else 0,
            "bcpnn": signal.metrics[3].value if signal.metrics else 0,
            "strength": signal.signal_strength,
            "is_signal": signal.is_signal,
        }

        if signal.is_signal:
            detected.append(entry)
        else:
            missed.append({**entry, "reason": "not detected"})

    # Check noise pairs for false positives
    for noise in NOISE_PAIRS:
        drug_ids = set()
        event_ids = set()
        co_ids = set()

        for r in records:
            if r["role_cod"] not in ("PS", "SS"):
                continue
            rid = r["primaryid"]
            if r["drugname"] == noise["drug"]:
                drug_ids.add(rid)
            if r["pt"] == noise["event"]:
                event_ids.add(rid)
            if r["drugname"] == noise["drug"] and r["pt"] == noise["event"]:
                co_ids.add(rid)

        all_ids = set(r["primaryid"] for r in records)
        a = len(co_ids)
        b = len(drug_ids - co_ids)
        c = len(event_ids - co_ids)
        d = len(all_ids - drug_ids - event_ids)

        if a >= min_cases:
            signal = detector.detect_signal(noise["drug"], noise["event"], a, b, c, d)
            if signal.is_signal:
                false_alarms.append({
                    **noise, "a": a,
                    "ror": signal.metrics[0].value,
                    "strength": signal.signal_strength,
                })

    sensitivity = len(detected) / len(INJECTED_SIGNALS) if INJECTED_SIGNALS else 0
    specificity = 1 - len(false_alarms) / len(NOISE_PAIRS) if NOISE_PAIRS else 1

    return {
        "detected": detected,
        "missed": missed,
        "false_alarms": false_alarms,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "n_injected": len(INJECTED_SIGNALS),
        "n_noise": len(NOISE_PAIRS),
    }


def generate_report(result: dict, n_records: int) -> str:
    """Generate validation report."""
    lines = [
        "=" * 70,
        "SYNTHETIC FAERS VALIDATION RESULTS",
        "=" * 70,
        "WARNING: These results are based on SYNTHETIC data with injected",
        "signals. They do NOT reflect real-world clinical performance.",
        "=" * 70,
        f"Records: {n_records}",
        f"Injected signals: {result['n_injected']}",
        f"Noise pairs: {result['n_noise']}",
        "",
        f"Sensitivity: {result['sensitivity']:.1%} ({len(result['detected'])}/{result['n_injected']}) [synthetic data only]",
        f"Specificity: {result['specificity']:.1%} ({result['n_noise'] - len(result['false_alarms'])}/{result['n_noise']}) [synthetic data only]",
        "",
        "DETECTED SIGNALS:",
        "-" * 70,
        f"{'Drug':20s} {'Event':25s} {'N':>5s} {'ROR':>8s} {'Strength':>10s}",
        "-" * 70,
    ]

    for d in result["detected"]:
        lines.append(
            f"{d['drug']:20s} {d['event']:25s} {d['a']:5d} "
            f"{d['ror']:8.2f} {d['strength']:>10s}"
        )

    if result["missed"]:
        lines.append("")
        lines.append("MISSED SIGNALS:")
        lines.append("-" * 70)
        for m in result["missed"]:
            lines.append(f"  {m['drug']} + {m['event']}: {m.get('reason', 'unknown')}")

    if result["false_alarms"]:
        lines.append("")
        lines.append("FALSE ALARMS:")
        lines.append("-" * 70)
        for f in result["false_alarms"]:
            lines.append(f"  {f['drug']} + {f['event']}: ROR={f['ror']:.2f}")

    # Signal strength vs injection probability correlation
    lines.append("")
    lines.append("SIGNAL STRENGTH vs INJECTION PROBABILITY:")
    lines.append("-" * 50)
    for d in result["detected"]:
        lines.append(f"  p={d['prob']:.2f} -> {d['strength']:>10s} (ROR={d['ror']:.2f})")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-records", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-cases", type=int, default=3)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate
    print(f"Generating {args.n_records} synthetic FAERS records...")
    records = generate_synthetic_faers(args.n_records, args.seed)

    # Validate
    print("Running signal detection validation...")
    result = validate_signals(records, args.min_cases)

    # Report
    report = generate_report(result, args.n_records)
    print(report)

    # Save
    with open(output_dir / "synthetic_validation.txt", "w") as f:
        f.write(report)
    with open(output_dir / "synthetic_validation.json", "w") as f:
        json.dump({
            "sensitivity": result["sensitivity"],
            "specificity": result["specificity"],
            "detected": result["detected"],
            "missed": result["missed"],
            "false_alarms": result["false_alarms"],
        }, f, indent=2, default=str)

    print(f"\nResults saved to {output_dir}/")


if __name__ == "__main__":
    main()

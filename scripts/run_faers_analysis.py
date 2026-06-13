#!/usr/bin/env python3
"""Run real FAERS herb-drug interaction signal detection analysis.

Usage:
    # Download FAERS data first (see instructions below), then:
    python scripts/run_faers_analysis.py

    # Or specify data directory:
    python scripts/run_faers_analysis.py --data-dir /path/to/faers_ascii

    # Analyze specific herbs:
    python scripts/run_faers_analysis.py --herbs ginkgo ginseng danshen

    # Specify quarters:
    python scripts/run_faers_analysis.py --quarters 2023Q1 2023Q2 2023Q3 2023Q4

FAERS Data Download Instructions:
    1. Visit: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
    2. Download quarterly ASCII files (e.g., "faers_ascii_2023Q1.zip")
    3. Extract each quarter into data/faers_ascii/2023Q1/, data/faers_ascii/2023Q2/, etc.
    4. Each quarter directory should contain: DEMO.txt, DRUG.txt, REAC.txt, etc.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.analysis.faers_pipeline import FAERSAnalysisPipeline
from backend.data.herb_name_normalizer import get_all_herb_names

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run FAERS herb-drug interaction signal detection"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data/faers_ascii",
        help="Path to FAERS ASCII data directory (default: data/faers_ascii)"
    )
    parser.add_argument(
        "--herbs", nargs="*", default=None,
        help="Herbs to analyze (default: all in database)"
    )
    parser.add_argument(
        "--quarters", nargs="*", default=None,
        help="Quarters to load (default: all available)"
    )
    parser.add_argument(
        "--min-cases", type=int, default=3,
        help="Minimum case count for signal detection (default: 3)"
    )
    parser.add_argument(
        "--top-k", type=int, default=20,
        help="Number of top events per herb (default: 20)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="output",
        help="Output directory for results (default: output)"
    )
    parser.add_argument(
        "--no-validate", action="store_true",
        help="Skip positive control validation"
    )
    args = parser.parse_args()

    # Check data directory
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("FAERS data directory not found: %s", data_dir)
        logger.error("")
        logger.error("Please download FAERS data first:")
        logger.error("  1. Visit: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html")
        logger.error("  2. Download quarterly ASCII files")
        logger.error("  3. Extract into %s/QQNN/", data_dir)
        logger.error("")
        logger.error("Example directory structure:")
        logger.error("  %s/", data_dir)
        logger.error("  ├── 2023Q1/")
        logger.error("  │   ├── DEMO23Q1.txt")
        logger.error("  │   ├── DRUG23Q1.txt")
        logger.error("  │   ├── REAC23Q1.txt")
        logger.error("  │   └── ...")
        logger.error("  ├── 2023Q2/")
        logger.error("  │   └── ...")
        sys.exit(1)

    # Resolve herb names
    herb_names = args.herbs
    if herb_names:
        available = get_all_herb_names()
        for h in herb_names:
            if h.lower().replace("-", "_").replace(" ", "_") not in available:
                logger.warning("Herb '%s' not in database. Available: %s", h, available)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run pipeline
    logger.info("=" * 60)
    logger.info("FAERS HERB-DRUG INTERACTION SIGNAL DETECTION")
    logger.info("=" * 60)

    pipeline = FAERSAnalysisPipeline(
        data_dir=str(data_dir),
        min_cases=args.min_cases,
        top_k_events=args.top_k,
    )

    result = pipeline.run(
        herb_names=herb_names,
        quarters=args.quarters,
        validate=not args.no_validate,
    )

    # Generate report
    report = pipeline.generate_report(result)
    print(report)

    # Save results
    report_path = output_dir / "faers_hdi_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Report saved to: %s", report_path)

    # Save signal table
    signal_df = pipeline.generate_signal_table(result)
    if not signal_df.empty:
        signal_path = output_dir / "signal_results.csv"
        signal_df.to_csv(signal_path, index=False)
        logger.info("Signal table saved to: %s", signal_path)

    # Save validation table
    val_df = pipeline.generate_validation_table(result)
    if not val_df.empty:
        val_path = output_dir / "validation_results.csv"
        val_df.to_csv(val_path, index=False)
        logger.info("Validation table saved to: %s", val_path)

    # Summary statistics
    logger.info("")
    logger.info("ANALYSIS COMPLETE")
    logger.info("-" * 40)
    stats = result.dataset_stats
    logger.info("Reports analyzed: %d", stats["n_reports"])
    logger.info("Herbs analyzed: %d", stats["n_herbs_analyzed"])
    logger.info("Herbs with signals: %d", stats["herbs_with_signals"])
    if result.validation:
        v = result.validation
        logger.info("Validation sensitivity: %.1f%% (%d/%d)",
                     v.sensitivity * 100, v.detected, v.total_controls)
    logger.info("Results saved to: %s", output_dir)


if __name__ == "__main__":
    main()

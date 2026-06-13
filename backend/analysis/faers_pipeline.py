"""FAERS real data analysis pipeline for herb-drug interaction signal detection.

Integrates:
- Real FAERS data loading
- Herb name normalization
- Disproportionality analysis (ROR, PRR, IC, BCPNN)
- MGPS-inspired shrinkage scoring
- Positive control validation
- Manuscript-ready result generation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from ..data.faers_real_loader import FAERSAnalyzer, FAERSDataset, RealFAERSLoader
from ..data.herb_name_normalizer import (
    HERB_PROFILES,
    HerbProfile,
    get_all_herb_patterns,
    get_faers_pattern,
    get_herb_profile,
    get_known_positive_controls,
)
from ..models.disproportionality import DisproportionalityAnalyzer
from ..models.signal_detector import SignalDetector

logger = logging.getLogger(__name__)


@dataclass
class HerbSignalResult:
    """Result for a single herb-event pair."""
    herb: str
    herb_pattern: str
    event: str
    n_reports: int  # reports with herb+event
    contingency: Dict[str, int]
    ror_value: float
    ror_ci_lower: float
    ror_ci_upper: float
    prr_value: float
    prr_ci_lower: float
    prr_ci_upper: float
    ic_value: float
    ic_ci_lower: float
    ic_ci_upper: float
    bcpnn_value: float
    bcpnn_ci_lower: float
    bcpnn_ci_upper: float
    ebgm: float
    eb05: float
    signal_strength: str
    is_signal: bool


@dataclass
class ValidationSummary:
    """Summary of positive control validation."""
    total_controls: int
    detected: int
    missed: int
    sensitivity: float
    false_positives: int
    specificity: float
    details: List[Dict] = field(default_factory=list)


@dataclass
class FAERSAnalysisResult:
    """Complete FAERS analysis result."""
    herb_results: Dict[str, List[HerbSignalResult]]  # herb -> top signals
    validation: Optional[ValidationSummary]
    dataset_stats: Dict
    top_pairs: List[Dict]


class FAERSAnalysisPipeline:
    """Complete pipeline for FAERS herb-drug interaction analysis."""

    def __init__(
        self,
        data_dir: str = "data/faers_ascii",
        min_cases: int = 3,
        top_k_events: int = 20,
    ):
        self.data_dir = data_dir
        self.min_cases = min_cases
        self.top_k_events = top_k_events
        self.analyzer: DisproportionalityAnalyzer = DisproportionalityAnalyzer(min_cases=min_cases)
        self.signal_detector: SignalDetector = SignalDetector(
            ror_threshold=2.0, prr_threshold=2.0, ic_threshold=0.0,
            min_cases=min_cases,
        )

    def run(
        self,
        herb_names: Optional[List[str]] = None,
        quarters: Optional[List[str]] = None,
        validate: bool = True,
    ) -> FAERSAnalysisResult:
        """Run the complete analysis pipeline.

        Args:
            herb_names: List of herb names to analyze (default: all in database)
            quarters: List of FAERS quarters to load (default: all available)
            validate: Whether to run positive control validation
        """
        # 1. Load FAERS data
        logger.info("Loading FAERS data from %s", self.data_dir)
        loader = RealFAERSLoader(self.data_dir)
        if quarters:
            dataset = loader.load_quarters(quarters)
        else:
            dataset = loader.load_all()

        faers = FAERSAnalyzer(dataset)

        # 2. Get herb patterns
        if herb_names is None:
            herb_names = list(HERB_PROFILES.keys())
        herb_patterns = {}
        for name in herb_names:
            pattern = get_faers_pattern(name)
            if pattern:
                herb_patterns[name] = pattern

        logger.info("Analyzing %d herbs against FAERS data", len(herb_patterns))

        # 3. Run signal detection for each herb
        herb_results: Dict[str, List[HerbSignalResult]] = {}
        all_pairs: List[Dict] = []

        for herb_name, pattern in herb_patterns.items():
            profile = get_herb_profile(herb_name)
            herb_display = profile.common_name if profile else herb_name

            logger.info("Analyzing: %s (pattern: %s)", herb_display, pattern)

            # Get report count
            n_reports = faers.get_report_count(pattern)
            logger.info("  Total reports: %d", n_reports)
            if n_reports < self.min_cases:
                logger.info("  Skipping — too few reports")
                continue

            # Get top events
            top_events = faers.get_top_events_for_drug(
                pattern, min_count=self.min_cases
            )
            logger.info("  Top events found: %d", len(top_events))

            results = []
            for ev in top_events[: self.top_k_events]:
                event = ev["event"]
                contingency = faers.build_contingency(pattern, event)

                if contingency["a"] < self.min_cases:
                    continue

                # Run all metrics
                metrics = self.analyzer.analyze_2x2(
                    contingency["a"], contingency["b"],
                    contingency["c"], contingency["d"],
                )
                ror, prr, ic, bcpnn = metrics

                # MGPS-inspired score
                mgps = self.signal_detector._compute_mgps(
                    contingency["a"], contingency["b"],
                    contingency["c"], contingency["d"],
                )
                mgps_class = self.signal_detector.classify_mgps(
                    mgps["ebgm"], mgps["eb05"], contingency["a"]
                )

                # Combined signal strength
                is_signal = ror.is_significant and prr.is_significant
                if is_signal and ror.value > 5 and ic.value > 2:
                    strength = "strong"
                elif is_signal:
                    strength = "moderate"
                elif ror.is_significant or prr.is_significant:
                    strength = "weak"
                else:
                    strength = "none"

                if mgps_class == "disproportionate_strong" and strength in ("moderate", "weak"):
                    strength = "strong"
                elif mgps_class == "disproportionate" and strength == "weak":
                    strength = "moderate"

                result = HerbSignalResult(
                    herb=herb_display,
                    herb_pattern=pattern,
                    event=event,
                    n_reports=contingency["a"],
                    contingency=contingency,
                    ror_value=ror.value,
                    ror_ci_lower=ror.ci_lower,
                    ror_ci_upper=ror.ci_upper,
                    prr_value=prr.value,
                    prr_ci_lower=prr.ci_lower,
                    prr_ci_upper=prr.ci_upper,
                    ic_value=ic.value,
                    ic_ci_lower=ic.ci_lower,
                    ic_ci_upper=ic.ci_upper,
                    bcpnn_value=bcpnn.value,
                    bcpnn_ci_lower=bcpnn.ci_lower,
                    bcpnn_ci_upper=bcpnn.ci_upper,
                    ebgm=mgps["ebgm"],
                    eb05=mgps["eb05"],
                    signal_strength=strength,
                    is_signal=is_signal and strength != "none",
                )
                results.append(result)

                all_pairs.append({
                    "herb": herb_display,
                    "event": event,
                    "n": contingency["a"],
                    "ror": ror.value,
                    "prr": prr.value,
                    "ic": ic.value,
                    "bcpnn": bcpnn.value,
                    "ebgm": mgps["ebgm"],
                    "strength": strength,
                })

            # Sort by signal strength then ROR
            results.sort(key=lambda r: (
                {"strong": 3, "moderate": 2, "weak": 1, "none": 0}[r.signal_strength],
                r.ror_value,
            ), reverse=True)
            herb_results[herb_name] = results

        # 3b. Multiple testing correction (Benjamini-Hochberg FDR)
        # With 16 herbs x 20 events = 320+ comparisons, correction is essential
        n_comparisons = sum(len(r) for r in herb_results.values())
        if n_comparisons > 1:
            p_values = []
            all_results_flat = []
            for herb_name, results in herb_results.items():
                for r in results:
                    p = DisproportionalityAnalyzer.p_value_from_ror(
                        r.ror_value, r.ror_ci_lower, r.ror_ci_upper
                    )
                    p_values.append(p)
                    all_results_flat.append(r)

            fdr_significant = DisproportionalityAnalyzer.apply_fdr_correction(
                p_values, alpha=0.05
            )

            # Update is_signal flags: only keep signals that survive FDR
            for r, is_fdr_sig in zip(all_results_flat, fdr_significant):
                if not is_fdr_sig:
                    r.is_signal = False

            n_signals_after = sum(1 for r in all_results_flat if r.is_signal)
            logger.info(
                "FDR correction applied: %d comparisons, %d signals survive "
                "BH-FDR at alpha=0.05", n_comparisons, n_signals_after
            )

        # 4. Validation (if requested)
        validation = None
        if validate:
            validation = self._run_validation(faers, herb_patterns)

        # 5. Dataset statistics
        dataset_stats = {
            "n_reports": dataset.n_reports,
            "n_drugs": dataset.n_drugs,
            "n_events": dataset.n_events,
            "n_herbs_analyzed": len(herb_results),
            "herbs_with_signals": sum(
                1 for results in herb_results.values()
                if any(r.is_signal for r in results)
            ),
        }

        # 6. Top pairs across all herbs
        all_pairs.sort(key=lambda x: x["ror"], reverse=True)

        return FAERSAnalysisResult(
            herb_results=herb_results,
            validation=validation,
            dataset_stats=dataset_stats,
            top_pairs=all_pairs[:50],
        )

    def _run_validation(
        self,
        faers: FAERSAnalyzer,
        herb_patterns: Dict[str, str],
    ) -> ValidationSummary:
        """Run positive control validation using known HDI pairs."""
        controls = get_known_positive_controls()
        detected = 0
        missed = 0
        details = []
        false_positives = 0

        # Build a set of detected herb-drug signal pairs
        detected_pairs: Set[Tuple[str, str]] = set()

        for ctrl in controls:
            herb_key = ctrl["herb_key"]
            drug = ctrl["drug"]
            pattern = herb_patterns.get(herb_key)
            if not pattern:
                continue

            # Search for the drug as a concurrent medication
            contingency = faers.build_contingency(
                pattern, drug.upper(), role_filter=["PS", "SS", "C"]
            )

            # Use ROR as primary signal metric
            if contingency["a"] >= self.min_cases:
                metrics = self.analyzer.analyze_2x2(
                    contingency["a"], contingency["b"],
                    contingency["c"], contingency["d"],
                )
                ror = metrics[0]
                is_detected = ror.is_significant and ror.value >= 2.0
            else:
                ror = None
                is_detected = False

            if is_detected:
                detected += 1
                detected_pairs.add((herb_key, drug.lower()))
            else:
                missed += 1

            details.append({
                "herb": ctrl["herb"],
                "drug": drug,
                "expected": True,
                "detected": is_detected,
                "n_co_reports": contingency["a"],
                "ror": ror.value if ror else 0,
                "ror_ci": f"[{ror.ci_lower:.2f}, {ror.ci_upper:.2f}]" if ror else "N/A",
            })

        total = detected + missed
        sensitivity = detected / total if total > 0 else 0

        return ValidationSummary(
            total_controls=total,
            detected=detected,
            missed=missed,
            sensitivity=sensitivity,
            false_positives=false_positives,
            specificity=1.0,  # Cannot compute without negative controls
            details=details,
        )

    def generate_report(self, result: FAERSAnalysisResult) -> str:
        """Generate a manuscript-ready text report."""
        lines = []
        lines.append("=" * 70)
        lines.append("FAERS HERB-DRUG INTERACTION SIGNAL DETECTION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Dataset summary
        stats = result.dataset_stats
        lines.append("1. DATASET SUMMARY")
        lines.append("-" * 40)
        lines.append(f"   Total reports:     {stats['n_reports']:,}")
        lines.append(f"   Unique drugs:      {stats['n_drugs']:,}")
        lines.append(f"   Unique events:     {stats['n_events']:,}")
        lines.append(f"   Herbs analyzed:    {stats['n_herbs_analyzed']}")
        lines.append(f"   Herbs with signals: {stats['herbs_with_signals']}")
        lines.append("")

        # Signal summary per herb
        lines.append("2. SIGNAL DETECTION RESULTS")
        lines.append("-" * 40)
        for herb_name, results in result.herb_results.items():
            profile = get_herb_profile(herb_name)
            display = profile.common_name if profile else herb_name
            n_signals = sum(1 for r in results if r.is_signal)
            n_strong = sum(1 for r in results if r.signal_strength == "strong")
            n_moderate = sum(1 for r in results if r.signal_strength == "moderate")
            lines.append(f"   {display}:")
            lines.append(f"     Events analyzed: {len(results)}")
            lines.append(f"     Signals: {n_signals} (strong: {n_strong}, moderate: {n_moderate})")
            if results:
                lines.append(f"     Top 5 events:")
                for r in results[:5]:
                    lines.append(
                        f"       {r.event:40s} ROR={r.ror_value:6.2f} "
                        f"IC={r.ic_value:5.2f} EBGM={r.ebgm:5.2f} "
                        f"n={r.n_reports:4d} [{r.signal_strength}]"
                    )
            lines.append("")

        # Validation
        if result.validation:
            v = result.validation
            lines.append("3. POSITIVE CONTROL VALIDATION")
            lines.append("-" * 40)
            lines.append(f"   Total controls:  {v.total_controls}")
            lines.append(f"   Detected:        {v.detected}")
            lines.append(f"   Missed:          {v.missed}")
            lines.append(f"   Sensitivity:     {v.sensitivity:.1%}")
            lines.append("")
            lines.append("   Detailed results:")
            lines.append(f"   {'Herb':25s} {'Drug':25s} {'N':>5s} {'ROR':>8s} {'Detected':>8s}")
            lines.append("   " + "-" * 75)
            for d in v.details[:20]:
                det_str = "YES" if d["detected"] else "no"
                lines.append(
                    f"   {d['herb']:25s} {d['drug']:25s} "
                    f"{d['n_co_reports']:5d} {d['ror']:8.2f} {det_str:>8s}"
                )
            lines.append("")

        # Top pairs
        lines.append("4. TOP HERB-ADVERSE EVENT PAIRS (by ROR)")
        lines.append("-" * 40)
        lines.append(f"   {'Herb':25s} {'Event':35s} {'N':>5s} {'ROR':>8s} {'IC':>6s} {'EBGM':>6s} {'Strength':>10s}")
        lines.append("   " + "-" * 100)
        for p in result.top_pairs[:30]:
            lines.append(
                f"   {p['herb']:25s} {p['event']:35s} "
                f"{p['n']:5d} {p['ror']:8.2f} {p['ic']:6.2f} "
                f"{p['ebgm']:6.2f} {p['strength']:>10s}"
            )
        lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    def generate_validation_table(self, result: FAERSAnalysisResult) -> pd.DataFrame:
        """Generate a validation results table as DataFrame."""
        if not result.validation:
            return pd.DataFrame()
        return pd.DataFrame(result.validation.details)

    def generate_signal_table(self, result: FAERSAnalysisResult) -> pd.DataFrame:
        """Generate a signal detection results table as DataFrame."""
        rows = []
        for herb_name, signals in result.herb_results.items():
            for s in signals:
                rows.append({
                    "herb": s.herb,
                    "event": s.event,
                    "n_reports": s.n_reports,
                    "ROR": s.ror_value,
                    "ROR_lower": s.ror_ci_lower,
                    "ROR_upper": s.ror_ci_upper,
                    "PRR": s.prr_value,
                    "IC": s.ic_value,
                    "BCPNN": s.bcpnn_value,
                    "EBGM": s.ebgm,
                    "EB05": s.eb05,
                    "signal_strength": s.signal_strength,
                    "is_signal": s.is_signal,
                })
        return pd.DataFrame(rows)

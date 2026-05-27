"""Real FAERS ASCII data loader and processor.

Handles the FDA FAERS quarterly ASCII data files:
  DEMO, DRUG, REAC, OUTC, INDI, THER, RPSR

These are pipe-delimited ('$') text files published quarterly by the FDA.
Reference: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
"""
from __future__ import annotations

import csv
import glob
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# FAERS file name patterns (varies across quarters)
_FILE_PATTERNS = {
    "demo": ["DEMO*.txt", "demo*.txt", "LG*.txt"],
    "drug": ["DRUG*.txt", "drug*.txt", "LR*.txt"],
    "reac": ["REAC*.txt", "reac*.txt", "LL*.txt"],
    "outc": ["OUTC*.txt", "outc*.txt", "LO*.txt"],
    "indi": ["INDI*.txt", "indi*.txt", "LI*.txt"],
    "ther": ["THER*.txt", "ther*.txt", "LT*.txt"],
}


def _find_file(data_dir: Path, table: str) -> Optional[Path]:
    """Find the FAERS file for a given table in a directory."""
    for pattern in _FILE_PATTERNS.get(table, []):
        matches = sorted(data_dir.glob(pattern))
        if matches:
            return matches[-1]  # latest if multiple
    return None


def _read_faers_file(path: Path, encoding: str = "latin-1") -> pd.DataFrame:
    """Read a pipe-delimited FAERS file into a DataFrame.

    FAERS files use '$' as delimiter and have a header row.
    Some quarters use different encodings; latin-1 is safest.
    """
    try:
        df = pd.read_csv(
            path,
            sep="$",
            encoding=encoding,
            dtype=str,
            on_bad_lines="skip",
            low_memory=False,
        )
    except Exception:
        # Fallback: try tab-delimited
        df = pd.read_csv(
            path,
            sep="\t",
            encoding=encoding,
            dtype=str,
            on_bad_lines="skip",
            low_memory=False,
        )
    # Normalize column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]
    return df


@dataclass
class FAERSDataset:
    """Processed FAERS dataset with joined tables."""
    demo: pd.DataFrame
    drug: pd.DataFrame
    reac: pd.DataFrame
    outc: Optional[pd.DataFrame] = None
    indi: Optional[pd.DataFrame] = None
    ther: Optional[pd.DataFrame] = None
    n_reports: int = 0
    n_drugs: int = 0
    n_events: int = 0


class RealFAERSLoader:
    """Load and process real FAERS quarterly ASCII files.

    Usage:
        loader = RealFAERSLoader("data/faers_ascii")
        dataset = loader.load_quarters(["2023Q1", "2023Q2"])
        # or load all available quarters
        dataset = loader.load_all()
    """

    def __init__(self, data_dir: str = "data/faers_ascii"):
        self.data_dir = Path(data_dir)
        self._raw_tables: Dict[str, pd.DataFrame] = {}

    def list_quarters(self) -> List[str]:
        """List available quarter directories."""
        quarters = []
        for d in sorted(self.data_dir.iterdir()):
            if d.is_dir() and d.name.upper().startswith(("20", "19")):
                quarters.append(d.name)
        return quarters

    def _load_table(self, quarter_dir: Path, table: str) -> Optional[pd.DataFrame]:
        """Load a single table from a quarter directory."""
        path = _find_file(quarter_dir, table)
        if path is None:
            logger.warning("No %s file found in %s", table, quarter_dir)
            return None
        logger.info("Loading %s from %s", table, path.name)
        return _read_faers_file(path)

    def load_quarter(self, quarter: str) -> Dict[str, pd.DataFrame]:
        """Load all tables from a single quarter."""
        quarter_dir = self.data_dir / quarter
        if not quarter_dir.exists():
            raise FileNotFoundError(f"Quarter directory not found: {quarter_dir}")

        tables = {}
        for table in ("demo", "drug", "reac", "outc", "indi", "ther"):
            df = self._load_table(quarter_dir, table)
            if df is not None:
                tables[table] = df
        return tables

    def load_quarters(self, quarters: List[str]) -> FAERSDataset:
        """Load and merge multiple quarters."""
        all_demo, all_drug, all_reac = [], [], []
        all_outc, all_indi, all_ther = [], [], []

        for q in quarters:
            logger.info("Loading quarter: %s", q)
            tables = self.load_quarter(q)
            if "demo" in tables:
                all_demo.append(tables["demo"])
            if "drug" in tables:
                all_drug.append(tables["drug"])
            if "reac" in tables:
                all_reac.append(tables["reac"])
            if "outc" in tables:
                all_outc.append(tables["outc"])
            if "indi" in tables:
                all_indi.append(tables["indi"])
            if "ther" in tables:
                all_ther.append(tables["ther"])

        demo = pd.concat(all_demo, ignore_index=True) if all_demo else pd.DataFrame()
        drug = pd.concat(all_drug, ignore_index=True) if all_drug else pd.DataFrame()
        reac = pd.concat(all_reac, ignore_index=True) if all_reac else pd.DataFrame()
        outc = pd.concat(all_outc, ignore_index=True) if all_outc else None
        indi = pd.concat(all_indi, ignore_index=True) if all_indi else None
        ther = pd.concat(all_ther, ignore_index=True) if all_ther else None

        return self._build_dataset(demo, drug, reac, outc, indi, ther)

    def load_all(self) -> FAERSDataset:
        """Load all available quarters."""
        quarters = self.list_quarters()
        if not quarters:
            raise FileNotFoundError(f"No quarter directories found in {self.data_dir}")
        return self.load_quarters(quarters)

    def _build_dataset(
        self,
        demo: pd.DataFrame,
        drug: pd.DataFrame,
        reac: pd.DataFrame,
        outc: Optional[pd.DataFrame],
        indi: Optional[pd.DataFrame],
        ther: Optional[pd.DataFrame],
    ) -> FAERSDataset:
        """Clean and build the merged dataset."""

        # --- DEMO: deduplicate by caseid, keep latest primaryid ---
        if not demo.empty and "caseid" in demo.columns:
            if "primaryid" in demo.columns:
                demo = demo.sort_values("primaryid").drop_duplicates(
                    subset=["caseid"], keep="last"
                )

        # --- DRUG: standardize columns ---
        if not drug.empty:
            drug.columns = [c.strip().lower() for c in drug.columns]
            # Standard column mapping
            col_map = {
                "drugname": "drugname",
                "drug_seq": "drug_seq",
                "role_cod": "role_cod",
                "primaryid": "primaryid",
                "caseid": "caseid",
            }
            for old, new in col_map.items():
                if old in drug.columns and old != new:
                    drug = drug.rename(columns={old: new})

        # --- REAC: standardize columns ---
        if not reac.empty:
            reac.columns = [c.strip().lower() for c in reac.columns]

        n_reports = len(demo) if not demo.empty else 0
        n_drugs = drug["drugname"].nunique() if not drug.empty and "drugname" in drug.columns else 0
        n_events = reac["pt"].nunique() if not reac.empty and "pt" in reac.columns else 0

        logger.info(
            "Dataset built: %d reports, %d unique drugs, %d unique events",
            n_reports, n_drugs, n_events,
        )

        return FAERSDataset(
            demo=demo, drug=drug, reac=reac,
            outc=outc, indi=indi, ther=ther,
            n_reports=n_reports, n_drugs=n_drugs, n_events=n_events,
        )


class FAERSAnalyzer:
    """Build contingency tables and run analyses on FAERS data."""

    def __init__(self, dataset: FAERSDataset):
        self.dataset = dataset
        self._merged: Optional[pd.DataFrame] = None

    def _get_merged(self) -> pd.DataFrame:
        """Merge DRUG and REAC tables on primaryid."""
        if self._merged is not None:
            return self._merged

        drug = self.dataset.drug
        reac = self.dataset.reac

        if drug.empty or reac.empty:
            return pd.DataFrame()

        # Merge on primaryid
        merged = drug.merge(reac, on="primaryid", how="inner", suffixes=("_drug", "_reac"))

        # Clean drug names
        if "drugname" in merged.columns:
            merged["drugname"] = merged["drugname"].str.strip().str.upper()
        if "pt" in merged.columns:
            merged["pt"] = merged["pt"].str.strip().str.upper()

        self._merged = merged
        return merged

    def filter_suspected_drugs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to suspected (PS) and concomitant (SS) drug roles.

        FAERS role codes:
          PS = Primary Suspect Drug
          SS = Secondary Suspect Drug
          C  = Concomitant
          I  = Interacting
        """
        if "role_cod" not in df.columns:
            return df
        # Keep PS (primary suspect) and SS (secondary suspect)
        return df[df["role_cod"].isin(["PS", "SS"])].copy()

    def build_contingency(
        self,
        drug_pattern: str,
        event: str,
        role_filter: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Build a 2x2 contingency table for a drug-event pair.

        Args:
            drug_pattern: Regex pattern to match drug names (case-insensitive)
            event: Event preferred term (exact match, case-insensitive)
            role_filter: List of role codes to include (default: PS, SS)
        """
        merged = self._get_merged()
        if merged.empty:
            return {"a": 0, "b": 0, "c": 0, "d": 0, "n": 0}

        # Filter by role
        if role_filter is None:
            role_filter = ["PS", "SS"]
        if "role_cod" in merged.columns:
            merged = merged[merged["role_cod"].isin(role_filter)]

        drug_mask = merged["drugname"].str.contains(drug_pattern, case=False, na=False)
        event_mask = merged["pt"].str.upper() == event.upper()

        # Count unique reports (primaryid) for each category
        all_ids = set(merged["primaryid"].unique())
        drug_ids = set(merged[drug_mask]["primaryid"].unique())
        event_ids = set(merged[event_mask]["primaryid"].unique())

        a = len(drug_ids & event_ids)       # drug + event
        b = len(drug_ids - event_ids)       # drug + not event
        c = len(event_ids - drug_ids)       # not drug + event
        d = len(all_ids - drug_ids - event_ids)  # not drug + not event
        n = len(all_ids)

        return {"a": a, "b": b, "c": c, "d": d, "n": n}

    def get_top_events_for_drug(
        self,
        drug_pattern: str,
        min_count: int = 3,
        role_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Get top adverse events reported for a drug."""
        merged = self._get_merged()
        if merged.empty:
            return []

        if role_filter is None:
            role_filter = ["PS", "SS"]
        if "role_cod" in merged.columns:
            merged = merged[merged["role_cod"].isin(role_filter)]

        drug_mask = merged["drugname"].str.contains(drug_pattern, case=False, na=False)
        drug_events = merged[drug_mask]

        if drug_events.empty:
            return []

        event_counts = (
            drug_events.groupby("pt")["primaryid"]
            .nunique()
            .reset_index(name="n_reports")
            .sort_values("n_reports", ascending=False)
        )

        results = []
        for _, row in event_counts.iterrows():
            if row["n_reports"] >= min_count:
                results.append({
                    "event": row["pt"],
                    "n_reports": int(row["n_reports"]),
                })

        return results

    def get_report_count(self, drug_pattern: str) -> int:
        """Get total number of reports mentioning a drug."""
        merged = self._get_merged()
        if merged.empty:
            return 0
        drug_mask = merged["drugname"].str.contains(drug_pattern, case=False, na=False)
        return merged[drug_mask]["primaryid"].nunique()

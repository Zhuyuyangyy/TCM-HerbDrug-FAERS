"""FAERS data loader and processor with MedDRA preferred term mapping."""
import csv
import json
from typing import List, Dict, Optional, Set
from pathlib import Path

class FAERSLoader:
    """FDA FAERS数据库加载器"""
    REQUIRED_COLS = ["primaryid", "caseid", "drugname", "pt", "role_cod"]

    # Default MedDRA preferred term (PT) to standardized term mapping
    # Maps common synonym / variant spellings to the canonical MedDRA PT.
    DEFAULT_MEDDRA_MAP: Dict[str, str] = {
        # Bleeding events
        "haemorrhage": "hemorrhage",
        "haemorragic": "hemorrhagic",
        "bleeding nos": "hemorrhage",
        "gi bleeding": "GI_hemorrhage",
        "gi haemorrhage": "GI_hemorrhage",
        # Liver events
        "hepatic failure": "hepatotoxicity",
        "hepatocellular injury": "hepatotoxicity",
        "liver injury": "hepatotoxicity",
        "drug-induced liver injury": "hepatotoxicity",
        "dili": "hepatotoxicity",
        # Cardiac
        "arrhythmia": "cardiac_arrhythmia",
        "cardiac arrhythmia nos": "cardiac_arrhythmia",
        "tachyarrhythmia": "cardiac_arrhythmia",
        "atrial fibrillation": "cardiac_arrhythmia",
        "ventricular tachycardia": "cardiac_arrhythmia",
        "qt prolongation": "cardiac_arrhythmia",
        # Renal
        "renal failure": "renal_impairment",
        "acute kidney injury": "renal_impairment",
        "nephrotoxicity": "renal_impairment",
        "aki": "renal_impairment",
        # Musculoskeletal
        "rhabdomyolysis": "myopathy",
        "myalgia": "myopathy",
        "myositis": "myopathy",
        # Lab abnormalities
        "inr increased": "elevated_INR",
        "international normalised ratio increased": "elevated_INR",
        "inr abnormal": "elevated_INR",
        "prothrombin time prolonged": "elevated_INR",
        # Electrolytes
        "hypokalaemia": "hypokalemia",
        "blood potassium decreased": "hypokalemia",
        # Hematology
        "thrombocytopaenia": "thrombocytopenia",
        "platelet count decreased": "thrombocytopenia",
        # General
        "feeling dizzy": "dizziness",
        "vertigo": "dizziness",
        "nauseous": "nausea",
        "vomiting": "nausea",
    }

    def __init__(self, data_dir: str = "data",
                 meddra_map: Optional[Dict[str, str]] = None):
        self.data_dir = Path(data_dir)
        self.records: List[Dict] = []
        self.meddra_map: Dict[str, str] = meddra_map or dict(self.DEFAULT_MEDDRA_MAP)
        # Cache of original -> mapped PT values
        self._pt_cache: Dict[str, str] = {}
        # Set of all unique mapped preferred terms
        self._mapped_pts: Set[str] = set()

    def load_meddra_map(self, filepath: str) -> None:
        """Load a MedDRA PT mapping file (JSON or CSV).

        JSON format: { "synonym": "preferred_term", ... }
        CSV format:  columns: synonym, preferred_term
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"MedDRA mapping file not found: {filepath}")

        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                extra = json.load(f)
            self.meddra_map.update({k.lower(): v for k, v in extra.items()})
        elif path.suffix.lower() == ".csv":
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    syn = row.get("synonym", "").strip().lower()
                    pt = row.get("preferred_term", "").strip()
                    if syn and pt:
                        self.meddra_map[syn] = pt
        else:
            raise ValueError(f"Unsupported mapping format: {path.suffix}")

    def map_pt(self, raw_pt: str) -> str:
        """Map a raw event term to a MedDRA preferred term.

        Applies case-insensitive lookup against the loaded mapping dictionary.
        Returns the canonical PT or the original term if no mapping exists.
        """
        if not raw_pt:
            return raw_pt
        # Check cache first
        if raw_pt in self._pt_cache:
            return self._pt_cache[raw_pt]
        # Normalized lookup
        normalized = raw_pt.strip().lower()
        mapped = self.meddra_map.get(normalized, raw_pt)
        self._pt_cache[raw_pt] = mapped
        self._mapped_pts.add(mapped)
        return mapped

    def get_mapped_pts(self) -> Set[str]:
        """Return the set of all unique mapped preferred terms seen so far."""
        return set(self._mapped_pts)

    def load_csv(self, filepath: str, apply_meddra: bool = True) -> List[Dict]:
        records = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if apply_meddra and "pt" in row:
                    row["pt_original"] = row["pt"]
                    row["pt"] = self.map_pt(row["pt"])
                records.append(row)
        self.records.extend(records)
        return records

    def load_from_dataframe(self, df, apply_meddra: bool = True) -> List[Dict]:
        records = df.to_dict("records")
        if apply_meddra:
            for rec in records:
                if "pt" in rec:
                    rec["pt_original"] = rec["pt"]
                    rec["pt"] = self.map_pt(rec["pt"])
        self.records = records
        return self.records

    def build_contingency(self, drug: str, event: str) -> Dict[str, int]:
        a = b = c = d = 0
        drug_upper = drug.upper()
        event_upper = event.upper()
        all_drugs = set()
        all_events = set()
        for rec in self.records:
            dname = rec.get("drugname", "").upper()
            pt = rec.get("pt", "").upper()
            all_drugs.add(dname)
            all_events.add(pt)
            if dname == drug_upper and pt == event_upper:
                a += 1
            elif dname == drug_upper and pt != event_upper:
                b += 1
            elif dname != drug_upper and pt == event_upper:
                c += 1
        n = len(self.records)
        d = max(0, n - a - b - c)
        return {"a": a, "b": b, "c": c, "d": d, "n": n}

    def get_drug_event_pairs(self, min_count: int = 1) -> List[Dict]:
        pairs = {}
        for rec in self.records:
            key = (rec.get("drugname", ""), rec.get("pt", ""))
            pairs[key] = pairs.get(key, 0) + 1
        return [{"drug": k[0], "event": k[1], "count": v} for k, v in pairs.items() if v >= min_count]

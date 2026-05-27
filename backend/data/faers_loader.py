"""FAERS data loader and processor."""
import csv
from typing import List, Dict, Optional
from pathlib import Path

class FAERSLoader:
    """FDA FAERS数据库加载器"""
    REQUIRED_COLS = ["primaryid", "caseid", "drugname", "pt", "role_cod"]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.records: List[Dict] = []

    def load_csv(self, filepath: str) -> List[Dict]:
        records = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        self.records.extend(records)
        return records

    def load_from_dataframe(self, df) -> List[Dict]:
        self.records = df.to_dict("records")
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
        n = a + b + c + d
        d = max(0, n - a - b - c)
        return {"a": a, "b": b, "c": c, "d": d, "n": a+b+c+d}

    def get_drug_event_pairs(self, min_count: int = 1) -> List[Dict]:
        pairs = {}
        for rec in self.records:
            key = (rec.get("drugname", ""), rec.get("pt", ""))
            pairs[key] = pairs.get(key, 0) + 1
        return [{"drug": k[0], "event": k[1], "count": v} for k, v in pairs.items() if v >= min_count]

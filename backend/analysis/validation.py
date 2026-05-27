"""External validation against known HDI databases."""
from typing import List, Dict, Set

class ExternalValidator:
    """外部验证器 — 交叉验证FAERS信号与已知HDI数据库"""

    KNOWN_HDI = {
        ("warfarin", "丹参"): {"source": "EMA/FDA", "severity": "major", "evidence": "case_report"},
        ("warfarin", "当归"): {"source": "literature", "severity": "moderate", "evidence": "case_report"},
        ("digoxin", "甘草"): {"source": "EMA", "severity": "major", "evidence": "pharmacokinetic"},
        ("clopidogrel", "丹参"): {"source": "literature", "severity": "moderate", "evidence": "in_vitro"},
        ("simvastatin", "红曲"): {"source": "FDA", "severity": "major", "evidence": "pharmacokinetic"},
        ("metformin", "黄连"): {"source": "literature", "severity": "minor", "evidence": "case_series"},
        ("cyclosporine", "圣约翰草"): {"source": "FDA", "severity": "major", "evidence": "clinical_trial"},
    }

    def validate(self, drug: str, herb: str) -> Optional[Dict]:
        key = (drug.lower(), herb)
        if key in self.KNOWN_HDI:
            return {**self.KNOWN_HDI[key], "validated": True}
        for (d, h), info in self.KNOWN_HDI.items():
            if d in drug.lower() or h in herb:
                return {**info, "validated": True, "note": "partial_match"}
        return {"validated": False}

    def batch_validate(self, pairs: List[Dict]) -> List[Dict]:
        results = []
        for pair in pairs:
            v = self.validate(pair["drug"], pair["herb"])
            results.append({**pair, **v})
        return results

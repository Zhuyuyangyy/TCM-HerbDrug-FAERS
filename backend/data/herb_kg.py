"""Herb knowledge graph interface."""
import yaml
from typing import List, Dict, Optional
from pathlib import Path

class HerbKnowledgeGraph:
    """中药知识图谱接口 — HERB 2.0 / BATMAN-TCM 2.0 风格"""

    def __init__(self, data_path: Optional[str] = None):
        self.herbs: Dict[str, Dict] = {}
        self.ingredients: Dict[str, Dict] = {}
        self.herb_ingredients: Dict[str, List[str]] = {}
        self._load_defaults()
        if data_path:
            self.load_from_yaml(data_path)

    def _load_defaults(self):
        defaults = {
            "丹参": {"latin": "Salviae Miltiorrhizae", "pinyin": "Danshen",
                     "ingredients": ["tanshinone_IIA", "salvianolic_acid_B", "cryptotanshinone"],
                     "cyp_inhibition": {"CYP2C9": 0.9, "CYP3A4": 0.7}},
            "甘草": {"latin": "Glycyrrhizae Radix", "pinyin": "Gancao",
                     "ingredients": ["glycyrrhizin", "liquiritin", "isoliquiritigenin"],
                     "cyp_inhibition": {"CYP2B6": 0.5, "CYP3A4": 0.6}},
            "当归": {"latin": "Angelicae Sinensis", "pinyin": "Danggui",
                     "ingredients": ["ferulic_acid", "ligustilide", "angelica_polysaccharide"],
                     "cyp_inhibition": {"CYP2C19": 0.6, "CYP2D6": 0.4}},
            "黄芩": {"latin": "Scutellariae Radix", "pinyin": "Huangqin",
                     "ingredients": ["baicalin", "wogonin", "baicalein"],
                     "cyp_inhibition": {"CYP2C9": 0.7, "CYP1A2": 0.8}},
            "大黄": {"latin": "Rhei Radix", "pinyin": "Dahuang",
                     "ingredients": ["emodin", "rhein", "sennoside_A"],
                     "cyp_inhibition": {"CYP3A4": 0.8, "CYP2C9": 0.5}},
        }
        for name, info in defaults.items():
            self.herbs[name] = info
            self.herb_ingredients[name] = info["ingredients"]
            for ing in info["ingredients"]:
                self.ingredients[ing] = {"herb_source": name}

    def load_from_yaml(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "herbs" in data:
            for h in data["herbs"]:
                self.herbs[h["name"]] = h

    def get_cyp_inhibitors(self, herb: str) -> Dict[str, float]:
        h = self.herbs.get(herb, {})
        return h.get("cyp_inhibition", {})

    def get_herbs_inhibiting_cyp(self, cyp: str) -> List[str]:
        result = []
        for name, info in self.herbs.items():
            cyp_data = info.get("cyp_inhibition", {})
            if cyp in cyp_data and cyp_data[cyp] > 0.5:
                result.append(name)
        return result

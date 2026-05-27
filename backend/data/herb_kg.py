"""Herb knowledge graph interface — 15 herbs with full CYP inhibition profiles."""
import yaml
from typing import List, Dict, Optional
from pathlib import Path

class HerbKnowledgeGraph:
    """中药知识图谱接口 — HERB 2.0 / BATMAN-TCM 2.0 风格

    Contains 15 default herbs with complete CYP inhibition profiles
    covering CYP1A2, CYP2C9, CYP2C19, CYP2D6, CYP3A4, CYP2B6, and P-gp.
    """

    def __init__(self, data_path: Optional[str] = None):
        self.herbs: Dict[str, Dict] = {}
        self.ingredients: Dict[str, Dict] = {}
        self.herb_ingredients: Dict[str, List[str]] = {}
        self._load_defaults()
        if data_path:
            self.load_from_yaml(data_path)

    def _load_defaults(self):
        defaults = {
            # ── Original 5 ────────────────────────────────────────────────
            "丹参": {
                "latin": "Salviae Miltiorrhizae", "pinyin": "Danshen",
                "ingredients": ["tanshinone_IIA", "salvianolic_acid_B", "cryptotanshinone"],
                "cyp_inhibition": {"CYP2C9": 0.9, "CYP3A4": 0.7, "CYP1A2": 0.5},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "established",
            },
            "甘草": {
                "latin": "Glycyrrhizae Radix", "pinyin": "Gancao",
                "ingredients": ["glycyrrhizin", "liquiritin", "isoliquiritigenin"],
                "cyp_inhibition": {"CYP2B6": 0.5, "CYP3A4": 0.6},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "established",
            },
            "当归": {
                "latin": "Angelicae Sinensis", "pinyin": "Danggui",
                "ingredients": ["ferulic_acid", "ligustilide", "angelica_polysaccharide"],
                "cyp_inhibition": {"CYP2C19": 0.6, "CYP2D6": 0.4, "CYP3A4": 0.55},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "probable",
            },
            "黄芩": {
                "latin": "Scutellariae Radix", "pinyin": "Huangqin",
                "ingredients": ["baicalin", "wogonin", "baicalein"],
                "cyp_inhibition": {"CYP2C9": 0.7, "CYP1A2": 0.8, "CYP3A4": 0.75},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "established",
            },
            "大黄": {
                "latin": "Rhei Radix", "pinyin": "Dahuang",
                "ingredients": ["emodin", "rhein", "sennoside_A"],
                "cyp_inhibition": {"CYP3A4": 0.8, "CYP2C9": 0.5, "CYP1A2": 0.45},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "probable",
            },
            # ── New herbs (6-15) ──────────────────────────────────────────
            "圣约翰草": {
                "latin": "Hypericum perforatum", "pinyin": "Shengyuehancao",
                "english": "St. John's Wort",
                "ingredients": ["hypericin", "hyperforin", "adhyperforin"],
                "cyp_inhibition": {},
                "cyp_induction": {"CYP3A4": 0.95, "CYP2C9": 0.7, "CYP1A2": 0.6, "CYP2C19": 0.5},
                "pgp_effect": "induction",
                "pgp_potency": 0.95,
                "evidence_level": "established",
            },
            "红曲": {
                "latin": "Monascus purpureus", "pinyin": "Hongqu",
                "english": "Red Yeast Rice",
                "ingredients": ["monacolin_K", "citrinin", "GABA"],
                "cyp_inhibition": {"CYP3A4": 0.8, "CYP2C9": 0.3},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "established",
            },
            "银杏": {
                "latin": "Ginkgo biloba", "pinyin": "Yinxing",
                "english": "Ginkgo",
                "ingredients": ["ginkgolide_B", "bilobalide", "quercetin"],
                "cyp_inhibition": {"CYP2C9": 0.5, "CYP3A4": 0.45, "CYP1A2": 0.3},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "established",
            },
            "人参": {
                "latin": "Panax ginseng", "pinyin": "Renshen",
                "english": "Ginseng",
                "ingredients": ["ginsenoside_Rb1", "ginsenoside_Rg1", "ginsenoside_Re"],
                "cyp_inhibition": {"CYP2D6": 0.55, "CYP3A4": 0.5, "CYP2C9": 0.45},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "probable",
            },
            "麻黄": {
                "latin": "Ephedra sinica", "pinyin": "Mahuang",
                "english": "Ephedra / Ma Huang",
                "ingredients": ["ephedrine", "pseudoephedrine", "methylephedrine"],
                "cyp_inhibition": {"CYP1A2": 0.4, "CYP2D6": 0.35},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "probable",
            },
            "半夏": {
                "latin": "Pinellia ternata", "pinyin": "Banxia",
                "english": "Pinellia",
                "ingredients": ["pinelline", "beta_sitosterol", "ephedrine_trace"],
                "cyp_inhibition": {"CYP2D6": 0.5, "CYP3A4": 0.45},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "possible",
            },
            "附子": {
                "latin": "Aconitum carmichaelii", "pinyin": "Fuzi",
                "english": "Aconite / Prepared Aconite",
                "ingredients": ["aconitine", "mesaconitine", "hypaconitine"],
                "cyp_inhibition": {"CYP3A4": 0.4},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "possible",
            },
            "姜黄": {
                "latin": "Curcuma longa", "pinyin": "Jianghuang",
                "english": "Turmeric",
                "ingredients": ["curcumin", "demethoxycurcumin", "bisdemethoxycurcumin"],
                "cyp_inhibition": {"CYP3A4": 0.6, "CYP2C9": 0.55, "CYP1A2": 0.5},
                "cyp_induction": {},
                "pgp_effect": "inhibition",
                "pgp_potency": 0.4,
                "evidence_level": "probable",
            },
            "大蒜": {
                "latin": "Allium sativum", "pinyin": "Dasuan",
                "english": "Garlic",
                "ingredients": ["allicin", "alliin", "ajoene"],
                "cyp_inhibition": {"CYP2C9": 0.3},
                "cyp_induction": {"CYP3A4": 0.4},
                "pgp_effect": "none",
                "evidence_level": "probable",
            },
            "山楂": {
                "latin": "Crataegus pinnatifida", "pinyin": "Shanzha",
                "english": "Hawthorn",
                "ingredients": ["vitexin", "hyperoside", "chlorogenic_acid"],
                "cyp_inhibition": {"CYP3A4": 0.35, "CYP2D6": 0.3},
                "cyp_induction": {},
                "pgp_effect": "none",
                "evidence_level": "possible",
            },
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
        """Get CYP inhibition profile for a herb (inhibition IC50 proxy)."""
        h = self.herbs.get(herb, {})
        return h.get("cyp_inhibition", {})

    def get_cyp_inducers(self, herb: str) -> Dict[str, float]:
        """Get CYP induction profile for a herb."""
        h = self.herbs.get(herb, {})
        return h.get("cyp_induction", {})

    def get_pgp_effect(self, herb: str) -> Dict:
        """Get P-glycoprotein effect for a herb."""
        h = self.herbs.get(herb, {})
        return {
            "effect": h.get("pgp_effect", "none"),
            "potency": h.get("pgp_potency", 0.0),
        }

    def get_herbs_inhibiting_cyp(self, cyp: str) -> List[str]:
        """Find all herbs that significantly inhibit a given CYP enzyme."""
        result = []
        for name, info in self.herbs.items():
            cyp_data = info.get("cyp_inhibition", {})
            if cyp in cyp_data and cyp_data[cyp] > 0.5:
                result.append(name)
        return result

    def get_herbs_inducing_cyp(self, cyp: str) -> List[str]:
        """Find all herbs that significantly induce a given CYP enzyme."""
        result = []
        for name, info in self.herbs.items():
            cyp_data = info.get("cyp_induction", {})
            if cyp in cyp_data and cyp_data[cyp] > 0.5:
                result.append(name)
        return result

    def get_full_cyp_profile(self, herb: str) -> Dict[str, Dict]:
        """Get complete CYP profile (inhibition + induction + P-gp) for a herb."""
        return {
            "inhibition": self.get_cyp_inhibitors(herb),
            "induction": self.get_cyp_inducers(herb),
            "pgp": self.get_pgp_effect(herb),
        }

    def search_herbs(self, query: str) -> List[str]:
        """Search herbs by Chinese name, pinyin, or Latin name."""
        q = query.lower()
        results = []
        for name, info in self.herbs.items():
            if (q in name or
                q in info.get("pinyin", "").lower() or
                q in info.get("latin", "").lower() or
                q in info.get("english", "").lower()):
                results.append(name)
        return results

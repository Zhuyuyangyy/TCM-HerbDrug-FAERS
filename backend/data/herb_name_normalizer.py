"""Herb drug name normalization for FAERS data.

Maps TCM herb names (English common names, Latin names, pinyin) to
FAERS drug name search patterns. These patterns are used as regex to
match drug names in the FAERS DRUG table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class HerbProfile:
    """Profile for a single herb with all its name variants."""
    common_name: str
    latin_name: str = ""
    pinyin: str = ""
    faers_patterns: List[str] = field(default_factory=list)
    description: str = ""
    # Known concurrent drugs of concern
    known_interactions: List[str] = field(default_factory=list)


# Comprehensive herb profiles for FAERS matching
# Each entry maps herb common name to its search patterns in FAERS
HERB_PROFILES: Dict[str, HerbProfile] = {
    "ginkgo": HerbProfile(
        common_name="Ginkgo biloba",
        latin_name="Ginkgo biloba L.",
        pinyin="银杏",
        faers_patterns=[
            r"GINKGO",
            r"GINKGO BILOBA",
            r"EGb 761",
            r"GINKGOFLAVONE",
        ],
        description="Ginkgo leaf extract; antiplatelet, neuroprotective",
        known_interactions=["warfarin", "aspirin", "clopidogrel", "ibuprofen",
                            "naproxen", "ticlopidine", "cilostazol"],
    ),
    "ginseng": HerbProfile(
        common_name="Panax ginseng",
        latin_name="Panax ginseng C.A. Mey.",
        pinyin="人参",
        faers_patterns=[
            r"\bGINSENG\b",
            r"PANAX",
            r"PANAX GINSENG",
            r"GINSENG EXTRACT",
            r"RED GINSENG",
            r"AMERICAN GINSENG",
        ],
        description="Ginseng root; adaptogenic, immunomodulatory",
        known_interactions=["warfarin", "insulin", "metformin", "phenelzine",
                            "imipramine", "caffeine"],
    ),
    "st_johns_wort": HerbProfile(
        common_name="St. John's wort",
        latin_name="Hypericum perforatum",
        pinyin="贯叶连翘",
        faers_patterns=[
            r"ST\.?\s*JOHN",
            r"HYPERICUM",
            r"ST JOHNS WORT",
            r"ST JOHN'S WORT",
            r"HYPERICIN",
        ],
        description="Antidepressant herb; potent CYP3A4/P-gp inducer",
        known_interactions=["warfarin", "cyclosporine", "tacrolimus",
                            "digoxin", "oral contraceptives", "SSRIs",
                            "HIV protease inhibitors", "irinotecan"],
    ),
    "danshen": HerbProfile(
        common_name="Danshen",
        latin_name="Salvia miltiorrhiza",
        pinyin="丹参",
        faers_patterns=[
            r"DANSHEN",
            r"SALVIA MILTI",
            r"SALVIA MILTIORRHIZA",
            r"TANSHINONE",
            r"SALVIANOLIC",
            r"RED SAGE",
        ],
        description="Danshen root; cardiovascular, antiplatelet",
        known_interactions=["warfarin", "digoxin", "theophylline",
                            "clopidogrel", "aspirin"],
    ),
    "licorice": HerbProfile(
        common_name="Licorice",
        latin_name="Glycyrrhiza glabra",
        pinyin="甘草",
        faers_patterns=[
            r"\bLICORICE\b",
            r"\bLIQUORICE\b",
            r"GLYCYRRHIZ",
            r"GLYCYRRHETINIC",
        ],
        description="Licorice root; anti-inflammatory, mineralocorticoid effects",
        known_interactions=["warfarin", "digoxin", "furosemide",
                            "hydrochlorothiazide", "prednisolone",
                            "insulin", "corticosteroids"],
    ),
    "ma_huang": HerbProfile(
        common_name="Ma Huang (Ephedra)",
        latin_name="Ephedra sinica",
        pinyin="麻黄",
        faers_patterns=[
            r"\bEPHEDRA\b",
            r"\bMA HUANG\b",
            r"\bEPHEDRINE\b",
            r"EPHEDRA SINICA",
            r"\bEPHEDRINE\b",
        ],
        description="Ephedra herb; sympathomimetic, banned in US supplements",
        known_interactions=["MAO inhibitors", "theophylline", "caffeine",
                            "pseudoephedrine", "phenylephrine",
                            "antihypertensives"],
    ),
    "dong_quai": HerbProfile(
        common_name="Dong Quai",
        latin_name="Angelica sinensis",
        pinyin="当归",
        faers_patterns=[
            r"DONG QUAI",
            r"ANGELICA SINENSIS",
            r"\bDANGGUI\b",
            r"\bDANG GUI\b",
        ],
        description="Female tonic; anticoagulant potential",
        known_interactions=["warfarin", "oral contraceptives",
                            "estrogen", "anticoagulants"],
    ),
    "garlic": HerbProfile(
        common_name="Garlic",
        latin_name="Allium sativum",
        pinyin="大蒜",
        faers_patterns=[
            r"\bGARLIC\b",
            r"ALLIUM SATIVUM",
            r"GARLIC EXTRACT",
            r"GARLIC OIL",
            r"ALLICIN",
        ],
        description="Garlic supplement; antiplatelet, lipid-lowering",
        known_interactions=["warfarin", "saquinavir", "isoniazid",
                            "birth control pills", "anticoagulants"],
    ),
    "turmeric": HerbProfile(
        common_name="Turmeric",
        latin_name="Curcuma longa",
        pinyin="姜黄",
        faers_patterns=[
            r"\bTURMERIC\b",
            r"CURCUMA",
            r"\bCURCUMIN\b",
        ],
        description="Turmeric spice; anti-inflammatory, CYP interaction potential",
        known_interactions=["warfarin", "aspirin", "clopidogrel",
                            "diabetes medications"],
    ),
    "saw_palmetto": HerbProfile(
        common_name="Saw Palmetto",
        latin_name="Serenoa repens",
        pinyin="锯棕榈",
        faers_patterns=[
            r"SAW PALMETTO",
            r"SERENOA",
        ],
        description="BPH remedy; antiandrogenic",
        known_interactions=["finasteride", "oral contraceptives",
                            "anticoagulants", "HRT"],
    ),
    "valerian": HerbProfile(
        common_name="Valerian",
        latin_name="Valeriana officinalis",
        pinyin="缬草",
        faers_patterns=[
            r"\bVALERIAN\b",
            r"VALERIANA",
        ],
        description="Sedative herb; GABAergic",
        known_interactions=["benzodiazepines", "barbiturates",
                            "alcohol", "CYP3A4 substrates"],
    ),
    "echinacea": HerbProfile(
        common_name="Echinacea",
        latin_name="Echinacea purpurea",
        pinyin="紫锥菊",
        faers_patterns=[
            r"\bECHINACEA\b",
            r"ECHINACEA PURPUREA",
        ],
        description="Immune stimulant",
        known_interactions=["immunosuppressants", "cyclosporine",
                            "liver-metabolized drugs"],
    ),
    "kava": HerbProfile(
        common_name="Kava",
        latin_name="Piper methysticum",
        pinyin="卡瓦",
        faers_patterns=[
            r"\bKAVA\b",
            r"PIPER METHYSTICUM",
            r"\bKAVA KAVA\b",
        ],
        description="Anxiolytic herb; CYP inhibition, hepatotoxicity risk",
        known_interactions=["benzodiazepines", "alcohol", "hepatotoxic drugs",
                            "CYP substrates", "levodopa"],
    ),
    "black_cohosh": HerbProfile(
        common_name="Black Cohosh",
        latin_name="Actaea racemosa",
        pinyin="黑升麻",
        faers_patterns=[
            r"BLACK COHOSH",
            r"ACTAEA RACEMOSA",
            r"CIMICIFUGA",
        ],
        description="Menopausal remedy; potential hepatotoxicity",
        known_interactions=["hepatotoxic drugs", "HRT", "tamoxifen"],
    ),
    "green_tea": HerbProfile(
        common_name="Green Tea Extract",
        latin_name="Camellia sinensis",
        pinyin="绿茶",
        faers_patterns=[
            r"GREEN TEA",
            r"CAMELLIA SINENSIS",
            r"GREEN TEA EXTRACT",
            r"EPIGALLOCATECHIN",
        ],
        description="Green tea extract; catechins, CYP interaction potential",
        known_interactions=["warfarin", "nadolol", "stimulants"],
    ),
    "hawthorn": HerbProfile(
        common_name="Hawthorn",
        latin_name="Crataegus",
        pinyin="山楂",
        faers_patterns=[
            r"\bHAWTHORN\b",
            r"\bCRATAEGUS\b",
        ],
        description="Cardiotonic herb",
        known_interactions=["digoxin", "antihypertensives",
                            "beta-blockers", "calcium channel blockers"],
    ),
}


def get_all_herb_names() -> List[str]:
    """Return list of all herb common names in the database."""
    return list(HERB_PROFILES.keys())


def get_herb_profile(name: str) -> Optional[HerbProfile]:
    """Get herb profile by common name (case-insensitive)."""
    name_lower = name.lower().replace(" ", "_").replace("-", "_")
    # Direct match
    if name_lower in HERB_PROFILES:
        return HERB_PROFILES[name_lower]
    # Fuzzy match
    for key, profile in HERB_PROFILES.items():
        if name_lower in key or key in name_lower:
            return profile
        if name.lower() == profile.common_name.lower():
            return profile
        if name.lower() == profile.latin_name.lower():
            return profile
    return None


def get_faers_pattern(herb_name: str) -> Optional[str]:
    """Get the combined regex pattern for matching a herb in FAERS data.

    Returns a single regex pattern that matches any of the herb's name variants.
    """
    profile = get_herb_profile(herb_name)
    if not profile:
        return None
    # Combine all patterns with OR
    return "|".join(profile.faers_patterns)


def get_all_herb_patterns() -> Dict[str, str]:
    """Return mapping of herb common name -> combined regex pattern."""
    result = {}
    for name in HERB_PROFILES:
        pattern = get_faers_pattern(name)
        if pattern:
            result[name] = pattern
    return result


def get_known_positive_controls() -> List[Dict]:
    """Return known herb-drug interactions for validation.

    Each entry has: herb, drug, expected_signal (bool), evidence_source
    """
    controls = []
    for herb_name, profile in HERB_PROFILES.items():
        for drug in profile.known_interactions:
            controls.append({
                "herb": profile.common_name,
                "herb_key": herb_name,
                "drug": drug,
                "expected_signal": True,
                "evidence": "Literature-reported interaction",
            })
    return controls

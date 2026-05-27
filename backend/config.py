from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Settings:
    app_name: str = "TCM-HerbDrug-FAERS"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8013
    # Disproportionality thresholds
    ror_threshold: float = 2.0
    prr_threshold: float = 2.0
    ic_threshold: float = 0.0
    min_cases: int = 3
    # Risk levels
    risk_level_1_label: str = "signal_only"
    risk_level_2_label: str = "signal_plus_database"
    risk_level_3_label: str = "signal_plus_mechanism"

settings = Settings()

import os
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Settings:
    app_name: str = "TCM-HerbDrug-FAERS"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8013
    debug: bool = True
    # Disproportionality thresholds
    ror_threshold: float = 2.0
    prr_threshold: float = 2.0
    ic_threshold: float = 0.0
    min_cases: int = 3
    # Risk levels
    risk_level_1_label: str = "signal_only"
    risk_level_2_label: str = "signal_plus_database"
    risk_level_3_label: str = "signal_plus_mechanism"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("FAERS_HOST", "0.0.0.0"),
            port=int(os.getenv("FAERS_PORT", "8013")),
            debug=os.getenv("FAERS_DEBUG", "true").lower() == "true",
            min_cases=int(os.getenv("FAERS_MIN_CASES", "3")),
        )

settings = Settings.from_env()

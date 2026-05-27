"""CYP enzyme / transporter mapping for herb-drug interactions."""
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CYPInteraction:
    drug: str
    cyp_enzyme: str
    interaction_type: str  # "substrate", "inhibitor", "inducer"
    potency: float  # 0-1

class CYPMapper:
    """CYP酶/转运体映射器"""

    CYP_SUBSTRATES = {
        "CYP2C9": ["warfarin", "phenytoin", "tolbutamide", "glipizide", "losartan"],
        "CYP2C19": ["clopidogrel", "omeprazole", "diazepam", "citalopram"],
        "CYP3A4": ["cyclosporine", "tacrolimus", "simvastatin", "midazolam",
                   "nifedipine", "amlodipine", "atorvastatin", "erythromycin"],
        "CYP2D6": ["metoprolol", "codeine", "tramadol", "fluoxetine", "dextromethorphan"],
        "CYP1A2": ["theophylline", "caffeine", "clozapine", "tizanidine"],
        "CYP2B6": ["efavirenz", "bupropion", "cyclophosphamide"],
    }

    def __init__(self):
        pass

    def get_substrate_drugs(self, cyp: str) -> List[str]:
        return self.CYP_SUBSTRATES.get(cyp, [])

    def find_cyp_conflicts(self, herb_cyp_inhibition: Dict[str, float],
                           drug: str) -> List[CYPInteraction]:
        conflicts = []
        for cyp, potency in herb_cyp_inhibition.items():
            substrates = self.get_substrate_drugs(cyp)
            if drug.lower() in [s.lower() for s in substrates]:
                conflicts.append(CYPInteraction(
                    drug=drug, cyp_enzyme=cyp,
                    interaction_type="inhibitor", potency=potency))
        return conflicts

    def get_all_cyp_risks(self, herb_name: str, herb_cyp_data: Dict[str, float]) -> List[Dict]:
        risks = []
        for cyp, inhib_score in herb_cyp_data.items():
            if inhib_score > 0.3:
                for substrate in self.get_substrate_drugs(cyp):
                    risks.append({
                        "herb": herb_name, "cyp": cyp,
                        "concurrent_drug": substrate,
                        "inhibition_score": inhib_score,
                        "risk_level": "high" if inhib_score > 0.7 else "moderate"
                    })
        return risks

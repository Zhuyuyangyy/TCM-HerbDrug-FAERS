"""Risk assessment API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..analysis.risk_scoring import RiskScorer

router = APIRouter(prefix="/api/risk", tags=["risk"])
_scorer = RiskScorer()

class RiskRequest(BaseModel):
    drug: str
    herb: str
    signal_strength: str = "none"
    has_db_support: bool = False
    has_mechanism: bool = False
    mechanism_confidence: float = 0.0
    cyp_potency: float = 0.0

@router.post("/assess")
async def assess_risk(req: RiskRequest):
    has_signal = req.signal_strength != "none"
    result = _scorer.assess_risk(
        drug=req.drug, herb=req.herb,
        has_signal=has_signal, signal_strength=req.signal_strength,
        has_db_support=req.has_db_support, has_mechanism=req.has_mechanism,
        mechanism_confidence=req.mechanism_confidence, cyp_potency=req.cyp_potency)
    return {"drug": result.drug, "herb": result.herb,
            "risk_level": result.level, "risk_label": result.level_label,
            "score": result.score, "factors": result.factors}

@router.get("/chain")
async def get_evidence_chain(drug: str, herb: str):
    from ..analysis.evidence_chain import EvidenceChainBuilder
    from ..models.mechanism_graph import MechanismGraph
    from ..data.herb_kg import HerbKnowledgeGraph
    from ..analysis.validation import ExternalValidator
    builder = EvidenceChainBuilder()
    # Gather mechanism data from knowledge graph
    mechanism_data = None
    kg = HerbKnowledgeGraph()
    cyp_inhib = kg.get_cyp_inhibitors(herb)
    if cyp_inhib:
        mech = MechanismGraph()
        # Try to find mechanism paths for common AEs
        sample_aes = ["bleeding_risk", "hypokalemia", "reduced_antiplatelet"]
        pathway_steps = []
        for ae in sample_aes:
            for mp in mech.find_mechanism_paths(herb, ae):
                pathway_steps.append({"from": mp.herb, "to": mp.ingredient,
                                      "relation": "herb_ingredient", "confidence": 1.0})
                if mp.cyp_enzyme:
                    pathway_steps.append({"from": mp.ingredient, "to": mp.cyp_enzyme,
                                          "relation": "ingredient_cyp", "confidence": 0.8})
                pathway_steps.append({"from": mp.cyp_enzyme or mp.target, "to": ae,
                                      "relation": "interaction_ae", "confidence": mp.confidence})
        if pathway_steps:
            mechanism_data = {"pathway": pathway_steps}
    # Check database support
    validator = ExternalValidator()
    validation = validator.validate(drug, herb)
    db_data = None
    if validation.get("validated"):
        db_data = {"support_score": 0.8 if validation.get("source") in ("EMA/FDA", "FDA") else 0.6}
    chain = builder.build_chain(herb, drug,
                                mechanism_data=mechanism_data,
                                db_data=db_data)
    return {"herb": chain.herb, "drug": chain.drug,
            "chain_type": chain.chain_type,
            "confidence": chain.overall_confidence,
            "links": [{"from": l.source, "to": l.target,
                       "relation": l.relation, "confidence": l.confidence}
                      for l in chain.links]}

"""Risk assessment API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/risk", tags=["risk"])

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
    from ..analysis.risk_scoring import RiskScorer
    from ..models.signal_detector import SignalDetector
    scorer = RiskScorer()
    has_signal = req.signal_strength != "none"
    result = scorer.assess_risk(
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
    builder = EvidenceChainBuilder()
    chain = builder.build_chain(herb, drug)
    return {"herb": chain.herb, "drug": chain.drug,
            "chain_type": chain.chain_type,
            "confidence": chain.overall_confidence,
            "links": [{"from": l.source, "to": l.target,
                       "relation": l.relation, "confidence": l.confidence}
                      for l in chain.links]}

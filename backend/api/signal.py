"""Signal detection API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/signal", tags=["signal"])

class SignalRequest(BaseModel):
    drug: str
    event: str
    a: int  # drug+event
    b: int  # drug+not_event
    c: int  # not_drug+event
    d: int  # not_drug+not_event

class BatchSignalRequest(BaseModel):
    records: List[SignalRequest]

@router.post("/detect")
async def detect_signal(req: SignalRequest):
    from ..models.signal_detector import SignalDetector
    detector = SignalDetector()
    signal = detector.detect_signal(req.drug, req.event, req.a, req.b, req.c, req.d)
    return {"drug": signal.drug, "event": signal.event,
            "is_signal": signal.is_signal, "strength": signal.signal_strength,
            "metrics": [{"metric": m.metric, "value": m.value,
                         "ci_lower": m.ci_lower, "ci_upper": m.ci_upper}
                        for m in signal.metrics]}

@router.post("/batch")
async def batch_detect(req: BatchSignalRequest):
    from ..models.signal_detector import SignalDetector
    detector = SignalDetector()
    records = [r.model_dump() for r in req.records]
    signals = detector.batch_detect(records)
    return {"total": len(signals), "signals": len([s for s in signals if s.is_signal]),
            "results": [{"drug": s.drug, "event": s.event,
                         "is_signal": s.is_signal, "strength": s.signal_strength}
                        for s in signals]}

@router.get("/query")
async def query_signals():
    return {"message": "Query endpoint — connect to FAERS database for real data"}

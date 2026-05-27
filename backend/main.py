"""TCM-HerbDrug-FAERS FastAPI application.

Unified herb-drug safety platform with:
- Signal detection (ROR, PRR, IC, BCPNN, MGPS)
- Mechanism explanation (CYP/P-gp knowledge graph)
- Risk assessment with bootstrap CI
- Temporal trend analysis for early warning
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.signal import router as signal_router
from .api.risk import router as risk_router
from .api.mechanism import router as mechanism_router
from .config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="中西药相互作用风险信号挖掘 — Unified Herb-Drug Safety Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(signal_router)
app.include_router(risk_router)
app.include_router(mechanism_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.2.0",
        "modules": ["signal_detection", "mechanism_explanation", "risk_assessment", "temporal_trends"],
    }


@app.get("/api/summary")
async def api_summary():
    """Overview of the platform capabilities."""
    from .models.mechanism_graph import MechanismGraph
    from .data.herb_kg import HerbKnowledgeGraph
    mg = MechanismGraph()
    kg = HerbKnowledgeGraph()
    return {
        "platform": settings.app_name,
        "herbs_in_kg": len(kg.herbs),
        "mechanism_nodes": mg.graph.number_of_nodes(),
        "mechanism_edges": mg.graph.number_of_edges(),
        "herbs": list(kg.herbs.keys()),
        "capabilities": [
            "HDI signal detection (ROR/PRR/IC/BCPNN/MGPS)",
            "Mechanism explanation via knowledge graph",
            "CYP enzyme / P-gp interaction profiling",
            "Three-level risk scoring with bootstrap CI",
            "Temporal trend analysis for early warning",
        ],
        "endpoints": {
            "signal": "/api/signal/detect, /api/signal/batch",
            "mechanism": "/api/mechanism/explain, /api/mechanism/search, /api/mechanism/herbs, /api/mechanism/cyps",
            "risk": "/api/risk/assess, /api/risk/chain",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

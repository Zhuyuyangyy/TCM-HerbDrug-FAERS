"""TCM-HerbDrug-FAERS FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.signal import router as signal_router
from .api.risk import router as risk_router
from .config import settings

app = FastAPI(title=settings.app_name, version=settings.version,
              description="中西药相互作用风险信号挖掘")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(signal_router)
app.include_router(risk_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": settings.version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

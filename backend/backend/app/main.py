from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import alerts

app = FastAPI(
    title="Sudan CRAM API",
    description="Conflict Risk Alert Monitoring API for Sudan",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)

@app.get("/")
async def root():
    return {
        "message": "Sudan CRAM API v2.0",
        "status": "operational",
        "data_source": "ACLED (Armed Conflict Location & Event Data)",
        "endpoints": {
            "alerts": "/api/alerts",
            "alerts_summary": "/api/alerts/summary"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

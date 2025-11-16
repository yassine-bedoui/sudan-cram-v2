# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import alerts, analytics, reports, dashboard, goldstein, intelligence

app = FastAPI(
    title="Sudan CRAM API",
    description="Conflict Risk Analysis & Monitoring System - Bivariate Climate + Conflict",
    version="2.0",
)

# CORS - Allow local development and your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://sudan-cram-v2.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(goldstein.router)  # has its own prefix="/api/goldstein"
app.include_router(intelligence.router)  # prefix="/api/intelligence" inside


@app.get("/")
async def root():
    return {
        "message": "Sudan CRAM API v2.0 - Bivariate Risk Analysis + GDELT Goldstein + Multi-Agent Intelligence",
        "status": "online",
        "endpoints": [
            "/api/dashboard",
            "/api/analytics",
            "/api/conflict-proneness",
            "/api/regions",
            "/api/monthly-trend",
            "/api/map-data",
            "/api/generate-brief",
            "/api/alerts",
            "/api/goldstein/escalation-risk",
            "/api/goldstein/timeline",
            "/api/goldstein/top-risks",
            "/api/intelligence/health",
            "/api/intelligence/analyze",
            "/docs",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

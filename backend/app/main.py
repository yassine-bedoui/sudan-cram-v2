# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    alerts,
    analytics,
    reports,
    dashboard,
    goldstein,
    intelligence,
    analysis,   
)
from app.api.routes import trend_routes
from app.api import collaboration  
from app.api.feedback import router as feedback_router
from app.api.reports import router as reports_router
from app.api.belief_state import router as belief_state_router






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
app.include_router(goldstein.router)      
app.include_router(intelligence.router)   
app.include_router(trend_routes.router, prefix="/api", tags=["trend-analysis"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])  
app.include_router(collaboration.router)
app.include_router(feedback_router)
app.include_router(reports_router, prefix="/api")
app.include_router(belief_state_router, prefix="/api")






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
            "/api/trend/risk",          # trend API endpoint
            "/api/analysis/run",        # 👈 NEW: LangGraph analysis endpoint
            "/docs",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

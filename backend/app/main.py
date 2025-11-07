# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import alerts, analytics, reports, dashboard

app = FastAPI(
    title="Sudan CRAM API",
    description="Conflict Risk Analysis & Monitoring System - Bivariate Climate + Conflict",
    version="2.0"
)

# CORS - Allow local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://sudan-cram-v2.onrender.com"
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

@app.get("/")
async def root():
    return {
        "message": "Sudan CRAM API v2.0 - Bivariate Risk Analysis",
        "status": "online",
        "endpoints": [
            "/api/dashboard",
            "/api/analytics",
            "/api/conflict-proneness",
            "/api/regions",
            "/api/monthly-trend",
            "/api/map-data",  # ADDED THIS LINE
            "/api/generate-brief",
            "/api/alerts",
            "/docs"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import alerts, analytics, reports, dashboard  

app = FastAPI(
    title="Sudan CRAM API",
    description="Conflict Risk Analysis & Monitoring System - Bivariate Climate + Conflict",
    version="2.0"
)

# CORS - Allow both local development and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                    # Local development
        "https://sudan-cram-v2.onrender.com"       # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers - ORDER MATTERS!
# Analytics first to ensure bivariate endpoints take priority
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(alerts.router)  # Keep for backwards compatibility
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
            "/api/generate-brief",
            "/api/alerts",
            "/docs"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import alerts, conflict_proneness, analytics

app = FastAPI(
    title="Sudan CRAM API",
    description="Conflict Risk Analysis & Monitoring System",
    version="2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(alerts.router)
app.include_router(conflict_proneness.router)
app.include_router(analytics.router, prefix="/api", tags=["analytics"])

@app.get("/")
async def root():
    return {
        "message": "Sudan CRAM API v2.0",
        "status": "online",
        "endpoints": [
            "/api/alerts",
            "/api/conflict-proneness",
            "/api/analytics",
            "/api/regions",
            "/docs"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

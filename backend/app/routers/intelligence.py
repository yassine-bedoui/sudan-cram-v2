from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.workflow import run_analysis

router = APIRouter(
    prefix="/api/intelligence",
    tags=["intelligence"],
)


class AnalysisRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: Optional[List[str]] = None


@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Run the full LangGraph multi-agent workflow:
      - RAG retrieval
      - (Optional) event extraction from raw text
      - trend analysis
      - scenario generation
      - consistency check + confidence
    """
    try:
        result = run_analysis(
            region=request.region,
            raw_data=request.raw_data,
            interventions=request.interventions,
        )

        return {
            "region": result["region"],
            "timestamp": result["timestamp"],
            "events": result.get("extracted_events"),
            "trends": result.get("trend_analysis"),
            "scenarios": result.get("scenarios"),
            "validation": result.get("validation"),
            "approval_status": result.get("approval_status"),
            "confidence": result.get("confidence_score"),
            "messages": result.get("messages", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "intelligence"}

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from .data_loader import get_alerts_from_acled

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("/")
async def get_alerts(severity: str = None, limit: int = 100):
    """Get alerts from ACLED conflict data"""
    try:
        alerts = get_alerts_from_acled(limit=limit)
        
        if severity and severity.upper() != "ALL":
            alerts = [a for a in alerts if a['alert_level'] == severity.upper()]
        
        # Calculate summary
        summary = {
            "total_alerts": len(alerts),
            "critical": sum(1 for a in alerts if a['alert_level'] == 'SEVERE'),
            "high": sum(1 for a in alerts if a['alert_level'] == 'HIGH'),
            "medium": sum(1 for a in alerts if a['alert_level'] == 'MEDIUM'),
            "low": sum(1 for a in alerts if a['alert_level'] == 'LOW'),
            "total_incidents": sum(a['event_count'] for a in alerts),
            "total_fatalities": sum(a['fatalities'] for a in alerts)
        }
        
        return {
            "success": True,
            "alerts": alerts,
            "summary": summary,
            "source": "ACLED",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_summary():
    """Get alerts summary"""
    try:
        alerts = get_alerts_from_acled(limit=1000)
        
        return {
            "success": True,
            "total_alerts": len(alerts),
            "total_incidents": sum(a['event_count'] for a in alerts),
            "avg_risk": sum(a['risk_score'] for a in alerts) / len(alerts) if alerts else 0,
            "total_fatalities": sum(a['fatalities'] for a in alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

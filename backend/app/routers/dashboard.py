# app/routers/dashboard.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd
from pathlib import Path

router = APIRouter()

# Load data - FIXED PATH AND FILE
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
COMBINED_DATA_PATH = DATA_DIR / "combined_risk_v2.csv"

try:
    df = pd.read_csv(COMBINED_DATA_PATH)
    print(f"✅ Loaded dashboard data: {len(df)} rows")
    print(f"   Columns: {', '.join(df.columns.tolist())}")
except Exception as e:
    print(f"❌ Error loading dashboard data: {e}")
    print(f"   Tried to load from: {COMBINED_DATA_PATH}")
    df = pd.DataFrame()


@router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get dashboard overview data with conflict metrics
    """
    if df.empty:
        raise HTTPException(status_code=500, detail="Dashboard data not loaded")

    try:
        # Calculate summary metrics
        total_events = int(df['events_6m'].sum()) if 'events_6m' in df.columns else 0
        total_fatalities = int(df['fatalities_6m'].sum()) if 'fatalities_6m' in df.columns else 0
        total_regions = len(df)

        # Calculate average risks
        avg_climate_risk = float(df['climate_risk_score'].mean()) if 'climate_risk_score' in df.columns else 0
        avg_conflict_risk = float(df['political_risk_score'].mean()) if 'political_risk_score' in df.columns else 0

        # Data confidence (mock for now - you can calculate based on data completeness)
        data_confidence = 94.8

        # Get highest risk region - FIXED: Use ADM1_NAME instead of 'region'
        if 'political_risk_score' in df.columns and 'ADM1_NAME' in df.columns:
            highest_risk_idx = df['political_risk_score'].idxmax()
            highest_risk_region = df.loc[highest_risk_idx, 'ADM1_NAME']
        else:
            highest_risk_region = "N/A"

        # Risk distribution
        climate_distribution = {}
        conflict_distribution = {}

        if 'cdi_category' in df.columns:
            climate_distribution = df['cdi_category'].value_counts().to_dict()

        if 'risk_category' in df.columns:
            conflict_distribution = df['risk_category'].value_counts().to_dict()

        # Get trend (mock - you can implement actual trend calculation)
        trend = {
            "direction": "rising",
            "percentage": 12.5
        }

        # Get quick insights
        alerts = {
            "high": int(conflict_distribution.get('HIGH', 0)) if conflict_distribution else 0,
            "very_high": int(conflict_distribution.get('VERY HIGH', 0)) if conflict_distribution else 0,
            "extreme": int(conflict_distribution.get('EXTREME', 0)) if conflict_distribution else 0
        }

        active_alerts = alerts['high'] + alerts['very_high'] + alerts['extreme']

        return {
            "summary": {
                "conflict_events": total_events,
                "states_analyzed": total_regions,
                "risk_assessments": total_regions,
                "data_confidence": data_confidence
            },
            "quick_insights": {
                "highest_risk_state": highest_risk_region,
                "active_alerts": active_alerts,
                "alert_breakdown": alerts,
                "trend": trend
            },
            "risk_distribution": {
                "climate": climate_distribution,
                "conflict": conflict_distribution
            },
            "metrics": {
                "total_events": total_events,
                "total_fatalities": total_fatalities,
                "avg_climate_risk": round(avg_climate_risk, 2),
                "avg_conflict_risk": round(avg_conflict_risk, 2)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard data: {str(e)}")

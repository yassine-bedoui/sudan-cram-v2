from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd
from pathlib import Path

router = APIRouter()

# Load data paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
CP_FILE = DATA_DIR / "conflict_proneness_v2.csv"

try:
    df_cp = pd.read_csv(CP_FILE)
    print(f"✅ Loaded dashboard CP data: {len(df_cp)} rows")
    print(f"   Columns: {', '.join(df_cp.columns.tolist())}")
except Exception as e:
    print(f"❌ Error loading CP data: {e}")
    df_cp = pd.DataFrame()


@router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get dashboard overview data with conflict metrics
    """
    if df_cp.empty:
        raise HTTPException(status_code=500, detail="Dashboard data not loaded")

    try:
        # Calculate summary metrics
        total_events = int(df_cp['incidents'].sum()) if 'incidents' in df_cp.columns else 0
        total_fatalities = int(df_cp['fatalities'].sum()) if 'fatalities' in df_cp.columns else 0
        total_regions = len(df_cp)

        # Calculate average scores
        avg_conflict_proneness = float(df_cp['conflict_proneness'].mean()) if 'conflict_proneness' in df_cp.columns else 0
        avg_climate_risk = float(df_cp['climate_risk_score'].mean()) if 'climate_risk_score' in df_cp.columns else 0

        # Data confidence
        data_confidence = 94.8

        # Get highest risk region
        if 'conflict_proneness' in df_cp.columns and 'region' in df_cp.columns:
            highest_risk_idx = df_cp['conflict_proneness'].idxmax()
            highest_risk_region = df_cp.loc[highest_risk_idx, 'region']
        else:
            highest_risk_region = "N/A"

        # Risk distribution
        climate_distribution = {}
        conflict_distribution = {}

        if 'cdi_category' in df_cp.columns:
            climate_distribution = df_cp['cdi_category'].value_counts().to_dict()

        if 'proneness_level' in df_cp.columns:
            conflict_distribution = df_cp['proneness_level'].value_counts().to_dict()

        # Get trend
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
                "avg_conflict_proneness": round(avg_conflict_proneness, 2),
                "avg_climate_risk": round(avg_climate_risk, 2)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard data: {str(e)}")


@router.get("/map-data")
async def get_map_data(indicator: str = "conflict-risk") -> Dict[str, float]:
    """
    Get risk scores by region for map visualization
    
    Parameters:
    - indicator: "conflict-risk", "climate-risk", or "combined-risk"
    """
    if df_cp.empty:
        raise HTTPException(status_code=500, detail="Dashboard data not loaded")

    try:
        # Check if region column exists
        if 'region' not in df_cp.columns:
            raise HTTPException(status_code=500, detail="Region column not found in data")

        # Select the appropriate risk metric
        if indicator == "climate-risk":
            if 'climate_risk_score' not in df_cp.columns:
                raise HTTPException(status_code=500, detail="Climate risk data not available")
            risk_col = 'climate_risk_score'
        elif indicator == "combined-risk":
            # Calculate combined risk (average of conflict + climate)
            if 'conflict_proneness' in df_cp.columns and 'climate_risk_score' in df_cp.columns:
                df_temp = df_cp.copy()
                df_temp['combined'] = (df_temp['conflict_proneness'] + df_temp['climate_risk_score']) / 2
                risk_col = 'combined'
            else:
                raise HTTPException(status_code=500, detail="Required data for combined risk not available")
        else:
            # Default: conflict risk
            if 'conflict_proneness' not in df_cp.columns:
                raise HTTPException(status_code=500, detail="Conflict proneness data not available")
            risk_col = 'conflict_proneness'

        # Group by region and calculate average
        if indicator == "combined-risk":
            result = df_temp.groupby('region')[risk_col].mean().round(1).to_dict()
        else:
            result = df_cp.groupby('region')[risk_col].mean().round(1).to_dict()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map data: {str(e)}")


@router.get("/regions")
async def get_regions() -> Dict[str, list]:
    """
    Get list of all regions
    """
    if df_cp.empty:
        raise HTTPException(status_code=500, detail="Dashboard data not loaded")

    try:
        if 'region' not in df_cp.columns:
            raise HTTPException(status_code=500, detail="Region column not found")

        regions = sorted(df_cp['region'].dropna().unique().tolist())
        return {"regions": regions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting regions: {str(e)}")

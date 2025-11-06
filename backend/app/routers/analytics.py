# app/routers/analytics.py
"""
✅ Enhanced Analytics Router - Conflict Proneness v2 with all 4 indicators
"""
from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

CP_FILE = DATA_DIR / "conflict_proneness_v2.csv"


def load_conflict_proneness():
    """Load CP v2 with all 4 indicators"""
    try:
        df_cp = pd.read_csv(CP_FILE)
        return df_cp
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {CP_FILE}")


def get_color_for_risk(level):
    """Map risk level to color"""
    color_map = {
        "EXTREME": "#8B0000",
        "VERY HIGH": "#DC143C",
        "HIGH": "#FF6347",
        "MODERATE": "#FFD700",
        "LOW": "#00A86B",
    }
    return color_map.get(str(level).upper(), "#6b7280")


@router.get("/conflict-proneness")
async def get_conflict_proneness():
    """
    ✅ Returns Conflict Proneness v2 with all 4 indicators breakdown
    
    Indicators:
    - incidents: Event frequency (0-10 normalized)
    - causes_pct: % of high-risk political/communal/resource events
    - num_actors: Number of distinct organizations involved
    - trend_delta: Recent trend (positive = increasing)
    """
    df = load_conflict_proneness()
    
    regions = {}
    for _, row in df.iterrows():
        region_name = str(row['region']).strip()
        
        regions[region_name] = {
            'region': region_name,
            # Main Conflict Proneness score
            'proneness_score': float(row['conflict_proneness']),
            'proneness_level': str(row['proneness_level']).strip(),
            'proneness_color': get_color_for_risk(row['proneness_level']),
            # All 4 Indicators (breakdown)
            'indicators': {
                'incidents': {
                    'value': int(row['incidents']),
                    'label': 'Event Frequency'
                },
                'causes_pct': {
                    'value': round(float(row['causes_pct']), 1),
                    'label': 'High-Risk % (Political/Communal/Resource)'
                },
                'num_actors': {
                    'value': int(row['num_actors']),
                    'label': 'Distinct Organizations'
                },
                'trend_delta': {
                    'value': int(row['trend_delta']),
                    'label': 'Recent Trend (+ = Increasing)'
                }
            },
            # Support metrics
            'high_risk_events': int(row['high_risk_events']),
            'fatalities': int(row['fatalities']),
            'fatality_rate': round(float(row['fatality_rate']), 3),
            'climate_risk_score': round(float(row['climate_risk_score']), 2),
            'climate_risk_level': str(row['cdi_category']).strip()
        }
    
    return regions


@router.get("/analytics")
async def get_analytics():
    """Get summary analytics with 4-indicator breakdowns"""
    df = load_conflict_proneness()
    
    return {
        "summary": {
            "total_regions": len(df),
            "avg_conflict_proneness": round(df['conflict_proneness'].mean(), 2),
            "total_events": int(df['incidents'].sum()),
            "total_fatalities": int(df['fatalities'].sum()),
            "high_proneness_count": (df['proneness_level'].isin(['EXTREME', 'VERY HIGH'])).sum(),
        },
        "indicator_averages": {
            "avg_incidents": round(df['incidents'].mean(), 1),
            "avg_causes_pct": round(df['causes_pct'].mean(), 1),
            "avg_actors": round(df['num_actors'].mean(), 1),
            "avg_trend": round(df['trend_delta'].mean(), 1)
        },
        "distribution": {
            'EXTREME': (df['proneness_level'] == 'EXTREME').sum(),
            'VERY_HIGH': (df['proneness_level'] == 'VERY HIGH').sum(),
            'HIGH': (df['proneness_level'] == 'HIGH').sum(),
            'MODERATE': (df['proneness_level'] == 'MODERATE').sum(),
            'LOW': (df['proneness_level'] == 'LOW').sum(),
        }
    }

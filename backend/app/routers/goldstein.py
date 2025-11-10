"""
GDELT Goldstein Scale API Endpoints
Real-time conflict escalation tracking
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime
import glob
import os

router = APIRouter(prefix="/api/goldstein", tags=["Goldstein Escalation"])

# Get project root (go up from backend/app/routers/ to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

def get_latest_file(pattern):
    """Get most recent file matching pattern"""
    # Make pattern absolute
    if not os.path.isabs(pattern):
        pattern = os.path.join(PROJECT_ROOT, pattern)
    
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

@router.get("/escalation-risk")
async def get_escalation_risk():
    """
    Get current escalation risk by location
    Returns: {location: {risk_score, level, goldstein, trend, events}}
    """
    try:
        risk_file = get_latest_file('data/processed/goldstein_escalation_risk_*.csv')
        
        if not risk_file:
            raise HTTPException(
                status_code=404,
                detail="No Goldstein analysis found. Run: python scripts/gdelt/analyze_goldstein_trends.py"
            )
        
        df = pd.read_csv(risk_file)
        
        # Format for frontend
        result = {
            'last_updated': datetime.fromtimestamp(os.path.getctime(risk_file)).isoformat(),
            'locations': {}
        }
        
        for _, row in df.iterrows():
            result['locations'][row['location']] = {
                'risk_score': round(float(row['escalation_risk']), 1),
                'risk_level': row['risk_level'],
                'avg_goldstein': round(float(row['avg_goldstein']), 2),
                'trend': round(float(row['goldstein_trend']), 2),
                'trend_direction': 'escalating' if row['goldstein_trend'] < 0 else 'de-escalating',
                'event_count': int(row['event_count']),
                'media_mentions': int(row['media_mentions']),
                'last_seen': row['last_seen']
            }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline")
async def get_goldstein_timeline(hours: int = 24):
    """
    Get hourly Goldstein timeline
    """
    try:
        timeline_file = get_latest_file('data/processed/goldstein_hourly_timeline_*.csv')
        
        if not timeline_file:
            raise HTTPException(status_code=404, detail="No timeline data found")
        
        df = pd.read_csv(timeline_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to requested hours
        cutoff = df['timestamp'].max() - pd.Timedelta(hours=hours)
        df = df[df['timestamp'] >= cutoff]
        
        return {
            'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
            'goldstein_scores': df['avg_goldstein'].tolist(),
            'event_counts': df['event_count'].tolist(),
            'mentions': df['mentions'].tolist()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-risks")
async def get_top_risks(limit: int = 10):
    """Get top N highest-risk locations"""
    try:
        risk_file = get_latest_file('data/processed/goldstein_escalation_risk_*.csv')
        
        if not risk_file:
            raise HTTPException(status_code=404, detail="No risk data")
        
        df = pd.read_csv(risk_file).head(limit)
        
        return {
            'top_risks': df.to_dict('records')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

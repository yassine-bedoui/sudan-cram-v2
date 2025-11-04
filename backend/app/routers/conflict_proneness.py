from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path
from app.utils.coordinates import SUDAN_COORDINATES

router = APIRouter(prefix="/api/conflict-proneness", tags=["conflict-proneness"])

_df_cache = None

def load_data():
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    
    acled_path = Path("data/processed/acled_with_causes.csv")
    if not acled_path.exists():
        raise FileNotFoundError(f"Data not found at {acled_path}")
    
    df = pd.read_csv(acled_path)
    _df_cache = df
    return df

@router.get("", include_in_schema=True)
async def get_conflict_proneness():
    """Get conflict proneness data for map visualization"""
    try:
        df = load_data()
        
        # Group by region and sum events/fatalities
        region_stats = df.groupby('ADMIN1').agg({
            'EVENTS': 'sum',
            'FATALITIES': 'sum'
        }).reset_index()
        
        # Calculate max events for normalization
        max_events = region_stats['EVENTS'].max()
        
        # Build regions list with risk scores
        regions = []
        for _, row in region_stats.iterrows():
            region = str(row['ADMIN1'])
            events = int(row['EVENTS'])
            fatalities = int(row['FATALITIES'])
            
            # Calculate normalized risk score (0-10 scale)
            risk_score = (events / max_events * 10) if max_events > 0 else 0
            
            coords = SUDAN_COORDINATES.get(region, {"lat": 15, "lon": 30})
            
            regions.append({
                'region': region,
                'risk_score': round(float(risk_score), 2),
                'events': events,
                'fatalities': fatalities,
                'level': 'SEVERE' if risk_score >= 7 else 'HIGH' if risk_score >= 5 else 'MEDIUM' if risk_score >= 3 else 'LOW',
                'lat': coords['lat'],
                'lon': coords['lon']
            })
        
        return {
            "success": True,
            "regions": sorted(regions, key=lambda x: x['risk_score'], reverse=True),
            "total_regions": len(regions)
        }
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

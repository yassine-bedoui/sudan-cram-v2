# app/routers/analytics.py
"""
✅ Enhanced Analytics Router - Conflict Proneness v2 with all 4 indicators
FIXED: Proper numpy type conversion + real monthly trends from ACLED
"""
from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from pathlib import Path

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

CP_FILE = DATA_DIR / "conflict_proneness_v2.csv"
ACLED_FILE = DATA_DIR / "acled_with_causes.csv"

_cp_cache = None
_acled_cache = None
_monthly_cache = None


def load_conflict_proneness():
    """Load CP v2 with caching"""
    global _cp_cache
    if _cp_cache is not None:
        return _cp_cache
    try:
        df_cp = pd.read_csv(CP_FILE)
        _cp_cache = df_cp
        return df_cp
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {CP_FILE}")


def load_acled_data():
    """Load ACLED events data with caching"""
    global _acled_cache
    if _acled_cache is not None:
        return _acled_cache
    try:
        df_acled = pd.read_csv(ACLED_FILE)
        _acled_cache = df_acled
        return df_acled
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {ACLED_FILE}")


def compute_monthly_trends():
    """Aggregate ACLED events by month - returns real data"""
    global _monthly_cache
    if _monthly_cache is not None:
        return _monthly_cache
    
    try:
        df_acled = load_acled_data()
        
        # Find date column
        date_col = None
        for col in ['event_date', 'WEEK', 'date', 'DATE']:
            if col in df_acled.columns:
                date_col = col
                break
        
        if date_col is None:
            return []
        
        # Parse dates and extract year-month
        df_acled[date_col] = pd.to_datetime(df_acled[date_col], errors='coerce')
        df_acled['year_month'] = df_acled[date_col].dt.strftime('%Y-%m')
        
        # Group by month
        monthly_agg = df_acled.groupby('year_month', as_index=False).agg({
            'year_month': 'first',
            'FATALITIES': ['sum', 'count']
        }).reset_index(drop=True)
        
        monthly_agg.columns = ['year_month', 'fatalities', 'events']
        monthly_agg = monthly_agg.sort_values('year_month')
        
        # Format response
        monthly_data = []
        for _, row in monthly_agg.iterrows():
            try:
                monthly_data.append({
                    'month': str(row['year_month']),
                    'events': convert_to_native(int(row['events'])),
                    'fatalities': convert_to_native(int(row['fatalities']) if pd.notna(row['fatalities']) else 0)
                })
            except:
                continue
        
        _monthly_cache = monthly_data
        return monthly_data
        
    except Exception as e:
        print(f"⚠️ Warning computing monthly trends: {e}")
        return []


def convert_to_native(value):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(value, (np.integer, np.int64, np.int32, np.int16)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, np.bool_):
        return bool(value)
    elif pd.isna(value):
        return None
    return value


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
    """Returns Conflict Proneness v2 with all 4 indicators breakdown"""
    try:
        df = load_conflict_proneness()
        
        regions = {}
        for _, row in df.iterrows():
            region_name = str(row['region']).strip()
            
            regions[region_name] = {
                'region': region_name,
                'proneness_score': convert_to_native(row['conflict_proneness']),
                'proneness_level': str(row['proneness_level']).strip(),
                'proneness_color': get_color_for_risk(row['proneness_level']),
                'indicators': {
                    'incidents': {
                        'value': convert_to_native(row['incidents']),
                        'label': 'Event Frequency'
                    },
                    'causes_pct': {
                        'value': round(convert_to_native(row['causes_pct']), 1),
                        'label': 'High-Risk % (Political/Communal/Resource)'
                    },
                    'num_actors': {
                        'value': convert_to_native(row['num_actors']),
                        'label': 'Distinct Organizations'
                    },
                    'trend_delta': {
                        'value': convert_to_native(row['trend_delta']),
                        'label': 'Recent Trend (+ = Increasing)'
                    }
                },
                'high_risk_events': convert_to_native(row['high_risk_events']),
                'fatalities': convert_to_native(row['fatalities']),
                'fatality_rate': round(convert_to_native(row['fatality_rate']), 3),
                'climate_risk_score': round(convert_to_native(row['climate_risk_score']), 2),
                'climate_risk_level': str(row['cdi_category']).strip()
            }
        
        return regions
        
    except Exception as e:
        print(f"❌ ERROR in /api/conflict-proneness: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics():
    """Returns summary analytics with 4-indicator breakdowns"""
    try:
        df = load_conflict_proneness()
        
        summary = {
            "total_regions": convert_to_native(len(df)),
            "avg_conflict_proneness": round(convert_to_native(df['conflict_proneness'].mean()), 2),
            "avg_climate_risk": round(convert_to_native(df['climate_risk_score'].mean()), 2),
            "total_events": convert_to_native(df['incidents'].sum()),
            "total_fatalities": convert_to_native(df['fatalities'].sum()),
            "highest_risk_region": str(df.loc[df['conflict_proneness'].idxmax(), 'region']),
            "high_proneness_count": convert_to_native((df['proneness_level'].isin(['EXTREME', 'VERY HIGH'])).sum()),
        }
        
        indicator_averages = {
            "avg_incidents": round(convert_to_native(df['incidents'].mean()), 1),
            "avg_causes_pct": round(convert_to_native(df['causes_pct'].mean()), 1),
            "avg_actors": round(convert_to_native(df['num_actors'].mean()), 1),
            "avg_trend": round(convert_to_native(df['trend_delta'].mean()), 1)
        }
        
        distribution = {
            'EXTREME': convert_to_native((df['proneness_level'] == 'EXTREME').sum()),
            'VERY_HIGH': convert_to_native((df['proneness_level'] == 'VERY HIGH').sum()),
            'HIGH': convert_to_native((df['proneness_level'] == 'HIGH').sum()),
            'MODERATE': convert_to_native((df['proneness_level'] == 'MODERATE').sum()),
            'LOW': convert_to_native((df['proneness_level'] == 'LOW').sum()),
        }
        
        climate_dist = df['cdi_category'].value_counts()
        conflict_dist = df['proneness_level'].value_counts()
        
        risk_distribution = {
            "climate": {str(cat): convert_to_native(count) for cat, count in climate_dist.items()},
            "conflict": {str(cat): convert_to_native(count) for cat, count in conflict_dist.items()}
        }
        
        top_regions = [
            {
                'region': str(row['region']),
                'climate_risk_score': round(convert_to_native(row['climate_risk_score']), 2),
                'political_risk_score': round(convert_to_native(row['conflict_proneness']), 2),
                'cdi_category': str(row['cdi_category']),
                'risk_category': str(row['proneness_level']),
                'events_6m': convert_to_native(row['incidents']),
                'fatalities_6m': convert_to_native(row['fatalities']),
            }
            for _, row in df.nlargest(10, 'conflict_proneness').iterrows()
        ]
        
        regional_data = [
            {
                'region': str(row['region']),
                'climate_risk_score': round(convert_to_native(row['climate_risk_score']), 2),
                'political_risk_score': round(convert_to_native(row['conflict_proneness']), 2),
                'events_6m': convert_to_native(row['incidents']),
                'fatalities_6m': convert_to_native(row['fatalities']),
            }
            for _, row in df.iterrows()
        ]
        
        return {
            "summary": summary,
            "indicator_averages": indicator_averages,
            "distribution": distribution,
            "risk_distribution": risk_distribution,
            "top_regions": top_regions,
            "regional_data": regional_data
        }
        
    except Exception as e:
        print(f"❌ ERROR in /api/analytics: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions")
async def get_regions():
    """Returns bivariate region data for regions/page.tsx"""
    try:
        df = load_conflict_proneness()
        
        regions = []
        for _, row in df.iterrows():
            regions.append({
                'region': str(row['region']),
                'climate_risk_score': round(convert_to_native(row['climate_risk_score']), 2),
                'cdi_category': str(row['cdi_category']),
                'political_risk_score': round(convert_to_native(row['conflict_proneness']), 2),
                'risk_category': str(row['proneness_level']),
                'bivariate_category': f"{row['proneness_level']}_{row['cdi_category']}",
                'events_6m': convert_to_native(row['incidents']),
                'fatalities_6m': convert_to_native(row['fatalities']),
                'trend': 'stable',
            })
        
        regions = sorted(regions, key=lambda x: x['political_risk_score'], reverse=True)
        
        climate_summary = {str(cat): convert_to_native((df['cdi_category'] == cat).sum()) for cat in df['cdi_category'].unique()}
        conflict_summary = {str(cat): convert_to_native((df['proneness_level'] == cat).sum()) for cat in df['proneness_level'].unique()}
        
        return {
            "regions": regions,
            "total_count": len(regions),
            "risk_summary": {
                "climate": climate_summary,
                "conflict": conflict_summary
            }
        }
        
    except Exception as e:
        print(f"❌ ERROR in /api/regions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly-trend")
async def get_monthly_trend():
    """Returns REAL monthly conflict trend data from ACLED events"""
    try:
        monthly_data = compute_monthly_trends()
        
        if not monthly_data:
            return {
                "data": [],
                "summary": {
                    "avg_monthly_events": 0,
                    "avg_monthly_fatalities": 0,
                    "trend": "unknown"
                }
            }
        
        events_list = [m['events'] for m in monthly_data if isinstance(m['events'], (int, float))]
        fatalities_list = [m['fatalities'] for m in monthly_data if isinstance(m['fatalities'], (int, float))]
        
        avg_events = round(sum(events_list) / len(events_list), 1) if events_list else 0
        avg_fatalities = round(sum(fatalities_list) / len(fatalities_list), 1) if fatalities_list else 0
        
        if len(events_list) >= 2:
            recent_avg = sum(events_list[-3:]) / 3 if len(events_list) >= 3 else events_list[-1]
            earlier_avg = sum(events_list[:3]) / 3 if len(events_list) >= 3 else events_list[0]
            trend = "increasing" if recent_avg > earlier_avg else "decreasing"
        else:
            trend = "stable"
        
        return {
            "data": monthly_data,
            "summary": {
                "avg_monthly_events": avg_events,
                "avg_monthly_fatalities": avg_fatalities,
                "trend": trend,
                "total_months": len(monthly_data)
            }
        }
        
    except Exception as e:
        print(f"❌ ERROR in /api/monthly-trend: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

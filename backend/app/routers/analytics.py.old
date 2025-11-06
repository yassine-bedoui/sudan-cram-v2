# app/routers/analytics.py
"""
Sudan CRAM Analytics Router - Bivariate Risk Data
Implements Climate Risk + Conflict Risk as separate dimensions
"""
from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path
import numpy as np

router = APIRouter()

# Paths to processed data files - FIXED: Go up 3 levels to reach project root
PROJECT_ROOT = Path(__file__).parent.parent.parent  # backend/app/routers -> backend/
DATA_DIR = PROJECT_ROOT / "data" / "processed"
CLIMATE_DATA = DATA_DIR / "climate_risk_cdi_v2_real.csv"
CONFLICT_DATA = DATA_DIR / "political_risk_v2.csv"
ACLED_DATA = DATA_DIR / "acled_with_causes.csv"


def load_bivariate_data():
    """Load and merge climate + conflict risk data"""
    try:
        climate_df = pd.read_csv(CLIMATE_DATA)
        conflict_df = pd.read_csv(CONFLICT_DATA)

        # Merge on region name
        combined = climate_df.merge(
            conflict_df[['ADM1_NAME', 'political_risk_score', 'events_6m', 'fatalities_6m', 'risk_category']],
            on='ADM1_NAME',
            how='left'
        )

        # Fill NaN values with safe defaults
        combined['political_risk_score'] = combined['political_risk_score'].fillna(0)
        combined['events_6m'] = combined['events_6m'].fillna(0)
        combined['fatalities_6m'] = combined['fatalities_6m'].fillna(0)
        combined['risk_category'] = combined['risk_category'].fillna('LOW')

        return combined
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data file not found: {e}")


def create_bivariate_category(climate_score, conflict_score):
    """Create bivariate category from two scores"""
    # Handle NaN/None values
    climate_score = climate_score if pd.notna(climate_score) else 0
    conflict_score = conflict_score if pd.notna(conflict_score) else 0

    # Climate levels
    if climate_score >= 7:
        climate_level = "severe"
    elif climate_score >= 5:
        climate_level = "high"
    elif climate_score >= 3:
        climate_level = "medium"
    else:
        climate_level = "low"

    # Conflict levels
    if conflict_score >= 8:
        conflict_level = "extreme"
    elif conflict_score >= 6:
        conflict_level = "very_high"
    elif conflict_score >= 4:
        conflict_level = "high"
    elif conflict_score >= 2:
        conflict_level = "moderate"
    else:
        conflict_level = "low"

    return f"{climate_level}_climate_{conflict_level}_conflict"


@router.get("/analytics")
async def get_analytics():
    """Get comprehensive bivariate analytics"""
    df = load_bivariate_data()

    # Calculate bivariate categories
    df['bivariate_category'] = df.apply(
        lambda row: create_bivariate_category(
            row['climate_risk_score'],
            row['political_risk_score']
        ),
        axis=1
    )

    # Summary statistics
    total_regions = len(df)
    avg_climate_risk = round(df['climate_risk_score'].mean(), 2)
    avg_conflict_risk = round(df['political_risk_score'].mean(), 2)
    total_events = int(df['events_6m'].sum())
    total_fatalities = int(df['fatalities_6m'].sum())

    # Highest risk regions
    df['combined_risk'] = (df['climate_risk_score'] + df['political_risk_score']) / 2
    highest_risk_region = df.nlargest(1, 'combined_risk').iloc[0]['ADM1_NAME']

    # Risk distribution by category
    climate_categories = df['cdi_category'].value_counts().to_dict()
    conflict_categories = df['risk_category'].value_counts().to_dict()

    # Top 10 highest combined risk regions
    top_regions = df.nlargest(10, 'combined_risk')[[
        'ADM1_NAME', 'climate_risk_score', 'political_risk_score',
        'cdi_category', 'risk_category', 'events_6m', 'fatalities_6m'
    ]].rename(columns={'ADM1_NAME': 'region'}).to_dict('records')

    # Regional data for visualization (all regions)
    regional_data = df[[
        'ADM1_NAME', 'climate_risk_score', 'political_risk_score',
        'cdi_category', 'risk_category', 'bivariate_category',
        'events_6m', 'fatalities_6m'
    ]].rename(columns={'ADM1_NAME': 'region'}).to_dict('records')

    return {
        "summary": {
            "total_regions": total_regions,
            "avg_climate_risk": avg_climate_risk,
            "avg_conflict_risk": avg_conflict_risk,
            "total_events": total_events,
            "total_fatalities": total_fatalities,
            "highest_risk_region": highest_risk_region
        },
        "risk_distribution": {
            "climate": climate_categories,
            "conflict": conflict_categories
        },
        "top_regions": top_regions,
        "regional_data": regional_data
    }


@router.get("/conflict-proneness")
async def get_conflict_proneness():
    """
    Get bivariate climate + conflict risk data
    Returns separate climate and conflict dimensions (NOT combined)
    """
    df = load_bivariate_data()

    # Create bivariate categories
    df['bivariate_category'] = df.apply(
        lambda row: create_bivariate_category(
            row['climate_risk_score'],
            row['political_risk_score']
        ),
        axis=1
    )

    regions = []
    for _, row in df.iterrows():
        regions.append({
            'region': row['ADM1_NAME'],
            'climate_risk_score': round(float(row['climate_risk_score']), 2),
            'climate_risk_level': row['cdi_category'],
            'conflict_risk_score': round(float(row['political_risk_score']), 2),
            'conflict_risk_level': row['risk_category'],
            'bivariate_category': row['bivariate_category'],
            'events_6m': int(row['events_6m']),
            'fatalities_6m': int(row['fatalities_6m'])
        })

    return {'regions': regions}


@router.get("/regions")
async def get_regions():
    """Get all regions with detailed bivariate stats"""
    df = load_bivariate_data()

    # Create bivariate categories
    df['bivariate_category'] = df.apply(
        lambda row: create_bivariate_category(
            row['climate_risk_score'],
            row['political_risk_score']
        ),
        axis=1
    )

    # Sort by combined risk (for ordering)
    df['combined_risk'] = (df['climate_risk_score'] + df['political_risk_score']) / 2
    df = df.sort_values('combined_risk', ascending=False)

    # Format for frontend
    regions = []
    for _, row in df.iterrows():
        regions.append({
            'region': row['ADM1_NAME'],
            'climate_risk_score': round(float(row['climate_risk_score']), 2),
            'climate_risk_level': row['cdi_category'],
            'conflict_risk_score': round(float(row['political_risk_score']), 2),
            'conflict_risk_level': row['risk_category'],
            'bivariate_category': row['bivariate_category'],
            'events': int(row['events_6m']),
            'fatalities': int(row['fatalities_6m']),
            'trend': 'stable'  # TODO: Calculate trend from time series
        })

    return {
        "regions": regions,
        "total_count": len(regions),
        "risk_summary": {
            "climate": {
                "ALERT": len(df[df['cdi_category'] == 'ALERT']),
                "WARNING": len(df[df['cdi_category'] == 'WARNING']),
                "WATCH": len(df[df['cdi_category'] == 'WATCH']),
                "NORMAL": len(df[df['cdi_category'] == 'NORMAL'])
            },
            "conflict": {
                "EXTREME": len(df[df['risk_category'] == 'EXTREME']),
                "VERY HIGH": len(df[df['risk_category'] == 'VERY HIGH']),
                "HIGH": len(df[df['risk_category'] == 'HIGH']),
                "MODERATE": len(df[df['risk_category'] == 'MODERATE']),
                "LOW": len(df[df['risk_category'] == 'LOW'])
            }
        }
    }


@router.get("/monthly-trend")
async def get_monthly_trend():
    """
    ✅ NEW: Get real monthly conflict trend data from ACLED
    Returns monthly event and fatality counts
    """
    try:
        # ✅ Load real ACLED data
        df = pd.read_csv(ACLED_DATA)

        # ✅ Parse dates and group by month
        df['event_date'] = pd.to_datetime(df['WEEK'], errors='coerce')
        df['year_month'] = df['event_date'].dt.to_period('M')

        # ✅ Aggregate: count events, sum fatalities per month
        monthly = df.groupby('year_month').agg({
            'EVENTS': 'sum',
            'FATALITIES': 'sum'
        }).reset_index()

        # ✅ Rename columns
        monthly.columns = ['month', 'events', 'fatalities']
        
        # ✅ Convert to string format (YYYY-MM)
        monthly['month'] = monthly['month'].astype(str)
        monthly['fatalities'] = monthly['fatalities'].fillna(0).astype(int)

        # ✅ Calculate summary
        summary = {
            "total_months": len(monthly),
            "avg_monthly_events": float(monthly['events'].mean()),
            "avg_monthly_fatalities": float(monthly['fatalities'].mean()),
            "trend": "increasing" if len(monthly) > 1 and monthly['events'].iloc[-1] > monthly['events'].iloc[0] else "decreasing"
        }

        return {
            "data": monthly.to_dict('records'),
            "summary": summary
        }
        
    except FileNotFoundError:
        return {"data": [], "summary": {"error": "ACLED data not found"}}
    except Exception as e:
        return {"data": [], "summary": {"error": str(e)}}


# ==================== BACKWARD COMPATIBILITY ====================
# For reports.py that imports load_data()
def load_data():
    """
    Legacy function for backward compatibility with reports.py
    Returns ACLED data with causes
    """
    try:
        return pd.read_csv(ACLED_DATA)
    except FileNotFoundError:
        return pd.DataFrame()

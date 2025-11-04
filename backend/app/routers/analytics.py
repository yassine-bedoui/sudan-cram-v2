from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter()

# Path to the processed data
DATA_PATH = Path(__file__).parent.parent / "data" / "processed" / "acled_with_causes.csv"

def load_data():
    """Load and prepare the ACLED data"""
    try:
        df = pd.read_csv(DATA_PATH)
        return df
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Data file not found")

def calculate_risk_score(events, fatalities, max_events, max_fatalities):
    """Calculate risk score on 0-10 scale"""
    if max_events == 0 or max_fatalities == 0:
        return 0
    normalized_events = events / max_events
    normalized_fatalities = fatalities / max_fatalities
    return round((normalized_events * 5) + (normalized_fatalities * 5), 2)

def get_risk_category(score):
    """Categorize risk score"""
    if score >= 7.5:
        return "SEVERE"
    elif score >= 5.0:
        return "HIGH"
    elif score >= 2.5:
        return "MEDIUM"
    else:
        return "LOW"

@router.get("/analytics")
async def get_analytics():
    """Get comprehensive analytics data"""
    df = load_data()
    
    # Group by region
    regional_stats = df.groupby('ADMIN1').agg({
        'EVENTS': 'sum',
        'FATALITIES': 'sum'
    }).reset_index()
    
    # Calculate risk scores
    max_events = regional_stats['EVENTS'].max()
    max_fatalities = regional_stats['FATALITIES'].max()
    
    regional_stats['risk_score'] = regional_stats.apply(
        lambda row: calculate_risk_score(
            row['EVENTS'], 
            row['FATALITIES'], 
            max_events, 
            max_fatalities
        ),
        axis=1
    )
    
    regional_stats['risk_category'] = regional_stats['risk_score'].apply(get_risk_category)
    
    # Sort by risk score descending
    regional_stats = regional_stats.sort_values('risk_score', ascending=False)
    
    # Summary statistics
    total_events = int(df['EVENTS'].sum())
    total_fatalities = int(df['FATALITIES'].sum())
    avg_risk = round(regional_stats['risk_score'].mean(), 2)
    highest_risk_region = regional_stats.iloc[0]['ADMIN1']
    
    # Monthly trend
    df['WEEK'] = pd.to_datetime(df['WEEK'])
    df['month'] = df['WEEK'].dt.to_period('M')
    
    monthly_stats = df.groupby('month').agg({
        'EVENTS': 'sum',
        'FATALITIES': 'sum'
    }).reset_index()
    
    monthly_stats['month'] = monthly_stats['month'].astype(str)
    monthly_stats['avg_risk'] = monthly_stats.apply(
        lambda row: calculate_risk_score(
            row['EVENTS'],
            row['FATALITIES'],
            monthly_stats['EVENTS'].max(),
            monthly_stats['FATALITIES'].max()
        ),
        axis=1
    )
    
    # Risk distribution
    risk_distribution = regional_stats['risk_category'].value_counts().to_dict()
    
    # Top 10 regions
    top_regions = regional_stats.head(10).to_dict('records')
    
    # Regional data for charts (top 15)
    regional_data = regional_stats.head(15).to_dict('records')
    
    return {
        "summary": {
            "total_events": total_events,
            "total_fatalities": total_fatalities,
            "avg_risk_score": avg_risk,
            "highest_risk_region": highest_risk_region,
            "regions_monitored": len(regional_stats)
        },
        "monthly_trend": monthly_stats.to_dict('records'),
        "regional_data": regional_data,
        "risk_distribution": risk_distribution,
        "top_regions": top_regions
    }


@router.get("/regions")
async def get_regions():
    """Get all regions with detailed stats"""
    df = load_data()
    
    # Group by region
    regional_stats = df.groupby('ADMIN1').agg({
        'EVENTS': 'sum',
        'FATALITIES': 'sum'
    }).reset_index()
    
    # Calculate risk scores
    max_events = regional_stats['EVENTS'].max()
    max_fatalities = regional_stats['FATALITIES'].max()
    
    regional_stats['risk_score'] = regional_stats.apply(
        lambda row: calculate_risk_score(
            row['EVENTS'], 
            row['FATALITIES'], 
            max_events, 
            max_fatalities
        ),
        axis=1
    )
    
    regional_stats['risk_category'] = regional_stats['risk_score'].apply(get_risk_category)
    
    # Calculate trend (compare last 3 months vs previous 3 months)
    df['WEEK'] = pd.to_datetime(df['WEEK'])
    recent_cutoff = df['WEEK'].max() - pd.Timedelta(days=90)
    previous_cutoff = recent_cutoff - pd.Timedelta(days=90)
    
    trends = []
    for region in regional_stats['ADMIN1']:
        region_df = df[df['ADMIN1'] == region]
        recent = region_df[region_df['WEEK'] >= recent_cutoff]['FATALITIES'].sum()
        previous = region_df[(region_df['WEEK'] >= previous_cutoff) & (region_df['WEEK'] < recent_cutoff)]['FATALITIES'].sum()
        
        if previous == 0:
            trend = "stable"
        elif recent > previous * 1.2:
            trend = "increasing"
        elif recent < previous * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"
        
        trends.append(trend)
    
    regional_stats['trend'] = trends
    
    # Sort by risk score descending
    regional_stats = regional_stats.sort_values('risk_score', ascending=False)
    
    # Rename columns for frontend
    regional_stats = regional_stats.rename(columns={
        'ADMIN1': 'region',
        'EVENTS': 'events',
        'FATALITIES': 'fatalities'
    })
    
    return {
        "regions": regional_stats.to_dict('records'),
        "total_count": len(regional_stats),
        "risk_summary": {
            "SEVERE": len(regional_stats[regional_stats['risk_category'] == 'SEVERE']),
            "HIGH": len(regional_stats[regional_stats['risk_category'] == 'HIGH']),
            "MEDIUM": len(regional_stats[regional_stats['risk_category'] == 'MEDIUM']),
            "LOW": len(regional_stats[regional_stats['risk_category'] == 'LOW'])
        }
    }

from fastapi import APIRouter
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def get_analytics() -> Dict[str, Any]:
    """
    Get comprehensive analytics data for charts and visualizations
    """
    
    # Load the ACLED data with conflict causes
    csv_path = Path(__file__).parent.parent / "data" / "processed" / "acled_with_causes.csv"
    
    if not csv_path.exists():
        return _empty_response()
    
    # Load data
    df = pd.read_csv(csv_path)
    
    # Ensure event_date is datetime
    df['event_date'] = pd.to_datetime(df['event_date'])
    
    # Create aggregated summary per region
    region_stats = df.groupby('ADMIN1').agg({
        'ID': 'count',  # Count unique IDs as events
        'FATALITIES': 'sum'
    }).reset_index()
    
    region_stats.columns = ['region', 'events', 'fatalities']
    
    # Calculate simple risk score (normalized events + fatalities)
    max_events = region_stats['events'].max() if region_stats['events'].max() > 0 else 1
    max_fatalities = region_stats['fatalities'].max() if region_stats['fatalities'].max() > 0 else 1
    
    region_stats['risk_score'] = (
        (region_stats['events'] / max_events) * 5 + 
        (region_stats['fatalities'] / max_fatalities) * 5
    )
    
    region_stats = region_stats.sort_values('risk_score', ascending=False)
    
    # Summary statistics
    total_events = int(region_stats['events'].sum())
    total_fatalities = int(region_stats['fatalities'].sum())
    avg_risk = round(float(region_stats['risk_score'].mean()), 2)
    highest_risk_region = region_stats.iloc[0]['region'] if len(region_stats) > 0 else 'N/A'
    regions_monitored = len(region_stats)
    
    # Top 10 regions by risk score
    top_regions = []
    for _, row in region_stats.head(10).iterrows():
        top_regions.append({
            'region': row['region'],
            'risk_score': round(float(row['risk_score']), 1),
            'events': int(row['events']),
            'fatalities': int(row['fatalities'])
        })
    
    # Monthly trend (group by month)
    df['year_month'] = df['event_date'].dt.to_period('M')
    monthly_trend_data = df.groupby('year_month').agg({
        'ID': 'count',
        'FATALITIES': 'sum'
    }).reset_index()
    
    monthly_trend_data.columns = ['year_month', 'events', 'fatalities']
    monthly_trend_data['year_month'] = monthly_trend_data['year_month'].astype(str)
    monthly_trend_data = monthly_trend_data.sort_values('year_month')
    
    # Calculate avg risk for month
    monthly_trend_data['avg_risk'] = (monthly_trend_data['events'] / monthly_trend_data['events'].max() * 5 + 
                                      monthly_trend_data['fatalities'] / monthly_trend_data['fatalities'].max() * 5) / 2
    
    monthly_trend = []
    for _, row in monthly_trend_data.tail(12).iterrows():  # Last 12 months
        # Convert YYYY-MM to readable format
        try:
            date_obj = datetime.strptime(row['year_month'], '%Y-%m')
            month_label = date_obj.strftime('%b %Y')
        except:
            month_label = row['year_month']
        
        monthly_trend.append({
            'month': month_label,
            'events': int(row['events']),
            'fatalities': int(row['fatalities']),
            'avg_risk': round(float(row['avg_risk']), 2)
        })
    
    # Risk level distribution (create categories based on risk_score)
    def categorize_risk(score):
        if score >= 7.5:
            return 'SEVERE'
        elif score >= 5.0:
            return 'HIGH'
        elif score >= 2.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    region_stats['risk_category'] = region_stats['risk_score'].apply(categorize_risk)
    risk_dist = region_stats['risk_category'].value_counts().to_dict()
    risk_distribution = {k: int(v) for k, v in risk_dist.items()}
    
    # Regional comparison data (for grouped bar chart)
    regional_data = []
    for _, row in region_stats.head(15).iterrows():
        regional_data.append({
            'region': row['region'],
            'events': int(row['events']),
            'fatalities': int(row['fatalities']),
            'risk_score': round(float(row['risk_score']), 1)
        })
    
    return {
        "summary": {
            "total_events": total_events,
            "total_fatalities": total_fatalities,
            "avg_risk_score": avg_risk,
            "highest_risk_region": highest_risk_region,
            "regions_monitored": regions_monitored
        },
        "monthly_trend": monthly_trend,
        "regional_data": regional_data,
        "risk_distribution": risk_distribution,
        "top_regions": top_regions
    }


def _empty_response():
    return {
        "summary": {
            "total_events": 0,
            "total_fatalities": 0,
            "avg_risk_score": 0.0,
            "highest_risk_region": "N/A",
            "regions_monitored": 0
        },
        "monthly_trend": [],
        "regional_data": [],
        "risk_distribution": {},
        "top_regions": []
    }

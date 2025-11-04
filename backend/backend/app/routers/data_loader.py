from pathlib import Path
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=1)
def load_acled_data():
    """Load ACLED conflict data - cached for performance"""
    data_path = Path("data/processed/acled_with_causes.csv")
    
    if not data_path.exists():
        raise FileNotFoundError(f"ACLED data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"✅ Loaded {len(df)} ACLED incidents")
    print(f"Columns: {df.columns.tolist()}")
    return df

def get_alerts_from_acled(limit: int = 1000):
    """Generate alerts from ACLED data"""
    df = load_acled_data()
    
    # Get region column
    region_col = None
    for col in ['admin1', 'STATE', 'state', 'region', 'ADMIN1']:
        if col in df.columns:
            region_col = col
            break
    
    if not region_col:
        region_col = df.columns[0]
    
    # Get date column
    date_col = None
    for col in ['date', 'DATE', 'event_date', 'EVENT_DATE']:
        if col in df.columns:
            date_col = col
            break
    
    # Calculate risk scores by region
    df['risk_indicator'] = df['deaths'].fillna(0) / (df['fatalities'].fillna(1) + 1) * 10
    
    region_stats = df.groupby(region_col).agg({
        'data_id': 'count',  # incident count
        'risk_indicator': 'mean',  # avg risk
        'deaths': 'sum'
    }).rename(columns={'data_id': 'event_count', 'risk_indicator': 'risk_score', 'deaths': 'fatalities'})
    
    region_stats = region_stats.sort_values('risk_score', ascending=False).head(limit)
    
    alerts = []
    for region, row in region_stats.iterrows():
        alerts.append({
            'region': str(region),
            'event_count': int(row['event_count']),
            'risk_score': float(min(row['risk_score'], 10)),  # Cap at 10
            'fatalities': int(row['fatalities']),
            'week': '2024-10-24',  # Latest date
            'alert_level': 'SEVERE' if row['risk_score'] > 7 else 'HIGH' if row['risk_score'] > 5 else 'MEDIUM'
        })
    
    return alerts

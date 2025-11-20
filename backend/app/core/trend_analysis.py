import pandas as pd
from sqlalchemy.orm import Session
from typing import Optional

from app.models.gdelt import GDELTEvent  # Ensure this import matches your structure


def load_events_from_db(db: Session, region: Optional[str] = None) -> pd.DataFrame:
    """
    Load historical GDELT events from database, optionally filtered by region (partial case-insensitive match).

    Args:
        db (Session): SQLAlchemy DB session.
        region (str, optional): Partial region name to filter events.

    Returns:
        pd.DataFrame: DataFrame containing the event records.
    """
    query = db.query(GDELTEvent)
    if region:
        # Case-insensitive partial match on region
        query = query.filter(GDELTEvent.region.ilike(f'%{region}%'))

    events = query.all()

    # Convert ORM objects to dicts, excluding SQLAlchemy internal keys
    data = []
    for e in events:
        d = e.__dict__.copy()
        d.pop('_sa_instance_state', None)
        data.append(d)

    df = pd.DataFrame(data)

    if not df.empty and 'event_date' in df.columns:
        df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')

    return df


def calculate_escalation_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate escalation risk scores grouped by location using Goldstein scale trends and event counts.

    Returns a DataFrame with columns:
    ['location', 'escalation_risk', 'risk_level', 'avg_goldstein', 'goldstein_trend', 'event_count',
    'media_mentions', 'recent_change', 'first_seen', 'last_seen']

    Args:
        df (pd.DataFrame): DataFrame of event data.

    Returns:
        pd.DataFrame: DataFrame with risk assessment results.
    """
    if df.empty:
        return pd.DataFrame()

    df['location_clean'] = df['region'].str.strip()

    location_stats = []

    for location in df['location_clean'].unique():
        loc_data = df[df['location_clean'] == location].sort_values('event_date')

        if len(loc_data) < 2:
            continue

        avg_goldstein = loc_data['goldstein_scale'].mean()
        event_count = len(loc_data)
        media_mentions = loc_data['num_mentions'].sum() if 'num_mentions' in loc_data else 0
        goldstein_trend = loc_data['goldstein_scale'].diff().mean()

        split_point = len(loc_data) // 2
        recent_avg = loc_data.iloc[split_point:]['goldstein_scale'].mean()
        older_avg = loc_data.iloc[:split_point]['goldstein_scale'].mean()
        recent_change = recent_avg - older_avg

        risk_score = (
            max(0, -avg_goldstein) * 0.4 +
            max(0, -goldstein_trend) * 0.3 +
            min(10, event_count / 5) * 0.2 +
            max(0, -recent_change) * 0.1
        )

        risk_score = min(risk_score, 10)

        if risk_score >= 7:
            risk_level = "CRITICAL"
        elif risk_score >= 5:
            risk_level = "HIGH"
        elif risk_score >= 3:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        location_stats.append({
            'location': location,
            'escalation_risk': risk_score,
            'risk_level': risk_level,
            'avg_goldstein': avg_goldstein,
            'goldstein_trend': goldstein_trend,
            'event_count': event_count,
            'media_mentions': media_mentions,
            'recent_change': recent_change,
            'first_seen': loc_data['event_date'].min(),
            'last_seen': loc_data['event_date'].max(),
        })

    risk_df = pd.DataFrame(location_stats).sort_values('escalation_risk', ascending=False)
    return risk_df


def generate_hourly_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate hourly Goldstein scale timeline for visualization purposes.

    Returns a DataFrame with columns: ['timestamp', 'avg_goldstein', 'event_count', 'mentions']

    Args:
        df (pd.DataFrame): DataFrame containing events with 'event_date' and related fields.

    Returns:
        pd.DataFrame: Hourly aggregated timeline.
    """
    if df.empty:
        return pd.DataFrame()

    df['hour'] = df['event_date'].dt.floor('H')

    end_time = pd.Timestamp.now().floor('H')
    start_time = end_time - pd.Timedelta(hours=24)
    all_hours = pd.date_range(start=start_time, end=end_time, freq='H')

    agg_dict = {
        'goldstein_scale': 'mean',
        'event_code': 'count',
    }
    if 'num_mentions' in df.columns:
        agg_dict['num_mentions'] = 'sum'

    hourly = df[df['hour'] >= start_time].groupby('hour').agg(agg_dict).reset_index()

    hourly_complete = pd.DataFrame({'hour': all_hours})
    hourly_complete = hourly_complete.merge(hourly, on='hour', how='left')

    hourly_complete['goldstein_scale'] = hourly_complete['goldstein_scale'].fillna(0)
    hourly_complete['event_code'] = hourly_complete['event_code'].fillna(0).astype(int)

    if 'num_mentions' in hourly_complete.columns:
        hourly_complete['num_mentions'] = hourly_complete['num_mentions'].fillna(0).astype(int)
    else:
        hourly_complete['num_mentions'] = 0

    hourly_complete.columns = ['timestamp', 'avg_goldstein', 'event_count', 'mentions']

    return hourly_complete

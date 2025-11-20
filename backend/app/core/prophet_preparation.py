import pandas as pd
from sqlalchemy.orm import Session
from typing import Optional

from app.models.gdelt import GDELTEvent


def prepare_time_series_for_prophet(
    db: Session,
    region: Optional[str] = None,
    target_col: str = 'event_id',
    time_freq: str = 'D'
) -> pd.DataFrame:
    """
    Load historical events from the DB and prepare aggregated time series data
    for Prophet forecasting.

    Args:
        db (Session): SQLAlchemy DB session.
        region (Optional[str]): Region filter (partial match, case-insensitive).
        target_col (str): Column to use as forecast target ('event_id' count by default).
        time_freq (str): Time frequency for aggregation ('D'=daily, 'W'=weekly, 'M'=monthly).

    Returns:
        pd.DataFrame: Prepared DataFrame with columns ['ds', 'y'] suitable for Prophet.
    """
    # Step 1: Query raw events filtered by region
    query = db.query(GDELTEvent)
    if region:
        query = query.filter(GDELTEvent.region.ilike(f"%{region}%"))
    events = query.all()

    # Step 2: Convert to list of dict and then DataFrame
    data = []
    for e in events:
        d = e.__dict__.copy()
        d.pop('_sa_instance_state', None)
        data.append(d)

    df = pd.DataFrame(data)

    if df.empty:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['ds', 'y'])

    # Step 3: Ensure date column is datetime
    if 'event_date' not in df.columns:
        raise ValueError("GDELTEvent objects must have 'event_date' field")

    df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
    df = df[df['event_date'].notna()]

    # Step 4: Aggregate by period and region
    df['ds'] = df['event_date'].dt.to_period(time_freq).dt.to_timestamp()

    # Step 5: Aggregate target column
    if target_col == 'event_id':
        agg_series = df.groupby('ds').size()
    else:
        agg_series = df.groupby('ds')[target_col].sum()

    agg_df = agg_series.reset_index()
    agg_df.rename(columns={agg_df.columns[0]: "ds", agg_df.columns[1]: "y"}, inplace=True)

    # Step 6: Fill missing dates in the time series with zeros
    full_date_index = pd.date_range(start=agg_df['ds'].min(), end=agg_df['ds'].max(), freq=time_freq)
    agg_df = agg_df.set_index('ds').reindex(full_date_index, fill_value=0).rename_axis('ds').reset_index()

    return agg_df

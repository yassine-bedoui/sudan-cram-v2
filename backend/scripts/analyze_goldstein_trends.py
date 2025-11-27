# scripts/gdelt/analyze_goldstein_trends.py
"""
Analyze Goldstein Scale trends to detect escalation.

NEW:
- Prefer reading from Postgres `gdelt_events` table (live pipeline).
- Fallback to the latest country-specific CSV under data/gdelt/ if DB is not available.
- Outputs the same processed CSVs used by the FastAPI router, now per-country:
    - data/processed/goldstein_escalation_risk_<ISO3>_YYYYMMDD.csv
    - data/processed/goldstein_hourly_timeline_<ISO3>_YYYYMMDD.csv
"""

import glob
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_COUNTRY_ISO3 = os.getenv("COUNTRY_ISO3", "SDN").upper()


# -------------------------------------------------------------------
# DB helpers
# -------------------------------------------------------------------


def get_engine():
    """
    Create a SQLAlchemy engine.

    Uses DATABASE_URL if set, otherwise falls back to the DSN pattern
    you already use elsewhere (populate_db.py).
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db",
    )
    return create_engine(db_url)


def load_gdelt_from_db(
    hours_back: int = 72, country_iso3: str = DEFAULT_COUNTRY_ISO3
) -> pd.DataFrame:
    """
    Load recent GDELT events from Postgres and return a DataFrame
    with the columns expected by the analysis functions:

        date, location, goldstein, event_code, num_mentions

    We derive:
        - date       <- gdelt_events.event_date
        - location   <- gdelt_events.region
        - goldstein  <- gdelt_events.goldstein_scale
        - event_code <- gdelt_events.event_code
        - num_mentions <- 1 (DB schema doesn't store NumMentions yet)

    Filtered by country_iso3.
    """
    engine = get_engine()
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)
    iso3 = country_iso3.upper()

    with engine.connect() as conn:
        # Pull the raw events
        df = pd.read_sql(
            text(
                """
                SELECT
                    event_date AS date,
                    region     AS location,
                    event_code,
                    goldstein_scale AS goldstein,
                    avg_tone
                FROM gdelt_events
                WHERE country_iso3 = :country_iso3
                  AND event_date >= :cutoff
                ORDER BY event_date
                """
            ),
            conn,
            params={"cutoff": cutoff, "country_iso3": iso3},
        )

    if df.empty:
        print(
            f"⚠️ No GDELT rows found in DB within the last {hours_back} hours "
            f"for {iso3} (cutoff={cutoff.isoformat()})"
        )
        return df

    # Ensure datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # For now we approximate num_mentions as 1 per event
    df["num_mentions"] = 1

    print(
        f"✅ Loaded {len(df)} GDELT events from DB for {iso3} "
        f"({df['date'].min()} → {df['date'].max()})"
    )
    return df


# -------------------------------------------------------------------
# Legacy CSV loader (fallback)
# -------------------------------------------------------------------


def load_latest_gdelt_csv(country_iso3: str = DEFAULT_COUNTRY_ISO3) -> pd.DataFrame:
    """
    Legacy loader: load the most recent country-specific GDELT events CSV
    from data/gdelt/<iso3>_events_*.csv.

    Expects columns:
        date, location, goldstein, event_code, num_mentions, ...
    """
    iso3 = country_iso3.upper()
    gdelt_files = glob.glob(f"data/gdelt/{iso3.lower()}_events_*.csv")

    # Backwards compatibility with old Sudan-only naming
    if not gdelt_files and iso3 == "SDN":
        gdelt_files = glob.glob("data/gdelt/sudan_events_*.csv")

    if not gdelt_files:
        raise FileNotFoundError(
            f"No GDELT data found in DB or CSVs for {iso3}. "
            "Run the GDELT ETL first."
        )

    latest_file = max(gdelt_files, key=os.path.getctime)
    print(f"📂 Falling back to CSV for {iso3}. Loading: {latest_file}")

    df = pd.read_csv(latest_file)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_latest_gdelt_data(
    hours_back: int = 72, country_iso3: str = DEFAULT_COUNTRY_ISO3
) -> pd.DataFrame:
    """
    Main loader:

    1. Try Postgres (gdelt_events) for last `hours_back` hours for country_iso3.
    2. If that fails (connection error, missing table, etc.), fall back to CSV.
    """
    iso3 = country_iso3.upper()
    try:
        df = load_gdelt_from_db(hours_back=hours_back, country_iso3=iso3)
        if not df.empty:
            return df
        else:
            print("ℹ️ DB returned no rows – will try CSV fallback.")
    except Exception as e:
        print(f"⚠️ Could not load GDELT from DB: {e}")
        print("   Falling back to latest CSV in data/gdelt/ ...")

    # Fallback
    return load_latest_gdelt_csv(country_iso3=iso3)


# -------------------------------------------------------------------
# Analysis functions (mostly unchanged)
# -------------------------------------------------------------------


def calculate_escalation_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate escalation risk scores by location
    Based on Goldstein trends, event frequency, and media attention.
    """
    print("\n🔍 Analyzing escalation patterns...\n")

    # Clean location names
    df["location_clean"] = df["location"].astype(str).str.strip()

    location_stats = []

    for location in df["location_clean"].unique():
        loc_data = df[df["location_clean"] == location].sort_values("date")

        if len(loc_data) < 2:
            continue

        avg_goldstein = loc_data["goldstein"].mean()
        event_count = len(loc_data)
        media_mentions = loc_data.get("num_mentions", pd.Series([1] * len(loc_data))).sum()

        # Goldstein trend (negative = escalating)
        goldstein_trend = loc_data["goldstein"].diff().mean()

        # Recent vs older
        split_point = len(loc_data) // 2
        recent_avg = loc_data.iloc[split_point:]["goldstein"].mean()
        older_avg = loc_data.iloc[:split_point]["goldstein"].mean()
        change = recent_avg - older_avg

        # Escalation Risk Score (0-10)
        risk_score = (
            max(0, -avg_goldstein) * 0.4 +        # Negative Goldstein = conflict
            max(0, -goldstein_trend) * 0.3 +      # Declining trend = escalation
            min(10, event_count / 5) * 0.2 +      # More events
            max(0, -change) * 0.1                 # Getting worse over time
        )

        if risk_score >= 7:
            risk_level = "CRITICAL"
        elif risk_score >= 5:
            risk_level = "HIGH"
        elif risk_score >= 3:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        location_stats.append(
            {
                "location": location,
                "escalation_risk": min(10, risk_score),
                "risk_level": risk_level,
                "avg_goldstein": avg_goldstein,
                "goldstein_trend": goldstein_trend,
                "event_count": event_count,
                "media_mentions": media_mentions,
                "recent_change": change,
                "first_seen": loc_data["date"].min(),
                "last_seen": loc_data["date"].max(),
            }
        )

    risk_df = pd.DataFrame(location_stats).sort_values(
        "escalation_risk", ascending=False
    )

    return risk_df


def generate_hourly_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate hourly Goldstein timeline for charts (24h by default).
    """
    # Floor timestamps to nearest hour
    df["hour"] = df["date"].dt.floor("H")

    # Create complete 24-hour range
    end_time = pd.Timestamp.now().floor("H")
    start_time = end_time - pd.Timedelta(hours=24)
    all_hours = pd.date_range(start=start_time, end=end_time, freq="H")

    # Group by hour and aggregate
    hourly = (
        df[df["hour"] >= start_time]
        .groupby("hour")
        .agg(
            {
                "goldstein": "mean",
                "event_code": "count",
                "num_mentions": "sum",
            }
        )
        .reset_index()
    )

    # Merge with complete range
    hourly_complete = pd.DataFrame({"hour": all_hours})
    hourly_complete = hourly_complete.merge(hourly, on="hour", how="left")

    # Fill missing hours with 0
    hourly_complete["goldstein"] = hourly_complete["goldstein"].fillna(0)
    hourly_complete["event_code"] = (
        hourly_complete["event_code"].fillna(0).astype(int)
    )
    hourly_complete["num_mentions"] = (
        hourly_complete["num_mentions"].fillna(0).astype(int)
    )

    hourly_complete.columns = ["timestamp", "avg_goldstein", "event_count", "mentions"]

    return hourly_complete


# -------------------------------------------------------------------
# Main entrypoint
# -------------------------------------------------------------------


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    country_iso3 = DEFAULT_COUNTRY_ISO3
    print("=" * 70)
    print(f"GOLDSTEIN SCALE TREND ANALYSIS (DB-first) – {country_iso3}")
    print("=" * 70)

    # Load data (DB preferred, fallback to CSV)
    df = load_latest_gdelt_data(hours_back=72, country_iso3=country_iso3)

    if df.empty:
        print("❌ No GDELT data available for analysis. Aborting.")
        return pd.DataFrame(), pd.DataFrame()

    print(f"✅ Loaded {len(df)} events")
    print(f"   Date range: {df['date'].min()} → {df['date'].max()}\n")

    # Calculate escalation risks
    risk_df = calculate_escalation_risk(df)

    # Save results
    os.makedirs("data/processed", exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")

    risk_file = f"data/processed/goldstein_escalation_risk_{country_iso3}_{today_str}.csv"
    risk_df.to_csv(risk_file, index=False)

    # Display results
    print("=" * 70)
    print("🚨 ESCALATION RISK RANKING (Top 10)")
    print("=" * 70)

    for i, row in risk_df.head(10).iterrows():
        print(f"\n{i+1}. {row['location']}")
        print(
            f"   Risk Score:      {row['escalation_risk']:.1f}/10 [{row['risk_level']}]"
        )
        print(
            f"   Avg Goldstein:   {row['avg_goldstein']:.2f} (negative = conflict)"
        )
        print(
            f"   Trend:           {row['goldstein_trend']:.2f} (negative = worsening)"
        )
        print(f"   Events:          {row['event_count']} events")
        print(f"   Media mentions:  {row['media_mentions']}")
        print(f"   Recent change:   {row['recent_change']:.2f}")

    # Generate hourly timeline
    timeline = generate_hourly_timeline(df)
    timeline_file = (
        f"data/processed/goldstein_hourly_timeline_{country_iso3}_{today_str}.csv"
    )
    timeline.to_csv(timeline_file, index=False)

    print("\n" + "=" * 70)
    print("📊 KEY INSIGHTS")
    print("=" * 70)

    critical = risk_df[risk_df["risk_level"] == "CRITICAL"]
    high = risk_df[risk_df["risk_level"] == "HIGH"]

    print(f"Critical risk locations:  {len(critical)}")
    print(f"High risk locations:      {len(high)}")
    print(f"Total locations tracked:  {len(risk_df)}")
    print(f"\nHourly timeline points:   {len(timeline)} hours")

    print(f"\n💾 Files saved:")
    print(f"   • {risk_file}")
    print(f"   • {timeline_file}")

    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

    return risk_df, timeline


if __name__ == "__main__":
    risk_df, timeline = main()

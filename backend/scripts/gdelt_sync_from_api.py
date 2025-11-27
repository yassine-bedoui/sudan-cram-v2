# backend/scripts/gdelt_sync_from_api.py

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text

# Robust import so the script works as:
#   python -m backend.scripts.gdelt_sync_from_api   (from repo root)
# and also when run directly from backend/ if PYTHONPATH is set.
try:
    from app.services.gdelt_client import GDELTClient, GDELTApiError, GDELTEventRecord
except ModuleNotFoundError:  # when imported as backend.scripts.*
    from backend.app.services.gdelt_client import (  # type: ignore
        GDELTClient,
        GDELTApiError,
        GDELTEventRecord,
    )

# Country configuration (centralised)
try:
    from app.config.countries import get_country_config
except ModuleNotFoundError:
    from backend.app.config.countries import get_country_config  # type: ignore


# --------------------------------------------------------------------
# DB connection helper
# --------------------------------------------------------------------

def get_engine():
    """
    Build a SQLAlchemy Engine.

    - Prefer DATABASE_URL env var
    - Fallback to the hardcoded DSN you already use in populate_db.py
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db",
    )
    return create_engine(db_url)


# --------------------------------------------------------------------
# Helpers: find last event, build DataFrame, upsert
# --------------------------------------------------------------------

def get_last_gdelt_event_timestamp(engine, country_iso3: str) -> Optional[datetime]:
    """
    Get the most recent event_date present in gdelt_events for a given country_iso3.

    Returns:
        A Python datetime (naive or aware depending on DB driver) or None.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT max(event_date) FROM gdelt_events WHERE country_iso3 = :iso3"),
            {"iso3": country_iso3},
        )
        max_ts = result.scalar()

    return max_ts


def records_to_dataframe(
    records: List[GDELTEventRecord],
    country_iso3: str,
) -> pd.DataFrame:
    """
    Convert a list of GDELTEventRecord objects into a pandas DataFrame
    matching the gdelt_events table schema.

    gdelt_events columns (from app/models/gdelt.py), extended with country_iso3:

        id = Column(Integer, primary_key=True, index=True)
        event_id = Column(String(50), unique=True, nullable=False)
        country_iso3 = Column(String(3), nullable=False, index=True)
        event_date = Column(DateTime, nullable=False, index=True)

        region = Column(String(100), index=True)
        latitude = Column(Float)
        longitude = Column(Float)

        event_code = Column(String(10))
        quad_class = Column(Integer)

        actor1_name = Column(String(200))
        actor2_name = Column(String(200))

        goldstein_scale = Column(Float)
        avg_tone = Column(Float)

        created_at = Column(DateTime, server_default=func.now())
    """
    if not records:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for rec in records:
        # Drop tzinfo so it fits neatly into TIMESTAMP WITHOUT TIME ZONE
        event_dt = rec.event_date
        if event_dt.tzinfo is not None:
            event_dt = event_dt.astimezone(timezone.utc).replace(tzinfo=None)

        rows.append(
            {
                "event_id": rec.event_id,
                "country_iso3": country_iso3,
                "event_date": event_dt,
                "region": rec.region,
                "latitude": rec.latitude,
                "longitude": rec.longitude,
                "event_code": rec.event_code,
                "quad_class": rec.quad_class,
                "actor1_name": rec.actor1_name,
                "actor2_name": rec.actor2_name,
                "goldstein_scale": rec.goldstein_scale,
                "avg_tone": rec.avg_tone,
            }
        )

    df = pd.DataFrame(rows)

    # Defensive type casting
    if not df.empty:
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
        for col in ("latitude", "longitude", "goldstein_scale", "avg_tone"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "quad_class" in df.columns:
            df["quad_class"] = (
                pd.to_numeric(df["quad_class"], errors="coerce").astype("Int64")
            )

    return df


def upsert_gdelt_events(engine, df: pd.DataFrame) -> int:
    """
    Insert GDELT events into gdelt_events table, skipping duplicates by event_id.

    Implementation:
      - Create a temporary table
      - Bulk-load DataFrame into temp table via pandas.to_sql
      - INSERT ... ON CONFLICT (event_id) DO NOTHING into the real table

    Returns:
        Number of rows successfully inserted (approximate; rowcount may be -1 for some drivers).
    """
    if df.empty:
        return 0

    tmp_table = "gdelt_events_tmp"

    with engine.begin() as conn:
        # 1) Drop temp table if it already exists
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_table};"))

        # 2) Create temp table with matching columns (minus id/created_at)
        conn.execute(
            text(
                f"""
                CREATE TEMP TABLE {tmp_table} (
                    event_id TEXT,
                    country_iso3 TEXT,
                    event_date TIMESTAMP,
                    region TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    event_code TEXT,
                    quad_class INTEGER,
                    actor1_name TEXT,
                    actor2_name TEXT,
                    goldstein_scale DOUBLE PRECISION,
                    avg_tone DOUBLE PRECISION
                ) ON COMMIT DROP;
                """
            )
        )

        # 3) Load DataFrame into temp table
        df.to_sql(tmp_table, conn, if_exists="append", index=False)

        # 4) Insert into real table with ON CONFLICT DO NOTHING on event_id
        result = conn.execute(
            text(
                f"""
                INSERT INTO gdelt_events (
                    event_id,
                    country_iso3,
                    event_date,
                    region,
                    latitude,
                    longitude,
                    event_code,
                    quad_class,
                    actor1_name,
                    actor2_name,
                    goldstein_scale,
                    avg_tone
                )
                SELECT
                    event_id,
                    country_iso3,
                    event_date,
                    region,
                    latitude,
                    longitude,
                    event_code,
                    quad_class,
                    actor1_name,
                    actor2_name,
                    goldstein_scale,
                    avg_tone
                FROM {tmp_table}
                ON CONFLICT (event_id) DO NOTHING;
                """
            )
        )

        inserted = (
            result.rowcount
            if result.rowcount is not None and result.rowcount >= 0
            else 0
        )

    return inserted


# --------------------------------------------------------------------
# Main sync logic
# --------------------------------------------------------------------

def sync_gdelt_for_country(
    country_iso3: str,
    days_back_if_empty: int = 7,
) -> None:
    """
    Incrementally sync GDELT events for a given country into gdelt_events.

    Logic:
      1. Look up the latest event_date in gdelt_events for that country_iso3.
      2. If table is empty for this country:
            - Start from now - `days_back_if_empty` days.
         Else:
            - Start from that last event_date (we rely on ON CONFLICT to skip duplicates).
      3. End at current UTC time.
      4. Use GDELTClient to fetch events for [start, end].
      5. Upsert into gdelt_events.

    Args:
        country_iso3: ISO3 code of the country (e.g. "SDN", "SOM").
        days_back_if_empty: How far back to go if the country has no data yet.
    """
    cfg = get_country_config(country_iso3)
    country_code = cfg.gdelt_country_code  # ActionGeo_CountryCode, e.g. "SU" or "SO"

    engine = get_engine()
    client = GDELTClient()

    # 1) Determine date window for this specific country
    last_ts = get_last_gdelt_event_timestamp(engine, cfg.iso3)

    now_utc = datetime.now(timezone.utc)

    if last_ts is None:
        # Fresh table for this country: backfill a recent window (default: 7 days)
        start_utc = now_utc - timedelta(days=days_back_if_empty)
        print(f"ℹ️ No existing GDELT events in DB for {cfg.iso3}.")
        print(
            f"   Backfilling last {days_back_if_empty} days: "
            f"{start_utc.date()} -> {now_utc.date()} (inclusive)"
        )
    else:
        # We may get a naive datetime from DB; treat it as UTC
        if last_ts.tzinfo is None:
            last_ts_utc = last_ts.replace(tzinfo=timezone.utc)
        else:
            last_ts_utc = last_ts.astimezone(timezone.utc)

        start_utc = last_ts_utc
        print(
            f"ℹ️ Latest GDELT event in DB for {cfg.iso3}: {last_ts_utc.isoformat()} "
            f"– requesting events from this timestamp onward."
        )

    end_utc = now_utc
    print(
        f"🔍 Fetching GDELT events for {cfg.iso3} "
        f"(GDELT country code: {country_code}) "
        f"from {start_utc.isoformat()} to {end_utc.isoformat()}..."
    )

    # 2) Fetch events from GDELT
    try:
        records = client.fetch_events_for_window(
            start=start_utc,
            end=end_utc,
            country_code=country_code,
        )
    except GDELTApiError as e:
        print("❌ GDELT API error while fetching events:")
        print(f"   {e}")
        print("   This is most likely a network or remote issue.")
        return

    if not records:
        print(
            f"✅ GDELT sync completed: no events returned for this window "
            f"for {cfg.iso3}."
        )
        return

    # 3) Transform to DataFrame
    df = records_to_dataframe(records, country_iso3=cfg.iso3)
    print(f"📦 Downloaded {len(df)} GDELT rows after transformation.")

    # 4) Upsert into DB
    inserted = upsert_gdelt_events(engine, df)
    duplicates = len(df) - inserted

    print("------------------------------------------------------------")
    print(f" Total rows from GDELT : {len(df)}")
    print(f" Inserted new events   : {inserted}")
    print(f" Likely duplicates     : {duplicates} (skipped via ON CONFLICT)")
    print("✅ GDELT sync complete.")
    print("============================================================")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Sync recent GDELT events into gdelt_events for a given country."
    )
    parser.add_argument(
        "--country",
        "-c",
        help="ISO3 country code (e.g. SDN, SOM)",
        default=os.getenv("GDELT_COUNTRY_ISO3", "SDN"),
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=int(os.getenv("GDELT_SYNC_DAYS_BACK", "7")),
        help="If the DB is empty for this country, how many days back to start.",
    )

    args = parser.parse_args()
    iso3 = (args.country or "SDN").upper()
    days_back = args.days_back

    sync_gdelt_for_country(country_iso3=iso3, days_back_if_empty=days_back)

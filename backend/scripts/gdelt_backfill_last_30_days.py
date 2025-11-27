# backend/scripts/gdelt_backfill_last_30_days.py
"""
Backfill GDELT 2.0 event data for a single country for the last 30 days.

- Downloads 15-minute GDELT 2.0 "export" snapshots:
    http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMM00.export.CSV.zip

- Filters to events where ActionGeo_CountryCode == cfg.gdelt_country_code.
- Transforms into your gdelt_events schema:
    event_id, country_iso3, event_date, region, latitude, longitude,
    event_code, quad_class, goldstein_scale, avg_tone

- Upserts into Postgres with ON CONFLICT (event_id) DO NOTHING.

Usage:
    GDELT_COUNTRY_ISO3=SOM python -m backend.scripts.gdelt_backfill_last_30_days
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import List, Optional

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from zipfile import ZipFile

# Country configuration (centralised)
try:
    from app.config.countries import get_country_config
except ModuleNotFoundError:
    from backend.app.config.countries import get_country_config  # type: ignore


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

GDELT_ARCHIVE_BASE = "http://data.gdeltproject.org/gdeltv2"


def get_engine():
    """
    Create SQLAlchemy engine.

    Uses DATABASE_URL env var if set, otherwise falls back to the same DSN
    used in your other scripts (populate_db.py, etc.).
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db",
    )
    return create_engine(db_url)


# ---------------------------------------------------------------------
# GDELT archive helpers
# ---------------------------------------------------------------------

def iter_15min_slots(start: datetime, end: datetime):
    """
    Yield 15-minute timestamps between [start, end) in UTC.
    """
    # Align to previous 15-min boundary
    minute_block = (start.minute // 15) * 15
    current = start.replace(minute=minute_block, second=0, microsecond=0)

    while current < end:
        yield current
        current += timedelta(minutes=15)


def build_export_url(ts: datetime) -> str:
    """
    Build URL for a GDELT 2.0 export snapshot at a given timestamp.

    Example:
        2025-11-23 12:00 UTC -> 20251123120000.export.CSV.zip
    """
    return f"{GDELT_ARCHIVE_BASE}/{ts:%Y%m%d%H%M00}.export.CSV.zip"


def fetch_export_snapshot(ts: datetime, country_code: str) -> Optional[pd.DataFrame]:
    """
    Download and parse a single GDELT 2.0 export snapshot for a given timestamp.

    Returns:
        pandas.DataFrame with a subset of columns, filtered to the given country,
        or None if snapshot is missing / fails to download.

    Notes:
        - Files are tab-delimited text (.CSV extension but TSV content).
        - GDELT export files have no header row; we map by column index.
    """
    url = build_export_url(ts)
    print(f"    • Fetching snapshot: {url}")

    try:
        resp = requests.get(url, timeout=60)
    except requests.RequestException as e:
        print(f"      ! Request error for {url}: {e}")
        return None

    if resp.status_code == 404:
        # Snapshot may not exist yet; skip silently
        print("      ↪ 404 (snapshot not found) – skipping.")
        return None

    if resp.status_code != 200:
        body = resp.text[:200].replace("\n", " ")
        print(f"      ! Non-200 status: {resp.status_code} – {body}...")
        return None

    # Decompress ZIP in memory
    try:
        with ZipFile(BytesIO(resp.content)) as zf:
            # export snapshots contain a single file
            inner_names = zf.namelist()
            if not inner_names:
                print("      ! Empty ZIP (no inner files) – skipping.")
                return None

            inner_name = inner_names[0]
            with zf.open(inner_name) as f:
                # Map by column index (0-based) as per GDELT 2.0 schema
                # We only load the columns we actually need:
                #
                #  0: GlobalEventID
                #  1: SQLDATE (yyyymmdd)
                #  6: Actor1Name
                # 16: Actor2Name
                # 26: EventCode
                # 29: QuadClass
                # 30: GoldsteinScale
                # 32: NumMentions
                # 34: AvgTone
                # 52: ActionGeo_FullName
                # 53: ActionGeo_CountryCode
                # 54: ActionGeo_ADM1Code
                # 56: ActionGeo_Lat
                # 57: ActionGeo_Long
                usecols = [
                    0,   # GlobalEventID
                    1,   # SQLDATE
                    6,   # Actor1Name
                    16,  # Actor2Name
                    26,  # EventCode
                    29,  # QuadClass
                    30,  # GoldsteinScale
                    32,  # NumMentions
                    34,  # AvgTone
                    52,  # ActionGeo_FullName
                    53,  # ActionGeo_CountryCode
                    54,  # ActionGeo_ADM1Code
                    56,  # ActionGeo_Lat
                    57,  # ActionGeo_Long
                ]

                df = pd.read_csv(
                    f,
                    sep="\t",
                    header=None,
                    usecols=usecols,
                    dtype=str,
                    engine="python",
                )

        # Rename columns
        df.columns = [
            "GlobalEventID",
            "SQLDATE",
            "Actor1Name",
            "Actor2Name",
            "EventCode",
            "QuadClass",
            "GoldsteinScale",
            "NumMentions",
            "AvgTone",
            "ActionGeo_FullName",
            "ActionGeo_CountryCode",
            "ActionGeo_ADM1Code",
            "ActionGeo_Lat",
            "ActionGeo_Long",
        ]

        # Filter to requested country (ActionGeo_CountryCode)
        df = df[df["ActionGeo_CountryCode"] == country_code]

        if df.empty:
            return None

        return df

    except Exception as e:
        print(f"      ! Error parsing snapshot for {ts}: {e}")
        return None


def fetch_gdelt_last_30_days(country_iso3: str) -> pd.DataFrame:
    """
    Collect GDELT events for a given country over the last 30 days
    by walking 15-minute snapshots and concatenating.

    Returns:
        DataFrame of raw GDELT rows (subset of columns) for that country.
    """
    cfg = get_country_config(country_iso3)
    country_code = cfg.gdelt_country_code  # e.g. "SU" for Sudan, "SO" for Somalia

    now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_utc = now_utc - timedelta(days=30)

    print(
        f" Time window (UTC): {start_utc.isoformat()}  ->  {now_utc.isoformat()}"
    )
    print(f" Country ISO3: {cfg.iso3}, GDELT country code: {country_code}")
    print("============================================================\n")

    all_chunks: List[pd.DataFrame] = []

    # We iterate by day for nicer logging & memory control
    current_day = start_utc.date()
    end_day = now_utc.date()

    while current_day <= end_day:
        day_start = datetime(
            current_day.year,
            current_day.month,
            current_day.day,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        day_end = day_start + timedelta(days=1)
        if day_end > now_utc:
            day_end = now_utc

        print(f"🔍 Fetching GDELT events for {current_day} ...")

        daily_chunks: List[pd.DataFrame] = []

        for ts in iter_15min_slots(day_start, day_end):
            df_slot = fetch_export_snapshot(ts, country_code=country_code)
            if df_slot is not None and not df_slot.empty:
                daily_chunks.append(df_slot)

        if daily_chunks:
            day_df = pd.concat(daily_chunks, ignore_index=True)
            print(f"    ✅ {len(day_df):,} rows for {current_day}")
            all_chunks.append(day_df)
        else:
            print(f"    … No events found for {current_day}")

        current_day += timedelta(days=1)

    if not all_chunks:
        return pd.DataFrame()

    return pd.concat(all_chunks, ignore_index=True)


# ---------------------------------------------------------------------
# Transform → gdelt_events schema
# ---------------------------------------------------------------------

def transform_gdelt_rows_to_events(
    df: pd.DataFrame,
    country_iso3: str,
) -> pd.DataFrame:
    """
    Transform raw GDELT rows into the schema expected by gdelt_events table.

    Output columns:
        event_id, country_iso3, event_date, region, latitude, longitude,
        event_code, quad_class, goldstein_scale, avg_tone
    """
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "event_id",
                "country_iso3",
                "event_date",
                "region",
                "latitude",
                "longitude",
                "event_code",
                "quad_class",
                "goldstein_scale",
                "avg_tone",
            ]
        )

    out = pd.DataFrame()

    # Event ID: use GlobalEventID, prefixed for clarity
    out["event_id"] = "gdelt-" + df["GlobalEventID"].astype(str)

    # Country ISO3: fixed for the entire run
    out["country_iso3"] = country_iso3

    # Event date: parse SQLDATE (yyyymmdd)
    out["event_date"] = pd.to_datetime(
        df["SQLDATE"], format="%Y%m%d", errors="coerce"
    ).dt.date

    # Region: use ADM1 if present, otherwise fall back to full name
    adm1 = df["ActionGeo_ADM1Code"].fillna("").astype(str)
    full_name = df["ActionGeo_FullName"].fillna("").astype(str)
    out["region"] = adm1.where(adm1.str.len() > 0, full_name)

    # Coordinates
    out["latitude"] = pd.to_numeric(df["ActionGeo_Lat"], errors="coerce")
    out["longitude"] = pd.to_numeric(df["ActionGeo_Long"], errors="coerce")

    # Event metadata
    out["event_code"] = df["EventCode"].astype(str)
    out["quad_class"] = pd.to_numeric(df["QuadClass"], errors="coerce").astype("Int64")
    out["goldstein_scale"] = pd.to_numeric(df["GoldsteinScale"], errors="coerce")
    out["avg_tone"] = pd.to_numeric(df["AvgTone"], errors="coerce")

    return out


# ---------------------------------------------------------------------
# Upsert into Postgres
# ---------------------------------------------------------------------

def upsert_gdelt_events(engine, df_events: pd.DataFrame) -> int:
    """
    Upsert events into gdelt_events table, skipping duplicates on event_id.

    We create a TEMP TABLE, bulk-insert the DataFrame, then insert
    into the real table with ON CONFLICT (event_id) DO NOTHING.

    IMPORTANT: This matches the actual gdelt_events schema:
        event_id, country_iso3, event_date, region, latitude, longitude,
        event_code, quad_class, goldstein_scale, avg_tone
    """
    if df_events.empty:
        return 0

    tmp_table = "gdelt_events_tmp"

    with engine.begin() as conn:
        # Drop temp table if exists
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_table};"))

        # Create temp table
        conn.execute(
            text(
                f"""
                CREATE TEMP TABLE {tmp_table} (
                    event_id TEXT,
                    country_iso3 TEXT,
                    event_date DATE,
                    region TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    event_code TEXT,
                    quad_class INTEGER,
                    goldstein_scale DOUBLE PRECISION,
                    avg_tone DOUBLE PRECISION
                ) ON COMMIT DROP;
                """
            )
        )

        # Bulk-insert into temp table
        df_events.to_sql(tmp_table, conn, if_exists="append", index=False)

        # Insert into real table, skipping duplicates on event_id
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


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def backfill_gdelt_last_30_days(country_iso3: str) -> None:
    print("============================================================")
    print(f" GDELT BACKFILL - {country_iso3} (LAST 30 DAYS)")
    print("============================================================")

    engine = get_engine()

    # 1) Fetch raw rows from archive
    raw_df = fetch_gdelt_last_30_days(country_iso3)
    total_raw = len(raw_df)
    print("\n------------------------------------------------------------")
    print(f" Raw rows collected from GDELT archive      : {total_raw:,}")

    if total_raw == 0:
        print(" No data collected. Nothing to insert.")
        print("============================================================")
        return

    # 2) Transform to gdelt_events schema
    events_df = transform_gdelt_rows_to_events(raw_df, country_iso3=country_iso3)
    print(f" Events after transformation                : {len(events_df):,}")

    # 3) Upsert into DB
    inserted = upsert_gdelt_events(engine, events_df)
    skipped = len(events_df) - inserted

    print("------------------------------------------------------------")
    print(f" Inserted new events   : {inserted:,}")
    print(f" Likely duplicates     : {skipped:,} (skipped via ON CONFLICT)")
    print("✅ GDELT backfill complete.")
    print("============================================================")


if __name__ == "__main__":
    iso3 = os.getenv("GDELT_COUNTRY_ISO3", "SDN").upper()
    backfill_gdelt_last_30_days(country_iso3=iso3)

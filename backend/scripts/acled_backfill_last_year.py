# backend/scripts/acled_backfill_last_year.py

import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, text

from backend.app.services.acled_client import ACLEDClient, ACLEDApiError


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def get_engine():
    """
    Create a SQLAlchemy engine.

    Uses DATABASE_URL from environment if set; otherwise falls back
    to the same hard-coded DSN pattern you use elsewhere.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db",
    )
    return create_engine(db_url)


# ---------------------------------------------------------------------------
# Transform helpers (same shape as ACLEDEvent model)
# ---------------------------------------------------------------------------

def transform_acled_rows_to_df(rows) -> pd.DataFrame:
    """
    Transform raw ACLED rows (dicts) into a DataFrame matching ACLEDEvent schema.

    ACLEDEvent expects:
        event_id, event_date, event_type, region, latitude, longitude,
        actor1, actor2, fatalities, notes

    This function is intentionally similar to the one in acled_sync_from_api.py,
    so both scripts stay consistent.
    """
    rows_list = list(rows)
    if not rows_list:
        return pd.DataFrame()

    df = pd.DataFrame(rows_list)

    # ACLED columns (from official schema) include e.g.:
    # - data_id (unique numeric ID)
    # - event_id_cnty (legacy ID)
    # - event_date (YYYY-MM-DD)
    # - event_type
    # - actor1, actor2
    # - admin1 (state), admin2, admin3
    # - latitude, longitude
    # - notes
    # - fatalities

    # Build a stable event_id for your DB using ACLED's IDs
    if "data_id" in df.columns:
        df["event_id"] = "acled-" + df["data_id"].astype(str)
    elif "event_id_cnty" in df.columns:
        df["event_id"] = "acled-" + df["event_id_cnty"].astype(str)
    else:
        # Fallback (less ideal): combine date + location + actor
        df["event_id"] = (
            "acled-"
            + df.get("event_date", "").astype(str)
            + "-"
            + df.get("location", "").astype(str)
            + "-"
            + df.get("actor1", "").astype(str)
        )

    # Map region: we’ll use admin1 (state-level) as your 'region'
    if "admin1" in df.columns:
        df["region"] = df["admin1"]
    else:
        df["region"] = df.get("country", "Unknown")

    # Ensure required columns exist
    for col in ["event_type", "actor1", "actor2", "notes", "fatalities", "latitude", "longitude"]:
        if col not in df.columns:
            df[col] = None

    # Convert types
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
    df["fatalities"] = pd.to_numeric(df["fatalities"], errors="coerce").fillna(0).astype(int)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Select the exact columns needed by acled_events table
    expected_cols = [
        "event_id",
        "event_date",
        "event_type",
        "region",
        "latitude",
        "longitude",
        "actor1",
        "actor2",
        "fatalities",
        "notes",
    ]

    return df[expected_cols]


def upsert_acled_events(engine, df: pd.DataFrame) -> int:
    """
    Insert ACLED events into acled_events table, skipping duplicates by event_id.

    We rely on the unique constraint on event_id and use ON CONFLICT DO NOTHING.

    Returns:
        Number of rows inserted (best-effort, may be 0 if driver does not
        provide rowcount for the INSERT/ON CONFLICT statement).
    """
    if df.empty:
        return 0

    tmp_table = "acled_events_tmp"

    with engine.begin() as conn:
        # 1) Drop temp table if exists
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_table};"))

        # 2) Create temp table with the same columns we plan to insert
        conn.execute(
            text(
                f"""
                CREATE TEMP TABLE {tmp_table} (
                    event_id TEXT,
                    event_date DATE,
                    event_type TEXT,
                    region TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    actor1 TEXT,
                    actor2 TEXT,
                    fatalities INTEGER,
                    notes TEXT
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
                INSERT INTO acled_events (
                    event_id, event_date, event_type, region,
                    latitude, longitude, actor1, actor2, fatalities, notes
                )
                SELECT
                    event_id, event_date, event_type, region,
                    latitude, longitude, actor1, actor2, fatalities, notes
                FROM {tmp_table}
                ON CONFLICT (event_id) DO NOTHING;
                """
            )
        )

        inserted = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else 0

    return inserted


# ---------------------------------------------------------------------------
# Backfill last-year data
# ---------------------------------------------------------------------------

def backfill_last_year(country: str = "Sudan") -> None:
    """
    Fetch ACLED events for the last 365 days for `country`
    and upsert them into the acled_events table.

    - Uses event_date BETWEEN start|end
    - Skips duplicates via ON CONFLICT (event_id) DO NOTHING
    """
    engine = get_engine()
    client = ACLEDClient()

    # Define date range: last 365 days up to today (inclusive)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)

    date_range = f"{start_date:%Y-%m-%d}|{end_date:%Y-%m-%d}"

    print("============================================================")
    print(" ACLED BACKFILL - LAST 365 DAYS")
    print("============================================================")
    print(f" Country     : {country}")
    print(f" Date range  : {start_date}  ->  {end_date} (inclusive)")
    print("============================================================")

    try:
        rows_iter = client.fetch_events_dicts(
            params={
                "country": country,
                "event_date": date_range,
                "event_date_where": "BETWEEN",
                "terms": "accept",
            },
            max_pages=100,   # adjust as needed
            per_page=3000,   # ACLED default max is 5000; 3000 is safe
        )

        df = transform_acled_rows_to_df(rows_iter)
    except ACLEDApiError as e:
        print("❌ ACLED API error while fetching backfill data:")
        print(f"   {e}")
        print("   Please try again later or verify ACLED API status / params.")
        return

    total_rows = len(df)
    print(f"📦 Downloaded {total_rows} ACLED rows after transformation.")

    if total_rows == 0:
        print("✅ No events returned by ACLED for this date range.")
        return

    inserted = upsert_acled_events(engine, df)

    # We can't always know exact duplicates, but we can show a hint
    duplicates_hint = total_rows - inserted if inserted <= total_rows else 0

    print("------------------------------------------------------------")
    print(f" Total rows from ACLED : {total_rows}")
    print(f" Inserted new events   : {inserted}")
    print(f" Likely duplicates     : {duplicates_hint} (skipped via ON CONFLICT)")
    print("✅ Backfill complete.")
    print("============================================================")


if __name__ == "__main__":
    backfill_last_year()

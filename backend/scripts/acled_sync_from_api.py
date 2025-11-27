# scripts/acled_sync_from_api.py

import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, text

# 🛠 Import that works both when run as:
#   - python -m backend.scripts.acled_sync_from_api   (from repo root)
#   - python scripts/acled_sync_from_api.py           (from backend/)
try:
    from app.services.acled_client import ACLEDClient, ACLEDApiError
except ModuleNotFoundError:  # running as a package: backend.scripts...
    from backend.app.services.acled_client import ACLEDClient, ACLEDApiError  # type: ignore

# Country configuration
try:
    from app.config.countries import get_country_config
except ModuleNotFoundError:
    from backend.app.config.countries import get_country_config  # type: ignore


# ----------------- Config -----------------

# Earliest date you want to backfill from if the table is empty
MIN_START_DATE = datetime(2024, 1, 1).date()

# How many days to go back from the last DB date to catch late ACLED updates
DEFAULT_BACKFILL_DAYS = int(os.getenv("ACLED_BACKFILL_DAYS", "0"))


# ----------------- DB connection -----------------


def get_engine():
    """
    Create a SQLAlchemy engine.

    Prefer DATABASE_URL from the environment; fall back to the DSN used in populate_db.py.
    """
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db",
    )
    return create_engine(db_url)


# ----------------- Helpers -----------------


def get_last_acled_event_date(engine, country_iso3: str):
    """
    Get the most recent event_date present in acled_events for a given country_iso3.
    Returns a datetime.date or None.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT max(event_date) FROM acled_events WHERE country_iso3 = :iso3"),
            {"iso3": country_iso3},
        )
        max_date = result.scalar()
    return max_date  # can be None


def transform_acled_rows_to_df(rows, country_iso3: str) -> pd.DataFrame:
    """
    Transform raw ACLED rows (dicts) into a DataFrame matching ACLEDEvent schema.

    ACLEDEvent expects:
        event_id, country_iso3, event_date, event_type, region,
        latitude, longitude, actor1, actor2, fatalities, notes
    """
    df = pd.DataFrame(list(rows))
    if df.empty:
        return df

    # Build a stable event_id for your DB
    # Using ACLED's data_id is safest; prefix with "acled-"
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

    # Map region: use admin1 (state-level) as your 'region'
    if "admin1" in df.columns:
        df["region"] = df["admin1"]
    else:
        df["region"] = df.get("country", "Unknown")

    # Ensure required columns exist
    for col in [
        "event_type",
        "actor1",
        "actor2",
        "notes",
        "fatalities",
        "latitude",
        "longitude",
    ]:
        if col not in df.columns:
            df[col] = None

    # Convert types
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
    df["fatalities"] = (
        pd.to_numeric(df["fatalities"], errors="coerce").fillna(0).astype(int)
    )
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Tag with the ISO3 country code
    df["country_iso3"] = country_iso3

    # Select the exact columns needed by acled_events table
    expected_cols = [
        "event_id",
        "country_iso3",
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
    """
    if df.empty:
        return 0

    tmp_table = "acled_events_tmp"

    with engine.begin() as conn:
        # 1) Drop temp table if exists
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_table};"))

        # 2) Create temp table same structure as acled_events (minus PK/created_at)
        conn.execute(
            text(
                f"""
                CREATE TEMP TABLE {tmp_table} (
                    event_id TEXT,
                    country_iso3 TEXT,
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
                    event_id, country_iso3, event_date, event_type, region,
                    latitude, longitude, actor1, actor2, fatalities, notes
                )
                SELECT
                    event_id, country_iso3, event_date, event_type, region,
                    latitude, longitude, actor1, actor2, fatalities, notes
                FROM {tmp_table}
                ON CONFLICT (event_id) DO NOTHING;
                """
            )
        )

        # SQLAlchemy 2.x: rowcount may be -1 depending on driver; we can’t rely 100%
        inserted = (
            result.rowcount
            if result.rowcount is not None and result.rowcount >= 0
            else 0
        )

    return inserted


# ----------------- Main ETL -----------------


def sync_acled_for_country(
    country_iso3: str = "SDN",
    backfill_days: int = DEFAULT_BACKFILL_DAYS,
) -> None:
    """
    Incrementally sync ACLED events for a given country into acled_events.

    Logic:
      - Look up max(event_date) in acled_events for this ISO3.
      - If empty: start from MIN_START_DATE.
      - Else:
          * If backfill_days > 0: go back that many days (to catch late updates),
            but never before MIN_START_DATE.
          * If backfill_days == 0: request events AFTER last_date (exclusive).
      - Fetch pages from ACLED.
      - Transform → upsert, skipping duplicates via ON CONFLICT(event_id) DO NOTHING.
    """
    cfg = get_country_config(country_iso3)
    acled_country = cfg.acled_country_name

    engine = get_engine()
    client = ACLEDClient()

    last_date = get_last_acled_event_date(engine, cfg.iso3)

    if last_date is None:
        # Table empty for this country → full historical sync from MIN_START_DATE
        start_date = MIN_START_DATE
        print(
            f"ℹ️ acled_events has no rows yet for {cfg.iso3}; "
            f"starting full sync from {start_date}."
        )
    else:
        backfill_days = max(0, int(backfill_days))
        if backfill_days > 0:
            candidate = last_date - timedelta(days=backfill_days)
            start_date = max(candidate, MIN_START_DATE)
            print(
                f"ℹ️ Latest ACLED event in DB for {cfg.iso3}: {last_date} – "
                f"re-syncing from {start_date} (backfill {backfill_days} days)."
            )
        else:
            start_date = last_date + timedelta(days=1)
            print(
                f"ℹ️ Latest ACLED event in DB for {cfg.iso3}: {last_date} – "
                f"requesting events AFTER this date (exclusive)."
            )

    start_str = start_date.strftime("%Y-%m-%d")
    print(
        f"🔍 Fetching ACLED events for {acled_country} ({cfg.iso3}) "
        f"from {start_str} onwards..."
    )

    try:
        rows = client.fetch_events_dicts(
            params={
                "country": acled_country,
                "event_date": start_str,
                "event_date_where": "AFTER",
                "terms": "accept",
            },
            max_pages=50,  # adjust as needed
        )
    except ACLEDApiError as e:
        print("❌ ACLED API error while fetching events:")
        print(f"   {e}")
        print(
            "   This is most likely an issue on ACLED's side (HTTP 5xx or similar)."
        )
        print("   Try again later or test the URL with curl to confirm.")
        return

    df = transform_acled_rows_to_df(rows, country_iso3=cfg.iso3)

    if df.empty:
        print(
            f"✅ ACLED sync completed: no new events to insert "
            f"(API returned 0 rows for {cfg.iso3})."
        )
        return

    inserted = upsert_acled_events(engine, df)
    print(f"📦 Downloaded {len(df)} ACLED rows after transformation.")
    print(f"✅ Inserted {inserted} new ACLED events into acled_events table.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Sync ACLED events for a single country into Postgres incrementally."
        )
    )
    parser.add_argument(
        "--country-iso3",
        type=str,
        default="SDN",
        help="ISO3 code of the country to sync (e.g. SDN, SOM). Default: SDN.",
    )
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=DEFAULT_BACKFILL_DAYS,
        help=(
            "How many days before the last DB date to re-sync "
            "(default from ACLED_BACKFILL_DAYS env, currently %(default)s)."
        ),
    )
    args = parser.parse_args()

    iso3 = args.country_iso3.upper()
    sync_acled_for_country(country_iso3=iso3, backfill_days=args.backfill_days)

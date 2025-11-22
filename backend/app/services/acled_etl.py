# app/services/acled_etl.py

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.acled import ACLEDEvent
from app.services.acled_client import ACLEDClient

# Import SessionLocal with backwards-compatible pattern
try:
    from database import SessionLocal  # when running from backend/
except ModuleNotFoundError:  # when imported as backend.database
    from backend.database import SessionLocal  # type: ignore

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        return None
    try:
        # ACLED event_date is ISO-8601 YYYY-MM-DD
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _map_acled_row_to_event(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Map raw ACLED API row to ACLEDEvent fields.

    We intentionally only depend on a small subset of ACLED columns:
      - event_id_cnty  -> event_id (with prefix)
      - event_date
      - event_type
      - admin1 OR region -> region (Sudan state)
      - latitude, longitude
      - actor1, actor2
      - fatalities
      - notes
    """
    raw_event_id = str(
        row.get("event_id_cnty") or row.get("event_id") or ""
    ).strip()
    if not raw_event_id:
        return None

    event_date = _parse_date(row.get("event_date"))
    if event_date is None:
        return None

    region = (
        str(row.get("admin1") or row.get("region") or "").strip() or None
    )
    if region is None:
        # In practice you may want to keep events without region;
        # for SudanCRAM's state-level mapping, we skip them by default.
        return None

    latitude = _safe_float(row.get("latitude"))
    longitude = _safe_float(row.get("longitude"))

    return {
        "event_id": f"acled-{raw_event_id}",  # keep distinct from CSV-seeded ids
        "event_date": event_date,
        "event_type": (row.get("event_type") or "")[:100],
        "region": region,
        "latitude": latitude,
        "longitude": longitude,
        "actor1": (row.get("actor1") or "")[:200],
        "actor2": (row.get("actor2") or "")[:200],
        "fatalities": _safe_int(row.get("fatalities")) or 0,
        "notes": row.get("notes") or "",
    }


def _upsert_events(
    db: Session, mapped_events: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Insert ACLED events if not present, keyed by event_id.

    Returns:
        (inserted_count, skipped_existing)
    """
    inserted = 0
    skipped = 0

    if not mapped_events:
        return inserted, skipped

    # Preload existing event_ids to avoid lots of small queries.
    # For weekly syncs per country this is cheap.
    event_ids = [e["event_id"] for e in mapped_events]
    existing_ids = {
        eid
        for (eid,) in db.query(ACLEDEvent.event_id)
        .filter(ACLEDEvent.event_id.in_(event_ids))
        .all()
    }

    for e in mapped_events:
        if e["event_id"] in existing_ids:
            skipped += 1
            continue

        db_event = ACLEDEvent(**e)
        db.add(db_event)
        inserted += 1

    db.commit()
    return inserted, skipped


def sync_acled_events(
    days_back: int = 7,
    country: str = "Sudan",
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Sync recent ACLED events into the acled_events table.

    This is designed to be called from:
      - a CLI script (cron / scheduled job),
      - a manual admin endpoint, or
      - any batch process.

    Args:
        days_back: How many days back from today to fetch.
        country:   ACLED country name ("Sudan" by default).
        session:   Optional SQLAlchemy Session; if None, uses SessionLocal.

    Returns:
        Summary dict with counts & freshness info.
    """
    own_session = False
    if session is None:
        session = SessionLocal()
        own_session = True

    try:
        today = date.today()
        start_date = today - timedelta(days=days_back)
        client = ACLEDClient()

        raw_events = client.fetch_country_events(
            country=country,
            start_date=start_date,
            end_date=today,
            page_size=5000,
        )

        mapped: List[Dict[str, Any]] = []
        for row in raw_events:
            e = _map_acled_row_to_event(row)
            if e:
                mapped.append(e)

        inserted, skipped = _upsert_events(session, mapped)

        # Data quality / freshness: how recent is the latest ACLED event in DB?
        max_date_in_db = session.query(func.max(ACLEDEvent.event_date)).scalar()
        freshness_days: Optional[int] = None
        if isinstance(max_date_in_db, date):
            freshness_days = (today - max_date_in_db).days

        summary: Dict[str, Any] = {
            "country": country,
            "days_back": days_back,
            "raw_events_fetched": len(raw_events),
            "mapped_events": len(mapped),
            "inserted": inserted,
            "skipped_existing": skipped,
            "latest_event_date": max_date_in_db.isoformat()
            if isinstance(max_date_in_db, date)
            else None,
            "freshness_days": freshness_days,
            "status": "ok",
        }

        # Simple alert-style log if ACLED looks stale.
        if freshness_days is not None and freshness_days > 7:
            summary["status"] = "stale"
            logger.warning(
                "ACLED data looks stale: last event is %d days old (%s)",
                freshness_days,
                max_date_in_db,
            )
        else:
            logger.info(
                "ACLED sync complete. Inserted=%d, skipped=%d, last_date=%s",
                inserted,
                skipped,
                summary["latest_event_date"],
            )

        return summary

    finally:
        if own_session and session is not None:
            session.close()

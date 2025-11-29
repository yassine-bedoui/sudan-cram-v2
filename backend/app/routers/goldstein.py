"""
GDELT Goldstein Scale API Endpoints
Real-time conflict escalation + political environment risk
"""

from typing import Any, Dict, Optional

from datetime import datetime, timedelta
import glob
import os
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# DB + ORM
from database import get_db

try:
    from app.models.gdelt import GDELTEvent
except ModuleNotFoundError:  # when imported as backend.app.routers.goldstein
    from backend.app.models.gdelt import GDELTEvent  # type: ignore


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

router = APIRouter(prefix="/api/goldstein", tags=["Goldstein Escalation"])


# ----------------------------------------------------------------------
# File helper - used by escalation/timeline endpoints
# ----------------------------------------------------------------------


def get_latest_file(pattern: str) -> Optional[str]:
    """Get most recent file matching pattern in data/processed/."""
    # Docker: files live under /app/data/processed
    docker_pattern = str(Path("/app/data/processed") / pattern)
    # Local dev: files live under <project_root>/data/processed
    local_pattern = str(DATA_DIR / pattern)

    files = glob.glob(docker_pattern)
    if not files:
        files = glob.glob(local_pattern)

    if not files:
        return None
    return max(files, key=os.path.getctime)


# ----------------------------------------------------------------------
# Existing endpoints: escalation risk + timeline + top risks
# ----------------------------------------------------------------------


@router.get("/escalation-risk")
async def get_escalation_risk(
    country_iso3: str = Query(
        "SDN",
        alias="country",  # 👈 allows ?country=SOM
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
):
    """
    Get current escalation risk by location (from precomputed CSV)
    for the selected country.

    Example:
      /api/goldstein/escalation-risk?country=SDN
      /api/goldstein/escalation-risk?country=SOM
    """
    try:
        iso3 = country_iso3.upper()
        risk_file = get_latest_file(f"goldstein_escalation_risk_{iso3}_*.csv")

        if not risk_file:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No Goldstein analysis found for this country. "
                    "Run: COUNTRY_ISO3=<ISO3> python backend/scripts/analyze_goldstein_trends.py"
                ),
            )

        df = pd.read_csv(risk_file)

        result: Dict[str, Any] = {
            "country_iso3": iso3,
            "last_updated": datetime.fromtimestamp(os.path.getctime(risk_file)).isoformat(),
            "locations": {},
        }

        for _, row in df.iterrows():
            result["locations"][row["location"]] = {
                "risk_score": round(float(row["escalation_risk"]), 1),
                "risk_level": row["risk_level"],
                "avg_goldstein": round(float(row["avg_goldstein"]), 2),
                "trend": round(float(row["goldstein_trend"]), 2),
                "trend_direction": (
                    "escalating" if float(row["goldstein_trend"]) < 0 else "de-escalating"
                ),
                "event_count": int(row["event_count"]),
                "media_mentions": int(row["media_mentions"]),
                "last_seen": row["last_seen"],
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_goldstein_timeline(
    hours: int = 24,
    country_iso3: str = Query(
        "SDN",
        alias="country",  # 👈 allows ?country=SOM
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
):
    """
    Get hourly Goldstein timeline (for charts) for the selected country.
    Reads precomputed goldstein_hourly_timeline_<ISO3>_*.csv.

    Example:
      /api/goldstein/timeline?country=SDN&hours=24
      /api/goldstein/timeline?country=SOM&hours=48
    """
    try:
        iso3 = country_iso3.upper()
        timeline_file = get_latest_file(f"goldstein_hourly_timeline_{iso3}_*.csv")

        if not timeline_file:
            raise HTTPException(status_code=404, detail="No timeline data found")

        df = pd.read_csv(timeline_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        cutoff = df["timestamp"].max() - pd.Timedelta(hours=hours)
        df = df[df["timestamp"] >= cutoff]

        return {
            "country_iso3": iso3,
            "timestamps": df["timestamp"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
            "goldstein_scores": df["avg_goldstein"].tolist(),
            "event_counts": df["event_count"].tolist(),
            "mentions": df["mentions"].tolist(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-risks")
async def get_top_risks(
    limit: int = 10,
    country_iso3: str = Query(
        "SDN",
        alias="country",  # 👈 allows ?country=SOM
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
):
    """
    Get top N highest-risk locations (from precomputed escalation CSV)
    for the selected country.

    Example:
      /api/goldstein/top-risks?country=SDN&limit=5
      /api/goldstein/top-risks?country=SOM&limit=10
    """
    try:
        iso3 = country_iso3.upper()
        risk_file = get_latest_file(f"goldstein_escalation_risk_{iso3}_*.csv")

        if not risk_file:
            raise HTTPException(status_code=404, detail="No risk data")

        df = pd.read_csv(risk_file).head(limit)

        return {
            "country_iso3": iso3,
            "top_risks": df.to_dict("records"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# Raw GDELT event points (for heatmaps / timelines)
# ----------------------------------------------------------------------


@router.get("/events")
def get_gdelt_events(
    days: int = Query(7, ge=1, le=365, description="Look-back window in days."),
    region: Optional[str] = Query(
        None, description="Optional exact region filter (e.g. 'Khartoum, Al Khartum, Sudan')."
    ),
    country_iso3: str = Query(
        "SDN",
        alias="country",  # 👈 allows ?country=SOM
        min_length=3,
        max_length=3,
        description="ISO3 country code for filtering events.",
    ),
    limit: int = Query(2000, ge=1, le=10000, description="Max number of events to return."),
    db: Session = Depends(get_db),
):
    """
    Return recent GDELT events (point data) from Postgres for a given country.

    This is meant for:
    - Maps / heatmaps (lat/lon points)
    - Detailed event timelines per region

    Example:
      GET /api/goldstein/events?days=7&limit=1000&country=SDN
      GET /api/goldstein/events?days=7&limit=1000&country=SOM
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        iso3 = country_iso3.upper()

        query = (
            db.query(GDELTEvent)
            .filter(GDELTEvent.country_iso3 == iso3)
            .filter(GDELTEvent.event_date >= cutoff)
        )

        if region:
            query = query.filter(GDELTEvent.region == region)

        # Newest first
        query = query.order_by(GDELTEvent.event_date.desc()).limit(limit)

        events = query.all()

        out_events = []
        for ev in events:
            out_events.append(
                {
                    "id": ev.id,
                    "event_id": ev.event_id,
                    "date": ev.event_date.isoformat() if ev.event_date else None,
                    "region": ev.region,
                    "latitude": ev.latitude,
                    "longitude": ev.longitude,
                    "event_code": ev.event_code,
                    "quad_class": ev.quad_class,
                    "goldstein": ev.goldstein_scale,
                    "avg_tone": ev.avg_tone,
                }
            )

        return {
            "country_iso3": iso3,
            "window_days": days,
            "region_filter": region,
            "total": len(out_events),
            "events": out_events,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# Political Environment Risk (GDELT + Goldstein → 0–10 score)
# ----------------------------------------------------------------------


def _normalize_series(series: pd.Series) -> pd.Series:
    """
    Min-max normalize to [0, 1].

    If all values are equal or series is empty, returns zeros.
    """
    if series.empty:
        return series.copy()

    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.0] * len(series), index=series.index)

    return (series - min_val) / (max_val - min_val)


def _classify_risk(score: float) -> str:
    """Bucket a 0–10 score into qualitative levels."""
    if score >= 8:
        return "EXTREME"
    if score >= 6:
        return "VERY HIGH"
    if score >= 4:
        return "HIGH"
    if score >= 2:
        return "MODERATE"
    return "LOW"


@router.get("/political-risk")
def get_political_environment_risk(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days."),
    region: Optional[str] = Query(
        None, description="Optional exact region filter (e.g. 'Khartoum, Al Khartum, Sudan')."
    ),
    country_iso3: str = Query(
        "SDN",
        alias="country",  # 👈 allows ?country=SOM
        min_length=3,
        max_length=3,
        description="ISO3 country code for filtering events.",
    ),
    db: Session = Depends(get_db),
):
    """
    Compute a Political Environment Risk score per region from GDELT events
    for the selected country.

    This uses the gdelt_events table in Postgres directly.

    Example:
      /api/goldstein/political-risk?country=SDN&days=30
      /api/goldstein/political-risk?country=SOM&days=30
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        iso3 = country_iso3.upper()

        query = db.query(GDELTEvent).filter(GDELTEvent.country_iso3 == iso3).filter(
            GDELTEvent.event_date >= cutoff
        )
        if region:
            query = query.filter(GDELTEvent.region == region)

        events = query.all()
        if not events:
            return {
                "country_iso3": iso3,
                "window_days": days,
                "cutoff": cutoff.isoformat(),
                "region_filter": region,
                "regions": {},
                "message": "No GDELT events found in this window.",
            }

        # Build a DataFrame from ORM objects
        rows = []
        for ev in events:
            rows.append(
                {
                    "region": ev.region or "Unknown",
                    "event_date": ev.event_date,
                    "goldstein_scale": ev.goldstein_scale,
                    "quad_class": ev.quad_class,
                    "avg_tone": ev.avg_tone,
                }
            )

        df = pd.DataFrame(rows)

        # Clean types / defaults
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
        df["goldstein_scale"] = pd.to_numeric(df["goldstein_scale"], errors="coerce").fillna(0.0)
        df["quad_class"] = pd.to_numeric(df["quad_class"], errors="coerce").fillna(0).astype(int)
        df["avg_tone"] = pd.to_numeric(df["avg_tone"], errors="coerce").fillna(0.0)

        # Group by region
        region_stats = []
        for region_name, group in df.groupby("region"):
            group_sorted = group.sort_values("event_date")

            event_count = len(group_sorted)
            if event_count == 0:
                continue

            avg_goldstein = float(group_sorted["goldstein_scale"].mean())
            neg_goldstein = max(0.0, -avg_goldstein)

            conflict_events = group_sorted[group_sorted["quad_class"] >= 3]
            conflict_share = float(len(conflict_events) / event_count)

            avg_tone = float(group_sorted["avg_tone"].mean())
            neg_tone = max(0.0, -avg_tone)

            region_stats.append(
                {
                    "region": region_name,
                    "event_count": event_count,
                    "avg_goldstein": avg_goldstein,
                    "neg_goldstein": neg_goldstein,
                    "conflict_share": conflict_share,
                    "avg_tone": avg_tone,
                    "neg_tone": neg_tone,
                    "first_seen": group_sorted["event_date"].min(),
                    "last_seen": group_sorted["event_date"].max(),
                }
            )

        if not region_stats:
            return {
                "country_iso3": iso3,
                "window_days": days,
                "cutoff": cutoff.isoformat(),
                "region_filter": region,
                "regions": {},
                "message": "No valid GDELT events after cleaning.",
            }

        df_regions = pd.DataFrame(region_stats)

        # Normalize components
        events_norm = _normalize_series(df_regions["event_count"].astype(float))
        neg_gold_norm = _normalize_series(df_regions["neg_goldstein"].astype(float))
        neg_tone_norm = _normalize_series(df_regions["neg_tone"].astype(float))
        conflict_share = df_regions["conflict_share"].clip(0.0, 1.0)

        raw = (
            0.4 * events_norm
            + 0.3 * neg_gold_norm
            + 0.2 * conflict_share
            + 0.1 * neg_tone_norm
        )

        df_regions["political_risk_score"] = (raw * 10.0).clip(0.0, 10.0)
        df_regions["political_risk_level"] = df_regions["political_risk_score"].apply(
            _classify_risk
        )

        # Build response
        regions_out: Dict[str, Any] = {}
        for _, row in df_regions.iterrows():
            first_seen = row["first_seen"]
            last_seen = row["last_seen"]
            regions_out[row["region"]] = {
                "political_risk_score": round(float(row["political_risk_score"]), 2),
                "political_risk_level": str(row["political_risk_level"]),
                "event_count": int(row["event_count"]),
                "conflict_event_share": round(float(row["conflict_share"]), 3),
                "avg_goldstein": round(float(row["avg_goldstein"]), 2),
                "avg_tone": round(float(row["avg_tone"]), 2),
                "first_seen": first_seen.isoformat() if isinstance(first_seen, datetime) else None,
                "last_seen": last_seen.isoformat() if isinstance(last_seen, datetime) else None,
            }

        return {
            "country_iso3": iso3,
            "window_days": days,
            "cutoff": cutoff.isoformat(),
            "region_filter": region,
            "regions": regions_out,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

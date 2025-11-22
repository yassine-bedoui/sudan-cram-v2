# app/routers/acled_events.py

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.acled import ACLEDEvent

# Keep this import style consistent with your other routers
from database import get_db  # type: ignore

router = APIRouter(
    prefix="/api/events",
    tags=["ACLED Events"],
)


def _default_date_range() -> (date, date):
    """Default window for the map: last 30 days."""
    today = date.today()
    return today - timedelta(days=30), today


@router.get("/acled")
def get_acled_events(
    region: Optional[str] = Query(
        None,
        description="Filter by region (usually ACLED admin1 - e.g. 'North Darfur').",
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date (inclusive). Defaults to 30 days ago.",
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date (inclusive). Defaults to today.",
    ),
    min_fatalities: int = Query(
        0,
        ge=0,
        description="Minimum fatalities filter for events.",
    ),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event_type (exact or partial match).",
    ),
    bbox: Optional[str] = Query(
        None,
        description="Optional bounding box filter: minLon,minLat,maxLon,maxLat",
    ),
    limit: int = Query(
        2000,
        ge=1,
        le=5000,
        description="Maximum number of events to return.",
    ),
    format: str = Query(
        "json",
        pattern="^(json|geojson)$",
        description="Response format: 'json' or 'geojson'.",
    ),
    db: Session = Depends(get_db),
) -> Any:
    """
    Return ACLED events as map-ready points.

    - Used by the frontend to render a points layer or heatmap.
    - Filters by region, date range, fatalities, event_type, and optional bbox.
    - Supports JSON and GeoJSON output.
    """
    if start_date is None or end_date is None:
        start_default, end_default = _default_date_range()
        start_date = start_date or start_default
        end_date = end_date or end_default

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be <= end_date",
        )

    query = db.query(ACLEDEvent).filter(
        ACLEDEvent.event_date >= start_date,
        ACLEDEvent.event_date <= end_date,
    )

    if region:
        query = query.filter(ACLEDEvent.region == region)

    if min_fatalities > 0:
        query = query.filter(ACLEDEvent.fatalities >= min_fatalities)

    if event_type:
        # Case-insensitive partial match
        pattern = f"%{event_type}%"
        query = query.filter(ACLEDEvent.event_type.ilike(pattern))

    # Bounding box filter if provided
    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox.split(",")]
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="bbox must be 'minLon,minLat,maxLon,maxLat'",
            )

        query = query.filter(
            ACLEDEvent.longitude >= min_lon,
            ACLEDEvent.longitude <= max_lon,
            ACLEDEvent.latitude >= min_lat,
            ACLEDEvent.latitude <= max_lat,
        )

    events: List[ACLEDEvent] = (
        query.order_by(ACLEDEvent.event_date.desc())
        .limit(limit)
        .all()
    )

    def _event_to_dict(ev: ACLEDEvent) -> Dict[str, Any]:
        return {
            "id": ev.id,
            "event_id": ev.event_id,
            "event_date": ev.event_date.isoformat() if ev.event_date else None,
            "event_type": ev.event_type,
            "region": ev.region,
            "latitude": ev.latitude,
            "longitude": ev.longitude,
            "fatalities": ev.fatalities,
            "actor1": ev.actor1,
            "actor2": ev.actor2,
            "notes": ev.notes,
        }

    if format == "json":
        return {
            "success": True,
            "count": len(events),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "events": [_event_to_dict(e) for e in events],
        }

    # GeoJSON format
    features: List[Dict[str, Any]] = []
    for ev in events:
        if ev.latitude is None or ev.longitude is None:
            continue
        props = _event_to_dict(ev)
        # GeoJSON: properties separate from geometry
        props.pop("latitude", None)
        props.pop("longitude", None)

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [ev.longitude, ev.latitude],
                },
                "properties": props,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "count": len(features),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "region": region,
        },
    }

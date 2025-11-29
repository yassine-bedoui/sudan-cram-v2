# backend/app/routers/humanitarian.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.humanitarian_service import (
    HumanitarianService,
    HumanitarianServiceError,
)

router = APIRouter(prefix="/api/humanitarian", tags=["Humanitarian"])


def _service_or_500(country_iso3: str) -> HumanitarianService:
    try:
        return HumanitarianService(country_iso3=country_iso3)
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


def _normalized_country_iso3(
    country_iso3: str,
    country: Optional[str],
) -> str:
    """
    Prefer the explicit `country` query param if provided (backwards compat),
    otherwise fall back to `country_iso3`. Always return upper-cased ISO3.
    """
    code = (country or country_iso3 or "").strip()
    if not code:
        # Should never happen because of defaults, but just in case.
        raise HTTPException(status_code=400, detail="country_iso3 is required")
    return code.upper()


@router.get("/dtm")
async def get_dtm_humanitarian_layer(
    country_iso3: str = Query(
        "SDN",
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
    # Backwards-compat alias: /dtm?country=SDN
    country: Optional[str] = Query(
        None,
        min_length=3,
        max_length=3,
        include_in_schema=False,
    ),
) -> Dict[str, Any]:
    """
    Latest DTM displacement snapshot (Admin1-level) for the selected country.
    """
    iso3 = _normalized_country_iso3(country_iso3, country)
    svc = _service_or_500(iso3)

    try:
        df = svc.get_dtm_snapshot()
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    regions: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        regions.append(
            {
                "region": row["region"],
                "idps": int(row["idps"]),
                "last_reported": str(row.get("dtm_reporting_date", "")),
            }
        )

    return {
        "country": svc.dtm_client.country_name,
        "country_iso3": svc.country_iso3,
        "regions": regions,
    }


@router.get("/ipc")
async def get_ipc_humanitarian_layer(
    country_iso3: str = Query(
        "SDN",
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
    # Backwards-compat alias: /ipc?country=SDN
    country: Optional[str] = Query(
        None,
        min_length=3,
        max_length=3,
        include_in_schema=False,
    ),
) -> Dict[str, Any]:
    """
    Latest IPC food insecurity snapshot (Admin-level) for the selected country.

    If IPC API is not working or not configured, this will simply return
    an empty "regions" list.
    """
    iso3 = _normalized_country_iso3(country_iso3, country)
    svc = _service_or_500(iso3)

    try:
        df = svc.get_ipc_snapshot()
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Prefer IPC client's own code if it has one; otherwise use the service ISO3.
    country_code = (
        getattr(svc.ipc_client, "country_code", svc.country_iso3)
        if svc.ipc_client
        else svc.country_iso3
    )

    if df is None or df.empty:
        return {
            "country_iso3": svc.country_iso3,
            "country_code": country_code,
            "regions": [],
        }

    regions: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        regions.append(
            {
                "region": row["region"],
                "ipc_phase": int(row["ipc_phase"]),
                "ipc_phase_label": str(row["ipc_phase_label"]),
                "ipc_population_phase3plus": int(
                    row.get("ipc_population_phase3plus", 0)
                ),
                "analysis_period": str(row.get("analysis_period", "")),
            }
        )

    return {
        "country_iso3": svc.country_iso3,
        "country_code": country_code,
        "regions": regions,
    }


@router.get("/idmc")
async def get_idmc_humanitarian_layer(
    country_iso3: str = Query(
        "SDN",
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
    # Backwards-compat alias: /idmc?country=SDN
    country: Optional[str] = Query(
        None,
        min_length=3,
        max_length=3,
        include_in_schema=False,
    ),
) -> Dict[str, Any]:
    """
    Country-level IDMC GIDD displacement snapshot.
    """
    iso3 = _normalized_country_iso3(country_iso3, country)
    svc = _service_or_500(iso3)

    snapshot = svc.get_idmc_snapshot()
    if not snapshot:
        # Graceful empty response if IDMC not configured or no data
        return {
            "country": getattr(svc.idmc_client, "country_name", "Unknown")
            if getattr(svc, "idmc_client", None)
            else "Unknown",
            "iso3": getattr(svc.idmc_client, "country_iso3", svc.country_iso3)
            if getattr(svc, "idmc_client", None)
            else svc.country_iso3,
            "country_iso3": svc.country_iso3,
            "latest_year": None,
            "conflict_new_displacements": None,
            "disaster_new_displacements": None,
            "total_new_displacements": None,
        }

    return {
        "country": snapshot.get("country"),
        "iso3": snapshot.get("iso3"),
        "country_iso3": svc.country_iso3,
        "latest_year": snapshot.get("year"),
        "conflict_new_displacements": snapshot.get("conflict_new_displacements"),
        "disaster_new_displacements": snapshot.get("disaster_new_displacements"),
        "total_new_displacements": snapshot.get("total_new_displacements"),
    }


@router.get("/summary")
async def get_humanitarian_summary(
    country_iso3: str = Query(
        "SDN",
        min_length=3,
        max_length=3,
        description="ISO3 country code (e.g. 'SDN', 'SOM').",
    ),
    # Backwards-compat alias: /summary?country=SDN
    country: Optional[str] = Query(
        None,
        min_length=3,
        max_length=3,
        include_in_schema=False,
    ),
) -> Dict[str, Any]:
    """
    Combined humanitarian layer (DTM + IPC + IDMC) with a simple risk score
    for the selected country.
    """
    iso3 = _normalized_country_iso3(country_iso3, country)
    svc = _service_or_500(iso3)

    # We deliberately call this directly so we know if IPC is working.
    ipc_df = svc.get_ipc_snapshot()
    ipc_available = ipc_df is not None and not ipc_df.empty

    try:
        snapshots = svc.get_humanitarian_summary()
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    regions: List[Dict[str, Any]] = []
    for snap in snapshots:
        row: Dict[str, Any] = {
            "region": snap.region,
            "idps": snap.idps,
            "idps_last_reported": snap.idps_last_reported,
            "humanitarian_risk_score": snap.humanitarian_risk_score,
            "humanitarian_risk_level": snap.humanitarian_risk_level,
        }
        # Only include IPC-related fields if IPC actually returned data
        if ipc_available:
            row.update(
                {
                    "ipc_phase": snap.ipc_phase,
                    "ipc_phase_label": snap.ipc_phase_label,
                    "ipc_population_phase3plus": snap.ipc_population_phase3plus,
                    "analysis_period": snap.analysis_period,
                }
            )
        regions.append(row)

    # IDMC country-level context
    idmc_snapshot = svc.get_idmc_snapshot()
    response: Dict[str, Any] = {
        "country": svc.dtm_client.country_name,
        "country_iso3": svc.country_iso3,
        "regions": regions,
    }

    if idmc_snapshot:
        response["idmc"] = {
            "country": idmc_snapshot.get("country"),
            "iso3": idmc_snapshot.get("iso3"),
            "latest_year": idmc_snapshot.get("year"),
            "conflict_new_displacements": idmc_snapshot.get(
                "conflict_new_displacements"
            ),
            "disaster_new_displacements": idmc_snapshot.get(
                "disaster_new_displacements"
            ),
            "total_new_displacements": idmc_snapshot.get("total_new_displacements"),
        }

    return response

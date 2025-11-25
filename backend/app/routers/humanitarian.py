# backend/app/routers/humanitarian.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.services.humanitarian_service import (
    HumanitarianService,
    HumanitarianServiceError,
)

router = APIRouter(prefix="/api/humanitarian", tags=["Humanitarian"])


def _service_or_500() -> HumanitarianService:
    try:
        return HumanitarianService()
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dtm")
async def get_dtm_humanitarian_layer() -> Dict[str, Any]:
    """
    Latest DTM displacement snapshot (Admin1-level, Sudan by default).

    Response:
        {
          "country": "Sudan",
          "regions": [
            {
              "region": "Blue Nile",
              "idps": 12345,
              "last_reported": "2025-09-30"
            },
            ...
          ]
        }
    """
    svc = _service_or_500()

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
        "regions": regions,
    }


@router.get("/ipc")
async def get_ipc_humanitarian_layer() -> Dict[str, Any]:
    """
    Latest IPC food insecurity snapshot (Admin-level, Sudan).

    If IPC API is not working or not configured, this will simply return
    an empty "regions" list.

    Response:
        {
          "country_code": "SDN",
          "regions": [
            {
              "region": "Blue Nile",
              "ipc_phase": 3,
              "ipc_phase_label": "Crisis",
              "ipc_population_phase3plus": 456789,
              "analysis_period": "2025-10-01 to 2025-12-31"
            },
            ...
          ]
        }
    """
    svc = _service_or_500()

    try:
        df = svc.get_ipc_snapshot()
    except HumanitarianServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df is None or df.empty:
        return {
            "country_code": getattr(svc.ipc_client, "country_code", "SDN") if svc.ipc_client else "SDN",
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
        "country_code": getattr(svc.ipc_client, "country_code", "SDN") if svc.ipc_client else "SDN",
        "regions": regions,
    }


@router.get("/idmc")
async def get_idmc_humanitarian_layer() -> Dict[str, Any]:
    """
    Country-level IDMC GIDD displacement snapshot for Sudan.

    Response:
        {
          "country": "Sudan",
          "iso3": "SDN",
          "latest_year": 2024,
          "conflict_new_displacements": 12345,
          "disaster_new_displacements": 6789,
          "total_new_displacements": 19134
        }
    """
    svc = _service_or_500()

    snapshot = svc.get_idmc_snapshot()
    if not snapshot:
        # Graceful empty response if IDMC not configured or no data
        return {
            "country": getattr(svc.idmc_client, "country_name", "Sudan") if getattr(svc, "idmc_client", None) else "Sudan",
            "iso3": getattr(svc.idmc_client, "country_iso3", "SDN") if getattr(svc, "idmc_client", None) else "SDN",
            "latest_year": None,
            "conflict_new_displacements": None,
            "disaster_new_displacements": None,
            "total_new_displacements": None,
        }

    return {
        "country": snapshot.get("country"),
        "iso3": snapshot.get("iso3"),
        "latest_year": snapshot.get("year"),
        "conflict_new_displacements": snapshot.get("conflict_new_displacements"),
        "disaster_new_displacements": snapshot.get("disaster_new_displacements"),
        "total_new_displacements": snapshot.get("total_new_displacements"),
    }


@router.get("/summary")
async def get_humanitarian_summary() -> Dict[str, Any]:
    """
    Combined humanitarian layer (DTM + IPC + IDMC) with a simple risk score.

    IPC fields are only included in the per-region output IF the IPC API
    is working and returned at least one region. Otherwise, IPC is ignored
    in the JSON (though its absence still influences the risk score).

    Response:
        {
          "country": "Sudan",
          "idmc": {
            "country": "Sudan",
            "iso3": "SDN",
            "latest_year": 2024,
            "conflict_new_displacements": 12345,
            "disaster_new_displacements": 6789,
            "total_new_displacements": 19134
          },
          "regions": [
            {
              "region": "Blue Nile",
              "idps": 26651,
              "idps_last_reported": "2025-09-30",
              "ipc_phase": 3,                   # only if IPC available
              "ipc_phase_label": "Crisis",      # only if IPC available
              "ipc_population_phase3plus": 4567,# only if IPC available
              "analysis_period": "2025-10-01 to 2025-12-31",  # only if IPC available
              "humanitarian_risk_score": 7.4,
              "humanitarian_risk_level": "VERY HIGH"
            },
            ...
          ]
        }
    """
    svc = _service_or_500()

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
        "regions": regions,
    }

    if idmc_snapshot:
        response["idmc"] = {
            "country": idmc_snapshot.get("country"),
            "iso3": idmc_snapshot.get("iso3"),
            "latest_year": idmc_snapshot.get("year"),
            "conflict_new_displacements": idmc_snapshot.get("conflict_new_displacements"),
            "disaster_new_displacements": idmc_snapshot.get("disaster_new_displacements"),
            "total_new_displacements": idmc_snapshot.get("total_new_displacements"),
        }

    return response

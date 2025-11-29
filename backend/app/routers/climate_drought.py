# app/routers/climate_drought.py

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(
    prefix="/api/climate/drought",
    tags=["Climate / Drought"],
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Default country (for backward compatibility)
DEFAULT_COUNTRY_ISO3 = os.getenv("COUNTRY_ISO3", "SDN").upper()


def _resolve_country_iso3(country_iso3: str | None) -> str:
    """Resolve ISO3, falling back to env/default."""
    return (country_iso3 or DEFAULT_COUNTRY_ISO3).upper()


def _get_drought_file(country_iso3: str) -> Path:
    """
    Per-country drought file with backward compatibility.

    Priority:
      1. data/processed/drought_index_wapor_<iso3>.csv
      2. data/processed/drought_index_wapor.csv (only for default country)
    """
    iso_lower = country_iso3.lower()
    candidate = DATA_DIR / f"drought_index_wapor_{iso_lower}.csv"
    if candidate.exists():
        return candidate

    # Legacy single-country file, only for the default ISO3
    if country_iso3 == DEFAULT_COUNTRY_ISO3:
        legacy = DATA_DIR / "drought_index_wapor.csv"
        return legacy

    # Return candidate even if it doesn't exist; caller will 404
    return candidate


def _load_drought_df(country_iso3: str) -> tuple[pd.DataFrame, Path]:
    drought_file = _get_drought_file(country_iso3)

    if not drought_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Drought index file not found for country_iso3={country_iso3}. "
                "Run the WaPOR drought script first, e.g.: "
                f"COUNTRY_ISO3={country_iso3} python scripts/wapor_drought_index.py"
            ),
        )

    df = pd.read_csv(drought_file)
    required_cols = {"region", "drought_index", "drought_level"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=500,
            detail=(
                f"Malformed {drought_file.name} – "
                f"missing required columns {required_cols}."
            ),
        )
    return df, drought_file


@router.get("/", summary="List WaPOR-based drought index per region")
async def list_drought_regions(
    country_iso3: str | None = Query(
        None,
        alias="country",  # 👈 so ?country=SOM works
        description="ISO3 country code (defaults to COUNTRY_ISO3 env var).",
    ),
) -> Dict[str, Any]:
    """
    Get latest WaPOR-based drought index per region for a given country.

    Query params:
      - country: ISO3 code, e.g. SDN, SOM (optional; defaults from env).

    Returns:
        {
          "country_iso3": "SDN",
          "last_updated": "...",
          "regions": [
            {
              "region": "Gedaref",
              "drought_index": 7.5,
              "drought_level": "HIGH",
              "rain_mean": 0.123,
              "start_date": "...",
              "end_date": "..."
            },
            ...
          ]
        }
    """
    iso3 = _resolve_country_iso3(country_iso3)
    df, drought_file = _load_drought_df(iso3)
    last_updated = datetime.fromtimestamp(drought_file.stat().st_mtime).isoformat()

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        records.append(
            {
                "region": str(row["region"]),
                "drought_index": float(row["drought_index"]),
                "drought_level": str(row["drought_level"]),
                "rain_mean": float(row.get("rain_mean", 0.0))
                if pd.notna(row.get("rain_mean"))
                else None,
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
            }
        )

    return {
        "country_iso3": iso3,
        "last_updated": last_updated,
        "regions": records,
    }


@router.get(
    "/top-driest",
    summary="Get driest regions by drought index",
    description="Return the N regions with highest drought_index (driest).",
)
async def top_driest(
    limit: int = 5,
    country_iso3: str | None = Query(
        None,
        alias="country",  # 👈 so ?limit=5&country=SOM works
        description="ISO3 country code (defaults to COUNTRY_ISO3 env var).",
    ),
) -> Dict[str, Any]:
    iso3 = _resolve_country_iso3(country_iso3)
    df, drought_file = _load_drought_df(iso3)
    df_sorted = df.sort_values("drought_index", ascending=False).head(limit)
    last_updated = datetime.fromtimestamp(drought_file.stat().st_mtime).isoformat()
    return {
        "country_iso3": iso3,
        "last_updated": last_updated,
        "regions": df_sorted.to_dict(orient="records"),
    }


@router.get(
    "/{region_name}",
    summary="Get drought info for a single region",
    description="Case-insensitive match on the 'region' column.",
)
async def get_region_drought(
    region_name: str,
    country_iso3: str | None = Query(
        None,
        alias="country",  # 👈 so /Bay?country=SOM uses SOM
        description="ISO3 country code (defaults to COUNTRY_ISO3 env var).",
    ),
) -> Dict[str, Any]:
    iso3 = _resolve_country_iso3(country_iso3)
    df, drought_file = _load_drought_df(iso3)
    mask = df["region"].astype(str).str.lower() == region_name.lower()
    subset = df[mask]

    if subset.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Region '{region_name}' not found in drought file "
                f"for country_iso3={iso3}."
            ),
        )

    row = subset.iloc[0]
    return {
        "country_iso3": iso3,
        "region": str(row["region"]),
        "drought_index": float(row["drought_index"]),
        "drought_level": str(row["drought_level"]),
        "rain_mean": float(row.get("rain_mean", 0.0))
        if pd.notna(row.get("rain_mean"))
        else None,
        "start_date": row.get("start_date"),
        "end_date": row.get("end_date"),
        "last_updated": datetime.fromtimestamp(drought_file.stat().st_mtime).isoformat(),
    }

# app/routers/climate_drought.py

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/climate/drought",
    tags=["Climate / Drought"],
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
DROUGHT_FILE = DATA_DIR / "drought_index_wapor.csv"


def _load_drought_df() -> pd.DataFrame:
    if not DROUGHT_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Drought index file not found. "
                "Run the WaPOR drought script first: "
                "python scripts/wapor_drought_index.py"
            ),
        )

    df = pd.read_csv(DROUGHT_FILE)
    required_cols = {"region", "drought_index", "drought_level"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=500,
            detail=(
                "Malformed drought_index_wapor.csv – "
                f"missing required columns {required_cols}."
            ),
        )
    return df


@router.get("/", summary="List WaPOR-based drought index per region")
async def list_drought_regions() -> Dict[str, Any]:
    """
    Get latest WaPOR-based drought index per region.

    Returns:
        {
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
    df = _load_drought_df()
    last_updated = datetime.fromtimestamp(DROUGHT_FILE.stat().st_mtime).isoformat()

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
        "last_updated": last_updated,
        "regions": records,
    }


@router.get(
    "/top-driest",
    summary="Get driest regions by drought index",
    description="Return the N regions with highest drought_index (driest).",
)
async def top_driest(limit: int = 5) -> Dict[str, Any]:
    df = _load_drought_df().sort_values("drought_index", ascending=False).head(limit)
    last_updated = datetime.fromtimestamp(DROUGHT_FILE.stat().st_mtime).isoformat()
    return {
        "last_updated": last_updated,
        "regions": df.to_dict(orient="records"),
    }


@router.get(
    "/{region_name}",
    summary="Get drought info for a single region",
    description="Case-insensitive match on the 'region' column.",
)
async def get_region_drought(region_name: str) -> Dict[str, Any]:
    df = _load_drought_df()
    mask = df["region"].astype(str).str.lower() == region_name.lower()
    subset = df[mask]

    if subset.empty:
        raise HTTPException(
            status_code=404, detail=f"Region '{region_name}' not found in drought file."
        )

    row = subset.iloc[0]
    return {
        "region": str(row["region"]),
        "drought_index": float(row["drought_index"]),
        "drought_level": str(row["drought_level"]),
        "rain_mean": float(row.get("rain_mean", 0.0))
        if pd.notna(row.get("rain_mean"))
        else None,
        "start_date": row.get("start_date"),
        "end_date": row.get("end_date"),
        "last_updated": datetime.fromtimestamp(DROUGHT_FILE.stat().st_mtime).isoformat(),
    }

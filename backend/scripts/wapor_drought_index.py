# scripts/wapor_drought_index.py

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

try:
    from app.services.wapor_client import WAPORClient, WAPORClientError
except ModuleNotFoundError:
    # Fallback if your project is packaged as `backend.app`
    from backend.app.services.wapor_client import WAPORClient, WAPORClientError  # type: ignore

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Admin1 boundaries (GeoJSON / shapefile)
ADMIN1_PATH = os.getenv(
    "SUDAN_ADMIN1_GEOJSON",
    str(PROJECT_ROOT / "data" / "geo" / "sudan_admin1.geojson"),
)

# WaPOR config from .env
RAIN_COLLECTION = os.getenv("WAPOR_RAIN_COLLECTION", "").strip()
RAIN_MEASURE = os.getenv("WAPOR_RAIN_MEASURE", "").strip()
TIME_DIMENSION = os.getenv("WAPOR_RAIN_TIME_DIMENSION", "").strip() or None

OUTPUT_FILE = DATA_DIR / "drought_index_wapor.csv"


def normalize_to_10(values: np.ndarray) -> np.ndarray:
    """Normalize numeric array to [0, 10]; fallback to 5 if no variance."""
    if len(values) == 0:
        return np.array([])
    vmax = np.nanmax(values)
    vmin = np.nanmin(values)
    if np.isclose(vmax, vmin):
        return np.full_like(values, 5.0, dtype=float)
    return 10.0 * (values - vmin) / (vmax - vmin)


def drought_level_from_score(score: float) -> str:
    """Map numeric drought index to qualitative level."""
    if score >= 8:
        return "EXTREME"
    elif score >= 6:
        return "HIGH"
    elif score >= 4:
        return "MODERATE"
    elif score >= 2:
        return "LOW"
    else:
        return "NONE"


def compute_drought_index() -> None:
    print("=" * 70)
    print("🌵 WaPOR-based Drought Index for Sudan (Admin1)")
    print("=" * 70)

    if not RAIN_COLLECTION:
        raise RuntimeError(
            "WAPOR_RAIN_COLLECTION is not set. "
            "Set it to the WaPOR precipitation collection (e.g. L2-PCP-D) "
            "in your .env."
        )

    print(f"\n📥 Reading admin1 boundaries from: {ADMIN1_PATH}")
    gdf = gpd.read_file(ADMIN1_PATH)

    # 1) Optional override from env: SUDAN_ADMIN1_NAME_FIELD
    region_col_env = os.getenv("SUDAN_ADMIN1_NAME_FIELD")
    region_col = None

    if region_col_env:
        if region_col_env in gdf.columns:
            region_col = region_col_env
        else:
            raise RuntimeError(
                f"SUDAN_ADMIN1_NAME_FIELD is set to '{region_col_env}', "
                f"but that column does not exist in {ADMIN1_PATH}.\n"
                f"Available columns: {', '.join(gdf.columns)}"
            )

    # 2) Auto-detect if env var not set
    if region_col is None:
        candidates = [
            "shapeName",   # 👈 your actual column
            "ADM1_NAME",
            "admin1Name",
            "NAME_1",
            "NAME_EN",
            "NAME",
            "STATE_NAME",
            "State",
            "STATE",
            "region",
        ]
        for cand in candidates:
            if cand in gdf.columns:
                region_col = cand
                break

    if region_col is None:
        raise RuntimeError(
            "Could not find an admin1 name column in the geo file.\n"
            f"Available columns: {', '.join(gdf.columns)}\n\n"
            "Set the env var SUDAN_ADMIN1_NAME_FIELD to the correct column name, "
            "e.g. SUDAN_ADMIN1_NAME_FIELD=shapeName in your .env file."
        )

    print(f"   Found region name column: {region_col}")
    gdf[region_col] = gdf[region_col].astype(str).str.strip()

    client = WAPORClient()

    # Last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    print(
        f"\n📆 Time window: {start_date.strftime('%Y-%m-%d')} "
        f"-> {end_date.strftime('%Y-%m-%d')} (UTC)"
    )
    print(f"📡 Collection: {RAIN_COLLECTION}")
    print(f"📏 Measure: {RAIN_MEASURE}")
    print("\n🔄 Fetching WaPOR stats per region...\n")

    rows = []
    for idx, row in gdf.iterrows():
        region = row[region_col]
        minx, miny, maxx, maxy = row.geometry.bounds
        bbox = (float(minx), float(miny), float(maxx), float(maxy))

        print(f" • {region} ... ", end="", flush=True)
        try:
            stat = client.get_area_stat(
                collection=RAIN_COLLECTION,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                statistic="MEAN",          
                measure=RAIN_MEASURE,      
                time_dimension=TIME_DIMENSION,  
            )
            val = stat.value
            print(f"{val:.3f}")
        except WAPORClientError as e:
            print(f"ERROR: {e}")
            val = np.nan

        rows.append(
            {
                "region": region,
                "rain_mean": val,
                "bbox_minx": bbox[0],
                "bbox_miny": bbox[1],
                "bbox_maxx": bbox[2],
                "bbox_maxy": bbox[3],
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
            }
        )

    df = pd.DataFrame(rows)

    # Compute drought index: low rain => high drought
    print("\n🔢 Computing drought indices (0–10, higher = drier)...")
    rain_vals = df["rain_mean"].to_numpy(dtype=float)
    rain_norm = normalize_to_10(rain_vals)  # 0 = lowest rain, 10 = highest rain
    drought_raw = 10.0 - rain_norm         # invert: less rain -> higher drought

    df["drought_index"] = np.round(drought_raw, 2)
    df["drought_level"] = df["drought_index"].apply(drought_level_from_score)

    # Basic summaries
    print("\n📋 Top 10 driest regions:")
    df_sorted = df.sort_values("drought_index", ascending=False)
    for _, r in df_sorted.head(10).iterrows():
        try:
            print(
                f"   {str(r['region']):<20} | drought={float(r['drought_index']):>4.1f} "
                f"| rain_mean={float(r['rain_mean']):.3f}"
            )
        except Exception:
            # Guard against NaNs casting issues
            continue

    print("\n📊 Summary stats:")
    print(f"   Regions: {len(df)}")
    print(f"   Mean drought index: {df['drought_index'].mean():.2f}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)
    print("   ✅ Done.")
    print("=" * 70)


if __name__ == "__main__":
    compute_drought_index()

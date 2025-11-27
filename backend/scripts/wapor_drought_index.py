# backend/scripts/wapor_drought_index.py

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

# WaPOR client
try:
    from app.services.wapor_client import WAPORClient, WAPORClientError
except ModuleNotFoundError:
    # Fallback if your project is packaged as `backend.app`
    from backend.app.services.wapor_client import WAPORClient, WAPORClientError  # type: ignore

# Country configuration (Sudan + Somalia, etc.)
try:
    from app.config.countries import get_country_config
except ModuleNotFoundError:
    from backend.app.config.countries import get_country_config  # type: ignore

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Legacy / generic env fallbacks (used if CountryConfig doesn't provide values)
_DEFAULT_ADMIN1_PATH = os.getenv(
    "SUDAN_ADMIN1_GEOJSON",
    str(PROJECT_ROOT / "data" / "geo" / "sudan_admin1.geojson"),
)
_DEFAULT_RAIN_COLLECTION = os.getenv("WAPOR_RAIN_COLLECTION", "").strip()
_DEFAULT_RAIN_MEASURE = os.getenv("WAPOR_RAIN_MEASURE", "").strip()
_DEFAULT_TIME_DIMENSION = os.getenv("WAPOR_RAIN_TIME_DIMENSION", "").strip() or None


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


def compute_drought_index(country_iso3: str = "SDN") -> None:
    """
    Compute WaPOR-based drought index for a given country (Admin1).

    - Uses CountryConfig to pick admin1 boundaries and WaPOR collection.
    - Still supports legacy env-based defaults for Sudan.
    """
    cfg = get_country_config(country_iso3)
    iso3 = cfg.iso3
    country_name = cfg.name

    # Country-specific admin1 boundaries
    admin1_path = cfg.admin1_geojson or _DEFAULT_ADMIN1_PATH

    # Country-specific WaPOR config (with legacy fallbacks)
    rain_collection = (cfg.wapor_rain_collection or _DEFAULT_RAIN_COLLECTION).strip()
    rain_measure = (cfg.wapor_rain_measure or _DEFAULT_RAIN_MEASURE).strip()
    time_dimension = (cfg.wapor_rain_time_dimension or _DEFAULT_TIME_DIMENSION) or None

    print("=" * 70)
    print("🌵 WaPOR-based Drought Index (Admin1)")
    print(f"   Country: {country_name} ({iso3})")
    print("=" * 70)

    if not rain_collection:
        raise RuntimeError(
            "WAPOR_RAIN_COLLECTION (or country-specific WaPOR collection) is not set. "
            "Set it to the WaPOR precipitation collection (e.g. L2-PCP-D) "
            "in your .env (or SOMALIA_WAPOR_RAIN_COLLECTION, etc.)."
        )

    print(f"\n📥 Reading admin1 boundaries from: {admin1_path}")
    gdf = gpd.read_file(admin1_path)

    # Optional override from env: <ISO3>_ADMIN1_NAME_FIELD (e.g. SUDAN_..., SOMALIA_...)
    region_col_env = None
    if iso3 == "SDN":
        region_col_env = os.getenv("SUDAN_ADMIN1_NAME_FIELD")
    elif iso3 == "SOM":
        region_col_env = os.getenv("SOMALIA_ADMIN1_NAME_FIELD")

    region_col = None

    if region_col_env:
        if region_col_env in gdf.columns:
            region_col = region_col_env
        else:
            raise RuntimeError(
                f"{iso3}_ADMIN1_NAME_FIELD is set to '{region_col_env}', "
                f"but that column does not exist in {admin1_path}.\n"
                f"Available columns: {', '.join(gdf.columns)}"
            )

    # Auto-detect if env var not set
    if region_col is None:
        candidates = [
            # Sudan common names
            "shapeName",
            "ADM1_NAME",
            "admin1Name",
            "NAME_1",
            "NAME_EN",
            "NAME",
            "STATE_NAME",
            "State",
            "STATE",
            "region",
            # Somalia common names
            "adm1_name",
            "adm1name",
        ]
        for cand in candidates:
            if cand in gdf.columns:
                region_col = cand
                break

    if region_col is None:
        raise RuntimeError(
            "Could not find an admin1 name column in the geo file.\n"
            f"Available columns: {', '.join(gdf.columns)}\n\n"
            "Set the appropriate *_ADMIN1_NAME_FIELD env var to the correct column name, "
            "e.g. SUDAN_ADMIN1_NAME_FIELD=shapeName or SOMALIA_ADMIN1_NAME_FIELD=adm1_name."
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
    print(f"📡 Collection: {rain_collection}")
    print(f"📏 Measure: {rain_measure}")
    print("\n🔄 Fetching WaPOR stats per region...\n")

    rows = []
    for idx, row in gdf.iterrows():
        region = row[region_col]
        minx, miny, maxx, maxy = row.geometry.bounds
        bbox = (float(minx), float(miny), float(maxx), float(maxy))

        print(f" • {region} ... ", end="", flush=True)
        try:
            stat = client.get_area_stat(
                collection=rain_collection,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                statistic="MEAN",
                measure=rain_measure,
                time_dimension=time_dimension,
            )
            val = stat.value
            print(f"{val:.3f}")
        except WAPORClientError as e:
            print(f"ERROR: {e}")
            val = np.nan

        rows.append(
            {
                "country_iso3": iso3,
                "country_name": country_name,
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

    # Country-specific output file (keep old name for backwards compatibility if SDN)
    output_file = DATA_DIR / f"drought_index_wapor_{iso3.lower()}.csv"
    print(f"\n💾 Saving to: {output_file}")
    df.to_csv(output_file, index=False)

    # For legacy consumers still expecting a single file, keep Sudan behaviour
    if iso3 == "SDN":
        legacy_file = DATA_DIR / "drought_index_wapor.csv"
        print(f"   (Also writing legacy Sudan file: {legacy_file})")
        df.to_csv(legacy_file, index=False)

    print("   ✅ Done.")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute WaPOR-based drought index (Admin1) for a given country."
    )
    parser.add_argument(
        "--country",
        "-c",
        help="ISO3 country code (e.g. SDN, SOM)",
        default=os.getenv("DROUGHT_COUNTRY_ISO3", "SDN"),
    )
    args = parser.parse_args()
    iso3 = (args.country or "SDN").upper()
    compute_drought_index(country_iso3=iso3)

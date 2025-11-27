# scripts/compute_somalia_admin1_centroids.py

from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd

# You can override these via env vars if needed
INPUT = Path(os.getenv("SOMALIA_ADMIN1_GEOJSON", "data/geo/somalia_admin1.geojson"))
OUTPUT = Path(
    os.getenv(
        "SOMALIA_ADMIN1_CENTROIDS_OUTPUT",
        "data/geo/somalia_admin1_centroids.json",
    )
)

# Optional override for the admin1 name column
ADMIN1_NAME_FIELD_ENV = os.getenv("SOMALIA_ADMIN1_NAME_FIELD")


def detect_name_column(gdf: gpd.GeoDataFrame) -> str:
    """
    Pick the best admin1 name column from the Somalia GeoJSON.

    Priority:
      1) SOMALIA_ADMIN1_NAME_FIELD env var (if set and exists)
      2) Common candidate columns (for Somalia COD)
    """
    if ADMIN1_NAME_FIELD_ENV:
        if ADMIN1_NAME_FIELD_ENV in gdf.columns:
            print(f"✅ Using admin1 name column from env: {ADMIN1_NAME_FIELD_ENV}")
            return ADMIN1_NAME_FIELD_ENV
        else:
            raise RuntimeError(
                f"SOMALIA_ADMIN1_NAME_FIELD='{ADMIN1_NAME_FIELD_ENV}' is not a column "
                f"in {INPUT}. Available columns: {list(gdf.columns)}"
            )

    # Auto-detect from common candidates
    candidates = [
        "adm1_name",   # 👈 your file has this
        "ADM1_NAME",
        "name",
        "NAME_1",
        "adm1_name1",
    ]
    for col in candidates:
        if col in gdf.columns:
            print(f"✅ Auto-detected admin1 name column: {col}")
            return col

    raise RuntimeError(
        "Could not find an admin1 name column in the Somalia GeoJSON.\n"
        f"Available columns: {list(gdf.columns)}\n\n"
        "Set SOMALIA_ADMIN1_NAME_FIELD to the correct column name "
        "(e.g. 'adm1_name')."
    )


def main() -> None:
    print("=========================================================")
    print(" Somalia – compute admin1 centroids")
    print("=========================================================")
    print(f"📥 Reading: {INPUT}")

    gdf = gpd.read_file(INPUT)

    # Detect which column holds the admin1 name (e.g. 'adm1_name')
    name_col = detect_name_column(gdf)
    gdf[name_col] = gdf[name_col].astype(str).str.strip()

    # Ensure WGS84 if geometry is used
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print(f"🔁 Reprojecting from {gdf.crs} to EPSG:4326")
        gdf = gdf.to_crs(epsg=4326)

    # Prefer precomputed center_lat/center_lon if present (your file has them),
    # otherwise fall back to geometry.centroid
    has_center_lat = "center_lat" in gdf.columns
    has_center_lon = "center_lon" in gdf.columns
    if has_center_lat and has_center_lon:
        print("✅ Using 'center_lat' / 'center_lon' from properties.")
    else:
        print("ℹ️ 'center_lat' / 'center_lon' not found – using geometry centroids.")

    centroids: dict[str, dict[str, float]] = {}

    for _, row in gdf.iterrows():
        name = str(row[name_col]).strip()
        if not name:
            continue

        if has_center_lat and has_center_lon:
            try:
                lat = float(row["center_lat"])
                lon = float(row["center_lon"])
            except (TypeError, ValueError):
                # Fallback to geometry centroid if conversion fails
                c = row.geometry.centroid
                lat, lon = float(c.y), float(c.x)
        else:
            c = row.geometry.centroid
            lat, lon = float(c.y), float(c.x)

        centroids[name] = {"lat": lat, "lon": lon}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(centroids, indent=2), encoding="utf-8")

    print(f"\n✅ Wrote {len(centroids)} Somalia admin1 centroids to: {OUTPUT}")
    print("   Example:")
    for k in list(centroids.keys())[:5]:
        print(f"   - {k}: {centroids[k]}")
    print("=========================================================")


if __name__ == "__main__":
    main()

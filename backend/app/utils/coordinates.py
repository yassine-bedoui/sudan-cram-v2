# app/utils/coordinates.py
"""
Country + admin1 centroid utilities.

- Sudan centroids are hard-coded (as before).
- Somalia centroids are loaded from a JSON file generated offline, e.g.:
    data/geo/somalia_admin1_centroids.json

  That JSON can be created with a small GeoPandas script that computes
  centroids from a Somalia admin1 boundary file (see docs / scripts).

JSON formats supported for Somalia:

1) Object mapping:
   {
     "Awdal": { "lat": 9.93, "lon": 43.18 },
     "Woqooyi Galbeed": { "lat": 9.56, "lon": 44.07 },
     ...
   }

2) List of records:
   [
     { "region": "Awdal", "lat": 9.93, "lon": 43.18 },
     ...
   ]

If the Somalia file is missing or malformed, functions will just return
None / [] for Somalia regions and the rest of the app should handle that
gracefully (e.g. fall back to not drawing centroids).
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple, List

# Type alias: (lat, lon)
LatLon = Tuple[float, float]

# ---------------------------------------------------------------------------
# Sudan – hard-coded centroids (existing behaviour)
# ---------------------------------------------------------------------------

SUDAN_COORDINATES: Dict[str, Dict[str, float]] = {
    "North Darfur": {"lat": 14.0, "lon": 26.0},
    "Khartoum": {"lat": 15.5, "lon": 32.5},
    "Al Jazirah": {"lat": 14.0, "lon": 35.0},
    "North Kordofan": {"lat": 16.5, "lon": 30.5},
    "South Darfur": {"lat": 11.5, "lon": 25.0},
    "West Kordofan": {"lat": 13.5, "lon": 27.0},
    "White Nile": {"lat": 13.0, "lon": 32.0},
    "South Kordofan": {"lat": 11.0, "lon": 30.0},
    "Northern": {"lat": 18.5, "lon": 31.0},
    "Red Sea": {"lat": 19.0, "lon": 37.5},
    "Sennar": {"lat": 13.5, "lon": 34.5},
    "East Darfur": {"lat": 12.5, "lon": 26.5},
    "Blue Nile": {"lat": 12.0, "lon": 33.0},
    "West Darfur": {"lat": 12.5, "lon": 22.5},
    "Central Darfur": {"lat": 12.0, "lon": 24.5},
    "River Nile": {"lat": 17.5, "lon": 30.5},
    "Abyei": {"lat": 10.0, "lon": 29.0},
    "Kassala": {"lat": 15.5, "lon": 36.0},
    "Gedaref": {"lat": 14.5, "lon": 35.0},
}

# ---------------------------------------------------------------------------
# Somalia – loaded from JSON at runtime
# ---------------------------------------------------------------------------

# Global cache (avoid re-reading file on every call)
_SOMALIA_COORDINATES: Optional[Dict[str, Dict[str, float]]] = None


def _somalia_centroids_path() -> str:
    """
    Path to the Somalia admin1 centroids JSON file.

    You can override with SOMALIA_ADMIN1_CENTROIDS_PATH if you want a custom path.
    """
    return os.getenv(
        "SOMALIA_ADMIN1_CENTROIDS_PATH",
        os.path.join("data", "geo", "somalia_admin1_centroids.json"),
    )


def _load_somalia_coordinates() -> Dict[str, Dict[str, float]]:
    """
    Lazy-load Somalia admin1 centroids from JSON.

    Returns an empty dict if:
      - file does not exist
      - JSON is invalid
      - records don't have usable lat/lon
    """
    global _SOMALIA_COORDINATES

    if _SOMALIA_COORDINATES is not None:
        return _SOMALIA_COORDINATES

    path = _somalia_centroids_path()
    coords: Dict[str, Dict[str, float]] = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        # Not fatal – just means Somalia centroids not configured yet
        _SOMALIA_COORDINATES = {}
        return _SOMALIA_COORDINATES
    except json.JSONDecodeError:
        _SOMALIA_COORDINATES = {}
        return _SOMALIA_COORDINATES

    # Support both dict and list formats
    if isinstance(raw, dict):
        for region, val in raw.items():
            try:
                lat = float(val["lat"])
                lon = float(val["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            coords[str(region).strip()] = {"lat": lat, "lon": lon}

    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            region = item.get("region")
            lat = item.get("lat")
            lon = item.get("lon")
            if not region:
                continue
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except (TypeError, ValueError):
                continue
            coords[str(region).strip()] = {"lat": lat_f, "lon": lon_f}

    _SOMALIA_COORDINATES = coords
    return _SOMALIA_COORDINATES


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_region_centroid(country_iso3: str, region_name: str) -> Optional[LatLon]:
    """
    Return (lat, lon) for a given country + admin1 region, or None if unknown.

    country_iso3:
        "SDN" for Sudan, "SOM" for Somalia (can be lower/upper case).
    region_name:
        Must match your normalized admin1 name (after any mapping logic).
    """
    iso3 = (country_iso3 or "").upper()
    region = (region_name or "").strip()
    if not iso3 or not region:
        return None

    if iso3 == "SDN":
        entry = SUDAN_COORDINATES.get(region)
        if not entry:
            return None
        try:
            return float(entry["lat"]), float(entry["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    if iso3 == "SOM":
        somalia = _load_somalia_coordinates()
        entry = somalia.get(region)
        if not entry:
            return None
        try:
            return float(entry["lat"]), float(entry["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    # Future countries: extend here
    return None


def list_regions(country_iso3: str) -> List[str]:
    """
    List all regions for which we have centroids for a given country.

    This is helpful for debugging, seeding dropdowns, etc.
    """
    iso3 = (country_iso3 or "").upper()

    if iso3 == "SDN":
        return sorted(SUDAN_COORDINATES.keys())
    if iso3 == "SOM":
        return sorted(_load_somalia_coordinates().keys())

    return []

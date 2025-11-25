# backend/app/services/wapor_client.py

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()


class WAPORClientError(RuntimeError):
    """Raised when the WaPOR / GISMGR API request fails or returns malformed data."""
    pass


@dataclass
class WAPORStat:
    """Simple container for an aggregated value over an area + time window."""
    collection: str
    bbox: Tuple[float, float, float, float]
    start_date: datetime
    end_date: datetime
    statistic: str
    value: float


class WAPORClient:
    """
    WaPOR v3 client using GISMGR catalog + COGs, **no authentication required**.

    Flow (mirrors the official WaPORv3_API notebook):

      1. List rasters in a given mapset (e.g. L2-PCP-D) via:
         GET /catalog/workspaces/WAPOR-3/mapsets/{mapset_code}/rasters

      2. Filter rasters by date (we parse the dekad from the raster code).

      3. For each raster in the time window, read the subset over the bbox from
         the Cloud Optimized GeoTIFF (downloadUrl) and compute a statistic
         (mean or sum). Finally aggregate over time.
    """

    # pattern to extract dekad date from raster code, e.g.
    # "WAPOR-3.L2-PCP-D.2024-03-D2" -> 2024, 03, dekad 2
    _DEKAD_RE = re.compile(r"\.(\d{4})-(\d{2})-D([123])")

    def __init__(
        self,
        base_url: Optional[str] = None,
        workspace_code: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        # Default to WaPOR v3 API (no auth)
        self.base_url = (
            base_url
            or os.getenv("WAPOR_API_BASE_URL", "https://data.apps.fao.org/gismgr/api/v2")
        ).rstrip("/")

        # WaPOR v3 workspace is WAPOR-3 (different from old WAPOR v2)
        self.workspace_code = workspace_code or os.getenv("WAPOR_WORKSPACE_CODE", "WAPOR-3")

        self.session = session or requests.Session()

    # ------------------------------------------------------------------ #
    # Public method: aggregated value over bbox + time window            #
    # ------------------------------------------------------------------ #

    def get_area_stat(
        self,
        collection: str,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        measure: Optional[str] = None,         # kept for compatibility
        time_dimension: Optional[str] = None,   # kept for compatibility
        statistic: str = "MEAN",
    ) -> WAPORStat:
        """
        Compute an aggregated rainfall statistic over a bbox and time window,
        using WaPOR v3 mapsets + COGs.

        Args:
            collection: WaPOR mapset code (e.g. "L2-PCP-D").
            bbox: (minx, miny, maxx, maxy) in WGS84.
            start_date: inclusive start datetime (UTC).
            end_date: inclusive end datetime (UTC).
            measure: ignored (for future extension).
            time_dimension: ignored (for future extension).
            statistic: "MEAN" or "SUM".

        Returns:
            WAPORStat with a single numeric value.
        """
        # 1) list all rasters in the mapset
        rasters = self._list_mapset_rasters(collection)

        # 2) keep only rasters whose dekad date falls in our window
        rasters_in_window: List[Dict[str, Any]] = []
        for r in rasters:
            dt = self._dekad_code_to_date(r.get("code", ""))
            if dt is None:
                continue
            if start_date.date() <= dt.date() <= end_date.date():
                rasters_in_window.append(r)

        if not rasters_in_window:
            raise WAPORClientError(
                f"No rasters found in time window {start_date.date()}–{end_date.date()} "
                f"for mapset {collection}"
            )

        # 3) compute bbox statistic for each dekad raster
        values: List[float] = []
        for r in rasters_in_window:
            url = r.get("downloadUrl")
            if not url:
                continue
            try:
                val = self._compute_raster_bbox_stat(url, bbox, statistic=statistic)
            except Exception as e:  # pragma: no cover - very defensive
                # If one raster fails, we log it via exception and continue
                raise WAPORClientError(
                    f"Failed to compute stat for raster {r.get('code')}: {e}"
                ) from e
            if np.isfinite(val):
                values.append(float(val))

        if not values:
            raise WAPORClientError(
                f"All rasters in time window returned NaN / empty data for bbox {bbox}."
            )

        # 4) aggregate over time (list of dekads)
        stat_u = statistic.upper()
        if stat_u in ("MEAN", "AVG", "AVERAGE"):
            agg_value = float(np.mean(values))
        elif stat_u == "SUM":
            agg_value = float(np.sum(values))
        else:
            raise WAPORClientError(f"Unsupported statistic '{statistic}'")

        return WAPORStat(
            collection=collection,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            statistic=statistic.upper(),
            value=agg_value,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _list_mapset_rasters(self, mapset_code: str) -> List[Dict[str, Any]]:
        """
        List rasters for a given WaPOR v3 mapset.

        Uses the same paging pattern as the official WaPORv3_API notebook.
        """
        # Example:
        #   /catalog/workspaces/WAPOR-3/mapsets/L2-PCP-D/rasters
        first_url = (
            f"{self.base_url}/catalog/workspaces/"
            f"{self.workspace_code}/mapsets/{mapset_code}/rasters"
        )

        items: List[Dict[str, Any]] = []

        # Fake initial "next" link to simplify loop
        data: Dict[str, Any] = {"links": [{"rel": "next", "href": first_url}]}

        while any(link.get("rel") == "next" for link in data.get("links", [])):
            next_url = [
                link.get("href")
                for link in data.get("links", [])
                if link.get("rel") == "next"
            ][0]

            resp = self.session.get(next_url, timeout=60)
            if resp.status_code != 200:
                raise WAPORClientError(
                    f"Failed to list rasters for mapset {mapset_code}: "
                    f"{resp.status_code} {resp.text[:300]}"
                )

            payload = resp.json()
            # GISMGR responses are of the form {"response": {...}}
            data = payload.get("response", payload)

            items.extend(data.get("items", []))

        # We only really need code + downloadUrl
        simplified: List[Dict[str, Any]] = []
        for it in items:
            code = it.get("code")
            url = it.get("downloadUrl")
            if code and url:
                simplified.append({"code": code, "downloadUrl": url})

        if not simplified:
            raise WAPORClientError(
                f"No rasters returned for mapset {mapset_code}. "
                f"Check that WAPOR_WORKSPACE_CODE={self.workspace_code} "
                f"and WAPOR_RAIN_COLLECTION={mapset_code} are correct."
            )

        return simplified

    def _dekad_code_to_date(self, raster_code: str) -> Optional[datetime]:
        """
        Parse dekad date from a raster code like:
            WAPOR-3.L2-PCP-D.2024-03-D2

        We approximate:
            D1 -> day 1
            D2 -> day 11
            D3 -> day 21
        which is good enough for a 30-day rolling window.
        """
        m = self._DEKAD_RE.search(raster_code)
        if not m:
            return None
        year = int(m.group(1))
        month = int(m.group(2))
        dekad = int(m.group(3))

        if dekad == 1:
            day = 1
        elif dekad == 2:
            day = 11
        else:
            day = 21

        return datetime(year, month, day)

    def _compute_raster_bbox_stat(
        self,
        url: str,
        bbox: Tuple[float, float, float, float],
        statistic: str = "MEAN",
    ) -> float:
        """
        Read a Cloud Optimized GeoTIFF over HTTP and compute a statistic for the
        given bbox using rasterio.

        Args:
            url: downloadUrl for the raster (HTTPS URL to a COG).
            bbox: (minx, miny, maxx, maxy) in WGS84.
            statistic: "MEAN" or "SUM".

        Returns:
            Single float (may be NaN if bbox has no data).
        """
        import rasterio
        from rasterio.windows import from_bounds

        minx, miny, maxx, maxy = bbox

        with rasterio.Env():  # let rasterio/GDAL manage HTTP / COG stuff
            with rasterio.open(url) as src:
                window = from_bounds(minx, miny, maxx, maxy, src.transform)
                data = src.read(1, window=window, masked=True)

        if data.size == 0:
            return float("nan")

        stat_u = statistic.upper()
        if stat_u in ("MEAN", "AVG", "AVERAGE"):
            return float(data.mean())
        elif stat_u == "SUM":
            return float(data.sum())
        else:
            raise WAPORClientError(f"Unsupported statistic '{statistic}'")

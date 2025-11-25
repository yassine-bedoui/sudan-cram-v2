# backend/app/services/idmc_client.py

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


class IDMCClientError(RuntimeError):
    """Raised when something goes wrong while calling the IDMC API."""
    pass


@dataclass
class IDMCSnapshot:
    """
    Country-level GIDD snapshot from IDMC.

    All numbers are annual NEW displacements (not stocks).
    """
    country: str
    iso3: str
    year: int
    conflict_new_displacements: int
    disaster_new_displacements: int
    total_new_displacements: int


class IDMCClient:
    """
    Thin client for the IDMC GIDD API.

    Env vars:
        IDMC_CLIENT_ID     - required, the "client_id" token sent by email
        IDMC_BASE_URL      - defaults to https://helix-tools-api.idmcdb.org/external-api
        IDMC_COUNTRY_ISO3  - defaults to SDN
        IDMC_COUNTRY_NAME  - optional human-readable country label
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        base_url: Optional[str] = None,
        country_iso3: Optional[str] = None,
        country_name: Optional[str] = None,
    ) -> None:
        # Allow fallback to IPC_API_KEY because you previously used that var
        self.client_id = (
            client_id
            or os.getenv("IDMC_CLIENT_ID")
            or os.getenv("IPC_API_KEY")  # fallback for your current .env
        )
        if not self.client_id:
            raise IDMCClientError(
                "IDMC_CLIENT_ID is not set. "
                "Set it in .env to the 'Access token' from the IDMC email."
            )

        self.base_url = (
            base_url
            or os.getenv("IDMC_BASE_URL")
            or "https://helix-tools-api.idmcdb.org/external-api"
        ).rstrip("/")

        self.country_iso3 = (country_iso3 or os.getenv("IDMC_COUNTRY_ISO3") or "SDN").upper()
        self.country_name = country_name or os.getenv("IDMC_COUNTRY_NAME") or "Sudan"

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ---------------- HTTP helper ---------------- #

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Low-level helper for GET requests.
        Automatically injects client_id and format=json.
        """
        url = f"{self.base_url}{path}"
        params = dict(params or {})
        params.setdefault("client_id", self.client_id)
        params.setdefault("format", "json")

        resp = self.session.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            raise IDMCClientError(
                f"IDMC API {url} returned {resp.status_code}: {resp.text[:300]}"
            )

        try:
            return resp.json()
        except Exception as e:
            raise IDMCClientError(f"Failed to parse IDMC JSON from {url}: {e}") from e

    # ---------------- Normalization helpers ---------------- #

    @staticmethod
    def _normalize_records(data: Any) -> List[Dict[str, Any]]:
        """
        Try to extract a flat list of records from various possible envelope formats.
        The IDMC API returns paginated responses like:
            {
              "last_updated": "2024-05-13",
              "count": 123,
              "next": "...",
              "previous": null,
              "results": [ {...}, {...} ]
            }
        """
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("results", "data", "records", "items"):
                v = data.get(key)
                if isinstance(v, list):
                    return v

        return []

    def _get_country_series(self, path: str) -> List[Dict[str, Any]]:
        """
        Fetch time-series for a single country from either
        /gidd/conflicts/ or /gidd/disasters/.

        Returns a list of dicts:
            {
              "year": int,
              "new_displacement": int,
              "country_name": str | None,
              "iso3": str | None,
            }
        """
        data = self._get(path, params={"iso3__iexact": self.country_iso3})
        records = self._normalize_records(data)
        series: List[Dict[str, Any]] = []

        for rec in records:
            # Year
            year_raw = rec.get("year")
            try:
                year = int(year_raw)
            except (TypeError, ValueError):
                continue

            # new_displacement (may be null)
            nd_raw = rec.get("new_displacement")
            try:
                nd_val = int(nd_raw) if nd_raw is not None else 0
            except (TypeError, ValueError):
                nd_val = 0

            series.append(
                {
                    "year": year,
                    "new_displacement": nd_val,
                    "country_name": rec.get("country_name"),
                    "iso3": rec.get("iso3"),
                }
            )

        return series

    def _fallback_displacements_snapshot(self) -> Optional[IDMCSnapshot]:
        """
        Fallback using /gidd/displacements/ (combined conflict+disaster) if needed.

        This uses the fields:
          - iso3
          - country_name
          - year
          - conflict_new_displacement
          - disaster_new_displacement
        as seen from:
          curl -s ".../gidd/displacements/?client_id=...&format=json" | jq '.results[0]'
        """
        try:
            data = self._get("/gidd/displacements/", params={"iso3__iexact": self.country_iso3})
        except IDMCClientError as e:
            print(f"[IDMCClient] Fallback /gidd/displacements/ failed: {e}")
            return None

        records = self._normalize_records(data)
        if not records:
            return None

        def _year(rec: Dict[str, Any]) -> int:
            try:
                return int(rec.get("year") or 0)
            except (TypeError, ValueError):
                return 0

        latest = max(records, key=_year)

        def _to_int(val: Any) -> int:
            try:
                return int(val)
            except (TypeError, ValueError):
                return 0

        year = _to_int(latest.get("year"))
        iso3 = str(latest.get("iso3") or self.country_iso3)
        country_name = str(latest.get("country_name") or self.country_name)

        conflict_nd = _to_int(latest.get("conflict_new_displacement"))
        disaster_nd = _to_int(latest.get("disaster_new_displacement"))
        total_nd = conflict_nd + disaster_nd

        return IDMCSnapshot(
            country=country_name,
            iso3=iso3,
            year=year,
            conflict_new_displacements=conflict_nd,
            disaster_new_displacements=disaster_nd,
            total_new_displacements=total_nd,
        )

    # ---------------- Public: GIDD snapshot ---------------- #

    def get_country_gidd_snapshot(self) -> Optional[IDMCSnapshot]:
        """
        Combine the GIDD conflict and disaster time series for one country
        and return the latest-year snapshot.

        Main endpoints used (from the docs):
          - GET /external-api/gidd/conflicts/?client_id=...&iso3__iexact=SDN
          - GET /external-api/gidd/disasters/?client_id=...&iso3__iexact=SDN
        """
        try:
            conflict_series = self._get_country_series("/gidd/conflicts/")
        except IDMCClientError as e:
            print(f"[IDMCClient] Error fetching /gidd/conflicts/: {e}")
            conflict_series = []

        try:
            disaster_series = self._get_country_series("/gidd/disasters/")
        except IDMCClientError as e:
            print(f"[IDMCClient] Error fetching /gidd/disasters/: {e}")
            disaster_series = []

        # If both are completely empty, try the combined /displacements/ endpoint as fallback
        if not conflict_series and not disaster_series:
            return self._fallback_displacements_snapshot()

        # Collect all years where we have at least one data point
        years = {entry["year"] for entry in conflict_series} | {
            entry["year"] for entry in disaster_series
        }
        if not years:
            return self._fallback_displacements_snapshot()

        latest_year = max(years)

        def _get_for_year(series: List[Dict[str, Any]], year: int) -> int:
            for rec in series:
                if rec["year"] == year:
                    return rec["new_displacement"]
            return 0

        conflict_nd = _get_for_year(conflict_series, latest_year)
        disaster_nd = _get_for_year(disaster_series, latest_year)
        total_nd = conflict_nd + disaster_nd

        # Prefer names/iso from one of the series, fall back to env values
        probe = (conflict_series or disaster_series)[0]
        country_name = str(probe.get("country_name") or self.country_name)
        iso3 = str(probe.get("iso3") or self.country_iso3)

        return IDMCSnapshot(
            country=country_name,
            iso3=iso3,
            year=latest_year,
            conflict_new_displacements=conflict_nd,
            disaster_new_displacements=disaster_nd,
            total_new_displacements=total_nd,
        )

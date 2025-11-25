# backend/app/services/ipc_client.py

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()


class IPCClientError(RuntimeError):
    """Raised when something goes wrong while calling the IPC API."""
    pass


IPC_PHASE_LABELS = {
    1: "Minimal",
    2: "Stressed",
    3: "Crisis",
    4: "Emergency",
    5: "Catastrophe/Famine",
}


class IPCClient:
    """
    Wrapper around the IPC-CH API.

    Env vars:
        IPC_API_KEY          - required API key (used as ?key= in query string)
        IPC_BASE_URL         - e.g. https://api.ipcinfo.org
        IPC_COUNTRY_ENDPOINT - e.g. /country  (MUST be a path, not full URL)
        IPC_COUNTRY_CODE     - e.g. SDN
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        country_endpoint: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> None:
        # --- API key ---
        self.api_key = api_key or os.getenv("IPC_API_KEY")
        if not self.api_key:
            raise IPCClientError("IPC_API_KEY must be set in environment.")

        # --- Base URL ---
        self.base_url = (base_url or os.getenv("IPC_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise IPCClientError("IPC_BASE_URL must be set in environment.")

        # --- Endpoint path (ensure it's NOT a full URL) ---
        raw_endpoint = country_endpoint or os.getenv(
            "IPC_COUNTRY_ENDPOINT",
            "/country",  # sensible default
        )

        # if someone put a full URL here, strip to just the path
        if raw_endpoint.startswith("http://") or raw_endpoint.startswith("https://"):
            parsed = urlparse(raw_endpoint)
            raw_endpoint = parsed.path or "/country"

        if not raw_endpoint.startswith("/"):
            raw_endpoint = "/" + raw_endpoint

        self.country_endpoint = raw_endpoint

        # Country code (likely ISO3)
        self.country_code = country_code or os.getenv("IPC_COUNTRY_CODE", "SDN")

        # Simple requests session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "sudan-cram-ipc-client/1.0",
            }
        )

    def _country_url(self) -> str:
        return f"{self.base_url}{self.country_endpoint}"

    def fetch_latest_country_analysis(self) -> pd.DataFrame:
        """
        Fetch the latest IPC analysis for the configured country and
        normalize it to one row per admin region.

        Returns DataFrame with:
            region
            ipc_phase (int)
            ipc_phase_label
            ipc_population_phase3plus (int)
            analysis_period (str)
        """
        url = self._country_url()

        # Key point: IPC API wants ?key= in QUERY STRING
        params: Dict[str, Any] = {
            # Country parameter name may vary, so we send both common variants.
            "code": self.country_code,
            "countryCode": self.country_code,
            # Auth:
            "key": self.api_key,
            # "latest" flag – if IPC supports it
            "latest": "true",
        }

        try:
            resp = self.session.get(url, params=params, timeout=30)
        except Exception as e:
            raise IPCClientError(f"Failed to call IPC API: {e}") from e

        if resp.status_code != 200:
            raise IPCClientError(
                f"IPC API non-200 response: {resp.status_code} {resp.text[:300]}"
            )

        try:
            data = resp.json()
        except Exception as e:
            raise IPCClientError(f"Failed to parse IPC JSON: {e}") from e

        # The IPC API may return a dict or a list; adapt as needed.
        if isinstance(data, dict):
            if "areas" in data and isinstance(data["areas"], list):
                records = data["areas"]
            elif "results" in data and isinstance(data["results"], list):
                records = data["results"]
            else:
                # You will probably need to adapt this once you see the actual JSON.
                raise IPCClientError(
                    f"Unexpected IPC JSON structure: top-level keys={list(data.keys())}"
                )
        elif isinstance(data, list):
            records = data
        else:
            raise IPCClientError(f"Unexpected IPC JSON type: {type(data)}")

        return self._normalize_response_to_df(records)

    def _normalize_response_to_df(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert raw IPC area records into the internal DataFrame schema.

        You WILL likely need to tweak field names here based on the real IPC response.
        """
        if not records:
            return pd.DataFrame(
                columns=[
                    "region",
                    "ipc_phase",
                    "ipc_phase_label",
                    "ipc_population_phase3plus",
                    "analysis_period",
                ]
            )

        rows: List[Dict[str, Any]] = []

        for rec in records:
            # ---- 1) Region/admin name -------------------------------
            region = (
                rec.get("admin1Name")
                or rec.get("areaName")
                or rec.get("adm_name")
                or rec.get("region")
            )
            if not region:
                # skip records with no recognizable region
                continue
            region = str(region).strip()

            # ---- 2) IPC phase (1-5) --------------------------------
            phase_raw = (
                rec.get("phase")
                or rec.get("phase_classification")
                or rec.get("ipcPhase")
            )
            try:
                phase = int(phase_raw) if phase_raw is not None else 0
            except (ValueError, TypeError):
                phase = 0

            phase_label = IPC_PHASE_LABELS.get(phase, "Unknown")

            # ---- 3) Population in phase 3+ -------------------------
            pop_3plus = (
                rec.get("population_phase3plus")
                or rec.get("pop_phase3plus")
                or rec.get("phase3plus_population")
                or 0
            )
            try:
                pop_3plus = int(pop_3plus)
            except (ValueError, TypeError):
                pop_3plus = 0

            # ---- 4) Analysis period --------------------------------
            analysis_period = (
                rec.get("analysis_period")
                or rec.get("analysisDate")
                or rec.get("period")
                or ""
            )
            analysis_period = str(analysis_period).strip()

            rows.append(
                {
                    "region": region,
                    "ipc_phase": phase,
                    "ipc_phase_label": phase_label,
                    "ipc_population_phase3plus": pop_3plus,
                    "analysis_period": analysis_period,
                }
            )

        return pd.DataFrame(rows)

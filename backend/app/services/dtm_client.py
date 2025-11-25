# backend/app/services/dtm_client.py

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from dtmapi import DTMApi  # pip install dtmapi

load_dotenv()


class DTMClientError(Exception):
    """Custom error type for DTM client issues (config, API failures, etc.)."""
    pass


class DTMClient:
    """
    Thin wrapper around the official `dtmapi` Python client (DTM API v3).

    - Uses your DTM_API_KEY (Ocp-Apim-Subscription-Key) from environment.
    - Defaults to DTM_COUNTRY_NAME (e.g. 'Sudan').

    Main helpers:
        - fetch_idp_admin1_latest(): latest IDP snapshot per admin1Name
        - fetch_idp_admin0_latest(): latest country-level snapshot
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        country_name: Optional[str] = None,
    ) -> None:
        # API key from env or argument
        self.api_key = api_key or os.getenv("DTM_API_KEY")
        if not self.api_key:
            raise DTMClientError(
                "DTM_API_KEY is not set. "
                "Set it to your 'Ocp-Apim-Subscription-Key' from the DTM API portal."
            )

        # Country name (DTM uses full country name, not ISO3)
        self.country_name = country_name or os.getenv("DTM_COUNTRY_NAME") or "Sudan"

        try:
            # Instantiate official client (v3 is default)
            self.api = DTMApi(subscription_key=self.api_key, api_version="v3")
        except Exception as e:
            raise DTMClientError(f"Failed to initialize DTMApi client: {e}") from e

    # ------------------------------------------------------------------
    # IDP ADMIN1 (STATE-LEVEL) – LATEST SNAPSHOT PER STATE
    # ------------------------------------------------------------------
    def fetch_idp_admin1_latest(
        self,
        country_name: Optional[str] = None,
        admin1_name: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch IDP data at Admin1 level and keep ONLY the latest reporting date
        per admin1Name, when possible.

        If the expected columns are missing, returns the raw DataFrame
        so you can still inspect what the API returns.

        Args:
            country_name: override default country name (e.g. 'Sudan')
            admin1_name: optional filter for one state
            from_date: optional ISO date 'YYYY-MM-DD'
            to_date: optional ISO date 'YYYY-MM-DD'

        Returns:
            pandas.DataFrame (one row per admin1Name where possible)
        """
        params = {
            "CountryName": country_name or self.country_name,
        }
        if admin1_name:
            params["Admin1Name"] = admin1_name
        if from_date:
            params["FromReportingDate"] = from_date
        if to_date:
            params["ToReportingDate"] = to_date

        try:
            df = self.api.get_idp_admin1_data(to_pandas=True, **params)
        except Exception as e:
            raise DTMClientError(f"DTM API admin1 request failed: {e}") from e

        # dtmapi may return dict-like -> normalize
        if isinstance(df, dict):
            df = pd.DataFrame(df)

        if df is None or df.empty:
            return pd.DataFrame()

        cols = list(df.columns)

        # Find date column (support both 'reportingDate' and 'ReportingDate')
        date_col = None
        for candidate in ("reportingDate", "ReportingDate"):
            if candidate in cols:
                date_col = candidate
                break

        # Find admin1 column (support both 'admin1Name' and 'Admin1Name')
        admin1_col = None
        for candidate in ("admin1Name", "Admin1Name"):
            if candidate in cols:
                admin1_col = candidate
                break

        # Parse date if present
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])

        if df.empty:
            return df

        # Latest per state
        if admin1_col and date_col:
            idx = df.groupby(admin1_col)[date_col].idxmax()
            latest = df.loc[idx].reset_index(drop=True)
            return latest

        # If only date exists -> latest overall
        if date_col:
            latest = df.sort_values(date_col).tail(1).reset_index(drop=True)
            return latest

        # No usable date col -> return raw
        return df

    # ------------------------------------------------------------------
    # ADMIN0 (COUNTRY-LEVEL) – LATEST SNAPSHOT
    # ------------------------------------------------------------------
    def fetch_idp_admin0_latest(
        self,
        country_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch IDP data at Admin0 (country) level and keep the latest snapshot
        when possible. Falls back to raw DataFrame if no date column exists.
        """
        params = {
            "CountryName": country_name or self.country_name,
        }

        try:
            df = self.api.get_idp_admin0_data(to_pandas=True, **params)
        except Exception as e:
            raise DTMClientError(f"DTM API admin0 request failed: {e}") from e

        if isinstance(df, dict):
            df = pd.DataFrame(df)

        if df is None or df.empty:
            return pd.DataFrame()

        cols = list(df.columns)
        date_col = None
        for candidate in ("reportingDate", "ReportingDate"):
            if candidate in cols:
                date_col = candidate
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            if not df.empty:
                idx = df[date_col].idxmax()
                df = df.loc[[idx]].reset_index(drop=True)

        return df

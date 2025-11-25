# backend/app/services/humanitarian_service.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd

from app.services.dtm_client import DTMClient, DTMClientError
from app.services.ipc_client import IPCClient, IPCClientError
from app.services.idmc_client import IDMCClient, IDMCSnapshot, IDMCClientError


class HumanitarianServiceError(Exception):
    """Custom error for HumanitarianService-level failures."""
    pass


@dataclass
class HumanitarianRegionSummary:
    """
    Unified humanitarian snapshot for one admin1 region.
    """
    region: str
    idps: int = 0
    idps_last_reported: Optional[str] = None

    ipc_phase: Optional[int] = None
    ipc_phase_label: Optional[str] = None
    ipc_population_phase3plus: int = 0
    analysis_period: Optional[str] = None

    humanitarian_risk_score: float = 0.0
    humanitarian_risk_level: str = "UNKNOWN"


class HumanitarianService:
    """
    Service that combines:
      - DTM: internal displacement (IDPs) per admin1
      - IPC: food insecurity phase per admin1
      - IDMC: country-level GIDD snapshot
    into a unified humanitarian risk view.
    """

    def __init__(
        self,
        dtm_client: Optional[DTMClient] = None,
        ipc_client: Optional[IPCClient] = None,
        idmc_client: Optional[IDMCClient] = None,
    ) -> None:
        try:
            self.dtm_client = dtm_client or DTMClient()
        except DTMClientError as e:
            raise HumanitarianServiceError(f"Failed to init DTM client: {e}") from e

        # IPC is optional – if it fails, we just operate without it
        try:
            self.ipc_client = ipc_client or IPCClient()
        except Exception as e:
            print(f"[HumanitarianService] IPC client init error: {e}")
            self.ipc_client = None

        # IDMC is also optional – summary still works without it
        try:
            self.idmc_client = idmc_client or IDMCClient()
        except Exception as e:
            print(f"[HumanitarianService] IDMC client init error: {e}")
            self.idmc_client = None

    # ---------------------- Helpers ---------------------- #

    def _normalize_df_regions(self, df: pd.DataFrame, region_col: str) -> pd.DataFrame:
        """
        Ensure we have a canonical 'region' column and clean it.
        """
        if df is None or df.empty:
            return pd.DataFrame(columns=["region"])

        df = df.copy()

        if region_col not in df.columns:
            if "region" in df.columns:
                region_col = "region"
            else:
                available = ", ".join(df.columns)
                raise KeyError(
                    f"Region column '{region_col}' not found. "
                    f"Available columns: {available}"
                )

        if region_col != "region":
            df.rename(columns={region_col: "region"}, inplace=True)

        df["region"] = df["region"].astype(str).str.strip()
        df = df[df["region"] != ""]

        return df

    @staticmethod
    def _risk_level_from_score(score: float) -> str:
        if score >= 8:
            return "EXTREME"
        if score >= 6:
            return "VERY HIGH"
        if score >= 4:
            return "HIGH"
        if score >= 2:
            return "MODERATE"
        return "LOW"

    # ---------------------- DTM ---------------------- #

    def get_dtm_snapshot(self) -> pd.DataFrame:
        """
        Fetch latest DTM IDP data and normalize to:

            region, idps, dtm_reporting_date

        aggregated at admin1 level.
        """
        try:
            df = self.dtm_client.fetch_idp_admin1_latest()
        except Exception as e:
            print(f"[HumanitarianService] DTM error: {e}")
            return pd.DataFrame(columns=["region", "idps", "dtm_reporting_date"])

        if df is None or df.empty:
            return pd.DataFrame(columns=["region", "idps", "dtm_reporting_date"])

        # Detect admin1 name column
        region_col = None
        for candidate in ("admin1Name", "Admin1Name", "ADM1_NAME", "admin1_name"):
            if candidate in df.columns:
                region_col = candidate
                break

        if region_col is None:
            for candidate in ("admin0Name", "Admin0Name", "country", "Country"):
                if candidate in df.columns:
                    region_col = candidate
                    break

        if region_col is None:
            region_col = "region"

        df = self._normalize_df_regions(df, region_col)

        # IDP count column
        idp_col = None
        for candidate in ("numPresentIdpInd", "NumPresentIdpInd", "idps", "IDPs"):
            if candidate in df.columns:
                idp_col = candidate
                break

        if idp_col:
            df["idps"] = (
                pd.to_numeric(df[idp_col], errors="coerce")
                .fillna(0)
                .astype(int)
            )
        else:
            df["idps"] = 0

        # Reporting date
        date_col = None
        for candidate in ("reportingDate", "ReportingDate", "reporting_date"):
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df["dtm_reporting_date"] = df[date_col].dt.date.astype(str)
        else:
            df["dtm_reporting_date"] = None

        grouped = (
            df.groupby("region", as_index=False)
            .agg(
                idps=("idps", "sum"),
                dtm_reporting_date=("dtm_reporting_date", "max"),
            )
        )

        return grouped

    # ---------------------- IPC ---------------------- #

    def get_ipc_snapshot(self) -> pd.DataFrame:
        """
        Fetch latest IPC analysis for the configured country and normalize to:

            region,
            ipc_phase,
            ipc_phase_label,
            ipc_population_phase3plus,
            analysis_period

        If IPC API fails or returns nothing, returns an empty DataFrame with
        the right columns so downstream code keeps working.
        """
        empty = pd.DataFrame(
            columns=[
                "region",
                "ipc_phase",
                "ipc_phase_label",
                "ipc_population_phase3plus",
                "analysis_period",
            ]
        )

        if self.ipc_client is None:
            return empty

        try:
            df = self.ipc_client.fetch_latest_country_analysis()
        except IPCClientError as e:
            print(f"[HumanitarianService] IPC error: {e}")
            return empty
        except Exception as e:
            print(f"[HumanitarianService] Unexpected IPC error: {e}")
            return empty

        if df is None or df.empty:
            return empty

        df = df.copy()

        # Region column may already be 'region'; if not, try some common variants
        region_col = "region"
        if "region" not in df.columns:
            for candidate in (
                "admin1_name",
                "Admin1Name",
                "ADM1_NAME",
                "areaName",
                "AreaName",
            ):
                if candidate in df.columns:
                    region_col = candidate
                    break
        df = self._normalize_df_regions(df, region_col)

        # Ensure core IPC columns exist
        if "ipc_phase" not in df.columns:
            df["ipc_phase"] = 0
        df["ipc_phase"] = pd.to_numeric(df["ipc_phase"], errors="coerce").fillna(0).astype(int)

        if "ipc_phase_label" not in df.columns:
            df["ipc_phase_label"] = df["ipc_phase"].map(
                {
                    1: "Minimal",
                    2: "Stressed",
                    3: "Crisis",
                    4: "Emergency",
                    5: "Famine",
                }
            ).fillna("Unknown")

        if "ipc_population_phase3plus" not in df.columns:
            df["ipc_population_phase3plus"] = 0
        df["ipc_population_phase3plus"] = (
            pd.to_numeric(df["ipc_population_phase3plus"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        if "analysis_period" not in df.columns:
            df["analysis_period"] = ""

        # Aggregate at region level
        grouped = (
            df.groupby("region", as_index=False)
            .agg(
                ipc_phase=("ipc_phase", "max"),
                ipc_phase_label=("ipc_phase_label", "first"),
                ipc_population_phase3plus=("ipc_population_phase3plus", "sum"),
                analysis_period=("analysis_period", "first"),
            )
        )

        return grouped

    # ---------------------- IDMC ---------------------- #

    def get_idmc_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Country-level GIDD snapshot from IDMC.

        Returns:
            dict or None if IDMC not configured / no data.
        """
        if self.idmc_client is None:
            return None

        try:
            snap: Optional[IDMCSnapshot] = self.idmc_client.get_country_gidd_snapshot()
        except IDMCClientError as e:
            print(f"[HumanitarianService] IDMC error: {e}")
            return None
        except Exception as e:
            print(f"[HumanitarianService] Unexpected IDMC error: {e}")
            return None

        if not snap:
            return None

        return {
            "country": snap.country,
            "iso3": snap.iso3,
            "year": snap.year,
            "conflict_new_displacements": snap.conflict_new_displacements,
            "disaster_new_displacements": snap.disaster_new_displacements,
            "total_new_displacements": snap.total_new_displacements,
        }

    # ---------------------- Combined summary ---------------------- #

    def get_humanitarian_summary(self) -> List[HumanitarianRegionSummary]:
        """
        Combine DTM and IPC into a per-region humanitarian risk summary.

        Risk score:
          - IDPs normalized 0–10
          - IPC phase (1..5) mapped to 0–10 (1→0, 5→10)
          - Score = 0.4 * IDPs_norm + 0.6 * IPC_norm
        """
        dtm_df = self.get_dtm_snapshot()
        ipc_df = self.get_ipc_snapshot()

        dtm_empty = dtm_df is None or dtm_df.empty
        ipc_empty = ipc_df is None or ipc_df.empty

        if dtm_empty and ipc_empty:
            return []

        if dtm_empty:
            merged = ipc_df.copy()
            merged["idps"] = 0
            merged["dtm_reporting_date"] = None
        elif ipc_empty:
            merged = dtm_df.copy()
            merged["ipc_phase"] = 0
            merged["ipc_phase_label"] = "Unknown"
            merged["ipc_population_phase3plus"] = 0
            merged["analysis_period"] = None
        else:
            merged = dtm_df.merge(ipc_df, on="region", how="outer", suffixes=("", "_ipc"))

        # Fill numeric fields
        for col in ("idps", "ipc_phase", "ipc_population_phase3plus"):
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

        merged["ipc_phase"] = merged.get("ipc_phase", 0).astype(int)

        # Normalize IDPs → 0–10
        if "idps" in merged.columns:
            idps_vals = merged["idps"].values.astype(float)
            if idps_vals.max() == idps_vals.min():
                idps_norm = np.zeros_like(idps_vals)
            else:
                idps_norm = 10.0 * (idps_vals - idps_vals.min()) / (
                    idps_vals.max() - idps_vals.min()
                )
        else:
            idps_norm = np.zeros(len(merged))

        # IPC phase 1..5 → 0..10 (1→0, 5→10)
        ipc_phase_vals = merged.get("ipc_phase", 0).values.astype(float)
        ipc_norm = np.clip(((ipc_phase_vals - 1) / 4.0) * 10.0, 0.0, 10.0)

        score = 0.4 * idps_norm + 0.6 * ipc_norm
        merged["humanitarian_risk_score"] = np.round(score, 2)
        merged["humanitarian_risk_level"] = merged["humanitarian_risk_score"].apply(
            self._risk_level_from_score
        )

        summaries: List[HumanitarianRegionSummary] = []
        for _, row in merged.iterrows():
            idps_last_reported = row.get("dtm_reporting_date")
            ipc_pop_3plus = int(row.get("ipc_population_phase3plus", 0) or 0)
            analysis_period = row.get("analysis_period")
            if isinstance(analysis_period, float) and np.isnan(analysis_period):
                analysis_period = None

            summaries.append(
                HumanitarianRegionSummary(
                    region=row.get("region", ""),
                    idps=int(row.get("idps", 0) or 0),
                    idps_last_reported=idps_last_reported,
                    ipc_phase=int(row.get("ipc_phase", 0) or 0),
                    ipc_phase_label=row.get("ipc_phase_label") or "Unknown",
                    ipc_population_phase3plus=ipc_pop_3plus,
                    analysis_period=analysis_period,
                    humanitarian_risk_score=float(
                        row.get("humanitarian_risk_score", 0.0) or 0.0
                    ),
                    humanitarian_risk_level=row.get("humanitarian_risk_level")
                    or "UNKNOWN",
                )
            )

        summaries.sort(key=lambda s: s.humanitarian_risk_score, reverse=True)
        return summaries

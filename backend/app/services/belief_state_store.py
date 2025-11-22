# app/services/belief_state_store.py

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class BeliefStateStore:
    """
    JSON-backed store for region-level 'belief state'.

    One JSON file with a dict of:

        {
          "<region-name>": {
            "region": "Khartoum",
            "last_baseline_run_id": "abc123",
            "last_scenario_run_id": "def456",
            "trend_classification": "ESCALATING",
            "armed_clash_likelihood": 80,
            "civilian_targeting_likelihood": 55,
            "risk_level_override": null,
            "active_interventions": [
              {
                "id": "<uuid>",
                "description": "Deploy UN observers...",
                "scenario_run_id": "def456",
                "status": "PLANNED|ONGOING|COMPLETED|CANCELLED",
                "notes": "Short comment",
                "created_at": "ISO-8601",
                "updated_at": "ISO-8601"
              }
            ],
            "notes": "Free-form notes",
            "created_at": "ISO-8601",
            "updated_at": "ISO-8601"
          },
          ...
        }
    """

    def __init__(
        self,
        base_path: str = "data/belief_state",
        filename: str = "belief_state.json",
    ) -> None:
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.file_path = os.path.join(base_path, filename)

        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the full belief-state map from disk.

        Returns:
            dict mapping region -> belief_state.
        """
        if not os.path.exists(self.file_path):
            return {}

        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    return {}
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    def _save_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Persist the full belief-state map to disk.
        """
        tmp = self.file_path + ".tmp"

        with self._lock:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.file_path)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def get_region_state(self, region: str) -> Dict[str, Any]:
        """
        Fetch the belief state for a given region.

        Returns a minimal default if the region has no stored state yet.
        """
        region_key = (region or "").strip()
        all_data = self._load_all()
        state = all_data.get(region_key)

        if state is None:
            # Provide a skeletal default
            now = self._now_iso()
            state = {
                "region": region_key,
                "last_baseline_run_id": None,
                "last_scenario_run_id": None,
                "trend_classification": None,
                "armed_clash_likelihood": None,
                "civilian_targeting_likelihood": None,
                "risk_level_override": None,
                "active_interventions": [],
                "notes": "",
                "created_at": now,
                "updated_at": now,
            }
            all_data[region_key] = state
            self._save_all(all_data)

        return state

    def update_baseline(
        self,
        region: str,
        run_id: str,
        trend_classification: Optional[str],
        armed_clash_likelihood: Optional[float],
        civilian_targeting_likelihood: Optional[float],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the baseline belief state for a region using an analysis run.

        This should typically be called after a baseline `/analysis/run`.
        """
        region_key = (region or "").strip()
        all_data = self._load_all()
        state = all_data.get(region_key)

        now = self._now_iso()

        if state is None:
            state = {
                "region": region_key,
                "created_at": now,
                "active_interventions": [],
            }

        state["region"] = region_key
        state["last_baseline_run_id"] = run_id
        # Keep last_scenario_run_id as-is if present
        state.setdefault("last_scenario_run_id", None)

        state["trend_classification"] = trend_classification
        state["armed_clash_likelihood"] = armed_clash_likelihood
        state["civilian_targeting_likelihood"] = civilian_targeting_likelihood
        state.setdefault("risk_level_override", None)

        if notes is not None:
            existing_notes = state.get("notes") or ""
            if existing_notes:
                state["notes"] = existing_notes + "\n" + notes
            else:
                state["notes"] = notes
        else:
            state.setdefault("notes", "")

        state.setdefault("active_interventions", [])
        state.setdefault("created_at", now)
        state["updated_at"] = now

        all_data[region_key] = state
        self._save_all(all_data)
        return state

    def apply_interventions(
        self,
        region: str,
        interventions: List[Dict[str, Any]],
        scenario_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add / update interventions in the belief state for a region.

        Each intervention dict is expected to contain:
          - description: str
          - status: PLANNED|ONGOING|COMPLETED|CANCELLED (default: PLANNED)
          - notes: Optional[str]
          - id: Optional[str] (if omitted, a new one is generated)

        Args:
            region: Region name.
            interventions: List of interventions to add or update.
            scenario_run_id: Optional scenario run_id this set is based on.

        Returns:
            Updated belief state for the region.
        """
        region_key = (region or "").strip()
        all_data = self._load_all()
        state = all_data.get(region_key) or self.get_region_state(region_key)

        now = self._now_iso()
        existing: List[Dict[str, Any]] = state.get("active_interventions") or []

        # Build a map for quick lookup by id
        by_id: Dict[str, Dict[str, Any]] = {}
        for iv in existing:
            iv_id = str(iv.get("id"))
            if iv_id:
                by_id[iv_id] = iv

        for iv in interventions:
            iv_id = iv.get("id")
            if iv_id:
                iv_id = str(iv_id)
            else:
                iv_id = uuid.uuid4().hex

            status = str(iv.get("status", "PLANNED")).upper()
            desc = str(iv.get("description", "")).strip()
            notes = iv.get("notes")

            existing_iv = by_id.get(iv_id)
            if existing_iv is None:
                # New intervention
                new_iv = {
                    "id": iv_id,
                    "description": desc,
                    "status": status,
                    "notes": notes or "",
                    "scenario_run_id": scenario_run_id,
                    "created_at": now,
                    "updated_at": now,
                }
                existing.append(new_iv)
                by_id[iv_id] = new_iv
            else:
                # Update existing intervention
                if desc:
                    existing_iv["description"] = desc
                existing_iv["status"] = status
                if notes is not None:
                    existing_iv["notes"] = notes
                if scenario_run_id is not None:
                    existing_iv["scenario_run_id"] = scenario_run_id
                existing_iv["updated_at"] = now

        state["active_interventions"] = existing
        state["last_scenario_run_id"] = scenario_run_id or state.get(
            "last_scenario_run_id"
        )
        state["updated_at"] = now

        all_data[region_key] = state
        self._save_all(all_data)
        return state


# ---------------------------------------------------------------------- #
# Dependency helper                                                     #
# ---------------------------------------------------------------------- #

_belief_store_singleton: Optional[BeliefStateStore] = None


def get_belief_state_store() -> BeliefStateStore:
    global _belief_store_singleton
    if _belief_store_singleton is None:
        _belief_store_singleton = BeliefStateStore()
    return _belief_store_singleton

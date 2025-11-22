# app/services/feedback_store.py

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


class FeedbackStore:
    """
    Simple JSONL-backed feedback storage for the SudanCRAM system.

    Each feedback item is a JSON object written as one line in a .jsonl file.
    This is intentionally simple and append-only, so it works on Render / bare
    VMs / Docker without needing a database.

    Expected feedback schema (not enforced here, but used by the API layer):

        {
          "id": "<uuid>",                    # added automatically if missing
          "run_id": "<analysis_run_id>",     # required by the API
          "region": "Khartoum",
          "source": "analyst" | "partner" | "system",
          "feedback_type": "CORRECTION" | "CONFIRMATION" | "COMMENT",
          "comment": "string",
          "severity": "LOW" | "MEDIUM" | "HIGH",
          "created_by": "username or email",
          "created_at": "ISO-8601 timestamp",  # added automatically
          "updated_at": "ISO-8601 timestamp",  # added automatically
          "status": "OPEN" | "RESOLVED" | "DISMISSED"
        }

    The API layer (FastAPI) is responsible for validating inputs with Pydantic
    models. This store is a thin persistence + query layer.
    """

    def __init__(
        self,
        base_path: str = "data/feedback",
        filename: str = "feedback.jsonl",
    ) -> None:
        """
        Create a FeedbackStore.

        Args:
            base_path: Directory where the feedback log file will live.
            filename:  Name of the JSONL file to use.
        """
        self.base_path = base_path
        self.file_path = os.path.join(base_path, filename)
        os.makedirs(self.base_path, exist_ok=True)

        # Simple in-process lock to avoid concurrent write corruption
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now_iso() -> str:
        """Return current UTC time in ISO-8601 format."""
        return datetime.utcnow().isoformat()

    def _safe_iter_rows(self) -> Iterable[Dict[str, Any]]:
        """
        Iterate over all feedback rows in the JSONL file.

        - Skips empty lines.
        - Ignores JSON parsing errors instead of crashing the app.
        """
        if not os.path.exists(self.file_path):
            return

        # We don't strictly need the lock for reads, but it makes behavior
        # more predictable under heavy concurrent writes/reads.
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            # Corrupt line: skip it and continue
                            continue
                        if isinstance(obj, dict):
                            yield obj
            except FileNotFoundError:
                # File could have been removed between the existence check and open
                return

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Append a feedback item to the JSONL file.

        Args:
            data: Dictionary containing feedback fields. At minimum, the API
                  should have validated and provided: run_id, region, source,
                  feedback_type, comment, severity, created_by (optional).

        Returns:
            The stored feedback item with server-generated fields populated.
        """
        item: Dict[str, Any] = dict(data)  # shallow copy

        # Server-side identifiers & timestamps
        item.setdefault("id", uuid.uuid4().hex)
        created_at = self._now_iso()
        item.setdefault("created_at", created_at)
        item.setdefault("updated_at", created_at)

        # Status tracking for red-team / triage flows
        # (could be extended later with more statuses)
        item.setdefault("status", "OPEN")

        # Defensive: ensure we always have run_id and region in some form,
        # even if the caller messed up (API layer should already validate).
        item.setdefault("run_id", "unknown_run")
        item.setdefault("region", "unknown_region")

        # Persist as a single line of JSON
        line = json.dumps(item, ensure_ascii=False)

        with self._lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        return item

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """
        Return all feedback items currently stored.

        This is mainly for admin tools or debugging, not for the main API.
        """
        return list(self._safe_iter_rows())

    def list_feedback_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Return all feedback entries associated with a specific analysis run_id.

        Args:
            run_id: The run identifier returned by the analysis workflow.

        Returns:
            List of feedback dictionaries (possibly empty).
        """
        results: List[Dict[str, Any]] = []
        for row in self._safe_iter_rows():
            if row.get("run_id") == run_id:
                results.append(row)
        return results

    def list_feedback_for_region(self, region: str) -> List[Dict[str, Any]]:
        """
        Return all feedback entries associated with a specific region.

        Args:
            region: Region name (e.g. "Khartoum").

        Returns:
            List of feedback dictionaries (possibly empty).
        """
        region_normalized = (region or "").strip().lower()
        results: List[Dict[str, Any]] = []
        for row in self._safe_iter_rows():
            row_region = str(row.get("region", "")).strip().lower()
            if row_region == region_normalized:
                results.append(row)
        return results

    def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single feedback item by its unique ID.

        Args:
            feedback_id: Hex string UUID assigned when the feedback was created.

        Returns:
            Feedback dictionary if found, otherwise None.
        """
        for row in self._safe_iter_rows():
            if row.get("id") == feedback_id:
                return row
        return None

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def update_status(
        self,
        feedback_id: str,
        status: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Update the status of a feedback item (e.g. OPEN -> RESOLVED).

        Implementation note:
        - Because we use JSONL (append-only log), the simplest "update"
          pattern is: read all rows, modify the matching one in-memory,
          and rewrite the file. This is acceptable for small/medium volumes.

        Args:
            feedback_id: ID of the feedback to update.
            status:      New status string (e.g. "RESOLVED", "DISMISSED").

        Returns:
            The updated feedback item, or None if the ID was not found.
        """
        status = status.upper()
        # You could enforce allowed statuses here if you like:
        # allowed = {"OPEN", "RESOLVED", "DISMISSED"}
        # if status not in allowed: raise ValueError(...)

        rows = list(self._safe_iter_rows())
        updated_item: Optional[Dict[str, Any]] = None
        changed = False

        for row in rows:
            if row.get("id") == feedback_id:
                row["status"] = status
                row["updated_at"] = self._now_iso()
                updated_item = row
                changed = True
                break

        if not changed:
            return None

        # Rewrite file with updated content
        tmp_path = self.file_path + ".tmp"

        with self._lock:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            os.replace(tmp_path, self.file_path)

        return updated_item

    # ------------------------------------------------------------------
    # Aggregation / summary helpers
    # ------------------------------------------------------------------

    def summary_for_run(self, run_id: str) -> Dict[str, Any]:
        """
        Build a small summary of feedback for a given run.

        Useful for:
        - Dashboard badges (e.g. "3 feedback items, 1 correction (HIGH)")
        - Showing analysts what has been contested about a run.

        Returns dict like:

        {
          "run_id": "abc123",
          "total": 3,
          "by_type": {"CORRECTION": 1, "COMMENT": 2},
          "by_severity": {"LOW": 1, "MEDIUM": 1, "HIGH": 1},
          "by_status": {"OPEN": 2, "RESOLVED": 1},
          "last_updated": "2025-11-21T18:03:12.123456"
        }
        """
        items = self.list_feedback_for_run(run_id)

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        last_updated: Optional[str] = None

        for item in items:
            t = str(item.get("feedback_type", "UNKNOWN")).upper()
            s = str(item.get("severity", "UNKNOWN")).upper()
            st = str(item.get("status", "UNKNOWN")).upper()
            by_type[t] = by_type.get(t, 0) + 1
            by_severity[s] = by_severity.get(s, 0) + 1
            by_status[st] = by_status.get(st, 0) + 1

            updated_at = item.get("updated_at") or item.get("created_at")
            if isinstance(updated_at, str):
                if last_updated is None or updated_at > last_updated:
                    last_updated = updated_at

        return {
            "run_id": run_id,
            "total": len(items),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
            "last_updated": last_updated,
        }

    def summary_for_region(self, region: str) -> Dict[str, Any]:
        """
        Build a summary of feedback for a given region.

        Similar to summary_for_run, but aggregated at region level.
        """
        items = self.list_feedback_for_region(region)

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        last_updated: Optional[str] = None

        for item in items:
            t = str(item.get("feedback_type", "UNKNOWN")).upper()
            s = str(item.get("severity", "UNKNOWN")).upper()
            st = str(item.get("status", "UNKNOWN")).upper()
            by_type[t] = by_type.get(t, 0) + 1
            by_severity[s] = by_severity.get(s, 0) + 1
            by_status[st] = by_status.get(st, 0) + 1

            updated_at = item.get("updated_at") or item.get("created_at")
            if isinstance(updated_at, str):
                if last_updated is None or updated_at > last_updated:
                    last_updated = updated_at

        return {
            "region": region,
            "total": len(items),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
            "last_updated": last_updated,
        }

    # ------------------------------------------------------------------
    # Compatibility helpers for API layer
    # ------------------------------------------------------------------

    def append(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Backwards-compatible wrapper used by the API layer.
        """
        return self.append_feedback(data)

    def list_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Backwards-compatible wrapper used by the API layer.
        """
        return self.list_feedback_for_run(run_id)

    def list_by_region(self, region: str) -> List[Dict[str, Any]]:
        """
        Backwards-compatible wrapper used by the API layer.
        """
        return self.list_feedback_for_region(region)

    def list_all(self) -> List[Dict[str, Any]]:
        """
        Backwards-compatible wrapper used by the API layer.
        """
        return self.get_all_feedback()


# ----------------------------------------------------------------------
# FastAPI dependency helper
# ----------------------------------------------------------------------

_feedback_store_singleton: Optional[FeedbackStore] = None


def get_feedback_store() -> FeedbackStore:
    """
    FastAPI dependency that returns a singleton FeedbackStore instance.

    This is what `from app.services.feedback_store import get_feedback_store`
    in `app.api.feedback` expects.
    """
    global _feedback_store_singleton

    if _feedback_store_singleton is None:
        base_path = os.getenv("FEEDBACK_BASE_PATH", "data/feedback")
        filename = os.getenv("FEEDBACK_FILENAME", "feedback.jsonl")
        _feedback_store_singleton = FeedbackStore(
            base_path=base_path,
            filename=filename,
        )

    return _feedback_store_singleton

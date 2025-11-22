# app/services/report_store.py

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


class ReportStore:
    """
    JSONL-backed storage for local / analyst / partner reports.

    Each report is one JSON object per line in a `.jsonl` file.

    Example schema (not strictly enforced here):

        {
          "id": "<uuid>",                     # generated server-side
          "run_id": "<analysis_run_id>|null", # optional link to an analysis run
          "region": "Khartoum",
          "source": "local_actor|ngo|analyst|media|system",
          "report_type": "FIELD_REPORT|SECURITY_UPDATE|COMMENT|OTHER",
          "language": "en",
          "tags": ["market", "checkpoint"],
          "text": "Free-form report text...",
          "metadata": { ... },                # optional structured info
          "created_by": "username or email",
          "created_at": "ISO-8601",
          "updated_at": "ISO-8601"
        }
    """

    def __init__(
        self,
        base_path: str = "data/reports",
        filename: str = "reports.jsonl",
    ) -> None:
        self.base_path = base_path
        self.file_path = os.path.join(base_path, filename)
        os.makedirs(self.base_path, exist_ok=True)

        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    def _safe_iter_rows(self) -> Iterable[Dict[str, Any]]:
        """
        Iterate over all stored reports, skipping bad lines instead of crashing.
        """
        if not os.path.exists(self.file_path):
            return

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
                            continue
                        if isinstance(obj, dict):
                            yield obj
            except FileNotFoundError:
                return

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def append_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Append a new report.

        The API layer should have validated required fields, but we add:
        - id
        - created_at / updated_at

        Args:
            data: dict with at least region, source, report_type, text.

        Returns:
            The stored report with server-generated fields.
        """
        item: Dict[str, Any] = dict(data)

        item.setdefault("id", uuid.uuid4().hex)
        now = self._now_iso()
        item.setdefault("created_at", now)
        item.setdefault("updated_at", now)

        # Normalize some fields
        item.setdefault("tags", [])
        item.setdefault("language", "en")
        item.setdefault("metadata", {})

        # Optional fields
        item.setdefault("run_id", None)
        item.setdefault("created_by", "unknown")

        line = json.dumps(item, ensure_ascii=False)

        with self._lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        return item

    def list_reports(
        self,
        region: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List reports, optionally filtered by region and/or source.

        Args:
            region: Region to filter by (exact match, case-insensitive).
            source: Source to filter by (exact match, case-insensitive).
            limit:  Maximum number of reports to return (most recent first).

        Returns:
            List of report dicts (possibly empty).
        """
        region_norm = (region or "").strip().lower()
        source_norm = (source or "").strip().lower()

        all_rows = list(self._safe_iter_rows())

        # Sort newest first by created_at
        all_rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)

        results: List[Dict[str, Any]] = []
        for row in all_rows:
            if region:
                row_region = str(row.get("region", "")).strip().lower()
                if row_region != region_norm:
                    continue

            if source:
                row_source = str(row.get("source", "")).strip().lower()
                if row_source != source_norm:
                    continue

            results.append(row)
            if len(results) >= limit:
                break

        return results

    def list_reports_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        List all reports associated with a given analysis run_id.

        This is useful if local actors submit reports referencing a specific
        dashboard assessment.
        """
        out: List[Dict[str, Any]] = []
        for row in self._safe_iter_rows():
            if row.get("run_id") == run_id:
                out.append(row)
        return out


# ---------------------------------------------------------------------- #
# Dependency helper (singleton-style)                                   #
# ---------------------------------------------------------------------- #

_report_store_singleton: Optional[ReportStore] = None


def get_report_store() -> ReportStore:
    """
    FastAPI dependency to access a shared ReportStore instance.
    """
    global _report_store_singleton
    if _report_store_singleton is None:
        _report_store_singleton = ReportStore()
    return _report_store_singleton

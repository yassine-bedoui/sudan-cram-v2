# app/services/collaboration_store.py

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Iterable, List

from app.models.collaboration import (
    FeedbackRecord,
    LocalActorInputRecord,
)

# Base data dir can be configured by env var; default to ./data
DATA_DIR = Path(os.getenv("SUDANCRAM_DATA_DIR", "data"))

FEEDBACK_DIR = DATA_DIR / "feedback"
FEEDBACK_FILE = FEEDBACK_DIR / "feedback.jsonl"

LOCAL_INPUT_DIR = DATA_DIR / "local_input"
LOCAL_INPUT_FILE = LOCAL_INPUT_DIR / "local_input.jsonl"

_feedback_lock = Lock()
_local_input_lock = Lock()


def _ensure_feedback_dirs() -> None:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_local_input_dirs() -> None:
    LOCAL_INPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---- Feedback persistence ----

def append_feedback(record: FeedbackRecord) -> None:
    """
    Append a feedback record to the JSONL log.
    """
    _ensure_feedback_dirs()
    line = record.json(ensure_ascii=False)
    with _feedback_lock:
        with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _iter_feedback_raw() -> Iterable[FeedbackRecord]:
    """
    Iterate over all feedback records in the JSONL file.
    """
    _ensure_feedback_dirs()
    if not FEEDBACK_FILE.exists():
        return []

    with FEEDBACK_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = FeedbackRecord.parse_raw(line)
            except Exception:
                continue
            yield rec


def get_feedback_for_run(run_id: str) -> List[FeedbackRecord]:
    return [r for r in _iter_feedback_raw() if r.run_id == run_id]


def get_feedback_for_region(region: str, limit: int = 100) -> List[FeedbackRecord]:
    region_lower = region.lower()
    results: List[FeedbackRecord] = []
    for r in _iter_feedback_raw():
        if r.region.lower() == region_lower:
            results.append(r)
            if len(results) >= limit:
                break
    return results


# ---- Local actor input persistence ----

def append_local_input(record: LocalActorInputRecord) -> None:
    _ensure_local_input_dirs()
    line = record.json(ensure_ascii=False)
    with _local_input_lock:
        with LOCAL_INPUT_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def _iter_local_input_raw() -> Iterable[LocalActorInputRecord]:
    _ensure_local_input_dirs()
    if not LOCAL_INPUT_FILE.exists():
        return []

    with LOCAL_INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = LocalActorInputRecord.parse_raw(line)
            except Exception:
                continue
            yield rec


def get_local_input_for_region(region: str, limit: int = 100) -> List[LocalActorInputRecord]:
    region_lower = region.lower()
    results: List[LocalActorInputRecord] = []
    for r in _iter_local_input_raw():
        if r.region.lower() == region_lower:
            results.append(r)
            if len(results) >= limit:
                break
    return results

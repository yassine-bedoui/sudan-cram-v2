# app/explainability/logger.py

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple
import uuid

# Environment variable to override log directory
DEFAULT_LOG_DIR_ENV = "SUDANCRAM_AUDIT_LOG_DIR"


def get_log_dir() -> Path:
    """Return the directory where audit logs are stored, creating it if needed."""
    base = os.getenv(DEFAULT_LOG_DIR_ENV) or "data/audit_logs"
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_and_data_metadata() -> Dict[str, Any]:
    """
    Lightweight metadata about models and data sources used in the pipeline.
    This is stored with each audit log entry.
    """
    return {
        "llm_model": os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
        "llm_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "embedding_model": os.getenv(
            "EMBEDDING_MODEL_NAME", "Alibaba-NLP/gte-multilingual-base"
        ),
        "vector_store_collection": os.getenv(
            "VECTOR_STORE_COLLECTION", "sudan_events"
        ),
        "data_sources": [
            {
                "name": "GDELT",
                "description": "Global Database of Events, Language, and Tone",
            },
        ],
    }


def log_analysis_run(payload: Dict[str, Any]) -> Tuple[str, str]:
    """
    Append a single analysis run to a JSONL audit log.

    Returns:
      (run_id, log_path)
    """
    run_id = payload.get("run_id") or uuid.uuid4().hex
    now = datetime.utcnow().isoformat()

    payload_to_log = {
        "run_id": run_id,
        "logged_at": now,
        "payload": payload,
        "meta": get_model_and_data_metadata(),
    }

    log_dir = get_log_dir()
    log_file = log_dir / "analysis_runs.jsonl"

    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload_to_log, ensure_ascii=False) + "\n")
        log_path_str = str(log_file)
    except Exception:
        # If logging fails (permissions, disk, etc.), don't break the app.
        log_path_str = ""

    return run_id, log_path_str

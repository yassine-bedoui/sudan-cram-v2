# backend/app/models/analysis_run.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    Float,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON

try:
    from database import Base
except ModuleNotFoundError:
    from backend.database import Base  # type: ignore


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Input
    region = Column(String(100), index=True)
    has_raw_data = Column(Boolean, default=False)
    interventions = Column(Text, nullable=True)  # JSON-encoded list

    # Trend
    trend_classification = Column(String(50), nullable=True)
    trend_confidence_label = Column(String(50), nullable=True)
    forecast_armed_clash = Column(Integer, nullable=True)
    forecast_civilian_targeting = Column(Integer, nullable=True)

    # Scenario summary
    recommendation_summary = Column(String(50), nullable=True)
    max_success_probability = Column(Integer, nullable=True)
    max_risk_probability = Column(Integer, nullable=True)

    # Validation
    validation_status = Column(String(50), nullable=True)
    issue_count = Column(Integer, default=0)
    overall_confidence = Column(Float, nullable=True)

    # Full explainability JSON
    explainability = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

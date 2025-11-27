# backend/app/models/gdelt.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func

# Make this work both when running from /backend and via "python -m backend..."
try:
    from database import Base  # when working directory is backend/
except ModuleNotFoundError:    # when imported as backend.app.models.gdelt
    from backend.database import Base  # type: ignore


class GDELTEvent(Base):
    __tablename__ = "gdelt_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False)
    event_date = Column(DateTime, nullable=False, index=True)

    # ISO3 country code for multi-country support (e.g. "SDN", "SOM")
    country_iso3 = Column(
        String(3),
        index=True,
        nullable=False,
        default="SDN",
        server_default="SDN",
    )

    region = Column(String(100), index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    event_code = Column(String(10))
    quad_class = Column(Integer)

    actor1_name = Column(String(200))
    actor2_name = Column(String(200))

    goldstein_scale = Column(Float)
    avg_tone = Column(Float)

    created_at = Column(DateTime, server_default=func.now())

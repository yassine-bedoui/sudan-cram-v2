from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.database import Base

class GDELTEvent(Base):
    __tablename__ = "gdelt_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    event_date = Column(DateTime, nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    event_code = Column(String(10))
    quad_class = Column(Integer)

    actor1_name = Column(String(200))
    actor2_name = Column(String(200))

    goldstein_scale = Column(Float)
    avg_tone = Column(Float)
    num_mentions = Column(Integer)
    num_articles = Column(Integer)

    raw_data = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

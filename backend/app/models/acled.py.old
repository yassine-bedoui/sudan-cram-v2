from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.sql import func
from backend.database import Base

class ACLEDEvent(Base):
    __tablename__ = "acled_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    event_type = Column(String(100))
    
    region = Column(String(100), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    actor1 = Column(String(200))
    actor2 = Column(String(200))
    
    fatalities = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())

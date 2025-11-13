from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    conflict_risk_score = Column(Float)
    gdelt_event_count = Column(Integer)
    
    flood_risk_score = Column(Float)
    drought_risk_score = Column(Float)
    climate_risk_score = Column(Float)
    
    overall_risk_score = Column(Float)
    risk_level = Column(String(20))
    
    last_updated = Column(DateTime, server_default=func.now())

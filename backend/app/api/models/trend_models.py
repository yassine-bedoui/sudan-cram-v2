from pydantic import BaseModel, Field
from typing import Optional, Tuple


class EscalationRiskSummary(BaseModel):
    region: str
    risk_score: float
    risk_level: str
    explanation: str
    forecasted_trend: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None


class ForecastResponse(BaseModel):
    region: str = Field(..., description="Region name for the forecast")
    forecast_periods: int = Field(..., description="Number of forecast periods")
    forecasted_trend: float = Field(..., description="Predicted trend value at the end of forecast period")
    confidence_interval: Tuple[float, float] = Field(..., description="Lower and upper confidence interval bounds")

    class Config:
        json_schema_extra = {
            "example": {
                "region": "Khartoum, Al Khartum, Sudan",
                "forecast_periods": 30,
                "forecasted_trend": 5.2,
                "confidence_interval": [3.1, 7.3]
            }
        }

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from app.agents.trend_forecasting_agent import TrendForecastingAgent
from app.api.models.trend_models import EscalationRiskSummary, ForecastResponse

router = APIRouter(
    prefix="/trend",
    tags=["Trend Analysis"]
)


@router.get(
    "/risk",
    response_model=List[EscalationRiskSummary],
    summary="Get escalation risk summaries by region",
    description="Calculate and retrieve escalation risk scores and levels for conflict regions. Optionally filter by region name."
)
def get_trend_risk(
    region: Optional[str] = Query(None, description="Filter risk by region name"),
    include_forecast: bool = Query(False, description="Include forecast data in response"),
    forecast_periods: int = Query(30, description="Number of periods to forecast (if include_forecast=True)"),
    db: Session = Depends(get_db)
):
    """
    Endpoint to retrieve escalation risk summaries for conflict events.
    Optionally includes forecast data with confidence intervals.

    Args:
        region (str, optional): Region name to filter risk calculation.
        include_forecast (bool): Whether to include forecast predictions.
        forecast_periods (int): Number of forecast periods (default 30 days).
        db (Session): Database session injected by FastAPI dependency.

    Returns:
        List[EscalationRiskSummary]: List of risk summaries per region with optional forecasts.
    """
    agent = TrendForecastingAgent(db_session=db)

    try:
        if include_forecast:
            # Use the forecast-enhanced output
            risks = agent.output_with_forecast(region=region, forecast_periods=forecast_periods)
        else:
            # Standard risk calculation without forecasts
            agent.ingest(region=region)
            risks = agent.calculate_escalation_risk()
        
        return risks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating escalation risk: {str(e)}"
        )


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get time-series forecast for a specific region",
    description="Generate Prophet-based forecasts with confidence intervals for event trends in a specific region."
)
def get_forecast(
    region: str = Query(..., description="Region name for forecasting (required)"),
    periods: int = Query(30, ge=1, le=365, description="Number of forecast periods (1-365 days)"),
    db: Session = Depends(get_db)
):
    """
    Endpoint to generate and retrieve time-series forecasts for a specific region.

    Args:
        region (str): Region name (required).
        periods (int): Number of periods to forecast (1-365, default 30).
        db (Session): Database session injected by FastAPI dependency.

    Returns:
        ForecastResponse: Forecast data with predictions and confidence intervals.
    """
    agent = TrendForecastingAgent(db_session=db)

    try:
        forecast_data = agent.predict_trends(region=region, periods=periods)
        
        if not forecast_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to generate forecast for region: {region}"
            )

        return ForecastResponse(
            region=region,
            forecast_periods=periods,
            forecasted_trend=forecast_data['forecasted_trend'],
            confidence_interval=forecast_data['confidence_interval']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating forecast: {str(e)}"
        )

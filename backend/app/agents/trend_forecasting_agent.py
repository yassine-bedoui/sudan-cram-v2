from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.api.models.trend_models import EscalationRiskSummary
from app.core import trend_analysis
from app.core.prophet_preparation import prepare_time_series_for_prophet
from app.core.forecasting import ProphetForecaster


class TrendForecastingAgent:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.historical_df = None
        self.forecasters = {}

    def ingest(self, region: Optional[str] = None):
        self.historical_df = trend_analysis.load_events_from_db(self.db, region=region)

    def calculate_escalation_risk(self) -> List[EscalationRiskSummary]:
        if self.historical_df is None or self.historical_df.empty:
            raise RuntimeError("No historical data ingested.")

        risk_df = trend_analysis.calculate_escalation_risk(self.historical_df)

        risk_summaries = []
        for _, row in risk_df.iterrows():
            summary = EscalationRiskSummary(
                region=row['location'],
                risk_score=row['escalation_risk'],
                risk_level=row['risk_level'],
                explanation=(
                    f"Risk score based on avg Goldstein {row['avg_goldstein']:.2f}, "
                    f"Goldstein trend {row['goldstein_trend']:.2f}, "
                    f"event count {row['event_count']} and media mentions {row['media_mentions']}."
                ),
                forecasted_trend=None,
                confidence_interval=None
            )
            risk_summaries.append(summary)
        return risk_summaries

    def train_forecast_model(self, region: str):
        logging.info(f"Training forecast model for region: {region}")

        ts_df = prepare_time_series_for_prophet(self.db, region=region, time_freq='D')
        if ts_df.empty:
            raise RuntimeError(f"No time series data for Prophet training in region {region}")

        prophet_model = ProphetForecaster()
        prophet_model.train(ts_df)

        self.forecasters[region] = prophet_model
        logging.info(f"Model trained for region: {region}")

    def predict_trends(self, region: str, periods: int = 30) -> Optional[dict]:
        if region not in self.forecasters:
            logging.info(f"No Prophet model for {region}, training now.")
            self.train_forecast_model(region)

        prophet_model = self.forecasters.get(region)
        if not prophet_model:
            logging.warning(f"Prophet model not found for {region}")
            return None

        forecast_df = prophet_model.predict(periods=periods)
        last_forecast = forecast_df.iloc[-1]

        forecasted_trend = last_forecast['yhat']
        confidence_interval = (last_forecast['yhat_lower'], last_forecast['yhat_upper'])

        return {
            'forecasted_trend': forecasted_trend,
            'confidence_interval': confidence_interval
        }

    def output_with_forecast(self, region: Optional[str] = None, forecast_periods: int = 30) -> List[EscalationRiskSummary]:
        self.ingest(region=region)
        risk_summaries = self.calculate_escalation_risk()

        if region:
            region_lower = region.lower()
            risk_summaries = [rs for rs in risk_summaries if region_lower in rs.region.lower()]

        for summary in risk_summaries:
            region_name = summary.region
            try:
                forecast_data = self.predict_trends(region_name, periods=forecast_periods)
                if forecast_data:
                    summary.forecasted_trend = forecast_data['forecasted_trend']
                    summary.confidence_interval = forecast_data['confidence_interval']
            except Exception as e:
                print(f"Forecast error for {region_name}: {e}")
                summary.forecasted_trend = None
                summary.confidence_interval = None

        return risk_summaries


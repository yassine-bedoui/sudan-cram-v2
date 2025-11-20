import logging
from typing import Optional, Tuple
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics


class ProphetForecaster:
    def __init__(self):
        self.model: Optional[Prophet] = None
        self.is_trained: bool = False

    def train(self, ts_df: pd.DataFrame, yearly_seasonality: bool = True, weekly_seasonality: bool = True, daily_seasonality: bool = False,
              changepoint_prior_scale: float = 0.05, holidays: Optional[pd.DataFrame] = None) -> None:
        if ts_df.empty:
            raise ValueError("Training dataframe is empty.")
        
        logging.info(f"Training Prophet model on {len(ts_df)} records.")

        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale,
            holidays=holidays
        )
        self.model.fit(ts_df)
        self.is_trained = True
        logging.info("Prophet model trained successfully.")

    def predict(self, periods: int = 30, freq: str = 'D') -> pd.DataFrame:
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model has not been trained yet.")

        logging.info(f"Generating forecast for next {periods} periods with frequency '{freq}'.")

        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)

        results = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        return results

    def cross_validate(self, initial: str = '365 days', period: str = '30 days', horizon: str = '90 days') -> Tuple[pd.DataFrame, pd.DataFrame]:
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model has not been trained yet.")

        logging.info(f"Performing cross-validation with initial={initial}, period={period}, horizon={horizon}.")
        
        cv_results = cross_validation(self.model, initial=initial, period=period, horizon=horizon)
        perf_metrics = performance_metrics(cv_results)

        return cv_results, perf_metrics

"""
ARIMA Model for Currency Forecasting

Auto-ARIMA implementation for short-term momentum-based predictions.
Uses pmdarima for automatic order selection.
"""

import logging
from typing import Optional, List
from datetime import date, timedelta
import pandas as pd
import numpy as np

from .base import BaseForecaster, ForecastResult

logger = logging.getLogger(__name__)

# Try to import pmdarima (optional dependency)
try:
    from pmdarima import auto_arima
    ARIMA_AVAILABLE = True
    logger.info("pmdarima loaded - ARIMA forecasting available")
except ImportError:
    ARIMA_AVAILABLE = False
    logger.warning("pmdarima not installed. Run: pip install pmdarima")


class ARIMAForecaster(BaseForecaster):
    """
    ARIMA-based forecaster for short-term currency predictions.
    
    Best for:
    - Short-term forecasts (7-30 days)
    - Capturing momentum and recent trends
    - Stationary or differenced time series
    """
    
    def __init__(
        self,
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5,
        seasonal: bool = False,
        stepwise: bool = True
    ):
        """
        Initialize ARIMA forecaster.
        
        Args:
            max_p: Maximum AR order
            max_d: Maximum differencing order
            max_q: Maximum MA order
            seasonal: Whether to fit seasonal ARIMA
            stepwise: Use stepwise algorithm for faster fitting
        """
        super().__init__(name="arima")
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.seasonal = seasonal
        self.stepwise = stepwise
        
        self._model = None
        self._currency = None
        self._last_date = None
        self._last_value = None
    
    def fit(self, df: pd.DataFrame, currency: str) -> "ARIMAForecaster":
        """
        Fit ARIMA model to historical data.
        
        Args:
            df: DataFrame with 'record_date' and 'exchange_rate' columns
            currency: Currency code
            
        Returns:
            Self for method chaining
        """
        if not ARIMA_AVAILABLE:
            logger.error("Cannot fit ARIMA - pmdarima not installed")
            return self
        
        self._currency = currency
        
        # Prepare data
        df = df.copy()
        df = df.sort_values("record_date")
        df = df.dropna(subset=["exchange_rate"])
        
        if len(df) < 30:
            logger.warning(f"Insufficient data for ARIMA ({len(df)} points). Need at least 30.")
            return self
        
        # Store reference points
        self._last_date = df["record_date"].iloc[-1]
        self._last_value = df["exchange_rate"].iloc[-1]
        self._training_data = df
        
        # Fit auto-ARIMA
        try:
            y = df["exchange_rate"].values
            
            self._model = auto_arima(
                y,
                max_p=self.max_p,
                max_d=self.max_d,
                max_q=self.max_q,
                seasonal=self.seasonal,
                stepwise=self.stepwise,
                suppress_warnings=True,
                error_action="ignore",
                trace=False
            )
            
            self.is_fitted = True
            logger.info(f"ARIMA fitted for {currency}: order={self._model.order}")
            
            # Calculate in-sample metrics
            fitted_values = self._model.predict_in_sample()
            self.evaluate(
                pd.Series(y[-len(fitted_values):]),
                pd.Series(fitted_values)
            )
            
        except Exception as e:
            logger.error(f"ARIMA fitting failed: {e}")
            self.is_fitted = False
        
        return self
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> ForecastResult:
        """
        Generate ARIMA forecasts.
        
        Args:
            horizon: Number of days to forecast
            confidence: Confidence interval level
            
        Returns:
            ForecastResult with predictions
        """
        if not self.is_fitted or self._model is None:
            logger.warning("ARIMA not fitted. Returning empty forecast.")
            return ForecastResult(
                model_name=self.name,
                currency=self._currency or "UNKNOWN",
                forecast_dates=[],
                point_forecasts=[],
                lower_bounds=[],
                upper_bounds=[],
                confidence_level=confidence
            )
        
        try:
            # Generate forecast with confidence intervals
            alpha = 1 - confidence
            forecast, conf_int = self._model.predict(
                n_periods=horizon,
                return_conf_int=True,
                alpha=alpha
            )
            
            # Generate forecast dates
            if isinstance(self._last_date, pd.Timestamp):
                last_date = self._last_date.date()
            else:
                last_date = self._last_date
            
            forecast_dates = [
                last_date + timedelta(days=i+1)
                for i in range(horizon)
            ]
            
            return ForecastResult(
                model_name=self.name,
                currency=self._currency,
                forecast_dates=forecast_dates,
                point_forecasts=forecast.tolist(),
                lower_bounds=conf_int[:, 0].tolist(),
                upper_bounds=conf_int[:, 1].tolist(),
                confidence_level=confidence,
                training_mape=self._mape,
                directional_accuracy=self._directional_accuracy
            )
            
        except Exception as e:
            logger.error(f"ARIMA prediction failed: {e}")
            return ForecastResult(
                model_name=self.name,
                currency=self._currency,
                forecast_dates=[],
                point_forecasts=[],
                lower_bounds=[],
                upper_bounds=[],
                confidence_level=confidence
            )
    
    @property
    def order(self) -> Optional[tuple]:
        """Get fitted ARIMA order (p, d, q)."""
        if self._model is not None:
            return self._model.order
        return None


def is_available() -> bool:
    """Check if ARIMA is available."""
    return ARIMA_AVAILABLE

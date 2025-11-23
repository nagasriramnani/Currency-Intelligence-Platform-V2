"""
ML forecasting layer using Prophet for currency rate prediction.
Provides forecast with confidence intervals.
"""

import logging
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Prophet with proper error handling
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    logger.info("Prophet successfully loaded - ML forecasting enabled")
except ImportError as e:
    logger.warning(f"Prophet not available: {e}. Using simple forecasting fallback.")
    PROPHET_AVAILABLE = False
    Prophet = None
except Exception as e:
    logger.warning(f"Prophet import error: {e}. Using simple forecasting fallback.")
    PROPHET_AVAILABLE = False
    Prophet = None


class CurrencyForecaster:
    """Forecasts currency exchange rates using Prophet or fallback methods."""
    
    def __init__(self, use_prophet: bool = True):
        """
        Initialize forecaster.
        
        Args:
            use_prophet: Whether to use Prophet (if available) or simple method
        """
        self.use_prophet = use_prophet and PROPHET_AVAILABLE
        self.models = {}  # Store trained models per currency
        self.growth_bounds: Dict[str, Dict[str, float]] = {}
        
    def prepare_data_for_prophet(
        self,
        df: pd.DataFrame,
        date_col: str = "record_date",
        value_col: str = "exchange_rate"
    ) -> pd.DataFrame:
        """
        Prepare data in Prophet's required format (ds, y).
        
        Args:
            df: Input DataFrame
            date_col: Name of date column
            value_col: Name of value column
            
        Returns:
            DataFrame with columns 'ds' and 'y'
        """
        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime(df[date_col]),
            "y": df[value_col]
        })
        
        # Remove duplicates and sort
        prophet_df = prophet_df.drop_duplicates(subset=["ds"]).sort_values("ds")
        
        return prophet_df
    
    def _compute_growth_bounds(self, values: pd.Series) -> Dict[str, float]:
        """Derive reasonable logistic growth bounds to keep forecasts realistic."""
        finite_values = values.replace([np.inf, -np.inf], np.nan).dropna()
        if finite_values.empty:
            return {"cap": 2.0, "floor": 0.0}
        
        min_rate = float(finite_values.min())
        max_rate = float(finite_values.max())
        spread = max(0.01, max_rate - min_rate)
        buffer = max(0.05, spread * 0.35)
        
        floor = max(0.0001, min_rate - buffer)
        cap = max_rate + buffer
        
        if floor >= cap:
            cap = floor + max(0.05, cap * 0.05)
        
        return {"cap": cap, "floor": floor}
    
    def train_prophet_model(
        self,
        df: pd.DataFrame,
        currency: str
    ) -> Optional[Prophet]:
        """
        Train a Prophet model for a specific currency.
        
        Args:
            df: DataFrame with historical data
            currency: Currency code
            
        Returns:
            Trained Prophet model or None if training fails
        """
        if not self.use_prophet:
            return None
        
        try:
            # Prepare data
            prophet_df = self.prepare_data_for_prophet(df)
            
            if len(prophet_df) < 10:
                logger.warning(f"Insufficient data for {currency}: {len(prophet_df)} points")
                return None
            
            bounds = self._compute_growth_bounds(prophet_df["y"])
            prophet_df["cap"] = bounds["cap"]
            prophet_df["floor"] = bounds["floor"]
            
            # Initialize and train model
            model = Prophet(
                growth="logistic",
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,  # More conservative
                interval_width=0.80  # 80% confidence interval
            )
            
            # Suppress Prophet's verbose output
            import logging as prophet_logging
            prophet_logging.getLogger('prophet').setLevel(prophet_logging.WARNING)
            
            model.fit(prophet_df)
            
            # Store model
            self.models[currency] = model
            self.growth_bounds[currency] = bounds
            
            logger.info(f"Trained Prophet model for {currency} with {len(prophet_df)} data points")
            
            return model
            
        except Exception as e:
            logger.error(f"Error training Prophet model for {currency}: {e}")
            return None
    
    def forecast_with_prophet(
        self,
        currency: str,
        horizon: int = 3,
        freq: str = "MS"
    ) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        Generate forecast using trained Prophet model.
        
        Args:
            currency: Currency code
            horizon: Number of periods to forecast
            freq: Frequency string (MS = month start)
            
        Returns:
            Tuple of (forecast DataFrame, confidence bands dict)
        """
        model = self.models.get(currency)
        
        if model is None:
            logger.warning(f"No model available for {currency}")
            return None, None
        
        try:
            # Create future dataframe (includes history)
            future = model.make_future_dataframe(periods=horizon, freq=freq, include_history=True)
            bounds = self.growth_bounds.get(currency)
            if bounds:
                future["cap"] = bounds["cap"]
                future["floor"] = bounds["floor"]
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Use only future horizon for output
            future_forecast = forecast.tail(horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            future_forecast.columns = ["date", "forecast", "lower_bound", "upper_bound"]
            
            # Create confidence band dict
            confidence = {
                "mean": future_forecast["forecast"].tolist(),
                "lower": future_forecast["lower_bound"].tolist(),
                "upper": future_forecast["upper_bound"].tolist(),
                "dates": future_forecast["date"].dt.strftime("%Y-%m-%d").tolist()
            }
            
            logger.info(f"Generated {horizon}-period forecast for {currency}")
            
            return future_forecast, confidence
            
        except Exception as e:
            logger.error(f"Error generating forecast for {currency}: {e}")
            return None, None
    
    def simple_forecast(
        self,
        df: pd.DataFrame,
        horizon: int = 3
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Simple moving average forecast (fallback when Prophet unavailable).
        
        Args:
            df: Historical data
            horizon: Number of periods to forecast
            
        Returns:
            Tuple of (forecast DataFrame, confidence bands)
        """
        df = df.sort_values("record_date")
        
        # Calculate moving average and std
        window = min(12, len(df))
        recent_mean = df["exchange_rate"].tail(window).mean()
        recent_std = df["exchange_rate"].tail(window).std()
        
        # Generate future dates
        last_date = df["record_date"].max()
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=horizon,
            freq="MS"
        )
        
        # Create simple forecast (flat projection with uncertainty)
        forecast_df = pd.DataFrame({
            "date": future_dates,
            "forecast": recent_mean,
            "lower_bound": recent_mean - 1.5 * recent_std,
            "upper_bound": recent_mean + 1.5 * recent_std
        })
        
        confidence = {
            "mean": forecast_df["forecast"].tolist(),
            "lower": forecast_df["lower_bound"].tolist(),
            "upper": forecast_df["upper_bound"].tolist(),
            "dates": forecast_df["date"].dt.strftime("%Y-%m-%d").tolist()
        }
        
        return forecast_df, confidence
    
    def forecast_rates(
        self,
        df: pd.DataFrame,
        currency: str,
        horizon: int = 3
    ) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        Main forecasting method - tries Prophet first, falls back to simple method.
        
        Args:
            df: Historical data for the currency
            currency: Currency code
            horizon: Number of periods to forecast
            
        Returns:
            Tuple of (forecast DataFrame, confidence bands dict)
        """
        # Filter to specific currency
        currency_df = df[df["currency"] == currency].copy()
        
        if currency_df.empty:
            logger.warning(f"No data for currency: {currency}")
            return None, None
        
        # Try Prophet first
        if self.use_prophet:
            # Train model if not already trained
            if currency not in self.models:
                self.train_prophet_model(currency_df, currency)
            
            # Generate forecast
            forecast_df, confidence = self.forecast_with_prophet(currency, horizon)
            
            if forecast_df is not None:
                return forecast_df, confidence
        
        # Fallback to simple method
        logger.info(f"Using simple forecast for {currency}")
        return self.simple_forecast(currency_df, horizon)
    
    def forecast_all_currencies(
        self,
        df: pd.DataFrame,
        horizon: int = 3
    ) -> Dict[str, Tuple[pd.DataFrame, Dict]]:
        """
        Generate forecasts for all currencies in the dataset.
        
        Args:
            df: DataFrame with all currencies
            horizon: Number of periods to forecast
            
        Returns:
            Dictionary mapping currency code to (forecast_df, confidence)
        """
        currencies = df["currency"].unique()
        forecasts = {}
        
        for currency in currencies:
            forecast_df, confidence = self.forecast_rates(df, currency, horizon)
            
            if forecast_df is not None:
                forecasts[currency] = (forecast_df, confidence)
        
        logger.info(f"Generated forecasts for {len(forecasts)} currencies")
        
        return forecasts
    
    def calculate_forecast_accuracy(
        self,
        actual: pd.Series,
        predicted: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics.
        
        Args:
            actual: Actual values
            predicted: Predicted values
            
        Returns:
            Dictionary with accuracy metrics (MAE, RMSE, MAPE)
        """
        # Align series
        aligned = pd.DataFrame({"actual": actual, "predicted": predicted}).dropna()
        
        if aligned.empty:
            return {"mae": None, "rmse": None, "mape": None}
        
        # Mean Absolute Error
        mae = np.mean(np.abs(aligned["actual"] - aligned["predicted"]))
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((aligned["actual"] - aligned["predicted"]) ** 2))
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((aligned["actual"] - aligned["predicted"]) / aligned["actual"])) * 100
        
        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape)
        }


if __name__ == "__main__":
    # Test with synthetic data
    dates = pd.date_range("2020-01-01", "2024-01-01", freq="MS")
    test_df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": 0.85 + 0.1 * np.sin(np.arange(len(dates)) * 0.3) + np.random.normal(0, 0.02, len(dates)),
        "currency": "EUR"
    })
    
    forecaster = CurrencyForecaster()
    forecast_df, confidence = forecaster.forecast_rates(test_df, "EUR", horizon=6)
    
    if forecast_df is not None:
        print("Forecast:")
        print(forecast_df.head())
        print("\nConfidence bands:")
        print(confidence)


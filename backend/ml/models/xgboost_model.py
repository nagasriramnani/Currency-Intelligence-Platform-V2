"""
XGBoost Model for Currency Forecasting

Gradient boosting model that can incorporate multiple features
for more complex pattern recognition.
"""

import logging
from typing import Optional, List, Dict
from datetime import date, timedelta
import pandas as pd
import numpy as np

from .base import BaseForecaster, ForecastResult

logger = logging.getLogger(__name__)

# Try to import xgboost (optional dependency)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
    logger.info("XGBoost loaded - ML regression available")
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not installed. Run: pip install xgboost")


class XGBoostForecaster(BaseForecaster):
    """
    XGBoost-based forecaster for currency predictions.
    
    Best for:
    - Capturing complex non-linear relationships
    - Incorporating multiple features (technical indicators, lags)
    - Longer-term trend prediction
    """
    
    def __init__(
        self,
        n_lags: int = 14,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.1,
        objective: str = "reg:squarederror"
    ):
        """
        Initialize XGBoost forecaster.
        
        Args:
            n_lags: Number of lagged features to create
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Boosting learning rate
            objective: XGBoost objective function
        """
        super().__init__(name="xgboost")
        self.n_lags = n_lags
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.objective = objective
        
        self._model = None
        self._currency = None
        self._last_values = None
        self._last_date = None
        self._feature_names = None
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create lagged features and technical indicators.
        
        Args:
            df: DataFrame with 'exchange_rate' column
            
        Returns:
            DataFrame with features
        """
        features = pd.DataFrame(index=df.index)
        
        # Lagged values
        for i in range(1, self.n_lags + 1):
            features[f"lag_{i}"] = df["exchange_rate"].shift(i)
        
        # Rolling statistics
        features["rolling_mean_7"] = df["exchange_rate"].rolling(7).mean()
        features["rolling_std_7"] = df["exchange_rate"].rolling(7).std()
        features["rolling_mean_30"] = df["exchange_rate"].rolling(30).mean()
        features["rolling_std_30"] = df["exchange_rate"].rolling(30).std()
        
        # Momentum indicators
        features["momentum_7"] = df["exchange_rate"] - df["exchange_rate"].shift(7)
        features["momentum_30"] = df["exchange_rate"] - df["exchange_rate"].shift(30)
        
        # Rate of change
        features["roc_7"] = df["exchange_rate"].pct_change(7) * 100
        features["roc_30"] = df["exchange_rate"].pct_change(30) * 100
        
        # Day of week / month (cyclical encoding)
        if "record_date" in df.columns:
            dates = pd.to_datetime(df["record_date"])
            features["day_of_week_sin"] = np.sin(2 * np.pi * dates.dt.dayofweek / 7)
            features["day_of_week_cos"] = np.cos(2 * np.pi * dates.dt.dayofweek / 7)
            features["month_sin"] = np.sin(2 * np.pi * dates.dt.month / 12)
            features["month_cos"] = np.cos(2 * np.pi * dates.dt.month / 12)
        
        return features
    
    def fit(self, df: pd.DataFrame, currency: str) -> "XGBoostForecaster":
        """
        Fit XGBoost model to historical data.
        
        Args:
            df: DataFrame with 'record_date' and 'exchange_rate' columns
            currency: Currency code
            
        Returns:
            Self for method chaining
        """
        if not XGBOOST_AVAILABLE:
            logger.error("Cannot fit XGBoost - package not installed")
            return self
        
        self._currency = currency
        
        # Prepare data
        df = df.copy()
        df = df.sort_values("record_date")
        df = df.dropna(subset=["exchange_rate"])
        
        if len(df) < self.n_lags + 30:
            logger.warning(f"Insufficient data for XGBoost ({len(df)} points)")
            return self
        
        # Store reference points
        self._last_date = df["record_date"].iloc[-1]
        self._last_values = df["exchange_rate"].tail(self.n_lags + 30).values
        self._training_data = df
        
        # Create features
        features = self._create_features(df)
        self._feature_names = features.columns.tolist()
        
        # Target is next day's rate
        target = df["exchange_rate"].shift(-1)
        
        # Remove rows with NaN
        valid_mask = ~(features.isna().any(axis=1) | target.isna())
        X = features[valid_mask]
        y = target[valid_mask]
        
        if len(X) < 100:
            logger.warning(f"Insufficient valid samples for XGBoost ({len(X)})")
            return self
        
        try:
            # Train XGBoost
            self._model = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                objective=self.objective,
                random_state=42,
                verbosity=0
            )
            
            self._model.fit(X, y)
            self.is_fitted = True
            logger.info(f"XGBoost fitted for {currency} with {len(X)} samples")
            
            # Calculate in-sample metrics
            predictions = self._model.predict(X)
            self.evaluate(y, pd.Series(predictions, index=y.index))
            
        except Exception as e:
            logger.error(f"XGBoost fitting failed: {e}")
            self.is_fitted = False
        
        return self
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> ForecastResult:
        """
        Generate XGBoost forecasts.
        
        Note: XGBoost doesn't provide native confidence intervals.
        We estimate them using historical prediction error.
        
        Args:
            horizon: Number of days to forecast
            confidence: Confidence interval level
            
        Returns:
            ForecastResult with predictions
        """
        if not self.is_fitted or self._model is None:
            logger.warning("XGBoost not fitted. Returning empty forecast.")
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
            # Use training data to bootstrap predict
            df = self._training_data.copy()
            
            # Get the error std from training for CI estimation
            if self._mape is not None:
                error_std = self._last_values[-1] * (self._mape / 100) * 0.5
            else:
                error_std = self._last_values[-1] * 0.02  # Default 2%
            
            # z-score for confidence
            from scipy import stats
            z = stats.norm.ppf((1 + confidence) / 2)
            
            # Generate forecast dates
            if isinstance(self._last_date, pd.Timestamp):
                last_date = self._last_date.date()
            else:
                last_date = self._last_date
            
            forecast_dates = []
            point_forecasts = []
            lower_bounds = []
            upper_bounds = []
            
            # Recursive forecasting
            current_df = df.copy()
            
            for i in range(horizon):
                # Create features for next prediction
                features = self._create_features(current_df)
                last_features = features.iloc[-1:][self._feature_names]
                
                if last_features.isna().any().any():
                    break
                
                # Predict
                pred = self._model.predict(last_features)[0]
                
                # Store results
                forecast_date = last_date + timedelta(days=i+1)
                forecast_dates.append(forecast_date)
                point_forecasts.append(float(pred))
                lower_bounds.append(float(pred - z * error_std))
                upper_bounds.append(float(pred + z * error_std))
                
                # Add prediction to dataframe for recursive forecasting
                new_row = pd.DataFrame({
                    "record_date": [forecast_date],
                    "exchange_rate": [pred]
                })
                current_df = pd.concat([current_df, new_row], ignore_index=True)
            
            return ForecastResult(
                model_name=self.name,
                currency=self._currency,
                forecast_dates=forecast_dates,
                point_forecasts=point_forecasts,
                lower_bounds=lower_bounds,
                upper_bounds=upper_bounds,
                confidence_level=confidence,
                training_mape=self._mape,
                directional_accuracy=self._directional_accuracy
            )
            
        except Exception as e:
            logger.error(f"XGBoost prediction failed: {e}")
            import traceback
            traceback.print_exc()
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
    def feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance scores."""
        if self._model is not None and self._feature_names is not None:
            importance = self._model.feature_importances_
            return dict(zip(self._feature_names, importance.tolist()))
        return None


def is_available() -> bool:
    """Check if XGBoost is available."""
    return XGBOOST_AVAILABLE

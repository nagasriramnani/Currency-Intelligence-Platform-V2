"""
XGBoost Trainer

XGBoost-based time series forecasting trainer with feature engineering.
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .base import BaseTrainer, TrainingMetrics

logger = logging.getLogger(__name__)

# Try to import XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed. Run: pip install xgboost")


class XGBoostTrainer(BaseTrainer):
    """
    XGBoost-based forecasting trainer with feature engineering.
    
    XGBoost is excellent for:
    - Non-linear relationships
    - Feature-rich prediction
    - Capturing macro correlations
    """
    
    MODEL_NAME = "xgboost"
    
    def __init__(
        self,
        model_dir: str = "trained_models",
        n_lags: int = 14,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.1
    ):
        super().__init__(model_dir)
        
        self.n_lags = n_lags
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        
        self._feature_cols: List[str] = []
        self._last_values: Optional[pd.DataFrame] = None
        self._prediction_std: float = 0.01
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for XGBoost."""
        df = df.copy()
        
        # Lag features
        for lag in [1, 2, 3, 7, 14]:
            if lag <= self.n_lags:
                df[f"lag_{lag}"] = df["exchange_rate"].shift(lag)
        
        # Rolling statistics
        df["rolling_mean_7"] = df["exchange_rate"].rolling(7).mean()
        df["rolling_mean_30"] = df["exchange_rate"].rolling(30).mean()
        df["rolling_std_7"] = df["exchange_rate"].rolling(7).std()
        df["rolling_std_30"] = df["exchange_rate"].rolling(30).std()
        
        # Momentum features
        df["momentum_7"] = df["exchange_rate"] - df["exchange_rate"].shift(7)
        df["momentum_30"] = df["exchange_rate"] - df["exchange_rate"].shift(30)
        
        # Rate of change
        df["roc_7"] = df["exchange_rate"].pct_change(periods=7)
        df["roc_30"] = df["exchange_rate"].pct_change(periods=30)
        
        # Time features
        df["day_of_week"] = pd.to_datetime(df["record_date"]).dt.dayofweek
        df["month"] = pd.to_datetime(df["record_date"]).dt.month
        
        # Cyclical encoding
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        
        return df
    
    def train(
        self,
        df: pd.DataFrame,
        currency: str,
        train_ratio: float = 0.8
    ) -> TrainingMetrics:
        """Train XGBoost model."""
        if not XGBOOST_AVAILABLE:
            raise RuntimeError("XGBoost not installed")
        
        start_time = time.time()
        
        # Prepare data
        df = df.copy()
        df = df.sort_values("record_date")
        df = df.dropna(subset=["exchange_rate"])
        
        self._data_start = pd.to_datetime(df["record_date"].min()).date()
        self._data_end = pd.to_datetime(df["record_date"].max()).date()
        self._currency = currency
        
        # Create features
        df = self._create_features(df)
        df = df.dropna()
        
        # Define feature columns - ONLY numeric columns, exclude all non-numeric
        exclude_cols = ["record_date", "exchange_rate", "currency", "day_of_week", "month"]
        
        # Get only numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        self._feature_cols = [
            col for col in numeric_cols 
            if col not in exclude_cols and col != "exchange_rate"
        ]
        
        logger.info(f"Using {len(self._feature_cols)} features: {self._feature_cols[:5]}...")
        
        # Train/test split
        split_idx = int(len(df) * train_ratio)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        logger.info(f"Training XGBoost for {currency}: {len(train_df)} train, {len(test_df)} test samples")
        
        X_train = train_df[self._feature_cols]
        y_train = train_df["exchange_rate"]
        X_test = test_df[self._feature_cols]
        y_test = test_df["exchange_rate"]
        
        # Train XGBoost
        self._model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            objective="reg:squarederror",
            random_state=42
        )
        self._model.fit(X_train, y_train)
        self._is_trained = True
        
        # Store last values for prediction
        self._last_values = df.tail(60).copy()
        
        # Evaluate on test set
        if len(test_df) > 0:
            predictions = self._model.predict(X_test)
            metrics = self.evaluate(y_test.values, predictions)
            
            # Calculate prediction std for confidence intervals
            errors = y_test.values - predictions
            self._prediction_std = np.std(errors)
        else:
            metrics = {"rmse": 0, "mape": 0, "mae": 0, "directional_accuracy": 0}
        
        training_time = time.time() - start_time
        
        self._metrics = TrainingMetrics(
            model_name=self.MODEL_NAME,
            currency=currency,
            rmse=metrics["rmse"],
            mape=metrics["mape"],
            mae=metrics["mae"],
            directional_accuracy=metrics["directional_accuracy"],
            train_samples=len(train_df),
            test_samples=len(test_df),
            training_time_seconds=training_time,
            data_start=self._data_start,
            data_end=self._data_end
        )
        
        logger.info(f"XGBoost training complete: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.6f}")
        
        return self._metrics
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> Dict:
        """Generate XGBoost forecast."""
        if not self._is_trained:
            raise RuntimeError("Model must be trained before prediction")
        
        from scipy.stats import norm
        from datetime import timedelta
        
        # Get last known values for building features
        current_data = self._last_values.copy()
        current_data = current_data.sort_values("record_date")
        
        # Get the last exchange rate to start predictions
        last_rate = current_data["exchange_rate"].iloc[-1]
        last_date = pd.to_datetime(current_data["record_date"].iloc[-1])
        
        # Generate forecasts
        forecasts = []
        rates_history = current_data["exchange_rate"].tolist()
        
        for i in range(horizon):
            # Calculate forecast date (monthly for FX data)
            forecast_date = last_date + timedelta(days=30 * (i + 1))
            
            # Build features from accumulated history
            # Lag features
            features = {}
            for lag in [1, 2, 3, 7, 14]:
                if lag <= self.n_lags and len(rates_history) > lag:
                    features[f"lag_{lag}"] = rates_history[-lag]
            
            # Rolling statistics (use available data)
            recent = rates_history[-min(30, len(rates_history)):]
            features["rolling_mean_7"] = np.mean(recent[-7:]) if len(recent) >= 7 else np.mean(recent)
            features["rolling_mean_30"] = np.mean(recent) if len(recent) >= 7 else np.mean(recent)
            features["rolling_std_7"] = np.std(recent[-7:]) if len(recent) >= 7 else 0.01
            features["rolling_std_30"] = np.std(recent) if len(recent) >= 7 else 0.01
            
            # Momentum features
            if len(rates_history) > 7:
                features["momentum_7"] = rates_history[-1] - rates_history[-7]
            else:
                features["momentum_7"] = 0
            if len(rates_history) > 30:
                features["momentum_30"] = rates_history[-1] - rates_history[-30]
            else:
                features["momentum_30"] = 0
            
            # Rate of change
            if len(rates_history) > 7:
                features["roc_7"] = (rates_history[-1] - rates_history[-7]) / rates_history[-7] if rates_history[-7] != 0 else 0
            else:
                features["roc_7"] = 0
            if len(rates_history) > 30:
                features["roc_30"] = (rates_history[-1] - rates_history[-30]) / rates_history[-30] if rates_history[-30] != 0 else 0
            else:
                features["roc_30"] = 0
            
            # Time features (cyclical)
            day_of_week = forecast_date.dayofweek
            month = forecast_date.month
            features["day_of_week_sin"] = np.sin(2 * np.pi * day_of_week / 7)
            features["day_of_week_cos"] = np.cos(2 * np.pi * day_of_week / 7)
            features["month_sin"] = np.sin(2 * np.pi * month / 12)
            features["month_cos"] = np.cos(2 * np.pi * month / 12)
            
            # Add any other expected features with defaults
            for col in self._feature_cols:
                if col not in features:
                    features[col] = 0.0
            
            # Create feature dataframe matching training columns
            X = pd.DataFrame([features])[self._feature_cols]
            
            # Predict
            pred = self._model.predict(X)[0]
            
            # Sanity check: ensure prediction is reasonable (within 50% of last rate)
            if pred < last_rate * 0.5 or pred > last_rate * 1.5:
                # Use simple random walk with drift
                pred = rates_history[-1] * (1 + np.random.normal(0, 0.01))
            
            # Calculate confidence interval
            z = norm.ppf((1 + confidence) / 2)
            margin = z * (self._prediction_std if self._prediction_std else last_rate * 0.05)
            
            forecasts.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "point_forecast": float(pred),
                "lower_bound": float(pred - margin),
                "upper_bound": float(pred + margin)
            })
            
            # Add prediction to history for next iteration
            rates_history.append(pred)
        
        return {
            "model_name": self.MODEL_NAME,
            "currency": self._currency,
            "horizon": horizon,
            "confidence": confidence,
            "forecasts": forecasts,
            "metrics": self._metrics.to_dict() if self._metrics else None
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self._is_trained:
            raise RuntimeError("Model not trained")
        
        importance = self._model.feature_importances_
        return dict(zip(self._feature_cols, importance.tolist()))


def is_available() -> bool:
    """Check if XGBoost is available."""
    return XGBOOST_AVAILABLE

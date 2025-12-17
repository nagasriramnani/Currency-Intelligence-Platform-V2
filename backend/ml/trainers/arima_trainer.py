"""
ARIMA Trainer

Auto-ARIMA based time series forecasting trainer using pmdarima.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from .base import BaseTrainer, TrainingMetrics

logger = logging.getLogger(__name__)

# Try to import pmdarima
try:
    import pmdarima as pm
    from pmdarima.arima import auto_arima
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    logger.warning("pmdarima not installed. Run: pip install pmdarima")


class ARIMATrainer(BaseTrainer):
    """
    Auto-ARIMA based forecasting trainer.
    
    ARIMA is excellent for:
    - Short-term momentum
    - Stationary time series
    - Fast training
    """
    
    MODEL_NAME = "arima"
    
    def __init__(
        self,
        model_dir: str = "trained_models",
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5,
        seasonal: bool = False,
        stepwise: bool = True
    ):
        super().__init__(model_dir)
        
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.seasonal = seasonal
        self.stepwise = stepwise
    
    def train(
        self,
        df: pd.DataFrame,
        currency: str,
        train_ratio: float = 0.8
    ) -> TrainingMetrics:
        """Train ARIMA model with auto order selection."""
        if not ARIMA_AVAILABLE:
            raise RuntimeError("pmdarima not installed")
        
        start_time = time.time()
        
        # Prepare data
        df = df.copy()
        df = df.sort_values("record_date")
        df = df.dropna(subset=["exchange_rate"])
        
        self._data_start = pd.to_datetime(df["record_date"].min()).date()
        self._data_end = pd.to_datetime(df["record_date"].max()).date()
        self._currency = currency
        
        # Train/test split
        split_idx = int(len(df) * train_ratio)
        train_data = df["exchange_rate"].iloc[:split_idx].values
        test_data = df["exchange_rate"].iloc[split_idx:].values
        
        logger.info(f"Training ARIMA for {currency}: {len(train_data)} train, {len(test_data)} test samples")
        
        # Auto ARIMA
        self._model = auto_arima(
            train_data,
            start_p=1,
            start_q=1,
            max_p=self.max_p,
            max_d=self.max_d,
            max_q=self.max_q,
            seasonal=self.seasonal,
            stepwise=self.stepwise,
            suppress_warnings=True,
            error_action="ignore"
        )
        self._is_trained = True
        
        # Evaluate on test set
        if len(test_data) > 0:
            predictions = self._model.predict(n_periods=len(test_data))
            metrics = self.evaluate(test_data, predictions)
        else:
            metrics = {"rmse": 0, "mape": 0, "mae": 0, "directional_accuracy": 0}
        
        training_time = time.time() - start_time
        
        order = self._model.order
        logger.info(f"ARIMA order selected: {order}")
        
        self._metrics = TrainingMetrics(
            model_name=f"arima{order}",
            currency=currency,
            rmse=metrics["rmse"],
            mape=metrics["mape"],
            mae=metrics["mae"],
            directional_accuracy=metrics["directional_accuracy"],
            train_samples=len(train_data),
            test_samples=len(test_data),
            training_time_seconds=training_time,
            data_start=self._data_start,
            data_end=self._data_end
        )
        
        logger.info(f"ARIMA training complete: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.6f}")
        
        return self._metrics
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> Dict:
        """Generate ARIMA forecast."""
        if not self._is_trained:
            raise RuntimeError("Model must be trained before prediction")
        
        # Generate forecast with confidence intervals
        forecast, conf_int = self._model.predict(
            n_periods=horizon,
            return_conf_int=True,
            alpha=1 - confidence
        )
        
        # Generate dates (monthly intervals - 30 days each)
        from datetime import timedelta
        base_date = self._data_end
        dates = [base_date + timedelta(days=30*(i+1)) for i in range(horizon)]
        
        return {
            "model_name": self.MODEL_NAME,
            "currency": self._currency,
            "horizon": horizon,
            "confidence": confidence,
            "arima_order": str(self._model.order),
            "forecasts": [
                {
                    "date": dates[i].strftime("%Y-%m-%d"),
                    "point_forecast": float(forecast[i]),
                    "lower_bound": float(conf_int[i, 0]),
                    "upper_bound": float(conf_int[i, 1])
                }
                for i in range(horizon)
            ],
            "metrics": self._metrics.to_dict() if self._metrics else None
        }


def is_available() -> bool:
    """Check if ARIMA is available."""
    return ARIMA_AVAILABLE

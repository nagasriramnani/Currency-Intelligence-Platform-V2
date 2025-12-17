"""
Ensemble Trainer

Combines multiple forecasting models with weighted averaging.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .base import BaseTrainer, TrainingMetrics, TrainedModel
from .prophet_trainer import ProphetTrainer, is_available as prophet_available
from .arima_trainer import ARIMATrainer, is_available as arima_available
from .xgboost_trainer import XGBoostTrainer, is_available as xgboost_available

logger = logging.getLogger(__name__)


class EnsembleTrainer(BaseTrainer):
    """
    Ensemble trainer that combines predictions from multiple models.
    
    Weighting strategies:
    - Equal: Simple average
    - Inverse MAPE: Better models get higher weights
    - Custom: User-provided weights
    """
    
    MODEL_NAME = "ensemble"
    
    def __init__(
        self,
        model_dir: str = "trained_models",
        models_to_use: List[str] = None,
        weighting: str = "inverse_mape"  # 'equal', 'inverse_mape', 'custom'
    ):
        super().__init__(model_dir)
        
        # Default to all available models
        if models_to_use is None:
            models_to_use = []
            if prophet_available():
                models_to_use.append("prophet")
            if arima_available():
                models_to_use.append("arima")
            if xgboost_available():
                models_to_use.append("xgboost")
        
        self.models_to_use = models_to_use
        self.weighting = weighting
        
        self._trainers: Dict[str, BaseTrainer] = {}
        self._weights: Dict[str, float] = {}
        self._ensemble_metrics: Optional[TrainingMetrics] = None
    
    def _create_trainer(self, model_name: str) -> BaseTrainer:
        """Create trainer instance by name."""
        if model_name == "prophet":
            return ProphetTrainer(self.model_dir)
        elif model_name == "arima":
            return ARIMATrainer(self.model_dir)
        elif model_name == "xgboost":
            return XGBoostTrainer(self.model_dir)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def _calculate_weights(self) -> Dict[str, float]:
        """Calculate ensemble weights based on strategy."""
        if self.weighting == "equal":
            n = len(self._trainers)
            return {name: 1.0 / n for name in self._trainers}
        
        elif self.weighting == "inverse_mape":
            # Weight inversely proportional to MAPE
            mapes = {}
            for name, trainer in self._trainers.items():
                if trainer._metrics:
                    mapes[name] = max(trainer._metrics.mape, 0.01)  # Avoid division by zero
            
            if not mapes:
                return {name: 1.0 / len(self._trainers) for name in self._trainers}
            
            inverse_mapes = {name: 1.0 / mape for name, mape in mapes.items()}
            total = sum(inverse_mapes.values())
            
            return {name: inv / total for name, inv in inverse_mapes.items()}
        
        else:
            # Default to equal weights
            n = len(self._trainers)
            return {name: 1.0 / n for name in self._trainers}
    
    def train(
        self,
        df: pd.DataFrame,
        currency: str,
        train_ratio: float = 0.8
    ) -> TrainingMetrics:
        """Train all component models."""
        start_time = time.time()
        
        self._currency = currency
        self._data_start = pd.to_datetime(df["record_date"].min()).date()
        self._data_end = pd.to_datetime(df["record_date"].max()).date()
        
        logger.info(f"Training ensemble for {currency} with models: {self.models_to_use}")
        
        # Train each model
        all_metrics = []
        for model_name in self.models_to_use:
            try:
                logger.info(f"Training {model_name}...")
                trainer = self._create_trainer(model_name)
                metrics = trainer.train(df, currency, train_ratio)
                self._trainers[model_name] = trainer
                all_metrics.append(metrics)
                logger.info(f"  {model_name} MAPE: {metrics.mape:.2f}%")
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
        
        if not self._trainers:
            raise RuntimeError("No models trained successfully")
        
        # Calculate weights
        self._weights = self._calculate_weights()
        logger.info(f"Ensemble weights: {self._weights}")
        
        # Calculate ensemble metrics (weighted average)
        avg_mape = sum(
            self._trainers[name]._metrics.mape * weight
            for name, weight in self._weights.items()
        )
        avg_rmse = sum(
            self._trainers[name]._metrics.rmse * weight
            for name, weight in self._weights.items()
        )
        avg_dir_acc = sum(
            self._trainers[name]._metrics.directional_accuracy * weight
            for name, weight in self._weights.items()
        )
        
        training_time = time.time() - start_time
        
        self._metrics = TrainingMetrics(
            model_name=self.MODEL_NAME,
            currency=currency,
            rmse=avg_rmse,
            mape=avg_mape,
            mae=0.0,  # Not calculated for ensemble
            directional_accuracy=avg_dir_acc,
            train_samples=all_metrics[0].train_samples if all_metrics else 0,
            test_samples=all_metrics[0].test_samples if all_metrics else 0,
            training_time_seconds=training_time,
            data_start=self._data_start,
            data_end=self._data_end
        )
        
        self._is_trained = True
        
        logger.info(f"Ensemble training complete: Weighted MAPE={avg_mape:.2f}%")
        
        return self._metrics
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> Dict:
        """Generate ensemble forecast using weighted averaging."""
        if not self._is_trained:
            raise RuntimeError("Model must be trained before prediction")
        
        # Get predictions from all models
        all_predictions = {}
        for name, trainer in self._trainers.items():
            try:
                pred = trainer.predict(horizon, confidence)
                all_predictions[name] = pred
            except Exception as e:
                logger.warning(f"Failed to get prediction from {name}: {e}")
        
        if not all_predictions:
            raise RuntimeError("No predictions available")
        
        # Combine forecasts
        ensemble_forecasts = []
        base_date = self._data_end
        
        for i in range(horizon):
            date = base_date + timedelta(days=i+1)
            
            # Weighted average of point forecasts
            point_sum = 0.0
            lower_sum = 0.0
            upper_sum = 0.0
            weight_sum = 0.0
            
            model_contributions = {}
            
            for name, pred in all_predictions.items():
                if i < len(pred["forecasts"]):
                    weight = self._weights.get(name, 0)
                    forecast = pred["forecasts"][i]
                    
                    point_sum += forecast["point_forecast"] * weight
                    lower_sum += forecast["lower_bound"] * weight
                    upper_sum += forecast["upper_bound"] * weight
                    weight_sum += weight
                    
                    model_contributions[name] = {
                        "forecast": forecast["point_forecast"],
                        "weight": weight
                    }
            
            if weight_sum > 0:
                ensemble_forecasts.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "point_forecast": point_sum / weight_sum,
                    "lower_bound": lower_sum / weight_sum,
                    "upper_bound": upper_sum / weight_sum,
                    "model_contributions": model_contributions
                })
        
        # Calculate trust score based on model agreement
        if len(ensemble_forecasts) > 0:
            agreements = []
            for forecast in ensemble_forecasts:
                contribs = forecast.get("model_contributions", {})
                if len(contribs) > 1:
                    values = [c["forecast"] for c in contribs.values()]
                    std = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1
                    agreements.append(1 - min(std, 1))
            trust_score = np.mean(agreements) if agreements else 0.5
        else:
            trust_score = 0.5
        
        return {
            "model_name": self.MODEL_NAME,
            "currency": self._currency,
            "horizon": horizon,
            "confidence": confidence,
            "weights": self._weights,
            "trust_score": round(trust_score, 3),
            "component_models": list(self._trainers.keys()),
            "forecasts": ensemble_forecasts,
            "metrics": self._metrics.to_dict() if self._metrics else None
        }
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current ensemble weights."""
        return self._weights.copy()
    
    def get_component_metrics(self) -> Dict[str, Dict]:
        """Get metrics for each component model."""
        return {
            name: trainer._metrics.to_dict()
            for name, trainer in self._trainers.items()
            if trainer._metrics
        }


def is_available() -> bool:
    """Check if at least one model is available."""
    return prophet_available() or arima_available() or xgboost_available()

"""
Ensemble Orchestrator

Combines multiple forecasting models (Prophet, ARIMA, XGBoost) with
dynamic weighting based on recent performance.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import pandas as pd
import numpy as np

from .base import BaseForecaster, ForecastResult

logger = logging.getLogger(__name__)


@dataclass
class EnsembleForecast:
    """Result from ensemble model combining multiple forecasters."""
    currency: str
    forecast_dates: List[date]
    point_forecasts: List[float]
    lower_bounds: List[float]
    upper_bounds: List[float]
    confidence_level: float
    
    # Model-specific information
    model_weights: Dict[str, float]
    model_contributions: Dict[str, List[float]]
    model_metrics: Dict[str, Dict]
    
    # Trust score (0-1) based on model agreement
    trust_score: float
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "currency": self.currency,
            "forecasts": [
                {
                    "date": d.isoformat() if isinstance(d, date) else str(d),
                    "point": p,
                    "lower": l,
                    "upper": u
                }
                for d, p, l, u in zip(
                    self.forecast_dates,
                    self.point_forecasts,
                    self.lower_bounds,
                    self.upper_bounds
                )
            ],
            "confidence_level": self.confidence_level,
            "model_weights": self.model_weights,
            "trust_score": self.trust_score,
            "model_metrics": self.model_metrics
        }


class EnsembleForecaster:
    """
    Ensemble forecaster that combines multiple models.
    
    Weighting strategies:
    - Equal: Simple average of all models
    - Performance-based: Weight by inverse MAPE
    - Dynamic: Adjust weights based on recent accuracy
    """
    
    def __init__(
        self,
        weighting: str = "performance",
        min_models: int = 1
    ):
        """
        Initialize ensemble forecaster.
        
        Args:
            weighting: Weighting strategy ('equal', 'performance', 'dynamic')
            min_models: Minimum number of models required
        """
        self.weighting = weighting
        self.min_models = min_models
        
        self._models: Dict[str, BaseForecaster] = {}
        self._weights: Dict[str, float] = {}
        self._currency = None
    
    def register_model(self, model: BaseForecaster) -> "EnsembleForecaster":
        """
        Register a model with the ensemble.
        
        Args:
            model: Forecaster implementing BaseForecaster interface
            
        Returns:
            Self for method chaining
        """
        self._models[model.name] = model
        logger.info(f"Registered model: {model.name}")
        return self
    
    def fit(self, df: pd.DataFrame, currency: str) -> "EnsembleForecaster":
        """
        Fit all registered models.
        
        Args:
            df: DataFrame with 'record_date' and 'exchange_rate' columns
            currency: Currency code
            
        Returns:
            Self for method chaining
        """
        self._currency = currency
        
        for name, model in self._models.items():
            try:
                logger.info(f"Fitting {name} for {currency}...")
                model.fit(df, currency)
            except Exception as e:
                logger.error(f"Failed to fit {name}: {e}")
        
        # Calculate weights based on fitted metrics
        self._calculate_weights()
        
        return self
    
    def _calculate_weights(self) -> None:
        """Calculate model weights based on strategy."""
        fitted_models = {
            name: model
            for name, model in self._models.items()
            if model.is_fitted
        }
        
        if not fitted_models:
            logger.warning("No models fitted successfully")
            return
        
        if self.weighting == "equal":
            # Equal weights
            weight = 1.0 / len(fitted_models)
            self._weights = {name: weight for name in fitted_models}
            
        elif self.weighting == "performance":
            # Weight by inverse MAPE (lower MAPE = higher weight)
            mapes = {}
            for name, model in fitted_models.items():
                mape = model._mape
                if mape is not None and mape > 0:
                    mapes[name] = mape
            
            if mapes:
                # Inverse MAPE weights
                inverse_mapes = {name: 1.0 / mape for name, mape in mapes.items()}
                total = sum(inverse_mapes.values())
                self._weights = {name: v / total for name, v in inverse_mapes.items()}
                
                # Add zero weight for models without MAPE
                for name in fitted_models:
                    if name not in self._weights:
                        self._weights[name] = 0.0
            else:
                # Fallback to equal
                weight = 1.0 / len(fitted_models)
                self._weights = {name: weight for name in fitted_models}
        
        else:  # dynamic - to be expanded
            weight = 1.0 / len(fitted_models)
            self._weights = {name: weight for name in fitted_models}
        
        logger.info(f"Model weights: {self._weights}")
    
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> EnsembleForecast:
        """
        Generate ensemble forecast by combining all models.
        
        Args:
            horizon: Number of days to forecast
            confidence: Confidence interval level
            
        Returns:
            EnsembleForecast with combined predictions
        """
        fitted_models = {
            name: model
            for name, model in self._models.items()
            if model.is_fitted
        }
        
        if len(fitted_models) < self.min_models:
            logger.error(f"Not enough fitted models ({len(fitted_models)} < {self.min_models})")
            return EnsembleForecast(
                currency=self._currency or "UNKNOWN",
                forecast_dates=[],
                point_forecasts=[],
                lower_bounds=[],
                upper_bounds=[],
                confidence_level=confidence,
                model_weights={},
                model_contributions={},
                model_metrics={},
                trust_score=0.0
            )
        
        # Get individual forecasts
        forecasts: Dict[str, ForecastResult] = {}
        for name, model in fitted_models.items():
            try:
                forecasts[name] = model.predict(horizon, confidence)
            except Exception as e:
                logger.error(f"Prediction failed for {name}: {e}")
        
        if not forecasts:
            logger.error("No successful predictions")
            return EnsembleForecast(
                currency=self._currency,
                forecast_dates=[],
                point_forecasts=[],
                lower_bounds=[],
                upper_bounds=[],
                confidence_level=confidence,
                model_weights=self._weights,
                model_contributions={},
                model_metrics={},
                trust_score=0.0
            )
        
        # Find common forecast length
        min_len = min(len(f.forecast_dates) for f in forecasts.values())
        
        if min_len == 0:
            logger.warning("No forecasts generated")
            return EnsembleForecast(
                currency=self._currency,
                forecast_dates=[],
                point_forecasts=[],
                lower_bounds=[],
                upper_bounds=[],
                confidence_level=confidence,
                model_weights=self._weights,
                model_contributions={},
                model_metrics={},
                trust_score=0.0
            )
        
        # Combine forecasts using weights
        forecast_dates = list(forecasts.values())[0].forecast_dates[:min_len]
        
        combined_point = np.zeros(min_len)
        combined_lower = np.zeros(min_len)
        combined_upper = np.zeros(min_len)
        
        model_contributions = {}
        model_metrics = {}
        
        total_weight = sum(
            self._weights.get(name, 0.0)
            for name in forecasts
        )
        
        for name, forecast in forecasts.items():
            weight = self._weights.get(name, 0.0)
            if total_weight > 0:
                norm_weight = weight / total_weight
            else:
                norm_weight = 1.0 / len(forecasts)
            
            contributions = np.array(forecast.point_forecasts[:min_len])
            model_contributions[name] = contributions.tolist()
            
            combined_point += norm_weight * contributions
            combined_lower += norm_weight * np.array(forecast.lower_bounds[:min_len])
            combined_upper += norm_weight * np.array(forecast.upper_bounds[:min_len])
            
            model_metrics[name] = {
                "mape": forecast.training_mape,
                "directional_accuracy": forecast.directional_accuracy,
                "weight": norm_weight
            }
        
        # Calculate trust score based on model agreement
        trust_score = self._calculate_trust_score(model_contributions)
        
        return EnsembleForecast(
            currency=self._currency,
            forecast_dates=forecast_dates,
            point_forecasts=combined_point.tolist(),
            lower_bounds=combined_lower.tolist(),
            upper_bounds=combined_upper.tolist(),
            confidence_level=confidence,
            model_weights=self._weights,
            model_contributions=model_contributions,
            model_metrics=model_metrics,
            trust_score=trust_score
        )
    
    def _calculate_trust_score(self, contributions: Dict[str, List[float]]) -> float:
        """
        Calculate trust score based on model agreement.
        
        Higher score = more agreement between models.
        """
        if len(contributions) < 2:
            return 0.5  # Default for single model
        
        # Calculate coefficient of variation across models
        values = np.array(list(contributions.values()))
        
        if values.shape[1] == 0:
            return 0.0
        
        # Mean and std across models for each time point
        mean = np.mean(values, axis=0)
        std = np.std(values, axis=0)
        
        # Coefficient of variation
        with np.errstate(divide='ignore', invalid='ignore'):
            cv = np.where(mean != 0, std / np.abs(mean), 0)
        
        # Trust score is inverse of CV (higher agreement = lower CV = higher trust)
        avg_cv = np.mean(cv)
        trust = max(0.0, min(1.0, 1.0 - avg_cv))
        
        return float(trust)
    
    @property
    def available_models(self) -> List[str]:
        """List of registered model names."""
        return list(self._models.keys())
    
    @property
    def fitted_models(self) -> List[str]:
        """List of successfully fitted model names."""
        return [name for name, model in self._models.items() if model.is_fitted]

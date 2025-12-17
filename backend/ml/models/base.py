"""
Base Model Interface

Defines the abstract interface for all forecasting models in the ensemble.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import pandas as pd
import numpy as np


@dataclass
class ForecastResult:
    """Standard result format for all forecasting models."""
    model_name: str
    currency: str
    forecast_dates: List[date]
    point_forecasts: List[float]
    lower_bounds: List[float]  # Lower confidence interval
    upper_bounds: List[float]  # Upper confidence interval
    confidence_level: float  # e.g., 0.80 for 80% CI
    
    # Model metadata
    training_mape: Optional[float] = None
    directional_accuracy: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_name": self.model_name,
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
            "metrics": {
                "mape": self.training_mape,
                "directional_accuracy": self.directional_accuracy
            }
        }


class BaseForecaster(ABC):
    """
    Abstract base class for all forecasting models.
    
    Each model must implement:
    - fit(): Train the model on historical data
    - predict(): Generate forecasts for future periods
    - evaluate(): Calculate performance metrics
    """
    
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self._training_data = None
        self._mape = None
        self._directional_accuracy = None
    
    @abstractmethod
    def fit(self, df: pd.DataFrame, currency: str) -> "BaseForecaster":
        """
        Train the model on historical data.
        
        Args:
            df: DataFrame with columns 'record_date', 'exchange_rate'
            currency: Currency code (EUR, GBP, CAD)
            
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> ForecastResult:
        """
        Generate forecasts for future periods.
        
        Args:
            horizon: Number of days to forecast
            confidence: Confidence interval level (0.0-1.0)
            
        Returns:
            ForecastResult with predictions
        """
        pass
    
    def evaluate(self, actual: pd.Series, predicted: pd.Series) -> Dict[str, float]:
        """
        Calculate performance metrics.
        
        Args:
            actual: Series of actual values
            predicted: Series of predicted values
            
        Returns:
            Dictionary with MAPE, directional accuracy, RMSE
        """
        # Remove NaN values
        mask = ~(actual.isna() | predicted.isna())
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) == 0:
            return {"mape": None, "directional_accuracy": None, "rmse": None}
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Directional Accuracy
        if len(actual) > 1:
            actual_direction = np.sign(actual.diff().dropna())
            predicted_direction = np.sign(predicted.diff().dropna())
            min_len = min(len(actual_direction), len(predicted_direction))
            if min_len > 0:
                directional_accuracy = np.mean(
                    actual_direction[:min_len].values == predicted_direction[:min_len].values
                )
            else:
                directional_accuracy = None
        else:
            directional_accuracy = None
        
        # RMSE (Root Mean Squared Error)
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        self._mape = mape
        self._directional_accuracy = directional_accuracy
        
        return {
            "mape": mape,
            "directional_accuracy": directional_accuracy,
            "rmse": rmse
        }
    
    @property
    def metrics(self) -> Dict[str, Optional[float]]:
        """Get current model metrics."""
        return {
            "mape": self._mape,
            "directional_accuracy": self._directional_accuracy
        }

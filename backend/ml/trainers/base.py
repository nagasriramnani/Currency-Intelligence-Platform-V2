"""
Base Trainer Interface

Abstract base class for all model trainers in the Currency Intelligence Platform.
Provides consistent interface for training, evaluation, and serialization.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
import pandas as pd
import numpy as np
import pickle
import os
import json

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Metrics from model training and evaluation."""
    model_name: str
    currency: str
    
    # Core metrics
    rmse: float
    mape: float
    mae: float
    directional_accuracy: float
    
    # Training info
    train_samples: int
    test_samples: int
    training_time_seconds: float
    
    # Data window
    data_start: date
    data_end: date
    
    # Timestamp
    trained_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        # Include train/test samples in metrics for registry storage
        return {
            "model_name": self.model_name,
            "currency": self.currency,
            "metrics": {
                "rmse": round(self.rmse, 6),
                "mape": round(self.mape, 4),
                "mae": round(self.mae, 6),
                "directional_accuracy": round(self.directional_accuracy, 4),
                # Include sample counts in metrics for ForecastService
                "train_samples": self.train_samples,
                "test_samples": self.test_samples
            },
            "training": {
                "train_samples": self.train_samples,
                "test_samples": self.test_samples,
                "training_time_seconds": round(self.training_time_seconds, 2)
            },
            "data_window": {
                "start": self.data_start.isoformat() if isinstance(self.data_start, date) else str(self.data_start),
                "end": self.data_end.isoformat() if isinstance(self.data_end, date) else str(self.data_end)
            },
            "trained_at": self.trained_at.isoformat()
        }


@dataclass
class TrainedModel:
    """Container for a trained model with metadata."""
    model_name: str
    currency: str
    model_object: Any  # The actual trained model
    metrics: TrainingMetrics
    model_path: Optional[str] = None
    is_active: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "currency": self.currency,
            "metrics": self.metrics.to_dict(),
            "model_path": self.model_path,
            "is_active": self.is_active
        }


class BaseTrainer(ABC):
    """
    Abstract base class for model trainers.
    
    All trainers must implement:
    - train(): Fit model to data
    - predict(): Generate forecasts
    - evaluate(): Calculate metrics
    - save(): Serialize model to disk
    - load(): Load model from disk
    """
    
    MODEL_NAME: str = "base"
    
    def __init__(self, model_dir: str = "trained_models"):
        """
        Initialize trainer.
        
        Args:
            model_dir: Directory to save/load models
        """
        self.model_dir = model_dir
        self._model = None
        self._is_trained = False
        self._currency = None
        self._metrics: Optional[TrainingMetrics] = None
        self._data_start = None
        self._data_end = None
        
        # Create model directory
        os.makedirs(model_dir, exist_ok=True)
    
    @abstractmethod
    def train(
        self,
        df: pd.DataFrame,
        currency: str,
        train_ratio: float = 0.8
    ) -> TrainingMetrics:
        """
        Train model on historical data.
        
        Args:
            df: DataFrame with 'record_date' and 'exchange_rate'
            currency: Currency code
            train_ratio: Fraction for training (rest for validation)
            
        Returns:
            TrainingMetrics with evaluation results
        """
        pass
    
    @abstractmethod
    def predict(
        self,
        horizon: int,
        confidence: float = 0.80
    ) -> Dict:
        """
        Generate forecast.
        
        Args:
            horizon: Days to forecast
            confidence: Confidence level for intervals
            
        Returns:
            Dict with forecasts and metadata
        """
        pass
    
    def evaluate(
        self,
        actual: np.ndarray,
        predicted: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate evaluation metrics.
        
        Args:
            actual: True values
            predicted: Predicted values
            
        Returns:
            Dict with RMSE, MAPE, MAE, directional accuracy
        """
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Filter valid pairs
        mask = ~np.isnan(actual) & ~np.isnan(predicted)
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) == 0:
            return {"rmse": float('inf'), "mape": float('inf'), "mae": float('inf'), "directional_accuracy": 0.0}
        
        # RMSE
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # MAE
        mae = np.mean(np.abs(actual - predicted))
        
        # MAPE
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Directional accuracy
        if len(actual) > 1:
            actual_dir = np.sign(np.diff(actual))
            pred_dir = np.sign(np.diff(predicted))
            dir_acc = np.mean(actual_dir == pred_dir)
        else:
            dir_acc = 0.0
        
        return {
            "rmse": float(rmse),
            "mape": float(mape),
            "mae": float(mae),
            "directional_accuracy": float(dir_acc)
        }
    
    def save(self, currency: str) -> str:
        """
        Save trained model to disk.
        
        Args:
            currency: Currency code
            
        Returns:
            Path to saved model
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before saving")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.MODEL_NAME}_{currency}_{timestamp}.pkl"
        filepath = os.path.join(self.model_dir, filename)
        
        # Save model and metadata
        save_data = {
            "model": self._model,
            "currency": self._currency,
            "metrics": self._metrics.to_dict() if self._metrics else None,
            "data_start": self._data_start,
            "data_end": self._data_end,
            "trained_at": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        logger.info(f"Saved model to {filepath}")
        return filepath
    
    def load(self, filepath: str) -> "BaseTrainer":
        """
        Load model from disk.
        
        Args:
            filepath: Path to saved model
            
        Returns:
            Self with loaded model
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self._model = data["model"]
        self._currency = data["currency"]
        self._data_start = data.get("data_start")
        self._data_end = data.get("data_end")
        self._is_trained = True
        
        logger.info(f"Loaded model from {filepath}")
        return self
    
    def get_trained_model(self) -> TrainedModel:
        """Get TrainedModel container with metadata."""
        if not self._is_trained:
            raise RuntimeError("Model not trained")
        
        return TrainedModel(
            model_name=self.MODEL_NAME,
            currency=self._currency,
            model_object=self._model,
            metrics=self._metrics
        )
    
    @property
    def is_trained(self) -> bool:
        return self._is_trained
    
    @property
    def model_name(self) -> str:
        return self.MODEL_NAME

"""
Training Orchestrator

Orchestrates the complete training pipeline:
1. Load data from Supabase
2. Select and train models
3. Evaluate and compare
4. Register best model
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from ..trainers.base import BaseTrainer, TrainingMetrics, TrainedModel
from ..trainers.prophet_trainer import ProphetTrainer, is_available as prophet_available
from ..trainers.arima_trainer import ARIMATrainer, is_available as arima_available
from ..trainers.xgboost_trainer import XGBoostTrainer, is_available as xgboost_available
from ..trainers.ensemble_trainer import EnsembleTrainer
from .model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class TrainingOrchestrator:
    """
    Orchestrates model training, evaluation, and registration.
    
    Usage:
        orchestrator = TrainingOrchestrator(model_type="ensemble")
        orchestrator.train(df, currency="EUR")
        orchestrator.save()
    """
    
    AVAILABLE_MODELS = {
        "prophet": ProphetTrainer,
        "arima": ARIMATrainer,
        "xgboost": XGBoostTrainer,
        "ensemble": EnsembleTrainer
    }
    
    def __init__(
        self,
        model_type: str = "ensemble",
        model_dir: str = "trained_models",
        use_supabase: bool = False
    ):
        """
        Initialize training orchestrator.
        
        Args:
            model_type: Model to train ('prophet', 'arima', 'xgboost', 'ensemble')
            model_dir: Directory for saved models
            use_supabase: Whether to sync with Supabase
        """
        self.model_type = model_type.lower()
        self.model_dir = model_dir
        self.use_supabase = use_supabase
        
        self._trainer: Optional[BaseTrainer] = None
        self._registry = ModelRegistry(model_dir, use_supabase)
        self._results: Dict[str, TrainingMetrics] = {}
        
        os.makedirs(model_dir, exist_ok=True)
        
        # Validate model type
        if self.model_type not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(self.AVAILABLE_MODELS.keys())}")
    
    @classmethod
    def get_available_models(cls) -> Dict[str, bool]:
        """Get available models and their status."""
        return {
            "prophet": prophet_available(),
            "arima": arima_available(),
            "xgboost": xgboost_available(),
            "ensemble": prophet_available() or arima_available() or xgboost_available()
        }
    
    def load_data_from_supabase(
        self,
        currency: str,
        days: int = 1825  # 5 years
    ) -> pd.DataFrame:
        """
        Load historical data from Supabase.
        
        Args:
            currency: Currency code
            days: Number of days of history
            
        Returns:
            DataFrame with record_date and exchange_rate
        """
        try:
            from core.database import get_fx_history, is_supabase_configured
            
            if not is_supabase_configured():
                raise RuntimeError("Supabase not configured")
            
            data = get_fx_history(currency, days)
            
            if not data:
                raise RuntimeError(f"No data found for {currency}")
            
            df = pd.DataFrame(data)
            df["record_date"] = pd.to_datetime(df["record_date"])
            df["exchange_rate"] = pd.to_numeric(df["rate"])
            df = df.sort_values("record_date")
            
            logger.info(f"Loaded {len(df)} records for {currency} from Supabase")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load from Supabase: {e}")
            raise
    
    def train(
        self,
        df: pd.DataFrame,
        currency: str,
        train_ratio: float = 0.8
    ) -> TrainingMetrics:
        """
        Train the selected model.
        
        Args:
            df: DataFrame with record_date and exchange_rate
            currency: Currency code
            train_ratio: Train/test split ratio
            
        Returns:
            TrainingMetrics
        """
        logger.info(f"Starting training: model={self.model_type}, currency={currency}, samples={len(df)}")
        
        # Create trainer
        trainer_class = self.AVAILABLE_MODELS[self.model_type]
        self._trainer = trainer_class(self.model_dir)
        
        # Train
        metrics = self._trainer.train(df, currency, train_ratio)
        self._results[currency] = metrics
        
        logger.info(f"Training complete: MAPE={metrics.mape:.2f}%, Dir. Acc={metrics.directional_accuracy:.1%}")
        
        return metrics
    
    def save(self, set_active: bool = True) -> str:
        """
        Save trained model and register.
        
        Args:
            set_active: Whether to set as active model
            
        Returns:
            Path to saved model
        """
        if self._trainer is None or not self._trainer.is_trained:
            raise RuntimeError("No model trained to save")
        
        # Save model to disk
        currency = self._trainer._currency
        model_path = self._trainer.save(currency)
        
        # Register in registry
        metrics = self._trainer._metrics
        self._registry.register(
            model_name=self.model_type,
            currency=currency,
            model_path=model_path,
            metrics=metrics.to_dict()["metrics"],
            data_start=str(metrics.data_start),
            data_end=str(metrics.data_end),
            set_active=set_active
        )
        
        logger.info(f"Model saved and registered: {model_path}")
        
        return model_path
    
    def train_all_currencies(
        self,
        currencies: List[str] = ["EUR", "GBP", "CAD"],
        days: int = 1825
    ) -> Dict[str, TrainingMetrics]:
        """
        Train model for all currencies.
        
        Args:
            currencies: List of currency codes
            days: Days of history
            
        Returns:
            Dict of currency -> TrainingMetrics
        """
        results = {}
        
        for currency in currencies:
            try:
                logger.info(f"\n{'='*50}\nTraining for {currency}\n{'='*50}")
                
                # Load data
                df = self.load_data_from_supabase(currency, days)
                
                # Train
                metrics = self.train(df, currency)
                
                # Save
                self.save(set_active=True)
                
                results[currency] = metrics
                
            except Exception as e:
                logger.error(f"Failed to train for {currency}: {e}")
        
        return results
    
    def compare_models(
        self,
        df: pd.DataFrame,
        currency: str,
        models_to_compare: List[str] = None
    ) -> Dict[str, TrainingMetrics]:
        """
        Compare multiple models on the same data.
        
        Args:
            df: Training data
            currency: Currency code
            models_to_compare: Models to compare
            
        Returns:
            Dict of model_name -> TrainingMetrics
        """
        if models_to_compare is None:
            models_to_compare = ["prophet", "arima", "xgboost"]
        
        results = {}
        
        for model_name in models_to_compare:
            if model_name not in self.AVAILABLE_MODELS:
                continue
            
            if not self.get_available_models().get(model_name, False):
                logger.warning(f"{model_name} not available, skipping")
                continue
            
            try:
                trainer_class = self.AVAILABLE_MODELS[model_name]
                trainer = trainer_class(self.model_dir)
                metrics = trainer.train(df, currency)
                results[model_name] = metrics
                
                logger.info(f"{model_name}: MAPE={metrics.mape:.2f}%")
                
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
        
        # Print comparison table
        self._print_comparison(results)
        
        return results
    
    def _print_comparison(self, results: Dict[str, TrainingMetrics]) -> None:
        """Print model comparison table."""
        if not results:
            return
        
        print("\n" + "="*70)
        print(f"{'Model':<15} {'MAPE':<10} {'RMSE':<12} {'Dir Acc':<10} {'Time (s)':<10}")
        print("="*70)
        
        for name, metrics in sorted(results.items(), key=lambda x: x[1].mape):
            print(f"{name:<15} {metrics.mape:<10.2f} {metrics.rmse:<12.6f} {metrics.directional_accuracy:<10.1%} {metrics.training_time_seconds:<10.1f}")
        
        print("="*70)
        
        # Best model
        best = min(results.items(), key=lambda x: x[1].mape)
        print(f"\n🏆 Best model by MAPE: {best[0]} ({best[1].mape:.2f}%)")
    
    def get_active_model(self, currency: str):
        """Get the active model for a currency."""
        return self._registry.get_active_model(currency)
    
    def get_registry_summary(self) -> Dict:
        """Get registry summary."""
        return self._registry.get_registry_summary()

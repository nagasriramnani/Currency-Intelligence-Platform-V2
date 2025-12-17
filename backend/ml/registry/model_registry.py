"""
Model Registry

Manages trained model versions, tracking which models are active per currency.
Supports both file-based and Supabase-based storage.
"""

import logging
import os
import json
import glob
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""
    model_id: str
    model_name: str
    currency_pair: str
    trained_at: str
    data_window_start: str
    data_window_end: str
    metrics: Dict[str, float]
    model_path: str
    is_active: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ModelRegistry:
    """
    Registry for trained models.
    
    Features:
    - Track multiple model versions per currency
    - Mark models as active/inactive
    - Persist to file or Supabase
    - Load active model for inference
    """
    
    def __init__(
        self,
        registry_dir: str = "trained_models",
        use_supabase: bool = False
    ):
        """
        Initialize model registry.
        
        Args:
            registry_dir: Directory for model files and registry
            use_supabase: Whether to sync with Supabase
        """
        self.registry_dir = registry_dir
        self.use_supabase = use_supabase
        self.registry_file = os.path.join(registry_dir, "model_registry.json")
        
        os.makedirs(registry_dir, exist_ok=True)
        
        self._registry: Dict[str, List[ModelMetadata]] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from file."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                for currency, models in data.items():
                    self._registry[currency] = [
                        ModelMetadata(**m) for m in models
                    ]
                
                logger.info(f"Loaded registry with {sum(len(v) for v in self._registry.values())} models")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self._registry = {}
        else:
            self._registry = {}
    
    def _save_registry(self) -> None:
        """Save registry to file."""
        data = {
            currency: [m.to_dict() for m in models]
            for currency, models in self._registry.items()
        }
        
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved registry to {self.registry_file}")
        
        # Optionally sync to Supabase
        if self.use_supabase:
            self._sync_to_supabase()
    
    def _sync_to_supabase(self) -> None:
        """Sync registry to Supabase."""
        try:
            from core.database import get_supabase_client, is_supabase_configured
            
            if not is_supabase_configured():
                logger.warning("Supabase not configured, skipping sync")
                return
            
            client = get_supabase_client()
            
            for currency, models in self._registry.items():
                for model in models:
                    # Upsert to Supabase
                    client.table("model_performance").upsert({
                        "model_name": model.model_name,
                        "currency_pair": model.currency_pair,
                        "mape": model.metrics.get("mape", 0),
                        "directional_accuracy": model.metrics.get("directional_accuracy", 0),
                        "is_active": model.is_active,
                        "trained_at": model.trained_at,
                        "model_path": model.model_path
                    }).execute()
            
            logger.info("Synced registry to Supabase")
            
        except Exception as e:
            logger.error(f"Failed to sync to Supabase: {e}")
    
    def register(
        self,
        model_name: str,
        currency: str,
        model_path: str,
        metrics: Dict[str, float],
        data_start: str,
        data_end: str,
        set_active: bool = True
    ) -> ModelMetadata:
        """
        Register a trained model.
        
        Args:
            model_name: Name of the model (prophet, arima, xgboost, ensemble)
            currency: Currency code
            model_path: Path to saved model file
            metrics: Training metrics
            data_start: Data window start date
            data_end: Data window end date
            set_active: Whether to set as active model
            
        Returns:
            ModelMetadata for registered model
        """
        model_id = f"{model_name}_{currency}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            currency_pair=currency,
            trained_at=datetime.utcnow().isoformat(),
            data_window_start=data_start,
            data_window_end=data_end,
            metrics=metrics,
            model_path=model_path,
            is_active=False
        )
        
        # Add to registry
        if currency not in self._registry:
            self._registry[currency] = []
        
        self._registry[currency].append(metadata)
        
        # Set as active if requested
        if set_active:
            self.set_active(currency, model_id)
        
        self._save_registry()
        
        logger.info(f"Registered model: {model_id}")
        
        return metadata
    
    def set_active(self, currency: str, model_id: str) -> bool:
        """
        Set a model as active for a currency.
        
        Args:
            currency: Currency code
            model_id: Model ID to activate
            
        Returns:
            True if successful
        """
        if currency not in self._registry:
            return False
        
        found = False
        for model in self._registry[currency]:
            if model.model_id == model_id:
                model.is_active = True
                found = True
            else:
                model.is_active = False
        
        if found:
            self._save_registry()
            logger.info(f"Set active model for {currency}: {model_id}")
        
        return found
    
    def get_active_model(self, currency: str) -> Optional[ModelMetadata]:
        """
        Get the active model for a currency.
        
        Args:
            currency: Currency code
            
        Returns:
            ModelMetadata or None if no active model
        """
        if currency not in self._registry:
            return None
        
        for model in self._registry[currency]:
            if model.is_active:
                return model
        
        # Return most recent if no active model
        if self._registry[currency]:
            return sorted(
                self._registry[currency],
                key=lambda m: m.trained_at,
                reverse=True
            )[0]
        
        return None
    
    def get_all_models(self, currency: Optional[str] = None) -> Dict[str, List[ModelMetadata]]:
        """
        Get all registered models.
        
        Args:
            currency: Optional filter by currency
            
        Returns:
            Dict of currency -> list of models
        """
        if currency:
            return {currency: self._registry.get(currency, [])}
        return self._registry.copy()
    
    def load_model(self, model_path: str) -> Any:
        """
        Load a model from disk.
        
        Args:
            model_path: Path to model file
            
        Returns:
            Loaded model object
        """
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        return data
    
    def get_best_model(
        self,
        currency: str,
        metric: str = "mape"
    ) -> Optional[ModelMetadata]:
        """
        Get the best performing model for a currency.
        
        Args:
            currency: Currency code
            metric: Metric to use for comparison (lower is better)
            
        Returns:
            ModelMetadata or None
        """
        if currency not in self._registry:
            return None
        
        models = self._registry[currency]
        if not models:
            return None
        
        # Sort by metric (lower is better for MAPE, RMSE)
        return min(models, key=lambda m: m.metrics.get(metric, float('inf')))
    
    def cleanup_old_models(self, keep_per_currency: int = 5) -> int:
        """
        Remove old model files, keeping only the most recent.
        
        Args:
            keep_per_currency: Number of models to keep per currency
            
        Returns:
            Number of models removed
        """
        removed = 0
        
        for currency, models in self._registry.items():
            if len(models) <= keep_per_currency:
                continue
            
            # Sort by trained_at
            sorted_models = sorted(models, key=lambda m: m.trained_at, reverse=True)
            
            # Remove old ones
            to_remove = sorted_models[keep_per_currency:]
            for model in to_remove:
                try:
                    if os.path.exists(model.model_path):
                        os.remove(model.model_path)
                        removed += 1
                    models.remove(model)
                except Exception as e:
                    logger.warning(f"Failed to remove model {model.model_id}: {e}")
        
        self._save_registry()
        logger.info(f"Removed {removed} old models")
        
        return removed
    
    def get_registry_summary(self) -> Dict:
        """Get summary of registry state."""
        summary = {
            "total_models": sum(len(v) for v in self._registry.values()),
            "currencies": list(self._registry.keys()),
            "active_models": {}
        }
        
        for currency in self._registry:
            active = self.get_active_model(currency)
            if active:
                summary["active_models"][currency] = {
                    "model_name": active.model_name,
                    "model_id": active.model_id,
                    "trained_at": active.trained_at,
                    "mape": active.metrics.get("mape")
                }
        
        return summary

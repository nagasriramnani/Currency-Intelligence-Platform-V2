"""
Model Migration Script

Migrates existing trained models to include residuals for confidence intervals.
For models missing residuals, performs a lightweight rolling backtest on the
last N observations to compute residuals.

Usage:
    python -m ml.services.migrate_models

Author: Currency Intelligence Platform
"""

import os
import sys
import logging
import pickle
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)


def compute_residuals_via_backtest(
    model,
    model_type: str,
    data: pd.DataFrame,
    n_points: int = 24
) -> np.ndarray:
    """
    Compute residuals via rolling backtest on last N observations.
    
    This simulates what the model would have predicted at each historical
    point and compares to actual values.
    
    Args:
        model: Trained model object
        model_type: Type of model (prophet, arima, xgboost)
        data: Historical data with record_date and exchange_rate columns
        n_points: Number of points to use for backtest
    
    Returns:
        Array of residuals (actual - predicted)
    """
    data = data.sort_values("record_date")
    if len(data) < n_points + 1:
        n_points = max(len(data) - 1, 5)
    
    residuals = []
    
    try:
        if model_type == "prophet":
            residuals = _compute_prophet_residuals(model, data, n_points)
        elif model_type == "arima":
            residuals = _compute_arima_residuals(model, data, n_points)
        elif model_type == "xgboost":
            residuals = _compute_xgboost_residuals(model, data, n_points)
        else:
            # Generic approach - use in-sample errors
            logger.warning(f"Unknown model type {model_type}, using generic residual estimation")
            residuals = _estimate_generic_residuals(data, n_points)
    except Exception as e:
        logger.error(f"Residual computation failed: {e}")
        # Fallback: estimate from data variance
        residuals = _estimate_generic_residuals(data, n_points)
    
    return np.array(residuals)


def _compute_prophet_residuals(model, data: pd.DataFrame, n_points: int) -> List[float]:
    """Compute Prophet residuals using in-sample predictions."""
    prophet_df = pd.DataFrame({
        "ds": pd.to_datetime(data["record_date"]),
        "y": data["exchange_rate"].values
    })
    
    # Get in-sample predictions
    forecast = model.predict(prophet_df)
    
    # Compute residuals for last n_points
    actual = prophet_df["y"].values[-n_points:]
    predicted = forecast["yhat"].values[-n_points:]
    
    return list(actual - predicted)


def _compute_arima_residuals(model, data: pd.DataFrame, n_points: int) -> List[float]:
    """Compute ARIMA residuals from model."""
    # ARIMA models store residuals
    if hasattr(model, 'resid'):
        residuals = model.resid()
        if len(residuals) >= n_points:
            return list(residuals[-n_points:])
    
    # Fallback: use prediction residuals
    return _estimate_generic_residuals(data, n_points)


def _compute_xgboost_residuals(model, data: pd.DataFrame, n_points: int) -> List[float]:
    """Compute XGBoost residuals via rolling prediction."""
    residuals = []
    
    rates = data["exchange_rate"].values
    
    # Build simple lag features for each point
    for i in range(len(rates) - n_points, len(rates) - 1):
        if i < 7:
            continue
        
        # Build features from history up to point i
        history = rates[:i]
        
        features = {
            "lag_1": history[-1] if len(history) >= 1 else 0,
            "lag_2": history[-2] if len(history) >= 2 else 0,
            "lag_3": history[-3] if len(history) >= 3 else 0,
            "rolling_mean_7": np.mean(history[-7:]) if len(history) >= 7 else np.mean(history),
            "rolling_std_7": np.std(history[-7:]) if len(history) >= 7 else 0.01,
        }
        
        # Get feature columns from model
        if hasattr(model, 'feature_names_in_'):
            feature_cols = list(model.feature_names_in_)
            X = pd.DataFrame([{col: features.get(col, 0) for col in feature_cols}])
        else:
            X = pd.DataFrame([features])
        
        try:
            pred = model.predict(X)[0]
            actual = rates[i + 1]
            residuals.append(actual - pred)
        except:
            continue
    
    if len(residuals) < 5:
        return _estimate_generic_residuals(data, n_points)
    
    return residuals


def _estimate_generic_residuals(data: pd.DataFrame, n_points: int) -> List[float]:
    """Estimate residuals from data variance as fallback."""
    rates = data["exchange_rate"].values[-n_points:]
    
    # Use returns as proxy for residuals
    returns = np.diff(rates)
    
    # Scale to match typical forecast error magnitude
    mean_rate = np.mean(rates)
    residuals = returns * mean_rate
    
    return list(residuals)


def migrate_model(model_path: str, model_type: str, data: pd.DataFrame) -> bool:
    """
    Migrate a single model to include residuals.
    
    Args:
        model_path: Path to model file
        model_type: Type of model
        data: Historical data for residual computation
    
    Returns:
        True if migration successful
    """
    try:
        # Load existing model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Check if already has residuals
        if isinstance(model_data, dict) and "residuals" in model_data:
            logger.info(f"Model {model_path} already has residuals, skipping")
            return True
        
        # Extract model object
        if isinstance(model_data, dict):
            model = model_data.get("model", model_data)
        else:
            model = model_data
        
        # Compute residuals
        residuals = compute_residuals_via_backtest(model, model_type, data)
        
        # Create new model data with residuals
        new_model_data = {
            "model": model,
            "residuals": residuals.tolist(),
            "migrated_at": datetime.utcnow().isoformat(),
            "residual_count": len(residuals)
        }
        
        # Save updated model
        with open(model_path, 'wb') as f:
            pickle.dump(new_model_data, f)
        
        logger.info(f"Migrated {model_path} with {len(residuals)} residuals")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate {model_path}: {e}")
        return False


def migrate_all_models(registry_dir: str = "trained_models", data_source=None):
    """
    Migrate all models in registry to include residuals.
    
    Args:
        registry_dir: Directory containing model files
        data_source: Callable or DataFrame to get historical data
    """
    import json
    
    registry_file = os.path.join(registry_dir, "model_registry.json")
    
    if not os.path.exists(registry_file):
        logger.warning(f"Registry file not found: {registry_file}")
        return
    
    with open(registry_file, 'r') as f:
        registry = json.load(f)
    
    migrated = 0
    failed = 0
    
    for currency, models in registry.items():
        # Get historical data for this currency
        if callable(data_source):
            data = data_source(currency)
        elif isinstance(data_source, pd.DataFrame):
            data = data_source[data_source["currency"] == currency].copy()
        else:
            logger.warning(f"No data source for {currency}, skipping")
            continue
        
        for model_info in models:
            model_path = model_info.get("model_path", "")
            model_type = model_info.get("model_name", "").lower()
            
            if not model_path or not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                failed += 1
                continue
            
            # Infer model type from name
            if "prophet" in model_type:
                model_type = "prophet"
            elif "arima" in model_type:
                model_type = "arima"
            elif "xgboost" in model_type:
                model_type = "xgboost"
            elif "ensemble" in model_type:
                model_type = "xgboost"  # Treat ensemble like xgboost
            
            if migrate_model(model_path, model_type, data):
                migrated += 1
            else:
                failed += 1
    
    logger.info(f"Migration complete: {migrated} migrated, {failed} failed")
    return {"migrated": migrated, "failed": failed}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Model Migration Script")
    print("=" * 60)
    print("\nThis script migrates existing models to include residuals")
    print("for proper confidence interval computation.\n")
    
    # Try to load data
    try:
        from data.treasury_client import TreasuryClient
        client = TreasuryClient()
        df = client.get_fx_rates(years_back=5)
        
        migrate_all_models("trained_models", df)
        
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Please ensure the backend is set up correctly.")

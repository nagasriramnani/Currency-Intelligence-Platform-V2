#!/usr/bin/env python
"""
Interactive Model Training CLI

Usage:
    python train_models.py

This script provides an interactive CLI for:
1. Syncing Treasury data to Supabase
2. Selecting forecasting model(s)
3. Training on 5 years of historical data
4. Comparing model performance
5. Registering the best model
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def print_header():
    """Print CLI header."""
    print("\n" + "="*60)
    print("  🧠 Currency Intelligence - Model Training CLI")
    print("="*60)
    print()


def print_available_models() -> Dict[str, bool]:
    """Print available models and return their status."""
    from ml.registry.orchestrator import TrainingOrchestrator
    
    available = TrainingOrchestrator.get_available_models()
    
    print("📦 Available Models:")
    print("-"*40)
    for name, is_available in available.items():
        status = "✅ Available" if is_available else "❌ Not installed"
        print(f"  {name.upper():<10} {status}")
    print()
    
    return available


def select_model() -> str:
    """Interactive model selection."""
    print("Select forecasting model:")
    print("-"*40)
    print("  [1] Prophet    - Best for trends & seasonality")
    print("  [2] ARIMA      - Best for short-term momentum")
    print("  [3] XGBoost    - Best for feature-rich prediction")
    print("  [4] Ensemble   - Combines all models (recommended)")
    print("  [5] Compare All - Train & compare all models")
    print("-"*40)
    
    while True:
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            return "prophet"
        elif choice == "2":
            return "arima"
        elif choice == "3":
            return "xgboost"
        elif choice == "4":
            return "ensemble"
        elif choice == "5":
            return "compare"
        else:
            print("Invalid choice. Please enter 1-5.")


def select_currencies() -> List[str]:
    """Select currencies to train."""
    print("\nSelect currencies to train:")
    print("-"*40)
    print("  [1] All (EUR, GBP, CAD)")
    print("  [2] EUR only")
    print("  [3] GBP only")
    print("  [4] CAD only")
    print("  [5] Custom")
    print("-"*40)
    
    while True:
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            return ["EUR", "GBP", "CAD"]
        elif choice == "2":
            return ["EUR"]
        elif choice == "3":
            return ["GBP"]
        elif choice == "4":
            return ["CAD"]
        elif choice == "5":
            custom = input("Enter currencies separated by comma: ").strip()
            return [c.strip().upper() for c in custom.split(",")]
        else:
            print("Invalid choice. Please enter 1-5.")


def sync_data_to_supabase() -> bool:
    """Sync Treasury data to Supabase."""
    print("\n📡 Syncing Treasury data to Supabase...")
    
    try:
        from data.sync import sync_treasury_to_supabase
        from core.database import is_supabase_configured
        
        if not is_supabase_configured():
            print("❌ Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env")
            return False
        
        result = sync_treasury_to_supabase()
        
        if result.get("status") == "success":
            print(f"✅ Synced {result.get('synced_count', 0)} records to Supabase")
            return True
        else:
            print(f"⚠️ Sync completed with issues: {result.get('message', 'Unknown')}")
            return True
            
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return False


def load_data(currency: str, days: int = 1825) -> Optional[pd.DataFrame]:
    """Load data from Supabase or fallback to Treasury API."""
    print(f"\n📊 Loading data for {currency}...")
    
    try:
        # Try Supabase first
        from core.database import get_fx_history, is_supabase_configured
        
        if is_supabase_configured():
            data = get_fx_history(currency, days)
            if data:
                df = pd.DataFrame(data)
                df["record_date"] = pd.to_datetime(df["record_date"])
                df["exchange_rate"] = pd.to_numeric(df["rate"])
                print(f"  ✅ Loaded {len(df)} records from Supabase")
                return df
        
        # Fallback to Treasury API
        print("  ⚠️ Supabase unavailable, falling back to Treasury API...")
        from data.treasury_client import TreasuryAPIClient
        
        client = TreasuryAPIClient()
        df = client.get_historical_data(currency)
        if not df.empty:
            print(f"  ✅ Loaded {len(df)} records from Treasury API")
            return df
        
        print(f"  ❌ No data found for {currency}")
        return None
        
    except Exception as e:
        print(f"  ❌ Failed to load data: {e}")
        return None


def train_model(model_type: str, currencies: List[str]) -> Dict:
    """Train model for specified currencies."""
    from ml.registry.orchestrator import TrainingOrchestrator
    
    results = {}
    
    for currency in currencies:
        print(f"\n{'='*60}")
        print(f"  Training {model_type.upper()} for {currency}")
        print("="*60)
        
        # Load data
        df = load_data(currency)
        if df is None or df.empty:
            print(f"❌ Skipping {currency} - no data")
            continue
        
        try:
            orchestrator = TrainingOrchestrator(model_type=model_type)
            metrics = orchestrator.train(df, currency)
            model_path = orchestrator.save(set_active=True)
            
            results[currency] = {
                "model": model_type,
                "mape": metrics.mape,
                "rmse": metrics.rmse,
                "directional_accuracy": metrics.directional_accuracy,
                "model_path": model_path
            }
            
            print(f"\n✅ {currency} trained successfully!")
            print(f"   MAPE: {metrics.mape:.2f}%")
            print(f"   Directional Accuracy: {metrics.directional_accuracy:.1%}")
            print(f"   Model saved: {model_path}")
            
        except Exception as e:
            print(f"❌ Training failed for {currency}: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def compare_models(currencies: List[str]) -> Dict:
    """Compare all models for specified currencies."""
    from ml.registry.orchestrator import TrainingOrchestrator
    
    all_results = {}
    
    for currency in currencies:
        print(f"\n{'='*60}")
        print(f"  Comparing Models for {currency}")
        print("="*60)
        
        # Load data
        df = load_data(currency)
        if df is None or df.empty:
            print(f"❌ Skipping {currency} - no data")
            continue
        
        try:
            orchestrator = TrainingOrchestrator(model_type="prophet")
            results = orchestrator.compare_models(df, currency)
            
            all_results[currency] = results
            
            # Train ensemble and save as active
            print(f"\n🎯 Training Ensemble for {currency}...")
            orchestrator = TrainingOrchestrator(model_type="ensemble")
            metrics = orchestrator.train(df, currency)
            orchestrator.save(set_active=True)
            
            print(f"✅ Ensemble model set as active for {currency}")
            
        except Exception as e:
            print(f"❌ Comparison failed for {currency}: {e}")
    
    return all_results


def print_summary(results: Dict) -> None:
    """Print training summary."""
    print("\n" + "="*60)
    print("  📋 Training Summary")
    print("="*60)
    
    for currency, data in results.items():
        print(f"\n  {currency}:")
        if isinstance(data, dict) and "mape" in data:
            print(f"    Model: {data.get('model', 'unknown')}")
            print(f"    MAPE: {data['mape']:.2f}%")
            print(f"    Dir. Accuracy: {data['directional_accuracy']:.1%}")
        else:
            print("    Failed to train")
    
    print("\n" + "="*60)
    print("  ✅ Training complete!")
    print("  📁 Models saved to: trained_models/")
    print("  🔧 Use /api/forecasts to generate predictions")
    print("="*60 + "\n")


def main():
    """Main CLI entry point."""
    print_header()
    
    # Check available models
    available = print_available_models()
    
    if not any(available.values()):
        print("❌ No models available. Please install required packages:")
        print("   pip install prophet pmdarima xgboost")
        return 1
    
    # Ask if user wants to sync data first
    sync_choice = input("Sync fresh data from Treasury API to Supabase? (y/n): ").strip().lower()
    if sync_choice == 'y':
        sync_data_to_supabase()
    
    # Select model
    model_type = select_model()
    
    # Select currencies
    currencies = select_currencies()
    
    print(f"\n📋 Configuration:")
    print(f"   Model: {model_type.upper()}")
    print(f"   Currencies: {', '.join(currencies)}")
    
    confirm = input("\nProceed with training? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Training cancelled.")
        return 0
    
    # Train
    if model_type == "compare":
        results = compare_models(currencies)
    else:
        results = train_model(model_type, currencies)
    
    # Summary
    print_summary(results)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

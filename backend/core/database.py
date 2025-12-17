"""
Supabase Database Client Module

Provides centralized database access for the Currency Intelligence Platform.
Tables:
  - fx_rates: Historical exchange rate data
  - forecasts: Model predictions with confidence intervals
  - alerts: System alerts and notifications
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Lazy import to handle missing package gracefully
_supabase_client = None


def get_supabase_client():
    """
    Get or create Supabase client singleton.
    Returns None if Supabase is not configured.
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except ImportError:
        logger.error("supabase package not installed. Run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def is_supabase_configured() -> bool:
    """Check if Supabase is available and configured."""
    return get_supabase_client() is not None


# =============================================================================
# FX Rates Table Operations
# =============================================================================

def save_fx_rate(currency_pair: str, rate: float, record_date: date, source: str = "treasury") -> bool:
    """
    Save or update an FX rate record.
    Uses upsert to handle duplicates based on (currency_pair, record_date).
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table("fx_rates").upsert({
            "currency_pair": currency_pair,
            "rate": rate,
            "record_date": record_date.isoformat(),
            "source": source
        }, on_conflict="currency_pair,record_date").execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save FX rate: {e}")
        return False


def save_fx_rates_batch(rates: List[Dict[str, Any]]) -> bool:
    """
    Batch insert/update FX rates.
    Each rate dict should have: currency_pair, rate, record_date, source (optional)
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Format dates as ISO strings
        formatted_rates = []
        for rate in rates:
            formatted_rates.append({
                "currency_pair": rate["currency_pair"],
                "rate": float(rate["rate"]),
                "record_date": rate["record_date"].isoformat() if isinstance(rate["record_date"], date) else rate["record_date"],
                "source": rate.get("source", "treasury")
            })
        
        client.table("fx_rates").upsert(
            formatted_rates,
            on_conflict="currency_pair,record_date"
        ).execute()
        logger.info(f"Saved {len(formatted_rates)} FX rates to Supabase")
        return True
    except Exception as e:
        logger.error(f"Failed to batch save FX rates: {e}")
        return False


def get_fx_rates(currency_pair: str, days: int = 365) -> List[Dict[str, Any]]:
    """
    Get historical FX rates for a currency pair.
    Returns list of dicts with: currency_pair, rate, record_date
    """
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table("fx_rates") \
            .select("currency_pair, rate, record_date") \
            .eq("currency_pair", currency_pair) \
            .order("record_date", desc=True) \
            .limit(days) \
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get FX rates: {e}")
        return []


def get_all_fx_rates(days: int = 365) -> List[Dict[str, Any]]:
    """
    Get historical FX rates for all currency pairs.
    """
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table("fx_rates") \
            .select("currency_pair, rate, record_date") \
            .order("record_date", desc=True) \
            .limit(days * 3) \
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get all FX rates: {e}")
        return []


def get_latest_rates() -> Dict[str, Dict[str, Any]]:
    """
    Get the most recent rate for each currency pair.
    Returns dict keyed by currency_pair.
    """
    client = get_supabase_client()
    if not client:
        return {}
    
    try:
        # Get latest for each currency
        result = {}
        for currency in ["EUR", "GBP", "CAD"]:
            response = client.table("fx_rates") \
                .select("currency_pair, rate, record_date") \
                .eq("currency_pair", currency) \
                .order("record_date", desc=True) \
                .limit(1) \
                .execute()
            if response.data:
                result[currency] = response.data[0]
        return result
    except Exception as e:
        logger.error(f"Failed to get latest rates: {e}")
        return {}


# =============================================================================
# Forecasts Table Operations
# =============================================================================

def save_forecast(
    currency_pair: str,
    forecast_date: date,
    horizon_days: int,
    point_forecast: float,
    lower_bound: float,
    upper_bound: float,
    confidence_score: float,
    model_weights: Optional[Dict[str, float]] = None
) -> bool:
    """Save a forecast record."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table("forecasts").insert({
            "currency_pair": currency_pair,
            "forecast_date": forecast_date.isoformat(),
            "horizon_days": horizon_days,
            "point_forecast": point_forecast,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_score": confidence_score,
            "model_weights": model_weights
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save forecast: {e}")
        return False


def get_latest_forecast(currency_pair: str) -> Optional[Dict[str, Any]]:
    """Get the most recent forecast for a currency pair."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.table("forecasts") \
            .select("*") \
            .eq("currency_pair", currency_pair) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Failed to get forecast: {e}")
        return None


# =============================================================================
# Alerts Table Operations
# =============================================================================

def save_alert(
    title: str,
    message: str,
    severity: str = "info",
    currency_pair: Optional[str] = None
) -> bool:
    """
    Save an alert to the database.
    severity: 'info', 'warning', 'critical'
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table("alerts").insert({
            "title": title,
            "message": message,
            "severity": severity,
            "currency_pair": currency_pair,
            "acknowledged": False
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save alert: {e}")
        return False


def get_unacknowledged_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent unacknowledged alerts."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        response = client.table("alerts") \
            .select("*") \
            .eq("acknowledged", False) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return []


def acknowledge_alert(alert_id: str) -> bool:
    """Mark an alert as acknowledged."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table("alerts") \
            .update({"acknowledged": True}) \
            .eq("id", alert_id) \
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        return False


# =============================================================================
# Health Check
# =============================================================================

def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and return stats.
    Useful for health endpoints.
    """
    client = get_supabase_client()
    
    if not client:
        return {
            "status": "disconnected",
            "configured": False,
            "message": "Supabase not configured"
        }
    
    try:
        # Try a simple query
        response = client.table("fx_rates").select("count", count="exact").limit(1).execute()
        rate_count = response.count if hasattr(response, 'count') else 0
        
        return {
            "status": "connected",
            "configured": True,
            "fx_rates_count": rate_count,
            "message": "Database connection healthy"
        }
    except Exception as e:
        return {
            "status": "error",
            "configured": True,
            "message": str(e)
        }

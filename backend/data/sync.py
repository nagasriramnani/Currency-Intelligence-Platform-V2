"""
Data Sync Module

Handles synchronization between Treasury API data and Supabase persistence.
"""

import logging
from typing import Optional
from datetime import date, datetime
import pandas as pd

from data.treasury_client import TreasuryAPIClient
from core.database import (
    save_fx_rates_batch,
    get_fx_rates,
    is_supabase_configured,
    check_database_health
)

logger = logging.getLogger(__name__)


def sync_treasury_to_supabase(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """
    Fetch data from Treasury API and persist to Supabase.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 2020-01-01)
        end_date: End date in YYYY-MM-DD format (default: today)
        
    Returns:
        Dictionary with sync status and counts
    """
    if not is_supabase_configured():
        logger.warning("Supabase not configured - skipping sync")
        return {
            "status": "skipped",
            "message": "Supabase not configured",
            "records_synced": 0
        }
    
    try:
        # Fetch from Treasury API
        logger.info("Fetching data from Treasury API...")
        client = TreasuryAPIClient()
        df = client.fetch_exchange_rates(
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            logger.warning("No data returned from Treasury API")
            return {
                "status": "no_data",
                "message": "No data from Treasury API",
                "records_synced": 0
            }
        
        # Prepare records for Supabase
        records = []
        for _, row in df.iterrows():
            records.append({
                "currency_pair": row["currency"],
                "rate": float(row["exchange_rate"]),
                "record_date": row["record_date"].date() if isinstance(row["record_date"], datetime) else row["record_date"],
                "source": "treasury"
            })
        
        # Save to Supabase
        logger.info(f"Saving {len(records)} records to Supabase...")
        success = save_fx_rates_batch(records)
        
        if success:
            logger.info(f"Successfully synced {len(records)} records")
            return {
                "status": "success",
                "message": f"Synced {len(records)} records",
                "records_synced": len(records),
                "date_range": {
                    "start": df["record_date"].min().isoformat(),
                    "end": df["record_date"].max().isoformat()
                },
                "currencies": df["currency"].unique().tolist()
            }
        else:
            logger.error("Failed to save records to Supabase")
            return {
                "status": "error",
                "message": "Failed to save to Supabase",
                "records_synced": 0
            }
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "records_synced": 0
        }


def get_fx_data_with_fallback(currency: str, days: int = 365) -> pd.DataFrame:
    """
    Get FX data, preferring Supabase but falling back to API if needed.
    
    Args:
        currency: Currency code (EUR, GBP, CAD)
        days: Number of days of history
        
    Returns:
        DataFrame with FX rate data
    """
    # Try Supabase first
    if is_supabase_configured():
        data = get_fx_rates(currency, days)
        if data:
            df = pd.DataFrame(data)
            df["record_date"] = pd.to_datetime(df["record_date"])
            df["exchange_rate"] = df["rate"]
            df["currency"] = df["currency_pair"]
            logger.info(f"Loaded {len(df)} records from Supabase for {currency}")
            return df
    
    # Fall back to API
    logger.info(f"Fetching {currency} from Treasury API (fallback)")
    client = TreasuryAPIClient()
    df = client.fetch_exchange_rates()
    
    if not df.empty:
        df = df[df["currency"] == currency]
    
    return df


if __name__ == "__main__":
    # Test sync
    import sys
    sys.path.insert(0, "..")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Testing Treasury -> Supabase sync...")
    result = sync_treasury_to_supabase(start_date="2024-01-01")
    print(f"Result: {result}")

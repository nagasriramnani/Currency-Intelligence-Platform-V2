"""
U.S. Treasury Fiscal Data API Client
Handles FX rate data ingestion with pagination, filtering, and error handling.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TreasuryAPIClient:
    """Client for fetching exchange rate data from US Treasury Fiscal Data API."""
    
    BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
    ENDPOINT = "/v1/accounting/od/rates_of_exchange"
    MIN_START_DATE = datetime(2020, 1, 1)
    
    # Map Treasury currency descriptions to standard pair names
    CURRENCY_MAP = {
        "Euro Zone-Euro": "EUR",
        "United Kingdom-Pound": "GBP",
        "Canada-Dollar": "CAD"
    }
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 30,
    ):
        """
        Initialize the Treasury API client.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay in seconds between retries
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = requests.Session()
        # Track external data availability (FMP integration currently disabled).
        self.fmp_available: bool = False
        
    def _make_request(
        self, 
        url: str, 
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            url: Full URL to request
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requesting Treasury API (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if response.status_code == 429:  # Rate limit
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                elif response.status_code >= 500:  # Server error
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                raise
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout after {self.timeout}s")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
        raise Exception(f"Failed after {self.max_retries} attempts")

    def fetch_exchange_rates(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        currencies: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch exchange rate data from Treasury API with full pagination.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 2000-01-01 for maximum historical data)
            end_date: End date in YYYY-MM-DD format (default: today)
            currencies: List of currency descriptions to filter (default: EUR, GBP, CAD)
            
        Returns:
            DataFrame with columns: record_date, currency, exchange_rate, country_currency_desc
        """
        # Set defaults - fetch maximum historical data
        if start_date is None:
            start_dt = self.MIN_START_DATE
        else:
            start_dt = max(datetime.fromisoformat(str(start_date)), self.MIN_START_DATE)
        if end_date is None:
            end_dt = datetime.now()
        else:
            end_dt = datetime.fromisoformat(str(end_date))
        if start_dt > end_dt:
            start_dt = self.MIN_START_DATE

        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")

        if currencies is None:
            currencies = list(self.CURRENCY_MAP.keys())
            
        logger.info(f"Fetching Treasury FX data from {start_date} to {end_date}")
        logger.info(f"Currencies: {currencies}")
        
        # Build base URL
        url = self.BASE_URL + self.ENDPOINT
        
        # Build currency filter
        currency_filter = ",".join(f"({c})" for c in currencies)
        
        # Initial request parameters
        params = {
            "fields": "country_currency_desc,exchange_rate,record_date",
            "filter": f"country_currency_desc:in:({','.join(currencies)}),record_date:gte:{start_date},record_date:lte:{end_date}",
            "page[size]": 1000,  # Max page size
            "page[number]": 1,
            "sort": "-record_date"  # Most recent first
        }
        
        all_records = []
        page_number = 1
        
        while True:
            params["page[number]"] = page_number
            
            try:
                response_data = self._make_request(url, params)
                
                # Extract data
                data = response_data.get("data", [])
                if not data:
                    logger.info("No more data to fetch")
                    break
                    
                all_records.extend(data)
                logger.info(f"Fetched page {page_number}: {len(data)} records")
                
                # Check if there are more pages
                meta = response_data.get("meta", {})
                total_pages = meta.get("total-pages", 1)
                
                if page_number >= total_pages:
                    logger.info(f"Reached last page ({total_pages})")
                    break
                    
                # Check for next link
                links = response_data.get("links", {})
                if not links.get("next"):
                    logger.info("No next link found")
                    break
                    
                page_number += 1
                
                # Small delay to be respectful of API limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching page {page_number}: {e}")
                # Return what we have so far
                if all_records:
                    logger.warning("Returning partial data due to error")
                    break
                else:
                    raise
        
        logger.info(f"Total records fetched: {len(all_records)}")
        
        # Convert to DataFrame
        if not all_records:
            logger.warning("No data returned from API")
            return pd.DataFrame(columns=["record_date", "currency", "exchange_rate", "country_currency_desc"])
        
        df = pd.DataFrame(all_records)
        
        # Transform and clean
        df = self._transform_data(df)
        
        return df

    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw API response into clean analytical format.
        
        Args:
            df: Raw DataFrame from API
            
        Returns:
            Cleaned DataFrame with proper types and standardized currency names
        """
        if df.empty:
            return df
        
        # Parse date
        df["record_date"] = pd.to_datetime(df["record_date"])
        
        # Convert exchange rate to float
        df["exchange_rate"] = pd.to_numeric(df["exchange_rate"], errors="coerce")
        
        # Map to standard currency codes
        df["currency"] = df["country_currency_desc"].map(self.CURRENCY_MAP)
        
        # Create pair notation (e.g., USD/EUR)
        df["pair"] = "USD/" + df["currency"]
        
        # Remove any rows with missing data
        df = df.dropna(subset=["record_date", "exchange_rate", "currency"])
        
        # Sort by date (most recent first)
        df = df.sort_values("record_date", ascending=False).reset_index(drop=True)
        
        logger.info(f"Transformed {len(df)} records across {df['currency'].nunique()} currencies")
        logger.info(f"Date range: {df['record_date'].min()} to {df['record_date'].max()}")
        
        return df
    
    def get_latest_rates(self) -> pd.DataFrame:
        """
        Fetch only the most recent exchange rates.
        
        Returns:
            DataFrame with latest rates for each currency
        """
        # Get last 30 days to ensure we have recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = self.fetch_exchange_rates(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if df.empty:
            return df
        
        # Get most recent rate for each currency
        latest = df.groupby("currency").first().reset_index()
        
        return latest


if __name__ == "__main__":
    # Test the client
    client = TreasuryAPIClient()
    df = client.fetch_exchange_rates(start_date="2023-01-01")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"\nCurrencies: {df['currency'].unique()}")
    print(f"\nDate range: {df['record_date'].min()} to {df['record_date'].max()}")


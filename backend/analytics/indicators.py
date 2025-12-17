"""
Statistical indicators for currency analysis.
Computes MoM, QoQ, YoY changes and direction classification.
"""

import logging
from typing import Literal, Optional, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DirectionType = Literal["Rising", "Falling", "Flat"]


def calculate_pct_change(
    series: pd.Series,
    periods_back: int = 1,
    method: str = "pct"
) -> pd.Series:
    """
    Calculate percentage change over a specified number of periods.
    
    Args:
        series: Time series data (should be sorted chronologically)
        periods_back: Number of periods to look back
        method: 'pct' for percentage change, 'diff' for absolute difference
        
    Returns:
        Series of percentage changes
    """
    if method == "pct":
        return series.pct_change(periods=periods_back) * 100
    else:
        return series.diff(periods=periods_back)


def calculate_mom_change(df: pd.DataFrame, rate_col: str = "exchange_rate") -> pd.DataFrame:
    """
    Calculate Month-over-Month percentage change.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        
    Returns:
        DataFrame with mom_change column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Approximate monthly frequency (assuming roughly monthly data)
    df["mom_change"] = calculate_pct_change(df[rate_col], periods_back=1)
    
    return df


def calculate_qoq_change(df: pd.DataFrame, rate_col: str = "exchange_rate") -> pd.DataFrame:
    """
    Calculate Quarter-over-Quarter percentage change.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        
    Returns:
        DataFrame with qoq_change column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Approximate quarterly frequency (3 months)
    df["qoq_change"] = calculate_pct_change(df[rate_col], periods_back=3)
    
    return df


def calculate_yoy_change(df: pd.DataFrame, rate_col: str = "exchange_rate") -> pd.DataFrame:
    """
    Calculate Year-over-Year percentage change.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        
    Returns:
        DataFrame with yoy_change column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Calculate YoY by finding rate from approximately 1 year ago
    df["year"] = df["record_date"].dt.year
    df["month"] = df["record_date"].dt.month
    
    # Self-join to find same month last year
    df_last_year = df.copy()
    df_last_year["year"] = df_last_year["year"] + 1
    df_last_year = df_last_year[["year", "month", rate_col]].rename(
        columns={rate_col: "rate_last_year"}
    )
    
    df = df.merge(df_last_year, on=["year", "month"], how="left")
    
    # Calculate YoY percentage change
    df["yoy_change"] = (
        (df[rate_col] - df["rate_last_year"]) / df["rate_last_year"] * 100
    )
    
    # Drop temporary columns
    df = df.drop(columns=["year", "month", "rate_last_year"], errors="ignore")
    
    return df


def classify_direction(
    recent_change: float,
    threshold: float = 0.5
) -> DirectionType:
    """
    Classify direction of currency movement.
    
    Args:
        recent_change: Recent percentage change (e.g., MoM or QoQ)
        threshold: Threshold for classifying as "Flat" (default: 0.5%)
        
    Returns:
        Direction classification: "Rising", "Falling", or "Flat"
    """
    if pd.isna(recent_change):
        return "Flat"
    
    if abs(recent_change) < threshold:
        return "Flat"
    elif recent_change > 0:
        return "Rising"
    else:
        return "Falling"


def get_direction_from_series(
    series: pd.Series,
    window: int = 3,
    threshold: float = 0.5
) -> DirectionType:
    """
    Determine overall direction from a series of values.
    
    Args:
        series: Time series of exchange rates (most recent first)
        window: Number of recent periods to consider
        threshold: Threshold for flat classification
        
    Returns:
        Overall direction classification
    """
    if len(series) < 2:
        return "Flat"
    
    # Take most recent values
    recent = series.head(window)
    
    # Calculate average change
    pct_changes = recent.pct_change() * 100
    avg_change = pct_changes.mean()
    
    return classify_direction(avg_change, threshold)


def calculate_all_indicators(
    df: pd.DataFrame,
    rate_col: str = "exchange_rate"
) -> pd.DataFrame:
    """
    Calculate all key indicators (MoM, QoQ, YoY) for a currency DataFrame.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        
    Returns:
        DataFrame with all indicator columns added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Calculate all changes
    df = calculate_mom_change(df, rate_col)
    df = calculate_qoq_change(df, rate_col)
    df = calculate_yoy_change(df, rate_col)
    
    # Calculate direction based on recent MoM changes
    df["direction"] = df.apply(
        lambda row: classify_direction(row.get("mom_change", 0), threshold=0.5),
        axis=1
    )
    
    logger.info(f"Calculated all indicators for {len(df)} records")
    
    return df


def get_latest_metrics(df: pd.DataFrame, currency: str) -> dict:
    """
    Extract latest key metrics for a specific currency.
    
    Args:
        df: DataFrame with all indicators calculated (filtered by date range)
        currency: Currency code (e.g., "EUR", "GBP", "CAD")
        
    Returns:
        Dictionary with latest metrics including period_change
        (change from first to last data point in the filtered range)
    """
    currency_df = df[df["currency"] == currency].copy()
    
    if currency_df.empty:
        return {
            "currency": currency,
            "latest_rate": None,
            "latest_date": None,
            "mom_change": None,
            "qoq_change": None,
            "yoy_change": None,
            "direction": "Flat"
        }
    
    # Sort by date (oldest first for period calculation)
    currency_df = currency_df.sort_values("record_date", ascending=True)
    
    # Get first and last data points in the filtered range
    first_point = currency_df.iloc[0]
    last_point = currency_df.iloc[-1]
    
    first_rate = float(first_point["exchange_rate"])
    last_rate = float(last_point["exchange_rate"])
    
    # Calculate period change (change over the entire filtered range)
    if first_rate != 0:
        period_change = ((last_rate - first_rate) / first_rate) * 100
    else:
        period_change = None
    
    return {
        "currency": currency,
        "pair": f"USD/{currency}",
        "latest_rate": last_rate,
        "latest_date": last_point["record_date"].strftime("%Y-%m-%d"),
        "mom_change": float(last_point.get("mom_change", 0)) if pd.notna(last_point.get("mom_change")) else None,
        "qoq_change": float(last_point.get("qoq_change", 0)) if pd.notna(last_point.get("qoq_change")) else None,
        # Use period_change instead of the pre-calculated yoy_change
        # This shows change over the selected date range (1Y, 3Y, 5Y, etc.)
        "yoy_change": period_change,
        "direction": get_direction_from_series(currency_df["exchange_rate"].iloc[::-1], window=3),
        # Include the starting rate so UI can display "from X.XXXX"
        "period_start_rate": first_rate
    }


def get_yoy_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a year-on-year comparison table for all currencies.
    
    Args:
        df: DataFrame with all indicators
        
    Returns:
        DataFrame with YoY comparison metrics
    """
    currencies = df["currency"].unique()
    comparison = []
    
    for currency in currencies:
        currency_df = df[df["currency"] == currency].sort_values("record_date", ascending=False)
        
        if len(currency_df) < 2:
            continue
        
        latest = currency_df.iloc[0]
        
        # Find rate from approximately 1 year ago
        one_year_ago = latest["record_date"] - pd.DateOffset(years=1)
        historical = currency_df[currency_df["record_date"] <= one_year_ago]
        
        if not historical.empty:
            year_ago_rate = historical.iloc[0]["exchange_rate"]
            yoy_pct = ((latest["exchange_rate"] - year_ago_rate) / year_ago_rate) * 100
        else:
            year_ago_rate = None
            yoy_pct = None
        
        comparison.append({
            "currency": currency,
            "pair": f"USD/{currency}",
            "current_rate": latest["exchange_rate"],
            "year_ago_rate": year_ago_rate,
            "yoy_change_pct": yoy_pct,
            "current_date": latest["record_date"]
        })
    
    return pd.DataFrame(comparison)


if __name__ == "__main__":
    # Test with synthetic data
    dates = pd.date_range("2020-01-01", "2024-01-01", freq="MS")
    test_df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": np.random.uniform(0.85, 0.95, len(dates)),
        "currency": "EUR"
    })
    
    result = calculate_all_indicators(test_df)
    print(result.tail())
    print("\nLatest metrics:")
    print(get_latest_metrics(result, "EUR"))



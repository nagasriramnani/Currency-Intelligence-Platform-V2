"""
Volatility and risk metrics for currency analysis.
Computes returns, rolling volatility, and stability scores.
"""

import logging
from typing import Optional, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_returns(
    df: pd.DataFrame,
    rate_col: str = "exchange_rate",
    method: str = "simple"
) -> pd.DataFrame:
    """
    Calculate period-over-period returns.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        method: 'simple' for arithmetic returns, 'log' for logarithmic returns
        
    Returns:
        DataFrame with returns column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    if method == "log":
        df["returns"] = np.log(df[rate_col] / df[rate_col].shift(1)) * 100
    else:
        df["returns"] = df[rate_col].pct_change() * 100
    
    return df


def calculate_rolling_volatility(
    df: pd.DataFrame,
    window: int = 12,
    returns_col: str = "returns"
) -> pd.DataFrame:
    """
    Calculate rolling volatility (standard deviation of returns).
    
    Args:
        df: DataFrame with returns
        window: Rolling window size (number of periods)
        returns_col: Name of the returns column
        
    Returns:
        DataFrame with rolling_volatility column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Calculate rolling standard deviation
    df["rolling_volatility"] = df[returns_col].rolling(window=window, min_periods=2).std()
    
    # Calculate annualized volatility (assuming monthly data)
    df["annualized_volatility"] = df["rolling_volatility"] * np.sqrt(12)
    
    return df


def calculate_stability_score(
    df: pd.DataFrame,
    window: int = 12,
    returns_col: str = "returns",
    volatility_col: str = "rolling_volatility"
) -> pd.DataFrame:
    """
    Calculate stability score (analogous to Sharpe ratio).
    Higher score indicates better return per unit of risk.
    
    Args:
        df: DataFrame with returns and volatility
        window: Window for calculating mean returns
        returns_col: Name of the returns column
        volatility_col: Name of the volatility column
        
    Returns:
        DataFrame with stability_score column added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Calculate rolling mean return
    df["mean_return"] = df[returns_col].rolling(window=window, min_periods=2).mean()
    
    # Stability score = mean return / volatility
    # Add small epsilon to avoid division by zero
    epsilon = 1e-6
    df["stability_score"] = df["mean_return"] / (df[volatility_col] + epsilon)
    
    # Replace infinite values
    df["stability_score"] = df["stability_score"].replace([np.inf, -np.inf], np.nan)
    
    return df


def identify_volatility_regimes(
    df: pd.DataFrame,
    volatility_col: str = "rolling_volatility",
    threshold_std: float = 1.0
) -> pd.DataFrame:
    """
    Identify high volatility regimes.
    
    Args:
        df: DataFrame with volatility calculated
        volatility_col: Name of the volatility column
        threshold_std: Number of standard deviations above mean to classify as high volatility
        
    Returns:
        DataFrame with volatility_regime column added
    """
    df = df.copy()
    
    # Calculate mean and std of volatility
    mean_vol = df[volatility_col].mean()
    std_vol = df[volatility_col].std()
    
    # Define thresholds
    high_vol_threshold = mean_vol + (threshold_std * std_vol)
    low_vol_threshold = mean_vol - (threshold_std * std_vol)
    
    # Classify regimes
    df["volatility_regime"] = "Normal"
    df.loc[df[volatility_col] > high_vol_threshold, "volatility_regime"] = "High"
    df.loc[df[volatility_col] < low_vol_threshold, "volatility_regime"] = "Low"
    
    logger.info(f"Volatility regimes identified: High threshold = {high_vol_threshold:.4f}")
    
    return df


def calculate_all_volatility_metrics(
    df: pd.DataFrame,
    rate_col: str = "exchange_rate",
    window: int = 12
) -> pd.DataFrame:
    """
    Calculate all volatility and risk metrics.
    
    Args:
        df: DataFrame with record_date and exchange_rate
        rate_col: Name of the rate column
        window: Rolling window size
        
    Returns:
        DataFrame with all volatility metrics added
    """
    df = df.copy()
    df = df.sort_values("record_date")
    
    # Calculate returns
    df = calculate_returns(df, rate_col)
    
    # Calculate rolling volatility
    df = calculate_rolling_volatility(df, window)
    
    # Calculate stability score
    df = calculate_stability_score(df, window)
    
    # Identify volatility regimes
    df = identify_volatility_regimes(df)
    
    logger.info(f"Calculated all volatility metrics for {len(df)} records")
    
    return df


def get_volatility_summary(df: pd.DataFrame, currency: str) -> dict:
    """
    Get volatility summary statistics for a specific currency.
    
    Args:
        df: DataFrame with volatility metrics
        currency: Currency code
        
    Returns:
        Dictionary with volatility summary
    """
    currency_df = df[df["currency"] == currency].copy()
    
    if currency_df.empty or "rolling_volatility" not in currency_df.columns:
        return {
            "currency": currency,
            "current_volatility": None,
            "mean_volatility": None,
            "max_volatility": None,
            "min_volatility": None,
            "volatility_regime": "Unknown"
        }
    
    # Remove NaN values
    vol_data = currency_df.dropna(subset=["rolling_volatility"])
    
    if vol_data.empty:
        return {
            "currency": currency,
            "current_volatility": None,
            "mean_volatility": None,
            "max_volatility": None,
            "min_volatility": None,
            "volatility_regime": "Unknown"
        }
    
    # Sort by date
    vol_data = vol_data.sort_values("record_date", ascending=False)
    latest = vol_data.iloc[0]
    
    return {
        "currency": currency,
        "pair": f"USD/{currency}",
        "current_volatility": float(latest["rolling_volatility"]),
        "annualized_volatility": float(latest.get("annualized_volatility", 0)),
        "mean_volatility": float(vol_data["rolling_volatility"].mean()),
        "max_volatility": float(vol_data["rolling_volatility"].max()),
        "min_volatility": float(vol_data["rolling_volatility"].min()),
        "volatility_regime": latest.get("volatility_regime", "Unknown"),
        "stability_score": float(latest.get("stability_score", 0)) if pd.notna(latest.get("stability_score")) else None
    }


def compare_volatility_across_currencies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create comparative volatility table across all currencies.
    
    Args:
        df: DataFrame with volatility metrics for all currencies
        
    Returns:
        DataFrame with comparative volatility metrics
    """
    currencies = df["currency"].unique()
    comparison = []
    
    for currency in currencies:
        summary = get_volatility_summary(df, currency)
        comparison.append(summary)
    
    return pd.DataFrame(comparison).sort_values("current_volatility", ascending=False)


def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    Calculate Value at Risk (VaR) at specified confidence level.
    
    Args:
        returns: Series of returns
        confidence: Confidence level (default: 95%)
        
    Returns:
        VaR value
    """
    returns_clean = returns.dropna()
    
    if returns_clean.empty:
        return 0.0
    
    percentile = (1 - confidence) * 100
    var = np.percentile(returns_clean, percentile)
    
    return float(var)


if __name__ == "__main__":
    # Test with synthetic data
    dates = pd.date_range("2020-01-01", "2024-01-01", freq="MS")
    test_df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": np.random.uniform(0.85, 0.95, len(dates)) + np.random.normal(0, 0.02, len(dates)),
        "currency": "EUR"
    })
    
    result = calculate_all_volatility_metrics(test_df)
    print(result[["record_date", "exchange_rate", "returns", "rolling_volatility", "volatility_regime"]].tail(10))
    print("\nVolatility summary:")
    print(get_volatility_summary(result, "EUR"))



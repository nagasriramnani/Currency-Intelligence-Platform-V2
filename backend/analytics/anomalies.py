"""
Anomaly detection for currency movements.
Identifies unusual rate movements using z-score and isolation forest methods.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sklearn with proper error handling
try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
    logger.info("scikit-learn successfully loaded - Isolation Forest available")
except Exception as e:
    logger.info(f"Using z-score anomaly detection (sklearn unavailable: {type(e).__name__})")
    SKLEARN_AVAILABLE = False
    IsolationForest = None


class AnomalyDetector:
    """Detects anomalies in currency exchange rate movements."""
    
    def __init__(
        self,
        method: str = "zscore",
        zscore_threshold: float = 3.0,
        contamination: float = 0.05
    ):
        """
        Initialize anomaly detector.
        
        Args:
            method: Detection method ('zscore' or 'isolation_forest')
            zscore_threshold: Threshold for z-score method (default: 3.0)
            contamination: Expected proportion of anomalies for isolation forest
        """
        self.method = method
        self.zscore_threshold = zscore_threshold
        self.contamination = contamination
        
        if method == "isolation_forest" and not SKLEARN_AVAILABLE:
            logger.warning("Isolation Forest not available, using z-score instead")
            self.method = "zscore"
    
    def detect_anomalies_zscore(
        self,
        series: pd.Series,
        threshold: Optional[float] = None
    ) -> pd.Series:
        """
        Detect anomalies using z-score method.
        
        Args:
            series: Series of values (e.g., returns or residuals)
            threshold: Z-score threshold (default: use instance threshold)
            
        Returns:
            Boolean series indicating anomalies
        """
        if threshold is None:
            threshold = self.zscore_threshold
        
        # Remove NaN values
        series_clean = series.dropna()
        
        if series_clean.empty:
            return pd.Series(False, index=series.index)
        
        # Calculate z-scores
        mean = series_clean.mean()
        std = series_clean.std()
        
        if std == 0:
            return pd.Series(False, index=series.index)
        
        z_scores = (series - mean) / std
        
        # Flag anomalies
        anomalies = np.abs(z_scores) > threshold
        
        return anomalies
    
    def detect_anomalies_isolation_forest(
        self,
        df: pd.DataFrame,
        features: List[str]
    ) -> pd.Series:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            df: DataFrame with features
            features: List of feature column names
            
        Returns:
            Boolean series indicating anomalies
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Isolation Forest not available")
            return pd.Series(False, index=df.index)
        
        # Prepare data
        X = df[features].copy()
        X = X.dropna()
        
        if X.empty or len(X) < 10:
            return pd.Series(False, index=df.index)
        
        # Train isolation forest
        iso_forest = IsolationForest(
            contamination=self.contamination,
            random_state=42
        )
        
        # Predict (-1 for anomalies, 1 for normal)
        predictions = iso_forest.fit_predict(X)
        
        # Create boolean series
        anomalies = pd.Series(False, index=df.index)
        anomalies.loc[X.index] = predictions == -1
        
        return anomalies
    
    def detect_rate_anomalies(
        self,
        df: pd.DataFrame,
        rate_col: str = "exchange_rate",
        use_returns: bool = True
    ) -> pd.DataFrame:
        """
        Detect anomalies in exchange rate movements.
        
        Args:
            df: DataFrame with exchange rates
            rate_col: Name of rate column
            use_returns: Whether to detect on returns (True) or levels (False)
            
        Returns:
            DataFrame with is_anomaly column added
        """
        df = df.copy()
        df = df.sort_values("record_date")
        
        if use_returns:
            # Calculate returns if not present
            if "returns" not in df.columns:
                df["returns"] = df[rate_col].pct_change() * 100
            
            detection_series = df["returns"]
        else:
            detection_series = df[rate_col]
        
        # Detect anomalies based on method
        if self.method == "zscore":
            df["is_anomaly"] = self.detect_anomalies_zscore(detection_series)
        elif self.method == "isolation_forest":
            # Use multiple features if available
            features = []
            if "returns" in df.columns:
                features.append("returns")
            if "rolling_volatility" in df.columns:
                features.append("rolling_volatility")
            if rate_col in df.columns and not use_returns:
                features.append(rate_col)
            
            if features:
                df["is_anomaly"] = self.detect_anomalies_isolation_forest(df, features)
            else:
                df["is_anomaly"] = False
        else:
            df["is_anomaly"] = False
        
        # Count anomalies
        num_anomalies = df["is_anomaly"].sum()
        logger.info(f"Detected {num_anomalies} anomalies using {self.method} method")
        
        return df
    
    def get_anomaly_periods(
        self,
        df: pd.DataFrame,
        currency: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get all anomaly periods with details.
        
        Args:
            df: DataFrame with is_anomaly column
            currency: Optional currency filter
            
        Returns:
            DataFrame of anomalies with dates, rates, and changes
        """
        if currency:
            df = df[df["currency"] == currency].copy()
        
        if "is_anomaly" not in df.columns:
            return pd.DataFrame()
        
        # Filter to anomalies only
        anomalies = df[df["is_anomaly"] == True].copy()
        
        if anomalies.empty:
            return pd.DataFrame()
        
        # Select relevant columns
        columns = ["record_date", "currency", "exchange_rate"]
        if "returns" in anomalies.columns:
            columns.append("returns")
        if "rolling_volatility" in anomalies.columns:
            columns.append("rolling_volatility")
        
        result = anomalies[columns].copy()
        result = result.sort_values("record_date", ascending=False)
        
        return result
    
    def calculate_anomaly_score(
        self,
        value: float,
        mean: float,
        std: float
    ) -> float:
        """
        Calculate anomaly score (z-score).
        
        Args:
            value: Value to score
            mean: Mean of distribution
            std: Standard deviation
            
        Returns:
            Absolute z-score
        """
        if std == 0:
            return 0.0
        
        return abs((value - mean) / std)
    
    def detect_forecast_deviation_anomalies(
        self,
        actual: pd.Series,
        forecast: pd.Series,
        threshold: float = 2.0
    ) -> pd.Series:
        """
        Detect anomalies where actual significantly deviates from forecast.
        
        Args:
            actual: Actual values
            forecast: Forecasted values
            threshold: Z-score threshold for deviation
            
        Returns:
            Boolean series indicating forecast deviation anomalies
        """
        # Calculate residuals
        residuals = actual - forecast
        
        # Detect anomalies in residuals
        anomalies = self.detect_anomalies_zscore(residuals, threshold)
        
        return anomalies
    
    def summarize_anomalies(
        self,
        df: pd.DataFrame
    ) -> Dict:
        """
        Summarize anomaly detection results.
        
        Args:
            df: DataFrame with anomaly detection results
            
        Returns:
            Dictionary with summary statistics
        """
        if "is_anomaly" not in df.columns:
            return {
                "total_records": len(df),
                "anomalies_detected": 0,
                "anomaly_rate": 0.0,
                "currencies_affected": []
            }
        
        total = len(df)
        anomalies = df["is_anomaly"].sum()
        rate = (anomalies / total * 100) if total > 0 else 0.0
        
        # Get currencies with anomalies
        if "currency" in df.columns:
            currencies_affected = df[df["is_anomaly"] == True]["currency"].unique().tolist()
        else:
            currencies_affected = []
        
        return {
            "total_records": int(total),
            "anomalies_detected": int(anomalies),
            "anomaly_rate": float(rate),
            "currencies_affected": currencies_affected,
            "detection_method": self.method
        }


def detect_all_anomalies(
    df: pd.DataFrame,
    method: str = "zscore",
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Convenience function to detect anomalies in a DataFrame.
    
    Args:
        df: DataFrame with exchange rate data
        method: Detection method
        threshold: Threshold for detection
        
    Returns:
        DataFrame with anomalies detected
    """
    detector = AnomalyDetector(method=method, zscore_threshold=threshold)
    return detector.detect_rate_anomalies(df)


if __name__ == "__main__":
    # Test with synthetic data including anomalies
    dates = pd.date_range("2020-01-01", "2024-01-01", freq="MS")
    rates = 0.85 + 0.05 * np.sin(np.arange(len(dates)) * 0.3) + np.random.normal(0, 0.01, len(dates))
    
    # Inject some anomalies
    rates[10] = 1.2  # Spike
    rates[25] = 0.5  # Drop
    
    test_df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": rates,
        "currency": "EUR"
    })
    
    detector = AnomalyDetector(method="zscore", zscore_threshold=2.5)
    result = detector.detect_rate_anomalies(test_df)
    
    print("Anomalies detected:")
    print(detector.get_anomaly_periods(result))
    print("\nSummary:")
    print(detector.summarize_anomalies(result))


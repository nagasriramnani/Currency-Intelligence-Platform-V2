"""
Tests for anomaly detection module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analytics.anomalies import AnomalyDetector, detect_all_anomalies


def test_anomaly_detector_initialization():
    """Test anomaly detector initialization."""
    detector = AnomalyDetector(method='zscore', zscore_threshold=3.0)
    assert detector.method == 'zscore'
    assert detector.zscore_threshold == 3.0


def test_detect_anomalies_zscore():
    """Test z-score anomaly detection."""
    detector = AnomalyDetector(method='zscore', zscore_threshold=2.0)
    
    # Create series with clear outlier
    series = pd.Series([1.0, 1.1, 1.05, 1.08, 1.02, 5.0, 1.04, 1.06])
    anomalies = detector.detect_anomalies_zscore(series, threshold=2.0)
    
    # The value 5.0 should be detected as anomaly
    assert anomalies[5] == True
    assert anomalies.sum() >= 1  # At least one anomaly detected


def test_detect_rate_anomalies():
    """Test anomaly detection on rate data."""
    dates = pd.date_range('2020-01-01', periods=20, freq='MS')
    rates = np.random.uniform(0.85, 0.95, 20)
    rates[10] = 1.5  # Inject anomaly
    
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': rates,
        'currency': 'EUR'
    })
    
    detector = AnomalyDetector(method='zscore', zscore_threshold=2.0)
    result = detector.detect_rate_anomalies(df)
    
    assert 'is_anomaly' in result.columns
    assert result['is_anomaly'].sum() >= 1  # At least one anomaly detected


def test_get_anomaly_periods():
    """Test extraction of anomaly periods."""
    dates = pd.date_range('2020-01-01', periods=20, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.95, 20),
        'currency': 'EUR',
        'is_anomaly': [False] * 20
    })
    df.loc[5, 'is_anomaly'] = True
    df.loc[15, 'is_anomaly'] = True
    
    detector = AnomalyDetector()
    anomalies = detector.get_anomaly_periods(df)
    
    assert len(anomalies) == 2
    assert 'record_date' in anomalies.columns
    assert 'currency' in anomalies.columns


def test_summarize_anomalies():
    """Test anomaly summary statistics."""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.95, 100),
        'currency': 'EUR',
        'is_anomaly': [False] * 95 + [True] * 5
    })
    
    detector = AnomalyDetector()
    summary = detector.summarize_anomalies(df)
    
    assert summary['total_records'] == 100
    assert summary['anomalies_detected'] == 5
    assert summary['anomaly_rate'] == 5.0
    assert 'EUR' in summary['currencies_affected']


def test_no_anomalies_detected():
    """Test case where no anomalies are detected."""
    dates = pd.date_range('2020-01-01', periods=20, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.87, 20),  # Very stable data
        'currency': 'EUR'
    })
    
    detector = AnomalyDetector(method='zscore', zscore_threshold=10.0)  # High threshold
    result = detector.detect_rate_anomalies(df)
    
    # With high threshold, should detect no or few anomalies
    assert result['is_anomaly'].sum() <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



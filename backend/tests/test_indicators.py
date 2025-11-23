"""
Tests for indicators module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analytics.indicators import (
    calculate_pct_change,
    classify_direction,
    get_direction_from_series,
    calculate_all_indicators,
    get_latest_metrics
)


def test_calculate_pct_change():
    """Test percentage change calculation."""
    series = pd.Series([100, 105, 110, 108])
    pct_change = calculate_pct_change(series, periods_back=1)
    
    assert pd.isna(pct_change.iloc[0])  # First value should be NaN
    assert abs(pct_change.iloc[1] - 5.0) < 0.01  # 5% increase
    assert abs(pct_change.iloc[2] - 4.76) < 0.01  # ~4.76% increase
    assert pct_change.iloc[3] < 0  # Negative change


def test_classify_direction():
    """Test direction classification."""
    assert classify_direction(2.5, threshold=0.5) == "Rising"
    assert classify_direction(-2.5, threshold=0.5) == "Falling"
    assert classify_direction(0.3, threshold=0.5) == "Flat"
    assert classify_direction(-0.3, threshold=0.5) == "Flat"


def test_get_direction_from_series():
    """Test direction determination from series."""
    # Rising series
    rising_series = pd.Series([1.0, 1.05, 1.10, 1.15])
    assert get_direction_from_series(rising_series) == "Rising"
    
    # Falling series
    falling_series = pd.Series([1.15, 1.10, 1.05, 1.0])
    assert get_direction_from_series(falling_series) == "Falling"
    
    # Flat series
    flat_series = pd.Series([1.0, 1.001, 1.002, 1.0])
    assert get_direction_from_series(flat_series) == "Flat"


def test_calculate_all_indicators():
    """Test calculation of all indicators."""
    # Create synthetic data
    dates = pd.date_range('2020-01-01', periods=24, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.linspace(0.85, 0.95, 24),
        'currency': 'EUR'
    })
    
    result = calculate_all_indicators(df)
    
    # Check that new columns are added
    assert 'mom_change' in result.columns
    assert 'qoq_change' in result.columns
    assert 'yoy_change' in result.columns
    assert 'direction' in result.columns
    
    # Check that values are computed
    assert result['mom_change'].notna().sum() > 0
    assert result['direction'].iloc[-1] in ['Rising', 'Falling', 'Flat']


def test_get_latest_metrics():
    """Test extraction of latest metrics."""
    dates = pd.date_range('2020-01-01', periods=24, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.linspace(0.85, 0.95, 24),
        'currency': 'EUR'
    })
    
    df = calculate_all_indicators(df)
    metrics = get_latest_metrics(df, 'EUR')
    
    assert metrics['currency'] == 'EUR'
    assert metrics['latest_rate'] is not None
    assert metrics['latest_date'] is not None
    assert 'yoy_change' in metrics


def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['record_date', 'exchange_rate', 'currency'])
    result = calculate_all_indicators(df)
    
    assert result.empty


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



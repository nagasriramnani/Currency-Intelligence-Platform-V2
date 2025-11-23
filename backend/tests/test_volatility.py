"""
Tests for volatility module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analytics.volatility import (
    calculate_returns,
    calculate_rolling_volatility,
    calculate_all_volatility_metrics,
    get_volatility_summary
)


def test_calculate_returns():
    """Test returns calculation."""
    dates = pd.date_range('2020-01-01', periods=10, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': [1.0, 1.05, 1.03, 1.08, 1.06, 1.10, 1.12, 1.09, 1.15, 1.13],
        'currency': 'EUR'
    })
    
    result = calculate_returns(df)
    
    assert 'returns' in result.columns
    assert pd.isna(result['returns'].iloc[0])  # First return is NaN
    assert result['returns'].iloc[1] > 0  # Second should be positive (1.05/1.0 - 1)
    assert not result['returns'].iloc[1:].isna().all()


def test_calculate_rolling_volatility():
    """Test rolling volatility calculation."""
    dates = pd.date_range('2020-01-01', periods=20, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.95, 20),
        'currency': 'EUR'
    })
    
    df = calculate_returns(df)
    result = calculate_rolling_volatility(df, window=6)
    
    assert 'rolling_volatility' in result.columns
    assert 'annualized_volatility' in result.columns
    
    # Check that volatility is never negative
    vol_values = result['rolling_volatility'].dropna()
    assert (vol_values >= 0).all()


def test_calculate_all_volatility_metrics():
    """Test calculation of all volatility metrics."""
    dates = pd.date_range('2020-01-01', periods=30, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.95, 30),
        'currency': 'EUR'
    })
    
    result = calculate_all_volatility_metrics(df, window=12)
    
    # Check all expected columns exist
    assert 'returns' in result.columns
    assert 'rolling_volatility' in result.columns
    assert 'stability_score' in result.columns
    assert 'volatility_regime' in result.columns
    
    # Check regime classification
    regime_values = result['volatility_regime'].dropna().unique()
    assert all(regime in ['Low', 'Normal', 'High'] for regime in regime_values)


def test_get_volatility_summary():
    """Test volatility summary generation."""
    dates = pd.date_range('2020-01-01', periods=30, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': np.random.uniform(0.85, 0.95, 30),
        'currency': 'EUR'
    })
    
    df = calculate_all_volatility_metrics(df)
    summary = get_volatility_summary(df, 'EUR')
    
    assert summary['currency'] == 'EUR'
    assert 'current_volatility' in summary
    assert 'mean_volatility' in summary
    assert 'volatility_regime' in summary


def test_volatility_with_stable_data():
    """Test volatility calculation with very stable data."""
    dates = pd.date_range('2020-01-01', periods=20, freq='MS')
    df = pd.DataFrame({
        'record_date': dates,
        'exchange_rate': [1.0] * 20,  # Perfectly stable
        'currency': 'EUR'
    })
    
    result = calculate_all_volatility_metrics(df)
    
    # Volatility should be zero or near-zero
    vol_values = result['rolling_volatility'].dropna()
    assert (vol_values < 0.01).all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



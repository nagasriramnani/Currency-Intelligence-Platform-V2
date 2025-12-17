"""
Regime Detection Module

Uses Hidden Markov Models (HMM) to classify market regimes:
- Low Volatility: Stable trends, longer hedging horizons
- High Volatility: Frequent reversals, reduce positions
- Trending: Directional momentum, trend-following
- Mean-Reverting: Oscillating within range
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import hmmlearn
try:
    from hmmlearn.hmm import GaussianHMM
    HMM_AVAILABLE = True
    logger.info("hmmlearn loaded - regime detection available")
except ImportError:
    HMM_AVAILABLE = False
    logger.warning("hmmlearn not installed. Run: pip install hmmlearn")


@dataclass
class MarketRegime:
    """Current market regime classification."""
    regime_name: str
    regime_id: int
    confidence: float  # 0-1 probability
    description: str
    strategy_implication: str
    
    # Regime characteristics
    volatility_level: str  # 'low', 'normal', 'high', 'extreme'
    trend_direction: str  # 'up', 'down', 'sideways'
    
    # Historical context
    days_in_regime: int
    regime_history: List[Tuple[str, int]]  # (regime_name, days) for last N regimes
    
    def to_dict(self) -> Dict:
        return {
            "regime": self.regime_name,
            "regime_id": self.regime_id,
            "confidence": round(self.confidence, 2),
            "description": self.description,
            "strategy": self.strategy_implication,
            "characteristics": {
                "volatility": self.volatility_level,
                "trend": self.trend_direction
            },
            "days_in_current_regime": self.days_in_regime,
            "recent_history": [
                {"regime": r, "days": d} for r, d in self.regime_history[-5:]
            ]
        }


# Regime definitions
REGIME_DEFINITIONS = {
    0: {
        "name": "Low Volatility",
        "description": "Stable markets with low daily fluctuations",
        "strategy": "Extend hedging horizons, consider reducing hedge ratios",
        "volatility": "low",
        "trend": "sideways"
    },
    1: {
        "name": "Trending",
        "description": "Clear directional momentum with moderate volatility",
        "strategy": "Use trend-following signals, dynamic hedging",
        "volatility": "normal",
        "trend": "directional"
    },
    2: {
        "name": "High Volatility",
        "description": "Elevated uncertainty with frequent reversals",
        "strategy": "Increase hedge ratios, shorten horizons, reduce position sizes",
        "volatility": "high",
        "trend": "choppy"
    },
    3: {
        "name": "Crisis",
        "description": "Extreme volatility, potential regime break",
        "strategy": "Maximum hedging, consider full currency coverage",
        "volatility": "extreme",
        "trend": "unstable"
    }
}


class RegimeDetector:
    """
    Detects market regimes using Gaussian Hidden Markov Models.
    
    Features used:
    - Daily returns
    - Rolling volatility (7-day, 30-day)
    - Return momentum
    """
    
    def __init__(
        self,
        n_regimes: int = 4,
        lookback_days: int = 252,
        random_state: int = 42
    ):
        """
        Initialize regime detector.
        
        Args:
            n_regimes: Number of regimes to detect (default 4)
            lookback_days: Days of history to use for fitting
            random_state: Random seed for reproducibility
        """
        self.n_regimes = n_regimes
        self.lookback_days = lookback_days
        self.random_state = random_state
        
        self._model = None
        self._is_fitted = False
        self._regime_mapping = {}  # Maps HMM states to regime definitions
    
    def fit(self, df: pd.DataFrame, currency: str) -> "RegimeDetector":
        """
        Fit HMM to historical data.
        
        Args:
            df: DataFrame with 'record_date' and 'exchange_rate'
            currency: Currency code
            
        Returns:
            Self for method chaining
        """
        if not HMM_AVAILABLE:
            logger.warning("HMM not available, using fallback")
            return self
        
        # Prepare features
        df = df.copy()
        df = df.sort_values("record_date").tail(self.lookback_days)
        
        if len(df) < 60:
            logger.warning(f"Insufficient data for regime detection ({len(df)} samples)")
            return self
        
        # Calculate features
        df["returns"] = df["exchange_rate"].pct_change()
        df["vol_7"] = df["returns"].rolling(7).std()
        df["vol_30"] = df["returns"].rolling(30).std()
        df["momentum"] = df["exchange_rate"].pct_change(periods=20)
        
        df = df.dropna()
        
        if len(df) < 30:
            logger.warning("Too many NaN values after feature calculation")
            return self
        
        # Prepare feature matrix
        features = df[["returns", "vol_7", "vol_30", "momentum"]].values
        
        # Standardize features
        self._feature_mean = features.mean(axis=0)
        self._feature_std = features.std(axis=0) + 1e-8
        features_scaled = (features - self._feature_mean) / self._feature_std
        
        try:
            # Fit Gaussian HMM
            self._model = GaussianHMM(
                n_components=self.n_regimes,
                covariance_type="full",
                n_iter=100,
                random_state=self.random_state
            )
            self._model.fit(features_scaled)
            self._is_fitted = True
            
            # Map HMM states to regime definitions based on volatility
            self._map_regimes(df, features_scaled)
            
            logger.info(f"Regime detector fitted for {currency}")
            
        except Exception as e:
            logger.error(f"HMM fitting failed: {e}")
        
        return self
    
    def _map_regimes(self, df: pd.DataFrame, features: np.ndarray) -> None:
        """Map HMM hidden states to semantic regime names."""
        # Get state sequence
        states = self._model.predict(features)
        
        # Calculate mean volatility for each state
        state_vols = {}
        for state in range(self.n_regimes):
            mask = states == state
            if mask.sum() > 0:
                state_vols[state] = df.iloc[mask]["vol_30"].mean()
            else:
                state_vols[state] = 0
        
        # Sort states by volatility
        sorted_states = sorted(state_vols.items(), key=lambda x: x[1])
        
        # Map to regime definitions (0=low vol, 3=crisis)
        for i, (state, _) in enumerate(sorted_states):
            regime_id = min(i, len(REGIME_DEFINITIONS) - 1)
            self._regime_mapping[state] = regime_id
    
    def detect(self, df: pd.DataFrame, currency: str) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            df: DataFrame with recent data
            currency: Currency code
            
        Returns:
            MarketRegime with classification
        """
        if not self._is_fitted or not HMM_AVAILABLE:
            return self._fallback_detection(df, currency)
        
        # Prepare features for recent data
        df = df.copy()
        df = df.sort_values("record_date").tail(60)
        
        df["returns"] = df["exchange_rate"].pct_change()
        df["vol_7"] = df["returns"].rolling(7).std()
        df["vol_30"] = df["returns"].rolling(30).std()
        df["momentum"] = df["exchange_rate"].pct_change(periods=20)
        
        df = df.dropna()
        
        if len(df) < 5:
            return self._fallback_detection(df, currency)
        
        # Scale features
        features = df[["returns", "vol_7", "vol_30", "momentum"]].values
        features_scaled = (features - self._feature_mean) / self._feature_std
        
        try:
            # Get state probabilities for latest observation
            log_probs = self._model.score_samples(features_scaled)
            states = self._model.predict(features_scaled)
            
            current_state = states[-1]
            regime_id = self._regime_mapping.get(current_state, 0)
            regime_def = REGIME_DEFINITIONS[regime_id]
            
            # Get state probability
            posteriors = self._model.predict_proba(features_scaled)
            confidence = posteriors[-1, current_state]
            
            # Calculate days in current regime
            days_in_regime = 1
            for i in range(len(states) - 2, -1, -1):
                if self._regime_mapping.get(states[i], 0) == regime_id:
                    days_in_regime += 1
                else:
                    break
            
            # Build regime history
            regime_history = []
            current_run = 1
            current_regime = self._regime_mapping.get(states[0], 0)
            
            for i in range(1, len(states)):
                mapped = self._regime_mapping.get(states[i], 0)
                if mapped == current_regime:
                    current_run += 1
                else:
                    regime_history.append((REGIME_DEFINITIONS[current_regime]["name"], current_run))
                    current_regime = mapped
                    current_run = 1
            regime_history.append((REGIME_DEFINITIONS[current_regime]["name"], current_run))
            
            # Determine trend
            if len(df) >= 20:
                recent_return = df["exchange_rate"].iloc[-1] / df["exchange_rate"].iloc[-20] - 1
                if recent_return > 0.02:
                    trend = "up"
                elif recent_return < -0.02:
                    trend = "down"
                else:
                    trend = "sideways"
            else:
                trend = regime_def["trend"]
            
            return MarketRegime(
                regime_name=regime_def["name"],
                regime_id=regime_id,
                confidence=float(confidence),
                description=regime_def["description"],
                strategy_implication=regime_def["strategy"],
                volatility_level=regime_def["volatility"],
                trend_direction=trend,
                days_in_regime=days_in_regime,
                regime_history=regime_history
            )
            
        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            return self._fallback_detection(df, currency)
    
    def _fallback_detection(self, df: pd.DataFrame, currency: str) -> MarketRegime:
        """Simple volatility-based fallback when HMM unavailable."""
        df = df.copy()
        df = df.sort_values("record_date").tail(60)
        
        if len(df) < 10:
            return MarketRegime(
                regime_name="Unknown",
                regime_id=-1,
                confidence=0.0,
                description="Insufficient data",
                strategy_implication="Unable to determine",
                volatility_level="unknown",
                trend_direction="unknown",
                days_in_regime=0,
                regime_history=[]
            )
        
        # Calculate simple volatility
        returns = df["exchange_rate"].pct_change().dropna()
        vol = returns.std() * np.sqrt(252) * 100  # Annualized %
        
        # Classify based on volatility
        if vol < 5:
            regime_id = 0
        elif vol < 10:
            regime_id = 1
        elif vol < 20:
            regime_id = 2
        else:
            regime_id = 3
        
        regime_def = REGIME_DEFINITIONS[regime_id]
        
        # Trend
        recent_return = df["exchange_rate"].iloc[-1] / df["exchange_rate"].iloc[0] - 1
        if recent_return > 0.02:
            trend = "up"
        elif recent_return < -0.02:
            trend = "down"
        else:
            trend = "sideways"
        
        return MarketRegime(
            regime_name=regime_def["name"],
            regime_id=regime_id,
            confidence=0.5,  # Lower confidence for fallback
            description=regime_def["description"],
            strategy_implication=regime_def["strategy"],
            volatility_level=regime_def["volatility"],
            trend_direction=trend,
            days_in_regime=len(df),
            regime_history=[(regime_def["name"], len(df))]
        )
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted


def is_available() -> bool:
    """Check if HMM is available."""
    return HMM_AVAILABLE


if __name__ == "__main__":
    # Test regime detector
    np.random.seed(42)
    
    # Generate synthetic data with regime changes
    dates = pd.date_range("2023-01-01", "2024-01-01", freq="D")
    
    # Low vol period, then high vol
    rates = np.concatenate([
        0.85 + np.cumsum(np.random.normal(0, 0.002, len(dates) // 2)),
        0.85 + np.cumsum(np.random.normal(0, 0.01, len(dates) - len(dates) // 2))
    ])
    
    df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": rates
    })
    
    detector = RegimeDetector(n_regimes=4)
    detector.fit(df, "EUR")
    
    regime = detector.detect(df, "EUR")
    print(f"Current regime: {regime.regime_name}")
    print(f"Confidence: {regime.confidence:.1%}")
    print(f"Strategy: {regime.strategy_implication}")

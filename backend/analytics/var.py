"""
Value-at-Risk (VaR) Calculator

Implements parametric, historical, and Monte Carlo VaR methods
for currency portfolio risk assessment.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class StressScenario:
    """Defines a historical stress scenario for testing."""
    name: str
    description: str
    eur_shock: float  # % change
    gbp_shock: float
    cad_shock: float
    
    def get_shocks(self) -> Dict[str, float]:
        return {
            "EUR": self.eur_shock,
            "GBP": self.gbp_shock,
            "CAD": self.cad_shock
        }


# Pre-defined historical stress scenarios
STRESS_SCENARIOS = [
    StressScenario(
        name="2008 GFC",
        description="Global Financial Crisis peak volatility (Sep-Nov 2008)",
        eur_shock=-8.5,
        gbp_shock=-15.2,
        cad_shock=-18.7
    ),
    StressScenario(
        name="Brexit Vote",
        description="June 2016 Brexit referendum shock",
        eur_shock=-3.2,
        gbp_shock=-11.8,
        cad_shock=-2.1
    ),
    StressScenario(
        name="COVID Crash",
        description="March 2020 pandemic market selloff",
        eur_shock=-4.5,
        gbp_shock=-6.8,
        cad_shock=-9.2
    ),
    StressScenario(
        name="2022 Energy Crisis",
        description="European energy crisis and USD strength",
        eur_shock=-12.3,
        gbp_shock=-10.5,
        cad_shock=-5.8
    ),
    StressScenario(
        name="Fed Rate Shock",
        description="Rapid Fed rate hike scenario (+150bps)",
        eur_shock=-5.0,
        gbp_shock=-4.5,
        cad_shock=-3.0
    )
]


@dataclass
class VaRResult:
    """Result from VaR calculation."""
    currency: str
    confidence: float
    horizon_days: int
    
    # VaR metrics (as positive percentages - potential loss)
    var_parametric: float
    var_historical: float
    var_monte_carlo: Optional[float]
    
    # Conditional VaR (Expected Shortfall)
    cvar: float
    
    # Component details
    volatility: float
    mean_return: float
    
    # Stress test results
    stress_results: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "currency": self.currency,
            "confidence": self.confidence,
            "horizon_days": self.horizon_days,
            "var": {
                "parametric": round(self.var_parametric, 4),
                "historical": round(self.var_historical, 4),
                "monte_carlo": round(self.var_monte_carlo, 4) if self.var_monte_carlo else None
            },
            "cvar": round(self.cvar, 4),
            "volatility": round(self.volatility, 4),
            "stress_tests": {k: round(v, 2) for k, v in self.stress_results.items()}
        }


@dataclass 
class PortfolioVaR:
    """Portfolio-level VaR combining multiple currencies."""
    portfolio_var: float
    portfolio_cvar: float
    confidence: float
    horizon_days: int
    currency_vars: Dict[str, VaRResult]
    correlation_matrix: Dict[str, Dict[str, float]]
    diversification_benefit: float  # Risk reduction from diversification
    worst_case_loss: float  # If all correlations = 1
    stress_results: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict:
        return {
            "portfolio_var": round(self.portfolio_var, 4),
            "portfolio_cvar": round(self.portfolio_cvar, 4),
            "confidence": self.confidence,
            "diversification_benefit": round(self.diversification_benefit, 4),
            "worst_case_loss": round(self.worst_case_loss, 4),
            "by_currency": {k: v.to_dict() for k, v in self.currency_vars.items()},
            "stress_tests": self.stress_results
        }


class VaRCalculator:
    """
    Value-at-Risk calculator for currency portfolios.
    
    Supports:
    - Parametric VaR (assumes normal distribution)
    - Historical VaR (from actual return distribution)
    - Monte Carlo VaR (simulated scenarios)
    - Conditional VaR (Expected Shortfall)
    - Stress testing
    """
    
    def __init__(
        self,
        confidence: float = 0.95,
        horizon_days: int = 1,
        mc_simulations: int = 10000
    ):
        """
        Initialize VaR calculator.
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95%)
            horizon_days: Time horizon in days
            mc_simulations: Number of Monte Carlo simulations
        """
        self.confidence = confidence
        self.horizon_days = horizon_days
        self.mc_simulations = mc_simulations
    
    def calculate_currency_var(
        self,
        returns: pd.Series,
        currency: str
    ) -> VaRResult:
        """
        Calculate VaR for a single currency.
        
        Args:
            returns: Series of daily returns (as decimals, not %)
            currency: Currency code
            
        Returns:
            VaRResult with all VaR metrics
        """
        returns = returns.dropna()
        
        if len(returns) < 30:
            logger.warning(f"Insufficient data for {currency} VaR ({len(returns)} points)")
            return VaRResult(
                currency=currency,
                confidence=self.confidence,
                horizon_days=self.horizon_days,
                var_parametric=0.0,
                var_historical=0.0,
                var_monte_carlo=None,
                cvar=0.0,
                volatility=0.0,
                mean_return=0.0
            )
        
        # Calculate basic statistics
        mean_return = returns.mean()
        volatility = returns.std()
        
        # Scale for horizon
        horizon_vol = volatility * np.sqrt(self.horizon_days)
        horizon_mean = mean_return * self.horizon_days
        
        # 1. Parametric VaR (normal distribution)
        z_score = stats.norm.ppf(1 - self.confidence)
        var_parametric = -(horizon_mean + z_score * horizon_vol)
        
        # 2. Historical VaR
        var_historical = -np.percentile(returns, (1 - self.confidence) * 100)
        if self.horizon_days > 1:
            var_historical = var_historical * np.sqrt(self.horizon_days)
        
        # 3. Monte Carlo VaR
        try:
            simulated_returns = np.random.normal(
                horizon_mean,
                horizon_vol,
                self.mc_simulations
            )
            var_monte_carlo = -np.percentile(simulated_returns, (1 - self.confidence) * 100)
        except Exception:
            var_monte_carlo = None
        
        # 4. Conditional VaR (Expected Shortfall)
        # Average loss beyond VaR threshold
        tail_returns = returns[returns < -var_historical / np.sqrt(self.horizon_days)]
        if len(tail_returns) > 0:
            cvar = -tail_returns.mean() * np.sqrt(self.horizon_days)
        else:
            cvar = var_historical * 1.2  # Fallback estimate
        
        # 5. Stress tests
        stress_results = {}
        current_rate = 1.0  # Normalized
        for scenario in STRESS_SCENARIOS:
            shocks = scenario.get_shocks()
            if currency in shocks:
                stress_results[scenario.name] = shocks[currency]
        
        return VaRResult(
            currency=currency,
            confidence=self.confidence,
            horizon_days=self.horizon_days,
            var_parametric=var_parametric * 100,  # Convert to %
            var_historical=var_historical * 100,
            var_monte_carlo=var_monte_carlo * 100 if var_monte_carlo else None,
            cvar=cvar * 100,
            volatility=volatility * 100 * np.sqrt(252),  # Annualized
            mean_return=mean_return * 100 * 252,  # Annualized
            stress_results=stress_results
        )
    
    def calculate_portfolio_var(
        self,
        returns_df: pd.DataFrame,
        weights: Dict[str, float]
    ) -> PortfolioVaR:
        """
        Calculate portfolio VaR accounting for correlations.
        
        Args:
            returns_df: DataFrame with currency returns
            weights: Portfolio weights by currency
            
        Returns:
            PortfolioVaR with portfolio and component risks
        """
        # Calculate individual VaRs
        currency_vars = {}
        for currency in weights:
            if currency in returns_df.columns:
                currency_vars[currency] = self.calculate_currency_var(
                    returns_df[currency],
                    currency
                )
        
        # Calculate correlation matrix
        corr_matrix = returns_df[list(weights.keys())].corr()
        correlation_dict = corr_matrix.to_dict()
        
        # Calculate covariance matrix
        cov_matrix = returns_df[list(weights.keys())].cov()
        
        # Portfolio variance using matrix multiplication
        weight_array = np.array([weights.get(c, 0) for c in cov_matrix.columns])
        portfolio_variance = np.dot(weight_array, np.dot(cov_matrix, weight_array))
        portfolio_vol = np.sqrt(portfolio_variance) * np.sqrt(self.horizon_days)
        
        # Portfolio VaR
        z_score = stats.norm.ppf(1 - self.confidence)
        portfolio_var = -z_score * portfolio_vol * 100
        
        # Portfolio CVaR (approximate)
        portfolio_cvar = portfolio_var * 1.2
        
        # Worst case (perfect correlation)
        individual_vars = [
            currency_vars[c].var_parametric * weights.get(c, 0) / 100
            for c in currency_vars
        ]
        worst_case = sum(individual_vars) * 100
        
        # Diversification benefit
        diversification_benefit = (worst_case - portfolio_var) / worst_case if worst_case > 0 else 0
        
        # Portfolio stress tests
        stress_results = {}
        for scenario in STRESS_SCENARIOS:
            shocks = scenario.get_shocks()
            portfolio_shock = sum(
                weights.get(c, 0) * shocks.get(c, 0)
                for c in weights
            )
            stress_results[scenario.name] = {
                "portfolio_impact": portfolio_shock,
                "by_currency": {c: shocks.get(c, 0) for c in weights if c in shocks}
            }
        
        return PortfolioVaR(
            portfolio_var=portfolio_var,
            portfolio_cvar=portfolio_cvar,
            confidence=self.confidence,
            horizon_days=self.horizon_days,
            currency_vars=currency_vars,
            correlation_matrix=correlation_dict,
            diversification_benefit=diversification_benefit,
            worst_case_loss=worst_case,
            stress_results=stress_results
        )


def calculate_returns(df: pd.DataFrame, currency: str) -> pd.Series:
    """
    Calculate daily returns from exchange rate data.
    
    Args:
        df: DataFrame with 'exchange_rate' and 'record_date'
        currency: Currency code
        
    Returns:
        Series of daily returns
    """
    df = df.copy()
    df = df.sort_values("record_date")
    df["return"] = df["exchange_rate"].pct_change()
    return df["return"].dropna()


if __name__ == "__main__":
    # Test VaR calculator
    np.random.seed(42)
    
    # Generate sample returns
    n_days = 500
    returns = pd.DataFrame({
        "EUR": np.random.normal(0.0001, 0.008, n_days),
        "GBP": np.random.normal(0.0002, 0.010, n_days),
        "CAD": np.random.normal(0.0000, 0.007, n_days)
    })
    
    # Single currency VaR
    var_calc = VaRCalculator(confidence=0.95, horizon_days=1)
    eur_var = var_calc.calculate_currency_var(returns["EUR"], "EUR")
    print(f"EUR VaR (95%, 1-day): {eur_var.var_parametric:.2f}%")
    print(f"EUR CVaR: {eur_var.cvar:.2f}%")
    
    # Portfolio VaR
    weights = {"EUR": 0.5, "GBP": 0.3, "CAD": 0.2}
    portfolio_var = var_calc.calculate_portfolio_var(returns, weights)
    print(f"\nPortfolio VaR: {portfolio_var.portfolio_var:.2f}%")
    print(f"Diversification benefit: {portfolio_var.diversification_benefit:.1%}")

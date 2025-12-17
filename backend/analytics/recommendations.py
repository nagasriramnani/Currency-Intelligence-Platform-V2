"""
Hedging Recommendations Engine

Generates actionable hedging recommendations based on VaR,
volatility, correlations, and model forecasts.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HedgingRecommendation:
    """A single hedging recommendation."""
    currency: str
    action: str  # 'hedge', 'reduce', 'hold', 'increase'
    urgency: str  # 'immediate', 'soon', 'monitor'
    rationale: str
    suggested_coverage: float  # % of exposure to hedge
    instruments: List[str]  # Suggested instruments
    confidence: float  # 0-1 confidence in recommendation
    
    def to_dict(self) -> Dict:
        return {
            "currency": self.currency,
            "action": self.action,
            "urgency": self.urgency,
            "rationale": self.rationale,
            "suggested_coverage": round(self.suggested_coverage, 2),
            "instruments": self.instruments,
            "confidence": round(self.confidence, 2)
        }


@dataclass
class PortfolioRecommendations:
    """Complete set of recommendations for a portfolio."""
    overall_risk_level: str  # 'low', 'moderate', 'high', 'critical'
    overall_recommendation: str
    currency_recommendations: List[HedgingRecommendation]
    cross_currency_opportunities: List[str]
    estimated_risk_reduction: float  # % reduction if recommendations followed
    
    def to_dict(self) -> Dict:
        return {
            "overall_risk_level": self.overall_risk_level,
            "overall_recommendation": self.overall_recommendation,
            "currency_recommendations": [r.to_dict() for r in self.currency_recommendations],
            "cross_currency_opportunities": self.cross_currency_opportunities,
            "estimated_risk_reduction": round(self.estimated_risk_reduction, 2)
        }


class HedgingRecommendationEngine:
    """
    Generates hedging recommendations based on multiple risk factors.
    
    Considers:
    - Current volatility vs historical
    - VaR levels
    - Cross-currency correlations
    - Model forecast direction
    - Market regime
    """
    
    # Thresholds for recommendations (adjusted for FX markets)
    VOL_HIGH_THRESHOLD = 25.0  # Annualized vol above this is "high"
    VOL_VERY_HIGH_THRESHOLD = 40.0  # Very high volatility
    VAR_HIGH_THRESHOLD = 5.0  # 5% daily VaR (more realistic for FX)
    CORRELATION_HEDGE_THRESHOLD = 0.7  # Above this, can hedge one instead of both
    
    def __init__(self):
        pass
    
    def generate_recommendations(
        self,
        var_results: Dict[str, "VaRResult"],
        volatility_metrics: Dict[str, Dict],
        correlations: Dict[str, Dict[str, float]],
        forecast_directions: Optional[Dict[str, str]] = None,
        current_hedges: Optional[Dict[str, float]] = None
    ) -> PortfolioRecommendations:
        """
        Generate hedging recommendations.
        
        Args:
            var_results: VaR results by currency
            volatility_metrics: Volatility metrics by currency
            correlations: Correlation matrix
            forecast_directions: Model forecast directions ('up', 'down', 'flat')
            current_hedges: Current hedge ratios by currency (0-1)
            
        Returns:
            PortfolioRecommendations
        """
        if current_hedges is None:
            current_hedges = {}
        if forecast_directions is None:
            forecast_directions = {}
        
        recommendations = []
        cross_opportunities = []
        
        # Analyze each currency
        for currency, var_result in var_results.items():
            vol_metrics = volatility_metrics.get(currency, {})
            current_hedge = current_hedges.get(currency, 0.0)
            forecast_dir = forecast_directions.get(currency, "unknown")
            
            rec = self._analyze_currency(
                currency,
                var_result,
                vol_metrics,
                forecast_dir,
                current_hedge
            )
            recommendations.append(rec)
        
        # Check for cross-currency opportunities
        cross_opportunities = self._find_cross_currency_opportunities(
            var_results,
            correlations
        )
        
        # Overall assessment
        overall_risk = self._assess_overall_risk(var_results, volatility_metrics)
        overall_rec = self._generate_overall_recommendation(recommendations, overall_risk)
        
        # Estimate risk reduction
        risk_reduction = self._estimate_risk_reduction(recommendations, var_results)
        
        return PortfolioRecommendations(
            overall_risk_level=overall_risk,
            overall_recommendation=overall_rec,
            currency_recommendations=recommendations,
            cross_currency_opportunities=cross_opportunities,
            estimated_risk_reduction=risk_reduction
        )
    
    def _analyze_currency(
        self,
        currency: str,
        var_result: "VaRResult",
        vol_metrics: Dict,
        forecast_dir: str,
        current_hedge: float
    ) -> HedgingRecommendation:
        """Analyze a single currency and generate recommendation."""
        
        # Extract metrics
        var_level = var_result.var_parametric
        volatility = var_result.volatility
        cvar = var_result.cvar
        
        # Determine action based on multiple factors
        action = "hold"
        urgency = "monitor"
        coverage = 0.0
        instruments = []
        confidence = 0.5
        rationales = []
        
        # Check volatility
        if volatility > self.VOL_VERY_HIGH_THRESHOLD:
            action = "hedge"
            urgency = "immediate"
            coverage = 0.75
            rationales.append(f"Volatility at {volatility:.1f}% (very high)")
            confidence = 0.85
        elif volatility > self.VOL_HIGH_THRESHOLD:
            action = "hedge"
            urgency = "soon"
            coverage = 0.50
            rationales.append(f"Volatility at {volatility:.1f}% (elevated)")
            confidence = 0.70
        
        # Check VaR
        if var_level > self.VAR_HIGH_THRESHOLD:
            if action != "hedge":
                action = "hedge"
                coverage = 0.50
            else:
                coverage = min(coverage + 0.25, 1.0)
            urgency = "immediate" if var_level > 3.0 else urgency
            rationales.append(f"VaR at {var_level:.2f}% exceeds threshold")
            confidence = max(confidence, 0.75)
        
        # Consider forecast direction
        if forecast_dir == "down" and action != "hedge":
            action = "hedge"
            coverage = max(coverage, 0.40)
            rationales.append("Model forecasts currency weakness")
            confidence = min(confidence + 0.1, 1.0)
        elif forecast_dir == "up":
            if action == "hedge":
                coverage = coverage * 0.7  # Reduce hedge if expecting strength
                rationales.append("Model forecasts currency strength - reduced coverage")
        
        # Adjust for current hedge
        if current_hedge >= coverage:
            action = "hold"
            rationales.append(f"Current hedge ({current_hedge:.0%}) adequate")
        elif current_hedge > 0:
            coverage = coverage - current_hedge
            rationales.append(f"Incremental hedge needed (currently {current_hedge:.0%})")
        
        # Suggest instruments
        if action == "hedge":
            if urgency == "immediate":
                instruments = ["FX Forwards (1-3M)", "Currency Options (puts)"]
            else:
                instruments = ["FX Forwards (3-6M)", "Cross-currency swaps"]
        
        # Build rationale
        if not rationales:
            rationales.append("Risk levels within normal range")
        
        return HedgingRecommendation(
            currency=currency,
            action=action,
            urgency=urgency,
            rationale="; ".join(rationales),
            suggested_coverage=coverage,
            instruments=instruments,
            confidence=confidence
        )
    
    def _find_cross_currency_opportunities(
        self,
        var_results: Dict,
        correlations: Dict
    ) -> List[str]:
        """Find natural hedges and correlation-based opportunities."""
        opportunities = []
        
        currencies = list(var_results.keys())
        
        for i, c1 in enumerate(currencies):
            for c2 in currencies[i+1:]:
                corr = correlations.get(c1, {}).get(c2, 0)
                
                if corr > self.CORRELATION_HEDGE_THRESHOLD:
                    opportunities.append(
                        f"{c1}-{c2} correlation is {corr:.2f} - hedge only one for natural offset"
                    )
                elif corr < -0.5:
                    opportunities.append(
                        f"{c1}-{c2} negative correlation ({corr:.2f}) - natural diversification"
                    )
        
        return opportunities
    
    def _assess_overall_risk(
        self,
        var_results: Dict,
        volatility_metrics: Dict
    ) -> str:
        """Assess overall portfolio risk level."""
        max_var = max((v.var_parametric for v in var_results.values()), default=0)
        max_vol = max((v.volatility for v in var_results.values()), default=0)
        
        # Adjusted thresholds for FX markets
        if max_var > 8.0 or max_vol > 45:
            return "critical"
        elif max_var > 5.0 or max_vol > 35:
            return "high"
        elif max_var > 2.0 or max_vol > 20:
            return "moderate"
        else:
            return "low"
    
    def _generate_overall_recommendation(
        self,
        recommendations: List[HedgingRecommendation],
        risk_level: str
    ) -> str:
        """Generate overall portfolio recommendation."""
        hedge_needed = sum(1 for r in recommendations if r.action == "hedge")
        immediate = sum(1 for r in recommendations if r.urgency == "immediate")
        
        if risk_level == "critical":
            return (
                f"CRITICAL: Portfolio at elevated risk. "
                f"{hedge_needed} currencies require hedging, {immediate} immediately. "
                f"Consider defensive positioning across all FX exposures."
            )
        elif risk_level == "high":
            return (
                f"HIGH RISK: Volatility elevated. "
                f"{hedge_needed} currencies flagged for hedging. "
                f"Review all unhedged exposures."
            )
        elif risk_level == "moderate":
            return (
                f"Moderate risk environment. "
                f"Standard hedging policies apply. Monitor flagged currencies."
            )
        else:
            return (
                f"Low risk environment. "
                f"Opportunistic hedging recommended. Consider reducing hedge costs."
            )
    
    def _estimate_risk_reduction(
        self,
        recommendations: List[HedgingRecommendation],
        var_results: Dict
    ) -> float:
        """Estimate portfolio risk reduction if recommendations followed."""
        total_var = sum(v.var_parametric for v in var_results.values())
        
        if total_var == 0:
            return 0
        
        # Estimate reduction from each hedge
        reduction = 0
        for rec in recommendations:
            if rec.action == "hedge" and rec.currency in var_results:
                currency_var = var_results[rec.currency].var_parametric
                # Hedging reduces VaR by coverage ratio
                reduction += currency_var * rec.suggested_coverage * 0.85
        
        return (reduction / total_var) * 100 if total_var > 0 else 0


# Import here to avoid circular imports
from analytics.var import VaRResult

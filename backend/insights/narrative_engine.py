"""
Narrative Intelligence Engine
Converts currency metrics into Board-friendly natural language insights.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NarrativeEngine:
    """Generates natural language insights from currency data and analytics."""
    
    def __init__(self):
        """Initialize the narrative engine."""
        self.insights_cache = {}
    
    def format_percentage(self, value: float, decimals: int = 1) -> str:
        """Format percentage with sign."""
        if value > 0:
            return f"+{value:.{decimals}f}%"
        return f"{value:.{decimals}f}%"
    
    def format_currency_rate(self, rate: float, decimals: int = 4) -> str:
        """Format currency rate."""
        return f"{rate:.{decimals}f}"
    
    def describe_magnitude(self, pct_change: float) -> str:
        """Describe the magnitude of a percentage change."""
        abs_change = abs(pct_change)
        
        if abs_change < 1:
            return "minimal"
        elif abs_change < 3:
            return "modest"
        elif abs_change < 5:
            return "moderate"
        elif abs_change < 10:
            return "significant"
        else:
            return "substantial"
    
    def describe_direction(self, pct_change: float, currency: str) -> str:
        """Describe direction of USD movement."""
        if pct_change > 0:
            return f"strengthened against {currency}"
        elif pct_change < 0:
            return f"weakened against {currency}"
        else:
            return f"remained stable against {currency}"
    
    def describe_volatility_regime(self, current_vol: float, mean_vol: float) -> str:
        """Describe volatility regime."""
        ratio = current_vol / mean_vol if mean_vol > 0 else 1.0
        
        if ratio > 1.5:
            return "elevated volatility"
        elif ratio > 1.2:
            return "above-average volatility"
        elif ratio < 0.7:
            return "low volatility"
        elif ratio < 0.85:
            return "below-average volatility"
        else:
            return "normal volatility"
    
    def generate_yoy_insight(
        self,
        currency: str,
        current_rate: float,
        yoy_change: float,
        latest_date: str
    ) -> str:
        """
        Generate insight about year-on-year performance.
        
        Args:
            currency: Currency code (e.g., EUR, GBP, CAD)
            current_rate: Current exchange rate
            yoy_change: YoY percentage change
            latest_date: Date of latest data
            
        Returns:
            Natural language insight string
        """
        magnitude = self.describe_magnitude(yoy_change)
        direction = self.describe_direction(yoy_change, currency)
        pct_str = self.format_percentage(yoy_change)
        rate_str = self.format_currency_rate(current_rate)
        
        # Determine time reference
        year = datetime.strptime(latest_date, "%Y-%m-%d").year
        
        insight = (
            f"USD has {direction} by {pct_str} over the past year, "
            f"reaching {rate_str} as of {latest_date}. "
            f"This represents a {magnitude} {abs(yoy_change):.1f}% movement."
        )
        
        return insight
    
    def generate_volatility_insight(
        self,
        currency: str,
        current_vol: float,
        mean_vol: float,
        annualized_vol: Optional[float] = None
    ) -> str:
        """
        Generate insight about volatility and risk.
        
        Args:
            currency: Currency code
            current_vol: Current rolling volatility
            mean_vol: Historical mean volatility
            annualized_vol: Annualized volatility
            
        Returns:
            Natural language insight string
        """
        regime = self.describe_volatility_regime(current_vol, mean_vol)
        pct_diff = ((current_vol / mean_vol) - 1) * 100 if mean_vol > 0 else 0
        
        if abs(pct_diff) < 10:
            comparison = "in line with historical averages"
        elif pct_diff > 0:
            comparison = f"{abs(pct_diff):.0f}% higher than the historical average"
        else:
            comparison = f"{abs(pct_diff):.0f}% lower than the historical average"
        
        insight = (
            f"USD/{currency} is currently experiencing {regime}, "
            f"with recent fluctuations {comparison}. "
        )
        
        if annualized_vol:
            insight += f"Annualized volatility stands at {annualized_vol:.2f}%."
        
        return insight
    
    def generate_forecast_insight(
        self,
        currency: str,
        forecast_direction: str,
        confidence: float,
        horizon: str = "next period"
    ) -> str:
        """
        Generate insight about forecast.
        
        Args:
            currency: Currency code
            forecast_direction: Direction of forecast (appreciation/depreciation/stable)
            confidence: Confidence level (0-1)
            horizon: Time horizon description
            
        Returns:
            Natural language insight string
        """
        confidence_pct = confidence * 100
        
        if confidence_pct >= 75:
            confidence_desc = "high confidence"
        elif confidence_pct >= 60:
            confidence_desc = "moderate confidence"
        else:
            confidence_desc = "low confidence"
        
        insight = (
            f"Our forecasting model anticipates {forecast_direction} "
            f"in USD/{currency} over the {horizon}, with {confidence_desc} "
            f"(approximately {confidence_pct:.0f}%)."
        )
        
        return insight
    
    def generate_anomaly_insight(
        self,
        currency: str,
        anomaly_date: str,
        anomaly_type: str,
        magnitude: Optional[float] = None
    ) -> str:
        """
        Generate insight about detected anomaly.
        
        Args:
            currency: Currency code
            anomaly_date: Date of anomaly
            anomaly_type: Type of anomaly
            magnitude: Size of anomaly
            
        Returns:
            Natural language insight string
        """
        insight = (
            f"An unusual movement in USD/{currency} was detected on {anomaly_date}. "
        )
        
        if magnitude:
            insight += (
                f"This {anomaly_type} event showed a {abs(magnitude):.1f}% deviation "
                f"from expected patterns, warranting closer attention."
            )
        else:
            insight += f"This {anomaly_type} event warrants closer attention."
        
        return insight
    
    def generate_comparative_insight(
        self,
        currency_metrics: List[Dict]
    ) -> str:
        """
        Generate comparative insight across multiple currencies.
        
        Args:
            currency_metrics: List of metric dictionaries for each currency
            
        Returns:
            Natural language insight string
        """
        if not currency_metrics:
            return "Insufficient data for comparative analysis."
        
        # Sort by YoY performance
        sorted_metrics = sorted(
            currency_metrics,
            key=lambda x: x.get("yoy_change", 0),
            reverse=True
        )
        
        best = sorted_metrics[0]
        worst = sorted_metrics[-1]
        
        insight = (
            f"Among tracked currencies, USD performed strongest against "
            f"{best['currency']} ({self.format_percentage(best.get('yoy_change', 0))}) "
            f"and weakest against {worst['currency']} "
            f"({self.format_percentage(worst.get('yoy_change', 0))}) on a year-over-year basis."
        )
        
        return insight
    
    def generate_risk_insight(
        self,
        currency: str,
        volatility_rank: int,
        total_currencies: int,
        var_95: Optional[float] = None
    ) -> str:
        """
        Generate risk-focused insight.
        
        Args:
            currency: Currency code
            volatility_rank: Rank by volatility (1 = most volatile)
            total_currencies: Total number of currencies
            var_95: 95% Value at Risk
            
        Returns:
            Natural language insight string
        """
        if volatility_rank == 1:
            rank_desc = "the most volatile"
        elif volatility_rank == total_currencies:
            rank_desc = "the least volatile"
        else:
            rank_desc = f"ranked #{volatility_rank} in volatility"
        
        insight = (
            f"USD/{currency} is {rank_desc} among tracked currency pairs. "
        )
        
        if var_95:
            insight += (
                f"With 95% confidence, daily moves should not exceed "
                f"{abs(var_95):.2f}% under normal market conditions."
            )
        
        return insight
    
    def generate_complete_narrative(
        self,
        currency: str,
        metrics: Dict,
        volatility: Dict,
        forecast: Optional[Dict] = None,
        anomalies: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        Generate complete narrative with multiple insights.
        
        Args:
            currency: Currency code
            metrics: Dictionary of key metrics
            volatility: Dictionary of volatility metrics
            forecast: Optional forecast information
            anomalies: Optional list of anomalies
            
        Returns:
            List of insight strings (2-4 bullets)
        """
        insights = []
        
        # 1. YoY insight
        if metrics.get("yoy_change") is not None:
            insights.append(
                self.generate_yoy_insight(
                    currency,
                    metrics.get("latest_rate", 0),
                    metrics.get("yoy_change", 0),
                    metrics.get("latest_date", "")
                )
            )
        
        # 2. Volatility insight
        if volatility.get("current_volatility") is not None:
            insights.append(
                self.generate_volatility_insight(
                    currency,
                    volatility.get("current_volatility", 0),
                    volatility.get("mean_volatility", 0),
                    volatility.get("annualized_volatility")
                )
            )
        
        # 3. Forecast insight (if available)
        if forecast and forecast.get("direction"):
            insights.append(
                self.generate_forecast_insight(
                    currency,
                    forecast.get("direction", "stable movement"),
                    forecast.get("confidence", 0.5),
                    forecast.get("horizon", "next period")
                )
            )
        
        # 4. Anomaly insight (if recent anomalies)
        if anomalies and len(anomalies) > 0:
            recent = anomalies[0]
            insights.append(
                self.generate_anomaly_insight(
                    currency,
                    recent.get("date", ""),
                    recent.get("type", "unusual"),
                    recent.get("magnitude")
                )
            )
        
        logger.info(f"Generated {len(insights)} insights for {currency}")
        
        return insights[:4]  # Return max 4 insights
    
    def generate_summary_narrative(
        self,
        all_metrics: Dict[str, Dict]
    ) -> str:
        """
        Generate high-level summary narrative across all currencies.
        
        Args:
            all_metrics: Dictionary mapping currency to metrics
            
        Returns:
            Executive summary string
        """
        currencies = list(all_metrics.keys())
        
        if not currencies:
            return "No data available for analysis."
        
        # Calculate average YoY change
        yoy_changes = [
            m.get("yoy_change", 0) 
            for m in all_metrics.values() 
            if m.get("yoy_change") is not None
        ]
        
        avg_yoy = sum(yoy_changes) / len(yoy_changes) if yoy_changes else 0
        
        summary = (
            f"Across {len(currencies)} tracked currency pairs "
            f"({', '.join(currencies)}), "
        )
        
        if avg_yoy > 2:
            summary += (
                f"the USD has shown broad-based strength with an average "
                f"{self.format_percentage(avg_yoy)} appreciation. "
            )
        elif avg_yoy < -2:
            summary += (
                f"the USD has shown broad-based weakness with an average "
                f"{self.format_percentage(avg_yoy)} depreciation. "
            )
        else:
            summary += "the USD has traded in a relatively balanced range. "
        
        summary += (
            "Market conditions warrant continued monitoring across all pairs."
        )
        
        return summary


if __name__ == "__main__":
    # Test narrative generation
    engine = NarrativeEngine()
    
    test_metrics = {
        "currency": "EUR",
        "latest_rate": 0.9234,
        "latest_date": "2024-11-22",
        "yoy_change": 8.2,
        "mom_change": 1.2,
        "qoq_change": 3.5
    }
    
    test_volatility = {
        "current_volatility": 2.5,
        "mean_volatility": 2.0,
        "annualized_volatility": 8.66
    }
    
    insights = engine.generate_complete_narrative(
        "EUR",
        test_metrics,
        test_volatility
    )
    
    print("Generated Insights:")
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}\n")



"""
SHAP Explainability Module

Provides explainability for XGBoost and ensemble forecasts using SHAP values.
Generates human-readable explanations of why a forecast was made.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
    logger.info("SHAP loaded - explainability available")
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("shap not installed. Run: pip install shap")


@dataclass
class FeatureContribution:
    """Individual feature's contribution to the forecast."""
    feature_name: str
    value: float  # The feature value
    contribution: float  # SHAP value (+ = pushes prediction higher)
    description: str  # Human-readable description
    
    def to_dict(self) -> Dict:
        return {
            "feature": self.feature_name,
            "value": round(self.value, 4) if isinstance(self.value, float) else self.value,
            "contribution": round(self.contribution, 6),
            "description": self.description
        }


@dataclass
class ForecastExplanation:
    """Complete explanation for a forecast."""
    currency: str
    forecast_direction: str  # 'up', 'down', 'flat'
    confidence: float
    base_value: float  # Expected value without any features
    predicted_value: float
    
    # Feature contributions (sorted by importance)
    feature_contributions: List[FeatureContribution]
    
    # High-level summary
    primary_driver: str
    summary: str
    
    # Model agreement
    model_agreement: Dict[str, str]  # {'prophet': 'up', 'arima': 'down', ...}
    agreement_score: float  # 0-1, how much models agree
    
    def to_dict(self) -> Dict:
        return {
            "currency": self.currency,
            "direction": self.forecast_direction,
            "confidence": round(self.confidence, 2),
            "base_value": round(self.base_value, 6),
            "predicted_value": round(self.predicted_value, 6),
            "primary_driver": self.primary_driver,
            "summary": self.summary,
            "feature_contributions": [f.to_dict() for f in self.feature_contributions[:10]],
            "model_agreement": self.model_agreement,
            "agreement_score": round(self.agreement_score, 2)
        }


# Feature name mappings for human-readable descriptions
FEATURE_DESCRIPTIONS = {
    "lag_1": "Yesterday's rate",
    "lag_2": "Rate 2 days ago",
    "lag_3": "Rate 3 days ago",
    "lag_7": "Rate 1 week ago",
    "lag_14": "Rate 2 weeks ago",
    "rolling_mean_7": "7-day average",
    "rolling_mean_30": "30-day average",
    "rolling_std_7": "7-day volatility",
    "rolling_std_30": "30-day volatility",
    "momentum_7": "7-day momentum",
    "momentum_30": "30-day momentum",
    "roc_7": "7-day rate of change",
    "roc_30": "30-day rate of change",
    "day_of_week_sin": "Day of week pattern",
    "day_of_week_cos": "Day of week pattern",
    "month_sin": "Monthly seasonality",
    "month_cos": "Monthly seasonality"
}


class ForecastExplainer:
    """
    Explains forecasts using SHAP values for tree-based models.
    
    For Prophet and ARIMA, provides component-based explanations.
    """
    
    def __init__(self):
        self._explainer = None
        self._feature_names = None
    
    def explain_xgboost(
        self,
        model,  # XGBoost model
        features: pd.DataFrame,
        currency: str,
        prediction: float
    ) -> ForecastExplanation:
        """
        Generate SHAP explanation for XGBoost prediction.
        
        Args:
            model: Fitted XGBoost model
            features: Feature DataFrame used for prediction
            currency: Currency code
            prediction: The predicted value
            
        Returns:
            ForecastExplanation with SHAP-based insights
        """
        if not SHAP_AVAILABLE:
            return self._generate_fallback_explanation(currency, prediction)
        
        try:
            # Create TreeExplainer for XGBoost
            explainer = shap.TreeExplainer(model)
            
            # Get SHAP values for the latest prediction
            shap_values = explainer.shap_values(features.iloc[-1:])
            
            # Base value (expected prediction without features)
            base_value = explainer.expected_value
            if isinstance(base_value, np.ndarray):
                base_value = base_value[0]
            
            # Get feature names and values
            feature_names = features.columns.tolist()
            feature_values = features.iloc[-1].values
            shap_vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            
            # Create feature contributions
            contributions = []
            for i, name in enumerate(feature_names):
                desc = FEATURE_DESCRIPTIONS.get(name, name.replace("_", " ").title())
                contribution = shap_vals[i]
                
                # Add direction context to description
                if contribution > 0.001:
                    direction = "pushing rate higher"
                elif contribution < -0.001:
                    direction = "pushing rate lower"
                else:
                    direction = "neutral impact"
                
                contributions.append(FeatureContribution(
                    feature_name=name,
                    value=float(feature_values[i]),
                    contribution=float(contribution),
                    description=f"{desc} ({direction})"
                ))
            
            # Sort by absolute contribution
            contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
            
            # Determine primary driver
            if contributions:
                primary = contributions[0]
                primary_driver = f"{FEATURE_DESCRIPTIONS.get(primary.feature_name, primary.feature_name)}"
            else:
                primary_driver = "No dominant factor identified"
            
            # Determine direction
            if prediction > base_value * 1.001:
                direction = "up"
            elif prediction < base_value * 0.999:
                direction = "down"
            else:
                direction = "flat"
            
            # Generate summary
            top_3 = contributions[:3]
            summary_parts = []
            for c in top_3:
                if abs(c.contribution) > 0.0001:
                    effect = "positive" if c.contribution > 0 else "negative"
                    feat_name = FEATURE_DESCRIPTIONS.get(c.feature_name, c.feature_name)
                    summary_parts.append(f"{feat_name} ({effect})")
            
            summary = f"Forecast driven by: {', '.join(summary_parts)}" if summary_parts else "Balanced forecast with no dominant factors"
            
            return ForecastExplanation(
                currency=currency,
                forecast_direction=direction,
                confidence=0.7,  # Default, would be calculated from model uncertainty
                base_value=float(base_value),
                predicted_value=float(prediction),
                feature_contributions=contributions,
                primary_driver=primary_driver,
                summary=summary,
                model_agreement={"xgboost": direction},
                agreement_score=1.0
            )
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._generate_fallback_explanation(currency, prediction)
    
    def explain_ensemble(
        self,
        currency: str,
        ensemble_prediction: float,
        model_predictions: Dict[str, float],
        model_directions: Dict[str, str],
        xgboost_model=None,
        xgboost_features: Optional[pd.DataFrame] = None
    ) -> ForecastExplanation:
        """
        Generate explanation for ensemble forecast.
        
        Args:
            currency: Currency code
            ensemble_prediction: Combined prediction
            model_predictions: Individual model predictions
            model_directions: Direction each model predicts
            xgboost_model: Optional XGBoost model for SHAP
            xgboost_features: Optional features for SHAP
            
        Returns:
            ForecastExplanation combining all models
        """
        # Calculate model agreement
        directions = list(model_directions.values())
        if directions:
            # Find majority direction
            from collections import Counter
            direction_counts = Counter(directions)
            majority_direction = direction_counts.most_common(1)[0][0]
            agreement_score = sum(1 for d in directions if d == majority_direction) / len(directions)
        else:
            majority_direction = "flat"
            agreement_score = 0.0
        
        # Get SHAP explanation if XGBoost available
        if xgboost_model is not None and xgboost_features is not None and SHAP_AVAILABLE:
            try:
                base_explanation = self.explain_xgboost(
                    xgboost_model,
                    xgboost_features,
                    currency,
                    model_predictions.get("xgboost", ensemble_prediction)
                )
                feature_contributions = base_explanation.feature_contributions
                primary_driver = base_explanation.primary_driver
            except Exception:
                feature_contributions = []
                primary_driver = "Ensemble of multiple models"
        else:
            feature_contributions = []
            primary_driver = "Ensemble of multiple models"
        
        # Generate confidence based on model agreement
        confidence = 0.5 + (agreement_score * 0.4)  # 0.5-0.9 based on agreement
        
        # Build summary
        agreeing = [m for m, d in model_directions.items() if d == majority_direction]
        disagreeing = [m for m, d in model_directions.items() if d != majority_direction]
        
        if len(agreeing) == len(model_directions):
            summary = f"Strong consensus: all models predict {majority_direction}"
        elif len(agreeing) > len(disagreeing):
            summary = f"Majority view: {', '.join(agreeing)} predict {majority_direction}"
        else:
            summary = f"Mixed signals: models disagree on direction"
        
        return ForecastExplanation(
            currency=currency,
            forecast_direction=majority_direction,
            confidence=confidence,
            base_value=0.0,  # Not applicable for ensemble
            predicted_value=ensemble_prediction,
            feature_contributions=feature_contributions,
            primary_driver=primary_driver,
            summary=summary,
            model_agreement=model_directions,
            agreement_score=agreement_score
        )
    
    def _generate_fallback_explanation(
        self,
        currency: str,
        prediction: float
    ) -> ForecastExplanation:
        """Generate basic explanation when SHAP is not available."""
        return ForecastExplanation(
            currency=currency,
            forecast_direction="flat",
            confidence=0.5,
            base_value=prediction,
            predicted_value=prediction,
            feature_contributions=[],
            primary_driver="Statistical patterns",
            summary="Forecast based on historical patterns and trends",
            model_agreement={},
            agreement_score=0.0
        )


def is_available() -> bool:
    """Check if SHAP is available."""
    return SHAP_AVAILABLE

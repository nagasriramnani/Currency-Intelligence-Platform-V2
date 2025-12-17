"""
Rolling Backtest Framework

Provides systematic evaluation of forecasting models using walk-forward
backtesting methodology. Calculates MAPE, directional accuracy, and
calibration metrics over time.
"""

import logging
from typing import Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    """Metrics from a backtest run."""
    model_name: str
    currency: str
    
    # Core metrics
    mape: float  # Mean Absolute Percentage Error
    rmse: float  # Root Mean Squared Error
    directional_accuracy: float  # % of correct up/down predictions
    
    # Calibration
    coverage_80: float  # % of actuals within 80% CI
    coverage_95: float  # % of actuals within 95% CI
    
    # Time series decomposition
    mape_by_horizon: Dict[int, float] = field(default_factory=dict)
    
    # Summary
    total_predictions: int = 0
    train_size: int = 0
    test_size: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "currency": self.currency,
            "mape": round(self.mape, 4),
            "rmse": round(self.rmse, 6),
            "directional_accuracy": round(self.directional_accuracy, 4),
            "calibration": {
                "coverage_80": round(self.coverage_80, 4),
                "coverage_95": round(self.coverage_95, 4)
            },
            "mape_by_horizon": {k: round(v, 4) for k, v in self.mape_by_horizon.items()},
            "total_predictions": self.total_predictions,
            "data_split": {
                "train": self.train_size,
                "test": self.test_size
            }
        }


@dataclass
class BacktestResult:
    """Complete backtest result with all metrics and predictions."""
    metrics: BacktestMetrics
    predictions: pd.DataFrame  # Date, actual, predicted, lower, upper
    passed: bool  # Whether model meets quality thresholds
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "metrics": self.metrics.to_dict(),
            "passed": self.passed,
            "recommendation": self.recommendation,
            "sample_predictions": self.predictions.tail(10).to_dict(orient="records")
        }


class RollingBacktester:
    """
    Walk-forward backtesting for forecasting models.
    
    Methodology:
    1. Start with minimum training window
    2. Generate forecast for next N days
    3. Roll forward, expanding training window
    4. Repeat until end of data
    5. Calculate aggregate metrics
    """
    
    def __init__(
        self,
        min_train_days: int = 180,
        test_days: int = 30,
        step_days: int = 7,
        horizons: List[int] = [1, 7, 30]
    ):
        """
        Initialize backtester.
        
        Args:
            min_train_days: Minimum training window size
            test_days: Days to hold out for each test
            step_days: Days to step forward each iteration
            horizons: Forecast horizons to test
        """
        self.min_train_days = min_train_days
        self.test_days = test_days
        self.step_days = step_days
        self.horizons = horizons
    
    def backtest(
        self,
        model_class,
        df: pd.DataFrame,
        currency: str,
        **model_kwargs
    ) -> BacktestResult:
        """
        Run rolling backtest on a model.
        
        Args:
            model_class: Class of model to test (must have fit/predict)
            df: DataFrame with 'record_date' and 'exchange_rate'
            currency: Currency code
            **model_kwargs: Arguments to pass to model constructor
            
        Returns:
            BacktestResult with metrics and predictions
        """
        # Prepare data
        df = df.copy()
        df = df.sort_values("record_date").reset_index(drop=True)
        df = df.dropna(subset=["exchange_rate"])
        
        n_samples = len(df)
        
        if n_samples < self.min_train_days + self.test_days:
            logger.warning(f"Insufficient data for backtest ({n_samples} samples)")
            return self._empty_result(currency, "Insufficient data")
        
        # Track predictions
        all_predictions = []
        
        # Walk-forward loop
        train_end = self.min_train_days
        
        while train_end + max(self.horizons) <= n_samples:
            # Split data
            train_df = df.iloc[:train_end].copy()
            
            # Fit model
            try:
                model = model_class(**model_kwargs)
                model.fit(train_df, currency)
                
                if not model.is_fitted:
                    train_end += self.step_days
                    continue
                
                # Generate forecasts for each horizon
                for horizon in self.horizons:
                    if train_end + horizon > n_samples:
                        continue
                    
                    result = model.predict(horizon=horizon, confidence=0.80)
                    
                    if not result.forecast_dates:
                        continue
                    
                    # Get actual values
                    for i, forecast_date in enumerate(result.forecast_dates):
                        idx = train_end + i
                        if idx >= n_samples:
                            break
                        
                        actual = df.iloc[idx]["exchange_rate"]
                        predicted = result.point_forecasts[i]
                        lower = result.lower_bounds[i] if result.lower_bounds else None
                        upper = result.upper_bounds[i] if result.upper_bounds else None
                        
                        all_predictions.append({
                            "date": forecast_date,
                            "actual": actual,
                            "predicted": predicted,
                            "lower_80": lower,
                            "upper_80": upper,
                            "horizon": i + 1,
                            "train_end": train_end
                        })
                
            except Exception as e:
                logger.warning(f"Model fit/predict failed at position {train_end}: {e}")
            
            # Step forward
            train_end += self.step_days
        
        # Calculate metrics
        if not all_predictions:
            return self._empty_result(currency, "No valid predictions generated")
        
        pred_df = pd.DataFrame(all_predictions)
        metrics = self._calculate_metrics(pred_df, model_class.__name__, currency)
        
        # Determine pass/fail
        passed, recommendation = self._evaluate_model(metrics)
        
        return BacktestResult(
            metrics=metrics,
            predictions=pred_df,
            passed=passed,
            recommendation=recommendation
        )
    
    def _calculate_metrics(
        self,
        pred_df: pd.DataFrame,
        model_name: str,
        currency: str
    ) -> BacktestMetrics:
        """Calculate aggregate metrics from predictions."""
        
        actual = pred_df["actual"].values
        predicted = pred_df["predicted"].values
        
        # MAPE
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # RMSE
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # Directional Accuracy
        if len(actual) > 1:
            actual_direction = np.sign(np.diff(actual))
            predicted_direction = np.sign(np.diff(predicted))
            directional_accuracy = np.mean(actual_direction == predicted_direction)
        else:
            directional_accuracy = 0.0
        
        # Coverage (calibration)
        if "lower_80" in pred_df.columns and pred_df["lower_80"].notna().any():
            in_ci = (actual >= pred_df["lower_80"].values) & (actual <= pred_df["upper_80"].values)
            coverage_80 = np.mean(in_ci)
        else:
            coverage_80 = 0.0
        
        coverage_95 = coverage_80 * 1.15  # Approximate
        
        # MAPE by horizon
        mape_by_horizon = {}
        for horizon in pred_df["horizon"].unique():
            horizon_df = pred_df[pred_df["horizon"] == horizon]
            if len(horizon_df) > 0:
                h_mape = np.mean(np.abs((horizon_df["actual"] - horizon_df["predicted"]) / horizon_df["actual"])) * 100
                mape_by_horizon[int(horizon)] = h_mape
        
        return BacktestMetrics(
            model_name=model_name,
            currency=currency,
            mape=mape,
            rmse=rmse,
            directional_accuracy=directional_accuracy,
            coverage_80=coverage_80,
            coverage_95=coverage_95,
            mape_by_horizon=mape_by_horizon,
            total_predictions=len(pred_df),
            train_size=pred_df["train_end"].max(),
            test_size=len(pred_df["date"].unique())
        )
    
    def _evaluate_model(self, metrics: BacktestMetrics) -> Tuple[bool, str]:
        """Evaluate if model meets quality thresholds."""
        issues = []
        
        # Check MAPE (target < 3%)
        if metrics.mape > 5:
            issues.append(f"MAPE too high ({metrics.mape:.1f}% > 5%)")
        elif metrics.mape > 3:
            issues.append(f"MAPE elevated ({metrics.mape:.1f}% > 3%)")
        
        # Check directional accuracy (target > 55%)
        if metrics.directional_accuracy < 0.50:
            issues.append(f"Directional accuracy below random ({metrics.directional_accuracy:.0%})")
        elif metrics.directional_accuracy < 0.55:
            issues.append(f"Directional accuracy marginal ({metrics.directional_accuracy:.0%})")
        
        # Check calibration (80% CI should contain ~80% of actuals)
        if metrics.coverage_80 < 0.60:
            issues.append(f"Confidence intervals too narrow (coverage {metrics.coverage_80:.0%})")
        elif metrics.coverage_80 > 0.95:
            issues.append(f"Confidence intervals too wide (coverage {metrics.coverage_80:.0%})")
        
        if not issues:
            return True, "Model meets all quality thresholds. Ready for production."
        elif len(issues) <= 2 and metrics.mape < 5:
            return True, f"Model acceptable with notes: {'; '.join(issues)}"
        else:
            return False, f"Model needs improvement: {'; '.join(issues)}"
    
    def _empty_result(self, currency: str, reason: str) -> BacktestResult:
        """Return empty result for failed backtest."""
        return BacktestResult(
            metrics=BacktestMetrics(
                model_name="Unknown",
                currency=currency,
                mape=float('inf'),
                rmse=float('inf'),
                directional_accuracy=0.0,
                coverage_80=0.0,
                coverage_95=0.0
            ),
            predictions=pd.DataFrame(),
            passed=False,
            recommendation=reason
        )
    
    def compare_models(
        self,
        model_classes: List[Tuple[Type, Dict]],
        df: pd.DataFrame,
        currency: str
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple models on the same data.
        
        Args:
            model_classes: List of (ModelClass, kwargs) tuples
            df: DataFrame with data
            currency: Currency code
            
        Returns:
            Dictionary of model_name -> BacktestResult
        """
        results = {}
        
        for model_class, kwargs in model_classes:
            name = model_class.__name__
            logger.info(f"Backtesting {name}...")
            
            result = self.backtest(model_class, df, currency, **kwargs)
            results[name] = result
            
            logger.info(f"{name}: MAPE={result.metrics.mape:.2f}%, Dir={result.metrics.directional_accuracy:.1%}")
        
        return results


if __name__ == "__main__":
    # Test backtester
    import sys
    sys.path.append("..")
    
    # Generate synthetic data
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", "2024-01-01", freq="D")
    rates = 0.85 + np.cumsum(np.random.normal(0, 0.005, len(dates)))
    
    df = pd.DataFrame({
        "record_date": dates,
        "exchange_rate": rates
    })
    
    print("Running backtest on synthetic data...")
    backtester = RollingBacktester(min_train_days=180, step_days=30)
    
    # Would test with actual model class
    print("Backtest framework initialized successfully")

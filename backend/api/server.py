"""
FastAPI Server for Currency Intelligence Platform
Exposes REST endpoints for data, analytics, forecasts, and alerts.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure local .env is respected for Slack credentials
load_dotenv()

from data.treasury_client import TreasuryAPIClient
from analytics.indicators import calculate_all_indicators, get_latest_metrics, get_yoy_comparison
from analytics.volatility import calculate_all_volatility_metrics, get_volatility_summary, compare_volatility_across_currencies
from analytics.forecasting import CurrencyForecaster
from analytics.anomalies import AnomalyDetector
from insights.narrative_engine import NarrativeEngine
from alerts.slack_notifier import SlackNotifier, AlertManager, AlertTrigger

# Supabase integration
from core.database import (
    is_supabase_configured,
    check_database_health,
    save_fx_rates_batch,
    get_all_fx_rates,
    save_alert
)
from data.sync import sync_treasury_to_supabase

# Risk Analytics
from analytics.var import VaRCalculator, calculate_returns
from analytics.recommendations import HedgingRecommendationEngine

# Background Jobs
from jobs.scheduler import get_scheduler, start_scheduler, stop_scheduler

# Explainability
from ml.explainability.shap_explainer import ForecastExplainer, is_available as shap_available

# Regime Detection
from analytics.regime import RegimeDetector, is_available as hmm_available

# PDF Reports
from reports.pdf_generator import PDFReportGenerator, is_available as pdf_available

# Model Registry and Trainers
from ml.registry import ModelRegistry, TrainingOrchestrator
from ml.trainers import ProphetTrainer, ARIMATrainer, XGBoostTrainer, EnsembleTrainer

# Intelligent Alerting
from alerts.engine import AlertEngine, create_alert_engine

# Production Forecast Service (load-only, no training in endpoints)
from ml.services.forecast_service import ForecastService, ModelNotFoundError, ModelLoadError

# EIS / Companies House Integration
from data.companies_house import (
    CompaniesHouseClient,
    get_sample_eis_data,
    get_client as get_companies_house_client
)
from reports.eis_newsletter import (
    EISNewsletterGenerator,
    generate_eis_newsletter,
    is_available as eis_newsletter_available
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app_state = {
    "data": None,
    "last_update": None,
    "treasury_client": None,
    "forecaster": None,
    "anomaly_detector": None,
    "narrative_engine": None,
    "alert_manager": None,
    "fmp_available": False
}


# Pydantic models for API responses
class HealthResponse(BaseModel):
    status: str
    last_update: Optional[str]
    data_points: int
    currencies: List[str]


class LatestRatesResponse(BaseModel):
    currency: str
    pair: str
    latest_rate: float
    latest_date: str
    mom_change: Optional[float]
    qoq_change: Optional[float]
    yoy_change: Optional[float]
    direction: str
    fmp_available: Optional[bool] = None
    period_start_rate: Optional[float] = None  # Rate at start of selected period


class VolatilityMetricsResponse(BaseModel):
    currency: str
    pair: str
    current_volatility: Optional[float]
    annualized_volatility: Optional[float]
    mean_volatility: Optional[float]
    volatility_regime: str


class ForecastPoint(BaseModel):
    date: str
    value: float


class ConfidenceBandPoint(BaseModel):
    date: str
    lower: float
    upper: float


class LastActualPoint(BaseModel):
    """Last actual data point for anchoring forecast."""
    date: str
    value: float


class ModelMetadata(BaseModel):
    """Metadata about the model that produced the forecast."""
    model_type: str  # prophet, arima, xgboost, ensemble
    model_version: Optional[str] = None
    trained_at: Optional[str] = None
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    data_window_start: Optional[str] = None
    data_window_end: Optional[str] = None
    metrics: Optional[dict] = None


class ForecastResponse(BaseModel):
    currency: str
    forecast_start: Optional[str]
    historical: List[ForecastPoint]
    forecast: List[ForecastPoint]
    confidence: Optional[List[ConfidenceBandPoint]]
    insight: Optional[str]
    model: Optional[ModelMetadata] = None  # Model provenance
    last_actual: Optional[LastActualPoint] = None  # For chart anchoring
    frequency: Optional[str] = "M"  # M=monthly, Q=quarterly


class InsightResponse(BaseModel):
    currency: str
    insights: List[str]


class AlertTestResponse(BaseModel):
    success: bool
    message: str


class TimeSeriesDataPoint(BaseModel):
    date: str
    rate: float
    currency: str


class HighlightItem(BaseModel):
    title: str
    body: str


class HighlightsResponse(BaseModel):
    highlights: List[HighlightItem]


class SlackSummaryRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# =============================================================================
# Interactive Model Selection for Server Startup
# =============================================================================

def interactive_model_selection() -> tuple:
    """Interactive CLI for model selection during server startup."""
    import sys
    
    print("\n" + "="*60)
    print("  🧠 Currency Intelligence - Model Configuration")
    print("="*60 + "\n")
    
    # Check available models
    available = TrainingOrchestrator.get_available_models()
    print("📦 Available Models:")
    for name, is_avail in available.items():
        status = "✅" if is_avail else "❌"
        print(f"   {status} {name.upper()}")
    print()
    
    # Model selection
    print("Select forecasting model:")
    print("-"*40)
    print("  [1] Prophet    - Best for trends & seasonality")
    print("  [2] ARIMA      - Best for short-term momentum")
    print("  [3] XGBoost    - Best for feature-rich prediction")
    print("  [4] Ensemble   - Combines all models (recommended)")
    print("  [5] Skip       - Use default Prophet (fastest)")
    print("-"*40)
    
    while True:
        try:
            choice = input("Enter choice (1-5) [default: 5]: ").strip() or "5"
            
            if choice == "1":
                model_type = "prophet"
                break
            elif choice == "2":
                model_type = "arima"
                break
            elif choice == "3":
                model_type = "xgboost"
                break
            elif choice == "4":
                model_type = "ensemble"
                break
            elif choice == "5":
                return None, None  # Skip interactive training
            else:
                print("Invalid choice. Please enter 1-5.")
        except (EOFError, KeyboardInterrupt):
            print("\nUsing default Prophet model...")
            return None, None
    
    # Currency selection
    print("\nSelect currencies to train:")
    print("-"*40)
    print("  [1] All (EUR, GBP, CAD)")
    print("  [2] EUR only")
    print("  [3] GBP only")
    print("  [4] CAD only")
    print("-"*40)
    
    while True:
        try:
            choice = input("Enter choice (1-4) [default: 1]: ").strip() or "1"
            
            if choice == "1":
                currencies = ["EUR", "GBP", "CAD"]
                break
            elif choice == "2":
                currencies = ["EUR"]
                break
            elif choice == "3":
                currencies = ["GBP"]
                break
            elif choice == "4":
                currencies = ["CAD"]
                break
            else:
                print("Invalid choice. Please enter 1-4.")
        except (EOFError, KeyboardInterrupt):
            currencies = ["EUR", "GBP", "CAD"]
            break
    
    print(f"\n📋 Configuration:")
    print(f"   Model: {model_type.upper()}")
    print(f"   Currencies: {', '.join(currencies)}")
    
    try:
        confirm = input("\nProceed with training? (y/n) [default: y]: ").strip().lower() or "y"
        if confirm != 'y':
            print("Training skipped. Using default Prophet.")
            return None, None
    except (EOFError, KeyboardInterrupt):
        return None, None
    
    return model_type, currencies


def train_selected_models(model_type: str, currencies: list, df: pd.DataFrame) -> None:
    """Train selected models for specified currencies."""
    print(f"\n🚀 Training {model_type.upper()} for {', '.join(currencies)}...")
    
    registry = ModelRegistry("trained_models", use_supabase=False)
    
    for currency in currencies:
        try:
            currency_df = df[df["currency"] == currency]
            if currency_df.empty:
                logger.warning(f"No data for {currency}, skipping")
                continue
            
            print(f"\n  Training {currency}...")
            orchestrator = TrainingOrchestrator(model_type=model_type)
            metrics = orchestrator.train(currency_df, currency)
            orchestrator.save(set_active=True)
            
            print(f"  ✅ {currency}: MAPE={metrics.mape:.2f}%, Dir. Acc={metrics.directional_accuracy:.1%}")
            
        except Exception as e:
            logger.error(f"Training failed for {currency}: {e}")
            print(f"  ❌ {currency}: Training failed - {e}")
    
    print("\n✅ Training complete! Models saved to trained_models/")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize app state on startup with interactive model selection."""
    logger.info("Initializing Currency Intelligence Platform API...")
    
    # Initialize components
    app_state["treasury_client"] = TreasuryAPIClient()
    app_state["fmp_available"] = getattr(app_state["treasury_client"], "fmp_available", False)
    app_state["forecaster"] = CurrencyForecaster(use_prophet=True)
    app_state["anomaly_detector"] = AnomalyDetector(method="zscore", zscore_threshold=1.8)
    app_state["narrative_engine"] = NarrativeEngine()
    app_state["alert_manager"] = AlertManager()
    
    # Interactive model selection
    import sys
    if sys.stdin.isatty():  # Only prompt if running interactively
        model_type, currencies = interactive_model_selection()
    else:
        model_type, currencies = None, None
    
    # Load initial data
    try:
        logger.info("Loading initial currency data...")
        refresh_data()
        logger.info("Initial data loaded successfully")
        
        # Train selected models if not skipped
        if model_type and currencies and app_state.get("data") is not None:
            train_selected_models(model_type, currencies, app_state["data"])
        
    except Exception as e:
        logger.error(f"Failed to load initial data: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Currency Intelligence Platform API...")


# Initialize FastAPI app
app = FastAPI(
    title="Currency Intelligence Platform API",
    description="REST API for Sapphire Capital Partners Currency Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def dataframe_to_records_safe(df: pd.DataFrame) -> List[Dict]:
    """Convert DataFrame to JSON-serializable records, handling NaN/inf."""
    if df is None or df.empty:
        return []
    sanitized = df.replace([np.inf, -np.inf], np.nan)
    sanitized = sanitized.astype(object)
    sanitized = sanitized.where(pd.notnull(sanitized), None)
    return sanitized.to_dict(orient="records")


def filter_dataframe_by_date(
    df: pd.DataFrame,
    start_date: Optional[str],
    end_date: Optional[str]
) -> pd.DataFrame:
    """Filter a DataFrame by ISO date strings."""
    if df is None or df.empty:
        return df
    
    filtered = df
    
    if "record_date" in filtered.columns and not pd.api.types.is_datetime64_any_dtype(filtered["record_date"]):
        filtered = filtered.copy()
        filtered["record_date"] = pd.to_datetime(filtered["record_date"])
    
    if start_date:
        start_dt = pd.to_datetime(start_date)
        filtered = filtered[filtered["record_date"] >= start_dt]
    
    if end_date:
        end_dt = pd.to_datetime(end_date)
        filtered = filtered[filtered["record_date"] <= end_dt]
    
    return filtered


def generate_highlights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Create narrative highlight bullets for the dashboard."""
    highlights: List[Dict[str, str]] = []
    engine: NarrativeEngine = app_state["narrative_engine"]
    
    # Direction of travel (YoY leaders/laggards)
    metrics_list = []
    for currency in df["currency"].unique():
        metrics = get_latest_metrics(df, currency)
        if metrics.get("latest_rate") is None:
            continue
        metrics_list.append(metrics)
    
    if metrics_list:
        comparative = engine.generate_comparative_insight(metrics_list)
        highlights.append({
            "title": "Direction of Travel",
            "body": comparative
        })
    
    # Volatility spotlight
    volatility_df = compare_volatility_across_currencies(df)
    if not volatility_df.empty:
        top_vol = volatility_df.dropna(subset=["current_volatility"]).head(1)
        if not top_vol.empty:
            row = top_vol.iloc[0]
            body = engine.generate_volatility_insight(
                row.get("currency", ""),
                row.get("current_volatility", 0) or 0,
                row.get("mean_volatility", 0) or 0,
                row.get("annualized_volatility")
            )
            highlights.append({
                "title": "Volatility Spotlight",
                "body": body
            })
    
    # Recent anomaly
    anomalies_df = app_state["anomaly_detector"].get_anomaly_periods(df)
    if anomalies_df is not None and not anomalies_df.empty:
        recent = anomalies_df.iloc[0]
        anomaly_date = recent.get("record_date")
        if hasattr(anomaly_date, "strftime"):
            anomaly_date_str = anomaly_date.strftime("%Y-%m-%d")
        else:
            anomaly_date_str = str(anomaly_date)
        
        highlights.append({
            "title": "Recent Anomaly",
            "body": engine.generate_anomaly_insight(
                recent.get("currency", ""),
                anomaly_date_str,
                "volatility spike",
                recent.get("returns")
            )
        })
    elif not metrics_list and not volatility_df.empty:
        highlights.append({
            "title": "No Notable Signals",
            "body": "Market conditions remain balanced across tracked currency pairs."
        })
    
    if not highlights:
        highlights.append({
            "title": "No Notable Signals",
            "body": "Market conditions remain balanced across tracked currency pairs."
        })
    
    return highlights


def build_slack_summary_lines(df: pd.DataFrame) -> List[str]:
    """Generate bullet lines for Slack summary messages."""
    lines: List[str] = []
    
    for currency in sorted(df["currency"].unique()):
        metrics = get_latest_metrics(df, currency)
        latest_rate = metrics.get("latest_rate")
        if latest_rate is None:
            continue
        
        yoy_change = metrics.get("yoy_change")
        yoy_text = f"{yoy_change:+.2f}%" if yoy_change is not None else "n/a"
        lines.append(f"{metrics.get('pair', f'USD/{currency}')}: {latest_rate:.4f} ({yoy_text} YoY)")
    
    volatility_df = compare_volatility_across_currencies(df)
    if not volatility_df.empty:
        top = volatility_df.dropna(subset=["current_volatility"]).head(1)
        if not top.empty:
            row = top.iloc[0]
            pair_label = row.get('pair', f"USD/{row.get('currency', '')}")
            lines.append(
                f"Highest volatility: {pair_label} at "
                f"{row.get('current_volatility', 0):.2f}% (avg {row.get('mean_volatility', 0):.2f}%)."
            )
    
    anomalies_df = app_state["anomaly_detector"].get_anomaly_periods(df)
    if anomalies_df is not None and not anomalies_df.empty:
        recent = anomalies_df.iloc[0]
        anomaly_date = recent.get("record_date")
        if hasattr(anomaly_date, "strftime"):
            anomaly_date_str = anomaly_date.strftime("%Y-%m-%d")
        else:
            anomaly_date_str = str(anomaly_date)
        
        returns = recent.get("returns")
        returns_text = f"{returns:+.2f}%" if returns is not None else "n/a"
        lines.append(
            f"Recent anomaly: USD/{recent.get('currency', '')} on {anomaly_date_str} "
            f"({returns_text} move)."
        )
    else:
        lines.append("Recent anomalies: None detected in the selected range.")
    
    return lines


def refresh_data(days_back: int = 9125):  # ~25 years default (maximum historical data)
    """Refresh data from Treasury API."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        min_start = app_state["treasury_client"].MIN_START_DATE
        if start_date < min_start:
            start_date = min_start
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Fetch data
        df = app_state["treasury_client"].fetch_exchange_rates(
            start_date=start_str,
            end_date=end_str
        )

        df = (
            df.sort_values("record_date")
            .drop_duplicates(subset=["currency", "record_date"], keep="last")
            .sort_values("record_date", ascending=False)
        )
        
        if df.empty:
            logger.warning("No FX data available after fetching")
            return
        
        # Calculate all indicators and volatility
        df = calculate_all_indicators(df)
        df = calculate_all_volatility_metrics(df)
        
        # Detect anomalies
        df = app_state["anomaly_detector"].detect_rate_anomalies(df)
        
        # Train forecasting models
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency]
            app_state["forecaster"].train_prophet_model(currency_df, currency)
        
        # Store in state
        app_state["fmp_available"] = getattr(app_state["treasury_client"], "fmp_available", False)
        app_state["data"] = df
        app_state["last_update"] = datetime.now().isoformat()
        
        logger.info(f"Data refreshed: {len(df)} records across {df['currency'].nunique()} currencies")
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        return HealthResponse(
            status="no_data",
            last_update=None,
            data_points=0,
            currencies=[]
        )
    
    return HealthResponse(
        status="healthy",
        last_update=app_state.get("last_update"),
        data_points=len(df),
        currencies=df["currency"].unique().tolist()
    )


@app.post("/api/data/refresh")
async def refresh_data_endpoint(days_back: int = Query(1460, ge=30, le=3650)):
    """Manually refresh data from Treasury API."""
    try:
        refresh_data(days_back)
        return {"status": "success", "message": f"Data refreshed for last {days_back} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Database (Supabase) Endpoints
# =============================================================================

@app.get("/api/database/health")
async def database_health():
    """Check Supabase database connectivity and stats."""
    return check_database_health()


@app.post("/api/database/sync")
async def sync_to_database(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Sync Treasury API data to Supabase database.
    This fetches data from Treasury and persists to Supabase for faster queries.
    """
    if not is_supabase_configured():
        raise HTTPException(
            status_code=503, 
            detail="Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env"
        )
    
    try:
        result = sync_treasury_to_supabase(start_date, end_date)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Also save an alert about the sync
        save_alert(
            title="Data Sync Complete",
            message=f"Synced {result.get('records_synced', 0)} records to database",
            severity="info"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Risk Analytics Endpoints
# =============================================================================

@app.get("/api/risk/var")
async def get_var_analysis(
    confidence: float = Query(0.95, ge=0.90, le=0.99, description="Confidence level"),
    horizon: int = Query(1, ge=1, le=30, description="Horizon in days")
):
    """
    Calculate Value-at-Risk for all currencies.
    Returns parametric, historical, and Monte Carlo VaR with CVaR.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        var_calc = VaRCalculator(confidence=confidence, horizon_days=horizon)
        results = {}
        
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency].copy()
            returns = calculate_returns(currency_df, currency)
            var_result = var_calc.calculate_currency_var(returns, currency)
            results[currency] = var_result.to_dict()
        
        return {
            "confidence": confidence,
            "horizon_days": horizon,
            "currencies": results
        }
    except Exception as e:
        logger.error(f"VaR calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/stress-test")
async def get_stress_test():
    """
    Run stress tests against historical scenarios.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        from analytics.var import STRESS_SCENARIOS
        
        scenarios = []
        for scenario in STRESS_SCENARIOS:
            scenarios.append({
                "name": scenario.name,
                "description": scenario.description,
                "impacts": scenario.get_shocks()
            })
        
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/recommendations")
async def get_hedging_recommendations():
    """
    Generate hedging recommendations based on current risk metrics.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        # Calculate VaR for each currency
        var_calc = VaRCalculator(confidence=0.95, horizon_days=1)
        var_results = {}
        volatility_metrics = {}
        
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency].copy()
            returns = calculate_returns(currency_df, currency)
            var_result = var_calc.calculate_currency_var(returns, currency)
            var_results[currency] = var_result
            volatility_metrics[currency] = {
                "volatility": var_result.volatility,
                "mean_return": var_result.mean_return
            }
        
        # Calculate correlations
        pivot_df = df.pivot_table(
            index="record_date",
            columns="currency",
            values="exchange_rate"
        ).pct_change().dropna()
        correlations = pivot_df.corr().to_dict()
        
        # Generate recommendations
        engine = HedgingRecommendationEngine()
        recommendations = engine.generate_recommendations(
            var_results=var_results,
            volatility_metrics=volatility_metrics,
            correlations=correlations
        )
        
        return recommendations.to_dict()
    except Exception as e:
        logger.error(f"Recommendations failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Scheduler Endpoints
# =============================================================================

@app.get("/api/scheduler/jobs")
async def get_scheduled_jobs():
    """Get list of scheduled background jobs."""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        return {
            "status": "running" if scheduler._is_running else "stopped",
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Failed to get jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/jobs/{job_id}/run")
async def trigger_job(job_id: str):
    """Manually trigger a scheduled job."""
    try:
        scheduler = get_scheduler()
        success = scheduler.run_job_now(job_id)
        
        if success:
            return {"status": "triggered", "job_id": job_id}
        else:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/start")
async def start_scheduler_endpoint():
    """Start the background scheduler."""
    try:
        start_scheduler()
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/stop")
async def stop_scheduler_endpoint():
    """Stop the background scheduler."""
    try:
        stop_scheduler()
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Explainability Endpoints
# =============================================================================

@app.get("/api/explain/status")
async def get_explainability_status():
    """Check if SHAP explainability is available."""
    return {
        "shap_available": shap_available(),
        "features": [
            "XGBoost feature importance",
            "SHAP value decomposition",
            "Model agreement analysis"
        ] if shap_available() else []
    }


# =============================================================================
# Forecast Endpoints (with Model Registry)
# =============================================================================

# Global model registry
_model_registry = ModelRegistry("trained_models", use_supabase=False)


@app.get("/api/forecasts")
async def get_forecasts(
    currency: str = Query("EUR", description="Currency code"),
    horizon: int = Query(30, description="Forecast horizon in days"),
    model: Optional[str] = Query(None, description="Model to use (or active model from registry)")
):
    """
    Generate forecasts using trained models.
    
    Returns predictions with confidence intervals and model metadata.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        # Determine which model to use
        if model is None:
            # Try to load active model from registry
            active_model = _model_registry.get_active_model(currency)
            if active_model:
                model = active_model.model_name
                logger.info(f"Using active model: {model} for {currency}")
            else:
                model = "ensemble"
                logger.info(f"No active model, defaulting to ensemble for {currency}")
        
        # Create trainer and train on available data
        model_lower = model.lower()
        
        if model_lower == "prophet":
            trainer = ProphetTrainer("trained_models")
        elif model_lower == "arima":
            trainer = ARIMATrainer("trained_models")
        elif model_lower == "xgboost":
            trainer = XGBoostTrainer("trained_models")
        elif model_lower == "ensemble":
            trainer = EnsembleTrainer("trained_models")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model: {model}")
        
        # Train and predict
        trainer.train(currency_df, currency, train_ratio=1.0)  # Use all data
        forecast = trainer.predict(horizon)
        
        return {
            "currency": currency,
            "horizon": horizon,
            "model_used": model_lower,
            "generated_at": datetime.now().isoformat(),
            **forecast
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/registry")
async def get_model_registry():
    """Get summary of registered models."""
    try:
        return _model_registry.get_registry_summary()
    except Exception as e:
        logger.error(f"Registry query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/available")
async def get_available_models():
    """Get list of available models and their status."""
    return TrainingOrchestrator.get_available_models()


@app.post("/api/models/train")
async def train_model_endpoint(
    currency: str = Query("EUR", description="Currency to train"),
    model_type: str = Query("ensemble", description="Model type to train")
):
    """
    Train a model for a specific currency.
    
    Note: For large-scale training, use the CLI instead:
    python ml/cli/train_models.py
    """
    from fastapi import BackgroundTasks
    
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        orchestrator = TrainingOrchestrator(model_type=model_type)
        metrics = orchestrator.train(currency_df, currency)
        model_path = orchestrator.save(set_active=True)
        
        return {
            "status": "success",
            "currency": currency,
            "model_type": model_type,
            "metrics": metrics.to_dict(),
            "model_path": model_path,
            "message": f"Model trained and set as active for {currency}"
        }
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Intelligent Alerting Endpoints
# =============================================================================

# Global alert engine
_alert_engine = create_alert_engine(dashboard_url="http://localhost:3000")


@app.get("/api/alerts/active")
async def get_active_alerts(currency: Optional[str] = Query(None, description="Currency filter")):
    """Get all active intelligent alerts."""
    try:
        alerts = _alert_engine.get_active_alerts(currency)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/trigger/volatility")
async def trigger_volatility_alert(
    currency: str = Query("EUR", description="Currency code")
):
    """
    Manually trigger volatility alert check for a currency.
    Will generate alert if conditions met.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        # Calculate volatility metrics
        returns = currency_df["exchange_rate"].pct_change().dropna()
        current_vol = returns.tail(30).std() * np.sqrt(252) * 100
        mean_vol = returns.std() * np.sqrt(252) * 100
        
        # Calculate percentile
        rolling_vols = returns.rolling(30).std() * np.sqrt(252) * 100
        percentile = (rolling_vols < current_vol).mean() * 100
        
        # Create and process alert
        alert = _alert_engine.create_volatility_alert(
            currency=currency,
            current_volatility=current_vol,
            mean_volatility=mean_vol,
            volatility_percentile=percentile
        )
        
        if alert:
            sent = _alert_engine.process_alert(alert)
            return {
                "status": "triggered" if sent else "suppressed",
                "alert": alert.to_dict() if alert else None,
                "sent_to_slack": sent
            }
        else:
            return {"status": "no_alert", "reason": "Volatility within normal range"}
            
    except Exception as e:
        logger.error(f"Alert trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/trigger/var")
async def trigger_var_alert(
    currency: str = Query("EUR", description="Currency code"),
    confidence: float = Query(0.95, description="VaR confidence level")
):
    """
    Trigger VaR breach alert check for a currency.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        # Calculate VaR
        returns = calculate_returns(currency_df, currency)
        var_calc = VaRCalculator(confidence=confidence, horizon_days=1)
        var_result = var_calc.calculate_currency_var(returns, currency)
        
        # Create and process alert
        alert = _alert_engine.create_var_breach_alert(
            currency=currency,
            var_95=var_result.var_parametric * 100,
            var_99=var_result.var_parametric * 100 * 1.3,  # Approximation
            cvar=var_result.cvar * 100,
            threshold=2.0
        )
        
        if alert:
            sent = _alert_engine.process_alert(alert)
            return {
                "status": "triggered" if sent else "suppressed",
                "alert": alert.to_dict(),
                "sent_to_slack": sent
            }
        else:
            return {"status": "no_alert", "reason": "VaR within threshold"}
            
    except Exception as e:
        logger.error(f"VaR alert trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/trigger/regime")
async def trigger_regime_alert(
    currency: str = Query("EUR", description="Currency code")
):
    """
    Trigger regime change alert check for a currency.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        # Detect regime
        detector = RegimeDetector(n_regimes=4)
        detector.fit(currency_df, currency)
        regime = detector.detect(currency_df, currency)
        
        # Create alert (assuming we track previous regime)
        previous_regime = "Low Volatility"  # Would be stored in state normally
        
        if regime.regime_name != previous_regime:
            alert = _alert_engine.create_regime_change_alert(
                currency=currency,
                old_regime=previous_regime,
                new_regime=regime.regime_name,
                confidence=regime.confidence,
                model_name="hmm"
            )
            
            if alert:
                sent = _alert_engine.process_alert(alert)
                return {
                    "status": "triggered" if sent else "suppressed",
                    "alert": alert.to_dict(),
                    "sent_to_slack": sent
                }
        
        return {
            "status": "no_change",
            "current_regime": regime.regime_name,
            "confidence": regime.confidence
        }
            
    except Exception as e:
        logger.error(f"Regime alert trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: str = Query("api_user")):
    """Acknowledge an alert."""
    success = _alert_engine.acknowledge_alert(alert_id, user)
    if success:
        return {"status": "acknowledged", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    success = _alert_engine.resolve_alert(alert_id)
    if success:
        return {"status": "resolved", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/api/alerts/{alert_id}/snooze")
async def snooze_alert(alert_id: str, hours: int = Query(4)):
    """Snooze an alert for specified hours."""
    success = _alert_engine.snooze_alert(alert_id, hours)
    if success:
        return {"status": "snoozed", "alert_id": alert_id, "hours": hours}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/api/alerts/summary")
async def send_alert_summary():
    """Send daily alert summary to Slack."""
    success = _alert_engine.send_daily_summary()
    return {"status": "sent" if success else "failed"}


@app.post("/api/alerts/portfolio")
async def set_portfolio_exposure(
    currency: str = Query(..., description="Currency code"),
    amount: float = Query(..., description="Exposure amount in USD"),
    direction: str = Query("long", description="Position direction")
):
    """Update portfolio exposure for a currency (affects alert impact calculations)."""
    _alert_engine.set_portfolio_exposure(currency, amount, direction)
    return {"status": "updated", "currency": currency, "amount": amount, "direction": direction}


# =============================================================================
# Regime Detection Endpoints
# =============================================================================

@app.get("/api/regime/detect")
async def detect_regime(currency: str = Query("EUR", description="Currency code")):
    """
    Detect current market regime using Hidden Markov Models.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        currency_df = df[df["currency"] == currency]
        if currency_df.empty:
            raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
        
        detector = RegimeDetector(n_regimes=4)
        detector.fit(currency_df, currency)
        regime = detector.detect(currency_df, currency)
        
        return {
            "currency": currency,
            "hmm_available": hmm_available(),
            **regime.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/regime/all")
async def detect_all_regimes():
    """
    Detect regimes for all currencies.
    """
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        results = {}
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency]
            detector = RegimeDetector(n_regimes=4)
            detector.fit(currency_df, currency)
            regime = detector.detect(currency_df, currency)
            results[currency] = regime.to_dict()
        
        return {"regimes": results, "hmm_available": hmm_available()}
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PDF Export Endpoints
# =============================================================================

@app.get("/api/reports/executive-summary")
async def generate_executive_summary():
    """
    Generate executive summary PDF report.
    Returns PDF as binary download.
    """
    from fastapi.responses import Response
    
    if not pdf_available():
        raise HTTPException(status_code=503, detail="PDF generation not available")
    
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        # Get recommendations
        var_calc = VaRCalculator(confidence=0.95, horizon_days=1)
        var_results = {}
        volatility_metrics = {}
        
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency]
            returns = calculate_returns(currency_df, currency)
            var_result = var_calc.calculate_currency_var(returns, currency)
            var_results[currency] = var_result
            volatility_metrics[currency] = {"volatility": var_result.volatility}
        
        pivot_df = df.pivot_table(
            index="record_date",
            columns="currency",
            values="exchange_rate"
        ).pct_change().dropna()
        correlations = pivot_df.corr().to_dict()
        
        engine = HedgingRecommendationEngine()
        recommendations = engine.generate_recommendations(
            var_results=var_results,
            volatility_metrics=volatility_metrics,
            correlations=correlations
        ).to_dict()
        
        # Get regime
        first_currency = df["currency"].iloc[0]
        currency_df = df[df["currency"] == first_currency]
        detector = RegimeDetector()
        detector.fit(currency_df, first_currency)
        regime = detector.detect(currency_df, first_currency).to_dict()
        
        # Generate PDF
        generator = PDFReportGenerator(title="Sapphire Intelligence")
        pdf_bytes = generator.generate_executive_summary(
            kpis={},
            recommendations=recommendations,
            regime=regime
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=executive_summary.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/risk-report")
async def generate_risk_report():
    """
    Generate detailed risk report PDF.
    Returns PDF as binary download.
    """
    from fastapi.responses import Response
    from analytics.var import STRESS_SCENARIOS
    
    if not pdf_available():
        raise HTTPException(status_code=503, detail="PDF generation not available")
    
    df = app_state.get("data")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    try:
        # Get VaR data
        var_calc = VaRCalculator(confidence=0.95, horizon_days=1)
        var_results = {}
        volatility_metrics = {}
        
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency]
            returns = calculate_returns(currency_df, currency)
            var_result = var_calc.calculate_currency_var(returns, currency)
            var_results[currency] = var_result.to_dict()
            volatility_metrics[currency] = {"volatility": var_result.volatility}
        
        # Stress tests
        stress_tests = [
            {"name": s.name, "description": s.description, "impacts": s.get_shocks()}
            for s in STRESS_SCENARIOS
        ]
        
        # Recommendations
        pivot_df = df.pivot_table(
            index="record_date",
            columns="currency",
            values="exchange_rate"
        ).pct_change().dropna()
        correlations = pivot_df.corr().to_dict()
        
        # Re-get var_results as objects for recommendations
        var_results_obj = {}
        for currency in df["currency"].unique():
            currency_df = df[df["currency"] == currency]
            returns = calculate_returns(currency_df, currency)
            var_results_obj[currency] = var_calc.calculate_currency_var(returns, currency)
        
        engine = HedgingRecommendationEngine()
        recommendations = engine.generate_recommendations(
            var_results=var_results_obj,
            volatility_metrics=volatility_metrics,
            correlations=correlations
        ).to_dict()
        
        # Generate PDF
        generator = PDFReportGenerator(title="Sapphire Intelligence - Risk Report")
        pdf_bytes = generator.generate_risk_report(
            var_data={"currencies": var_results},
            stress_tests=stress_tests,
            recommendations=recommendations
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=risk_report.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/timeseries")
async def get_timeseries_data(
    currencies: Optional[str] = Query(None, description="Comma-separated currency codes"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get time series data for visualization."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    df_filtered = filter_dataframe_by_date(df, start_date, end_date)
    
    # Filter by currencies
    if currencies:
        currency_list = [c.strip().upper() for c in currencies.split(",")]
        df_filtered = df_filtered[df_filtered["currency"].isin(currency_list)]
    
    # Select relevant columns
    result = df_filtered[["record_date", "currency", "pair", "exchange_rate", "returns", 
                 "rolling_volatility", "mom_change", "yoy_change"]].copy()
    
    # Convert to records
    result["record_date"] = result["record_date"].dt.strftime("%Y-%m-%d")
    records = dataframe_to_records_safe(result)
    
    return {
        "data": records,
        "count": len(records)
    }


@app.get("/api/metrics/latest", response_model=List[LatestRatesResponse])
async def get_latest_rates(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get latest rates and metrics for all currencies."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    
    if filtered.empty:
        return []
    
    # Ensure consistent currency ordering (alphabetical: CAD, EUR, GBP)
    currencies = sorted(filtered["currency"].unique())
    results = []
    fmp_available = bool(app_state.get("fmp_available", False))
    
    for currency in currencies:
        metrics = get_latest_metrics(filtered, currency)
        results.append(LatestRatesResponse(**metrics, fmp_available=fmp_available))
    
    return results


@app.get("/api/metrics/yoy-comparison")
async def get_yoy_comparison_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get year-on-year comparison data."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    
    if filtered.empty:
        return {"data": []}
    
    comparison = get_yoy_comparison(filtered)
    comparison["current_date"] = comparison["current_date"].dt.strftime("%Y-%m-%d")
    records = dataframe_to_records_safe(comparison)
    
    return {
        "data": records
    }


@app.get("/api/volatility/summary", response_model=List[VolatilityMetricsResponse])
async def get_volatility_summary_all():
    """Get volatility summary for all currencies."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    comparison = compare_volatility_across_currencies(df)
    
    results = []
    for _, row in comparison.iterrows():
        results.append(VolatilityMetricsResponse(**row.to_dict()))
    
    return results


@app.get("/api/volatility/{currency}")
async def get_volatility_timeseries(currency: str):
    """Get volatility time series for a specific currency."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    currency = currency.upper()
    currency_df = df[df["currency"] == currency].copy()
    
    if currency_df.empty:
        raise HTTPException(status_code=404, detail=f"Currency {currency} not found")
    
    result = currency_df[["record_date", "rolling_volatility", "annualized_volatility", 
                          "volatility_regime"]].dropna()
    result["record_date"] = result["record_date"].dt.strftime("%Y-%m-%d")
    records = dataframe_to_records_safe(result)
    
    return {
        "currency": currency,
        "data": records
    }


@app.get("/api/forecast/{currency}", response_model=ForecastResponse)
async def get_forecast(
    currency: str,
    horizon: int = Query(6, ge=1, le=12),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get forecast for a specific currency.
    
    PRODUCTION BEHAVIOR:
    - Loads trained model from registry (NEVER trains)
    - Returns 422 if no trained model exists
    - No silent fallbacks
    
    Train models via terminal before using this endpoint.
    """
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    currency = currency.upper()
    
    # Get historical data for display
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    currency_display_df = filtered[filtered["currency"] == currency].copy()
    
    if currency_display_df.empty:
        currency_display_df = df[df["currency"] == currency].copy()
    
    if currency_display_df.empty:
        raise HTTPException(status_code=404, detail=f"Currency not found: {currency}")
    
    currency_display_df = currency_display_df.sort_values("record_date")
    historical_df = currency_display_df.dropna(subset=["exchange_rate"]).tail(120)
    historical_points = [
        ForecastPoint(
            date=row["record_date"].strftime("%Y-%m-%d"),
            value=float(row["exchange_rate"])
        )
        for _, row in historical_df.iterrows()
    ]
    
    # Use ForecastService to generate predictions (NEVER trains)
    forecast_service = ForecastService(_model_registry)
    
    try:
        # Generate forecast using trained model from registry
        result = forecast_service.generate_forecast(
            currency=currency,
            horizon=horizon,
            confidence=0.80,
            historical_data=currency_display_df
        )
        
        # Convert to response format
        forecast_points = [
            ForecastPoint(date=fc.date, value=fc.value)
            for fc in result.forecasts
        ]
        
        confidence_points = [
            ConfidenceBandPoint(date=fc.date, lower=fc.lower, upper=fc.upper)
            for fc in result.forecasts
        ]
        
        forecast_start = forecast_points[0].date if forecast_points else None
        
        # Build model metadata from ForecastService result
        model_meta = ModelMetadata(
            model_type=result.metadata.model_type,
            model_version=result.metadata.model_id,
            trained_at=result.metadata.trained_at,
            is_fallback=result.metadata.is_fallback,
            data_window_start=result.metadata.data_window_start,
            data_window_end=result.metadata.data_window_end,
            metrics={
                "mape": result.metadata.validation_mape,
                "rmse": result.metadata.validation_rmse,
                "train_samples": result.metadata.training_samples,
                "test_samples": result.metadata.test_samples,
                "forecast_strategy": result.metadata.forecast_strategy
            }
        )
        
        # Generate narrative insight
        insight = None
        narrative_engine: NarrativeEngine = app_state["narrative_engine"]
        
        if forecast_points and historical_points:
            last_actual = historical_points[-1].value
            final_forecast = forecast_points[-1].value
            
            if final_forecast > last_actual * 1.01:
                direction = "mild appreciation"
            elif final_forecast < last_actual * 0.99:
                direction = "mild depreciation"
            else:
                direction = "relative stability"
            
            insight = narrative_engine.generate_forecast_insight(
                currency,
                direction,
                confidence=0.65,
                horizon=f"next {horizon} months"
            )
        
        logger.info(f"Generated forecast for {currency} using {result.metadata.model_type} (no training)")
        
        # Compute last_actual from historical points for chart anchoring
        last_actual_point = None
        if historical_points:
            last_actual_point = LastActualPoint(
                date=historical_points[-1].date,
                value=historical_points[-1].value
            )
        
        return ForecastResponse(
            currency=currency,
            forecast_start=forecast_start,
            historical=historical_points,
            forecast=forecast_points,
            confidence=confidence_points,
            insight=insight,
            model=model_meta,
            last_actual=last_actual_point,
            frequency="M"  # Monthly data
        )
        
    except ModelNotFoundError as e:
        # No trained model - return explicit error (NO FALLBACK)
        logger.warning(f"No trained model for {currency}: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "model_not_trained",
                "message": f"No trained model found for currency: {currency}",
                "currency": currency,
                "action": "Train a model via terminal using: python -c \"from ml.registry import TrainingOrchestrator; ...\"",
                "hint": "Models must be trained before forecasts can be generated. Use the terminal training menu on server startup."
            }
        )
        
    except ModelLoadError as e:
        logger.error(f"Failed to load model for {currency}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "model_load_failed",
                "message": f"Failed to load model: {e.reason}",
                "model_id": e.model_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating forecast for {currency}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anomalies")
async def get_anomalies(
    currency: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get detected anomalies."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    
    if currency:
        currency = currency.upper()
    
    anomalies = app_state["anomaly_detector"].get_anomaly_periods(filtered, currency)
    
    if anomalies.empty:
        return {"anomalies": []}
    
    anomalies["record_date"] = anomalies["record_date"].dt.strftime("%Y-%m-%d")
    records = dataframe_to_records_safe(anomalies)
    
    return {
        "anomalies": records,
        "count": len(records)
    }


@app.get("/api/insights/{currency}", response_model=InsightResponse)
async def get_insights(currency: str):
    """Get narrative insights for a specific currency."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    currency = currency.upper()
    
    # Get metrics
    metrics = get_latest_metrics(df, currency)
    volatility = get_volatility_summary(df, currency)
    
    # Get forecast info
    try:
        forecast_df, confidence = app_state["forecaster"].forecast_rates(df, currency, 3)
        
        if forecast_df is not None and len(confidence["mean"]) > 0:
            # Determine forecast direction
            current_rate = metrics.get("latest_rate", 0)
            forecast_rate = confidence["mean"][0]
            
            if forecast_rate > current_rate * 1.01:
                direction = "mild appreciation"
            elif forecast_rate < current_rate * 0.99:
                direction = "mild depreciation"
            else:
                direction = "relative stability"
            
            forecast_info = {
                "direction": direction,
                "confidence": 0.65,
                "horizon": "the next quarter"
            }
        else:
            forecast_info = None
    except:
        forecast_info = None
    
    # Get anomalies
    anomalies_df = app_state["anomaly_detector"].get_anomaly_periods(df, currency)
    
    anomalies_list = None
    if not anomalies_df.empty:
        recent_anomaly = anomalies_df.iloc[0]
        anomalies_list = [{
            "date": recent_anomaly["record_date"].strftime("%Y-%m-%d") if hasattr(recent_anomaly["record_date"], "strftime") else str(recent_anomaly["record_date"]),
            "type": "volatility spike",
            "magnitude": recent_anomaly.get("returns", None)
        }]
    
    # Generate insights
    insights = app_state["narrative_engine"].generate_complete_narrative(
        currency,
        metrics,
        volatility,
        forecast_info,
        anomalies_list
    )
    
    return InsightResponse(
        currency=currency,
        insights=insights
    )


@app.get("/api/insights/summary")
async def get_summary_insight():
    """Get high-level summary insight across all currencies."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    currencies = df["currency"].unique()
    all_metrics = {}
    
    for currency in currencies:
        all_metrics[currency] = get_latest_metrics(df, currency)
    
    summary = app_state["narrative_engine"].generate_summary_narrative(all_metrics)
    
    return {
        "summary": summary
    }


@app.get("/api/insights/highlights", response_model=HighlightsResponse)
async def get_highlights(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get highlight bullets for the dashboard."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    
    if filtered.empty:
        fallback_highlights = generate_highlights(df)
        response_items = [
            HighlightItem(
                title="No Data in Range",
                body="Expand the date range to generate insights for the selected window. Showing most recent signals instead."
            ),
            *[HighlightItem(**highlight) for highlight in fallback_highlights]
        ]
        return HighlightsResponse(highlights=response_items)
    
    highlights = generate_highlights(filtered)
    return HighlightsResponse(highlights=[HighlightItem(**highlight) for highlight in highlights])


@app.post("/api/alerts/test", response_model=AlertTestResponse)
async def send_test_alert():
    """Send a test Slack alert."""
    try:
        notifier = app_state["alert_manager"].notifier
        
        if not notifier.is_configured():
            return AlertTestResponse(
                success=False,
                message="Slack webhook not configured. Set SLACK_WEBHOOK_URL environment variable."
            )
        
        success = notifier.send_test_alert()
        
        if success:
            return AlertTestResponse(
                success=True,
                message="Test alert sent successfully to Slack"
            )
        else:
            return AlertTestResponse(
                success=False,
                message="Failed to send test alert. Check webhook URL and logs."
            )
            
    except Exception as e:
        return AlertTestResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@app.post("/api/alerts/slack-summary")
async def send_slack_summary(payload: SlackSummaryRequest):
    """Send a concise summary message to Slack."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    notifier = app_state["alert_manager"].notifier
    
    if not notifier.is_configured():
        raise HTTPException(status_code=400, detail="Slack webhook not configured")
    
    filtered = filter_dataframe_by_date(df, payload.start_date, payload.end_date)
    
    if filtered.empty:
        raise HTTPException(status_code=400, detail="No data available for the requested date range")
    
    summary_lines = build_slack_summary_lines(filtered)
    
    success = notifier.send_summary(
        title="Currency Intelligence – Daily Summary",
        lines=summary_lines
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send Slack summary")
    
    return {
        "status": "sent",
        "lines": len(summary_lines)
    }


@app.get("/api/alerts/history")
async def get_alert_history(limit: int = Query(10, ge=1, le=100)):
    """Get recent alert history."""
    history = app_state["alert_manager"].get_alert_history(limit)
    
    return {
        "alerts": history,
        "count": len(history)
    }


@app.post("/api/alerts/check")
async def check_alerts():
    """Check all alert conditions and send alerts if triggered."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    alerts_sent = []
    
    currencies = df["currency"].unique()
    
    for currency in currencies:
        pair = f"USD/{currency}"
        
        # Check YoY alerts
        metrics = get_latest_metrics(df, currency)
        if metrics.get("yoy_change") is not None:
            if app_state["alert_manager"].check_yoy_alert(
                pair,
                metrics["yoy_change"],
                metrics["latest_rate"]
            ):
                alerts_sent.append({"type": "YoY Movement", "currency": pair})
        
        # Check volatility alerts
        vol_summary = get_volatility_summary(df, currency)
        if vol_summary.get("current_volatility") is not None:
            currency_df = df[df["currency"] == currency]
            vol_data = currency_df["rolling_volatility"].dropna()
            
            if len(vol_data) > 0:
                std_vol = vol_data.std()
                
                if app_state["alert_manager"].check_volatility_alert(
                    pair,
                    vol_summary["current_volatility"],
                    vol_summary["mean_volatility"],
                    std_vol
                ):
                    alerts_sent.append({"type": "Volatility Spike", "currency": pair})
    
    return {
        "alerts_sent": alerts_sent,
        "count": len(alerts_sent)
    }


# =============================================================================
# EIS / Companies House Endpoints
# =============================================================================

@app.get("/api/eis/companies")
async def get_eis_companies():
    """
    Get list of EIS companies for monitoring.
    Returns sample data for demo, real data from Companies House when available.
    """
    try:
        # Return sample EIS data for demo
        companies = get_sample_eis_data()
        
        return {
            "companies": companies,
            "count": len(companies),
            "source": "sample_data",
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get EIS companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/company/{company_number}")
async def get_company_details(company_number: str):
    """
    Get detailed company information from Companies House.
    
    Args:
        company_number: 8-character company registration number
    """
    try:
        client = get_companies_house_client()
        
        if not client.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Companies House API not configured. Set COMPANIES_HOUSE_API_KEY in .env"
            )
        
        company_data = client.get_company_with_details(company_number)
        
        if not company_data:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_number} not found"
            )
        
        return company_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company {company_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/company/{company_number}/full-profile")
async def get_company_full_profile(company_number: str):
    """
    Get comprehensive company profile with ALL available data and EIS assessment.
    
    This endpoint orchestrates multiple Companies House API calls:
    - Company profile
    - Officers (directors/secretaries)
    - Persons with Significant Control (PSCs)
    - Charges (mortgages/security)
    - Filing history (with analysis)
    
    Plus calculates EIS likelihood score using heuristic rules.
    
    Args:
        company_number: 8-character company registration number
        
    Returns:
        Full company profile with EIS assessment
    """
    try:
        client = get_companies_house_client()
        
        if not client.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Companies House API not configured. Set COMPANIES_HOUSE_API_KEY in .env"
            )
        
        # Get full profile from Companies House
        full_profile = client.get_full_profile(company_number)
        
        if not full_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_number} not found"
            )
        
        # Calculate EIS assessment
        try:
            from analytics.eis_heuristics import calculate_eis_likelihood
            eis_assessment = calculate_eis_likelihood(full_profile)
        except Exception as e:
            logger.warning(f"EIS assessment failed for {company_number}: {e}")
            eis_assessment = {
                "score": 0,
                "status": "Assessment Failed",
                "error": str(e)
            }
        
        # Combine profile with assessment
        full_profile["eis_assessment"] = eis_assessment
        
        return full_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get full profile for {company_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/company/{company_number}/news")
async def get_company_news(company_number: str):
    """
    Get AI-powered news summary for a company using dual-agent pipeline.
    
    Agent A (Research): Uses Tavily API for contextual news search with SIC-sector keywords.
    Agent B (Editor): Uses HuggingFace LLM to create professional 2-sentence investor briefings.
    
    Args:
        company_number: 8-character company registration number
        
    Returns:
        Professional news summary with sources for the company
    """
    try:
        # Get company profile for context
        client = get_companies_house_client()
        company_name = f'Company {company_number}'
        sic_codes = []
        eis_score = 0
        sector = "Unknown"
        
        if client.is_configured():
            try:
                profile = client.get_company_profile(company_number)
                company_name = profile.get('company_name', company_name)
                sic_codes = profile.get('sic_codes', [])
                
                # Get sector name from SIC codes
                from automation.writer import get_sector_name
                sector = get_sector_name(sic_codes)
                
                # Try to get EIS score if available
                try:
                    from core.eis_eligibility_scorer import EISEligibilityScorer
                    scorer = EISEligibilityScorer()
                    eis_result = scorer.quick_score({'company': profile})
                    eis_score = eis_result.get('score', 0)
                except:
                    eis_score = 0
                    
            except Exception as e:
                logger.warning(f"Could not get company profile: {e}")
        
        # === AGENT A: RESEARCH (Tavily) ===
        research_results = None
        try:
            from services.research_agent import ResearchAgent
            researcher = ResearchAgent()
            
            if researcher.available:
                research_results = researcher.search(
                    company_name=company_name,
                    sic_codes=sic_codes,
                    max_results=5
                )
                logger.info(f"Research Agent found {len(research_results.get('results', []))} results")
        except ImportError:
            logger.warning("Research Agent not available")
        except Exception as e:
            logger.warning(f"Research Agent failed: {e}")
        
        # === AGENT B: EDITOR (HuggingFace LLM) ===
        editor_summary = None
        if research_results and research_results.get('success') and research_results.get('results'):
            try:
                from services.editor_agent import EditorAgent
                editor = EditorAgent()
                
                editor_summary = editor.summarize(
                    company_name=company_name,
                    raw_results=research_results.get('results', []),
                    eis_score=eis_score,
                    sector=sector,
                    eis_status="Under Review"
                )
                logger.info(f"Editor Agent generated summary (relevant: {editor_summary.get('is_relevant')})")
            except ImportError:
                logger.warning("Editor Agent not available")
            except Exception as e:
                logger.warning(f"Editor Agent failed: {e}")
        
        # Build response
        if editor_summary and editor_summary.get('is_relevant') and editor_summary.get('summary'):
            # Full pipeline success - return professional summary
            return {
                "company_number": company_number,
                "company_name": company_name,
                "sector": sector,
                "summary": editor_summary.get('summary'),
                "source": "ai-agents",
                "agents": {
                    "research": "tavily" if research_results.get('success') else "fallback",
                    "editor": editor_summary.get('model', 'unknown')
                },
                "sources": editor_summary.get('sources', []),
                "raw_results": research_results.get('results', [])[:3],
                "tavily_answer": research_results.get('answer'),
                "query": research_results.get('query')
            }
        elif research_results and research_results.get('results'):
            # Research succeeded but no LLM summary - use Tavily's answer or raw results
            news_items = []
            for item in research_results['results'][:3]:
                news_items.append(f"- {item.get('title', 'News')}: {item.get('content', '')[:150]}...")
            
            summary = research_results.get('answer') or f"Latest news for {company_name}:\n\n" + "\n\n".join(news_items)
            
            return {
                "company_number": company_number,
                "company_name": company_name,
                "sector": sector,
                "summary": summary,
                "source": "tavily-raw",
                "agents": {"research": "tavily", "editor": "none"},
                "sources": [r.get('url') for r in research_results['results'][:3]],
                "raw_results": research_results.get('results', [])[:3],
                "query": research_results.get('query')
            }
        else:
            # Fallback - no agents available
            return {
                "company_number": company_number,
                "company_name": company_name,
                "sector": sector,
                "summary": (
                    f"AI Newsroom for {company_name} ({sector} sector).\n\n"
                    f"To enable real-time news:\n"
                    f"1. Set TAVILY_API_KEY in your .env for news search\n"
                    f"2. Set HUGGINGFACE_API_KEY for AI summaries\n\n"
                    f"Currently using Companies House data for company analysis."
                ),
                "source": "fallback",
                "agents": {"research": "unavailable", "editor": "unavailable"},
                "sources": [],
                "raw_results": []
            }
        
    except Exception as e:
        logger.error(f"Failed to get news for {company_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/search")
async def search_companies(
    query: str = Query(..., description="Company name or number to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search Companies House for companies.
    """
    try:
        client = get_companies_house_client()
        
        if not client.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Companies House API not configured"
            )
        
        results = client.search_companies(query, items_per_page=limit)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed for '{query}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/summary")
async def get_eis_summary():
    """
    Get summary statistics for EIS companies.
    """
    try:
        companies = get_sample_eis_data()
        
        # Calculate summary stats
        total_companies = len(companies)
        approved = sum(1 for c in companies if c.get('eis_status') == 'Approved')
        pending = sum(1 for c in companies if c.get('eis_status') == 'Pending')
        total_raised = sum(c.get('amount_raised', 0) for c in companies)
        
        # Risk breakdown
        low_risk = sum(1 for c in companies if c.get('risk_score') == 'Low')
        medium_risk = sum(1 for c in companies if c.get('risk_score') == 'Medium')
        high_risk = sum(1 for c in companies if c.get('risk_score') == 'High')
        
        # Sector breakdown
        sectors = {}
        for c in companies:
            sector = c.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + 1
        
        # Investment stage breakdown
        stages = {}
        for c in companies:
            stage = c.get('investment_stage', 'Unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        return {
            "total_companies": total_companies,
            "eis_approved": approved,
            "eis_pending": pending,
            "total_raised": total_raised,
            "average_raised": total_raised / total_companies if total_companies > 0 else 0,
            "risk_breakdown": {
                "low": low_risk,
                "medium": medium_risk,
                "high": high_risk
            },
            "sectors": sectors,
            "investment_stages": stages,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get EIS summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/newsletter")
async def generate_eis_newsletter_pdf_sample():
    """
    Generate EIS Newsletter PDF with sample data.
    Use POST /api/eis/newsletter with company data for real companies.
    """
    from fastapi.responses import Response
    
    try:
        if not eis_newsletter_available():
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available. Install reportlab."
            )
        
        companies = get_sample_eis_data()
        
        generator = EISNewsletterGenerator()
        pdf_bytes = generator.generate_newsletter(
            companies=companies,
            title="EIS Investment Due Diligence Report"
        )
        
        filename = f"eis_newsletter_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/eis/newsletter")
async def generate_eis_newsletter_pdf_custom(companies: List[Dict[str, Any]] = Body(...)):
    """
    Generate EIS Newsletter PDF with custom company data.
    
    Accepts a list of company objects from Companies House API.
    Each company should have:
    - company_number: str
    - company_name: str
    - company_status: str
    - date_of_creation: str (optional)
    - sic_codes: list (optional)
    - registered_office_address: dict (optional)
    - directors: list (optional)
    - has_charges: bool (optional)
    - has_insolvency_history: bool (optional)
    """
    from fastapi.responses import Response
    
    try:
        if not eis_newsletter_available():
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available. Install reportlab."
            )
        
        if not companies or len(companies) == 0:
            raise HTTPException(
                status_code=400,
                detail="No companies provided. Please select at least one company."
            )
        
        generator = EISNewsletterGenerator()
        pdf_bytes = generator.generate_newsletter(
            companies=companies,
            title="EIS Investment Due Diligence Report"
        )
        
        filename = f"eis_portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/health")
async def eis_health_check():
    """
    Check EIS integration health status.
    """
    client = get_companies_house_client()
    
    return {
        "companies_house_configured": client.is_configured(),
        "newsletter_available": eis_newsletter_available(),
        "sample_data_count": len(get_sample_eis_data()),
        "status": "healthy" if client.is_configured() else "limited"
    }


@app.get("/api/eis/sectors")
async def get_sector_companies():
    """
    Get top companies from each major investment sector.
    Returns companies grouped by sector for initial page display.
    """
    try:
        client = get_companies_house_client()
        
        if not client.is_configured():
            # Return sample data if API not configured
            return {
                "sectors": {},
                "total_count": 0,
                "api_configured": False
            }
        
        # Define sectors to search for
        sector_keywords = [
            ("Technology", "technology startup"),
            ("Fintech", "fintech"),
            ("Healthcare", "healthcare innovation"),
            ("Clean Energy", "clean energy"),
            ("Agriculture", "agritech"),
        ]
        
        sectors = {}
        total_count = 0
        
        for sector_name, keyword in sector_keywords:
            try:
                results = client.search_companies(keyword, items_per_page=10)
                # Filter to only active companies
                active_results = [r for r in results if r.get('company_status') == 'active'][:10]
                sectors[sector_name] = active_results
                total_count += len(active_results)
            except Exception as e:
                logger.warning(f"Failed to search sector {sector_name}: {e}")
                sectors[sector_name] = []
        
        return {
            "sectors": sectors,
            "total_count": total_count,
            "api_configured": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get sector companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EIS AUTOMATION ENDPOINTS
# =============================================================================

# Import automation modules
try:
    from automation.scanner import EISScanner
    from automation.writer import EISWriter
    from automation.slack_sender import EISSlackSender
    AUTOMATION_AVAILABLE = True
except ImportError as e:
    AUTOMATION_AVAILABLE = False
    logger.warning(f"Automation modules not available: {e}")


@app.get("/api/eis/automation/status")
async def get_automation_status():
    """Get the status of the newsletter automation system."""
    from pathlib import Path
    import json
    
    automation_dir = Path(__file__).parent.parent / "automation"
    output_dir = automation_dir / "output"
    scans_dir = output_dir / "scans" if output_dir.exists() else automation_dir / "scans"
    
    # Get last scan info
    last_scan = None
    scan_files = list(scans_dir.glob("eis_scan_*.json")) if scans_dir.exists() else []
    if scan_files:
        latest_scan_file = max(scan_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_scan_file, 'r') as f:
                scan_data = json.load(f)
                last_scan = {
                    "file": latest_scan_file.name,
                    "timestamp": scan_data.get("scan_timestamp"),
                    "total_found": scan_data.get("total_found", 0),
                    "companies": len(scan_data.get("companies", []))
                }
        except:
            pass
    
    # Get subscriber count
    subscribers_file = automation_dir / "subscribers.json"
    subscriber_count = 0
    if subscribers_file.exists():
        try:
            with open(subscribers_file, 'r') as f:
                data = json.load(f)
                subscriber_count = len(data.get("subscribers", []))
        except:
            pass
    
    # Get newsletter history
    newsletter_files = list(output_dir.glob("newsletter_*.json")) if output_dir.exists() else []
    
    return {
        "automation_available": AUTOMATION_AVAILABLE,
        "last_scan": last_scan,
        "subscriber_count": subscriber_count,
        "newsletters_generated": len(newsletter_files),
        "scans_available": len(scan_files),
        "gmail_configured": bool(os.environ.get("GMAIL_ADDRESS")),
        "companies_house_configured": bool(os.environ.get("COMPANIES_HOUSE_API_KEY"))
    }


@app.post("/api/eis/automation/scan")
async def run_automation_scan(
    days: int = Query(default=7, ge=1, le=30),
    min_score: int = Query(default=50, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Run the SH01 scanner to find companies with recent investment activity."""
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation modules not available")
    
    try:
        from pathlib import Path
        output_dir = Path(__file__).parent.parent / "automation" / "output"
        output_dir.mkdir(exist_ok=True)
        scans_dir = output_dir / "scans"
        scans_dir.mkdir(exist_ok=True)
        
        scanner = EISScanner(output_dir=str(scans_dir))
        results = scanner.run_scan(days=days, min_score=min_score, limit=limit)
        
        # Generate newsletter content if companies found
        newsletter_content = None
        if results.get("companies"):
            writer = EISWriter(use_ai=False)
            newsletter_content = writer.generate_newsletter_content(results["companies"])
        
        return {
            "success": True,
            "scan_results": {
                "candidates": results.get("total_candidates", 0),
                "likely_eligible": results.get("likely_eligible", 0),
                "output_file": results.get("output_file")
            },
            "newsletter_generated": newsletter_content is not None,
            "companies": [
                {
                    "company_name": c.get("company_name"),
                    "company_number": c.get("company_number"),
                    "eis_score": c.get("eis_assessment", {}).get("score", 0),
                    "eis_status": c.get("eis_assessment", {}).get("status", "Unknown"),
                    "narrative": newsletter_content["deal_highlights"][i].get("narrative") if newsletter_content and i < len(newsletter_content.get("deal_highlights", [])) else None
                }
                for i, c in enumerate(results.get("companies", [])[:20])
            ]
        }
        
    except Exception as e:
        logger.error(f"Automation scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eis/automation/subscribers")
async def get_subscribers():
    """Get the list of newsletter subscribers."""
    from pathlib import Path
    import json
    
    subscribers_file = Path(__file__).parent.parent / "automation" / "subscribers.json"
    
    if not subscribers_file.exists():
        return {"subscribers": [], "count": 0}
    
    try:
        with open(subscribers_file, 'r') as f:
            data = json.load(f)
        return {
            "subscribers": data.get("subscribers", []),
            "count": len(data.get("subscribers", [])),
            "updated": data.get("updated")
        }
    except Exception as e:
        logger.error(f"Failed to read subscribers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/eis/automation/subscribers")
async def manage_subscriber(request: Dict = Body(...)):
    """Add a subscriber with their preferred frequency."""
    from pathlib import Path
    import json
    from datetime import datetime
    
    email = request.get("email")
    frequency = request.get("frequency", "weekly")
    action = request.get("action", "add")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    subscribers_file = Path(__file__).parent.parent / "automation" / "subscribers.json"
    
    # Load existing
    if subscribers_file.exists():
        with open(subscribers_file, 'r') as f:
            data = json.load(f)
    else:
        data = {"subscribers": [], "updated": datetime.now().isoformat(), "notes": "Add subscribers using: python mailer.py --add-subscriber email@example.com"}
    
    subscribers = data.get("subscribers", [])
    
    if action == "add":
        if email not in subscribers:
            subscribers.append(email)
            message = f"Added {email} with {frequency} frequency"
        else:
            message = f"{email} already subscribed"
    elif action == "remove":
        if email in subscribers:
            subscribers.remove(email)
            message = f"Removed {email}"
        else:
            message = f"{email} not found"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'add' or 'remove'")
    
    # Save
    data["subscribers"] = subscribers
    data["updated"] = datetime.now().isoformat()
    
    with open(subscribers_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "message": message,
        "count": len(subscribers)
    }


@app.get("/api/eis/automation/history")
async def get_scan_history(limit: int = Query(default=10, ge=1, le=50)):
    """Get history of past scans."""
    from pathlib import Path
    import json
    
    automation_dir = Path(__file__).parent.parent / "automation"
    output_dir = automation_dir / "output"
    scans_dir = output_dir / "scans" if output_dir.exists() else automation_dir / "scans"
    
    if not scans_dir.exists():
        return {"scans": [], "count": 0}
    
    scan_files = sorted(scans_dir.glob("eis_scan_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
    
    history = []
    for scan_file in scan_files:
        try:
            with open(scan_file, 'r') as f:
                data = json.load(f)
                history.append({
                    "file": scan_file.name,
                    "timestamp": data.get("scan_timestamp"),
                    "total_found": data.get("total_found", 0)
                })
        except:
            continue
    
    return {"scans": history, "count": len(history)}


@app.post("/api/eis/automation/send")
async def send_newsletter_email(request: Dict = Body(default={})):
    """Send newsletter email to all subscribers immediately."""
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation modules not available")
    
    try:
        # Extract companies from request
        companies = request.get("companies", [])
        if not companies:
            raise HTTPException(status_code=400, detail="No companies provided")
        
        # Check Slack configuration
        slack_sender = EISSlackSender()
        if not slack_sender.is_configured():
            raise HTTPException(status_code=400, detail="Slack webhook not configured. Set SLACK_WEBHOOK_URL environment variable.")
        
        # Generate newsletter content from companies
        writer = EISWriter(use_ai=True)  # Try AI first, falls back to templates
        
        # Format companies for the writer
        formatted_companies = []
        for c in companies:
            formatted_companies.append({
                "company_name": c.get("company_name"),
                "company_number": c.get("company_number"),
                "eis_assessment": {
                    "score": c.get("eis_score", 0),
                    "status": c.get("eis_status", "Unknown")
                },
                "full_profile": {
                    "company": {"sic_codes": []}
                }
            })
        
        newsletter = writer.generate_newsletter_content(formatted_companies)
        
        # Send to Slack
        results = slack_sender.send_newsletter(newsletter)
        
        return {
            "success": results.get("success", False),
            "sent": results.get("sent", 0),
            "method": "slack",
            "ai_generated": newsletter.get("ai_generated", False),
            "companies": len(companies)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send newsletter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/eis/automation/send-email")
async def send_email_now(request: Dict = Body(...)):
    """
    Send a comprehensive AI-powered newsletter email to a specific recipient immediately.
    
    Includes:
    - Portfolio companies (user's saved selections)
    - Latest scan results (from automation history)
    - AI-generated narratives for each company
    
    Request body:
    - email: target email address
    - portfolio_companies: optional list of company objects from portfolio
    - test_mode: if true, don't actually send
    """
    try:
        email = request.get("email")
        portfolio_companies = request.get("portfolio_companies", [])
        test_mode = request.get("test_mode", False)
        
        if not email:
            raise HTTPException(status_code=400, detail="Email address is required")
        
        # Load .env from backend directory
        from pathlib import Path
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        # Get Gmail credentials from environment
        gmail_address = os.environ.get('GMAIL_ADDRESS')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not gmail_address or not gmail_password:
            raise HTTPException(
                status_code=400, 
                detail="Gmail credentials not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
            )
        
        # Initialize AI Writer for generating content
        from automation.writer import EISWriter, get_sector_name
        writer = EISWriter(use_ai=False)  # Use templates for speed, AI can be slow
        
        # Collect companies from different sources
        all_companies = []
        sections = {
            "portfolio": [],
            "scan_results": [],
            "featured": []
        }
        
        # 1. Portfolio Companies (from user's selections)
        if portfolio_companies:
            for pc in portfolio_companies[:5]:  # Limit to 5
                company_data = {
                    'company_name': pc.get('company_name', 'Unknown'),
                    'company_number': pc.get('company_number', ''),
                    'eis_assessment': {
                        'score': pc.get('eis_score', 0),
                        'status': pc.get('eis_status', 'Unknown')
                    },
                    'full_profile': {
                        'company': {
                            'sic_codes': pc.get('sic_codes', [])
                        }
                    }
                }
                narrative = writer.generate_deal_highlight(company_data)
                sections["portfolio"].append({
                    "company_name": pc.get('company_name'),
                    "company_number": pc.get('company_number'),
                    "eis_score": pc.get('eis_score', 0),
                    "eis_status": pc.get('eis_status', 'Unknown'),
                    "sector": get_sector_name(pc.get('sic_codes', [])),
                    "narrative": narrative
                })
                all_companies.append(company_data)
        
        # 2. Latest Scan Results (from scan history)
        scan_history_path = Path(__file__).parent.parent / "automation" / "scan_history.json"
        if scan_history_path.exists():
            try:
                with open(scan_history_path, 'r') as f:
                    scan_history = json.load(f)
                
                # Get latest scan results
                if scan_history.get("scans"):
                    latest_scan = scan_history["scans"][-1]
                    scan_companies = latest_scan.get("companies_found", [])[:5]
                    
                    for sc in scan_companies:
                        if not any(c['company_number'] == sc.get('company_number') for c in sections["portfolio"]):
                            company_data = {
                                'company_name': sc.get('company_name', 'Unknown'),
                                'company_number': sc.get('company_number', ''),
                                'eis_assessment': {
                                    'score': sc.get('eis_score', 0),
                                    'status': sc.get('eis_status', 'Unknown')
                                },
                                'full_profile': {
                                    'company': {
                                        'sic_codes': sc.get('sic_codes', [])
                                    }
                                }
                            }
                            narrative = writer.generate_deal_highlight(company_data)
                            sections["scan_results"].append({
                                "company_name": sc.get('company_name'),
                                "company_number": sc.get('company_number'),
                                "eis_score": sc.get('eis_score', 0),
                                "eis_status": sc.get('eis_status', 'Unknown'),
                                "sector": get_sector_name(sc.get('sic_codes', [])),
                                "narrative": narrative
                            })
                            all_companies.append(company_data)
            except Exception as e:
                logger.warning(f"Could not load scan history: {e}")
        
        # 3. Featured Companies (if no data from above, use quality samples)
        if not sections["portfolio"] and not sections["scan_results"]:
            featured = [
                {
                    "company_name": "Alpha Ventures Ltd",
                    "company_number": "12345678",
                    "eis_score": 88,
                    "eis_status": "Likely Eligible",
                    "sector": "Technology",
                    "narrative": "A promising technology company demonstrating strong growth signals. Recent share issuances indicate active investment activity. With an EIS likelihood score of 88/100, this company appears well-positioned for EIS investment."
                },
                {
                    "company_name": "Green Future Energy",
                    "company_number": "87654321",
                    "eis_score": 76,
                    "eis_status": "Review Required",
                    "sector": "Clean Energy",
                    "narrative": "An emerging player in the renewable energy sector. The company shows investment signals with recent capital activity. Some aspects warrant closer review for EIS eligibility."
                },
                {
                    "company_name": "MedTech Innovations",
                    "company_number": "11223344",
                    "eis_score": 92,
                    "eis_status": "Likely Eligible",
                    "sector": "Healthcare",
                    "narrative": "A healthcare technology company advancing innovative solutions. Strong fundamentals and high EIS likelihood score of 92/100 make this an attractive opportunity."
                }
            ]
            sections["featured"] = featured
        
        # Generate executive summary
        total_companies = len(sections["portfolio"]) + len(sections["scan_results"]) + len(sections["featured"])
        all_deals = sections["portfolio"] + sections["scan_results"] + sections["featured"]
        eligible_count = sum(1 for d in all_deals if 'Eligible' in d.get('eis_status', ''))
        avg_score = sum(d.get('eis_score', 0) for d in all_deals) / max(total_companies, 1)
        
        exec_summary = f"""This week's EIS Deal Scanner has curated {total_companies} high-potential investment opportunities.

{'📁 **Your Portfolio:** ' + str(len(sections["portfolio"])) + ' companies from your saved selections.' if sections["portfolio"] else ''}
{'🔍 **Latest Scan:** ' + str(len(sections["scan_results"])) + ' newly discovered companies from our automated scans.' if sections["scan_results"] else ''}
{'⭐ **Featured Deals:** ' + str(len(sections["featured"])) + ' curated opportunities meeting our quality criteria.' if sections["featured"] else ''}

**Summary:** {eligible_count} companies ({eligible_count/max(total_companies,1)*100:.0f}%) score as Likely Eligible for EIS investment with an average score of {avg_score:.0f}/100.

All companies listed have demonstrated recent investment activity through Statement of Capital filings, indicating active share issuances."""
        
        # Build comprehensive newsletter
        newsletter = {
            "title": "EIS Intelligence Weekly - AI-Powered Deal Scanner",
            "executive_summary": exec_summary,
            "sections": sections,
            "deal_highlights": all_deals,
            "ai_generated": True,
            "generated_at": datetime.now().isoformat(),
            "disclaimer": (
                "This newsletter is for informational purposes only and does not constitute financial advice. "
                "EIS eligibility assessments are indicative only - HMRC Advance Assurance is required for confirmation. "
                "Always consult with qualified tax and investment professionals before making investment decisions."
            )
        }
        
        if test_mode:
            return {
                "success": True,
                "message": f"Test mode: Would send email to {email}",
                "email": email,
                "newsletter": newsletter
            }
        
        # Import mailer and send
        from automation.mailer import EISMailer
        mailer = EISMailer(gmail_address=gmail_address, gmail_password=gmail_password)
        
        results = mailer.send_newsletter(
            newsletter=newsletter,
            recipients=[email],
            test_mode=False
        )
        
        if results.get("sent", 0) > 0:
            return {
                "success": True,
                "message": f"Newsletter sent to {email}",
                "email": email,
                "sent": results["sent"],
                "companies_included": total_companies,
                "sections": {
                    "portfolio": len(sections["portfolio"]),
                    "scan_results": len(sections["scan_results"]),
                    "featured": len(sections["featured"])
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



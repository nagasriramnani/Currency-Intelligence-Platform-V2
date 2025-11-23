"""
FastAPI Server for Currency Intelligence Platform
Exposes REST endpoints for data, analytics, forecasts, and alerts.
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
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


class ForecastResponse(BaseModel):
    currency: str
    forecast_start: Optional[str]
    historical: List[ForecastPoint]
    forecast: List[ForecastPoint]
    confidence: Optional[List[ConfidenceBandPoint]]
    insight: Optional[str]


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


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize app state on startup."""
    logger.info("Initializing Currency Intelligence Platform API...")
    
    # Initialize components
    app_state["treasury_client"] = TreasuryAPIClient()
    app_state["fmp_available"] = getattr(app_state["treasury_client"], "fmp_available", False)
    app_state["forecaster"] = CurrencyForecaster(use_prophet=True)
    app_state["anomaly_detector"] = AnomalyDetector(method="zscore", zscore_threshold=1.8)
    app_state["narrative_engine"] = NarrativeEngine()
    app_state["alert_manager"] = AlertManager()
    
    # Load initial data
    try:
        logger.info("Loading initial currency data...")
        refresh_data()
        logger.info("Initial data loaded successfully")
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
    
    currencies = filtered["currency"].unique()
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
    """Get forecast for a specific currency."""
    df = app_state.get("data")
    
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="No data available")
    
    currency = currency.upper()
    filtered = filter_dataframe_by_date(df, start_date, end_date)
    currency_display_df = filtered[filtered["currency"] == currency].copy()
    
    if currency_display_df.empty:
        currency_display_df = df[df["currency"] == currency].copy()
    
    currency_display_df = currency_display_df.sort_values("record_date")
    historical_df = currency_display_df.dropna(subset=["exchange_rate"]).tail(120)
    historical_points = [
        ForecastPoint(
            date=row["record_date"].strftime("%Y-%m-%d"),
            value=float(row["exchange_rate"])
        )
        for _, row in historical_df.iterrows()
    ]
    
    try:
        forecast_df, confidence = app_state["forecaster"].forecast_rates(
            df, currency, horizon
        )
        
        forecast_points: List[ForecastPoint] = []
        confidence_points: Optional[List[ConfidenceBandPoint]] = None
        forecast_start: Optional[str] = None
        
        if forecast_df is not None and not forecast_df.empty:
            forecast_copy = forecast_df.copy()
            forecast_copy["date"] = pd.to_datetime(forecast_copy["date"]).dt.strftime("%Y-%m-%d")
            
            forecast_points = [
                ForecastPoint(
                    date=row["date"],
                    value=float(row["forecast"])
                )
                for _, row in forecast_copy.iterrows()
            ]
            
            forecast_start = forecast_points[0].date if forecast_points else None
            
            if confidence and confidence.get("dates"):
                confidence_points = []
                for idx, date in enumerate(confidence.get("dates", [])):
                    lower = confidence["lower"][idx]
                    upper = confidence["upper"][idx]
                    mean_val = confidence["mean"][idx] if confidence.get("mean") else None
                    confidence_points.append(
                        ConfidenceBandPoint(
                            date=date,
                            lower=float(lower) if lower is not None else float(mean_val) if mean_val is not None else 0.0,
                            upper=float(upper) if upper is not None else float(mean_val) if mean_val is not None else 0.0
                        )
                    )
        else:
            forecast_points = []
            confidence_points = None
        
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
        elif not forecast_points:
            insight = "Insufficient historical data to generate a reliable forecast for this range."
        
        return ForecastResponse(
            currency=currency,
            forecast_start=forecast_start,
            historical=historical_points,
            forecast=forecast_points,
            confidence=confidence_points,
            insight=insight
        )
        
    except Exception as e:
        logger.error(f"Error generating forecast for {currency}: {e}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


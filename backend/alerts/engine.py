"""
Alert Engine

Intelligent alert orchestration with:
- Alert generation from analytics outputs
- Deduplication and fatigue control
- Severity escalation
- State tracking
- Slack delivery
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

from .models import (
    Alert, AlertType, AlertSeverity, AlertState,
    AlertContext, SuggestedAction, PortfolioContext,
    determine_severity
)
from .block_builder import SlackBlockBuilder

logger = logging.getLogger(__name__)


@dataclass
class FatigueConfig:
    """Configuration for alert fatigue control."""
    cooldown_minutes: int = 60  # Min time between same alert type
    max_per_hour: int = 10  # Max alerts per hour per currency
    escalation_threshold: int = 3  # Occurrences before escalation
    snooze_default_hours: int = 4
    dedup_window_hours: int = 24


class AlertStore:
    """
    In-memory alert store with persistence capability.
    Tracks alert history and state.
    """
    
    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = persist_path
        self._alerts: Dict[str, Alert] = {}  # alert_id -> Alert
        self._dedup_cache: Dict[str, datetime] = {}  # dedup_key -> last_sent
        self._hourly_counts: Dict[str, int] = {}  # currency -> count
        self._hour_start: datetime = datetime.utcnow()
        
        if persist_path and os.path.exists(persist_path):
            self._load()
    
    def add(self, alert: Alert) -> None:
        """Add alert to store."""
        self._alerts[alert.alert_id] = alert
        self._dedup_cache[alert.dedup_key] = alert.created_at
        
        # Track hourly counts
        self._check_hour_reset()
        self._hourly_counts[alert.currency] = self._hourly_counts.get(alert.currency, 0) + 1
        
        if self.persist_path:
            self._save()
    
    def get(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._alerts.get(alert_id)
    
    def get_by_dedup_key(self, dedup_key: str) -> Optional[Alert]:
        """Get most recent alert by deduplication key."""
        for alert in sorted(self._alerts.values(), key=lambda a: a.created_at, reverse=True):
            if alert.dedup_key == dedup_key and alert.is_active():
                return alert
        return None
    
    def get_active(self, currency: Optional[str] = None) -> List[Alert]:
        """Get all active alerts."""
        alerts = [a for a in self._alerts.values() if a.is_active()]
        if currency:
            alerts = [a for a in alerts if a.currency == currency]
        return alerts
    
    def get_recent(self, hours: int = 24) -> List[Alert]:
        """Get alerts from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self._alerts.values() if a.created_at > cutoff]
    
    def update(self, alert: Alert) -> None:
        """Update alert in store."""
        self._alerts[alert.alert_id] = alert
        if self.persist_path:
            self._save()
    
    def can_send(self, dedup_key: str, cooldown_minutes: int) -> bool:
        """Check if we can send based on cooldown."""
        last_sent = self._dedup_cache.get(dedup_key)
        if not last_sent:
            return True
        
        elapsed = (datetime.utcnow() - last_sent).total_seconds() / 60
        return elapsed >= cooldown_minutes
    
    def get_hourly_count(self, currency: str) -> int:
        """Get hourly alert count for currency."""
        self._check_hour_reset()
        return self._hourly_counts.get(currency, 0)
    
    def _check_hour_reset(self) -> None:
        """Reset hourly counts if hour changed."""
        now = datetime.utcnow()
        if (now - self._hour_start).total_seconds() >= 3600:
            self._hourly_counts = {}
            self._hour_start = now
    
    def _save(self) -> None:
        """Persist alerts to disk."""
        try:
            data = {
                alert_id: alert.to_dict()
                for alert_id, alert in self._alerts.items()
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def _load(self) -> None:
        """Load alerts from disk."""
        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
            # Note: Full deserialization would require more work
            logger.info(f"Loaded {len(data)} alerts from disk")
        except Exception as e:
            logger.error(f"Failed to load alerts: {e}")


class AlertEngine:
    """
    Main alert orchestration engine.
    
    Generates, filters, and delivers intelligent alerts.
    """
    
    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        dashboard_url: str = "http://localhost:3000",
        fatigue_config: Optional[FatigueConfig] = None,
        persist_path: Optional[str] = None
    ):
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.dashboard_url = dashboard_url
        self.fatigue_config = fatigue_config or FatigueConfig()
        
        self.store = AlertStore(persist_path)
        self.block_builder = SlackBlockBuilder(dashboard_url)
        
        # Portfolio exposures (can be updated dynamically)
        self._portfolio: Dict[str, float] = {
            "EUR": 1_000_000,
            "GBP": 500_000,
            "CAD": 250_000
        }
    
    def set_portfolio_exposure(self, currency: str, amount: float, direction: str = "long") -> None:
        """Update portfolio exposure for a currency."""
        self._portfolio[currency] = amount if direction == "long" else -amount
    
    def create_volatility_alert(
        self,
        currency: str,
        current_volatility: float,
        mean_volatility: float,
        volatility_percentile: float,
        model_name: str = "historical"
    ) -> Optional[Alert]:
        """Create volatility spike alert."""
        metrics = {
            "volatility": current_volatility,
            "mean_volatility": mean_volatility,
            "volatility_percentile": volatility_percentile,
            "change_pct": ((current_volatility / mean_volatility) - 1) * 100 if mean_volatility > 0 else 0
        }
        
        severity = determine_severity(AlertType.VOLATILITY_SPIKE, metrics)
        
        if severity == AlertSeverity.INFO and volatility_percentile < 70:
            return None  # Not worth alerting
        
        # Build context
        interpretation = f"Volatility is at the {volatility_percentile:.0f}th percentile, "
        interpretation += f"{metrics['change_pct']:.1f}% above normal levels."
        
        if severity == AlertSeverity.CRITICAL:
            interpretation += " This is an extreme spike requiring immediate attention."
        
        context = AlertContext(
            interpretation=interpretation,
            business_impact=self._estimate_impact(currency, current_volatility / 100),
            model_rationale="Historical volatility analysis detected unusual price fluctuations.",
            key_drivers=["Price variance", "Market uncertainty", "Recent news"],
            uncertainty_change="Increased significantly" if volatility_percentile > 80 else "Elevated"
        )
        
        action = SuggestedAction(
            action_type="hedge" if severity != AlertSeverity.INFO else "monitor",
            description="Consider increasing hedge ratio or reducing position size.",
            urgency="immediate" if severity == AlertSeverity.CRITICAL else "today",
            instruments=["FX Forward", "Put Option"],
            coverage_suggestion=0.75 if severity == AlertSeverity.CRITICAL else 0.5
        )
        
        return Alert(
            alert_id="",
            alert_type=AlertType.VOLATILITY_SPIKE,
            severity=severity,
            currency=currency,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            message=f"*{currency}* volatility spike detected: {current_volatility:.1f}% (vs {mean_volatility:.1f}% average)",
            metrics=metrics,
            context=context,
            suggested_action=action,
            portfolio_context=self._get_portfolio_context(currency, current_volatility / 100),
            model_name=model_name,
            model_confidence=0.85
        )
    
    def create_var_breach_alert(
        self,
        currency: str,
        var_95: float,
        var_99: float,
        cvar: float,
        threshold: float = 2.0,
        model_name: str = "parametric"
    ) -> Optional[Alert]:
        """Create VaR breach alert."""
        metrics = {
            "var_95": var_95,
            "var_99": var_99,
            "cvar": cvar,
            "threshold": threshold
        }
        
        severity = determine_severity(AlertType.VAR_BREACH, metrics)
        
        if var_95 < threshold * 0.8:
            return None  # Not near threshold
        
        context = AlertContext(
            interpretation=f"VaR at 95% confidence is {var_95:.2f}%, indicating elevated tail risk.",
            business_impact=self._estimate_impact(currency, var_95 / 100),
            model_rationale=f"{model_name.title()} VaR model based on historical return distribution.",
            key_drivers=["Return distribution", "Volatility clustering", "Tail risk"],
            uncertainty_change="VaR increased" if var_95 > threshold else "Near threshold"
        )
        
        action = SuggestedAction(
            action_type="hedge",
            description="Reduce exposure or implement tail risk hedge.",
            urgency="immediate" if severity == AlertSeverity.CRITICAL else "today",
            instruments=["FX Option", "FX Forward", "Stop-loss order"],
            coverage_suggestion=0.80 if var_99 > 3.0 else 0.60
        )
        
        alert_type = AlertType.CVAR_BREACH if cvar > var_99 * 1.2 else AlertType.VAR_BREACH
        
        return Alert(
            alert_id="",
            alert_type=alert_type,
            severity=severity,
            currency=currency,
            created_at=datetime.utcnow(),
            message=f"*{currency}* VaR breach: 95% VaR = {var_95:.2f}%, CVaR = {cvar:.2f}%",
            metrics=metrics,
            context=context,
            suggested_action=action,
            portfolio_context=self._get_portfolio_context(currency, var_95 / 100),
            model_name=model_name,
            model_confidence=0.90
        )
    
    def create_regime_change_alert(
        self,
        currency: str,
        old_regime: str,
        new_regime: str,
        confidence: float,
        model_name: str = "hmm"
    ) -> Optional[Alert]:
        """Create regime change alert."""
        metrics = {
            "old_regime": old_regime,
            "new_regime": new_regime,
            "regime_changed": old_regime != new_regime,
            "confidence": confidence
        }
        
        severity = determine_severity(AlertType.REGIME_CHANGE, metrics)
        
        if not metrics["regime_changed"]:
            return None
        
        context = AlertContext(
            interpretation=f"Market regime shifted from '{old_regime}' to '{new_regime}'.",
            business_impact="Regime shifts often precede significant price movements.",
            model_rationale="Hidden Markov Model detected state transition in volatility patterns.",
            key_drivers=["Volatility shift", "Trend change", "Correlation break"],
            uncertainty_change="Structure changed" if new_regime in ["Crisis", "High Volatility"] else "Moderate shift"
        )
        
        # Regime-specific actions
        if new_regime == "Crisis":
            action_type = "hedge"
            urgency = "immediate"
            coverage = 1.0
        elif new_regime == "High Volatility":
            action_type = "hedge"
            urgency = "today"
            coverage = 0.75
        else:
            action_type = "monitor"
            urgency = "this_week"
            coverage = 0.0
        
        action = SuggestedAction(
            action_type=action_type,
            description=f"Adjust strategy for '{new_regime}' environment.",
            urgency=urgency,
            instruments=["Dynamic hedge", "Option collar"],
            coverage_suggestion=coverage
        )
        
        return Alert(
            alert_id="",
            alert_type=AlertType.REGIME_CHANGE,
            severity=severity,
            currency=currency,
            created_at=datetime.utcnow(),
            message=f"*{currency}* regime change: {old_regime} → {new_regime} (confidence: {confidence:.0%})",
            metrics=metrics,
            context=context,
            suggested_action=action,
            model_name=model_name,
            model_confidence=confidence
        )
    
    def create_forecast_reversal_alert(
        self,
        currency: str,
        old_direction: str,
        new_direction: str,
        magnitude: float,
        model_name: str = "ensemble"
    ) -> Optional[Alert]:
        """Create forecast direction change alert."""
        metrics = {
            "old_direction": old_direction,
            "new_direction": new_direction,
            "magnitude": magnitude
        }
        
        severity = AlertSeverity.WARNING if abs(magnitude) > 0.02 else AlertSeverity.INFO
        
        context = AlertContext(
            interpretation=f"Forecast direction changed from {old_direction} to {new_direction}.",
            business_impact=f"Potential {abs(magnitude)*100:.1f}% movement anticipated.",
            model_rationale="Ensemble model detected shift in underlying trend components.",
            key_drivers=["Trend reversal", "Momentum shift", "Model agreement"],
            uncertainty_change="Direction uncertainty increased"
        )
        
        action = SuggestedAction(
            action_type="monitor",
            description="Re-evaluate existing hedge positions.",
            urgency="today",
            instruments=["Adjust hedge ratio"],
            coverage_suggestion=0.0
        )
        
        return Alert(
            alert_id="",
            alert_type=AlertType.FORECAST_REVERSAL,
            severity=severity,
            currency=currency,
            created_at=datetime.utcnow(),
            message=f"*{currency}* forecast reversal: {old_direction} → {new_direction} ({magnitude*100:+.1f}%)",
            metrics=metrics,
            context=context,
            suggested_action=action,
            model_name=model_name,
            model_confidence=0.70
        )
    
    def _estimate_impact(self, currency: str, var_pct: float) -> str:
        """Estimate financial impact based on portfolio exposure."""
        exposure = abs(self._portfolio.get(currency, 0))
        impact = exposure * var_pct
        
        if impact > 50_000:
            return f"Potential ${impact:,.0f} at risk under adverse scenario."
        elif impact > 10_000:
            return f"Moderate risk: ~${impact:,.0f} potential impact."
        else:
            return f"Limited impact: ~${impact:,.0f}."
    
    def _get_portfolio_context(self, currency: str, var_pct: float) -> PortfolioContext:
        """Build portfolio context for alert."""
        exposure = self._portfolio.get(currency, 0)
        direction = "long" if exposure >= 0 else "short"
        
        return PortfolioContext(
            currency=currency,
            exposure_amount=abs(exposure),
            exposure_direction=direction,
            estimated_impact=-abs(exposure) * var_pct if direction == "long" else abs(exposure) * var_pct,
            natural_hedges=self._find_natural_hedges(currency),
            hedge_efficiency=0.65  # Could be calculated dynamically
        )
    
    def _find_natural_hedges(self, currency: str) -> List[str]:
        """Find natural hedges in portfolio."""
        # Simple logic: opposite positions provide natural hedge
        hedges = []
        position = self._portfolio.get(currency, 0)
        
        for curr, exp in self._portfolio.items():
            if curr != currency and (position > 0 and exp < 0) or (position < 0 and exp > 0):
                hedges.append(curr)
        
        return hedges
    
    def process_alert(self, alert: Alert) -> bool:
        """
        Process alert through fatigue control and deliver if appropriate.
        
        Returns True if alert was sent, False if suppressed.
        """
        if alert is None:
            return False
        
        # Check cooldown
        if not self.store.can_send(alert.dedup_key, self.fatigue_config.cooldown_minutes):
            existing = self.store.get_by_dedup_key(alert.dedup_key)
            if existing:
                existing.occurrence_count += 1
                self.store.update(existing)
                logger.info(f"Alert {alert.dedup_key} deduplicated (count: {existing.occurrence_count})")
            return False
        
        # Check hourly limit
        if self.store.get_hourly_count(alert.currency) >= self.fatigue_config.max_per_hour:
            logger.warning(f"Hourly limit reached for {alert.currency}, suppressing alert")
            return False
        
        # Check escalation
        existing = self.store.get_by_dedup_key(alert.dedup_key)
        if existing and existing.occurrence_count >= self.fatigue_config.escalation_threshold:
            if alert.severity != AlertSeverity.CRITICAL:
                alert.severity = AlertSeverity(min(alert.severity.priority + 1, 3))
                alert.message += f" _(Escalated: {existing.occurrence_count} occurrences)_"
        
        # Store alert
        self.store.add(alert)
        
        # Send to Slack
        return self._send_to_slack(alert)
    
    def _send_to_slack(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        if not self.slack_webhook_url:
            logger.warning("No Slack webhook configured")
            return False
        
        try:
            payload = self.block_builder.build_alert_message(alert)
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent to Slack: {alert.alert_id}")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def send_daily_summary(self) -> bool:
        """Send daily alert summary."""
        alerts = self.store.get_recent(hours=24)
        
        if not alerts:
            logger.info("No alerts to summarize")
            return False
        
        payload = self.block_builder.build_summary_message(alerts, period="daily")
        
        if not self.slack_webhook_url:
            return False
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send summary: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert."""
        alert = self.store.get(alert_id)
        if alert:
            alert.acknowledge(user)
            self.store.update(alert)
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        alert = self.store.get(alert_id)
        if alert:
            alert.resolve()
            self.store.update(alert)
            return True
        return False
    
    def snooze_alert(self, alert_id: str, hours: int = 4) -> bool:
        """Snooze an alert."""
        alert = self.store.get(alert_id)
        if alert:
            alert.snooze(hours)
            self.store.update(alert)
            return True
        return False
    
    def get_active_alerts(self, currency: Optional[str] = None) -> List[Dict]:
        """Get all active alerts as dictionaries."""
        alerts = self.store.get_active(currency)
        return [a.to_dict() for a in alerts]


# Factory function
def create_alert_engine(
    slack_webhook_url: Optional[str] = None,
    dashboard_url: str = "http://localhost:3000"
) -> AlertEngine:
    """Create configured alert engine."""
    return AlertEngine(
        slack_webhook_url=slack_webhook_url,
        dashboard_url=dashboard_url,
        fatigue_config=FatigueConfig(),
        persist_path="alert_history.json"
    )

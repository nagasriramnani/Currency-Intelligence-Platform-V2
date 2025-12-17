"""
Alert Models & Taxonomy

Defines data models for intelligent alerts with severity levels,
context, explainability, and state tracking.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels with escalation rules."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Attention recommended
    CRITICAL = "critical"   # Immediate action required
    
    @property
    def color(self) -> str:
        """Slack color for severity."""
        return {
            "info": "#36a64f",      # Green
            "warning": "#ff9800",   # Orange
            "critical": "#dc3545"   # Red
        }[self.value]
    
    @property
    def emoji(self) -> str:
        """Emoji for severity."""
        return {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🔴"
        }[self.value]
    
    @property
    def priority(self) -> int:
        """Numeric priority (higher = more urgent)."""
        return {"info": 1, "warning": 2, "critical": 3}[self.value]


class AlertType(Enum):
    """Types of alerts the system can generate."""
    VOLATILITY_SPIKE = "volatility_spike"
    VAR_BREACH = "var_breach"
    CVAR_BREACH = "cvar_breach"
    FORECAST_REVERSAL = "forecast_reversal"
    MODEL_CONFIDENCE_DROP = "model_confidence_drop"
    REGIME_CHANGE = "regime_change"
    CORRELATION_SHIFT = "correlation_shift"
    PORTFOLIO_IMPACT = "portfolio_impact"
    ANOMALY_DETECTED = "anomaly_detected"
    THRESHOLD_BREACH = "threshold_breach"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return {
            "volatility_spike": "Volatility Spike Detected",
            "var_breach": "VaR Threshold Breach",
            "cvar_breach": "CVaR Threshold Breach",
            "forecast_reversal": "Forecast Direction Change",
            "model_confidence_drop": "Model Confidence Deterioration",
            "regime_change": "Market Regime Change",
            "correlation_shift": "Correlation Regime Shift",
            "portfolio_impact": "Portfolio Impact Alert",
            "anomaly_detected": "Anomaly Detected",
            "threshold_breach": "Custom Threshold Breach"
        }[self.value]


class AlertState(Enum):
    """Alert lifecycle states."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"


@dataclass
class AlertContext:
    """Contextual information explaining why an alert matters."""
    interpretation: str  # Why this matters
    business_impact: str  # Potential financial impact
    model_rationale: str  # Model-driven explanation
    key_drivers: List[str]  # What's driving this alert
    uncertainty_change: str  # How uncertainty changed
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SuggestedAction:
    """Recommended action for an alert."""
    action_type: str  # 'hedge', 'monitor', 'no_action', 'escalate'
    description: str
    urgency: str  # 'immediate', 'today', 'this_week', 'none'
    instruments: List[str] = field(default_factory=list)
    coverage_suggestion: float = 0.0  # e.g., 0.5 for 50% hedge
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class PortfolioContext:
    """Portfolio-aware alert context."""
    currency: str
    exposure_amount: float = 0.0  # USD equivalent
    exposure_direction: str = "long"  # 'long' or 'short'
    estimated_impact: float = 0.0  # Financial impact in USD
    natural_hedges: List[str] = field(default_factory=list)
    hedge_efficiency: float = 0.0  # 0-1 score
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Alert:
    """
    Intelligent alert with full context and explainability.
    """
    # Core identification
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    currency: str
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    # Content
    title: str = ""
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Intelligence
    context: Optional[AlertContext] = None
    suggested_action: Optional[SuggestedAction] = None
    portfolio_context: Optional[PortfolioContext] = None
    
    # Model info
    model_name: str = ""
    model_confidence: float = 0.0  # 0-1
    
    # State tracking
    state: AlertState = AlertState.OPEN
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    
    # Deduplication
    dedup_key: str = ""
    occurrence_count: int = 1
    
    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = self._generate_id()
        if not self.dedup_key:
            self.dedup_key = self._generate_dedup_key()
        if not self.title:
            self.title = f"{self.severity.emoji} {self.alert_type.description}"
    
    def _generate_id(self) -> str:
        """Generate unique alert ID."""
        content = f"{self.alert_type.value}_{self.currency}_{self.created_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _generate_dedup_key(self) -> str:
        """Generate deduplication key (same type + currency = same key)."""
        return f"{self.alert_type.value}_{self.currency}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "title": self.title,
            "message": self.message,
            "metrics": self.metrics,
            "context": self.context.to_dict() if self.context else None,
            "suggested_action": self.suggested_action.to_dict() if self.suggested_action else None,
            "portfolio_context": self.portfolio_context.to_dict() if self.portfolio_context else None,
            "model_name": self.model_name,
            "model_confidence": self.model_confidence,
            "state": self.state.value,
            "dedup_key": self.dedup_key,
            "occurrence_count": self.occurrence_count
        }
    
    def acknowledge(self, user: str = "system") -> None:
        """Mark alert as acknowledged."""
        self.state = AlertState.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user
    
    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.state = AlertState.RESOLVED
        self.resolved_at = datetime.utcnow()
    
    def snooze(self, duration_hours: int = 4) -> None:
        """Snooze alert for specified duration."""
        self.state = AlertState.SNOOZED
        self.snoozed_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def is_active(self) -> bool:
        """Check if alert is still active."""
        if self.state in [AlertState.RESOLVED]:
            return False
        if self.state == AlertState.SNOOZED and self.snoozed_until:
            if datetime.utcnow() < self.snoozed_until:
                return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


# Severity determination rules
SEVERITY_RULES = {
    AlertType.VOLATILITY_SPIKE: {
        "critical": lambda m: m.get("volatility_percentile", 0) > 95,
        "warning": lambda m: m.get("volatility_percentile", 0) > 80,
    },
    AlertType.VAR_BREACH: {
        "critical": lambda m: m.get("var_99", 0) > 2.5,
        "warning": lambda m: m.get("var_95", 0) > 1.5,
    },
    AlertType.CVAR_BREACH: {
        "critical": lambda m: m.get("cvar", 0) > 3.0,
        "warning": lambda m: m.get("cvar", 0) > 2.0,
    },
    AlertType.MODEL_CONFIDENCE_DROP: {
        "critical": lambda m: m.get("confidence", 1) < 0.5,
        "warning": lambda m: m.get("confidence", 1) < 0.7,
    },
    AlertType.REGIME_CHANGE: {
        "critical": lambda m: m.get("new_regime") in ["Crisis", "High Volatility"],
        "warning": lambda m: m.get("regime_changed", False),
    }
}


def determine_severity(alert_type: AlertType, metrics: Dict) -> AlertSeverity:
    """Determine severity based on alert type and metrics."""
    rules = SEVERITY_RULES.get(alert_type, {})
    
    if rules.get("critical") and rules["critical"](metrics):
        return AlertSeverity.CRITICAL
    if rules.get("warning") and rules["warning"](metrics):
        return AlertSeverity.WARNING
    
    return AlertSeverity.INFO

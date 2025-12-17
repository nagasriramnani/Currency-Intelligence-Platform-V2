"""Alert and notification modules."""

from .slack_notifier import SlackNotifier, AlertManager, AlertTrigger
from .models import Alert, AlertType, AlertSeverity, AlertState, AlertContext, SuggestedAction
from .block_builder import SlackBlockBuilder
from .engine import AlertEngine, create_alert_engine, FatigueConfig

__all__ = [
    # Original
    "SlackNotifier", "AlertManager", "AlertTrigger",
    # New intelligent alerting
    "Alert", "AlertType", "AlertSeverity", "AlertState",
    "AlertContext", "SuggestedAction",
    "SlackBlockBuilder",
    "AlertEngine", "create_alert_engine", "FatigueConfig"
]

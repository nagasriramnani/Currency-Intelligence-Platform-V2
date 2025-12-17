"""
Slack Block Kit Builder

Creates rich, interactive Slack messages using Block Kit.
Supports action buttons, metrics sections, and severity badges.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import Alert, AlertSeverity, AlertType, AlertContext, SuggestedAction

logger = logging.getLogger(__name__)


class SlackBlockBuilder:
    """
    Builds Slack Block Kit messages for intelligent alerts.
    
    Block Kit reference: https://api.slack.com/block-kit
    """
    
    def __init__(self, dashboard_url: str = "http://localhost:3000"):
        self.dashboard_url = dashboard_url
    
    def build_alert_message(self, alert: Alert) -> Dict:
        """
        Build complete Slack message for an alert.
        
        Returns Slack message payload with blocks.
        """
        blocks = []
        
        # Header with severity
        blocks.append(self._header_block(alert))
        blocks.append(self._divider())
        
        # Main message
        blocks.append(self._message_block(alert))
        
        # Metrics section
        if alert.metrics:
            blocks.append(self._metrics_block(alert))
        
        # Context/Interpretation
        if alert.context:
            blocks.append(self._context_block(alert.context))
        
        # Model rationale (explainability)
        if alert.context and alert.context.model_rationale:
            blocks.append(self._model_rationale_block(alert))
        
        # Suggested action
        if alert.suggested_action:
            blocks.append(self._action_recommendation_block(alert.suggested_action))
        
        # Portfolio context
        if alert.portfolio_context:
            blocks.append(self._portfolio_block(alert))
        
        blocks.append(self._divider())
        
        # Action buttons
        blocks.append(self._action_buttons_block(alert))
        
        # Footer
        blocks.append(self._footer_block(alert))
        
        return {
            "blocks": blocks,
            "attachments": [
                {
                    "color": alert.severity.color,
                    "blocks": []
                }
            ]
        }
    
    def _header_block(self, alert: Alert) -> Dict:
        """Create header with severity badge."""
        severity_badge = {
            AlertSeverity.INFO: "ℹ️ INFO",
            AlertSeverity.WARNING: "⚠️ WARNING",
            AlertSeverity.CRITICAL: "🔴 CRITICAL"
        }[alert.severity]
        
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_badge} | {alert.title}",
                "emoji": True
            }
        }
    
    def _divider(self) -> Dict:
        """Create divider block."""
        return {"type": "divider"}
    
    def _message_block(self, alert: Alert) -> Dict:
        """Create main message block."""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": alert.message
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📊 View Dashboard",
                    "emoji": True
                },
                "url": f"{self.dashboard_url}/risk?currency={alert.currency}",
                "action_id": "view_dashboard"
            }
        }
    
    def _metrics_block(self, alert: Alert) -> Dict:
        """Create metrics section with key values."""
        fields = []
        
        # Format common metrics
        metric_labels = {
            "var_95": ("VaR (95%)", "%"),
            "var_99": ("VaR (99%)", "%"),
            "cvar": ("CVaR", "%"),
            "volatility": ("Volatility", "%"),
            "current_rate": ("Current Rate", ""),
            "change_pct": ("Change", "%"),
            "directional_accuracy": ("Dir. Accuracy", "%")
        }
        
        for key, (label, suffix) in metric_labels.items():
            if key in alert.metrics:
                value = alert.metrics[key]
                if isinstance(value, float):
                    if suffix == "%":
                        formatted = f"{value:.2f}{suffix}"
                    else:
                        formatted = f"{value:.4f}"
                else:
                    formatted = str(value)
                
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{label}*\n{formatted}"
                })
        
        # Add model confidence if available
        if alert.model_confidence > 0:
            confidence_emoji = "🟢" if alert.model_confidence > 0.8 else "🟡" if alert.model_confidence > 0.6 else "🔴"
            fields.append({
                "type": "mrkdwn",
                "text": f"*Model Confidence*\n{confidence_emoji} {alert.model_confidence:.0%}"
            })
        
        # Limit to 10 fields (Slack limit)
        fields = fields[:10]
        
        return {
            "type": "section",
            "fields": fields
        }
    
    def _context_block(self, context: AlertContext) -> Dict:
        """Create context/interpretation block."""
        text = f"*📋 Why This Matters*\n{context.interpretation}"
        
        if context.business_impact:
            text += f"\n\n*💰 Business Impact*\n{context.business_impact}"
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    
    def _model_rationale_block(self, alert: Alert) -> Dict:
        """Create explainable AI rationale block."""
        context = alert.context
        
        text = f"*🧠 Model Rationale*\n{context.model_rationale}"
        
        if context.key_drivers:
            drivers = ", ".join(context.key_drivers[:5])
            text += f"\n\n*Key Drivers:* {drivers}"
        
        if context.uncertainty_change:
            text += f"\n*Uncertainty:* {context.uncertainty_change}"
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    
    def _action_recommendation_block(self, action: SuggestedAction) -> Dict:
        """Create suggested action block."""
        urgency_emoji = {
            "immediate": "🔴",
            "today": "🟠",
            "this_week": "🟡",
            "none": "⚪"
        }.get(action.urgency, "⚪")
        
        text = f"*💡 Suggested Action*\n{urgency_emoji} *{action.action_type.upper()}* - {action.description}"
        
        if action.coverage_suggestion > 0:
            text += f"\n*Suggested Coverage:* {action.coverage_suggestion:.0%}"
        
        if action.instruments:
            text += f"\n*Instruments:* {', '.join(action.instruments)}"
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    
    def _portfolio_block(self, alert: Alert) -> Dict:
        """Create portfolio context block."""
        pc = alert.portfolio_context
        
        direction_emoji = "📈" if pc.exposure_direction == "long" else "📉"
        
        text = f"*📊 Portfolio Impact*\n"
        text += f"{direction_emoji} {pc.currency} Exposure: ${pc.exposure_amount:,.0f} ({pc.exposure_direction})\n"
        
        if pc.estimated_impact != 0:
            impact_emoji = "🔴" if pc.estimated_impact < 0 else "🟢"
            text += f"{impact_emoji} Estimated Impact: ${pc.estimated_impact:,.0f}\n"
        
        if pc.natural_hedges:
            text += f"*Natural Hedges:* {', '.join(pc.natural_hedges)}\n"
        
        if pc.hedge_efficiency > 0:
            text += f"*Hedge Efficiency:* {pc.hedge_efficiency:.0%}"
        
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    
    def _action_buttons_block(self, alert: Alert) -> Dict:
        """Create interactive action buttons."""
        buttons = [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Acknowledge",
                    "emoji": True
                },
                "style": "primary",
                "action_id": f"ack_{alert.alert_id}",
                "value": alert.alert_id
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🔬 Run Stress Test",
                    "emoji": True
                },
                "url": f"{self.dashboard_url}/risk?currency={alert.currency}&action=stress",
                "action_id": "stress_test"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✓ Mark Hedged",
                    "emoji": True
                },
                "action_id": f"hedged_{alert.alert_id}",
                "value": alert.alert_id
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "😴 Snooze 4h",
                    "emoji": True
                },
                "action_id": f"snooze_{alert.alert_id}",
                "value": alert.alert_id
            }
        ]
        
        return {
            "type": "actions",
            "elements": buttons
        }
    
    def _footer_block(self, alert: Alert) -> Dict:
        """Create footer with metadata."""
        footer_text = (
            f"Alert ID: `{alert.alert_id}` | "
            f"Currency: {alert.currency} | "
            f"Model: {alert.model_name or 'N/A'} | "
            f"Generated: {alert.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        if alert.occurrence_count > 1:
            footer_text += f" | Occurrences: {alert.occurrence_count}"
        
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": footer_text
                }
            ]
        }
    
    def build_summary_message(
        self,
        alerts: List[Alert],
        period: str = "daily"
    ) -> Dict:
        """Build summary message for multiple alerts."""
        blocks = []
        
        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 {period.title()} Alert Summary",
                "emoji": True
            }
        })
        blocks.append(self._divider())
        
        # Count by severity
        critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
        warning = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
        info = sum(1 for a in alerts if a.severity == AlertSeverity.INFO)
        
        summary = f"*Total Alerts:* {len(alerts)}\n"
        summary += f"🔴 Critical: {critical} | ⚠️ Warning: {warning} | ℹ️ Info: {info}"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary}
        })
        
        # Top alerts
        if alerts:
            blocks.append(self._divider())
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Top Alerts:*"}
            })
            
            # Sort by severity and show top 5
            sorted_alerts = sorted(alerts, key=lambda a: a.severity.priority, reverse=True)[:5]
            
            for alert in sorted_alerts:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{alert.severity.emoji} *{alert.currency}* - {alert.alert_type.description}"
                    }
                })
        
        return {"blocks": blocks}

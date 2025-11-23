"""
Slack Alert System
Sends formatted currency intelligence alerts to Slack webhooks.
"""

import logging
import os
from typing import Dict, Optional, List
from datetime import datetime
import requests
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertTrigger(Enum):
    """Types of alert triggers."""
    YOY_MOVEMENT = "YoY Movement"
    FORECAST_DEVIATION = "Forecast Deviation"
    VOLATILITY_SPIKE = "Volatility Spike"
    ANOMALY = "Anomaly Detected"
    MANUAL = "Manual Alert"


class SlackNotifier:
    """Handles sending formatted alerts to Slack."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        
        if self.webhook_url:
            logger.info("Slack notifier initialized successfully")
        # Silently handle missing webhook - not an error, just not configured
    
    def is_configured(self) -> bool:
        """Check if Slack webhook is configured."""
        return self.webhook_url is not None and len(self.webhook_url) > 0
    
    def format_alert_message(
        self,
        trigger_type: AlertTrigger,
        currency: str,
        details: Dict,
        timestamp: Optional[str] = None
    ) -> Dict:
        """
        Format alert as Slack message payload.
        
        Args:
            trigger_type: Type of alert trigger
            currency: Currency pair (e.g., USD/EUR)
            details: Dictionary with alert details
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Slack message payload dictionary
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Choose color based on trigger type
        color_map = {
            AlertTrigger.YOY_MOVEMENT: "#0047FF",      # Sapphire blue
            AlertTrigger.FORECAST_DEVIATION: "#FACC15", # Warning yellow
            AlertTrigger.VOLATILITY_SPIKE: "#DC2626",  # Danger red
            AlertTrigger.ANOMALY: "#DC2626",           # Danger red
            AlertTrigger.MANUAL: "#616977"             # Gray
        }
        
        color = color_map.get(trigger_type, "#616977")
        
        # Build fields
        fields = []
        
        # Currency pair
        fields.append({
            "title": "Currency Pair",
            "value": currency,
            "short": True
        })
        
        # Trigger type
        fields.append({
            "title": "Alert Type",
            "value": trigger_type.value,
            "short": True
        })
        
        # Add specific details based on trigger type
        for key, value in details.items():
            if isinstance(value, (int, float)):
                if abs(value) < 100 and "rate" not in key.lower():
                    # Likely a percentage
                    display_value = f"{value:+.2f}%" if value != 0 else f"{value:.2f}%"
                else:
                    display_value = f"{value:.4f}"
            else:
                display_value = str(value)
            
            # Format key as title case
            title = key.replace("_", " ").title()
            
            fields.append({
                "title": title,
                "value": display_value,
                "short": True
            })
        
        # Generate contextual message
        so_what = self._generate_so_what(trigger_type, currency, details)
        
        # Build Slack message
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Currency Alert: {trigger_type.value}",
                    "text": f"Alert triggered for *{currency}*",
                    "fields": fields,
                    "footer": so_what,
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        return message
    
    def _generate_so_what(
        self,
        trigger_type: AlertTrigger,
        currency: str,
        details: Dict
    ) -> str:
        """
        Generate "so what" contextual message.
        
        Args:
            trigger_type: Type of trigger
            currency: Currency pair
            details: Alert details
            
        Returns:
            Contextual message string
        """
        if trigger_type == AlertTrigger.YOY_MOVEMENT:
            return f"💡 Consider reviewing current hedging strategies for {currency} exposure."
        
        elif trigger_type == AlertTrigger.FORECAST_DEVIATION:
            return f"💡 Actual movement diverged from forecast. Market conditions may have shifted for {currency}."
        
        elif trigger_type == AlertTrigger.VOLATILITY_SPIKE:
            return f"💡 Increased volatility in {currency} may impact risk calculations and position sizing."
        
        elif trigger_type == AlertTrigger.ANOMALY:
            return f"💡 Unusual activity detected in {currency}. Investigate potential market events or data quality issues."
        
        else:
            return f"💡 Review latest {currency} data and adjust strategies accordingly."
    
    def send_alert(
        self,
        trigger_type: AlertTrigger,
        currency: str,
        details: Dict,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Send alert to Slack.
        
        Args:
            trigger_type: Type of alert trigger
            currency: Currency pair
            details: Alert details
            timestamp: Optional timestamp
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("Slack webhook not configured. Cannot send alert.")
            return False
        
        try:
            # Format message
            message = self.format_alert_message(
                trigger_type,
                currency,
                details,
                timestamp
            )
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(f"Alert sent successfully for {currency}: {trigger_type.value}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Error formatting or sending alert: {e}")
            return False
    
    def send_summary(self, title: str, lines: List[str]) -> bool:
        """Send a plain-English summary message to Slack."""
        if not self.is_configured():
            logger.error("Slack webhook not configured. Cannot send summary.")
            return False
        
        body = "\n".join(f"• {line}" for line in lines)
        payload = {
            "text": f"*{title}*\n{body}"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Summary alert sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack summary: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack summary: {e}")
            return False
    
    def send_test_alert(self) -> bool:
        """
        Send a test alert to verify configuration.
        
        Returns:
            True if sent successfully, False otherwise
        """
        return self.send_alert(
            trigger_type=AlertTrigger.MANUAL,
            currency="USD/EUR",
            details={
                "message": "Test alert",
                "status": "Configuration verified"
            }
        )


class AlertManager:
    """Manages alert logic and thresholds."""
    
    def __init__(
        self,
        slack_notifier: Optional[SlackNotifier] = None,
        yoy_threshold: float = 5.0,
        volatility_threshold_std: float = 2.0,
        forecast_deviation_threshold: float = 2.0
    ):
        """
        Initialize alert manager.
        
        Args:
            slack_notifier: SlackNotifier instance
            yoy_threshold: YoY change threshold (percentage)
            volatility_threshold_std: Volatility spike threshold (std deviations)
            forecast_deviation_threshold: Forecast deviation threshold (std deviations)
        """
        self.notifier = slack_notifier or SlackNotifier()
        self.yoy_threshold = yoy_threshold
        self.volatility_threshold_std = volatility_threshold_std
        self.forecast_deviation_threshold = forecast_deviation_threshold
        
        self.alert_history: List[Dict] = []
    
    def check_yoy_alert(
        self,
        currency: str,
        yoy_change: float,
        current_rate: float
    ) -> bool:
        """
        Check if YoY movement exceeds threshold and send alert.
        
        Args:
            currency: Currency pair
            yoy_change: YoY percentage change
            current_rate: Current exchange rate
            
        Returns:
            True if alert sent
        """
        if abs(yoy_change) > self.yoy_threshold:
            details = {
                "yoy_change": yoy_change,
                "current_rate": current_rate,
                "threshold": self.yoy_threshold
            }
            
            success = self.notifier.send_alert(
                AlertTrigger.YOY_MOVEMENT,
                currency,
                details
            )
            
            if success:
                self._log_alert(AlertTrigger.YOY_MOVEMENT, currency, details)
            
            return success
        
        return False
    
    def check_volatility_alert(
        self,
        currency: str,
        current_volatility: float,
        mean_volatility: float,
        std_volatility: float
    ) -> bool:
        """
        Check if volatility spike occurs and send alert.
        
        Args:
            currency: Currency pair
            current_volatility: Current volatility
            mean_volatility: Historical mean volatility
            std_volatility: Historical std of volatility
            
        Returns:
            True if alert sent
        """
        threshold = mean_volatility + (self.volatility_threshold_std * std_volatility)
        
        if current_volatility > threshold:
            spike_pct = ((current_volatility / mean_volatility) - 1) * 100
            
            details = {
                "current_volatility": current_volatility,
                "mean_volatility": mean_volatility,
                "spike_percentage": spike_pct,
                "threshold": threshold
            }
            
            success = self.notifier.send_alert(
                AlertTrigger.VOLATILITY_SPIKE,
                currency,
                details
            )
            
            if success:
                self._log_alert(AlertTrigger.VOLATILITY_SPIKE, currency, details)
            
            return success
        
        return False
    
    def check_anomaly_alert(
        self,
        currency: str,
        anomaly_date: str,
        rate: float,
        anomaly_score: Optional[float] = None
    ) -> bool:
        """
        Send alert for detected anomaly.
        
        Args:
            currency: Currency pair
            anomaly_date: Date of anomaly
            rate: Exchange rate at anomaly
            anomaly_score: Optional anomaly score
            
        Returns:
            True if alert sent
        """
        details = {
            "anomaly_date": anomaly_date,
            "rate": rate
        }
        
        if anomaly_score:
            details["anomaly_score"] = anomaly_score
        
        success = self.notifier.send_alert(
            AlertTrigger.ANOMALY,
            currency,
            details
        )
        
        if success:
            self._log_alert(AlertTrigger.ANOMALY, currency, details)
        
        return success
    
    def _log_alert(
        self,
        trigger_type: AlertTrigger,
        currency: str,
        details: Dict
    ):
        """Log alert to history."""
        self.alert_history.append({
            "timestamp": datetime.now().isoformat(),
            "trigger_type": trigger_type.value,
            "currency": currency,
            "details": details
        })
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:]


if __name__ == "__main__":
    # Test Slack notifier
    notifier = SlackNotifier()
    
    if notifier.is_configured():
        print("Sending test alert...")
        success = notifier.send_test_alert()
        print(f"Test alert {'sent' if success else 'failed'}")
    else:
        print("Slack webhook not configured. Set SLACK_WEBHOOK_URL environment variable.")


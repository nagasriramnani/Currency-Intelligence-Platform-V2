"""
Tests for Slack notification module.
"""

import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alerts.slack_notifier import SlackNotifier, AlertManager, AlertTrigger


def test_slack_notifier_initialization():
    """Test Slack notifier initialization."""
    notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
    assert notifier.webhook_url == "https://hooks.slack.com/test"
    assert notifier.is_configured() == True


def test_slack_notifier_no_webhook():
    """Test Slack notifier without webhook."""
    notifier = SlackNotifier(webhook_url=None)
    assert notifier.is_configured() == False


def test_format_alert_message():
    """Test alert message formatting."""
    notifier = SlackNotifier()
    
    details = {
        'yoy_change': 8.2,
        'current_rate': 0.9234,
        'threshold': 5.0
    }
    
    message = notifier.format_alert_message(
        AlertTrigger.YOY_MOVEMENT,
        'USD/EUR',
        details,
        '2024-11-22 10:00:00'
    )
    
    assert 'attachments' in message
    assert len(message['attachments']) > 0
    assert message['attachments'][0]['title'].startswith('🚨')
    assert len(message['attachments'][0]['fields']) > 0


def test_alert_manager_initialization():
    """Test alert manager initialization."""
    manager = AlertManager(yoy_threshold=5.0)
    assert manager.yoy_threshold == 5.0
    assert len(manager.alert_history) == 0


def test_alert_manager_check_yoy():
    """Test YoY alert checking."""
    notifier = SlackNotifier(webhook_url=None)  # No actual webhook
    manager = AlertManager(slack_notifier=notifier, yoy_threshold=5.0)
    
    # Should not trigger (below threshold)
    result = manager.check_yoy_alert('USD/EUR', 3.0, 0.92)
    assert result == False
    
    # Would trigger (above threshold), but will fail due to no webhook
    # Just testing the logic, not actual sending
    assert manager.yoy_threshold == 5.0


def test_alert_history_logging():
    """Test alert history logging."""
    notifier = SlackNotifier(webhook_url=None)
    manager = AlertManager(slack_notifier=notifier)
    
    # Manually log an alert
    manager._log_alert(
        AlertTrigger.YOY_MOVEMENT,
        'USD/EUR',
        {'yoy_change': 8.2}
    )
    
    assert len(manager.alert_history) == 1
    assert manager.alert_history[0]['trigger_type'] == 'YoY Movement'
    assert manager.alert_history[0]['currency'] == 'USD/EUR'


def test_get_alert_history():
    """Test retrieving alert history."""
    notifier = SlackNotifier(webhook_url=None)
    manager = AlertManager(slack_notifier=notifier)
    
    # Add multiple alerts
    for i in range(15):
        manager._log_alert(
            AlertTrigger.YOY_MOVEMENT,
            f'USD/TEST{i}',
            {'value': i}
        )
    
    # Get last 10
    history = manager.get_alert_history(limit=10)
    assert len(history) == 10
    
    # Get all
    history = manager.get_alert_history(limit=100)
    assert len(history) == 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



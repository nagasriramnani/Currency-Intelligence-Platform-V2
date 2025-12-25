"""
EIS Newsletter Slack Sender

Sends the generated newsletter to Slack using webhook.
Replaces email delivery for simpler, more reliable notifications.

Uses existing SLACK_WEBHOOK_URL environment variable.

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EISSlackSender:
    """Sends EIS newsletters to Slack via webhook."""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
        
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured")
    
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    def format_newsletter_blocks(self, newsletter: Dict) -> Dict:
        """Format newsletter as Slack Block Kit message."""
        blocks = []
        
        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 {newsletter.get('title', 'EIS Deal Scanner')}",
                "emoji": True
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Executive Summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Executive Summary*\n{newsletter.get('executive_summary', '')[:500]}"
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Deal Highlights (top 5)
        highlights = newsletter.get('deal_highlights', [])[:5]
        
        if highlights:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🎯 Top Deal Highlights*"
                }
            })
            
            for deal in highlights:
                score = deal.get('eis_score', 0)
                status = deal.get('eis_status', 'Unknown')
                accounts_type = deal.get('accounts_type', 'N/A')
                size_eligible = deal.get('size_eligible', None)
                
                # Score emoji
                if score >= 70:
                    emoji = "🟢"
                elif score >= 50:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                # Size eligibility indicator
                if size_eligible is True:
                    size_text = "✓ Size OK"
                elif size_eligible is False:
                    size_text = "✗ Size Exceeds"
                else:
                    size_text = "? Size Unknown"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{deal.get('company_name', 'Unknown')}*\n{emoji} Score: {score}/100 | {status}\n📊 Accounts: {accounts_type} | {size_text}\n_{deal.get('narrative', '')[:180]}_"
                    }
                })
        
        blocks.append({"type": "divider"})
        
        # Footer
        ai_status = "🤖 AI-Generated" if newsletter.get('ai_generated') else "📝 Template-Based"
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{ai_status} | {newsletter.get('total_companies', 0)} companies analyzed | Sapphire Intelligence Platform"
                }
            ]
        })
        
        # Disclaimer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⚠️ _EIS assessments are heuristic-based. HMRC verification required for actual eligibility._"
                }
            ]
        })
        
        return {"blocks": blocks}
    
    def send_newsletter(self, newsletter: Dict) -> Dict[str, Any]:
        """Send newsletter to Slack channel."""
        if not self.is_configured():
            logger.error("Slack webhook not configured")
            return {"success": False, "error": "Slack not configured"}
        
        try:
            payload = self.format_newsletter_blocks(newsletter)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Newsletter sent to Slack successfully!")
                return {"success": True, "sent": 1}
            else:
                logger.error(f"Slack error: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Failed to send to Slack: {e}")
            return {"success": False, "error": str(e)}
    
    def send_simple_message(self, text: str) -> bool:
        """Send a simple text message to Slack."""
        if not self.is_configured():
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json={"text": text},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


def main():
    """Test the Slack sender."""
    sender = EISSlackSender()
    
    if not sender.is_configured():
        print("SLACK_WEBHOOK_URL not set in environment")
        return
    
    # Test message
    test_newsletter = {
        "title": "EIS Deal Scanner - Test",
        "executive_summary": "This is a test newsletter from the EIS automation system.",
        "total_companies": 2,
        "ai_generated": False,
        "deal_highlights": [
            {
                "company_name": "Test Company Ltd",
                "eis_score": 85,
                "eis_status": "Likely Eligible",
                "narrative": "A promising technology company showing strong investment signals."
            }
        ]
    }
    
    result = sender.send_newsletter(test_newsletter)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()

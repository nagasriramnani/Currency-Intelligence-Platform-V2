"""
EIS Newsletter Mailer

Sends the generated newsletter via email using Gmail SMTP.
Zero cost solution using Python's built-in smtplib (up to 500 emails/day).

Features:
- Gmail SMTP integration
- HTML email template with professional styling
- Subscriber list management
- Sends both HTML and plain text versions

Setup:
1. Enable "Less secure app access" in Gmail OR
2. Create an "App Password" (recommended for 2FA accounts)
   - Go to Google Account > Security > App passwords
   - Generate a password for "Mail" on "Windows Computer"

Usage:
    python mailer.py newsletter.json                    # Send to all subscribers
    python mailer.py newsletter.json --test me@email    # Test send to one address
    python mailer.py --add-subscriber new@email.com     # Add subscriber

Author: Sapphire Intelligence Platform
Version: 1.0 (Stage 1 MVP)
"""

import os
import sys
import json
import logging
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"


class EISMailer:
    """
    Sends EIS newsletter via Gmail SMTP.
    Zero cost, up to 500 emails per day.
    """
    
    # Email styling
    PRIMARY_COLOR = "#1a365d"
    ACCENT_COLOR = "#3182ce"
    SUCCESS_COLOR = "#38a169"
    WARNING_COLOR = "#dd6b20"
    
    def __init__(
        self,
        gmail_address: str = None,
        gmail_password: str = None,
        subscribers_file: str = None
    ):
        self.gmail_address = gmail_address or os.environ.get('GMAIL_ADDRESS')
        self.gmail_password = gmail_password or os.environ.get('GMAIL_APP_PASSWORD')
        self.subscribers_file = Path(subscribers_file or SUBSCRIBERS_FILE)
        
        if not self.gmail_address or not self.gmail_password:
            logger.warning(
                "Gmail credentials not configured. "
                "Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables."
            )
    
    def load_subscribers(self) -> List[str]:
        """Load subscriber list from file."""
        if not self.subscribers_file.exists():
            # Create default file
            self.save_subscribers([])
            return []
        
        with open(self.subscribers_file, 'r') as f:
            data = json.load(f)
        
        return data.get('subscribers', [])
    
    def save_subscribers(self, subscribers: List[str]):
        """Save subscriber list to file."""
        with open(self.subscribers_file, 'w') as f:
            json.dump({'subscribers': subscribers, 'updated': datetime.now().isoformat()}, f, indent=2)
    
    def add_subscriber(self, email: str) -> bool:
        """Add a subscriber to the list."""
        subscribers = self.load_subscribers()
        if email not in subscribers:
            subscribers.append(email)
            self.save_subscribers(subscribers)
            logger.info(f"Added subscriber: {email}")
            return True
        logger.info(f"Subscriber already exists: {email}")
        return False
    
    def remove_subscriber(self, email: str) -> bool:
        """Remove a subscriber from the list."""
        subscribers = self.load_subscribers()
        if email in subscribers:
            subscribers.remove(email)
            self.save_subscribers(subscribers)
            logger.info(f"Removed subscriber: {email}")
            return True
        return False
    
    def generate_html_email(self, newsletter: Dict) -> str:
        """Generate beautiful HTML email from newsletter content."""
        
        title = newsletter.get('title', 'EIS Deal Scanner')
        executive_summary = newsletter.get('executive_summary', '')
        deal_highlights = newsletter.get('deal_highlights', [])
        disclaimer = newsletter.get('disclaimer', '')
        
        # Build deal highlights HTML
        deals_html = ""
        for deal in deal_highlights[:10]:  # Limit to top 10
            score = deal.get('eis_score', 0)
            status = deal.get('eis_status', 'Unknown')
            
            # Color based on status
            if 'Eligible' in status and 'Ineligible' not in status:
                status_color = self.SUCCESS_COLOR
            elif 'Review' in status:
                status_color = self.WARNING_COLOR
            else:
                status_color = "#e53e3e"  # Red
            
            deals_html += f"""
            <div style="background: #f7fafc; border-left: 4px solid {status_color}; 
                        padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0;">
                <h3 style="margin: 0 0 10px 0; color: {self.PRIMARY_COLOR};">
                    {deal.get('company_name', 'Unknown')}
                    <span style="font-size: 14px; color: {status_color}; font-weight: normal;">
                        {score}/100 - {status}
                    </span>
                </h3>
                <p style="margin: 0 0 5px 0; color: #718096; font-size: 12px;">
                    Sector: {deal.get('sector', 'Unknown')}
                </p>
                <p style="margin: 0; color: #2d3748; line-height: 1.6;">
                    {deal.get('narrative', '')}
                </p>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
             background-color: #edf2f7; margin: 0; padding: 20px;">
    
    <div style="max-width: 600px; margin: 0 auto; background: white; 
                border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, {self.PRIMARY_COLOR}, {self.ACCENT_COLOR}); 
                    padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">
                📊 {title}
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0; font-size: 14px;">
                Sapphire Capital Partners | Automated EIS Intelligence
            </p>
        </div>
        
        <!-- Executive Summary -->
        <div style="padding: 25px; border-bottom: 1px solid #e2e8f0;">
            <h2 style="color: {self.PRIMARY_COLOR}; margin: 0 0 15px 0; font-size: 18px;">
                📋 Executive Summary
            </h2>
            <p style="color: #4a5568; line-height: 1.7; margin: 0;">
                {executive_summary}
            </p>
        </div>
        
        <!-- Deal Highlights -->
        <div style="padding: 25px;">
            <h2 style="color: {self.PRIMARY_COLOR}; margin: 0 0 15px 0; font-size: 18px;">
                🎯 This Week's Deal Highlights
            </h2>
            {deals_html}
        </div>
        
        <!-- Disclaimer -->
        <div style="background: #fff5f5; padding: 20px; border-top: 1px solid #fed7d7;">
            <p style="color: #c53030; font-size: 11px; margin: 0; line-height: 1.6;">
                ⚠️ {disclaimer}
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: {self.PRIMARY_COLOR}; padding: 20px; text-align: center;">
            <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 0;">
                Generated by Sapphire Intelligence Platform<br>
                Data Source: UK Companies House Registry<br>
                © Sapphire Capital Partners | <a href="#" style="color: white;">Unsubscribe</a>
            </p>
        </div>
        
    </div>
    
</body>
</html>
"""
        return html
    
    def generate_plain_text(self, newsletter: Dict) -> str:
        """Generate plain text version of newsletter."""
        title = newsletter.get('title', 'EIS Deal Scanner')
        executive_summary = newsletter.get('executive_summary', '')
        deal_highlights = newsletter.get('deal_highlights', [])
        disclaimer = newsletter.get('disclaimer', '')
        
        text = f"""
{title}
{'=' * len(title)}

EXECUTIVE SUMMARY
-----------------
{executive_summary}

DEAL HIGHLIGHTS
---------------
"""
        for i, deal in enumerate(deal_highlights[:10], 1):
            text += f"""
{i}. {deal.get('company_name', 'Unknown')}
   Score: {deal.get('eis_score', 0)}/100 | Status: {deal.get('eis_status', 'Unknown')}
   Sector: {deal.get('sector', 'Unknown')}
   
   {deal.get('narrative', '')}
"""
        
        text += f"""
DISCLAIMER
----------
{disclaimer}

---
Sapphire Capital Partners
Data Source: UK Companies House Registry
"""
        return text
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Send email via Gmail SMTP."""
        if not self.gmail_address or not self.gmail_password:
            logger.error("Gmail credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Sapphire Capital Partners <{self.gmail_address}>"
            msg['To'] = to_address
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_address, self.gmail_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_address}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Gmail authentication failed. "
                "Ensure you're using an App Password if 2FA is enabled."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_address}: {e}")
            return False
    
    def send_newsletter(
        self,
        newsletter: Dict,
        recipients: List[str] = None,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Send newsletter to all recipients.
        
        Args:
            newsletter: Newsletter content dictionary
            recipients: Optional list of recipients (defaults to subscribers)
            test_mode: If True, only logs what would be sent
        """
        if recipients is None:
            recipients = self.load_subscribers()
        
        if not recipients:
            logger.warning("No recipients to send to")
            return {'sent': 0, 'failed': 0, 'recipients': []}
        
        # Generate email content
        html_content = self.generate_html_email(newsletter)
        text_content = self.generate_plain_text(newsletter)
        subject = f"📊 {newsletter.get('title', 'EIS Deal Scanner')}"
        
        results = {
            'sent': 0,
            'failed': 0,
            'recipients': []
        }
        
        for recipient in recipients:
            if test_mode:
                logger.info(f"[TEST MODE] Would send to: {recipient}")
                results['sent'] += 1
                results['recipients'].append({'email': recipient, 'status': 'test'})
            else:
                success = self.send_email(recipient, subject, html_content, text_content)
                if success:
                    results['sent'] += 1
                    results['recipients'].append({'email': recipient, 'status': 'sent'})
                else:
                    results['failed'] += 1
                    results['recipients'].append({'email': recipient, 'status': 'failed'})
        
        logger.info(f"Newsletter sent: {results['sent']} successful, {results['failed']} failed")
        return results


def main():
    """Command-line interface for the mailer."""
    parser = argparse.ArgumentParser(
        description='Send EIS newsletter via Gmail SMTP'
    )
    
    # Main arguments
    parser.add_argument(
        'newsletter_file', nargs='?',
        help='Path to newsletter JSON file'
    )
    parser.add_argument(
        '--test', type=str, metavar='EMAIL',
        help='Send test email to specific address'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would be sent without actually sending'
    )
    
    # Subscriber management
    parser.add_argument(
        '--add-subscriber', type=str, metavar='EMAIL',
        help='Add email to subscriber list'
    )
    parser.add_argument(
        '--remove-subscriber', type=str, metavar='EMAIL',
        help='Remove email from subscriber list'
    )
    parser.add_argument(
        '--list-subscribers', action='store_true',
        help='List all subscribers'
    )
    
    args = parser.parse_args()
    
    mailer = EISMailer()
    
    # Handle subscriber management
    if args.add_subscriber:
        mailer.add_subscriber(args.add_subscriber)
        return
    
    if args.remove_subscriber:
        mailer.remove_subscriber(args.remove_subscriber)
        return
    
    if args.list_subscribers:
        subscribers = mailer.load_subscribers()
        print(f"\n📧 SUBSCRIBERS ({len(subscribers)} total):")
        for email in subscribers:
            print(f"  - {email}")
        return
    
    # Send newsletter
    if not args.newsletter_file:
        parser.print_help()
        return
    
    # Load newsletter
    logger.info(f"Loading newsletter from {args.newsletter_file}")
    with open(args.newsletter_file, 'r', encoding='utf-8') as f:
        newsletter = json.load(f)
    
    # Determine recipients
    if args.test:
        recipients = [args.test]
    else:
        recipients = None  # Will use subscriber list
    
    # Send
    results = mailer.send_newsletter(
        newsletter,
        recipients=recipients,
        test_mode=args.dry_run
    )
    
    print(f"\n📬 SEND RESULTS:")
    print(f"   Sent: {results['sent']}")
    print(f"   Failed: {results['failed']}")


if __name__ == "__main__":
    main()

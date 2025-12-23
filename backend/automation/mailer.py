"""
EIS Professional Newsletter Generator

Generates analyst-grade investment intelligence newsletters
following strict professional formatting guidelines.

Author: Sapphire Intelligence Platform
Version: 2.0 (Professional Edition)
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"


class ProfessionalNewsletterGenerator:
    """
    Generates professional EIS investment intelligence newsletters.
    Designed for investment professionals, treasury teams, and analysts.
    """
    
    # Professional color scheme
    HEADER_BG = "#1a365d"
    SECTION_BG = "#f8fafc"
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    BORDER_COLOR = "#e2e8f0"
    ELIGIBLE_COLOR = "#059669"
    REVIEW_COLOR = "#d97706"
    RISK_COLOR = "#dc2626"
    
    def __init__(self, gmail_address: str = None, gmail_password: str = None):
        self.gmail_address = gmail_address or os.environ.get('GMAIL_ADDRESS')
        self.gmail_password = gmail_password or os.environ.get('GMAIL_APP_PASSWORD')
    
    def generate_subject(self, data: Dict) -> str:
        """Generate professional email subject line."""
        portfolio_count = data.get('portfolio_count', 0)
        frequency = data.get('frequency', 'Weekly')
        
        return f"EIS Portfolio Intelligence — {frequency} Snapshot ({portfolio_count} Companies Reviewed)"
    
    def generate_newsletter(self, data: Dict) -> Dict[str, str]:
        """
        Generate complete newsletter with HTML and plain text versions.
        
        Args:
            data: Newsletter data containing companies, scores, insights
            
        Returns:
            Dict with 'subject', 'html', 'plain_text' keys
        """
        companies = data.get('companies', [])
        ai_insights = data.get('ai_insights', [])
        timestamp = datetime.now().strftime("%d %B %Y, %H:%M UTC")
        date_display = datetime.now().strftime("%d %B %Y")
        
        # Calculate portfolio stats
        portfolio_count = len(companies)
        eligible_count = sum(1 for c in companies if 'Eligible' in c.get('eis_status', '') and 'Ineligible' not in c.get('eis_status', ''))
        review_count = sum(1 for c in companies if 'Review' in c.get('eis_status', ''))
        risk_companies = [c for c in companies if c.get('risk_flags')]
        
        # Select spotlight companies (top 2 by score)
        spotlight = sorted(companies, key=lambda x: x.get('eis_score', 0), reverse=True)[:2]
        
        # Generate HTML
        html = self._generate_html(
            companies=companies,
            spotlight=spotlight,
            risk_companies=risk_companies,
            ai_insights=ai_insights,
            portfolio_count=portfolio_count,
            eligible_count=eligible_count,
            review_count=review_count,
            date_display=date_display,
            timestamp=timestamp
        )
        
        # Generate plain text
        plain_text = self._generate_plain_text(
            companies=companies,
            spotlight=spotlight,
            risk_companies=risk_companies,
            ai_insights=ai_insights,
            portfolio_count=portfolio_count,
            eligible_count=eligible_count,
            review_count=review_count,
            date_display=date_display,
            timestamp=timestamp
        )
        
        return {
            'subject': self.generate_subject({'portfolio_count': portfolio_count, 'frequency': data.get('frequency', 'Weekly')}),
            'html': html,
            'plain_text': plain_text
        }
    
    def _generate_html(self, **kwargs) -> str:
        """Generate professional HTML email."""
        companies = kwargs['companies']
        spotlight = kwargs['spotlight']
        risk_companies = kwargs['risk_companies']
        ai_insights = kwargs['ai_insights']
        portfolio_count = kwargs['portfolio_count']
        eligible_count = kwargs['eligible_count']
        review_count = kwargs['review_count']
        date_display = kwargs['date_display']
        timestamp = kwargs['timestamp']
        
        # Build portfolio overview rows
        portfolio_rows = ""
        for c in companies[:10]:
            status = c.get('eis_status', 'Unknown')
            score = c.get('eis_score', 0)
            
            if 'Eligible' in status and 'Ineligible' not in status:
                status_color = self.ELIGIBLE_COLOR
            elif 'Review' in status:
                status_color = self.REVIEW_COLOR
            else:
                status_color = self.RISK_COLOR
            
            risk_flag = c.get('risk_flags', ['None'])[0] if c.get('risk_flags') else 'None'
            
            portfolio_rows += f"""
            <tr style="border-bottom: 1px solid {self.BORDER_COLOR};">
                <td style="padding: 12px; font-weight: 500;">{c.get('company_name', 'Unknown')}</td>
                <td style="padding: 12px; text-align: center;">{score}/110</td>
                <td style="padding: 12px; color: {status_color}; font-weight: 500;">{status}</td>
                <td style="padding: 12px; color: {self.TEXT_SECONDARY}; font-size: 13px;">{risk_flag}</td>
                <td style="padding: 12px; color: {self.TEXT_SECONDARY}; font-size: 13px;">{c.get('sector', 'N/A')}</td>
            </tr>
            """
        
        # Build spotlight sections
        spotlight_html = ""
        for i, c in enumerate(spotlight, 1):
            news = c.get('news_summary', c.get('narrative', 'No recent updates available.'))
            sources = c.get('news_sources', [])
            sources_text = f"<p style='font-size: 12px; color: {self.TEXT_SECONDARY}; margin-top: 10px;'>Sources: {', '.join(sources[:2])}</p>" if sources else ""
            
            spotlight_html += f"""
            <div style="background: {self.SECTION_BG}; border-left: 3px solid {self.ELIGIBLE_COLOR}; 
                        padding: 20px; margin: 15px 0;">
                <h4 style="margin: 0 0 8px 0; color: {self.TEXT_PRIMARY};">
                    {c.get('company_name', 'Unknown')} — {c.get('eis_score', 0)}/110 ({c.get('eis_status', 'Unknown')})
                </h4>
                <p style="margin: 0 0 8px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">
                    Sector: {c.get('sector', 'N/A')}
                </p>
                <p style="margin: 0; color: {self.TEXT_PRIMARY}; line-height: 1.6;">
                    {news}
                </p>
                {sources_text}
            </div>
            """
        
        # Build risk section
        risk_html = ""
        for c in risk_companies[:3]:
            flags = c.get('risk_flags', ['Under review'])
            risk_html += f"""
            <div style="background: #fef2f2; border-left: 3px solid {self.RISK_COLOR}; 
                        padding: 15px; margin: 10px 0;">
                <strong>{c.get('company_name', 'Unknown')}</strong> — {', '.join(flags)}
                <br><span style="font-size: 13px; color: {self.TEXT_SECONDARY};">
                    Recommended: Seek HMRC Advance Assurance before investment
                </span>
            </div>
            """
        if not risk_html:
            risk_html = f"<p style='color: {self.ELIGIBLE_COLOR};'>No companies require immediate attention.</p>"
        
        # Build AI insights
        insights_html = ""
        for insight in ai_insights[:3]:
            insights_html += f"<li style='margin-bottom: 8px;'>{insight}</li>"
        if not insights_html:
            insights_html = """
            <li style='margin-bottom: 8px;'>EIS qualifying trade requirements remain focused on growth-oriented activities</li>
            <li style='margin-bottom: 8px;'>Technology and healthcare sectors continue to show strong EIS eligibility patterns</li>
            <li style='margin-bottom: 8px;'>Recent HMRC guidance emphasizes importance of 7-year trading age threshold</li>
            """
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EIS Portfolio Intelligence</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; 
             background-color: #f1f5f9; margin: 0; padding: 20px; color: {self.TEXT_PRIMARY};">
    
    <div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 4px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: {self.HEADER_BG}; padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.5px;">
                EIS Investment Intelligence Report
            </h1>
            <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0; font-size: 14px;">
                Prepared for: Portfolio Subscribers | Date: {date_display}
            </p>
        </div>
        
        <!-- Executive Summary -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                EXECUTIVE SUMMARY
            </h2>
            <ul style="margin: 0; padding-left: 20px; color: {self.TEXT_PRIMARY}; line-height: 1.8;">
                <li>Portfolio contains <strong>{portfolio_count} companies</strong> under active review</li>
                <li><strong>{eligible_count} companies</strong> ({int(eligible_count/max(portfolio_count,1)*100)}%) assessed as Likely Eligible for EIS</li>
                <li><strong>{review_count} companies</strong> flagged for additional compliance review</li>
                <li>Analysis based on Companies House filings, HMRC EIS criteria, and AI-enhanced screening</li>
            </ul>
        </div>
        
        <!-- Portfolio Overview -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                PORTFOLIO OVERVIEW
            </h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background: {self.SECTION_BG}; border-bottom: 2px solid {self.BORDER_COLOR};">
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Company</th>
                        <th style="padding: 12px; text-align: center; font-weight: 600;">Score</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Status</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Risk Flag</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Sector</th>
                    </tr>
                </thead>
                <tbody>
                    {portfolio_rows if portfolio_rows else '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #64748b;">No companies in portfolio</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <!-- Top Company Spotlight -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                TOP COMPANY SPOTLIGHT
            </h2>
            {spotlight_html if spotlight_html else f"<p style='color: {self.TEXT_SECONDARY};'>Add companies to portfolio to see spotlight analysis.</p>"}
        </div>
        
        <!-- Risk & Compliance Watch -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                RISK AND COMPLIANCE WATCH
            </h2>
            {risk_html}
        </div>
        
        <!-- AI Insights -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                AI MARKET INSIGHTS
            </h2>
            <ul style="margin: 0; padding-left: 20px; color: {self.TEXT_PRIMARY}; line-height: 1.8;">
                {insights_html}
            </ul>
        </div>
        
        <!-- Action Summary -->
        <div style="padding: 25px; border-bottom: 1px solid {self.BORDER_COLOR};">
            <h2 style="color: {self.TEXT_PRIMARY}; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                ACTION SUMMARY
            </h2>
            <p style="margin: 0; color: {self.TEXT_PRIMARY}; line-height: 1.7;">
                This report enables rapid screening and prioritisation of EIS investment candidates. 
                Companies scoring above 80/110 with "Likely Eligible" status can proceed to detailed due diligence. 
                Companies flagged under Risk Watch should undergo manual review or HMRC Advance Assurance before commitment.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="padding: 25px; background: {self.SECTION_BG}; font-size: 12px; color: {self.TEXT_SECONDARY};">
            <p style="margin: 0 0 8px 0;">
                <strong>Data Sources:</strong> Companies House, HMRC EIS Guidance, Extracted Statutory Filings, AI-Assisted Analysis (Tavily + HuggingFace)
            </p>
            <p style="margin: 0 0 8px 0;">
                <strong>Generated by:</strong> EIS Investment Scanner — Sapphire Intelligence Platform
            </p>
            <p style="margin: 0;">
                <strong>Timestamp:</strong> {timestamp}
            </p>
        </div>
        
    </div>
</body>
</html>"""
    
    def _generate_plain_text(self, **kwargs) -> str:
        """Generate plain text version for email clients that don't support HTML."""
        companies = kwargs['companies']
        spotlight = kwargs['spotlight']
        ai_insights = kwargs['ai_insights']
        portfolio_count = kwargs['portfolio_count']
        eligible_count = kwargs['eligible_count']
        review_count = kwargs['review_count']
        date_display = kwargs['date_display']
        timestamp = kwargs['timestamp']
        
        text = f"""
EIS INVESTMENT INTELLIGENCE REPORT
{'='*50}
Prepared for: Portfolio Subscribers
Date: {date_display}

EXECUTIVE SUMMARY
{'-'*50}
- Portfolio contains {portfolio_count} companies under active review
- {eligible_count} companies ({int(eligible_count/max(portfolio_count,1)*100)}%) assessed as Likely Eligible for EIS
- {review_count} companies flagged for additional compliance review
- Analysis based on Companies House filings, HMRC EIS criteria, and AI-enhanced screening

PORTFOLIO OVERVIEW
{'-'*50}
"""
        for c in companies[:10]:
            text += f"{c.get('company_name', 'Unknown')} | {c.get('eis_score', 0)}/110 | {c.get('eis_status', 'Unknown')} | {c.get('sector', 'N/A')}\n"
        
        text += f"""
TOP COMPANY SPOTLIGHT
{'-'*50}
"""
        for c in spotlight:
            text += f"""
{c.get('company_name', 'Unknown')} - {c.get('eis_score', 0)}/110 ({c.get('eis_status', 'Unknown')})
Sector: {c.get('sector', 'N/A')}
{c.get('news_summary', c.get('narrative', 'No recent updates available.'))}
"""
        
        text += f"""
AI MARKET INSIGHTS
{'-'*50}
"""
        for insight in (ai_insights[:3] if ai_insights else ['EIS qualifying trade requirements remain focused on growth-oriented activities', 'Technology and healthcare sectors continue to show strong EIS eligibility patterns', 'Recent HMRC guidance emphasizes importance of 7-year trading age threshold']):
            text += f"- {insight}\n"
        
        text += f"""
ACTION SUMMARY
{'-'*50}
This report enables rapid screening and prioritisation of EIS investment candidates.
Companies scoring above 80/110 with "Likely Eligible" status can proceed to detailed due diligence.
Companies flagged under Risk Watch should undergo manual review or HMRC Advance Assurance.

{'-'*50}
Data Sources: Companies House, HMRC EIS Guidance, Extracted Statutory Filings, AI-Assisted Analysis
Generated by: EIS Investment Scanner - Sapphire Intelligence Platform
Timestamp: {timestamp}
"""
        return text
    
    def send_newsletter(self, newsletter_data: Dict, recipients: List[str], test_mode: bool = False) -> Dict:
        """Send newsletter to recipients."""
        if not self.gmail_address or not self.gmail_password:
            logger.error("Gmail credentials not configured")
            return {"sent": 0, "failed": len(recipients), "error": "Gmail not configured"}
        
        # Generate newsletter content
        content = self.generate_newsletter(newsletter_data)
        
        sent = 0
        failed = 0
        
        for recipient in recipients:
            if test_mode:
                logger.info(f"[TEST MODE] Would send to: {recipient}")
                sent += 1
                continue
            
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = content['subject']
                msg['From'] = f"EIS Intelligence <{self.gmail_address}>"
                msg['To'] = recipient
                
                # Attach plain text and HTML versions
                msg.attach(MIMEText(content['plain_text'], 'plain'))
                msg.attach(MIMEText(content['html'], 'html'))
                
                # Send via Gmail SMTP
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(self.gmail_address, self.gmail_password)
                    server.send_message(msg)
                
                logger.info(f"Sent newsletter to: {recipient}")
                sent += 1
                
            except Exception as e:
                logger.error(f"Failed to send to {recipient}: {e}")
                failed += 1
        
        return {"sent": sent, "failed": failed, "subject": content['subject']}


# Backward compatibility with existing EISMailer interface
class EISMailer:
    """Wrapper for backward compatibility."""
    
    def __init__(self, gmail_address: str = None, gmail_password: str = None, subscribers_file: str = None):
        self.generator = ProfessionalNewsletterGenerator(gmail_address, gmail_password)
        self.subscribers_file = Path(subscribers_file) if subscribers_file else SUBSCRIBERS_FILE
    
    def load_subscribers(self) -> List[str]:
        if not self.subscribers_file.exists():
            return []
        with open(self.subscribers_file, 'r') as f:
            return json.load(f).get('subscribers', [])
    
    def send_newsletter(self, newsletter: Dict, recipients: List[str], test_mode: bool = False) -> Dict:
        # Convert old format to new format
        companies = newsletter.get('deal_highlights', [])
        
        # Normalize scores to /110 scale
        for c in companies:
            if c.get('eis_score', 0) <= 100:
                c['eis_score'] = int(c.get('eis_score', 0) * 1.1)
        
        data = {
            'companies': companies,
            'ai_insights': newsletter.get('ai_insights', []),
            'frequency': 'Weekly'
        }
        
        return self.generator.send_newsletter(data, recipients, test_mode)

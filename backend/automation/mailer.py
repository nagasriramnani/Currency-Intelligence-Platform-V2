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
            data: Newsletter data containing companies, scores, insights, sector_news
            
        Returns:
            Dict with 'subject', 'html', 'plain_text' keys
        """
        companies = data.get('companies', [])
        ai_insights = data.get('ai_insights', [])
        sector_news = data.get('sector_news', [])  # NEW: Sector news from Tavily
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
            sector_news=sector_news,
            portfolio_count=portfolio_count,
            eligible_count=eligible_count,
            review_count=review_count,
            date_display=date_display,
            timestamp=timestamp,
            frequency=data.get('frequency', 'Weekly')
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
        """Generate professional HTML email - clean, compact format."""
        companies = kwargs['companies']
        spotlight = kwargs['spotlight']
        risk_companies = kwargs['risk_companies']
        ai_insights = kwargs['ai_insights']
        sector_news = kwargs.get('sector_news', [])
        portfolio_count = kwargs['portfolio_count']
        eligible_count = kwargs['eligible_count']
        review_count = kwargs['review_count']
        date_display = kwargs['date_display']
        timestamp = kwargs['timestamp']
        frequency = kwargs.get('frequency', 'Weekly')
        
        # Calculate ineligible count
        ineligible_count = portfolio_count - eligible_count - review_count
        if ineligible_count < 0:
            ineligible_count = 0
        
        # Calculate risk flags
        risk_flag_count = len(risk_companies)
        
        # Next scheduled run based on frequency
        from datetime import datetime, timedelta
        next_run_date = datetime.now()
        if frequency.lower() == 'weekly':
            days_ahead = 7 - next_run_date.weekday()
            next_run_date = next_run_date + timedelta(days=days_ahead)
            next_run_text = next_run_date.strftime("Monday %d %b %Y, 08:00")
        elif frequency.lower() == 'monthly':
            if next_run_date.month == 12:
                next_run_date = next_run_date.replace(year=next_run_date.year+1, month=1, day=1)
            else:
                next_run_date = next_run_date.replace(month=next_run_date.month+1, day=1)
            next_run_text = next_run_date.strftime("1st %b %Y, 08:00")
        elif frequency.lower() == 'yearly':
            next_run_date = next_run_date.replace(year=next_run_date.year+1, month=1, day=1)
            next_run_text = next_run_date.strftime("1st Jan %Y, 08:00")
        else:
            next_run_text = "On-demand (manual trigger)"
        
        # =====================================================================
        # TOP CHANGES - Top 3 companies with recommendations
        # =====================================================================
        top_changes_html = ""
        for i, c in enumerate(spotlight[:3], 1):
            status = c.get('eis_status', 'Unknown')
            score = c.get('eis_score', 0)
            company_number = c.get('company_number', 'N/A')
            company_name = c.get('company_name', 'Unknown')
            sector = c.get('sector', 'N/A')
            
            # Determine status color
            if 'Eligible' in status and 'Ineligible' not in status:
                status_color = self.ELIGIBLE_COLOR
            elif 'Review' in status:
                status_color = self.REVIEW_COLOR
            else:
                status_color = self.RISK_COLOR
            
            # Generate recommendation
            if 'Eligible' in status and 'Ineligible' not in status:
                recommendation = "Consider HMRC Advance Assurance check"
            elif 'Review' in status:
                recommendation = "Confirm investment/EIS status and review changes"
            else:
                recommendation = "Remove from EIS candidate list"
            
            # Get risk signals
            risk_flags = c.get('risk_flags', [])
            signals_text = ""
            if risk_flags:
                for flag in risk_flags[:2]:
                    signals_text += f'<div style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 3px 0 3px 15px;">• {flag}</div>'
            else:
                signals_text = f'<div style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 3px 0 3px 15px;">• No adverse filings detected</div>'
            
            top_changes_html += f'''
            <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid {self.BORDER_COLOR};">
                <div style="font-weight: 600; color: {self.TEXT_PRIMARY}; font-size: 14px; margin-bottom: 6px;">
                    {i}) {company_name} ({company_number}) — 
                    <span style="color: {status_color};">{status}</span>
                    <span style="color: {self.HEADER_BG}; font-weight: 700;">(Score: {score}/100)</span>
                </div>
                {signals_text}
                <div style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 6px 0 0 15px; font-style: italic;">
                    → Recommended action: {recommendation}
                </div>
            </div>
            '''
        
        if not top_changes_html:
            top_changes_html = f'<p style="color: {self.TEXT_SECONDARY}; font-size: 13px;">No companies to highlight this period.</p>'
        
        # =====================================================================
        # WATCHLIST - Companies needing review
        # =====================================================================
        review_companies = [c for c in companies if 'Review' in c.get('eis_status', '')]
        watchlist_html = ""
        if review_companies:
            watchlist_html = f'<p style="color: {self.TEXT_PRIMARY}; font-size: 13px; margin-bottom: 10px;">{len(review_companies)} companies need manual verification due to missing/ambiguous signals:</p>'
            watchlist_html += '<ul style="margin: 0; padding-left: 20px;">'
            for reason in ['Sector/SIC mismatch', 'Age outside standard EIS window', 'Unclear share allotment history', 'Director changes detected', 'Missing filing history']:
                if any(reason.lower() in str(c.get('risk_flags', [])).lower() for c in review_companies):
                    watchlist_html += f'<li style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 4px 0;">{reason}</li>'
            watchlist_html += '</ul>'
        else:
            watchlist_html = f'<p style="color: {self.TEXT_SECONDARY}; font-size: 13px;">No companies currently flagged for review.</p>'
        
        # =====================================================================
        # PORTFOLIO TABLE - Compact company list
        # =====================================================================
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
            
            portfolio_rows += f'''
            <tr>
                <td style="padding: 8px 10px; border-bottom: 1px solid {self.BORDER_COLOR}; font-size: 13px; color: {self.TEXT_PRIMARY};">
                    {c.get('company_name', 'Unknown')[:30]}
                </td>
                <td style="padding: 8px 10px; border-bottom: 1px solid {self.BORDER_COLOR}; font-size: 13px; color: {self.HEADER_BG}; font-weight: 600; text-align: center;">
                    {score}/100
                </td>
                <td style="padding: 8px 10px; border-bottom: 1px solid {self.BORDER_COLOR}; font-size: 13px; color: {status_color}; text-align: center;">
                    {status}
                </td>
                <td style="padding: 8px 10px; border-bottom: 1px solid {self.BORDER_COLOR}; font-size: 12px; color: {self.TEXT_SECONDARY};">
                    {c.get('sector', 'N/A')}
                </td>
            </tr>
            '''
        
        # =====================================================================
        # BUILD COMPLETE EMAIL - Clean, minimal design
        # =====================================================================
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EIS Portfolio Intelligence</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
             background-color: #f8fafc; margin: 0; padding: 20px; color: {self.TEXT_PRIMARY}; line-height: 1.5;">
    
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 640px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <tr>
            <td>
                <!-- Header -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                       style="background: {self.HEADER_BG}; border-radius: 8px 8px 0 0;">
                    <tr>
                        <td style="padding: 24px 30px;">
                            <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 600;">
                                EIS Portfolio Intelligence
                            </h1>
                            <p style="color: rgba(255,255,255,0.8); margin: 6px 0 0 0; font-size: 13px;">
                                {frequency} Snapshot — Week of {date_display}
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- Intro -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 24px 30px 16px 30px;">
                            <p style="margin: 0; color: {self.TEXT_PRIMARY}; font-size: 14px;">
                                Hi team,
                            </p>
                            <p style="margin: 12px 0 0 0; color: {self.TEXT_SECONDARY}; font-size: 14px;">
                                Here is this period's automated EIS monitoring update based on Companies House + enrichment signals.
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- PORTFOLIO SUMMARY -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; 
                                       text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 8px;">
                                Portfolio Summary
                            </h2>
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">• Companies reviewed:</td>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_PRIMARY}; font-weight: 600;">{portfolio_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">• Likely eligible (heuristic):</td>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.ELIGIBLE_COLOR}; font-weight: 600;">{eligible_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">• Review required:</td>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.REVIEW_COLOR}; font-weight: 600;">{review_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">• Likely ineligible:</td>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.RISK_COLOR}; font-weight: 600;">{ineligible_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_SECONDARY};">• Risk flags raised:</td>
                                    <td style="padding: 4px 0; font-size: 13px; color: {self.TEXT_PRIMARY}; font-weight: 600;">{risk_flag_count}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                
                <!-- TOP CHANGES -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; 
                                       text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 8px;">
                                Top Changes (This Period)
                            </h2>
                            {top_changes_html}
                        </td>
                    </tr>
                </table>
                
                <!-- WATCHLIST -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; 
                                       text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 8px;">
                                Watchlist (Review Required)
                            </h2>
                            {watchlist_html}
                        </td>
                    </tr>
                </table>
                
                <!-- PORTFOLIO TABLE -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; 
                                       text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 8px;">
                                Full Portfolio
                            </h2>
                            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 1px solid {self.BORDER_COLOR}; border-radius: 6px;">
                                <tr style="background: {self.SECTION_BG};">
                                    <th style="padding: 10px; text-align: left; font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; font-weight: 600;">Company</th>
                                    <th style="padding: 10px; text-align: center; font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; font-weight: 600;">Score</th>
                                    <th style="padding: 10px; text-align: center; font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; font-weight: 600;">Status</th>
                                    <th style="padding: 10px; text-align: left; font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; font-weight: 600;">Sector</th>
                                </tr>
                                {portfolio_rows}
                            </table>
                        </td>
                    </tr>
                </table>
                
                <!-- DATA SOURCES -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 12px 0; font-size: 15px; font-weight: 600; 
                                       text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 8px;">
                                Data Sources Used
                            </h2>
                            <p style="margin: 0; color: {self.TEXT_SECONDARY}; font-size: 13px;">
                                • <strong>Companies House:</strong> profile, officers, PSCs, charges, filing history<br>
                                • <strong>AI Enrichment:</strong> Tavily search, HuggingFace analysis<br>
                                • <strong>Note:</strong> EIS "Likely Eligible" is an indicative score — not an official HMRC confirmation.
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- NEXT RUN -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                        <td style="padding: 0 30px 24px 30px;">
                            <p style="margin: 0; color: {self.TEXT_SECONDARY}; font-size: 13px; font-style: italic;">
                                Next scheduled run: {next_run_text}
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- Footer -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                       style="background: {self.SECTION_BG}; border-radius: 0 0 8px 8px; border-top: 1px solid {self.BORDER_COLOR};">
                    <tr>
                        <td style="padding: 20px 30px;">
                            <p style="margin: 0 0 6px 0; color: {self.TEXT_PRIMARY}; font-size: 13px;">
                                Regards,<br>
                                <strong>Sapphire Intelligence</strong> (Automated)
                            </p>
                            <p style="margin: 12px 0 0 0; font-size: 11px; color: {self.TEXT_SECONDARY};">
                                Generated: {timestamp}
                            </p>
                        </td>
                    </tr>
                </table>
                
            </td>
        </tr>
    </table>
</body>
</html>'''
    
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
            text += f"{c.get('company_name', 'Unknown')} | {c.get('eis_score', 0)}/100 | {c.get('eis_status', 'Unknown')} | {c.get('sector', 'N/A')}\n"
        
        text += f"""
TOP COMPANY SPOTLIGHT
{'-'*50}
"""
        for c in spotlight:
            text += f"""
{c.get('company_name', 'Unknown')} - {c.get('eis_score', 0)}/100 ({c.get('eis_status', 'Unknown')})
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
Companies scoring above 80/100 with "Likely Eligible" status can proceed to detailed due diligence.
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
        
        # Keep scores on /100 scale (EIS standard)
        # No conversion needed - scores are already 0-100
        
        data = {
            'companies': companies,
            'ai_insights': newsletter.get('ai_insights', []),
            'frequency': 'Weekly'
        }
        
        return self.generator.send_newsletter(data, recipients, test_mode)

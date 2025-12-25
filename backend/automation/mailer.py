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
            sector_news=sector_news,  # NEW
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
        """Generate professional HTML email with 3 sections: Portfolio, Sector News, Company News."""
        companies = kwargs['companies']
        spotlight = kwargs['spotlight']
        risk_companies = kwargs['risk_companies']
        ai_insights = kwargs['ai_insights']
        sector_news = kwargs.get('sector_news', [])  # NEW
        portfolio_count = kwargs['portfolio_count']
        eligible_count = kwargs['eligible_count']
        review_count = kwargs['review_count']
        date_display = kwargs['date_display']
        timestamp = kwargs['timestamp']
        
        # =====================================================================
        # SECTION 1: PORTFOLIO INTRO - Company cards with scores
        # =====================================================================
        portfolio_cards = ""
        for c in companies[:8]:
            status = c.get('eis_status', 'Unknown')
            score = c.get('eis_score', 0)
            
            if 'Eligible' in status and 'Ineligible' not in status:
                status_color = self.ELIGIBLE_COLOR
                badge_bg = "#dcfce7"
            elif 'Review' in status:
                status_color = self.REVIEW_COLOR
                badge_bg = "#fef3c7"
            else:
                status_color = self.RISK_COLOR
                badge_bg = "#fee2e2"
            
            # Sector badge color
            sector = c.get('sector', 'N/A')
            sector_colors = {
                'Technology': ('#8b5cf6', '#f3e8ff'),
                'Healthcare': ('#10b981', '#d1fae5'),
                'Fintech': ('#3b82f6', '#dbeafe'),
                'Clean Energy': ('#22c55e', '#dcfce7'),
                'Financial Services': ('#6366f1', '#e0e7ff'),
            }
            sector_text, sector_bg = sector_colors.get(sector, ('#64748b', '#f1f5f9'))
            
            portfolio_cards += f"""
            <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                   style="background: white; border: 1px solid {self.BORDER_COLOR}; border-radius: 8px; margin-bottom: 12px;">
                <tr>
                    <td style="padding: 16px;">
                        <table cellpadding="0" cellspacing="0" border="0" width="100%">
                            <tr>
                                <td style="font-weight: 600; color: {self.TEXT_PRIMARY}; font-size: 15px;">
                                    {c.get('company_name', 'Unknown')}
                                </td>
                                <td style="text-align: right;">
                                    <span style="background: {badge_bg}; color: {status_color}; padding: 4px 10px; 
                                                 border-radius: 12px; font-size: 11px; font-weight: 600;">
                                        {status}
                                    </span>
                                </td>
                            </tr>
                        </table>
                        <table cellpadding="0" cellspacing="0" border="0" style="margin-top: 10px;">
                            <tr>
                                <td style="padding-right: 10px;">
                                    <span style="background: {self.HEADER_BG}; color: white; padding: 6px 12px; 
                                                 border-radius: 6px; font-weight: 700; font-size: 14px; display: inline-block;">
                                        {score}/110
                                    </span>
                                </td>
                                <td style="padding-right: 10px;">
                                    <span style="background: {sector_bg}; color: {sector_text}; padding: 4px 10px; 
                                                 border-radius: 12px; font-size: 11px; font-weight: 500; display: inline-block;">
                                        {sector}
                                    </span>
                                </td>
                                <td>
                                    <span style="color: {self.TEXT_SECONDARY}; font-size: 12px;">
                                        #{c.get('company_number', 'N/A')}
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """
        
        if not portfolio_cards:
            portfolio_cards = f"""
            <div style="text-align: center; padding: 30px; color: {self.TEXT_SECONDARY};">
                <p>No companies in your portfolio yet.</p>
                <p style="font-size: 13px;">Add companies via the EIS Investment Scanner to start tracking.</p>
            </div>
            """
        
        # =====================================================================
        # SECTION 2: TOP SECTOR NEWS - EIS-eligible sector news from Tavily
        # =====================================================================
        sector_news_html = ""
        if sector_news:
            for news in sector_news[:4]:
                sector = news.get('sector', 'General')
                sector_text, sector_bg = {
                    'Technology': ('#8b5cf6', '#f3e8ff'),
                    'Healthcare': ('#10b981', '#d1fae5'),
                    'Fintech': ('#3b82f6', '#dbeafe'),
                    'Clean Energy': ('#22c55e', '#dcfce7'),
                }.get(sector, ('#64748b', '#f1f5f9'))
                
                sector_news_html += f"""
                <div style="background: {self.SECTION_BG}; border-left: 4px solid {sector_text}; 
                            padding: 16px; margin-bottom: 12px; border-radius: 0 8px 8px 0;">
                    <div style="margin-bottom: 8px;">
                        <span style="background: {sector_bg}; color: {sector_text}; padding: 3px 8px; 
                                     border-radius: 10px; font-size: 10px; font-weight: 600; text-transform: uppercase;">
                            {sector}
                        </span>
                        <span style="color: {self.TEXT_SECONDARY}; font-size: 11px; margin-left: 8px;">
                            {news.get('source', 'Unknown')}
                        </span>
                    </div>
                    <h4 style="margin: 0 0 6px 0; color: {self.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; line-height: 1.4;">
                        {news.get('title', 'No title')}
                    </h4>
                    <p style="margin: 0; color: {self.TEXT_SECONDARY}; font-size: 13px; line-height: 1.5;">
                        {news.get('content', '')[:150]}...
                    </p>
                </div>
                """
        else:
            sector_news_html = f"""
            <div style="background: {self.SECTION_BG}; padding: 20px; border-radius: 8px; text-align: center;">
                <p style="margin: 0; color: {self.TEXT_SECONDARY}; font-size: 13px;">
                    Sector news not available. Tavily API may be rate-limited.
                </p>
            </div>
            """
        
        # =====================================================================
        # SECTION 3: COMPANY-SPECIFIC NEWS - AI summaries for each company
        # =====================================================================
        company_news_html = ""
        for c in spotlight[:3]:  # Top 3 companies by score
            news = c.get('news_summary', c.get('narrative', 'No recent updates available.'))
            sources = c.get('news_sources', [])
            sources_text = f"<span style='color: {self.TEXT_SECONDARY}; font-size: 11px;'>Sources: {', '.join(sources[:2])}</span>" if sources else ""
            
            score = c.get('eis_score', 0)
            status = c.get('eis_status', 'Unknown')
            if 'Eligible' in status and 'Ineligible' not in status:
                status_color = self.ELIGIBLE_COLOR
            elif 'Review' in status:
                status_color = self.REVIEW_COLOR
            else:
                status_color = self.RISK_COLOR
            
            company_news_html += f"""
            <div style="background: white; border: 1px solid {self.BORDER_COLOR}; border-radius: 8px; 
                        padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="border-bottom: 1px solid {self.BORDER_COLOR}; padding-bottom: 12px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: {self.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;">
                            {c.get('company_name', 'Unknown')}
                        </h3>
                        <span style="background: {self.HEADER_BG}; color: white; padding: 4px 10px; 
                                     border-radius: 4px; font-weight: 700; font-size: 13px;">
                            {score}/110
                        </span>
                    </div>
                    <div style="margin-top: 6px;">
                        <span style="color: {status_color}; font-weight: 500; font-size: 13px;">{status}</span>
                        <span style="color: {self.TEXT_SECONDARY}; font-size: 12px; margin-left: 12px;">
                            {c.get('sector', 'N/A')}
                        </span>
                    </div>
                </div>
                <div style="color: {self.TEXT_PRIMARY}; font-size: 14px; line-height: 1.7;">
                    {news}
                </div>
                <div style="margin-top: 10px;">
                    {sources_text}
                </div>
            </div>
            """
        
        if not company_news_html:
            company_news_html = f"""
            <div style="text-align: center; padding: 30px; color: {self.TEXT_SECONDARY};">
                <p>Add companies to your portfolio to receive AI-powered news summaries.</p>
            </div>
            """
        
        # =====================================================================
        # BUILD COMPLETE EMAIL - Using TABLE layout for email compatibility
        # =====================================================================
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EIS Portfolio Intelligence</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; 
             background-color: #f1f5f9; margin: 0; padding: 20px; color: {self.TEXT_PRIMARY};">
    
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto;">
        <tr>
            <td>
                <!-- Header -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                       style="background: linear-gradient(135deg, {self.HEADER_BG} 0%, #4f46e5 100%); 
                              border-radius: 12px 12px 0 0;">
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <h1 style="color: white; margin: 0; font-size: 26px; font-weight: 700;">
                                EIS Intelligence Newsletter
                            </h1>
                            <p style="color: rgba(255,255,255,0.85); margin: 12px 0 0 0; font-size: 15px;">
                                Your Weekly Investment Intelligence Briefing
                            </p>
                            <p style="color: rgba(255,255,255,0.6); margin: 8px 0 0 0; font-size: 13px;">
                                {date_display}
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- Stats Bar -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                       style="background: white; border-bottom: 2px solid {self.BORDER_COLOR};">
                    <tr>
                        <td width="33%" style="padding: 25px 15px; text-align: center; border-right: 1px solid {self.BORDER_COLOR};">
                            <div style="font-size: 32px; font-weight: 800; color: {self.HEADER_BG}; line-height: 1;">{portfolio_count}</div>
                            <div style="font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px;">COMPANIES</div>
                        </td>
                        <td width="34%" style="padding: 25px 15px; text-align: center; border-right: 1px solid {self.BORDER_COLOR};">
                            <div style="font-size: 32px; font-weight: 800; color: {self.ELIGIBLE_COLOR}; line-height: 1;">{eligible_count}</div>
                            <div style="font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px;">ELIGIBLE</div>
                        </td>
                        <td width="33%" style="padding: 25px 15px; text-align: center;">
                            <div style="font-size: 32px; font-weight: 800; color: {self.REVIEW_COLOR}; line-height: 1;">{review_count}</div>
                            <div style="font-size: 11px; color: {self.TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px;">REVIEW</div>
                        </td>
                    </tr>
                </table>
                
                <!-- SECTION 1: Your Portfolio -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: white;">
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 20px 0; font-size: 20px; font-weight: 700; border-bottom: 2px solid {self.HEADER_BG}; padding-bottom: 10px;">
                                Your EIS Portfolio
                            </h2>
                            {portfolio_cards}
                        </td>
                    </tr>
                </table>
                
                <!-- SECTION 2: Top Sector News -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: #f8fafc;">
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 8px 0; font-size: 20px; font-weight: 700;">
                                UK EIS Sector Intelligence
                            </h2>
                            <p style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 0 0 20px 0;">
                                Latest funding news from EIS-eligible sectors
                            </p>
                            {sector_news_html}
                        </td>
                    </tr>
                </table>
                
                <!-- SECTION 3: Portfolio Company News -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: white;">
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="color: {self.HEADER_BG}; margin: 0 0 8px 0; font-size: 20px; font-weight: 700;">
                                AI News Summaries
                            </h2>
                            <p style="color: {self.TEXT_SECONDARY}; font-size: 13px; margin: 0 0 20px 0;">
                                AI-generated news for your top portfolio companies
                            </p>
                            {company_news_html}
                        </td>
                    </tr>
                </table>
                
                <!-- Footer -->
                <table cellpadding="0" cellspacing="0" border="0" width="100%" 
                       style="background: {self.HEADER_BG}; border-radius: 0 0 12px 12px;">
                    <tr>
                        <td style="padding: 25px 30px;">
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: rgba(255,255,255,0.7);">
                                <strong style="color: white;">Data Sources:</strong> Companies House, HMRC EIS Guidance, Tavily AI, HuggingFace
                            </p>
                            <p style="margin: 0 0 8px 0; font-size: 12px; color: rgba(255,255,255,0.7);">
                                <strong style="color: white;">Generated:</strong> {timestamp}
                            </p>
                            <p style="margin: 0; font-size: 11px; color: rgba(255,255,255,0.5);">
                                This newsletter provides indicative EIS assessments only. Consult HMRC for official eligibility.
                            </p>
                        </td>
                    </tr>
                </table>
                
            </td>
        </tr>
    </table>
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

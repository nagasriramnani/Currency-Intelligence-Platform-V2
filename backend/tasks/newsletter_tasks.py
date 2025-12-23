"""
Newsletter Background Tasks

Celery tasks for:
1. Generating company news with AI
2. Sending scheduled newsletters
3. Managing cache refresh
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Celery, fall back to sync execution if not available
try:
    from tasks.celery_app import celery_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None

# Import database models
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    get_db_session, 
    NewsletterSubscriber, 
    CompanyNewsCache,
    NewsletterHistory,
    init_database
)


def task(func):
    """Decorator that registers with Celery if available, otherwise returns function as-is."""
    if CELERY_AVAILABLE:
        return celery_app.task(func)
    return func


@task
def generate_company_news(company_number: str, company_name: str = None) -> Dict[str, Any]:
    """
    Generate AI news summary for a company.
    
    Steps:
    1. Check if cache is fresh (less than 24 hours old)
    2. If not, trigger Research Agent (Tavily search)
    3. Trigger Local Editor Agent (TinyLlama)
    4. Save to database cache
    
    Returns:
        Dict with company_number, summary, and success status
    """
    logger.info(f"Generating news for company: {company_number}")
    
    result = {
        'company_number': company_number,
        'company_name': company_name,
        'summary': None,
        'success': False,
        'from_cache': False
    }
    
    try:
        session = get_db_session()
        
        # Step 1: Check cache
        cached = session.query(CompanyNewsCache).filter_by(
            company_number=company_number
        ).order_by(CompanyNewsCache.created_at.desc()).first()
        
        if cached and cached.is_fresh():
            logger.info(f"Using cached news for {company_number}")
            result['summary'] = cached.ai_summary
            result['success'] = True
            result['from_cache'] = True
            session.close()
            return result
        
        # Step 2: Research Agent - Search for news
        from services.research_agent import ResearchAgent
        researcher = ResearchAgent()
        
        # Get company SIC codes if available
        sic_codes = None
        try:
            from data.companies_house import CompaniesHouseClient
            ch_client = CompaniesHouseClient()
            profile = ch_client.get_company_profile(company_number)
            sic_codes = profile.get('sic_codes', [])
            company_name = company_name or profile.get('company_name')
        except Exception as e:
            logger.warning(f"Could not fetch company profile: {e}")
        
        research_result = researcher.research_company(
            company_name or company_number,
            sic_codes
        )
        
        raw_news = researcher.get_raw_news_text(research_result)
        
        # Step 3: Local Editor Agent - Generate summary
        from services.local_editor_agent import LocalEditorAgent
        editor = LocalEditorAgent()
        
        summary_result = editor.generate_summary(
            company_name or company_number,
            raw_news
        )
        
        result['summary'] = summary_result.get('summary')
        result['fallback_used'] = summary_result.get('fallback_used', False)
        
        # Step 4: Save to cache
        new_cache = CompanyNewsCache(
            company_number=company_number,
            company_name=company_name,
            ai_summary=result['summary'],
            raw_news_json=json.dumps(research_result),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        session.add(new_cache)
        session.commit()
        
        result['success'] = True
        logger.info(f"Generated and cached news for {company_number}")
        
        session.close()
        
    except Exception as e:
        logger.error(f"Failed to generate news for {company_number}: {e}")
        result['error'] = str(e)
    
    return result


@task
def send_scheduled_newsletters() -> Dict[str, Any]:
    """
    Send newsletters to subscribers whose next_send_at has passed.
    
    Steps:
    1. Query subscribers where next_send_at <= now()
    2. For each subscriber, get cached news
    3. Render email template
    4. Send via SMTP
    5. Update next_send_at
    
    Returns:
        Dict with count of newsletters sent
    """
    logger.info("Running scheduled newsletter send...")
    
    result = {
        'newsletters_sent': 0,
        'failures': 0,
        'subscribers_processed': 0
    }
    
    try:
        session = get_db_session()
        
        # Find subscribers due for newsletter
        now = datetime.utcnow()
        due_subscribers = session.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.is_active == True,
            NewsletterSubscriber.next_send_at <= now
        ).all()
        
        logger.info(f"Found {len(due_subscribers)} subscribers due for newsletter")
        
        for subscriber in due_subscribers:
            result['subscribers_processed'] += 1
            
            try:
                # Get recent company news from cache
                recent_news = session.query(CompanyNewsCache).filter(
                    CompanyNewsCache.created_at >= now - timedelta(days=7)
                ).order_by(CompanyNewsCache.eis_score.desc()).limit(10).all()
                
                if not recent_news:
                    logger.warning(f"No recent news to send to {subscriber.email}")
                    continue
                
                # Render and send email
                success = send_newsletter_email(subscriber, recent_news)
                
                if success:
                    result['newsletters_sent'] += 1
                    
                    # Log the send
                    history = NewsletterHistory(
                        subscriber_id=subscriber.id,
                        companies_included=len(recent_news),
                        delivery_status='sent'
                    )
                    session.add(history)
                    
                    # Update next send time based on frequency
                    subscriber.next_send_at = calculate_next_send(subscriber.frequency)
                else:
                    result['failures'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to send to {subscriber.email}: {e}")
                result['failures'] += 1
        
        session.commit()
        session.close()
        
    except Exception as e:
        logger.error(f"Newsletter send failed: {e}")
        result['error'] = str(e)
    
    logger.info(f"Newsletter send complete: {result}")
    return result


@task
def refresh_stale_cache() -> Dict[str, Any]:
    """
    Refresh stale news cache entries.
    
    Finds companies with expired cache and regenerates their news.
    """
    logger.info("Refreshing stale cache entries...")
    
    result = {'refreshed': 0, 'errors': 0}
    
    try:
        session = get_db_session()
        
        # Find stale entries
        now = datetime.utcnow()
        stale_entries = session.query(CompanyNewsCache).filter(
            CompanyNewsCache.expires_at < now
        ).limit(10).all()
        
        for entry in stale_entries:
            try:
                generate_company_news(entry.company_number, entry.company_name)
                result['refreshed'] += 1
            except Exception as e:
                logger.error(f"Failed to refresh {entry.company_number}: {e}")
                result['errors'] += 1
        
        session.close()
        
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        result['error'] = str(e)
    
    return result


def send_newsletter_email(subscriber: NewsletterSubscriber, companies: List[CompanyNewsCache]) -> bool:
    """
    Send a newsletter email to a subscriber.
    
    Uses Jinja2 template and Gmail SMTP.
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from jinja2 import Environment, FileSystemLoader
        
        # Load email template
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('newsletter_email.html')
        
        # Render template
        html_content = template.render(
            subscriber=subscriber,
            companies=[c.to_dict() for c in companies],
            date=datetime.now().strftime('%B %d, %Y')
        )
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'EIS Investment Opportunities - ' + datetime.now().strftime('%B %d, %Y')
        msg['From'] = os.getenv('GMAIL_ADDRESS', 'noreply@example.com')
        msg['To'] = subscriber.email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send via Gmail SMTP
        gmail_user = os.getenv('GMAIL_ADDRESS')
        gmail_pass = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_pass:
            logger.warning("Gmail credentials not configured")
            return False
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
        
        logger.info(f"Newsletter sent to {subscriber.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {subscriber.email}: {e}")
        return False


def calculate_next_send(frequency: str) -> datetime:
    """Calculate next send time based on frequency."""
    now = datetime.utcnow()
    
    if frequency == 'daily':
        return now + timedelta(days=1)
    elif frequency == 'weekly':
        return now + timedelta(weeks=1)
    elif frequency == 'monthly':
        return now + timedelta(days=30)
    else:
        return now + timedelta(weeks=1)  # Default to weekly

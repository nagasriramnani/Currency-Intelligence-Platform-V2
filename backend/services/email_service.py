"""
Email Service - Async Gmail SMTP sender

Handles sending HTML/text emails via Gmail SMTP with safety validation
and rate limiting.
"""

import os
import re
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email service configuration"""
    host: str = "smtp.gmail.com"
    port: int = 587
    user: str = ""
    password: str = ""
    from_address: str = ""
    from_name: str = "Sapphire Intelligence"
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Load configuration from environment variables"""
        return cls(
            host=os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
            port=int(os.environ.get('SMTP_PORT', '587')),
            user=os.environ.get('SMTP_USER', os.environ.get('GMAIL_ADDRESS', '')),
            password=os.environ.get('SMTP_PASSWORD', os.environ.get('GMAIL_APP_PASSWORD', '')),
            from_address=os.environ.get('SMTP_FROM', os.environ.get('GMAIL_ADDRESS', '')),
            from_name=os.environ.get('SMTP_FROM_NAME', 'Sapphire Intelligence')
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.user and self.password and self.from_address)


class ContentSafetyError(Exception):
    """Raised when content contains prohibited phrases"""
    pass


class EmailService:
    """
    Async email service using Gmail SMTP.
    
    Features:
    - HTML and plain text multipart emails
    - Content safety validation
    - Rate limiting support
    - Batch sending with single connection
    """
    
    # Phrases that must not appear in any newsletter content
    BANNED_PHRASES = [
        "guaranteed tax relief",
        "hmrc approved this investment",
        "hmrc has approved",
        "certain to qualify for eis",
        "guaranteed returns",
        "risk-free investment",
        "hmrc endorses",
        "tax-free guaranteed",
        "100% tax deductible",
        "no risk",
        "surefire",
        "guaranteed profit"
    ]
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env()
        
    @property
    def is_configured(self) -> bool:
        """Check if service is ready to send"""
        return self.config.is_configured
    
    def validate_content(
        self, 
        subject: str, 
        html_body: str, 
        text_body: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate content for prohibited phrases.
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        all_content = f"{subject} {html_body} {text_body}".lower()
        
        for phrase in self.BANNED_PHRASES:
            if phrase in all_content:
                return False, f"Content contains prohibited phrase: '{phrase}'"
        
        return True, None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        skip_safety_check: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Send an email synchronously.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of the email
            text_body: Plain text version
            skip_safety_check: If True, skip content validation (use with caution)
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_configured:
            return False, "Email service not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD."
        
        # Safety check
        if not skip_safety_check:
            is_safe, error = self.validate_content(subject, html_body, text_body)
            if not is_safe:
                logger.warning(f"Content safety check failed: {error}")
                raise ContentSafetyError(error)
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_address}>"
            msg['To'] = to_email
            
            # Attach parts (text first, then HTML - HTML takes precedence)
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                server.starttls()
                server.login(self.config.user, self.config.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True, None
            
        except smtplib.SMTPAuthenticationError:
            error = "SMTP authentication failed. Check GMAIL_APP_PASSWORD."
            logger.error(error)
            return False, error
            
        except smtplib.SMTPException as e:
            error = f"SMTP error: {str(e)}"
            logger.error(error)
            return False, error
            
        except Exception as e:
            error = f"Unexpected error sending email: {str(e)}"
            logger.error(error)
            return False, error
    
    def send_batch(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str,
        max_per_batch: int = 50
    ) -> Tuple[int, int, List[str]]:
        """
        Send to multiple recipients using a single SMTP connection.
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content
            max_per_batch: Maximum emails per batch (safety limit)
            
        Returns:
            Tuple of (sent_count, failed_count, error_messages)
        """
        if not self.is_configured:
            return 0, len(recipients), ["Email service not configured"]
        
        # Safety check content once
        is_safe, error = self.validate_content(subject, html_body, text_body)
        if not is_safe:
            raise ContentSafetyError(error)
        
        # Apply batch limit
        recipients = recipients[:max_per_batch]
        
        sent = 0
        failed = 0
        errors = []
        
        try:
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                server.starttls()
                server.login(self.config.user, self.config.password)
                
                for email in recipients:
                    try:
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = f"{self.config.from_name} <{self.config.from_address}>"
                        msg['To'] = email
                        
                        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                        
                        server.send_message(msg)
                        sent += 1
                        logger.info(f"Sent to {email}")
                        
                    except Exception as e:
                        failed += 1
                        errors.append(f"{email}: {str(e)}")
                        logger.error(f"Failed to send to {email}: {e}")
                        
        except smtplib.SMTPAuthenticationError:
            return 0, len(recipients), ["SMTP authentication failed"]
            
        except Exception as e:
            # Partial failure - some may have been sent
            errors.append(f"Batch error: {str(e)}")
            
        return sent, failed, errors


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create singleton email service"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

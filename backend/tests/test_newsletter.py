"""
Newsletter System Unit Tests

Tests for:
- Newsletter agent content generation
- Email service sending and validation
- Subscription endpoint validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Import models
from models.newsletter import (
    SubscriptionCreate,
    NewsletterContent,
    CompanySummary,
    FrequencyEnum
)


# =============================================================================
# Newsletter Agent Tests
# =============================================================================

class TestNewsletterAgent:
    """Tests for newsletter_agent.py"""
    
    @pytest.fixture
    def sample_companies(self):
        return [
            CompanySummary(
                company_number="12743269",
                company_name="REVOLUT GROUP HOLDINGS LTD",
                eis_score=90,
                eis_status="Likely Eligible",
                sector="Financial Services"
            ),
            CompanySummary(
                company_number="15312606",
                company_name="AMBER LODGES LTD",
                eis_score=85,
                eis_status="Likely Eligible",
                sector="Diversified"
            )
        ]
    
    def test_fallback_content_generation(self, sample_companies):
        """Test fallback template when LLM is unavailable"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        agent.available = False  # Force fallback
        
        content = agent._generate_fallback_content("weekly", sample_companies)
        
        assert isinstance(content, NewsletterContent)
        assert "EIS Portfolio Intelligence" in content.subject
        assert "Weekly" in content.subject
        assert content.ai_generated == False
        assert "REVOLUT" in content.html_body
        assert "85" in content.text_body or "90" in content.text_body
    
    def test_fallback_with_empty_companies(self):
        """Test fallback handles empty company list"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        agent.available = False
        
        content = agent._generate_fallback_content("daily", [])
        
        assert isinstance(content, NewsletterContent)
        assert content.subject != ""
        assert "0" in content.text_body  # Should show 0 companies
    
    def test_parse_valid_json_response(self):
        """Test parsing valid JSON from LLM"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        
        valid_response = json.dumps({
            "subject": "EIS Portfolio Update",
            "preview_text": "5 new opportunities",
            "text_body": "Weekly update...",
            "html_body": "<h1>Update</h1>"
        })
        
        content = agent._parse_llm_response(valid_response)
        
        assert content is not None
        assert content.subject == "EIS Portfolio Update"
        assert content.ai_generated == True
    
    def test_parse_markdown_wrapped_json(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        
        wrapped_response = """```json
{
    "subject": "EIS Update",
    "preview_text": "Preview",
    "text_body": "Body",
    "html_body": "<p>HTML</p>"
}
```"""
        
        content = agent._parse_llm_response(wrapped_response)
        
        assert content is not None
        assert content.subject == "EIS Update"
    
    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None (triggers fallback)"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        
        invalid_response = "This is not JSON at all"
        content = agent._parse_llm_response(invalid_response)
        
        assert content is None
    
    def test_safety_check_rejects_banned_phrases(self):
        """Test that banned phrases are rejected"""
        from services.newsletter_agent import NewsletterAgent
        
        agent = NewsletterAgent()
        
        unsafe_response = json.dumps({
            "subject": "Guaranteed tax relief for investors",
            "preview_text": "Preview",
            "text_body": "Body",
            "html_body": "<p>HTML</p>"
        })
        
        content = agent._parse_llm_response(unsafe_response)
        
        # Should return None due to safety check failure
        assert content is None


# =============================================================================
# Email Service Tests
# =============================================================================

class TestEmailService:
    """Tests for email_service.py"""
    
    def test_content_safety_validation_passes(self):
        """Test that safe content passes validation"""
        from services.email_service import EmailService
        
        service = EmailService()
        
        is_safe, error = service.validate_content(
            subject="EIS Portfolio Update",
            html_body="<p>Your weekly EIS opportunities</p>",
            text_body="Weekly opportunities from Sapphire Intelligence"
        )
        
        assert is_safe == True
        assert error is None
    
    def test_content_safety_validation_fails(self):
        """Test that unsafe content fails validation"""
        from services.email_service import EmailService
        
        service = EmailService()
        
        is_safe, error = service.validate_content(
            subject="Guaranteed tax relief available!",
            html_body="<p>Get guaranteed returns</p>",
            text_body="Risk-free investment"
        )
        
        assert is_safe == False
        assert "prohibited phrase" in error.lower()
    
    def test_is_configured_false_without_env(self):
        """Test that service reports unconfigured without env vars"""
        from services.email_service import EmailService, EmailConfig
        
        config = EmailConfig(
            host="smtp.gmail.com",
            port=587,
            user="",
            password="",
            from_address=""
        )
        service = EmailService(config)
        
        assert service.is_configured == False
    
    def test_is_configured_true_with_env(self):
        """Test that service reports configured with env vars"""
        from services.email_service import EmailService, EmailConfig
        
        config = EmailConfig(
            host="smtp.gmail.com",
            port=587,
            user="test@gmail.com",
            password="app-password",
            from_address="test@gmail.com"
        )
        service = EmailService(config)
        
        assert service.is_configured == True
    
    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email send with mocked SMTP"""
        from services.email_service import EmailService, EmailConfig
        
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = Mock(return_value=False)
        
        config = EmailConfig(
            host="smtp.gmail.com",
            port=587,
            user="test@gmail.com",
            password="password",
            from_address="test@gmail.com"
        )
        service = EmailService(config)
        
        success, error = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<p>Test</p>",
            text_body="Test"
        )
        
        assert success == True
        assert error is None
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()


# =============================================================================
# Subscription Validation Tests
# =============================================================================

class TestSubscriptionValidation:
    """Tests for subscription request validation"""
    
    def test_valid_subscription_create(self):
        """Test valid subscription request"""
        sub = SubscriptionCreate(
            email="test@example.com",
            frequency=FrequencyEnum.WEEKLY
        )
        
        assert sub.email == "test@example.com"
        assert sub.frequency == FrequencyEnum.WEEKLY
    
    def test_email_normalized(self):
        """Test email is normalized to lowercase"""
        sub = SubscriptionCreate(
            email="TEST@EXAMPLE.COM",
            frequency=FrequencyEnum.DAILY
        )
        
        assert sub.email == "test@example.com"
    
    def test_invalid_email_rejected(self):
        """Test invalid email format is rejected"""
        with pytest.raises(ValueError):
            SubscriptionCreate(
                email="not-an-email",
                frequency=FrequencyEnum.WEEKLY
            )
    
    def test_invalid_frequency_rejected(self):
        """Test invalid frequency is rejected"""
        with pytest.raises(ValueError):
            SubscriptionCreate(
                email="test@example.com",
                frequency="yearly"  # Invalid
            )


# =============================================================================
# NewsletterContent Safety Tests
# =============================================================================

class TestNewsletterContentSafety:
    """Tests for content safety in NewsletterContent model"""
    
    def test_banned_phrase_in_subject_fails(self):
        """Test that banned phrases in subject are caught"""
        with pytest.raises(ValueError) as exc_info:
            NewsletterContent(
                subject="HMRC approved this investment",
                preview_text="Safe preview",
                text_body="Safe body",
                html_body="<p>Safe HTML</p>"
            )
        
        assert "prohibited phrase" in str(exc_info.value).lower()
    
    def test_banned_phrase_in_body_fails(self):
        """Test that banned phrases in body are caught"""
        with pytest.raises(ValueError):
            NewsletterContent(
                subject="Safe subject",
                preview_text="Safe preview",
                text_body="This is a risk-free investment opportunity",
                html_body="<p>Safe HTML</p>"
            )
    
    def test_safe_content_passes(self):
        """Test that safe content passes validation"""
        content = NewsletterContent(
            subject="EIS Portfolio Update - January 2026",
            preview_text="5 new opportunities reviewed",
            text_body="Your weekly update includes indicative EIS scores.",
            html_body="<p>EIS scores are indicative only.</p>"
        )
        
        assert content.subject == "EIS Portfolio Update - January 2026"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

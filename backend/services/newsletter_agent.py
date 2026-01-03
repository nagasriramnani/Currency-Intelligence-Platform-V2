"""
Newsletter Agent - Ollama-powered content generation

Uses llama3.2 to generate structured newsletter content while preserving
the existing email format and style.
"""

import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.newsletter import (
    NewsletterContent,
    CompanySummary
)

logger = logging.getLogger(__name__)


class NewsletterAgent:
    """
    Generates newsletter content using Ollama LLM.
    Falls back to template-based generation if LLM fails.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.ollama_url = ollama_url
        self.model = model
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if Ollama is available"""
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                self.available = any(m.get("name", "").startswith(self.model) for m in models)
                if self.available:
                    logger.info(f"NewsletterAgent: Ollama available with {self.model}")
                else:
                    logger.warning(f"NewsletterAgent: {self.model} not found in Ollama")
        except Exception as e:
            logger.warning(f"NewsletterAgent: Ollama not available - {e}")
            self.available = False
    
    async def compose_newsletter(
        self,
        frequency: str,
        companies: List[CompanySummary],
        recipient_type: str = "professional investor"
    ) -> NewsletterContent:
        """
        Generate newsletter content using Ollama.
        
        Args:
            frequency: Newsletter frequency (daily/weekly/monthly)
            companies: List of companies to include
            recipient_type: Type of recipient for tone adjustment
            
        Returns:
            NewsletterContent with subject, preview, text_body, html_body
        """
        if not self.available or not companies:
            return self._generate_fallback_content(frequency, companies)
        
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(frequency, companies, recipient_type)
            
            # Call Ollama
            response = await self._call_ollama(system_prompt, user_prompt)
            
            # Parse JSON response
            content = self._parse_llm_response(response)
            if content:
                return content
            else:
                logger.warning("Failed to parse LLM response, using fallback")
                return self._generate_fallback_content(frequency, companies)
                
        except Exception as e:
            logger.error(f"NewsletterAgent error: {e}")
            return self._generate_fallback_content(frequency, companies)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for Ollama"""
        return """You are an EIS investment newsletter assistant for professional investors in the UK.

IMPORTANT RULES:
1. Do NOT give personalised tax advice.
2. Do NOT claim HMRC has approved any investment.
3. Do NOT use phrases like "guaranteed tax relief" or "certain to qualify".
4. Use neutral, professional tone and UK spelling.
5. Always note that EIS scores are indicative, not official HMRC confirmation.

You will receive a list of companies with EIS scores and eligibility status.
Generate concise, factual newsletter content summarising key investment opportunities.

RESPOND ONLY with valid JSON in this exact format:
{
  "subject": "string (max 100 chars)",
  "preview_text": "string (max 200 chars)", 
  "text_body": "string (plain text version)",
  "html_body": "string (HTML formatted version)"
}

The HTML body should use simple HTML (h1, h2, p, ul, li, strong, em, table) for email compatibility."""

    def _build_user_prompt(
        self, 
        frequency: str, 
        companies: List[CompanySummary],
        recipient_type: str
    ) -> str:
        """Build the user prompt with company data"""
        
        # Format companies as compact JSON
        company_data = []
        for c in companies[:10]:  # Limit to 10 companies
            company_data.append({
                "name": c.company_name,
                "number": c.company_number,
                "score": c.eis_score,
                "status": c.eis_status,
                "sector": c.sector,
                "revenue": c.revenue or "N/A",
                "news": c.news_summary[:200] if c.news_summary else None
            })
        
        week_of = datetime.now().strftime("%d %B %Y")
        
        return f"""Generate a {frequency} EIS portfolio newsletter for {recipient_type}s.

Week of: {week_of}
Companies ({len(company_data)} total):

{json.dumps(company_data, indent=2)}

Requirements:
- Subject line should mention "EIS Portfolio" and the date/frequency
- Preview text should highlight top opportunity
- Text body: Plain version for email clients without HTML
- HTML body: Formatted version with sections for each company

Include these sections:
1. Portfolio Summary (counts by status)
2. Top Opportunities (highest scores)
3. AI Intelligence (company news if available)
4. Disclaimer about EIS being indicative

Return ONLY valid JSON."""

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama API"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent JSON
                        "num_predict": 4000
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            else:
                raise Exception(f"Ollama returned {response.status_code}")
    
    def _parse_llm_response(self, response: str) -> Optional[NewsletterContent]:
        """Parse LLM response as JSON"""
        try:
            # Try to extract JSON from response
            # Sometimes LLM wraps it in markdown code blocks
            json_str = response.strip()
            
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            data = json.loads(json_str)
            
            # Validate with Pydantic (includes safety checks)
            return NewsletterContent(
                subject=data.get("subject", "EIS Portfolio Update"),
                preview_text=data.get("preview_text", "Your weekly EIS opportunities"),
                text_body=data.get("text_body", ""),
                html_body=data.get("html_body", ""),
                ai_generated=True
            )
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return None
        except ValueError as e:
            # Pydantic validation failed (likely safety check)
            logger.warning(f"Content validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    def _generate_fallback_content(
        self, 
        frequency: str, 
        companies: List[CompanySummary]
    ) -> NewsletterContent:
        """Generate newsletter using template (no LLM)"""
        
        week_of = datetime.now().strftime("%d %B %Y")
        
        # Count by status
        likely_eligible = sum(1 for c in companies if "Eligible" in c.eis_status)
        review_required = sum(1 for c in companies if "Review" in c.eis_status)
        not_eligible = len(companies) - likely_eligible - review_required
        
        # Subject
        subject = f"EIS Portfolio Intelligence - {frequency.title()} Snapshot — {week_of}"
        
        # Preview
        if companies:
            top = max(companies, key=lambda c: c.eis_score)
            preview = f"{len(companies)} companies reviewed. Top: {top.company_name} ({top.eis_score}/100)"
        else:
            preview = "Your EIS portfolio update is ready"
        
        # Text body
        text_lines = [
            f"EIS Portfolio Intelligence",
            f"{frequency.title()} Snapshot — Week of {week_of}",
            "",
            "Portfolio Summary",
            f"• Companies reviewed: {len(companies)}",
            f"• Likely eligible: {likely_eligible}",
            f"• Review required: {review_required}",
            f"• Not eligible: {not_eligible}",
            "",
            "Top Companies:",
        ]
        
        for c in sorted(companies, key=lambda x: x.eis_score, reverse=True)[:5]:
            text_lines.append(f"• {c.company_name} ({c.company_number}) — {c.eis_status} ({c.eis_score}/100)")
            if c.news_summary:
                text_lines.append(f"  News: {c.news_summary[:100]}...")
        
        text_lines.extend([
            "",
            "---",
            "Note: EIS 'Likely Eligible' is an indicative score — not official HMRC confirmation.",
            "",
            "Regards,",
            "Sapphire Intelligence (Automated)"
        ])
        
        text_body = "\n".join(text_lines)
        
        # HTML body (preserving existing format)
        html_body = self._generate_html_template(frequency, week_of, companies)
        
        return NewsletterContent(
            subject=subject,
            preview_text=preview,
            text_body=text_body,
            html_body=html_body,
            ai_generated=False
        )
    
    def _generate_html_template(
        self, 
        frequency: str, 
        week_of: str, 
        companies: List[CompanySummary]
    ) -> str:
        """Generate HTML email using existing template style"""
        
        likely_eligible = sum(1 for c in companies if "Eligible" in c.eis_status)
        review_required = sum(1 for c in companies if "Review" in c.eis_status)
        not_eligible = len(companies) - likely_eligible - review_required
        
        # Company rows for the table
        company_rows = ""
        for c in sorted(companies, key=lambda x: x.eis_score, reverse=True):
            status_color = "#10B981" if "Eligible" in c.eis_status else "#F59E0B" if "Review" in c.eis_status else "#EF4444"
            company_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{c.company_name[:40]}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">{c.eis_score}/100</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: {status_color}; font-weight: 600;">{c.eis_status}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{c.sector}</td>
            </tr>"""
        
        # AI Intelligence section
        ai_section = ""
        for c in sorted(companies, key=lambda x: x.eis_score, reverse=True)[:5]:
            if c.news_summary:
                sources = ", ".join(c.news_sources[:2]) if c.news_sources else "Various sources"
                ai_section += f"""
                <div style="margin-bottom: 24px; padding: 16px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #6366F1;">
                    <h3 style="margin: 0 0 8px 0; color: #111827;">
                        {c.company_name} ({c.company_number}) 
                        <span style="color: #6366F1;">{c.eis_score}/100</span>
                    </h3>
                    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px;">
                        💰 Revenue: {c.revenue or 'N/A'} | 🏢 Sector: {c.sector} | 📊 Status: {c.eis_status}
                    </p>
                    <p style="margin: 0 0 8px 0; color: #374151;">{c.news_summary[:300]}...</p>
                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">📰 Sources: {sources}</p>
                </div>"""
        
        if not ai_section:
            ai_section = "<p style='color: #6b7280;'>No AI-generated intelligence available for this run.</p>"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 800px; margin: 0 auto; padding: 20px;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); padding: 32px; border-radius: 12px; margin-bottom: 24px;">
        <h1 style="color: white; margin: 0; font-size: 28px;">EIS Portfolio Intelligence</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 16px;">
            {frequency.title()} Snapshot — Week of {week_of}
        </p>
    </div>
    
    <p>Hi team,</p>
    <p>Here is this period's automated EIS monitoring update based on Companies House + enrichment signals.</p>
    
    <!-- Portfolio Summary -->
    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 24px 0;">
        <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 18px;">Portfolio Summary</h2>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Companies reviewed: <strong>{len(companies)}</strong></li>
            <li>Likely eligible (heuristic): <strong style="color: #10B981;">{likely_eligible}</strong></li>
            <li>Review required: <strong style="color: #F59E0B;">{review_required}</strong></li>
            <li>Likely ineligible: <strong style="color: #EF4444;">{not_eligible}</strong></li>
        </ul>
    </div>
    
    <!-- AI Intelligence Section -->
    <h2 style="color: #111827; font-size: 20px; margin-top: 32px;">
        🤖 AI Company Intelligence
    </h2>
    <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
        Real-time news research powered by Tavily AI
    </p>
    {ai_section}
    
    <!-- Full Portfolio Table -->
    <h2 style="color: #111827; font-size: 20px; margin-top: 32px;">Full Portfolio</h2>
    <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
        <thead>
            <tr style="background: #f9fafb;">
                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Company</th>
                <th style="padding: 12px; text-align: center; font-weight: 600; color: #374151;">Score</th>
                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Status</th>
                <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Sector</th>
            </tr>
        </thead>
        <tbody>
            {company_rows}
        </tbody>
    </table>
    
    <!-- Data Sources -->
    <div style="margin-top: 32px; padding: 16px; background: #fffbeb; border-radius: 8px; border-left: 4px solid #F59E0B;">
        <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 14px;">Data Sources Used</h3>
        <ul style="margin: 0; padding-left: 20px; color: #92400E; font-size: 13px;">
            <li>Companies House: profile, officers, PSCs, charges, filing history</li>
            <li>AI Enrichment: Tavily search, HuggingFace analysis</li>
            <li><strong>Note:</strong> EIS "Likely Eligible" is an indicative score — not official HMRC confirmation.</li>
        </ul>
    </div>
    
    <!-- Footer -->
    <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 13px;">
        <p>Regards,<br><strong>Sapphire Intelligence</strong> (Automated)</p>
        <p style="font-size: 12px;">Generated: {datetime.now().strftime("%d %B %Y, %H:%M")} UTC</p>
    </div>
    
</body>
</html>
"""


# Singleton instance
_newsletter_agent = None

def get_newsletter_agent() -> NewsletterAgent:
    """Get or create singleton newsletter agent"""
    global _newsletter_agent
    if _newsletter_agent is None:
        _newsletter_agent = NewsletterAgent()
    return _newsletter_agent

"""
EIS Newsletter Writer

Transforms raw company data into engaging narrative content for the newsletter.
Generates "Deal Highlight" stories that turn statistics into readable text.

Two modes available:
1. Template-based generation (zero cost, always works)
2. AI-powered generation (optional, uses Hugging Face API)

Usage:
    python writer.py scan_results.json              # Generate narratives
    python writer.py scan_results.json --ai         # Use AI enhancement
    python writer.py scan_results.json --output newsletter.json

Author: Sapphire Intelligence Platform
Version: 1.0 (Stage 1 MVP)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EISWriter:
    """
    Generates narrative content from company data.
    Transforms raw facts into engaging "Deal Highlights."
    """
    
    # Sector display names
    SECTOR_NAMES = {
        '62': 'Technology',
        '63': 'Digital Services',
        '72': 'Research & Development',
        '58': 'Publishing & Media',
        '59': 'Film & Video',
        '61': 'Telecommunications',
        '64': 'Financial Services',
        '86': 'Healthcare',
        '21': 'Pharmaceuticals',
        '71': 'Engineering',
        '70': 'Business Consulting',
        '73': 'Advertising & Marketing',
    }
    
    # Template phrases for narrative generation
    OPENING_PHRASES = [
        "This innovative company",
        "A promising venture",
        "An emerging player",
        "This dynamic enterprise",
        "A growth-focused company",
    ]
    
    ACTIVITY_PHRASES = {
        'technology': "developing cutting-edge solutions",
        'software': "building innovative software products",
        'digital': "creating digital transformation tools",
        'healthcare': "advancing healthcare technology",
        'fintech': "revolutionizing financial services",
        'biotech': "pioneering biotechnology research",
        'default': "driving innovation in its sector",
    }
    
    INVESTMENT_PHRASES = [
        "has recently issued new shares, signaling active investment activity",
        "shows strong investment signals with recent capital activity",
        "demonstrates growth momentum with new share issuances",
        "is actively raising capital to fuel expansion",
    ]
    
    EIS_RECOMMENDATION = {
        'Likely Eligible': "appears well-positioned for EIS investment based on our heuristic analysis",
        'Review Required': "warrants closer review for potential EIS eligibility",
        'Likely Ineligible': "may face challenges meeting EIS criteria",
    }
    
    def __init__(self, use_ai: bool = False, hf_api_key: str = None):
        self.use_ai = use_ai
        self.hf_api_key = hf_api_key or os.environ.get('HUGGINGFACE_API_KEY')
        
        if use_ai and not self.hf_api_key:
            logger.warning("AI mode requested but no HUGGINGFACE_API_KEY found. Falling back to templates.")
            self.use_ai = False
    
    def get_sector_name(self, sic_codes: List[str]) -> str:
        """Convert SIC code to readable sector name."""
        if not sic_codes:
            return "Diversified"
        
        first_sic = str(sic_codes[0])[:2]
        return self.SECTOR_NAMES.get(first_sic, "Diversified")
    
    def get_activity_phrase(self, company_name: str, sic_codes: List[str]) -> str:
        """Get appropriate activity phrase based on company/sector."""
        name_lower = company_name.lower()
        
        for keyword, phrase in self.ACTIVITY_PHRASES.items():
            if keyword in name_lower:
                return phrase
        
        return self.ACTIVITY_PHRASES['default']
    
    def generate_deal_highlight_template(self, company: Dict) -> str:
        """
        Generate a 50-word "Deal Highlight" narrative using templates.
        Zero cost, always works.
        """
        # Extract data
        company_name = company.get('company_name', 'Unknown Company')
        full_profile = company.get('full_profile', {})
        eis_assessment = company.get('eis_assessment', {})
        
        company_data = full_profile.get('company', {})
        sic_codes = company_data.get('sic_codes', [])
        date_of_creation = company_data.get('date_of_creation', '')
        
        # Calculate age
        age = 0
        if date_of_creation:
            try:
                year = int(date_of_creation[:4])
                age = datetime.now().year - year
            except:
                pass
        
        # Get EIS status and score
        eis_status = eis_assessment.get('status', 'Review Required')
        eis_score = eis_assessment.get('score', 0)
        
        # Build narrative
        sector = self.get_sector_name(sic_codes)
        activity = self.get_activity_phrase(company_name, sic_codes)
        import random
        opening = random.choice(self.OPENING_PHRASES)
        investment = random.choice(self.INVESTMENT_PHRASES)
        recommendation = self.EIS_RECOMMENDATION.get(eis_status, self.EIS_RECOMMENDATION['Review Required'])
        
        # Construct the narrative
        if age > 0:
            age_text = f"Founded {age} years ago, this {sector} company"
        else:
            age_text = f"This {sector} company"
        
        narrative = (
            f"{age_text} is {activity}. "
            f"The company {investment}. "
            f"With an EIS likelihood score of {eis_score}/100, it {recommendation}. "
            f"Further due diligence is recommended."
        )
        
        return narrative
    
    def generate_deal_highlight_ai(self, company: Dict) -> str:
        """
        Generate narrative using Hugging Face API.
        Requires HUGGINGFACE_API_KEY environment variable.
        """
        try:
            import requests
        except ImportError:
            logger.warning("requests library not available for AI generation")
            return self.generate_deal_highlight_template(company)
        
        # Extract data for prompt
        company_name = company.get('company_name', 'Unknown')
        full_profile = company.get('full_profile', {})
        eis_assessment = company.get('eis_assessment', {})
        
        company_data = full_profile.get('company', {})
        sic_codes = company_data.get('sic_codes', [])
        eis_score = eis_assessment.get('score', 0)
        eis_status = eis_assessment.get('status', 'Review Required')
        
        sector = self.get_sector_name(sic_codes)
        
        # Build prompt
        prompt = f"""Write a professional 50-word investment highlight about this company:

Company: {company_name}
Sector: {sector}
EIS Likelihood Score: {eis_score}/100
Status: {eis_status}
Key Points: Recent share issuance indicates active investment round

Write an engaging, professional summary suitable for an investment newsletter. 
Focus on the investment opportunity. Be concise."""

        # Call Hugging Face API
        API_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
        headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 150}},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    # Extract just the response (after the prompt)
                    if prompt in generated:
                        generated = generated.split(prompt)[-1].strip()
                    return generated if generated else self.generate_deal_highlight_template(company)
            
            logger.warning(f"AI API returned {response.status_code}, falling back to template")
            return self.generate_deal_highlight_template(company)
            
        except Exception as e:
            logger.warning(f"AI generation failed: {e}, falling back to template")
            return self.generate_deal_highlight_template(company)
    
    def generate_deal_highlight(self, company: Dict) -> str:
        """Generate deal highlight using configured method."""
        if self.use_ai:
            return self.generate_deal_highlight_ai(company)
        return self.generate_deal_highlight_template(company)
    
    def generate_executive_summary(self, companies: List[Dict]) -> str:
        """Generate newsletter executive summary."""
        total = len(companies)
        likely_eligible = sum(1 for c in companies 
                            if 'Eligible' in c.get('eis_assessment', {}).get('status', ''))
        
        avg_score = 0
        if companies:
            scores = [c.get('eis_assessment', {}).get('score', 0) for c in companies]
            avg_score = sum(scores) / len(scores)
        
        summary = f"""This week's EIS Deal Scanner identified {total} companies showing 
active investment signals through recent share capital filings. Of these, {likely_eligible} 
companies ({likely_eligible/total*100:.0f}%) score as "Likely Eligible" for EIS investment 
based on our heuristic analysis. The average EIS likelihood score is {avg_score:.0f}/100.

All companies listed have filed Statement of Capital (SH01) returns recently, 
indicating active share issuances - a key signal of investment rounds in progress. 
As always, this analysis is indicative only; HMRC Advance Assurance is required 
to confirm actual EIS eligibility."""

        return summary
    
    def generate_newsletter_content(self, companies: List[Dict]) -> Dict[str, Any]:
        """
        Generate complete newsletter content from scan results.
        """
        logger.info(f"Generating newsletter content for {len(companies)} companies...")
        
        # Generate executive summary
        executive_summary = self.generate_executive_summary(companies)
        
        # Generate deal highlights for each company
        deal_highlights = []
        for i, company in enumerate(companies):
            logger.info(f"Writing narrative {i+1}/{len(companies)}: {company.get('company_name', 'Unknown')}")
            
            highlight = {
                'company_number': company.get('company_number'),
                'company_name': company.get('company_name'),
                'eis_score': company.get('eis_assessment', {}).get('score', 0),
                'eis_status': company.get('eis_assessment', {}).get('status', 'Unknown'),
                'sector': self.get_sector_name(
                    company.get('full_profile', {}).get('company', {}).get('sic_codes', [])
                ),
                'narrative': self.generate_deal_highlight(company),
                'flags': company.get('eis_assessment', {}).get('flags', []),
            }
            deal_highlights.append(highlight)
        
        # Compile newsletter
        newsletter = {
            'generated_at': datetime.now().isoformat(),
            'title': f"EIS Deal Scanner - {datetime.now().strftime('%B %d, %Y')}",
            'executive_summary': executive_summary,
            'total_companies': len(companies),
            'deal_highlights': deal_highlights,
            'disclaimer': (
                "DISCLAIMER: This newsletter provides EIS-likelihood indicators based on "
                "heuristic analysis of Companies House data. HMRC does not provide a public "
                "API for EIS registration verification. All assessments are indicative only. "
                "Actual EIS eligibility requires HMRC Advance Assurance application. "
                "This is not investment advice."
            )
        }
        
        logger.info("Newsletter content generation complete")
        return newsletter
    
    def save_newsletter(self, newsletter: Dict, output_path: str) -> str:
        """Save newsletter content to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(newsletter, f, indent=2)
        
        logger.info(f"Newsletter saved to {output_path}")
        return output_path


def main():
    """Command-line interface for the writer."""
    parser = argparse.ArgumentParser(
        description='Generate narrative newsletter content from scan results'
    )
    parser.add_argument(
        'input_file',
        help='Path to scan results JSON file'
    )
    parser.add_argument(
        '--ai', action='store_true',
        help='Use AI (Hugging Face) for narrative generation'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output file path (default: newsletter_YYYYMMDD.json)'
    )
    
    args = parser.parse_args()
    
    # Load scan results
    logger.info(f"Loading scan results from {args.input_file}")
    with open(args.input_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    
    companies = scan_data.get('companies', [])
    
    if not companies:
        logger.error("No companies found in scan results")
        return
    
    # Generate newsletter
    writer = EISWriter(use_ai=args.ai)
    newsletter = writer.generate_newsletter_content(companies)
    
    # Save
    output_path = args.output or f"newsletter_{datetime.now().strftime('%Y%m%d')}.json"
    writer.save_newsletter(newsletter, output_path)
    
    # Preview
    print("\n📰 NEWSLETTER PREVIEW")
    print("=" * 60)
    print(f"Title: {newsletter['title']}")
    print(f"Companies: {newsletter['total_companies']}")
    print()
    print("EXECUTIVE SUMMARY:")
    print(newsletter['executive_summary'])
    print()
    print("TOP DEAL HIGHLIGHTS:")
    for i, deal in enumerate(newsletter['deal_highlights'][:3], 1):
        print(f"\n{i}. {deal['company_name']} (Score: {deal['eis_score']}/100)")
        print(f"   {deal['narrative'][:200]}...")
    print()


if __name__ == "__main__":
    main()

"""
EIS Newsletter Writer with Local AI

Generates intelligent narrative content using a local Hugging Face model.
Falls back to template-based generation if AI is unavailable.

Author: Sapphire Intelligence Platform
Version: 2.0 (Local AI Enhancement)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SECTOR_NAMES = {
    '62': 'Technology', '63': 'Digital Services', '72': 'R and D',
    '58': 'Media', '61': 'Telecom', '64': 'Financial Services',
    '86': 'Healthcare', '21': 'Pharma', '71': 'Engineering',
    '70': 'Consulting', '73': 'Marketing',
}


def get_sector_name(sic_codes: List[str]) -> str:
    if not sic_codes:
        return "Diversified"
    return SECTOR_NAMES.get(str(sic_codes[0])[:2], "Diversified")


class LocalAIWriter:
    """AI-powered narrative generator using local Hugging Face model."""
    
    # Use TinyLlama instead of Phi-3 for better compatibility
    MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    def __init__(self):
        self.generator = None
        self.available = False
        self._initialize_model()
    
    def _initialize_model(self):
        try:
            from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading AI model: {self.MODEL_NAME}")
            
            # Check for CUDA
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Device: {device}")
            
            # Load with explicit settings to avoid DynamicCache issues
            self.generator = pipeline(
                "text-generation",
                model=self.MODEL_NAME,
                device_map="auto" if torch.cuda.is_available() else None,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            self.available = True
            logger.info("AI model loaded!")
            
        except ImportError:
            logger.warning("Install: pip install transformers torch accelerate")
            self.available = False
        except Exception as e:
            logger.warning(f"AI unavailable: {e}")
            self.available = False
    
    def generate(self, company_data: Dict) -> Optional[str]:
        if not self.available:
            return None
        
        name = company_data.get('company_name', 'Unknown')
        score = company_data.get('eis_assessment', {}).get('score', 0)
        status = company_data.get('eis_assessment', {}).get('status', 'Unknown')
        sic = company_data.get('full_profile', {}).get('company', {}).get('sic_codes', [])
        sector = get_sector_name(sic)
        
        prompt = f"Write a 50-word investment summary for {name}, a {sector} company with EIS score {score}/100 ({status}). Focus on investment potential. Be professional and concise."
        
        try:
            result = self.generator(prompt, max_new_tokens=100, do_sample=True, temperature=0.7)
            text = result[0]['generated_text']
            # Extract just the generated part (after prompt)
            if prompt in text:
                text = text.split(prompt)[-1].strip()
            return text[:300]  # Limit length
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return None


class TemplateWriter:
    """Template-based fallback narrative generator."""
    
    OPENINGS = [
        "This innovative company", "A promising venture", "An emerging player",
        "This dynamic enterprise", "A growth-focused company",
    ]
    
    ACTIVITIES = {
        'Technology': "developing cutting-edge solutions",
        'Healthcare': "advancing healthcare technology",
        'Financial Services': "revolutionizing financial services",
        'default': "driving innovation in its sector",
    }
    
    INVESTMENT_PHRASES = [
        "has recently issued new shares, signaling active investment activity",
        "shows strong investment signals with recent capital activity",
        "demonstrates growth momentum with new share issuances",
    ]
    
    def generate(self, company_data: Dict) -> str:
        name = company_data.get('company_name', 'Unknown')
        score = company_data.get('eis_assessment', {}).get('score', 0)
        status = company_data.get('eis_assessment', {}).get('status', 'Unknown')
        sic = company_data.get('full_profile', {}).get('company', {}).get('sic_codes', [])
        sector = get_sector_name(sic)
        
        opening = random.choice(self.OPENINGS)
        activity = self.ACTIVITIES.get(sector, self.ACTIVITIES['default'])
        investment = random.choice(self.INVESTMENT_PHRASES)
        
        if 'Eligible' in status:
            recommendation = "appears well-positioned for EIS investment"
        elif 'Review' in status:
            recommendation = "warrants closer review for EIS eligibility"
        else:
            recommendation = "may face challenges meeting EIS criteria"
        
        return f"{opening} in {sector} is {activity}. The company {investment}. With an EIS likelihood score of {score}/100, it {recommendation}. Further due diligence recommended."


class EISWriter:
    """Main writer that combines AI and template approaches."""
    
    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai
        self.ai_writer = None
        self.template_writer = TemplateWriter()
        
        if use_ai:
            self.ai_writer = LocalAIWriter()
            if not self.ai_writer.available:
                logger.info("AI unavailable, using templates")
    
    def generate_deal_highlight(self, company: Dict) -> str:
        if self.use_ai and self.ai_writer and self.ai_writer.available:
            result = self.ai_writer.generate(company)
            if result:
                return result
        return self.template_writer.generate(company)
    
    def generate_executive_summary(self, companies: List[Dict]) -> str:
        total = len(companies)
        eligible = sum(1 for c in companies if 'Eligible' in c.get('eis_assessment', {}).get('status', ''))
        avg = sum(c.get('eis_assessment', {}).get('score', 0) for c in companies) / max(total, 1)
        
        return f"""This week's EIS Deal Scanner identified {total} companies showing active investment signals. 
Of these, {eligible} companies ({eligible/max(total,1)*100:.0f}%) score as Likely Eligible for EIS investment. 
The average EIS likelihood score is {avg:.0f}/100. All companies listed have filed Statement of Capital returns recently, 
indicating active share issuances. This analysis is indicative only; HMRC Advance Assurance is required for confirmation."""
    
    def generate_newsletter_content(self, companies: List[Dict]) -> Dict[str, Any]:
        logger.info(f"Generating newsletter for {len(companies)} companies...")
        
        highlights = []
        for i, company in enumerate(companies):
            logger.info(f"Writing {i+1}/{len(companies)}: {company.get('company_name', 'Unknown')}")
            highlights.append({
                'company_number': company.get('company_number'),
                'company_name': company.get('company_name'),
                'eis_score': company.get('eis_assessment', {}).get('score', 0),
                'eis_status': company.get('eis_assessment', {}).get('status', 'Unknown'),
                'sector': get_sector_name(company.get('full_profile', {}).get('company', {}).get('sic_codes', [])),
                'narrative': self.generate_deal_highlight(company),
            })
        
        return {
            'generated_at': datetime.now().isoformat(),
            'title': f"EIS Deal Scanner - {datetime.now().strftime('%B %d, %Y')}",
            'executive_summary': self.generate_executive_summary(companies),
            'total_companies': len(companies),
            'deal_highlights': highlights,
            'ai_generated': self.use_ai and self.ai_writer and self.ai_writer.available,
            'disclaimer': "DISCLAIMER: EIS assessments are heuristic-based. HMRC verification required."
        }
    
    def save_newsletter(self, newsletter: Dict, path: str) -> str:
        with open(path, 'w') as f:
            json.dump(newsletter, f, indent=2)
        logger.info(f"Saved to {path}")
        return path


def main():
    parser = argparse.ArgumentParser(description='Generate EIS newsletter narratives')
    parser.add_argument('input_file', help='Scan results JSON file')
    parser.add_argument('--ai', action='store_true', help='Use AI generation')
    parser.add_argument('--template', action='store_true', help='Force template mode')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    with open(args.input_file, 'r') as f:
        data = json.load(f)
    
    companies = data.get('companies', [])
    if not companies:
        logger.error("No companies found")
        return
    
    use_ai = not args.template
    writer = EISWriter(use_ai=use_ai)
    newsletter = writer.generate_newsletter_content(companies)
    
    output = args.output or f"newsletter_{datetime.now().strftime('%Y%m%d')}.json"
    writer.save_newsletter(newsletter, output)
    
    print(f"\nNewsletter: {newsletter['title']}")
    print(f"Companies: {newsletter['total_companies']}")
    print(f"AI Generated: {newsletter['ai_generated']}")


if __name__ == "__main__":
    main()

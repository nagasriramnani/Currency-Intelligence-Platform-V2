"""
Editor Agent - Hugging Face LLM Integration

Agent B: The Editor - Summarizes raw search results into professional
investment briefings using Hugging Face Inference API.

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt for the investment analyst persona
SYSTEM_PROMPT = """You are a Senior Investment Analyst at a VC firm specializing in UK EIS (Enterprise Investment Scheme) opportunities. 
You write concise, professional briefings for investor updates.
Focus on material facts: funding rounds, partnerships, product launches, regulatory changes.
Ignore irrelevant noise like job postings or minor operational updates.
If the news is irrelevant or just noise, respond with exactly: NULL"""

# Task prompt template
TASK_PROMPT = """Summarize the following raw search results for {company_name} into a single, professional 2-sentence update for an investor briefing.

Company Context:
- Name: {company_name}
- EIS Score: {eis_score}/100
- Sector: {sector}
- Status: {eis_status}

Raw Search Results:
{raw_results}

Instructions:
- Write exactly 2 sentences
- Focus on investment-relevant news only
- Include specific facts (funding amounts, partnerships, product launches)
- If no relevant news, output exactly: NULL
- Do not include disclaimers or speculation

Your 2-sentence summary:"""


class EditorAgent:
    """
    Agent B: The Editor
    
    Uses Hugging Face Inference API to summarize news into professional briefings.
    """
    
    # Recommended models for summarization
    MODELS = {
        'mistral': 'mistralai/Mistral-7B-Instruct-v0.2',
        'zephyr': 'HuggingFaceH4/zephyr-7b-beta',
        'llama': 'meta-llama/Llama-2-7b-chat-hf',
        'falcon': 'tiiuae/falcon-7b-instruct'
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = 'mistral'):
        self.api_key = api_key or os.environ.get('HUGGINGFACE_API_KEY')
        self.model_id = self.MODELS.get(model, self.MODELS['mistral'])
        self.client = None
        self.available = False
        
        if self.api_key:
            try:
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(token=self.api_key)
                self.available = True
                logger.info(f"Editor Agent initialized with model: {self.model_id}")
            except ImportError:
                logger.warning("huggingface_hub not installed. Run: pip install huggingface_hub")
            except Exception as e:
                logger.error(f"Failed to initialize HuggingFace client: {e}")
        else:
            logger.warning("HUGGINGFACE_API_KEY not set. Editor Agent will use fallback.")
    
    def format_raw_results(self, results: List[Dict]) -> str:
        """Format raw Tavily results into a string for the LLM."""
        if not results:
            return "No search results available."
        
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get('title', 'Untitled')
            content = r.get('content', '')[:300]  # Limit content length
            url = r.get('url', '')
            formatted.append(f"{i}. {title}\n   {content}\n   Source: {url}")
        
        return "\n\n".join(formatted)
    
    def build_prompt(
        self, 
        company_name: str,
        raw_results: List[Dict],
        eis_score: int = 0,
        sector: str = "Unknown",
        eis_status: str = "Unknown"
    ) -> str:
        """Build the full prompt for the LLM."""
        formatted_results = self.format_raw_results(raw_results)
        
        return TASK_PROMPT.format(
            company_name=company_name,
            eis_score=eis_score,
            sector=sector,
            eis_status=eis_status,
            raw_results=formatted_results
        )
    
    def summarize(
        self,
        company_name: str,
        raw_results: List[Dict],
        eis_score: int = 0,
        sector: str = "Unknown",
        eis_status: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Summarize raw search results into a professional briefing.
        
        Args:
            company_name: Name of the company
            raw_results: List of search results from Research Agent
            eis_score: Company's EIS eligibility score
            sector: Company's business sector
            eis_status: EIS eligibility status
        
        Returns:
            Dict with 'summary', 'is_relevant', and metadata
        """
        prompt = self.build_prompt(
            company_name, raw_results, eis_score, sector, eis_status
        )
        
        if not self.available:
            # Fallback: Generate template-based summary
            return self._fallback_summary(company_name, raw_results, sector)
        
        try:
            # Call Hugging Face Inference API
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat_completion(
                model=self.model_id,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Check if LLM returned NULL (no relevant news)
            is_relevant = summary.upper() != "NULL"
            
            return {
                'success': True,
                'summary': summary if is_relevant else None,
                'is_relevant': is_relevant,
                'model': self.model_id,
                'generated_at': datetime.now().isoformat(),
                'sources': [r.get('url') for r in raw_results if r.get('url')]
            }
            
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return self._fallback_summary(company_name, raw_results, sector)
    
    def _fallback_summary(
        self, 
        company_name: str, 
        raw_results: List[Dict],
        sector: str
    ) -> Dict[str, Any]:
        """Generate fallback summary when LLM is unavailable."""
        if not raw_results:
            return {
                'success': True,
                'summary': f"No recent news available for {company_name}.",
                'is_relevant': False,
                'model': 'fallback-template',
                'generated_at': datetime.now().isoformat(),
                'sources': []
            }
        
        # Extract key info from top result
        top_result = raw_results[0]
        title = top_result.get('title', '')
        
        # Template-based summary
        summary = (
            f"Recent activity detected for {company_name} in the {sector} sector. "
            f"Latest coverage: {title[:100]}..."
        )
        
        return {
            'success': True,
            'summary': summary,
            'is_relevant': True,
            'model': 'fallback-template',
            'generated_at': datetime.now().isoformat(),
            'sources': [r.get('url') for r in raw_results if r.get('url')][:3]
        }
    
    def process_multiple(
        self,
        companies_with_results: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Process multiple companies' search results.
        
        Args:
            companies_with_results: Dict mapping company_number to research results
        
        Returns:
            Dict mapping company_number to editor summaries
        """
        summaries = {}
        
        for company_number, research_data in companies_with_results.items():
            if research_data.get('success') and research_data.get('results'):
                # Get company context from research data
                summary = self.summarize(
                    company_name=research_data.get('company_name', 'Unknown'),
                    raw_results=research_data.get('results', []),
                    eis_score=research_data.get('eis_score', 0),
                    sector=research_data.get('sector', 'Unknown'),
                    eis_status=research_data.get('eis_status', 'Unknown')
                )
                summaries[company_number] = summary
        
        return summaries


# Convenience function for direct use
def summarize_company_news(
    company_name: str,
    raw_results: List[Dict],
    eis_score: int = 0,
    sector: str = "Unknown",
    api_key: str = None
) -> Dict[str, Any]:
    """
    Quick function to summarize company news.
    
    Usage:
        from services.editor_agent import summarize_company_news
        summary = summarize_company_news("Acme Tech", raw_results, eis_score=85)
    """
    agent = EditorAgent(api_key=api_key)
    return agent.summarize(company_name, raw_results, eis_score, sector)


if __name__ == "__main__":
    # Test the agent
    sample_results = [
        {
            'title': 'Acme Tech raises £5M Series A',
            'content': 'UK tech startup Acme Tech has secured £5 million in Series A funding...',
            'url': 'https://example.com/acme-funding'
        },
        {
            'title': 'Acme Tech launches new AI product',
            'content': 'The company announced its new AI-powered platform for enterprise...',
            'url': 'https://example.com/acme-product'
        }
    ]
    
    agent = EditorAgent()
    result = agent.summarize(
        company_name="Acme Tech Ltd",
        raw_results=sample_results,
        eis_score=85,
        sector="Technology",
        eis_status="Likely Eligible"
    )
    
    print(f"\n{'='*60}")
    print("Editor Agent Summary")
    print(f"{'='*60}")
    print(f"Summary: {result.get('summary')}")
    print(f"Relevant: {result.get('is_relevant')}")
    print(f"Model: {result.get('model')}")
    print(f"Sources: {result.get('sources')}")

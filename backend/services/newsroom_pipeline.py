"""
Newsroom Pipeline Orchestrator

Coordinates the Research Agent and Local Editor Agent
to produce AI-generated company news summaries.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsroomPipeline:
    """
    Orchestrates the Local AI Newsroom pipeline.
    
    Flow:
    1. Research Agent searches for company news
    2. Local Editor Agent generates summary
    3. Results cached in database
    """
    
    def __init__(self):
        self._research_agent = None
        self._editor_agent = None
    
    @property
    def research_agent(self):
        if self._research_agent is None:
            from services.research_agent import ResearchAgent
            self._research_agent = ResearchAgent()
        return self._research_agent
    
    @property
    def editor_agent(self):
        if self._editor_agent is None:
            from services.local_editor_agent import LocalEditorAgent
            self._editor_agent = LocalEditorAgent()
        return self._editor_agent
    
    def generate_news_summary(
        self,
        company_number: str,
        company_name: str,
        sic_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI news summary for a company.
        
        Args:
            company_number: Companies House number
            company_name: Company name for search
            sic_codes: Optional SIC codes for sector targeting
            
        Returns:
            Dict with summary and metadata
        """
        result = {
            'company_number': company_number,
            'company_name': company_name,
            'summary': None,
            'research': None,
            'success': False,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Research
            logger.info(f"Researching {company_name}...")
            research = self.research_agent.research_company(company_name, sic_codes)
            result['research'] = {
                'query': research.get('query'),
                'results_count': len(research.get('results', [])),
                'success': research.get('success', False)
            }
            
            # Get raw text for editor
            raw_news = self.research_agent.get_raw_news_text(research)
            
            # Step 2: Edit/Summarize
            logger.info(f"Generating summary for {company_name}...")
            summary_result = self.editor_agent.generate_summary(
                company_name,
                raw_news
            )
            
            result['summary'] = summary_result.get('summary')
            result['fallback_used'] = summary_result.get('fallback_used', False)
            result['model_used'] = summary_result.get('model_used')
            result['success'] = summary_result.get('success', False)
            
        except Exception as e:
            logger.error(f"Pipeline failed for {company_name}: {e}")
            result['error'] = str(e)
        
        return result
    
    def batch_generate(
        self,
        companies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple companies.
        
        Args:
            companies: List of dicts with company_number, company_name, sic_codes
            
        Returns:
            List of summary results
        """
        results = []
        
        for company in companies:
            result = self.generate_news_summary(
                company.get('company_number'),
                company.get('company_name'),
                company.get('sic_codes')
            )
            results.append(result)
        
        return results


# Convenience function
def generate_company_news_summary(
    company_number: str,
    company_name: str,
    sic_codes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate AI news summary for a company."""
    pipeline = NewsroomPipeline()
    return pipeline.generate_news_summary(company_number, company_name, sic_codes)

"""
Research Agent - Tavily API Integration

Agent A: The Researcher - Searches for company news using Tavily API
with contextual querying based on company SIC sector.

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SIC Code to Sector Keywords mapping
SIC_SECTOR_KEYWORDS = {
    '62': ['technology', 'software', 'IT services', 'digital'],
    '63': ['data processing', 'web hosting', 'digital services'],
    '72': ['research', 'R&D', 'scientific', 'innovation'],
    '58': ['publishing', 'media', 'content', 'games'],
    '61': ['telecommunications', 'telecom', 'mobile', '5G'],
    '64': ['financial services', 'fintech', 'banking', 'investments'],
    '86': ['healthcare', 'medical', 'health services'],
    '21': ['pharmaceutical', 'biotech', 'drug development'],
    '71': ['engineering', 'architecture', 'technical consulting'],
    '70': ['management consulting', 'business advisory'],
    '73': ['marketing', 'advertising', 'PR', 'market research'],
    '35': ['energy', 'power generation', 'utilities'],
    '41': ['construction', 'property development', 'building'],
    '46': ['wholesale trade', 'distribution'],
    '47': ['retail', 'e-commerce', 'consumer goods'],
}


def get_sector_keywords(sic_codes: List[str]) -> str:
    """Convert SIC codes to searchable sector keywords."""
    if not sic_codes:
        return "business investment funding"
    
    keywords = set()
    for sic in sic_codes:
        prefix = str(sic)[:2]
        if prefix in SIC_SECTOR_KEYWORDS:
            keywords.update(SIC_SECTOR_KEYWORDS[prefix])
    
    if not keywords:
        return "business investment funding"
    
    return ' OR '.join(list(keywords)[:4])  # Limit to 4 keywords


class ResearchAgent:
    """
    Agent A: The Researcher
    
    Uses Tavily API to search for company news with SIC-sector-aware queries.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('TAVILY_API_KEY')
        self.client = None
        self.available = False
        
        if self.api_key:
            try:
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=self.api_key)
                self.available = True
                logger.info("Research Agent initialized with Tavily API")
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
        else:
            logger.warning("TAVILY_API_KEY not set. Research Agent disabled.")
    
    def build_query(self, company_name: str, sic_codes: List[str] = None) -> str:
        """
        Build contextual search query using company name and SIC sector.
        
        Example: '"Acme Tech Ltd" latest business news AND (technology OR software)'
        """
        sector_keywords = get_sector_keywords(sic_codes or [])
        
        # Clean company name for search
        clean_name = company_name.replace('"', '').strip()
        
        query = f'"{clean_name}" latest business news AND ({sector_keywords})'
        
        logger.info(f"Built search query: {query}")
        return query
    
    def search(
        self, 
        company_name: str, 
        sic_codes: List[str] = None,
        max_results: int = 5,
        include_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Search for company news using Tavily API.
        
        Args:
            company_name: Name of the company to search
            sic_codes: List of SIC codes for sector context
            max_results: Maximum number of results to return
            include_answer: Whether to include Tavily's AI-generated answer
        
        Returns:
            Dict with 'results', 'answer', and 'query' keys
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Research Agent not available. Set TAVILY_API_KEY.',
                'results': [],
                'answer': None,
                'query': None
            }
        
        query = self.build_query(company_name, sic_codes)
        
        try:
            # Perform search with Tavily
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=False
            )
            
            # Extract and format results
            results = []
            for item in response.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'content': item.get('content', ''),
                    'url': item.get('url', ''),
                    'score': item.get('score', 0),
                    'published_date': item.get('published_date')
                })
            
            return {
                'success': True,
                'query': query,
                'answer': response.get('answer'),
                'results': results,
                'searched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'answer': None
            }
    
    def search_multiple(
        self, 
        companies: List[Dict], 
        max_results_per_company: int = 3
    ) -> Dict[str, Any]:
        """
        Search for news about multiple companies.
        
        Args:
            companies: List of company dicts with 'company_name' and optional 'sic_codes'
            max_results_per_company: Max results per company
        
        Returns:
            Dict mapping company numbers to their search results
        """
        all_results = {}
        
        for company in companies:
            company_name = company.get('company_name', '')
            company_number = company.get('company_number', company_name)
            sic_codes = company.get('sic_codes', [])
            
            if company_name:
                result = self.search(
                    company_name=company_name,
                    sic_codes=sic_codes,
                    max_results=max_results_per_company
                )
                all_results[company_number] = result
        
        return all_results


# Convenience function for direct use
def search_company_news(
    company_name: str, 
    sic_codes: List[str] = None,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Quick function to search for company news.
    
    Usage:
        from services.research_agent import search_company_news
        results = search_company_news("Acme Tech Ltd", ["62020"])
    """
    agent = ResearchAgent(api_key=api_key)
    return agent.search(company_name, sic_codes)


if __name__ == "__main__":
    # Test the agent
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Agent - Search company news")
    parser.add_argument("company", help="Company name to search")
    parser.add_argument("--sic", nargs="+", help="SIC codes", default=[])
    args = parser.parse_args()
    
    agent = ResearchAgent()
    results = agent.search(args.company, args.sic)
    
    print(f"\n{'='*60}")
    print(f"Search Results for: {args.company}")
    print(f"{'='*60}")
    
    if results['success']:
        print(f"\nQuery: {results['query']}")
        print(f"\nAI Summary: {results.get('answer', 'N/A')}")
        print(f"\n--- News Articles ---")
        for i, r in enumerate(results['results'], 1):
            print(f"\n{i}. {r['title']}")
            print(f"   {r['content'][:200]}...")
            print(f"   URL: {r['url']}")
    else:
        print(f"Error: {results.get('error')}")

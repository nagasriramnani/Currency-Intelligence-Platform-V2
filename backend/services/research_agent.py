"""
Research Agent - Tavily API Integration (VC-Grade)

Agent A: The Researcher - Searches for company investment news using Tavily API
with strict focus on business/finance sources and domain filtering.

Author: Sapphire Intelligence Platform
Version: 2.0 (VC-Grade)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SIC Code to Sector Keywords mapping
SIC_SECTOR_KEYWORDS = {
    '62': ['technology', 'software', 'IT services', 'SaaS'],
    '63': ['data processing', 'cloud', 'digital platform'],
    '72': ['research', 'R&D', 'scientific', 'biotech'],
    '58': ['publishing', 'media', 'gaming', 'content'],
    '61': ['telecommunications', 'telecom', '5G', 'connectivity'],
    '64': ['financial services', 'fintech', 'payments', 'investments'],
    '86': ['healthcare', 'medtech', 'health services'],
    '21': ['pharmaceutical', 'biotech', 'life sciences'],
    '71': ['engineering', 'technical consulting', 'infrastructure'],
    '70': ['management consulting', 'business services'],
    '73': ['marketing', 'advertising', 'adtech'],
    '35': ['energy', 'cleantech', 'renewables'],
    '41': ['construction', 'proptech', 'real estate'],
    '46': ['wholesale', 'B2B', 'distribution'],
    '47': ['retail', 'e-commerce', 'consumer'],
}

# Domains to exclude - not investment/business relevant
EXCLUDED_DOMAINS = [
    'dictionary.cambridge.org',
    'merriam-webster.com',
    'wikipedia.org',
    'wiktionary.org',
    'urbandictionary.com',
    'youtube.com',
    'facebook.com',
    'twitter.com',
    'instagram.com',
    'pinterest.com',
    'reddit.com',
    'quora.com',
    'stackoverflow.com',
    'github.com',
    'amazon.com',
    'ebay.com',
    'lecrabeinfo.net',
    'doogal.co.uk',
]

# Preferred business/investment news domains
PREFERRED_DOMAINS = [
    'techcrunch.com',
    'crunchbase.com',
    'pitchbook.com',
    'dealroom.co',
    'uktech.news',
    'sifted.eu',
    'businessinsider.com',
    'reuters.com',
    'bloomberg.com',
    'ft.com',
    'cityam.com',
    'theguardian.com/business',
    'telegraph.co.uk/business',
    'standard.co.uk/business',
    'growthbusiness.co.uk',
    'startups.co.uk',
    'businesscloud.co.uk',
    'uktechnews.co.uk',
    'gov.uk',
    'companieshouse.gov.uk',
]


def get_sector_keywords(sic_codes: List[str]) -> str:
    """Convert SIC codes to searchable sector keywords."""
    if not sic_codes:
        return "UK startup investment funding"
    
    keywords = set()
    for sic in sic_codes:
        prefix = str(sic)[:2]
        if prefix in SIC_SECTOR_KEYWORDS:
            keywords.update(SIC_SECTOR_KEYWORDS[prefix])
    
    if not keywords:
        return "UK startup investment funding"
    
    return ' OR '.join(list(keywords)[:3])  # Limit to 3 keywords


def is_relevant_url(url: str) -> bool:
    """Check if URL is from a relevant business/investment source."""
    url_lower = url.lower()
    
    # Exclude irrelevant domains
    for excluded in EXCLUDED_DOMAINS:
        if excluded in url_lower:
            return False
    
    return True


def score_url_quality(url: str) -> int:
    """Score URL quality based on domain priority."""
    url_lower = url.lower()
    
    # High priority - investment/startup news
    for domain in PREFERRED_DOMAINS[:10]:
        if domain in url_lower:
            return 100
    
    # Medium priority - general business
    for domain in PREFERRED_DOMAINS[10:]:
        if domain in url_lower:
            return 75
    
    # Companies House is always relevant
    if 'company-information.service.gov.uk' in url_lower:
        return 90
    
    # Default score
    return 50


class ResearchAgent:
    """
    Agent A: The Researcher (VC-Grade)
    
    Uses Tavily API to search for company investment news.
    Filters for business/finance sources only.
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
                logger.info("Research Agent initialized with Tavily API (VC-Grade)")
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
        else:
            logger.warning("TAVILY_API_KEY not set. Research Agent disabled.")
    
    def build_query(self, company_name: str, sic_codes: List[str] = None, query_type: str = "news") -> str:
        """
        Build VC-focused search query.
        
        Query types:
        - news: Latest company news (general)
        - company_specific: ONLY news about this specific company
        - funding: Investment/funding news
        - insights: Market/sector insights
        """
        sector_keywords = get_sector_keywords(sic_codes or [])
        clean_name = company_name.replace('"', '').replace("'", '').strip()
        
        # Remove common suffixes for better matching
        search_name = clean_name
        for suffix in [' LTD', ' LIMITED', ' PLC', ' LP', ' LLP', ' INC', ' CORP']:
            if search_name.upper().endswith(suffix):
                search_name = search_name[:-len(suffix)].strip()
        
        if query_type == "company_specific":
            # STRICT mode - only find news about this exact company
            query = f'"{clean_name}" UK registered company news'
        elif query_type == "funding":
            query = f'"{clean_name}" UK (funding OR investment OR raised OR round OR venture capital)'
        elif query_type == "insights":
            query = f'UK EIS Enterprise Investment Scheme {sector_keywords} startups investment 2024 2025'
        else:
            # Default news query
            query = f'"{clean_name}" UK company (news OR funding OR growth OR expansion OR partnership OR acquisition)'
        
        logger.info(f"Built query [{query_type}]: {query}")
        return query
    
    def _result_mentions_company(self, content: str, title: str, company_name: str) -> bool:
        """Check if the result actually mentions the company (not just sector news)."""
        clean_name = company_name.lower().replace('"', '').replace("'", '').strip()
        
        # Remove common suffixes
        search_terms = [clean_name]
        for suffix in [' ltd', ' limited', ' plc', ' lp', ' llp', ' inc', ' corp']:
            if clean_name.endswith(suffix):
                base_name = clean_name[:-len(suffix)].strip()
                search_terms.append(base_name)
                break
        
        # Also add major words from company name
        words = [w for w in clean_name.split() if len(w) > 3 and w not in ['limited', 'ltd', 'company', 'the']]
        if words:
            search_terms.extend(words[:2])  # First 2 significant words
        
        combined_text = (content + ' ' + title).lower()
        
        # Check if any search term is in the content
        for term in search_terms:
            if term in combined_text:
                return True
        
        return False
    
    def search(
        self, 
        company_name: str, 
        sic_codes: List[str] = None,
        max_results: int = 5,
        query_type: str = "news",
        strict_company_match: bool = False
    ) -> Dict[str, Any]:
        """
        Search for company investment news using Tavily API.
        
        Args:
            company_name: Company name to search for
            sic_codes: SIC codes for sector context
            max_results: Maximum results to return
            query_type: Type of query (news, company_specific, funding, insights)
            strict_company_match: If True, only return results that mention the company
        
        Returns only business-relevant results filtered by domain.
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Research Agent not available. Set TAVILY_API_KEY.',
                'results': [],
                'answer': None,
                'query': None
            }
        
        # Use company_specific query type if strict matching is enabled
        effective_query_type = "company_specific" if strict_company_match else query_type
        query = self.build_query(company_name, sic_codes, effective_query_type)
        
        try:
            # Perform search with Tavily
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results + 8,  # Get extra to filter
                include_answer=True,
                include_raw_content=False
            )
            
            # Extract, filter, and score results
            results = []
            for item in response.get('results', []):
                url = item.get('url', '')
                
                # Filter out irrelevant domains
                if not is_relevant_url(url):
                    logger.debug(f"Filtered out irrelevant URL: {url}")
                    continue
                
                quality_score = score_url_quality(url)
                content = item.get('content', '')
                title = item.get('title', '')
                
                # Skip results with very short content
                if len(content) < 50:
                    continue
                
                # If strict matching, ensure result actually mentions the company
                if strict_company_match:
                    if not self._result_mentions_company(content, title, company_name):
                        logger.debug(f"Filtered: doesn't mention {company_name}")
                        continue
                
                results.append({
                    'title': title,
                    'content': content,
                    'url': url,
                    'score': item.get('score', 0),
                    'quality_score': quality_score,
                    'published_date': item.get('published_date'),
                    'mentions_company': True if strict_company_match else None
                })
            
            # Sort by quality score and limit
            results = sorted(results, key=lambda x: x['quality_score'], reverse=True)[:max_results]
            
            return {
                'success': True,
                'query': query,
                'answer': response.get('answer'),
                'results': results,
                'searched_at': datetime.now().isoformat(),
                'filtered_count': len(response.get('results', [])) - len(results)
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
    
    def get_market_insights(self, sector_focus: str = None) -> Dict[str, Any]:
        """
        Get EIS market insights for newsletter AI section.
        """
        if not self.available:
            return {
                'success': False,
                'insights': []
            }
        
        focus = sector_focus or "technology healthcare cleantech"
        query = f"UK EIS Enterprise Investment Scheme {focus} startups investment trends 2024 2025"
        
        try:
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True
            )
            
            insights = []
            
            # Use Tavily's AI answer as primary insight
            if response.get('answer'):
                answer = response['answer']
                # Split into bullets if long
                if len(answer) > 200:
                    sentences = answer.split('. ')
                    for s in sentences[:3]:
                        if len(s) > 30:
                            insights.append(s.strip() + '.' if not s.endswith('.') else s.strip())
                else:
                    insights.append(answer)
            
            # Add insights from top results
            for result in response.get('results', [])[:3]:
                if is_relevant_url(result.get('url', '')):
                    content = result.get('content', '')
                    if len(content) > 50:
                        # Take first sentence or first 150 chars
                        first_sentence = content.split('. ')[0]
                        if len(first_sentence) > 150:
                            first_sentence = first_sentence[:147] + '...'
                        if first_sentence not in insights:
                            insights.append(first_sentence)
            
            return {
                'success': True,
                'insights': insights[:3],  # Max 3 insights
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Failed to get market insights: {e}")
            return {
                'success': False,
                'insights': [],
                'error': str(e)
            }


# Convenience function for direct use
def search_company_news(
    company_name: str, 
    sic_codes: List[str] = None,
    api_key: str = None
) -> Dict[str, Any]:
    """Quick function to search for company news."""
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
        print(f"Filtered: {results.get('filtered_count', 0)} irrelevant results")
        print(f"\nAI Summary: {results.get('answer', 'N/A')}")
        print(f"\n--- News Articles ---")
        for i, r in enumerate(results['results'], 1):
            print(f"\n{i}. [{r['quality_score']}] {r['title']}")
            print(f"   {r['content'][:200]}...")
            print(f"   URL: {r['url']}")
    else:
        print(f"Error: {results.get('error')}")

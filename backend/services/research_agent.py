"""
Research Agent - Tavily API Integration

Agent A in the Local AI Newsroom pipeline.
Searches for live news about companies using Tavily API.

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# SIC code to sector mapping for search query optimization
SIC_TO_SECTOR = {
    "62": "technology software",
    "63": "technology data services",
    "72": "research development",
    "58": "publishing media",
    "26": "electronics manufacturing",
    "21": "pharmaceutical healthcare",
    "28": "machinery engineering",
    "46": "wholesale trade",
    "47": "retail",
    "41": "construction",
    "56": "food service restaurant",
    "86": "healthcare medical",
    "85": "education",
    "70": "management consulting",
}


class ResearchAgent:
    """
    Agent A: The Researcher
    
    Uses Tavily API to search for live news about companies.
    Filters results based on company sector for relevance.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Research Agent.
        
        Args:
            api_key: Tavily API key. Falls back to TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.api_key:
            logger.warning("No Tavily API key provided. Research will be limited.")
        
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Tavily client."""
        if self._client is None and self.api_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily client initialized successfully")
            except ImportError:
                logger.error("tavily-python not installed. Run: pip install tavily-python")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
        return self._client
    
    def research_company(
        self,
        company_name: str,
        sic_codes: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for news about a company.
        
        Args:
            company_name: The company name to search for
            sic_codes: Optional SIC codes to focus search on relevant sector
            max_results: Maximum number of results to return
            
        Returns:
            Dict with query, results, and metadata
        """
        result = {
            "company_name": company_name,
            "query": "",
            "results": [],
            "sector": None,
            "searched_at": datetime.now().isoformat(),
            "success": False,
            "error": None
        }
        
        # Build search query
        sector = self._get_sector_from_sic(sic_codes)
        result["sector"] = sector
        
        query = f'"{company_name}" business news UK'
        if sector:
            query += f" {sector}"
        
        result["query"] = query
        
        if not self.client:
            result["error"] = "Tavily client not available"
            logger.warning("Tavily client not available for research")
            return result
        
        try:
            logger.info(f"Researching: {query}")
            
            # Search using Tavily
            search_response = self.client.search(
                query=query,
                search_depth="basic",  # "basic" or "advanced"
                max_results=max_results,
                include_domains=["bbc.co.uk", "reuters.com", "ft.com", "theguardian.com", 
                                "techcrunch.com", "businessinsider.com", "uk.finance.yahoo.com"],
                exclude_domains=["linkedin.com", "facebook.com", "twitter.com"]
            )
            
            # Parse results
            for item in search_response.get("results", []):
                result["results"].append({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date")
                })
            
            result["success"] = True
            logger.info(f"Found {len(result['results'])} results for {company_name}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Research failed for {company_name}: {e}")
        
        return result
    
    def _get_sector_from_sic(self, sic_codes: Optional[List[str]]) -> Optional[str]:
        """
        Map SIC codes to sector keywords for search optimization.
        """
        if not sic_codes:
            return None
        
        for sic in sic_codes:
            sic_str = str(sic)[:2]  # Get first 2 digits
            if sic_str in SIC_TO_SECTOR:
                return SIC_TO_SECTOR[sic_str]
        
        return None
    
    def get_raw_news_text(self, research_result: Dict[str, Any], max_chars: int = 2000) -> str:
        """
        Extract raw text from research results for LLM processing.
        
        Args:
            research_result: Result from research_company()
            max_chars: Maximum characters to return
            
        Returns:
            Concatenated text from all results
        """
        if not research_result.get("success") or not research_result.get("results"):
            return ""
        
        texts = []
        for item in research_result["results"]:
            title = item.get("title", "")
            content = item.get("content", "")
            texts.append(f"{title}: {content}")
        
        combined = " | ".join(texts)
        
        # Truncate if too long
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "..."
        
        return combined


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def search_company_news(
    company_name: str,
    sic_codes: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to search for company news.
    
    Args:
        company_name: Company name to search
        sic_codes: Optional SIC codes for sector targeting
        api_key: Optional Tavily API key
        
    Returns:
        Research results dict
    """
    agent = ResearchAgent(api_key=api_key)
    return agent.research_company(company_name, sic_codes)

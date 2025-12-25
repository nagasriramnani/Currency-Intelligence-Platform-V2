"""
Company Research Agent - Tavily-Powered Company Diligence

Conducts in-depth company research using multiple Tavily queries across:
- Company: products, history, leadership, business model
- Industry: market position, competitors, trends, market size
- Financial: funding, revenue, statements, profit
- News: announcements, press releases, partnerships, latest

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompanyResearcher:
    """Tavily-powered company research agent."""
    
    TAVILY_API_URL = "https://api.tavily.com/search"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('TAVILY_API_KEY')
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not configured")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate_queries(self, company_name: str, industry: str = None) -> Dict[str, List[str]]:
        """Generate 16 research queries across 4 categories."""
        ind = industry or "business"
        
        return {
            "company": [
                f"{company_name} core products and services",
                f"{company_name} company history and key milestones",
                f"{company_name} leadership team members and roles",
                f"{company_name} business model and strategy"
            ],
            "industry": [
                f"{company_name} market position in {ind} industry",
                f"{company_name} main competitors in {ind} industry",
                f"{ind} industry trends and challenges affecting {company_name}",
                f"{company_name} market size and growth in {ind} industry"
            ],
            "financial": [
                f"{company_name} fundraising history and valuation",
                f"{company_name} latest financial statements and key metrics",
                f"{company_name} revenue sources breakdown",
                f"{company_name} profit sources analysis"
            ],
            "news": [
                f"{company_name} recent company announcements 2025",
                f"{company_name} press releases December 2025",
                f"{company_name} new partnerships 2025",
                f"{company_name} latest news December 2025"
            ]
        }
    
    async def search_tavily(self, query: str, max_results: int = 5) -> Dict:
        """Execute single Tavily search."""
        if not self.api_key:
            return {"results": [], "query": query}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.TAVILY_API_URL,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_answer": True,
                        "include_raw_content": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "query": query,
                        "answer": data.get("answer", ""),
                        "results": data.get("results", [])
                    }
                else:
                    logger.error(f"Tavily error {response.status_code}: {response.text}")
                    return {"results": [], "query": query}
                    
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"results": [], "query": query}
    
    async def search_category(self, queries: List[str]) -> List[Dict]:
        """Execute all queries in a category concurrently."""
        tasks = [self.search_tavily(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    async def conduct_research(
        self, 
        company_name: str,
        company_url: str = None,
        company_hq: str = None,
        company_industry: str = None
    ) -> Dict:
        """
        Conduct full company research.
        
        Returns structured report with:
        - company_overview
        - industry_overview  
        - financial_overview
        - news
        - references
        - stats (curation metrics)
        """
        if not self.is_available():
            return {"error": "Tavily API key not configured"}
        
        logger.info(f"Starting research for: {company_name}")
        start_time = datetime.now()
        
        # Generate all queries
        queries = self.generate_queries(company_name, company_industry)
        
        # Execute all searches concurrently by category
        results = {}
        all_references = []
        stats = {}
        
        for category, category_queries in queries.items():
            logger.info(f"Researching {category}...")
            category_results = await self.search_category(category_queries)
            
            # Aggregate results
            aggregated = []
            sources_found = 0
            sources_selected = 0
            
            for result in category_results:
                for r in result.get("results", []):
                    sources_found += 1
                    if r.get("content") and len(r.get("content", "")) > 100:
                        sources_selected += 1
                        aggregated.append({
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "url": r.get("url", ""),
                            "score": r.get("score", 0)
                        })
                        
                        # Add to references
                        url = r.get("url", "")
                        if url and url not in [ref["url"] for ref in all_references]:
                            all_references.append({
                                "title": r.get("title", ""),
                                "url": url
                            })
            
            results[category] = aggregated
            stats[category] = f"{sources_selected} selected from {sources_found}"
        
        # Build report sections
        report = {
            "company_name": company_name,
            "company_url": company_url,
            "company_hq": company_hq,
            "company_industry": company_industry,
            "generated_at": datetime.now().isoformat(),
            "research_time": (datetime.now() - start_time).total_seconds(),
            
            "company_overview": self._build_section(results.get("company", []), company_name),
            "industry_overview": self._build_industry_section(results.get("industry", []), company_name, company_industry),
            "financial_overview": self._build_financial_section(results.get("financial", []), company_name),
            "news": self._build_news_section(results.get("news", []), company_name),
            
            "references": all_references[:20],  # Limit to 20 references
            "stats": stats,
            "queries": queries
        }
        
        logger.info(f"Research completed in {report['research_time']:.1f}s")
        return report
    
    def _build_section(self, results: List[Dict], company_name: str) -> Dict:
        """Build company overview section."""
        content = []
        for r in results[:10]:
            if r.get("content"):
                content.append(r["content"])
        
        combined = " ".join(content)
        
        return {
            "business_description": combined[:1500] if combined else f"Research data for {company_name} is being compiled.",
            "leadership_team": self._extract_leadership(results),
            "target_market": self._extract_by_keywords(results, ["customers", "users", "market", "target", "audience"]),
            "key_differentiators": self._extract_by_keywords(results, ["differ", "unique", "advantage", "innovation"]),
            "business_model": self._extract_by_keywords(results, ["revenue", "model", "subscription", "pricing", "fee"])
        }
    
    def _build_industry_section(self, results: List[Dict], company_name: str, industry: str) -> Dict:
        """Build industry overview section."""
        content = " ".join([r.get("content", "") for r in results[:10]])
        
        return {
            "market_landscape": content[:800] if content else f"Industry analysis for {industry or 'sector'} pending.",
            "competition": self._extract_by_keywords(results, ["competitor", "compete", "rival", "versus", "vs"]),
            "competitive_advantages": self._extract_by_keywords(results, ["advantage", "leader", "strength", "best"]),
            "market_challenges": self._extract_by_keywords(results, ["challenge", "risk", "concern", "issue", "problem"])
        }
    
    def _build_financial_section(self, results: List[Dict], company_name: str) -> Dict:
        """Build financial overview section."""
        content = " ".join([r.get("content", "") for r in results[:10]])
        
        return {
            "funding_investment": self._extract_by_keywords(results, ["funding", "raised", "investment", "round", "series", "valuation"]),
            "revenue_model": self._extract_by_keywords(results, ["revenue", "income", "profit", "margin", "sales"]),
            "financial_milestones": self._extract_by_keywords(results, ["milestone", "achieve", "reach", "surpass", "billion", "million"])
        }
    
    def _build_news_section(self, results: List[Dict], company_name: str) -> List[Dict]:
        """Build news section as list of items."""
        news_items = []
        seen_titles = set()
        
        for r in results:
            title = r.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                news_items.append({
                    "title": title,
                    "content": r.get("content", "")[:300],
                    "url": r.get("url", "")
                })
        
        return news_items[:10]  # Top 10 news items
    
    def _extract_leadership(self, results: List[Dict]) -> str:
        """Extract leadership team information."""
        keywords = ["CEO", "CTO", "CFO", "COO", "founder", "president", "executive", "director", "board"]
        return self._extract_by_keywords(results, keywords)
    
    def _extract_by_keywords(self, results: List[Dict], keywords: List[str]) -> str:
        """Extract content matching keywords."""
        matches = []
        for r in results:
            content = r.get("content", "").lower()
            for kw in keywords:
                if kw.lower() in content:
                    matches.append(r.get("content", ""))
                    break
        
        combined = " ".join(matches)
        return combined[:1000] if combined else ""


# Standalone function for API use
async def research_company(
    company_name: str,
    company_url: str = None,
    company_hq: str = None,
    company_industry: str = None
) -> Dict:
    """Convenience function to conduct company research."""
    researcher = CompanyResearcher()
    return await researcher.conduct_research(
        company_name=company_name,
        company_url=company_url,
        company_hq=company_hq,
        company_industry=company_industry
    )


if __name__ == "__main__":
    # Test the researcher
    import asyncio
    
    async def test():
        researcher = CompanyResearcher()
        if researcher.is_available():
            result = await researcher.conduct_research(
                company_name="Spotify",
                company_industry="Music Streaming"
            )
            print(f"Research completed: {result.get('company_name')}")
            print(f"Stats: {result.get('stats')}")
        else:
            print("Tavily API key not configured")
    
    asyncio.run(test())

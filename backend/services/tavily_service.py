"""
Tavily Service - Centralized wrapper for Tavily API

Features:
- Result caching with TTL (default 1 hour)
- Rate limiting (10 requests/minute)
- Retry logic with exponential backoff
- LLM-optimized result formatting
- Specialized search methods for different use cases
"""

import os
import time
import hashlib
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Cache storage
_cache: Dict[str, Dict[str, Any]] = {}
_rate_limit_tracker: List[float] = []

# Constants
CACHE_TTL_SECONDS = 3600  # 1 hour
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


class TavilyService:
    """
    Centralized Tavily API service with caching, rate limiting, and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None
        self.available = False
        
        if self.api_key:
            try:
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=self.api_key)
                self.available = True
                logger.info("TavilyService initialized successfully")
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
        else:
            logger.warning("TAVILY_API_KEY not configured")
    
    # ==================== CACHING ====================
    
    def _get_cache_key(self, query: str, search_type: str = "general") -> str:
        """Generate cache key from query and type"""
        content = f"{search_type}:{query.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get result from cache if not expired"""
        if cache_key in _cache:
            entry = _cache[cache_key]
            if datetime.now() < entry["expires_at"]:
                logger.debug(f"Cache HIT for key {cache_key[:8]}...")
                return entry["data"]
            else:
                # Expired, remove
                del _cache[cache_key]
                logger.debug(f"Cache EXPIRED for key {cache_key[:8]}...")
        return None
    
    def _set_cache(self, cache_key: str, data: Dict, ttl: int = CACHE_TTL_SECONDS):
        """Store result in cache with TTL"""
        _cache[cache_key] = {
            "data": data,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "cached_at": datetime.now().isoformat()
        }
        logger.debug(f"Cache SET for key {cache_key[:8]}... (TTL: {ttl}s)")
    
    def clear_cache(self):
        """Clear all cached results"""
        global _cache
        count = len(_cache)
        _cache = {}
        logger.info(f"Cleared {count} cached results")
        return count
    
    # ==================== RATE LIMITING ====================
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits. Returns True if OK to proceed."""
        global _rate_limit_tracker
        now = time.time()
        
        # Remove old entries outside the window
        _rate_limit_tracker = [t for t in _rate_limit_tracker 
                               if now - t < RATE_LIMIT_WINDOW_SECONDS]
        
        if len(_rate_limit_tracker) >= RATE_LIMIT_MAX_REQUESTS:
            oldest = min(_rate_limit_tracker)
            wait_time = RATE_LIMIT_WINDOW_SECONDS - (now - oldest)
            logger.warning(f"Rate limit reached. Wait {wait_time:.1f}s")
            return False
        
        return True
    
    def _record_request(self):
        """Record a request for rate limiting"""
        _rate_limit_tracker.append(time.time())
    
    # ==================== CORE SEARCH ====================
    
    def search(
        self, 
        query: str, 
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        use_cache: bool = True,
        cache_ttl: int = CACHE_TTL_SECONDS
    ) -> Dict[str, Any]:
        """
        Execute Tavily search with caching and rate limiting.
        
        Args:
            query: Search query
            search_depth: 'basic' or 'advanced'
            max_results: Number of results (1-10)
            include_answer: Include AI-generated answer
            use_cache: Whether to use caching
            cache_ttl: Cache TTL in seconds
            
        Returns:
            Search results dict with 'results', 'answer', 'success' keys
        """
        if not self.available:
            return {
                "success": False,
                "error": "Tavily not configured. Set TAVILY_API_KEY in .env",
                "results": [],
                "answer": None
            }
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(query, f"{search_depth}_{max_results}")
            cached = self._get_from_cache(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
        
        # Check rate limit
        if not self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded. Please wait.",
                "results": [],
                "answer": None
            }
        
        # Execute search with retry logic
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                self._record_request()
                
                response = self.client.search(
                    query=query,
                    search_depth=search_depth,
                    max_results=max_results,
                    include_answer=include_answer
                )
                
                result = {
                    "success": True,
                    "query": query,
                    "answer": response.get("answer"),
                    "results": response.get("results", []),
                    "from_cache": False,
                    "searched_at": datetime.now().isoformat()
                }
                
                # Cache the result
                if use_cache:
                    self._set_cache(cache_key, result, cache_ttl)
                
                logger.info(f"Tavily search completed: '{query[:50]}...' -> {len(result['results'])} results")
                return result
                
            except Exception as e:
                last_error = str(e)
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"Tavily search attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"Tavily search failed after {MAX_RETRIES} attempts: {last_error}")
        return {
            "success": False,
            "error": f"Search failed: {last_error}",
            "results": [],
            "answer": None
        }
    
    # ==================== SPECIALIZED SEARCHES ====================
    
    def search_company_news(self, company_name: str, max_results: int = 5) -> Dict:
        """Search for recent news about a company"""
        query = f"{company_name} UK company news funding investment 2024 2025"
        return self.search(query, search_depth="basic", max_results=max_results)
    
    def search_financials(self, company_name: str) -> Dict:
        """Search for financial data about a company"""
        query = f"{company_name} UK company revenue funding valuation financial results"
        return self.search(query, search_depth="advanced", max_results=5)
    
    def search_eis_eligibility(self, company_name: str) -> Dict:
        """Search for EIS-related information about a company"""
        query = f"{company_name} UK company EIS SEIS investment scheme eligible startup"
        return self.search(query, search_depth="basic", max_results=3)
    
    def search_sector_news(self, sector: str) -> Dict:
        """Search for sector-specific news"""
        sector_queries = {
            "technology": "UK technology startup funding investment news",
            "tech": "UK technology startup funding investment news",
            "fintech": "UK fintech startup funding investment news",
            "healthcare": "UK healthcare biotech medtech startup investment news",
            "cleantech": "UK cleantech climate green energy startup investment news",
            "general": "UK startup investment venture capital news"
        }
        query = sector_queries.get(sector.lower(), sector_queries["general"])
        return self.search(query, search_depth="basic", max_results=5)
    
    # ==================== LLM FORMATTING ====================
    
    def format_for_llm(self, results: Dict, include_urls: bool = True) -> str:
        """
        Format search results for LLM consumption.
        
        Returns a clean, structured text summary optimized for context injection.
        """
        if not results.get("success"):
            return f"Search failed: {results.get('error', 'Unknown error')}"
        
        parts = []
        
        # Add AI-generated answer if available
        if results.get("answer"):
            parts.append(f"📊 Summary:\n{results['answer']}")
        
        # Add individual results
        articles = results.get("results", [])
        if articles:
            parts.append("\n📰 Sources:")
            for i, article in enumerate(articles[:5], 1):
                title = article.get("title", "No title")
                content = article.get("content", "")[:200]  # Truncate
                url = article.get("url", "")
                
                if include_urls:
                    parts.append(f"{i}. {title}\n   {content}...\n   🔗 {url}")
                else:
                    parts.append(f"{i}. {title}\n   {content}...")
        
        if results.get("from_cache"):
            parts.append("\n(ℹ️ Cached result)")
        
        return "\n".join(parts) if parts else "No results found."
    
    def format_news_summary(self, results: Dict) -> str:
        """Format news results as a brief summary"""
        if not results.get("success"):
            return "News unavailable"
        
        articles = results.get("results", [])[:3]
        if not articles:
            return "No recent news found"
        
        lines = ["Recent News:"]
        for article in articles:
            title = article.get("title", "")[:80]
            lines.append(f"• {title}")
        
        return "\n".join(lines)
    
    def format_financial_summary(self, results: Dict) -> str:
        """Format financial search results"""
        if not results.get("success"):
            return "Financial data unavailable"
        
        answer = results.get("answer")
        if answer:
            return f"💰 Financial Data:\n{answer}"
        
        return "No financial data found"
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict:
        """Get service status and statistics"""
        return {
            "available": self.available,
            "cache_size": len(_cache),
            "rate_limit_used": len(_rate_limit_tracker),
            "rate_limit_max": RATE_LIMIT_MAX_REQUESTS,
            "cache_ttl_seconds": CACHE_TTL_SECONDS
        }


# ==================== SINGLETON ====================

_tavily_instance: Optional[TavilyService] = None

def get_tavily_service() -> TavilyService:
    """Get or create the Tavily service instance"""
    global _tavily_instance
    if _tavily_instance is None:
        _tavily_instance = TavilyService()
    return _tavily_instance

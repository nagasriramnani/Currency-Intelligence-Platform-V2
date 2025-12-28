"""
EIS Advisor Agent - Multi-tool conversational agent powered by Ollama

This agent can:
1. Search local portfolio data
2. Look up companies via Companies House API
3. Calculate EIS eligibility scores
4. Get company news via Tavily (Research Agent)
5. Get financial data via Tavily
6. Get sector news (AI Daily News)
7. Answer general EIS questions
8. Answer general knowledge questions (since Ollama has general intelligence)
"""

import os
import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# EIS Knowledge Base for built-in answers
EIS_KNOWLEDGE = """
Enterprise Investment Scheme (EIS) Key Rules:

COMPANY AGE REQUIREMENT:
- Companies must be under 7 years old from first commercial sale
- Knowledge Intensive Companies (KIC) can be up to 10 years old
- This factor is worth 20 points in the EIS score

QUALIFYING SECTORS:
- Technology, Software, SaaS
- Healthcare, Biotech, Medtech
- Clean Energy, CleanTech
- Fintech, Financial Services
- Manufacturing, Engineering

EXCLUDED SECTORS:
- Property development
- Financial services (banking, insurance)
- Legal and accounting services
- Hotels and nursing homes
- Coal and steel production
- Farming and market gardening

COMPANY STATUS:
- Must be an active UK company
- Cannot be dissolved, liquidated, or in administration
- Worth 15 points in EIS score

GROSS ASSETS:
- Must have gross assets under £15 million before investment
- Under £16 million after investment

EMPLOYEE LIMIT:
- Must have fewer than 250 employees (standard EIS)
- Knowledge Intensive Companies can have up to 500 employees

INVESTMENT LIMITS:
- Maximum £5 million per year per company from EIS
- £12 million lifetime limit per company

INVESTOR BENEFITS:
- 30% income tax relief
- Capital gains tax deferral
- Loss relief on failed investments
- No inheritance tax after 2 years
"""

SYSTEM_PROMPT = f"""You are an EIS (Enterprise Investment Scheme) Advisor - a helpful AI assistant that specializes in UK company eligibility screening for EIS investments.

You have access to these capabilities:
1. PORTFOLIO DATA: Information about companies the user has saved
2. COMPANY LOOKUP: Can search UK Companies House database
3. EIS SCORING: Can calculate eligibility scores (0-100)
4. NEWS SEARCH: Can find recent news about companies
5. FINANCIAL DATA: Can find revenue/funding information
6. SECTOR NEWS: Can get UK startup/investment sector news

EIS KNOWLEDGE:
{EIS_KNOWLEDGE}

GUIDELINES:
- For EIS-related questions, provide detailed, accurate information
- For company analysis, break down the EIS score factors
- For general questions (like geography, math, general knowledge), answer helpfully - you have general intelligence
- Always cite sources when providing financial/news data
- Be conversational but professional
- If you don't know something, say so clearly

When analyzing companies, format your response like:
📊 EIS Score: XX/100 (Status)
✅ Passed Factors: ...
❌ Failed Factors: ...
💰 Financial Data: ...
📌 Recommendation: ...
"""


class EISAdvisorAgent:
    """Multi-tool EIS advisor powered by Ollama"""
    
    def __init__(self, model: str = "llama3.2"):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model
        self.available = False
        self.conversation_history: List[Dict[str, str]] = []
        
        # Check if Ollama is available
        self._check_ollama()
        
        # Import other agents (lazy loading)
        self._research_agent = None
        self._companies_house = None
        
    def _check_ollama(self):
        """Check if Ollama is running and model is available"""
        try:
            import httpx
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                if self.model in model_names or f"{self.model}:latest" in [m.get("name") for m in models]:
                    self.available = True
                    logger.info(f"Ollama connected with model: {self.model}")
                else:
                    logger.warning(f"Model {self.model} not found. Available: {model_names}")
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.available = False
            
    @property
    def research_agent(self):
        """Lazy load Research Agent"""
        if self._research_agent is None:
            try:
                from services.research_agent import ResearchAgent
                self._research_agent = ResearchAgent()
            except Exception as e:
                logger.warning(f"Research Agent not available: {e}")
        return self._research_agent
    
    @property
    def companies_house(self):
        """Lazy load Companies House client"""
        if self._companies_house is None:
            try:
                from analytics.companies_house import CompaniesHouseClient
                self._companies_house = CompaniesHouseClient()
            except Exception as e:
                logger.warning(f"Companies House client not available: {e}")
        return self._companies_house
    
    # ============ TOOLS ============
    
    def tool_search_portfolio(self, query: str, portfolio: List[Dict]) -> str:
        """Search saved portfolio for company info"""
        if not portfolio:
            return "No companies in portfolio."
        
        query_lower = query.lower()
        matches = []
        
        for company in portfolio:
            name = company.get("company_name", "").lower()
            number = company.get("company_number", "")
            
            if query_lower in name or query_lower == number:
                score = company.get("eis_score", "N/A")
                status = company.get("eis_status", "Unknown")
                matches.append(f"- {company.get('company_name')} ({number}): Score {score}/100, {status}")
        
        if matches:
            return "Found in portfolio:\n" + "\n".join(matches)
        return f"'{query}' not found in portfolio."
    
    async def tool_lookup_company(self, company_name: str) -> Dict:
        """Get company from Companies House API"""
        if not self.companies_house:
            return {"error": "Companies House API not configured"}
        
        try:
            # Search for company
            results = self.companies_house.search_companies(company_name, limit=1)
            if results and len(results) > 0:
                company_number = results[0].get("company_number")
                # Get full profile
                profile = self.companies_house.get_full_profile(company_number)
                return profile
        except Exception as e:
            logger.error(f"Company lookup failed: {e}")
            return {"error": str(e)}
        
        return {"error": "Company not found"}
    
    def tool_calculate_eis(self, company_data: Dict) -> Dict:
        """Calculate EIS eligibility score"""
        try:
            from analytics.eis_heuristics import calculate_eis_likelihood
            return calculate_eis_likelihood(company_data)
        except Exception as e:
            logger.error(f"EIS calculation failed: {e}")
            return {"error": str(e), "score": 0}
    
    async def tool_search_news(self, company_name: str) -> str:
        """Get recent news via Tavily (Research Agent)"""
        if not self.research_agent or not self.research_agent.available:
            return "News search not available (Tavily not configured)"
        
        try:
            query = f"{company_name} UK company news 2024 2025"
            results = self.research_agent.client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True
            )
            
            articles = results.get("results", [])[:3]
            if articles:
                news_items = []
                for a in articles:
                    title = a.get("title", "No title")
                    url = a.get("url", "")
                    news_items.append(f"- {title}\n  Source: {url}")
                return "Recent News:\n" + "\n".join(news_items)
            
            return f"No recent news found for {company_name}"
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return f"News search failed: {str(e)}"
    
    async def tool_get_financials(self, company_name: str) -> str:
        """Get revenue/funding via Tavily"""
        if not self.research_agent or not self.research_agent.available:
            return "Financial search not available (Tavily not configured)"
        
        try:
            query = f"{company_name} UK company revenue funding valuation 2024"
            results = self.research_agent.client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True
            )
            
            answer = results.get("answer", "")
            if answer:
                return f"Financial Data:\n{answer}"
            
            return f"No financial data found for {company_name}"
        except Exception as e:
            logger.error(f"Financial search failed: {e}")
            return f"Financial search failed: {str(e)}"
    
    async def tool_sector_news(self, sector: str) -> str:
        """Get sector news (AI Daily News)"""
        if not self.research_agent or not self.research_agent.available:
            return "Sector news not available (Tavily not configured)"
        
        sector_queries = {
            "technology": "UK technology startup funding investment news 2024",
            "tech": "UK technology startup funding investment news 2024",
            "healthcare": "UK healthcare biotech medtech startup investment news 2024",
            "fintech": "UK fintech digital banking payments startup news 2024",
            "cleantech": "UK cleantech green energy renewable startup investment news 2024",
            "clean energy": "UK cleantech green energy renewable startup investment news 2024",
        }
        
        query = sector_queries.get(sector.lower(), f"UK {sector} startup investment news 2024")
        
        try:
            results = self.research_agent.client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True
            )
            
            articles = results.get("results", [])[:3]
            if articles:
                news_items = []
                for a in articles:
                    title = a.get("title", "No title")
                    url = a.get("url", "")
                    news_items.append(f"- {title}\n  Source: {url}")
                return f"Latest {sector.title()} News:\n" + "\n".join(news_items)
            
            return f"No recent {sector} news found"
        except Exception as e:
            logger.error(f"Sector news search failed: {e}")
            return f"Sector news search failed: {str(e)}"
    
    # ============ MAIN CHAT ============
    
    def _build_context(self, portfolio: List[Dict]) -> str:
        """Build context string from portfolio"""
        if not portfolio:
            return "User has no companies in their portfolio."
        
        context_parts = [f"User's Portfolio ({len(portfolio)} companies):"]
        for c in portfolio[:10]:  # Limit to 10 for context size
            name = c.get("company_name", "Unknown")
            number = c.get("company_number", "N/A")
            score = c.get("eis_score", "N/A")
            status = c.get("eis_status", "Unknown")
            context_parts.append(f"- {name} ({number}): {score}/100, {status}")
        
        return "\n".join(context_parts)
    
    def _detect_question_type(self, question: str) -> List[str]:
        """Detect which tools might be needed"""
        question_lower = question.lower()
        tools = []
        
        # Company-specific keywords
        company_keywords = ["score", "eligibility", "eligible", "analyze", "analysis", "assessment"]
        if any(k in question_lower for k in company_keywords):
            tools.append("portfolio")
            tools.append("eis")
        
        # News keywords
        if any(k in question_lower for k in ["news", "latest", "recent", "happening"]):
            if any(k in question_lower for k in ["sector", "industry", "tech", "fintech", "healthcare"]):
                tools.append("sector_news")
            else:
                tools.append("news")
        
        # Financial keywords
        if any(k in question_lower for k in ["revenue", "funding", "valuation", "financial", "money"]):
            tools.append("financials")
        
        # Portfolio keywords
        if any(k in question_lower for k in ["portfolio", "saved", "my companies", "list"]):
            tools.append("portfolio")
        
        return tools
    
    async def chat(self, question: str, portfolio: List[Dict] = None) -> str:
        """Main entry point for advisor chat"""
        
        if not self.available:
            return "⚠️ EIS Advisor is not available. Please ensure Ollama is running with llama3.2 model installed.\n\nTo install: `ollama pull llama3.2`"
        
        portfolio = portfolio or []
        
        # Build context
        context = self._build_context(portfolio)
        
        # Detect what tools might help
        tools_needed = self._detect_question_type(question)
        
        # Gather tool results
        tool_context = []
        
        if "portfolio" in tools_needed:
            # Extract company name from question if possible
            result = self.tool_search_portfolio(question, portfolio)
            tool_context.append(result)
        
        if "news" in tools_needed:
            # Try to extract company name
            result = await self.tool_search_news(question)
            tool_context.append(result)
        
        if "sector_news" in tools_needed:
            # Detect sector
            for sector in ["technology", "tech", "fintech", "healthcare", "cleantech"]:
                if sector in question.lower():
                    result = await self.tool_sector_news(sector)
                    tool_context.append(result)
                    break
        
        if "financials" in tools_needed:
            result = await self.tool_get_financials(question)
            tool_context.append(result)
        
        # Build final prompt
        full_context = context
        if tool_context:
            full_context += "\n\nTool Results:\n" + "\n\n".join(tool_context)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": f"Context:\n{full_context}\n\nQuestion: {question}"
        })
        
        # Keep history manageable (last 10 exchanges)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Call Ollama
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            *self.conversation_history
                        ],
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = result.get("message", {}).get("content", "")
                    
                    # Add to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    return assistant_message
                else:
                    logger.error(f"Ollama error: {response.status_code} - {response.text}")
                    return f"⚠️ Error communicating with Ollama: {response.status_code}"
                    
        except httpx.TimeoutException:
            return "⚠️ Request timed out. The model might be loading. Please try again."
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return f"⚠️ Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        return "Conversation history cleared."


# Singleton instance
_advisor_instance: Optional[EISAdvisorAgent] = None

def get_advisor() -> EISAdvisorAgent:
    """Get or create the advisor instance"""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = EISAdvisorAgent()
    return _advisor_instance

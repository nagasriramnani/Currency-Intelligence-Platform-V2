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
Enterprise Investment Scheme (EIS) MANDATORY ELIGIBILITY CRITERIA:

⚠️ CRITICAL RULE: If ANY of these criteria fails, the company is NOT ELIGIBLE (Score = 0)

MANDATORY GATE 1 - COMPANY STATUS:
- MUST be 'active' - not dissolved, liquidation, or administration
- If status is NOT active → IMMEDIATELY NOT ELIGIBLE

MANDATORY GATE 2 - EXCLUDED SECTORS (AUTOMATIC DISQUALIFICATION):
- Banking, insurance, money-lending, financial services (SIC 64xxx, 65xxx, 66xxx)
- Property development (SIC 41xxx, 68xxx)  
- Legal and accounting services (SIC 69xxx)
- Hotels, nursing homes, care homes (SIC 55xxx, 87xxx)
- Coal and steel production
- Farming and market gardening
- Energy generation from renewables with subsidies
- If company operates in ANY excluded sector → IMMEDIATELY NOT ELIGIBLE

MANDATORY GATE 3 - COMPANY AGE:
- MUST be under 7 years old from first commercial sale
- Knowledge Intensive Companies (KIC) can be up to 10 years
- If age > limit → NOT ELIGIBLE

MANDATORY GATE 4 - EMPLOYEE LIMIT:
- MUST have fewer than 250 full-time equivalent employees
- KIC companies: up to 500 employees
- If employees > limit → NOT ELIGIBLE

MANDATORY GATE 5 - GROSS ASSETS:
- MUST have gross assets under £15 million BEFORE investment
- MUST be under £16 million AFTER investment
- If assets > £15M → NOT ELIGIBLE

MANDATORY GATE 6 - INDEPENDENCE:
- MUST NOT be controlled (>50%) by another company
- If subsidiary of large company → NOT ELIGIBLE

EXAMPLES OF INELIGIBLE COMPANIES:
- Revolut: Banking sector = EXCLUDED, >30,000 employees, >£15M assets
- BP: >100 years old, >250 employees, >£15M assets
- HSBC: Banking = EXCLUDED
- Hilton: Hotels = EXCLUDED
- Any property developer = EXCLUDED

INVESTOR BENEFITS (only if company is eligible):
- 30% income tax relief
- Capital gains tax deferral
- Loss relief on failed investments
- No inheritance tax after 2 years
"""

SYSTEM_PROMPT = f"""You are an EIS (Enterprise Investment Scheme) Advisor for UK company eligibility screening.

{EIS_KNOWLEDGE}

⚠️ CRITICAL INSTRUCTIONS:
1. NEVER make up EIS scores - ALWAYS use the actual API calculation results provided in Tool Results
2. If Tool Results show "Not Eligible" or "failed_gates", the company is NOT ELIGIBLE - do not override this
3. For large/famous companies (BP, Revolut, HSBC, etc.) - they are almost certainly NOT ELIGIBLE due to size/sector
4. If a mandatory gate fails, score is 0 and status is "Not Eligible" - no exceptions

You have access to:
1. PORTFOLIO DATA: Saved companies with their actual EIS scores
2. COMPANY LOOKUP: UK Companies House database
3. EIS SCORING API: Calculates the REAL eligibility (use this result, do not make up scores)
4. NEWS SEARCH: Recent company news via Tavily
5. FINANCIAL DATA: Revenue/funding information

RESPONSE FORMAT for EIS eligibility:
📊 EIS Assessment: [Use ACTUAL score from Tool Results]
Status: [ELIGIBLE / NOT ELIGIBLE based on Tool Results]

❌ Failed Mandatory Gates: [List from failed_gates in results]
✅ Passed Criteria: [Only if actually passed]

📌 Recommendation: [Based on actual results]

REMEMBER: Your role is to EXPLAIN the results, not to calculate them yourself.
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
    def tavily_service(self):
        """Lazy load Tavily Service (centralized with caching)"""
        if not hasattr(self, '_tavily_service') or self._tavily_service is None:
            try:
                from services.tavily_service import get_tavily_service
                self._tavily_service = get_tavily_service()
            except Exception as e:
                logger.warning(f"TavilyService not available: {e}")
                self._tavily_service = None
        return self._tavily_service
            
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
                # Handle both flat and nested data structures
                eis_assessment = company.get("eis_assessment", {})
                score = company.get("eis_score") or eis_assessment.get("score", "N/A")
                status = company.get("eis_status") or eis_assessment.get("status", "Unknown")
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
        """Get recent news via TavilyService (with caching)"""
        if not self.tavily_service or not self.tavily_service.available:
            # Fallback to Research Agent if TavilyService not available
            if self.research_agent and self.research_agent.available:
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
                        return "Recent News:\n" + "\n".join([
                            f"- {a.get('title', 'No title')}\n  Source: {a.get('url', '')}"
                            for a in articles
                        ])
                except Exception as e:
                    logger.error(f"Fallback news search failed: {e}")
            return "News search not available (Tavily not configured)"
        
        # Use TavilyService with caching
        results = self.tavily_service.search_company_news(company_name)
        return self.tavily_service.format_news_summary(results)
    
    async def tool_get_financials(self, company_name: str) -> str:
        """Get revenue/funding via TavilyService (with caching)"""
        if not self.tavily_service or not self.tavily_service.available:
            # Fallback to Research Agent
            if self.research_agent and self.research_agent.available:
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
                except Exception as e:
                    logger.error(f"Fallback financial search failed: {e}")
            return "Financial search not available (Tavily not configured)"
        
        # Use TavilyService with caching
        results = self.tavily_service.search_financials(company_name)
        return self.tavily_service.format_financial_summary(results)
    
    async def tool_sector_news(self, sector: str) -> str:
        """Get sector news via TavilyService (with caching)"""
        if not self.tavily_service or not self.tavily_service.available:
            # Fallback to Research Agent
            if self.research_agent and self.research_agent.available:
                try:
                    sector_queries = {
                        "technology": "UK technology startup funding investment news 2024",
                        "tech": "UK technology startup funding investment news 2024",
                        "healthcare": "UK healthcare biotech medtech startup investment news 2024",
                        "fintech": "UK fintech digital banking payments startup news 2024",
                        "cleantech": "UK cleantech green energy renewable startup investment news 2024",
                    }
                    query = sector_queries.get(sector.lower(), f"UK {sector} startup investment news 2024")
                    results = self.research_agent.client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3,
                        include_answer=True
                    )
                    articles = results.get("results", [])[:3]
                    if articles:
                        return f"Latest {sector.title()} News:\n" + "\n".join([
                            f"- {a.get('title', 'No title')}\n  Source: {a.get('url', '')}"
                            for a in articles
                        ])
                except Exception as e:
                    logger.error(f"Fallback sector news failed: {e}")
            return "Sector news not available (Tavily not configured)"
        
        # Use TavilyService with caching
        results = self.tavily_service.search_sector_news(sector)
        return self.tavily_service.format_for_llm(results)
    
    # ============ MAIN CHAT ============
    
    def _build_context(self, portfolio: List[Dict]) -> str:
        """Build context string from portfolio"""
        if not portfolio:
            return "User has no companies in their portfolio."
        
        context_parts = [f"User's Portfolio ({len(portfolio)} companies):"]
        for c in portfolio[:10]:  # Limit to 10 for context size
            name = c.get("company_name", "Unknown")
            number = c.get("company_number", "N/A")
            # Handle both flat and nested data structures
            eis_assessment = c.get("eis_assessment", {})
            score = c.get("eis_score") or eis_assessment.get("score", "N/A")
            status = c.get("eis_status") or eis_assessment.get("status", "Unknown")
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
            async with httpx.AsyncClient(timeout=120.0) as client:
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

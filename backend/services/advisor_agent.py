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
2. COMPANY LOOKUP: Can search UK Companies House database for ANY company
3. EIS SCORING: Can calculate eligibility scores (0-100)
4. NEWS SEARCH: Can find recent news about companies via Tavily
5. FINANCIAL DATA: Can find revenue/funding information via Tavily
6. SECTOR NEWS: Can get UK startup/investment sector news

EIS KNOWLEDGE:
{EIS_KNOWLEDGE}

CRITICAL GUIDELINES:
- ALWAYS TRY TO HELP - never refuse to look up a company
- If company not in portfolio, I will research it via Companies House and Tavily
- Use the provided Tool Results data to give accurate information
- Synthesize all gathered data into a clear, conversational response
- For EIS analysis, use the actual calculated scores from Tool Results
- Be conversational, professional, and thorough

When analyzing companies, format your response like:
📊 Company Overview:
[Company details from research]

📈 EIS Assessment:
- Score: XX/100 (Status)
- Key Factors: ...

📰 Recent News & Activity:
[News from Tavily]

💰 Financial Insights:
[Financial data]

📌 Recommendation:
[Your analysis and advice]
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
        """Get recent news via Tavily (Research Agent) - ENHANCED"""
        if not self.research_agent or not self.research_agent.available:
            return "News search not available (Tavily not configured)"
        
        try:
            query = f"{company_name} UK company news funding investment 2024 2025"
            results = self.research_agent.client.search(
                query=query,
                search_depth="advanced",  # Better quality results
                max_results=5,
                include_answer=True,
                topic="news",  # Use news topic for recent updates
            )
            
            # Get LLM-generated answer from Tavily
            answer = results.get("answer", "")
            articles = results.get("results", [])[:5]
            
            news_output = []
            if answer:
                news_output.append(f"Summary: {answer}")
            
            if articles:
                news_output.append("\nSources:")
                for a in articles:
                    title = a.get("title", "No title")
                    url = a.get("url", "")
                    content = a.get("content", "")[:200]  # First 200 chars
                    news_output.append(f"- {title}\n  {content}...\n  Source: {url}")
                return "📰 Recent News:\n" + "\n".join(news_output)
            
            return f"No recent news found for {company_name}"
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return f"News search failed: {str(e)}"
    
    async def tool_get_financials(self, company_name: str) -> str:
        """Get revenue/funding via Tavily - ENHANCED with finance topic"""
        if not self.research_agent or not self.research_agent.available:
            return "Financial search not available (Tavily not configured)"
        
        try:
            query = f"{company_name} UK company revenue turnover funding valuation employees size 2024 2025"
            results = self.research_agent.client.search(
                query=query,
                search_depth="advanced",  # Better quality
                max_results=5,
                include_answer=True,
                topic="finance",  # Use finance topic for financial queries
            )
            
            answer = results.get("answer", "")
            articles = results.get("results", [])[:3]
            
            financial_output = []
            if answer:
                financial_output.append(f"Summary: {answer}")
            
            if articles:
                financial_output.append("\nSources:")
                for a in articles:
                    title = a.get("title", "No title")
                    content = a.get("content", "")[:150]
                    url = a.get("url", "")
                    financial_output.append(f"- {title}: {content}... ({url})")
            
            if financial_output:
                return "💰 Financial Data:\n" + "\n".join(financial_output)
            
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
        
        # Check if question mentions a company (contains "Ltd", "Limited", "plc", etc.)
        company_indicators = ["ltd", "limited", "plc", "inc", "corp", "company", "llp"]
        has_company_mention = any(ind in question_lower for ind in company_indicators)
        
        # Check for company-related action keywords
        company_action_keywords = ["tell me about", "information", "info", "details", "analyze", 
                                   "analysis", "score", "eligibility", "eligible", "eis",
                                   "check", "lookup", "look up", "find", "search", "research"]
        wants_company_info = any(k in question_lower for k in company_action_keywords)
        
        # If company mentioned OR company action requested → full research pipeline
        if has_company_mention or wants_company_info:
            tools.append("portfolio")      # Step 1: Check portfolio
            tools.append("lookup")         # Step 2: Companies House lookup
            tools.append("eis")            # Step 3: Calculate EIS
            tools.append("news")           # Step 4: Get news
            tools.append("financials")     # Step 5: Get financials
        
        # News-specific keywords (sector news)
        if any(k in question_lower for k in ["sector news", "industry news", "market news"]):
            tools.append("sector_news")
        
        # Portfolio-only keywords
        if any(k in question_lower for k in ["my portfolio", "my saved", "my companies", "list my"]):
            tools = ["portfolio"]  # Only check portfolio
        
        return tools
    
    def _extract_company_name(self, question: str) -> Optional[str]:
        """Try to extract company name from question"""
        # Common patterns: "tell me about XYZ Ltd", "check XYZ Limited"
        question_lower = question.lower()
        
        # Look for company suffixes
        suffixes = [" ltd", " limited", " plc", " llp", " inc"]
        for suffix in suffixes:
            if suffix in question_lower:
                # Find the word(s) before the suffix
                idx = question_lower.find(suffix)
                # Get up to 50 chars before suffix
                start = max(0, idx - 50)
                before = question[start:idx + len(suffix)]
                # Take last few words as company name
                words = before.strip().split()
                if len(words) >= 2:
                    return " ".join(words[-4:])  # Up to 4 words + suffix
        
        # If no suffix found, use the whole question (cleaned)
        # Remove common question starters
        starters = ["tell me about", "what is", "check", "analyze", "search for", 
                   "find", "lookup", "look up", "information on", "info on", "details of"]
        cleaned = question
        for starter in starters:
            if cleaned.lower().startswith(starter):
                cleaned = cleaned[len(starter):].strip()
                break
        
        return cleaned if len(cleaned) > 2 else None
    
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
        company_name = self._extract_company_name(question)
        company_data = None  # Will hold Companies House data if found
        
        logger.info(f"Processing question: '{question}' | Extracted company: '{company_name}' | Tools: {tools_needed}")
        
        # ============ FALLBACK CHAIN ============
        # Step 1: Check Portfolio
        if "portfolio" in tools_needed and company_name:
            portfolio_result = self.tool_search_portfolio(company_name, portfolio)
            tool_context.append(f"📁 Portfolio Search:\n{portfolio_result}")
        
        # Step 2: Companies House Lookup (if company mentioned)
        if "lookup" in tools_needed and company_name:
            try:
                company_data = await self.tool_lookup_company(company_name)
                if company_data and not company_data.get("error"):
                    co = company_data.get("company", {})
                    tool_context.append(f"""🏢 Companies House Data:
- Name: {co.get('company_name', 'N/A')}
- Number: {co.get('company_number', 'N/A')}
- Status: {co.get('company_status', 'N/A')}
- Incorporated: {co.get('date_of_creation', 'N/A')}
- Type: {co.get('type', 'N/A')}
- SIC Codes: {', '.join(co.get('sic_codes', []))}
- Address: {co.get('registered_office_address', {}).get('locality', 'N/A')}""")
                else:
                    tool_context.append(f"🏢 Companies House: Company '{company_name}' not found in registry")
            except Exception as e:
                logger.warning(f"Companies House lookup failed: {e}")
                tool_context.append(f"🏢 Companies House: Lookup failed - {str(e)}")
        
        # Step 3: Calculate EIS (if we have company data)
        if "eis" in tools_needed and company_data and not company_data.get("error"):
            try:
                eis_result = self.tool_calculate_eis(company_data)
                score = eis_result.get("score", 0)
                status = eis_result.get("status", "Unknown")
                failed_gates = eis_result.get("failed_gates", [])
                
                eis_output = f"""📊 EIS Assessment:
- Score: {score}/100
- Status: {status}
- Description: {eis_result.get('status_description', 'N/A')}"""
                
                if failed_gates:
                    eis_output += f"\n- Failed Gates ({len(failed_gates)}):"
                    for gate in failed_gates:
                        eis_output += f"\n  ❌ {gate.get('gate', 'Unknown')}: {gate.get('reason', 'N/A')}"
                else:
                    factors = eis_result.get("factors", [])[:3]
                    if factors:
                        eis_output += "\n- Key Factors:"
                        for f in factors:
                            eis_output += f"\n  ✅ {f.get('factor', 'Unknown')}: {f.get('rationale', '')[:80]}"
                
                tool_context.append(eis_output)
            except Exception as e:
                logger.warning(f"EIS calculation failed: {e}")
        
        # Step 4: Get News via Tavily
        if "news" in tools_needed and company_name:
            try:
                news_result = await self.tool_search_news(company_name)
                if news_result and "not available" not in news_result.lower():
                    tool_context.append(news_result)
            except Exception as e:
                logger.warning(f"News search failed: {e}")
        
        # Step 5: Get Financials via Tavily
        if "financials" in tools_needed and company_name:
            try:
                financials_result = await self.tool_get_financials(company_name)
                if financials_result and "not available" not in financials_result.lower():
                    tool_context.append(financials_result)
            except Exception as e:
                logger.warning(f"Financials search failed: {e}")
        
        # Sector News (special case)
        if "sector_news" in tools_needed:
            for sector in ["technology", "tech", "fintech", "healthcare", "cleantech"]:
                if sector in question.lower():
                    result = await self.tool_sector_news(sector)
                    tool_context.append(result)
                    break

        
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

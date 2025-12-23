"""
Services Module - AI Agents for EIS Intelligence Platform

Contains:
- Research Agent: Tavily API integration for news search
- Editor Agent: Hugging Face LLM for professional summaries
"""

from .research_agent import ResearchAgent, search_company_news
from .editor_agent import EditorAgent, summarize_company_news

__all__ = [
    'ResearchAgent',
    'EditorAgent', 
    'search_company_news',
    'summarize_company_news'
]

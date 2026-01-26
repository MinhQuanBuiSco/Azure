"""Tavily web search tool for research."""

from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


def get_tavily_client() -> TavilyClient | None:
    """Get Tavily client instance."""
    settings = get_settings()
    if settings.tavily_api_key:
        return TavilyClient(api_key=settings.tavily_api_key.get_secret_value())
    return None


@tool
def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Search the web for information using Tavily.

    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Dictionary containing search results with titles, URLs, and content snippets
    """
    client = get_tavily_client()
    if not client:
        logger.warning("Tavily API key not configured")
        return {
            "error": "Tavily API key not configured",
            "results": [],
        }

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
        )

        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0),
            })

        return {
            "query": query,
            "answer": response.get("answer", ""),
            "results": results,
            "total_results": len(results),
        }

    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return {
            "error": str(e),
            "query": query,
            "results": [],
        }


@tool
def search_company_info(company_name: str) -> dict[str, Any]:
    """
    Search for company information including overview, products, and recent news.

    Args:
        company_name: Name of the company to research

    Returns:
        Dictionary containing company information from web search
    """
    client = get_tavily_client()
    if not client:
        return {"error": "Tavily API key not configured", "results": []}

    try:
        # Search for company overview
        overview_query = f"{company_name} company overview business model products services"
        overview_response = client.search(
            query=overview_query,
            max_results=3,
            search_depth="advanced",
            include_answer=True,
        )

        # Search for recent developments
        news_query = f"{company_name} latest news developments 2024"
        news_response = client.search(
            query=news_query,
            max_results=3,
            search_depth="basic",
        )

        return {
            "company_name": company_name,
            "overview": {
                "summary": overview_response.get("answer", ""),
                "sources": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                    }
                    for r in overview_response.get("results", [])
                ],
            },
            "recent_news": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in news_response.get("results", [])
            ],
        }

    except Exception as e:
        logger.error(f"Company info search error: {e}")
        return {"error": str(e), "company_name": company_name}


@tool
def search_competitors(company_name: str, industry: str | None = None) -> dict[str, Any]:
    """
    Search for competitor information for a company.

    Args:
        company_name: Name of the company
        industry: Optional industry context

    Returns:
        Dictionary containing competitor analysis
    """
    client = get_tavily_client()
    if not client:
        return {"error": "Tavily API key not configured", "results": []}

    try:
        query = f"{company_name} competitors market share comparison"
        if industry:
            query += f" {industry} industry"

        response = client.search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_answer=True,
        )

        return {
            "company_name": company_name,
            "industry": industry,
            "competitor_analysis": response.get("answer", ""),
            "sources": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in response.get("results", [])
            ],
        }

    except Exception as e:
        logger.error(f"Competitor search error: {e}")
        return {"error": str(e), "company_name": company_name}

"""LangChain tools for research data gathering."""

from backend.tools.newsapi import (
    analyze_news_sentiment,
    get_company_news,
    get_market_news,
    search_financial_news,
)
from backend.tools.tavily import (
    search_company_info,
    search_competitors,
    web_search,
)
from backend.tools.yfinance_tool import (
    get_analyst_recommendations,
    get_financial_metrics,
    get_historical_prices,
    get_stock_info,
    lookup_ticker,
)

__all__ = [
    # Tavily tools
    "web_search",
    "search_company_info",
    "search_competitors",
    # yfinance tools
    "get_stock_info",
    "get_financial_metrics",
    "get_historical_prices",
    "get_analyst_recommendations",
    "lookup_ticker",
    # NewsAPI tools
    "get_company_news",
    "get_market_news",
    "search_financial_news",
    "analyze_news_sentiment",
]

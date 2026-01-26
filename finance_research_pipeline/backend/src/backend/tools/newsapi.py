"""NewsAPI tool for news retrieval and analysis."""

from datetime import datetime, timedelta
from typing import Any

from langchain_core.tools import tool
from newsapi import NewsApiClient

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


def get_newsapi_client() -> NewsApiClient | None:
    """Get NewsAPI client instance."""
    settings = get_settings()
    if settings.newsapi_key:
        return NewsApiClient(api_key=settings.newsapi_key.get_secret_value())
    return None


@tool
def get_company_news(
    company_name: str,
    days: int = 7,
    language: str = "en",
) -> dict[str, Any]:
    """
    Get recent news articles about a company.

    Args:
        company_name: Name of the company to search news for
        days: Number of days to look back (default: 7)
        language: Language of articles (default: 'en')

    Returns:
        Dictionary containing news articles with titles, descriptions, and sources
    """
    client = get_newsapi_client()
    if not client:
        logger.warning("NewsAPI key not configured")
        return {
            "error": "NewsAPI key not configured",
            "articles": [],
        }

    try:
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        response = client.get_everything(
            q=company_name,
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by="relevancy",
            page_size=20,
        )

        articles = []
        for article in response.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source", {}).get("name", ""),
                "author": article.get("author", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "image_url": article.get("urlToImage", ""),
            })

        return {
            "company_name": company_name,
            "period": {
                "from": from_date,
                "to": to_date,
            },
            "total_results": response.get("totalResults", 0),
            "articles": articles,
        }

    except Exception as e:
        logger.error(f"NewsAPI error for {company_name}: {e}")
        return {
            "error": str(e),
            "company_name": company_name,
            "articles": [],
        }


@tool
def get_market_news(
    category: str = "business",
    country: str = "us",
) -> dict[str, Any]:
    """
    Get top headlines for a category.

    Args:
        category: News category (business, technology, etc.)
        country: Country code (default: 'us')

    Returns:
        Dictionary containing top headlines
    """
    client = get_newsapi_client()
    if not client:
        return {"error": "NewsAPI key not configured", "articles": []}

    try:
        response = client.get_top_headlines(
            category=category,
            country=country,
            page_size=20,
        )

        articles = []
        for article in response.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })

        return {
            "category": category,
            "country": country,
            "total_results": response.get("totalResults", 0),
            "articles": articles,
        }

    except Exception as e:
        logger.error(f"NewsAPI market news error: {e}")
        return {"error": str(e), "articles": []}


@tool
def search_financial_news(
    query: str,
    domains: str | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """
    Search for financial news with specific query.

    Args:
        query: Search query for financial news
        domains: Comma-separated list of domains to search (optional)
        days: Number of days to look back (default: 30)

    Returns:
        Dictionary containing search results
    """
    client = get_newsapi_client()
    if not client:
        return {"error": "NewsAPI key not configured", "articles": []}

    try:
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Default financial news domains if not specified
        default_domains = (
            "reuters.com,bloomberg.com,wsj.com,ft.com,cnbc.com,"
            "marketwatch.com,seekingalpha.com,finance.yahoo.com"
        )

        response = client.get_everything(
            q=query,
            domains=domains or default_domains,
            from_param=from_date,
            language="en",
            sort_by="relevancy",
            page_size=15,
        )

        articles = []
        for article in response.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })

        return {
            "query": query,
            "period_days": days,
            "total_results": response.get("totalResults", 0),
            "articles": articles,
        }

    except Exception as e:
        logger.error(f"Financial news search error: {e}")
        return {"error": str(e), "query": query, "articles": []}


@tool
def analyze_news_sentiment(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze sentiment from a list of news articles (basic keyword analysis).

    Args:
        articles: List of article dictionaries with 'title' and 'description'

    Returns:
        Dictionary containing basic sentiment analysis
    """
    positive_keywords = [
        "growth", "profit", "surge", "gain", "rise", "beat", "exceed",
        "bullish", "upgrade", "success", "strong", "record", "breakthrough",
        "innovation", "expansion", "revenue", "positive", "outperform",
    ]

    negative_keywords = [
        "loss", "decline", "fall", "drop", "miss", "cut", "bearish",
        "downgrade", "weak", "concern", "risk", "warning", "layoff",
        "lawsuit", "investigation", "fraud", "crash", "plunge", "negative",
    ]

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    analyzed_articles = []

    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()

        pos_matches = sum(1 for kw in positive_keywords if kw in text)
        neg_matches = sum(1 for kw in negative_keywords if kw in text)

        if pos_matches > neg_matches:
            sentiment = "positive"
            positive_count += 1
        elif neg_matches > pos_matches:
            sentiment = "negative"
            negative_count += 1
        else:
            sentiment = "neutral"
            neutral_count += 1

        analyzed_articles.append({
            "title": article.get("title", ""),
            "sentiment": sentiment,
            "positive_indicators": pos_matches,
            "negative_indicators": neg_matches,
        })

    total = len(articles)
    return {
        "total_articles": total,
        "sentiment_distribution": {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
        },
        "sentiment_score": (
            round((positive_count - negative_count) / total * 100, 2)
            if total > 0
            else 0
        ),
        "overall_sentiment": (
            "positive" if positive_count > negative_count
            else "negative" if negative_count > positive_count
            else "neutral"
        ),
        "analyzed_articles": analyzed_articles[:10],  # Top 10 for brevity
    }

"""News analysis agent using NewsAPI for news retrieval and sentiment analysis."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.tools.newsapi import (
    analyze_news_sentiment,
    get_company_news,
    search_financial_news,
)

logger = get_logger(__name__)

NEWS_ANALYSIS_PROMPT = """You are a financial analyst specializing in news and sentiment analysis.
Analyze the provided news articles and sentiment data to provide insights on:
1. Key themes and narratives in recent coverage
2. Overall market sentiment toward the company
3. Significant events or announcements
4. Potential impact on stock price and investor perception
5. Emerging risks or opportunities mentioned in the news

Be objective and identify both positive and negative coverage."""


def create_news_analysis_agent(llm: BaseChatModel):
    """
    Create the news analysis agent function.

    Args:
        llm: Language model to use

    Returns:
        News analysis agent function
    """

    async def news_analysis_node(state: ResearchState) -> dict[str, Any]:
        """
        News analysis node that gathers and analyzes news.

        Args:
            state: Current research state

        Returns:
            Updated state with news analysis data
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        ticker = state.get("ticker_symbol")
        time_period = state.get("time_period_days", 30)

        logger.info(f"News analysis starting for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.NEWS_ANALYSIS.value] = AgentProgress(
            agent_type=AgentType.NEWS_ANALYSIS,
            status=AgentStatus.RUNNING,
            message="Starting news analysis",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        news_data: dict[str, Any] = {}

        try:
            # Get company news
            agent_progress[AgentType.NEWS_ANALYSIS.value].message = "Fetching company news"
            agent_progress[AgentType.NEWS_ANALYSIS.value].progress = 25.0

            company_news = get_company_news.invoke({
                "company_name": company_name,
                "days": min(time_period, 30),  # NewsAPI free tier limit
                "language": "en",
            })
            news_data["company_news"] = company_news

            # Search financial news if ticker available
            if ticker:
                agent_progress[AgentType.NEWS_ANALYSIS.value].message = "Searching financial coverage"
                agent_progress[AgentType.NEWS_ANALYSIS.value].progress = 45.0

                financial_news = search_financial_news.invoke({
                    "query": f"{ticker} stock {company_name}",
                    "days": min(time_period, 30),
                })
                news_data["financial_news"] = financial_news

            # Analyze sentiment
            agent_progress[AgentType.NEWS_ANALYSIS.value].message = "Analyzing sentiment"
            agent_progress[AgentType.NEWS_ANALYSIS.value].progress = 65.0

            all_articles = company_news.get("articles", [])
            if ticker and "financial_news" in news_data:
                all_articles.extend(news_data["financial_news"].get("articles", []))

            if all_articles:
                sentiment_analysis = analyze_news_sentiment.invoke({
                    "articles": all_articles[:20],  # Limit for analysis
                })
                news_data["sentiment"] = sentiment_analysis
            else:
                news_data["sentiment"] = {
                    "total_articles": 0,
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0,
                    "message": "No articles available for sentiment analysis",
                }

            # Generate news summary with LLM
            agent_progress[AgentType.NEWS_ANALYSIS.value].message = "Generating analysis"
            agent_progress[AgentType.NEWS_ANALYSIS.value].progress = 85.0

            analysis_prompt = f"""Analyze the following news coverage for {company_name}:

News Articles Found: {company_news.get('total_results', 0)}

Recent Headlines:
{_format_headlines(company_news.get('articles', [])[:10])}

Sentiment Analysis:
{_format_sentiment(news_data.get('sentiment', {}))}

{f"Financial News Coverage: {_format_headlines(news_data.get('financial_news', {}).get('articles', [])[:5])}" if ticker else ""}

Provide a comprehensive news analysis covering:
1. Key themes and narratives
2. Sentiment assessment
3. Notable events or announcements
4. Potential market impact
5. Emerging risks or opportunities"""

            messages = [
                SystemMessage(content=NEWS_ANALYSIS_PROMPT),
                HumanMessage(content=analysis_prompt),
            ]

            analysis = await llm.ainvoke(messages)
            news_data["analysis_summary"] = analysis.content

            # Mark as completed
            agent_progress[AgentType.NEWS_ANALYSIS.value] = AgentProgress(
                agent_type=AgentType.NEWS_ANALYSIS,
                status=AgentStatus.COMPLETED,
                message="News analysis completed",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=analysis.content[:500] if analysis.content else None,
            )

            logger.info(f"News analysis completed for {company_name}")

        except Exception as e:
            logger.error(f"News analysis error: {e}")
            agent_progress[AgentType.NEWS_ANALYSIS.value] = AgentProgress(
                agent_type=AgentType.NEWS_ANALYSIS,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )
            news_data["error"] = str(e)

        return {
            "news_data": news_data,
            "agent_progress": agent_progress,
            "current_agent": AgentType.NEWS_ANALYSIS,
            "overall_progress": calculate_overall_progress(state),
        }

    return news_analysis_node


def _format_headlines(articles: list[dict[str, Any]]) -> str:
    """Format article headlines for analysis."""
    if not articles:
        return "No articles available"

    lines = []
    for article in articles:
        title = article.get("title", "Untitled")
        source = article.get("source", "Unknown")
        date = article.get("published_at", "")[:10] if article.get("published_at") else ""
        lines.append(f"- [{date}] {title} ({source})")

    return "\n".join(lines)


def _format_sentiment(sentiment: dict[str, Any]) -> str:
    """Format sentiment analysis for summary."""
    if not sentiment:
        return "Sentiment analysis unavailable"

    parts = [
        f"Overall Sentiment: {sentiment.get('overall_sentiment', 'neutral').upper()}",
        f"Sentiment Score: {sentiment.get('sentiment_score', 0)}",
        f"Total Articles Analyzed: {sentiment.get('total_articles', 0)}",
    ]

    if dist := sentiment.get("sentiment_distribution"):
        parts.extend([
            f"  Positive: {dist.get('positive', 0)}",
            f"  Negative: {dist.get('negative', 0)}",
            f"  Neutral: {dist.get('neutral', 0)}",
        ])

    return "\n".join(parts)

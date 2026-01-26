"""Web research agent using Tavily for company research."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.tools.tavily import search_company_info, search_competitors, web_search

logger = get_logger(__name__)

WEB_RESEARCH_SYSTEM_PROMPT = """You are a financial research analyst specializing in company background research.
Your task is to gather comprehensive information about a company including:
1. Company overview and business model
2. Products and services
3. Market position and competitive landscape
4. Recent developments and news
5. Key leadership and corporate structure

Synthesize the information from web searches into a clear, factual summary.
Focus on information relevant to investment analysis."""


def create_web_research_agent(llm: BaseChatModel):
    """
    Create the web research agent function.

    Args:
        llm: Language model to use

    Returns:
        Web research agent function
    """

    async def web_research_node(state: ResearchState) -> dict[str, Any]:
        """
        Web research node that gathers company information.

        Args:
            state: Current research state

        Returns:
            Updated state with web research data
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        include_competitors = state.get("include_competitors", True)

        logger.info(f"Web research starting for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.WEB_RESEARCH.value] = AgentProgress(
            agent_type=AgentType.WEB_RESEARCH,
            status=AgentStatus.RUNNING,
            message=f"Researching {company_name}",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        web_data: dict[str, Any] = {}

        try:
            # Search for company information
            agent_progress[AgentType.WEB_RESEARCH.value].message = "Gathering company overview"
            agent_progress[AgentType.WEB_RESEARCH.value].progress = 30.0

            company_info = search_company_info.invoke({"company_name": company_name})
            web_data["company_info"] = company_info

            # Search for industry context
            agent_progress[AgentType.WEB_RESEARCH.value].message = "Researching industry context"
            agent_progress[AgentType.WEB_RESEARCH.value].progress = 50.0

            industry_search = web_search.invoke({
                "query": f"{company_name} industry market trends analysis",
                "max_results": 5,
            })
            web_data["industry_context"] = industry_search

            # Search for competitors if requested
            if include_competitors:
                agent_progress[AgentType.WEB_RESEARCH.value].message = "Analyzing competitors"
                agent_progress[AgentType.WEB_RESEARCH.value].progress = 70.0

                competitor_info = search_competitors.invoke({
                    "company_name": company_name,
                    "industry": company_info.get("overview", {}).get("industry"),
                })
                web_data["competitors"] = competitor_info

            # Synthesize findings with LLM
            agent_progress[AgentType.WEB_RESEARCH.value].message = "Synthesizing research"
            agent_progress[AgentType.WEB_RESEARCH.value].progress = 90.0

            synthesis_prompt = f"""Based on the following research data about {company_name}, provide a comprehensive summary:

Company Information:
{_format_company_info(company_info)}

Industry Context:
{_format_search_results(industry_search)}

{f"Competitor Analysis: {_format_competitor_info(competitor_info)}" if include_competitors and 'competitor_info' in dir() else ""}

Provide a structured summary covering:
1. Company Overview
2. Business Model and Products/Services
3. Market Position
4. Industry Trends
5. Key Takeaways for Investors"""

            messages = [
                SystemMessage(content=WEB_RESEARCH_SYSTEM_PROMPT),
                HumanMessage(content=synthesis_prompt),
            ]

            synthesis = await llm.ainvoke(messages)
            web_data["synthesis"] = synthesis.content

            # Mark as completed
            agent_progress[AgentType.WEB_RESEARCH.value] = AgentProgress(
                agent_type=AgentType.WEB_RESEARCH,
                status=AgentStatus.COMPLETED,
                message="Web research completed",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=synthesis.content[:500] if synthesis.content else None,
            )

            logger.info(f"Web research completed for {company_name}")

        except Exception as e:
            logger.error(f"Web research error: {e}")
            agent_progress[AgentType.WEB_RESEARCH.value] = AgentProgress(
                agent_type=AgentType.WEB_RESEARCH,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )
            web_data["error"] = str(e)

        return {
            "web_research_data": web_data,
            "agent_progress": agent_progress,
            "current_agent": AgentType.WEB_RESEARCH,
            "overall_progress": calculate_overall_progress(state),
        }

    return web_research_node


def _format_company_info(info: dict[str, Any]) -> str:
    """Format company info for LLM prompt."""
    if not info or "error" in info:
        return "No company information available"

    parts = []
    if overview := info.get("overview"):
        parts.append(f"Summary: {overview.get('summary', 'N/A')}")
        for source in overview.get("sources", [])[:2]:
            parts.append(f"- {source.get('title', '')}: {source.get('content', '')[:200]}")

    if news := info.get("recent_news"):
        parts.append("\nRecent News:")
        for article in news[:3]:
            parts.append(f"- {article.get('title', '')}")

    return "\n".join(parts)


def _format_search_results(results: dict[str, Any]) -> str:
    """Format search results for LLM prompt."""
    if not results or "error" in results:
        return "No search results available"

    parts = []
    if answer := results.get("answer"):
        parts.append(f"Summary: {answer}")

    for result in results.get("results", [])[:3]:
        parts.append(f"- {result.get('title', '')}: {result.get('content', '')[:200]}")

    return "\n".join(parts)


def _format_competitor_info(info: dict[str, Any]) -> str:
    """Format competitor info for LLM prompt."""
    if not info or "error" in info:
        return "No competitor information available"

    parts = []
    if analysis := info.get("competitor_analysis"):
        parts.append(f"Analysis: {analysis}")

    for source in info.get("sources", [])[:3]:
        parts.append(f"- {source.get('title', '')}: {source.get('content', '')[:200]}")

    return "\n".join(parts)

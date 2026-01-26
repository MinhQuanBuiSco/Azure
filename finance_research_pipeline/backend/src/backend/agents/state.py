"""Research state definition for LangGraph."""

from datetime import datetime
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.schemas.research import ResearchStatus, ResearchType


def merge_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Merge two dictionaries, with right taking precedence."""
    result = left.copy()
    result.update(right)
    return result


def update_agent_progress(
    left: dict[str, AgentProgress],
    right: dict[str, AgentProgress],
) -> dict[str, AgentProgress]:
    """Update agent progress dictionary."""
    result = left.copy()
    result.update(right)
    return result


class ResearchState(TypedDict, total=False):
    """
    State for the research pipeline.

    This TypedDict defines the complete state that flows through the LangGraph.
    """

    # Identity
    research_id: str
    company_name: str
    ticker_symbol: str | None
    research_type: ResearchType
    additional_context: str | None
    include_competitors: bool
    time_period_days: int

    # Status tracking
    status: ResearchStatus
    current_agent: AgentType | None
    overall_progress: float
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    # Agent progress tracking
    agent_progress: Annotated[dict[str, AgentProgress], update_agent_progress]

    # Messages for agent communication
    messages: Annotated[list[BaseMessage], add_messages]

    # Research data collected by agents
    web_research_data: Annotated[dict[str, Any], merge_dict]
    financial_data: Annotated[dict[str, Any], merge_dict]
    news_data: Annotated[dict[str, Any], merge_dict]
    competitor_data: Annotated[dict[str, Any], merge_dict]

    # Analysis outputs
    market_analysis: str | None
    risk_assessment: str | None
    investment_thesis: str | None

    # Final outputs
    executive_summary: str | None
    full_report: str | None
    recommendations: list[str]

    # Review feedback
    review_feedback: str | None
    revision_needed: bool
    revision_count: int  # Track number of revisions to prevent infinite loops

    # Routing (used by supervisor for conditional edges)
    next: str | None


def create_initial_state(
    research_id: str,
    company_name: str,
    research_type: ResearchType,
    ticker_symbol: str | None = None,
    additional_context: str | None = None,
    include_competitors: bool = True,
    time_period_days: int = 30,
) -> ResearchState:
    """
    Create initial research state.

    Args:
        research_id: Unique research session ID
        company_name: Company to research
        research_type: Type of research
        ticker_symbol: Optional stock ticker
        additional_context: Optional additional context
        include_competitors: Whether to include competitor analysis
        time_period_days: Number of days of historical data

    Returns:
        Initialized ResearchState
    """
    # Initialize agent progress for all agents
    agent_progress = {}
    for agent_type in AgentType:
        agent_progress[agent_type.value] = AgentProgress(
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            progress=0.0,
        )

    return ResearchState(
        research_id=research_id,
        company_name=company_name,
        ticker_symbol=ticker_symbol,
        research_type=research_type,
        additional_context=additional_context,
        include_competitors=include_competitors,
        time_period_days=time_period_days,
        status=ResearchStatus.PENDING,
        current_agent=None,
        overall_progress=0.0,
        started_at=None,
        completed_at=None,
        error_message=None,
        agent_progress=agent_progress,
        messages=[],
        web_research_data={},
        financial_data={},
        news_data={},
        competitor_data={},
        market_analysis=None,
        risk_assessment=None,
        investment_thesis=None,
        executive_summary=None,
        full_report=None,
        recommendations=[],
        review_feedback=None,
        revision_needed=False,
        revision_count=0,
        next=None,
    )


def calculate_overall_progress(state: ResearchState) -> float:
    """
    Calculate overall progress based on agent progress.

    Args:
        state: Current research state

    Returns:
        Overall progress percentage (0-100)
    """
    agent_weights = {
        AgentType.SUPERVISOR.value: 0.05,
        AgentType.WEB_RESEARCH.value: 0.15,
        AgentType.FINANCIAL_DATA.value: 0.20,
        AgentType.NEWS_ANALYSIS.value: 0.15,
        AgentType.ANALYST.value: 0.20,
        AgentType.WRITER.value: 0.15,
        AgentType.REVIEWER.value: 0.10,
    }

    total_progress = 0.0
    agent_progress = state.get("agent_progress", {})

    for agent_name, weight in agent_weights.items():
        progress = agent_progress.get(agent_name)
        if progress:
            if isinstance(progress, dict):
                agent_pct = progress.get("progress", 0.0)
            else:
                agent_pct = progress.progress
            total_progress += agent_pct * weight

    return min(100.0, total_progress)

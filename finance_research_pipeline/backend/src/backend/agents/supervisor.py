"""Supervisor agent for orchestrating the research pipeline."""

from datetime import datetime, UTC
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.schemas.research import ResearchStatus, ResearchType

logger = get_logger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """You are a research supervisor coordinating a financial research pipeline.
Your role is to:
1. Analyze the research request and determine the best approach
2. Route work to specialized agents
3. Monitor progress and handle any issues
4. Ensure comprehensive coverage of the research topic

Based on the current state, determine the next agent to invoke or if research is complete.

Research types and their focus:
- COMPREHENSIVE: Full analysis including all aspects
- QUICK_ANALYSIS: Essential financial data and brief market overview
- NEWS_FOCUSED: Emphasize news and sentiment analysis
- FINANCIAL_ONLY: Focus on financial metrics and stock data

Respond with ONLY the next agent to invoke:
- web_research: For company background and market research
- financial_data: For stock data and financial metrics
- news_analysis: For news and sentiment analysis
- analyst: For synthesizing research into analysis
- writer: For generating the final report
- reviewer: For quality assurance review
- FINISH: When research is complete

Consider the research type and what data has already been collected when making your decision."""


def create_supervisor_agent(llm: BaseChatModel):
    """
    Create the supervisor agent function.

    Args:
        llm: Language model to use

    Returns:
        Supervisor agent function
    """

    async def supervisor_node(state: ResearchState) -> dict[str, Any]:
        """
        Supervisor node that orchestrates the research pipeline.

        Args:
            state: Current research state

        Returns:
            Updated state with routing decision
        """
        logger.info(f"Supervisor processing research: {state['research_id']}")

        # Update supervisor status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.SUPERVISOR.value] = AgentProgress(
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.RUNNING,
            message="Coordinating research pipeline",
            progress=50.0,
            started_at=datetime.now(UTC),
        )

        # Build context for decision
        context_parts = [
            f"Company: {state['company_name']}",
            f"Research Type: {state['research_type'].value}",
            f"Ticker: {state.get('ticker_symbol', 'Unknown')}",
        ]

        if state.get("additional_context"):
            context_parts.append(f"Additional Context: {state['additional_context']}")

        # Check what data has been collected
        collected = []
        if state.get("web_research_data"):
            collected.append("web_research (company background)")
        if state.get("financial_data"):
            collected.append("financial_data (stock metrics)")
        if state.get("news_data"):
            collected.append("news_analysis (news sentiment)")
        if state.get("market_analysis"):
            collected.append("analyst (market analysis)")
        if state.get("full_report"):
            collected.append("writer (report draft)")
        if state.get("review_feedback"):
            collected.append("reviewer (quality review)")

        if collected:
            context_parts.append(f"Data collected: {', '.join(collected)}")
        else:
            context_parts.append("No data collected yet - starting fresh")

        # Check for revision needs
        if state.get("revision_needed"):
            context_parts.append(f"Revision needed: {state.get('review_feedback', 'No feedback')}")

        context = "\n".join(context_parts)

        # Get routing decision from LLM
        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Current research state:\n{context}\n\nWhat is the next step?"),
        ]

        response = await llm.ainvoke(messages)
        decision = response.content.strip().lower()

        # Parse decision
        next_agent = _parse_routing_decision(decision, state)

        # Update supervisor progress
        agent_progress[AgentType.SUPERVISOR.value] = AgentProgress(
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.COMPLETED,
            message=f"Routed to: {next_agent}",
            progress=100.0,
            completed_at=datetime.now(UTC),
        )

        logger.info(f"Supervisor routing to: {next_agent}")

        return {
            "agent_progress": agent_progress,
            "current_agent": AgentType.SUPERVISOR,
            "overall_progress": calculate_overall_progress(state),
            "next": next_agent,  # Used for conditional routing
        }

    return supervisor_node


def _parse_routing_decision(
    decision: str,
    state: ResearchState,
) -> str:
    """
    Parse the LLM's routing decision.

    Args:
        decision: Raw decision from LLM
        state: Current state for context

    Returns:
        Validated next node name
    """
    # Map of valid agents
    valid_agents = {
        "web_research": "web_research",
        "financial_data": "financial_data",
        "news_analysis": "news_analysis",
        "analyst": "analyst",
        "writer": "writer",
        "reviewer": "reviewer",
        "finish": "finish",
    }

    # Try to match decision to valid agent
    for key, value in valid_agents.items():
        if key in decision:
            return value

    # Default routing based on state if LLM decision unclear
    return _default_routing(state)


def _default_routing(state: ResearchState) -> str:
    """
    Determine default routing based on current state.

    Args:
        state: Current research state

    Returns:
        Next node name
    """
    research_type = state.get("research_type", ResearchType.COMPREHENSIVE)

    # Check what's missing and route accordingly
    if not state.get("financial_data"):
        return "financial_data"

    if research_type == ResearchType.FINANCIAL_ONLY:
        if not state.get("market_analysis"):
            return "analyst"
        if not state.get("full_report"):
            return "writer"
        return "finish"

    if not state.get("web_research_data"):
        return "web_research"

    if research_type != ResearchType.QUICK_ANALYSIS and not state.get("news_data"):
        return "news_analysis"

    if not state.get("market_analysis"):
        return "analyst"

    if not state.get("full_report"):
        return "writer"

    if not state.get("review_feedback"):
        return "reviewer"

    if state.get("revision_needed"):
        # Limit revisions to prevent infinite loops
        revision_count = state.get("revision_count", 0)
        if revision_count < 2:  # Max 2 revisions
            return "writer"
        else:
            logger.warning(f"Max revisions reached for research, finishing anyway")
            return "finish"

    return "finish"


def get_next_node(state: ResearchState) -> Literal[
    "web_research",
    "financial_data",
    "news_analysis",
    "analyst",
    "writer",
    "reviewer",
    "finish",
]:
    """
    Get the next node based on supervisor decision.

    This function is used as the conditional edge in the graph.

    Args:
        state: Current research state

    Returns:
        Name of the next node
    """
    next_node = state.get("next", "finish")
    if next_node not in [
        "web_research",
        "financial_data",
        "news_analysis",
        "analyst",
        "writer",
        "reviewer",
        "finish",
    ]:
        return "finish"
    return next_node

"""LangGraph StateGraph definition for the research pipeline."""

from datetime import datetime, UTC
from typing import Any, Callable

from langgraph.graph import END, StateGraph
from langchain_core.language_models import BaseChatModel

from backend.agents.analyst import create_analyst_agent
from backend.agents.financial_data import create_financial_data_agent
from backend.agents.news_analysis import create_news_analysis_agent
from backend.agents.reviewer import create_reviewer_agent
from backend.agents.state import ResearchState, calculate_overall_progress
from backend.agents.supervisor import create_supervisor_agent, get_next_node
from backend.agents.web_research import create_web_research_agent
from backend.agents.writer import create_writer_agent
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.schemas.research import ResearchStatus
from backend.services.websocket_manager import WebSocketManager

logger = get_logger(__name__)


def create_research_graph(
    llm: BaseChatModel,
    ws_manager: WebSocketManager | None = None,
) -> StateGraph:
    """
    Create the research pipeline StateGraph.

    Args:
        llm: Language model to use for all agents
        ws_manager: Optional WebSocket manager for progress updates

    Returns:
        Compiled StateGraph
    """
    # Create all agent nodes
    supervisor_node = create_supervisor_agent(llm)
    web_research_node = create_web_research_agent(llm)
    financial_data_node = create_financial_data_agent(llm)
    news_analysis_node = create_news_analysis_agent(llm)
    analyst_node = create_analyst_agent(llm)
    writer_node = create_writer_agent(llm)
    reviewer_node = create_reviewer_agent(llm)

    # Wrap nodes with progress broadcasting if ws_manager provided
    if ws_manager:
        supervisor_node = _wrap_with_progress(supervisor_node, ws_manager)
        web_research_node = _wrap_with_progress(web_research_node, ws_manager)
        financial_data_node = _wrap_with_progress(financial_data_node, ws_manager)
        news_analysis_node = _wrap_with_progress(news_analysis_node, ws_manager)
        analyst_node = _wrap_with_progress(analyst_node, ws_manager)
        writer_node = _wrap_with_progress(writer_node, ws_manager)
        reviewer_node = _wrap_with_progress(reviewer_node, ws_manager)

    # Create the graph
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("start", _create_start_node(ws_manager))
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("web_research", web_research_node)
    graph.add_node("financial_data", financial_data_node)
    graph.add_node("news_analysis", news_analysis_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("finish", _create_finish_node(ws_manager))

    # Set entry point
    graph.set_entry_point("start")

    # Add edges
    graph.add_edge("start", "supervisor")

    # Supervisor routes to appropriate agent
    graph.add_conditional_edges(
        "supervisor",
        get_next_node,
        {
            "web_research": "web_research",
            "financial_data": "financial_data",
            "news_analysis": "news_analysis",
            "analyst": "analyst",
            "writer": "writer",
            "reviewer": "reviewer",
            "finish": "finish",
        },
    )

    # All agents return to supervisor for routing
    graph.add_edge("web_research", "supervisor")
    graph.add_edge("financial_data", "supervisor")
    graph.add_edge("news_analysis", "supervisor")
    graph.add_edge("analyst", "supervisor")
    graph.add_edge("writer", "supervisor")
    graph.add_edge("reviewer", "supervisor")

    # Finish node ends the graph
    graph.add_edge("finish", END)

    return graph.compile()


def _create_start_node(
    ws_manager: WebSocketManager | None,
) -> Callable[[ResearchState], dict[str, Any]]:
    """Create the start node that initializes the pipeline."""

    async def start_node(state: ResearchState) -> dict[str, Any]:
        """Initialize the research pipeline."""
        research_id = state["research_id"]
        logger.info(f"Starting research pipeline: {research_id}")

        # Update status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.SUPERVISOR.value] = AgentProgress(
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.RUNNING,
            message="Initializing research pipeline",
            progress=0.0,
            started_at=datetime.now(UTC),
        )

        if ws_manager:
            await ws_manager.send_message(
                research_id,
                "pipeline_start",
                {
                    "research_id": research_id,
                    "company_name": state["company_name"],
                    "message": "Research pipeline started",
                },
            )

        return {
            "status": ResearchStatus.IN_PROGRESS,
            "started_at": datetime.now(UTC),
            "agent_progress": agent_progress,
            "overall_progress": 0.0,
        }

    return start_node


def _create_finish_node(
    ws_manager: WebSocketManager | None,
) -> Callable[[ResearchState], dict[str, Any]]:
    """Create the finish node that completes the pipeline."""

    async def finish_node(state: ResearchState) -> dict[str, Any]:
        """Complete the research pipeline."""
        research_id = state["research_id"]
        logger.info(f"Completing research pipeline: {research_id}")

        # Check if there was an error
        error_message = state.get("error_message")
        status = ResearchStatus.FAILED if error_message else ResearchStatus.COMPLETED

        # Update all agent progress to completed or keep their status
        agent_progress = state.get("agent_progress", {}).copy()

        if ws_manager:
            await ws_manager.send_completion(
                research_id,
                summary=state.get("executive_summary"),
            )

        return {
            "status": status,
            "completed_at": datetime.now(UTC),
            "overall_progress": 100.0,
            "agent_progress": agent_progress,
        }

    return finish_node


def _wrap_with_progress(
    node_func: Callable,
    ws_manager: WebSocketManager,
) -> Callable:
    """Wrap a node function to broadcast progress updates."""

    async def wrapped_node(state: ResearchState) -> dict[str, Any]:
        """Wrapped node with progress broadcasting."""
        research_id = state["research_id"]

        # Execute the original node
        result = await node_func(state)

        # Broadcast progress update
        if "agent_progress" in result:
            current_agent = result.get("current_agent")
            if current_agent:
                progress = result["agent_progress"].get(current_agent.value)
                if progress:
                    await ws_manager.send_agent_progress(
                        research_id,
                        current_agent,
                        progress,
                    )

        # Broadcast overall progress
        overall_progress = result.get("overall_progress", calculate_overall_progress(state))
        await ws_manager.send_message(
            research_id,
            "progress_update",
            {
                "overall_progress": overall_progress,
                "current_agent": result.get("current_agent", "").value
                if result.get("current_agent")
                else None,
            },
        )

        return result

    return wrapped_node


async def run_research_pipeline(
    research_id: str,
    company_name: str,
    research_type: str,
    llm: BaseChatModel,
    ws_manager: WebSocketManager | None = None,
    ticker_symbol: str | None = None,
    additional_context: str | None = None,
    include_competitors: bool = True,
    time_period_days: int = 30,
) -> ResearchState:
    """
    Run the complete research pipeline.

    Args:
        research_id: Unique research session ID
        company_name: Company to research
        research_type: Type of research
        llm: Language model
        ws_manager: Optional WebSocket manager
        ticker_symbol: Optional stock ticker
        additional_context: Optional additional context
        include_competitors: Whether to include competitor analysis
        time_period_days: Days of historical data

    Returns:
        Final research state
    """
    from backend.agents.state import create_initial_state
    from backend.schemas.research import ResearchType

    # Create initial state
    initial_state = create_initial_state(
        research_id=research_id,
        company_name=company_name,
        research_type=ResearchType(research_type),
        ticker_symbol=ticker_symbol,
        additional_context=additional_context,
        include_competitors=include_competitors,
        time_period_days=time_period_days,
    )

    # Create and run the graph
    graph = create_research_graph(llm, ws_manager)

    logger.info(f"Executing research pipeline for {company_name}")

    try:
        # Run the graph
        final_state = await graph.ainvoke(initial_state)
        logger.info(f"Research pipeline completed: {research_id}")
        return final_state

    except Exception as e:
        logger.error(f"Research pipeline error: {e}")

        if ws_manager:
            await ws_manager.send_error(research_id, str(e))

        # Return state with error
        initial_state["status"] = ResearchStatus.FAILED
        initial_state["error_message"] = str(e)
        initial_state["completed_at"] = datetime.now(UTC)
        return initial_state

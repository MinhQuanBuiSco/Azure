"""Reviewer agent for quality assurance of research reports."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType

logger = get_logger(__name__)

REVIEWER_SYSTEM_PROMPT = """You are a senior research editor and quality assurance specialist.
Your role is to review financial research reports for:

1. **Accuracy**: Are claims supported by data? Are metrics cited correctly?
2. **Completeness**: Does the report cover all essential aspects?
3. **Clarity**: Is the report well-structured and easy to understand?
4. **Balance**: Are both opportunities and risks adequately addressed?
5. **Actionability**: Are recommendations clear and actionable?
6. **Professionalism**: Is the tone appropriate for institutional investors?

Provide specific, constructive feedback.
Rate the report quality as: EXCELLENT, GOOD, NEEDS_REVISION, or POOR.
A rating of NEEDS_REVISION or POOR means the report should be revised."""


def create_reviewer_agent(llm: BaseChatModel):
    """
    Create the reviewer agent function.

    Args:
        llm: Language model to use

    Returns:
        Reviewer agent function
    """

    async def reviewer_node(state: ResearchState) -> dict[str, Any]:
        """
        Reviewer node that performs quality assurance.

        Args:
            state: Current research state

        Returns:
            Updated state with review feedback
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        full_report = state.get("full_report", "")

        logger.info(f"Reviewer checking report for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.REVIEWER.value] = AgentProgress(
            agent_type=AgentType.REVIEWER,
            status=AgentStatus.RUNNING,
            message="Reviewing report quality",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        try:
            if not full_report:
                raise ValueError("No report available to review")

            # Gather context for review
            financial_data = state.get("financial_data", {})
            news_data = state.get("news_data", {})
            recommendations = state.get("recommendations", [])

            # Perform review
            agent_progress[AgentType.REVIEWER.value].message = "Analyzing report structure"
            agent_progress[AgentType.REVIEWER.value].progress = 30.0

            review_prompt = f"""Review the following investment research report for {company_name}.

## Report to Review:
{full_report}

## Available Source Data for Verification:

Financial Metrics:
{_format_verification_data(financial_data)}

News Sentiment:
{news_data.get('sentiment', {}).get('overall_sentiment', 'Unknown')} (Score: {news_data.get('sentiment', {}).get('sentiment_score', 'N/A')})

Stated Recommendations:
{chr(10).join(f'- {rec}' for rec in recommendations[:5]) if recommendations else 'None provided'}

## Review Criteria:

1. **Accuracy** (0-25 points)
   - Are financial metrics accurately cited?
   - Do claims align with source data?
   - Are there any factual errors?

2. **Completeness** (0-25 points)
   - Does it cover all key sections?
   - Is the analysis thorough?
   - Are there gaps in coverage?

3. **Clarity & Structure** (0-25 points)
   - Is the report well-organized?
   - Is the writing clear and professional?
   - Are visuals/tables appropriate?

4. **Balance & Objectivity** (0-25 points)
   - Are both bull and bear cases presented?
   - Are risks adequately addressed?
   - Is the tone appropriately objective?

## Required Output:

Provide your review in this format:

### Quality Rating: [EXCELLENT/GOOD/NEEDS_REVISION/POOR]

### Score Breakdown:
- Accuracy: X/25
- Completeness: X/25
- Clarity: X/25
- Balance: X/25
- **Total: X/100**

### Strengths:
[List 2-3 key strengths]

### Areas for Improvement:
[List specific issues that need attention]

### Specific Feedback:
[Detailed feedback for revision if needed]

### Recommendation:
[Final recommendation - approve or request revision with specific guidance]"""

            messages = [
                SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
                HumanMessage(content=review_prompt),
            ]

            agent_progress[AgentType.REVIEWER.value].message = "Generating review"
            agent_progress[AgentType.REVIEWER.value].progress = 70.0

            review_response = await llm.ainvoke(messages)
            review_feedback = review_response.content

            # Determine if revision is needed
            revision_needed = _needs_revision(review_feedback)

            agent_progress[AgentType.REVIEWER.value].message = "Review complete"
            agent_progress[AgentType.REVIEWER.value].progress = 100.0

            # Mark as completed
            agent_progress[AgentType.REVIEWER.value] = AgentProgress(
                agent_type=AgentType.REVIEWER,
                status=AgentStatus.COMPLETED,
                message=f"Review complete - {'Revision needed' if revision_needed else 'Approved'}",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=review_feedback[:500],
            )

            logger.info(
                f"Reviewer completed for {company_name}: "
                f"{'Revision needed' if revision_needed else 'Approved'}"
            )

            return {
                "review_feedback": review_feedback,
                "revision_needed": revision_needed,
                "agent_progress": agent_progress,
                "current_agent": AgentType.REVIEWER,
                "overall_progress": calculate_overall_progress(state),
            }

        except Exception as e:
            logger.error(f"Reviewer error: {e}")
            agent_progress[AgentType.REVIEWER.value] = AgentProgress(
                agent_type=AgentType.REVIEWER,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )

            return {
                "agent_progress": agent_progress,
                "current_agent": AgentType.REVIEWER,
                "error_message": str(e),
            }

    return reviewer_node


def _format_verification_data(financial_data: dict[str, Any]) -> str:
    """Format financial data for verification."""
    if not financial_data:
        return "Not available"

    parts = []

    if stock_info := financial_data.get("stock_info"):
        if price := stock_info.get("price"):
            parts.append(f"Current Price: ${price.get('current', 'N/A')}")
        if mc := stock_info.get("market_cap"):
            parts.append(f"Market Cap: ${mc:,.0f}" if isinstance(mc, (int, float)) else f"Market Cap: {mc}")

    if metrics := financial_data.get("metrics"):
        if val := metrics.get("valuation"):
            parts.append(f"P/E: {val.get('pe_ratio', 'N/A')}")
        if prof := metrics.get("profitability"):
            parts.append(f"Profit Margin: {prof.get('profit_margin', 'N/A')}")

    if historical := financial_data.get("historical"):
        if stats := historical.get("statistics"):
            parts.append(f"Period Change: {stats.get('change_percent', 'N/A')}%")

    return "\n".join(parts) if parts else "Not available"


def _needs_revision(review_feedback: str) -> bool:
    """
    Determine if the report needs revision based on review feedback.

    Args:
        review_feedback: Review feedback text

    Returns:
        True if revision is needed
    """
    feedback_lower = review_feedback.lower()

    # Check for explicit revision indicators
    if "needs_revision" in feedback_lower or "needs revision" in feedback_lower:
        return True

    if "poor" in feedback_lower and "quality rating" in feedback_lower:
        return True

    # Check for score-based indicators
    import re
    total_match = re.search(r"total:\s*(\d+)/100", feedback_lower)
    if total_match:
        score = int(total_match.group(1))
        if score < 70:  # Below 70% requires revision
            return True

    # Check for explicit approval
    if "excellent" in feedback_lower or "good" in feedback_lower:
        if "approve" in feedback_lower:
            return False

    # Default to no revision if unclear
    return False

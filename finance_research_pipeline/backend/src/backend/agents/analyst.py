"""Analyst agent for synthesizing research into comprehensive analysis."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType

logger = get_logger(__name__)

ANALYST_SYSTEM_PROMPT = """You are a senior equity research analyst with expertise in fundamental analysis.
Your task is to synthesize all available research data into a comprehensive investment analysis.

Your analysis should cover:
1. **Company Overview**: Brief summary of the business
2. **Market Position**: Competitive advantages and market share
3. **Financial Health**: Key metrics and trends
4. **Growth Prospects**: Revenue and earnings outlook
5. **Risk Assessment**: Key risks to the investment thesis
6. **Investment Thesis**: Bull and bear cases

Be objective, thorough, and base your analysis on the data provided.
Highlight both opportunities and risks."""


def create_analyst_agent(llm: BaseChatModel):
    """
    Create the analyst agent function.

    Args:
        llm: Language model to use

    Returns:
        Analyst agent function
    """

    async def analyst_node(state: ResearchState) -> dict[str, Any]:
        """
        Analyst node that synthesizes all research data.

        Args:
            state: Current research state

        Returns:
            Updated state with analysis
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        ticker = state.get("ticker_symbol", "N/A")

        logger.info(f"Analyst processing data for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.ANALYST.value] = AgentProgress(
            agent_type=AgentType.ANALYST,
            status=AgentStatus.RUNNING,
            message="Synthesizing research data",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        try:
            # Gather all research data
            web_data = state.get("web_research_data", {})
            financial_data = state.get("financial_data", {})
            news_data = state.get("news_data", {})
            additional_context = state.get("additional_context", "")

            # Build comprehensive analysis prompt
            agent_progress[AgentType.ANALYST.value].message = "Building analysis framework"
            agent_progress[AgentType.ANALYST.value].progress = 30.0

            analysis_prompt = f"""Conduct a comprehensive investment analysis for {company_name} ({ticker}).

## Research Data Available:

### Company Background:
{web_data.get('synthesis', 'No web research data available')}

### Financial Analysis:
{financial_data.get('analysis_summary', 'No financial data available')}

### News & Sentiment:
{news_data.get('analysis_summary', 'No news analysis available')}

{f"### Additional Context: {additional_context}" if additional_context else ""}

## Your Task:
Provide a comprehensive investment analysis covering:

1. **Executive Summary** (2-3 sentences)
2. **Company Overview**
   - Business model and key products/services
   - Market position and competitive landscape
3. **Financial Analysis**
   - Valuation assessment
   - Financial health indicators
   - Growth trends
4. **Market Analysis**
   - Industry dynamics
   - Competitive positioning
   - Growth opportunities
5. **Risk Assessment**
   - Key business risks
   - Financial risks
   - Market/industry risks
6. **Investment Thesis**
   - Bull case (reasons to be optimistic)
   - Bear case (reasons to be cautious)
   - Key catalysts to watch
7. **Recommendations**
   - 3-5 actionable recommendations for investors

Be thorough, objective, and data-driven in your analysis."""

            # Generate market analysis
            agent_progress[AgentType.ANALYST.value].message = "Generating market analysis"
            agent_progress[AgentType.ANALYST.value].progress = 60.0

            messages = [
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=analysis_prompt),
            ]

            analysis_response = await llm.ainvoke(messages)
            market_analysis = analysis_response.content

            # Generate risk assessment
            agent_progress[AgentType.ANALYST.value].message = "Assessing risks"
            agent_progress[AgentType.ANALYST.value].progress = 80.0

            risk_prompt = f"""Based on your analysis of {company_name}, provide a detailed risk assessment:

1. **Business Risks**: Operational, competitive, and strategic risks
2. **Financial Risks**: Balance sheet, liquidity, and debt risks
3. **Market Risks**: Industry, macroeconomic, and regulatory risks
4. **ESG Risks**: Environmental, social, and governance considerations
5. **Risk Mitigation**: How the company addresses these risks

Rate the overall risk level as: Low, Moderate, High, or Very High
Explain your rating."""

            risk_messages = [
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=risk_prompt),
            ]

            risk_response = await llm.ainvoke(risk_messages)
            risk_assessment = risk_response.content

            # Extract recommendations
            recommendations = _extract_recommendations(market_analysis)

            # Mark as completed
            agent_progress[AgentType.ANALYST.value] = AgentProgress(
                agent_type=AgentType.ANALYST,
                status=AgentStatus.COMPLETED,
                message="Analysis completed",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=market_analysis[:500],
            )

            logger.info(f"Analyst completed analysis for {company_name}")

            return {
                "market_analysis": market_analysis,
                "risk_assessment": risk_assessment,
                "recommendations": recommendations,
                "agent_progress": agent_progress,
                "current_agent": AgentType.ANALYST,
                "overall_progress": calculate_overall_progress(state),
            }

        except Exception as e:
            logger.error(f"Analyst error: {e}")
            agent_progress[AgentType.ANALYST.value] = AgentProgress(
                agent_type=AgentType.ANALYST,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )

            return {
                "agent_progress": agent_progress,
                "current_agent": AgentType.ANALYST,
                "error_message": str(e),
            }

    return analyst_node


def _extract_recommendations(analysis: str) -> list[str]:
    """
    Extract recommendations from the analysis text.

    Args:
        analysis: Full analysis text

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Look for recommendations section
    lines = analysis.split("\n")
    in_recommendations = False

    for line in lines:
        line = line.strip()

        # Check if we're in recommendations section
        if "recommendation" in line.lower() and ("##" in line or "**" in line):
            in_recommendations = True
            continue

        # Check if we've moved to a new section
        if in_recommendations and line.startswith(("##", "**")) and "recommendation" not in line.lower():
            break

        # Extract recommendation items
        if in_recommendations and line:
            # Handle numbered items
            if line[0].isdigit() and "." in line[:3]:
                rec = line.split(".", 1)[1].strip()
                if rec:
                    recommendations.append(rec)
            # Handle bullet points
            elif line.startswith(("-", "*", "•")):
                rec = line.lstrip("-*• ").strip()
                if rec:
                    recommendations.append(rec)

    # If no recommendations found, create generic ones
    if not recommendations:
        recommendations = [
            "Review the company's quarterly earnings reports for trend analysis",
            "Monitor industry developments and competitive dynamics",
            "Consider position sizing based on risk tolerance",
            "Set price alerts for key support and resistance levels",
            "Stay informed about regulatory and market changes",
        ]

    return recommendations[:7]  # Limit to 7 recommendations

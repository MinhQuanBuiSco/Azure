"""Writer agent for generating comprehensive research reports."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType

logger = get_logger(__name__)

WRITER_SYSTEM_PROMPT = """You are an expert financial report writer with experience creating institutional-quality research reports.

Your reports should be:
- Professional and well-structured
- Data-driven with clear citations of metrics
- Balanced, presenting both opportunities and risks
- Actionable, with clear recommendations
- Easy to read with appropriate headers and sections

Follow this structure:
1. Executive Summary (key takeaways in 3-5 bullet points)
2. Company Overview
3. Financial Analysis
4. Market & Competitive Analysis
5. News & Sentiment Overview
6. Risk Assessment
7. Investment Thesis
8. Recommendations
9. Appendix (key metrics summary)

Write in a professional, objective tone suitable for institutional investors."""

REVISION_PROMPT = """Please revise the report based on the following feedback:

{feedback}

Maintain the same structure but address all the points raised in the review.
Improve clarity, accuracy, and completeness where noted."""


def create_writer_agent(llm: BaseChatModel):
    """
    Create the writer agent function.

    Args:
        llm: Language model to use

    Returns:
        Writer agent function
    """

    async def writer_node(state: ResearchState) -> dict[str, Any]:
        """
        Writer node that generates the final report.

        Args:
            state: Current research state

        Returns:
            Updated state with full report
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        ticker = state.get("ticker_symbol", "N/A")
        revision_needed = state.get("revision_needed", False)
        review_feedback = state.get("review_feedback")

        logger.info(f"Writer {'revising' if revision_needed else 'generating'} report for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.WRITER.value] = AgentProgress(
            agent_type=AgentType.WRITER,
            status=AgentStatus.RUNNING,
            message="Generating report" if not revision_needed else "Revising report",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        try:
            # Gather all analysis data
            market_analysis = state.get("market_analysis", "")
            risk_assessment = state.get("risk_assessment", "")
            recommendations = state.get("recommendations", [])
            web_data = state.get("web_research_data", {})
            financial_data = state.get("financial_data", {})
            news_data = state.get("news_data", {})

            if revision_needed and review_feedback:
                # Revise existing report
                agent_progress[AgentType.WRITER.value].message = "Incorporating feedback"
                agent_progress[AgentType.WRITER.value].progress = 30.0

                existing_report = state.get("full_report", "")

                revision_prompt = f"""Here is the existing report:

{existing_report}

{REVISION_PROMPT.format(feedback=review_feedback)}"""

                messages = [
                    SystemMessage(content=WRITER_SYSTEM_PROMPT),
                    HumanMessage(content=revision_prompt),
                ]

            else:
                # Generate new report
                agent_progress[AgentType.WRITER.value].message = "Drafting report sections"
                agent_progress[AgentType.WRITER.value].progress = 30.0

                report_prompt = f"""Generate a comprehensive investment research report for {company_name} ({ticker}).

## Available Research Data:

### Market Analysis:
{market_analysis}

### Risk Assessment:
{risk_assessment}

### Company Background:
{web_data.get('synthesis', 'Not available')}

### Financial Data Summary:
{financial_data.get('analysis_summary', 'Not available')}

Stock Information:
{_format_stock_summary(financial_data.get('stock_info', {}))}

Key Metrics:
{_format_metrics_summary(financial_data.get('metrics', {}))}

### News & Sentiment:
{news_data.get('analysis_summary', 'Not available')}

Sentiment: {news_data.get('sentiment', {}).get('overall_sentiment', 'Neutral')}

### Recommendations:
{chr(10).join(f'- {rec}' for rec in recommendations) if recommendations else 'See analysis for recommendations'}

## Report Requirements:
Generate a professional research report following this structure:

1. **Executive Summary**
   - Key investment highlights (3-5 bullet points)
   - Overall assessment

2. **Company Overview**
   - Business description
   - Key products/services
   - Market position

3. **Financial Analysis**
   - Valuation metrics with interpretation
   - Financial health assessment
   - Growth trends

4. **Market & Competitive Analysis**
   - Industry dynamics
   - Competitive positioning
   - Market opportunities

5. **News & Sentiment Analysis**
   - Recent developments
   - Market sentiment
   - Key events

6. **Risk Assessment**
   - Key risks by category
   - Risk mitigation factors

7. **Investment Thesis**
   - Bull case
   - Bear case
   - Key catalysts

8. **Recommendations**
   - Actionable investment recommendations

9. **Key Metrics Summary** (Table format)
   - Stock price, P/E, Market Cap, etc.

Make the report comprehensive yet readable, approximately 2000-3000 words."""

                messages = [
                    SystemMessage(content=WRITER_SYSTEM_PROMPT),
                    HumanMessage(content=report_prompt),
                ]

            # Generate report
            agent_progress[AgentType.WRITER.value].message = "Writing report"
            agent_progress[AgentType.WRITER.value].progress = 70.0

            report_response = await llm.ainvoke(messages)
            full_report = report_response.content

            # Generate executive summary
            agent_progress[AgentType.WRITER.value].message = "Finalizing executive summary"
            agent_progress[AgentType.WRITER.value].progress = 90.0

            summary_prompt = f"""Based on this research report for {company_name}, provide a concise executive summary (3-5 sentences) that captures:
1. The company's core business and position
2. Key financial highlights
3. Overall investment assessment
4. Primary risk to consider

Report excerpt:
{full_report[:3000]}..."""

            summary_messages = [
                SystemMessage(content="You are a financial analyst writing executive summaries."),
                HumanMessage(content=summary_prompt),
            ]

            summary_response = await llm.ainvoke(summary_messages)
            executive_summary = summary_response.content

            # Mark as completed
            agent_progress[AgentType.WRITER.value] = AgentProgress(
                agent_type=AgentType.WRITER,
                status=AgentStatus.COMPLETED,
                message="Report generated",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=executive_summary[:500],
            )

            logger.info(f"Writer completed report for {company_name}")

            # Increment revision count if this was a revision
            revision_count = state.get("revision_count", 0)
            if revision_needed:
                revision_count += 1

            return {
                "full_report": full_report,
                "executive_summary": executive_summary,
                "revision_needed": False,  # Clear revision flag
                "revision_count": revision_count,
                "agent_progress": agent_progress,
                "current_agent": AgentType.WRITER,
                "overall_progress": calculate_overall_progress(state),
            }

        except Exception as e:
            logger.error(f"Writer error: {e}")
            agent_progress[AgentType.WRITER.value] = AgentProgress(
                agent_type=AgentType.WRITER,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )

            return {
                "agent_progress": agent_progress,
                "current_agent": AgentType.WRITER,
                "error_message": str(e),
            }

    return writer_node


def _format_stock_summary(stock_info: dict[str, Any]) -> str:
    """Format stock info summary."""
    if not stock_info or "error" in stock_info:
        return "Not available"

    parts = []
    if price := stock_info.get("price"):
        parts.append(f"Current Price: ${price.get('current', 'N/A')}")
        parts.append(f"52W Range: ${price.get('fifty_two_week_low', 'N/A')} - ${price.get('fifty_two_week_high', 'N/A')}")

    if mc := stock_info.get("market_cap"):
        if isinstance(mc, (int, float)):
            parts.append(f"Market Cap: ${mc/1e9:.2f}B" if mc > 1e9 else f"Market Cap: ${mc/1e6:.2f}M")

    return " | ".join(parts) if parts else "Not available"


def _format_metrics_summary(metrics: dict[str, Any]) -> str:
    """Format key metrics summary."""
    if not metrics or "error" in metrics:
        return "Not available"

    parts = []

    if val := metrics.get("valuation"):
        parts.append(f"P/E: {val.get('pe_ratio', 'N/A')}")
        parts.append(f"Forward P/E: {val.get('forward_pe', 'N/A')}")
        parts.append(f"PEG: {val.get('peg_ratio', 'N/A')}")

    if prof := metrics.get("profitability"):
        margin = prof.get("profit_margin")
        if margin:
            parts.append(f"Profit Margin: {margin*100:.1f}%")
        roe = prof.get("return_on_equity")
        if roe:
            parts.append(f"ROE: {roe*100:.1f}%")

    return " | ".join(parts) if parts else "Not available"

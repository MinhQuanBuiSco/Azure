"""Financial data agent using yfinance for stock data retrieval."""

from datetime import datetime, UTC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from backend.agents.state import ResearchState, calculate_overall_progress
from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentStatus, AgentType
from backend.tools.yfinance_tool import (
    get_analyst_recommendations,
    get_financial_metrics,
    get_historical_prices,
    get_stock_info,
    lookup_ticker,
)

logger = get_logger(__name__)

FINANCIAL_ANALYSIS_PROMPT = """You are a financial analyst specializing in equity research.
Analyze the provided financial data and provide insights on:
1. Valuation metrics and how they compare to industry averages
2. Financial health indicators
3. Growth trends and momentum
4. Analyst sentiment and price targets
5. Key risks and opportunities based on the data

Be factual and base your analysis only on the data provided."""


def create_financial_data_agent(llm: BaseChatModel):
    """
    Create the financial data agent function.

    Args:
        llm: Language model to use

    Returns:
        Financial data agent function
    """

    async def financial_data_node(state: ResearchState) -> dict[str, Any]:
        """
        Financial data node that gathers stock information.

        Args:
            state: Current research state

        Returns:
            Updated state with financial data
        """
        research_id = state["research_id"]
        company_name = state["company_name"]
        ticker = state.get("ticker_symbol")
        time_period = state.get("time_period_days", 30)

        logger.info(f"Financial data collection starting for {company_name}")

        # Update agent status
        agent_progress = state.get("agent_progress", {}).copy()
        agent_progress[AgentType.FINANCIAL_DATA.value] = AgentProgress(
            agent_type=AgentType.FINANCIAL_DATA,
            status=AgentStatus.RUNNING,
            message="Starting financial data collection",
            progress=10.0,
            started_at=datetime.now(UTC),
        )

        financial_data: dict[str, Any] = {}
        detected_ticker = ticker

        try:
            # Lookup ticker if not provided
            if not ticker:
                agent_progress[AgentType.FINANCIAL_DATA.value].message = "Looking up ticker symbol"
                agent_progress[AgentType.FINANCIAL_DATA.value].progress = 15.0

                ticker_result = lookup_ticker.invoke({"company_name": company_name})
                if ticker_result.get("ticker"):
                    detected_ticker = ticker_result["ticker"]
                    financial_data["ticker_lookup"] = ticker_result
                    logger.info(f"Found ticker: {detected_ticker} for {company_name}")
                else:
                    logger.warning(f"Could not find ticker for {company_name}")
                    agent_progress[AgentType.FINANCIAL_DATA.value] = AgentProgress(
                        agent_type=AgentType.FINANCIAL_DATA,
                        status=AgentStatus.ERROR,
                        message="Could not find ticker symbol",
                        progress=0.0,
                        error="Ticker symbol not found",
                    )
                    return {
                        "financial_data": {"error": "Ticker not found"},
                        "agent_progress": agent_progress,
                        "current_agent": AgentType.FINANCIAL_DATA,
                    }

            # Get stock information
            agent_progress[AgentType.FINANCIAL_DATA.value].message = "Fetching stock information"
            agent_progress[AgentType.FINANCIAL_DATA.value].progress = 30.0

            stock_info = get_stock_info.invoke({"ticker": detected_ticker})
            financial_data["stock_info"] = stock_info

            # Get financial metrics
            agent_progress[AgentType.FINANCIAL_DATA.value].message = "Analyzing financial metrics"
            agent_progress[AgentType.FINANCIAL_DATA.value].progress = 50.0

            metrics = get_financial_metrics.invoke({"ticker": detected_ticker})
            financial_data["metrics"] = metrics

            # Get historical prices
            agent_progress[AgentType.FINANCIAL_DATA.value].message = "Fetching historical prices"
            agent_progress[AgentType.FINANCIAL_DATA.value].progress = 70.0

            historical = get_historical_prices.invoke({
                "ticker": detected_ticker,
                "period_days": time_period,
            })
            financial_data["historical"] = historical

            # Get analyst recommendations
            agent_progress[AgentType.FINANCIAL_DATA.value].message = "Gathering analyst recommendations"
            agent_progress[AgentType.FINANCIAL_DATA.value].progress = 85.0

            recommendations = get_analyst_recommendations.invoke({"ticker": detected_ticker})
            financial_data["recommendations"] = recommendations

            # Generate analysis summary
            agent_progress[AgentType.FINANCIAL_DATA.value].message = "Generating analysis"
            agent_progress[AgentType.FINANCIAL_DATA.value].progress = 95.0

            analysis_prompt = f"""Analyze the following financial data for {company_name} ({detected_ticker}):

Stock Information:
{_format_stock_info(stock_info)}

Financial Metrics:
{_format_metrics(metrics)}

Historical Performance ({time_period} days):
{_format_historical(historical)}

Analyst Recommendations:
{_format_recommendations(recommendations)}

Provide a concise financial analysis covering valuation, financial health, momentum, and analyst sentiment."""

            messages = [
                SystemMessage(content=FINANCIAL_ANALYSIS_PROMPT),
                HumanMessage(content=analysis_prompt),
            ]

            analysis = await llm.ainvoke(messages)
            financial_data["analysis_summary"] = analysis.content

            # Mark as completed
            agent_progress[AgentType.FINANCIAL_DATA.value] = AgentProgress(
                agent_type=AgentType.FINANCIAL_DATA,
                status=AgentStatus.COMPLETED,
                message="Financial data collection completed",
                progress=100.0,
                completed_at=datetime.now(UTC),
                output_preview=analysis.content[:500] if analysis.content else None,
            )

            logger.info(f"Financial data collection completed for {detected_ticker}")

        except Exception as e:
            logger.error(f"Financial data error: {e}")
            agent_progress[AgentType.FINANCIAL_DATA.value] = AgentProgress(
                agent_type=AgentType.FINANCIAL_DATA,
                status=AgentStatus.ERROR,
                message=f"Error: {str(e)}",
                progress=0.0,
                error=str(e),
            )
            financial_data["error"] = str(e)

        return {
            "financial_data": financial_data,
            "ticker_symbol": detected_ticker,
            "agent_progress": agent_progress,
            "current_agent": AgentType.FINANCIAL_DATA,
            "overall_progress": calculate_overall_progress(state),
        }

    return financial_data_node


def _format_stock_info(info: dict[str, Any]) -> str:
    """Format stock info for analysis."""
    if not info or "error" in info:
        return "Stock information unavailable"

    parts = [
        f"Name: {info.get('name', 'N/A')}",
        f"Sector: {info.get('sector', 'N/A')}",
        f"Industry: {info.get('industry', 'N/A')}",
    ]

    if price := info.get("price"):
        parts.extend([
            f"Current Price: ${price.get('current', 'N/A')}",
            f"52-Week High: ${price.get('fifty_two_week_high', 'N/A')}",
            f"52-Week Low: ${price.get('fifty_two_week_low', 'N/A')}",
        ])

    if mc := info.get("market_cap"):
        parts.append(f"Market Cap: ${mc:,.0f}" if isinstance(mc, (int, float)) else f"Market Cap: {mc}")

    return "\n".join(parts)


def _format_metrics(metrics: dict[str, Any]) -> str:
    """Format financial metrics for analysis."""
    if not metrics or "error" in metrics:
        return "Financial metrics unavailable"

    parts = []

    if val := metrics.get("valuation"):
        parts.append("Valuation:")
        parts.append(f"  P/E Ratio: {val.get('pe_ratio', 'N/A')}")
        parts.append(f"  Forward P/E: {val.get('forward_pe', 'N/A')}")
        parts.append(f"  PEG Ratio: {val.get('peg_ratio', 'N/A')}")
        parts.append(f"  Price/Book: {val.get('price_to_book', 'N/A')}")

    if prof := metrics.get("profitability"):
        parts.append("Profitability:")
        parts.append(f"  Profit Margin: {_format_pct(prof.get('profit_margin'))}")
        parts.append(f"  ROE: {_format_pct(prof.get('return_on_equity'))}")
        parts.append(f"  ROA: {_format_pct(prof.get('return_on_assets'))}")

    if earn := metrics.get("earnings"):
        parts.append("Earnings:")
        parts.append(f"  EPS: ${earn.get('eps', 'N/A')}")
        parts.append(f"  Earnings Growth: {_format_pct(earn.get('earnings_growth'))}")
        parts.append(f"  Revenue Growth: {_format_pct(earn.get('revenue_growth'))}")

    return "\n".join(parts)


def _format_historical(historical: dict[str, Any]) -> str:
    """Format historical data for analysis."""
    if not historical or "error" in historical:
        return "Historical data unavailable"

    if stats := historical.get("statistics"):
        return (
            f"Period: {historical.get('period_days', 'N/A')} days\n"
            f"Start Price: ${stats.get('start_price', 'N/A')}\n"
            f"End Price: ${stats.get('end_price', 'N/A')}\n"
            f"Change: {stats.get('change_percent', 'N/A')}%\n"
            f"Period High: ${stats.get('high', 'N/A')}\n"
            f"Period Low: ${stats.get('low', 'N/A')}\n"
            f"Volatility (Std Dev): ${stats.get('volatility', 'N/A')}"
        )

    return "Historical statistics unavailable"


def _format_recommendations(recs: dict[str, Any]) -> str:
    """Format analyst recommendations for analysis."""
    if not recs or "error" in recs:
        return "Analyst recommendations unavailable"

    parts = []

    if targets := recs.get("price_targets"):
        parts.append(f"Target Price Mean: ${targets.get('target_mean', 'N/A')}")
        parts.append(f"Target High: ${targets.get('target_high', 'N/A')}")
        parts.append(f"Target Low: ${targets.get('target_low', 'N/A')}")
        parts.append(f"Number of Analysts: {targets.get('number_of_analysts', 'N/A')}")

    if rec := recs.get("recommendation"):
        parts.append(f"Consensus: {rec.upper()}")

    return "\n".join(parts)


def _format_pct(value: float | None) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"

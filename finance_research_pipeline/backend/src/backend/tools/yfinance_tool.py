"""Yahoo Finance tool for financial data retrieval."""

from datetime import datetime, timedelta
from typing import Any

import yfinance as yf
from langchain_core.tools import tool

from backend.core.logging import get_logger

logger = get_logger(__name__)


@tool
def get_stock_info(ticker: str) -> dict[str, Any]:
    """
    Get comprehensive stock information for a ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Dictionary containing stock information including price, market cap, etc.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "name": info.get("longName", info.get("shortName", "")),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", ""),
            "price": {
                "current": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            },
            "volume": {
                "current": info.get("volume") or info.get("regularMarketVolume"),
                "average": info.get("averageVolume"),
                "average_10_day": info.get("averageVolume10days"),
            },
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "currency": info.get("currency", "USD"),
        }

    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


@tool
def get_financial_metrics(ticker: str) -> dict[str, Any]:
    """
    Get key financial metrics and ratios for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing financial metrics like P/E, EPS, etc.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "valuation": {
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            },
            "profitability": {
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "gross_margin": info.get("grossMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
            },
            "earnings": {
                "eps": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
                "earnings_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
            },
            "dividends": {
                "dividend_rate": info.get("dividendRate"),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio"),
                "ex_dividend_date": info.get("exDividendDate"),
            },
            "balance_sheet": {
                "total_cash": info.get("totalCash"),
                "total_debt": info.get("totalDebt"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching financial metrics for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


@tool
def get_historical_prices(
    ticker: str,
    period_days: int = 30,
) -> dict[str, Any]:
    """
    Get historical price data for a stock.

    Args:
        ticker: Stock ticker symbol
        period_days: Number of days of historical data (default: 30)

    Returns:
        Dictionary containing historical price data and statistics
    """
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            return {"error": "No historical data available", "ticker": ticker}

        prices = []
        for date, row in hist.iterrows():
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        # Calculate statistics
        close_prices = hist["Close"]
        return {
            "ticker": ticker,
            "period_days": period_days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "statistics": {
                "start_price": round(close_prices.iloc[0], 2),
                "end_price": round(close_prices.iloc[-1], 2),
                "change_percent": round(
                    ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100,
                    2,
                ),
                "high": round(close_prices.max(), 2),
                "low": round(close_prices.min(), 2),
                "average": round(close_prices.mean(), 2),
                "volatility": round(close_prices.std(), 2),
                "total_volume": int(hist["Volume"].sum()),
                "average_volume": int(hist["Volume"].mean()),
            },
            "prices": prices[-10:],  # Last 10 days for brevity
        }

    except Exception as e:
        logger.error(f"Error fetching historical prices for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


@tool
def get_analyst_recommendations(ticker: str) -> dict[str, Any]:
    """
    Get analyst recommendations and price targets for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing analyst recommendations and targets
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        recommendations = []
        try:
            rec_df = stock.recommendations
            if rec_df is not None and not rec_df.empty:
                recent_recs = rec_df.tail(10)
                for date, row in recent_recs.iterrows():
                    recommendations.append({
                        "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
                        "firm": row.get("Firm", ""),
                        "to_grade": row.get("To Grade", ""),
                        "from_grade": row.get("From Grade", ""),
                        "action": row.get("Action", ""),
                    })
        except Exception:
            pass

        return {
            "ticker": ticker,
            "price_targets": {
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
                "target_mean": info.get("targetMeanPrice"),
                "target_median": info.get("targetMedianPrice"),
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
            },
            "recommendation": info.get("recommendationKey", ""),
            "recommendation_mean": info.get("recommendationMean"),
            "recent_recommendations": recommendations,
        }

    except Exception as e:
        logger.error(f"Error fetching analyst recommendations for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


@tool
def lookup_ticker(company_name: str) -> dict[str, Any]:
    """
    Look up a ticker symbol from a company name.

    Args:
        company_name: Name of the company

    Returns:
        Dictionary containing potential ticker matches
    """
    try:
        search = yf.Ticker(company_name)
        info = search.info

        if info.get("symbol"):
            return {
                "company_name": company_name,
                "ticker": info.get("symbol"),
                "name": info.get("longName", info.get("shortName", "")),
                "exchange": info.get("exchange", ""),
            }

        # Try common variations
        variations = [
            company_name.upper(),
            company_name.replace(" ", ""),
            company_name.split()[0].upper() if " " in company_name else company_name,
        ]

        for variation in variations:
            try:
                test = yf.Ticker(variation)
                test_info = test.info
                if test_info.get("regularMarketPrice"):
                    return {
                        "company_name": company_name,
                        "ticker": variation,
                        "name": test_info.get("longName", test_info.get("shortName", "")),
                        "exchange": test_info.get("exchange", ""),
                    }
            except Exception:
                continue

        return {
            "company_name": company_name,
            "error": "Could not find ticker symbol",
            "suggestion": "Please provide the ticker symbol directly",
        }

    except Exception as e:
        logger.error(f"Error looking up ticker for {company_name}: {e}")
        return {"error": str(e), "company_name": company_name}

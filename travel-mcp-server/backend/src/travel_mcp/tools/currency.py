"""Currency exchange rate tool."""

from typing import Any

import structlog

from travel_mcp.config import get_settings
from travel_mcp.services.http_client import get_http_client
from travel_mcp.services.cache import get_cache_service

logger = structlog.get_logger()

EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"


async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float = 1.0,
) -> dict[str, Any]:
    """
    Get current exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g., 'USD', 'EUR', 'GBP')
        to_currency: Target currency code (e.g., 'JPY', 'THB', 'MXN')
        amount: Amount to convert (default: 1.0)

    Returns:
        Dictionary containing exchange rate, converted amount, and rate info
    """
    settings = get_settings()
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if not settings.exchangerate_api_key:
        return _get_mock_exchange_rate(from_currency, to_currency, amount)

    # Check cache
    cache_params = {"from": from_currency, "to": to_currency}
    cache = await get_cache_service()
    cached = await cache.get("exchange", cache_params)
    if cached:
        rate = cached["rate"]
        return {
            **cached,
            "amount": amount,
            "converted_amount": round(amount * rate, 2),
        }

    http = get_http_client()

    try:
        url = f"{EXCHANGERATE_API_URL}/{settings.exchangerate_api_key}/pair/{from_currency}/{to_currency}"
        data = await http.get(url)

        if data.get("result") != "success":
            return {
                "error": f"Failed to get exchange rate: {data.get('error-type', 'Unknown error')}",
            }

        rate = data.get("conversion_rate", 0)
        result = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "amount": amount,
            "converted_amount": round(amount * rate, 2),
            "last_updated": data.get("time_last_update_utc", ""),
        }

        # Cache rate (without amount) for 1 hour
        await cache.set(
            "exchange",
            cache_params,
            {"from_currency": from_currency, "to_currency": to_currency, "rate": rate},
            ttl=3600,
        )

        return result

    except Exception as e:
        logger.error("Exchange rate fetch failed", error=str(e))
        return {"error": f"Failed to get exchange rate: {str(e)}"}


# Common exchange rates for mock data
MOCK_RATES = {
    ("USD", "EUR"): 0.92,
    ("USD", "GBP"): 0.79,
    ("USD", "JPY"): 149.50,
    ("USD", "CNY"): 7.24,
    ("USD", "THB"): 35.20,
    ("USD", "MXN"): 17.15,
    ("USD", "CAD"): 1.36,
    ("USD", "AUD"): 1.53,
    ("USD", "INR"): 83.12,
    ("USD", "KRW"): 1320.50,
    ("EUR", "USD"): 1.09,
    ("EUR", "GBP"): 0.86,
    ("EUR", "JPY"): 162.50,
    ("GBP", "USD"): 1.27,
    ("GBP", "EUR"): 1.17,
}


def _get_mock_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float,
) -> dict[str, Any]:
    """Return mock exchange rate data."""
    # Try direct rate
    rate = MOCK_RATES.get((from_currency, to_currency))

    # Try inverse rate
    if rate is None:
        inverse = MOCK_RATES.get((to_currency, from_currency))
        if inverse:
            rate = 1 / inverse

    # Default rate
    if rate is None:
        rate = 1.0 if from_currency == to_currency else 1.15

    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": round(rate, 4),
        "amount": amount,
        "converted_amount": round(amount * rate, 2),
        "last_updated": "Mock data",
        "note": "Mock data - set EXCHANGERATE_API_KEY for real results",
    }

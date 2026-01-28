"""Travel Planner MCP Server - Main entry point."""

import structlog
from fastmcp import FastMCP

from travel_mcp.config import get_settings
from travel_mcp.tools.flights import search_flights
from travel_mcp.tools.hotels import search_hotels
from travel_mcp.tools.weather import get_weather
from travel_mcp.tools.places import search_attractions, search_restaurants
from travel_mcp.tools.currency import get_exchange_rate
from travel_mcp.tools.visa import get_visa_info
from travel_mcp.tools.planner import plan_itinerary, calculate_budget
from travel_mcp.resources.destinations import (
    get_destination_overview,
    get_destination_tips,
    get_popular_destinations,
)
from travel_mcp.prompts.templates import (
    weekend_getaway_prompt,
    family_vacation_prompt,
    budget_backpacker_prompt,
    luxury_escape_prompt,
    romantic_trip_prompt,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Initialize settings
settings = get_settings()

# Create MCP Server
mcp = FastMCP(
    name=settings.server_name,
    version=settings.server_version,
)


# ============================================================================
# TOOLS - Executable functions for travel planning
# ============================================================================

@mcp.tool
async def tool_search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    passengers: int = 1,
    travel_class: str = "economy",
) -> dict:
    """
    Search for available flights between two airports.

    Args:
        origin: Departure airport code (e.g., 'SFO', 'LAX', 'JFK')
        destination: Arrival airport code (e.g., 'NRT', 'CDG', 'LHR')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date for round trips (YYYY-MM-DD)
        passengers: Number of passengers (default: 1)
        travel_class: Class - economy, premium_economy, business, first

    Returns:
        Flight options with prices, times, and airline information
    """
    logger.info("Searching flights", origin=origin, destination=destination)
    return await search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        passengers=passengers,
        travel_class=travel_class,
    )


@mcp.tool
async def tool_search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 2,
    rooms: int = 1,
    min_price: int | None = None,
    max_price: int | None = None,
) -> dict:
    """
    Search for available hotels in a location.

    Args:
        location: City or area (e.g., 'Tokyo, Japan', 'Paris, France')
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)
        min_price: Minimum price per night in USD (optional)
        max_price: Maximum price per night in USD (optional)

    Returns:
        Hotel options with prices, ratings, and amenities
    """
    logger.info("Searching hotels", location=location)
    return await search_hotels(
        location=location,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        guests=guests,
        rooms=rooms,
        min_price=min_price,
        max_price=max_price,
    )


@mcp.tool
async def tool_get_weather(
    location: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Get weather forecast for a location.

    Args:
        location: City name (e.g., 'Tokyo', 'Paris, France')
        start_date: Start date for forecast (YYYY-MM-DD), defaults to today
        end_date: End date for forecast (YYYY-MM-DD), defaults to 5 days later

    Returns:
        Weather forecast with temperatures, conditions, and packing tips
    """
    logger.info("Getting weather", location=location)
    return await get_weather(
        location=location,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool
async def tool_search_attractions(
    location: str,
    categories: list[str] | None = None,
    max_results: int = 10,
) -> dict:
    """
    Search for tourist attractions and points of interest.

    Args:
        location: City or area (e.g., 'Tokyo, Japan')
        categories: Filter by type - temple, museum, park, landmark, shopping, nightlife
        max_results: Maximum results to return (default: 10)

    Returns:
        Attractions with ratings, descriptions, and visitor information
    """
    logger.info("Searching attractions", location=location)
    return await search_attractions(
        location=location,
        categories=categories,
        max_results=max_results,
    )


@mcp.tool
async def tool_search_restaurants(
    location: str,
    cuisine: str | None = None,
    price_level: str | None = None,
    max_results: int = 10,
) -> dict:
    """
    Search for restaurants in a location.

    Args:
        location: City or area (e.g., 'Tokyo, Japan')
        cuisine: Type of cuisine (e.g., 'japanese', 'italian', 'local')
        price_level: Price range - budget, moderate, expensive, luxury
        max_results: Maximum results to return (default: 10)

    Returns:
        Restaurants with ratings, cuisine type, and price information
    """
    logger.info("Searching restaurants", location=location)
    return await search_restaurants(
        location=location,
        cuisine=cuisine,
        price_level=price_level,
        max_results=max_results,
    )


@mcp.tool
async def tool_get_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float = 1.0,
) -> dict:
    """
    Get current exchange rate between two currencies.

    Args:
        from_currency: Source currency code (e.g., 'USD', 'EUR')
        to_currency: Target currency code (e.g., 'JPY', 'THB')
        amount: Amount to convert (default: 1.0)

    Returns:
        Exchange rate and converted amount
    """
    logger.info("Getting exchange rate", from_currency=from_currency, to_currency=to_currency)
    return await get_exchange_rate(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
    )


@mcp.tool
async def tool_get_visa_info(
    passport_country: str,
    destination: str,
) -> dict:
    """
    Get visa requirements for traveling to a destination.

    Args:
        passport_country: Country of passport (e.g., 'US', 'UK', 'Germany')
        destination: Destination country (e.g., 'Japan', 'France')

    Returns:
        Visa requirements, duration of stay, and application information
    """
    logger.info("Getting visa info", passport=passport_country, destination=destination)
    return await get_visa_info(
        passport_country=passport_country,
        destination=destination,
    )


@mcp.tool
async def tool_plan_itinerary(
    destination: str,
    days: int,
    interests: list[str] | None = None,
    pace: str = "moderate",
) -> dict:
    """
    Generate a day-by-day travel itinerary.

    Args:
        destination: Destination city (e.g., 'Tokyo', 'Paris')
        days: Number of days for the trip
        interests: List of interests - culture, food, nature, shopping, nightlife
        pace: Travel pace - relaxed, moderate, intensive

    Returns:
        Day-by-day itinerary with activities, meals, and tips
    """
    logger.info("Planning itinerary", destination=destination, days=days)
    return await plan_itinerary(
        destination=destination,
        days=days,
        interests=interests,
        pace=pace,
    )


@mcp.tool
async def tool_calculate_budget(
    destination: str,
    days: int,
    travelers: int = 1,
    travel_style: str = "moderate",
    include_flights: bool = True,
) -> dict:
    """
    Calculate estimated trip budget.

    Args:
        destination: Destination city
        days: Number of days
        travelers: Number of travelers (default: 1)
        travel_style: Style - budget, moderate, luxury
        include_flights: Include flight estimate (default: True)

    Returns:
        Detailed budget breakdown with totals and tips
    """
    logger.info("Calculating budget", destination=destination, style=travel_style)
    return await calculate_budget(
        destination=destination,
        days=days,
        travelers=travelers,
        travel_style=travel_style,
        include_flights=include_flights,
    )


# ============================================================================
# RESOURCES - Read-only data about destinations
# ============================================================================

@mcp.resource("destination://{city}/overview")
def resource_destination_overview(city: str) -> dict:
    """Get comprehensive overview of a destination city."""
    return get_destination_overview(city)


@mcp.resource("destination://{city}/tips")
def resource_destination_tips(city: str) -> dict:
    """Get travel tips and local customs for a destination."""
    return get_destination_tips(city)


@mcp.resource("destinations://popular")
def resource_popular_destinations() -> dict:
    """Get list of popular travel destinations."""
    return get_popular_destinations()


# ============================================================================
# PROMPTS - Pre-defined templates for common travel scenarios
# ============================================================================

@mcp.prompt
def prompt_weekend_getaway(destination: str) -> str:
    """Plan a weekend getaway to a destination."""
    return weekend_getaway_prompt(destination)


@mcp.prompt
def prompt_family_vacation(destination: str, adults: int = 2, children: int = 2) -> str:
    """Plan a family-friendly vacation."""
    return family_vacation_prompt(destination, adults, children)


@mcp.prompt
def prompt_budget_backpacker(destination: str, days: int = 14) -> str:
    """Plan a budget backpacker trip."""
    return budget_backpacker_prompt(destination, days)


@mcp.prompt
def prompt_luxury_escape(destination: str, days: int = 5) -> str:
    """Plan a luxury travel experience."""
    return luxury_escape_prompt(destination, days)


@mcp.prompt
def prompt_romantic_trip(destination: str, occasion: str = "anniversary") -> str:
    """Plan a romantic trip for a special occasion."""
    return romantic_trip_prompt(destination, occasion)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Run the MCP server."""
    logger.info(
        "Starting Travel Planner MCP Server",
        name=settings.server_name,
        version=settings.server_version,
    )
    mcp.run()


if __name__ == "__main__":
    main()

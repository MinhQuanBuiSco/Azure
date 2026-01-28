"""Travel MCP Tools - External API integrations for travel planning."""

from travel_mcp.tools.flights import search_flights
from travel_mcp.tools.hotels import search_hotels
from travel_mcp.tools.weather import get_weather
from travel_mcp.tools.places import search_attractions, search_restaurants
from travel_mcp.tools.currency import get_exchange_rate
from travel_mcp.tools.visa import get_visa_info
from travel_mcp.tools.planner import plan_itinerary, calculate_budget

__all__ = [
    "search_flights",
    "search_hotels",
    "get_weather",
    "search_attractions",
    "search_restaurants",
    "get_exchange_rate",
    "get_visa_info",
    "plan_itinerary",
    "calculate_budget",
]

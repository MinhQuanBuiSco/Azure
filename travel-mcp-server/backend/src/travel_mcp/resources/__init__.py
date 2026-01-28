"""Travel MCP Resources - Static and dynamic data resources."""

from travel_mcp.resources.destinations import (
    get_destination_overview,
    get_destination_tips,
    get_popular_destinations,
)

__all__ = [
    "get_destination_overview",
    "get_destination_tips",
    "get_popular_destinations",
]

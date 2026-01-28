"""Hotel search tool using SerpAPI Google Hotels."""

from typing import Any

import structlog

from travel_mcp.config import get_settings
from travel_mcp.services.http_client import get_http_client
from travel_mcp.services.cache import get_cache_service

logger = structlog.get_logger()

SERPAPI_BASE_URL = "https://serpapi.com/search"


async def search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 2,
    rooms: int = 1,
    min_price: int | None = None,
    max_price: int | None = None,
    star_rating: int | None = None,
    max_results: int = 5,
) -> dict[str, Any]:
    """
    Search for available hotels in a location.

    Args:
        location: City or area to search (e.g., 'Tokyo, Japan', 'Paris, France')
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        guests: Number of guests (default: 2)
        rooms: Number of rooms (default: 1)
        min_price: Minimum price per night in USD (optional)
        max_price: Maximum price per night in USD (optional)
        star_rating: Minimum star rating 1-5 (optional)
        max_results: Maximum number of hotels to return (default: 5)

    Returns:
        Dictionary containing hotel options with prices, ratings, and amenities
    """
    settings = get_settings()

    if not settings.serpapi_api_key:
        return _get_mock_hotels(location, check_in_date, check_out_date)

    # Check cache
    cache_params = {
        "location": location,
        "check_in": check_in_date,
        "check_out": check_out_date,
        "guests": guests,
        "rooms": rooms,
    }

    cache = await get_cache_service()
    cached = await cache.get("hotels", cache_params)
    if cached:
        return cached

    # Make API request
    http = get_http_client()

    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": guests,
        "rooms": rooms,
        "currency": "USD",
        "hl": "en",
        "api_key": settings.serpapi_api_key,
    }

    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    if star_rating:
        params["hotel_class"] = star_rating

    try:
        data = await http.get(SERPAPI_BASE_URL, params=params)
        result = _parse_hotel_results(data, max_results)

        await cache.set("hotels", cache_params, result, ttl=1800)

        return result

    except Exception as e:
        logger.error("Hotel search failed", error=str(e))
        return {
            "error": f"Failed to search hotels: {str(e)}",
            "hotels": [],
        }


def _parse_hotel_results(data: dict[str, Any], max_results: int) -> dict[str, Any]:
    """Parse SerpAPI hotel results into clean format."""
    hotels = []

    properties = data.get("properties", [])

    for hotel in properties[:max_results]:
        hotels.append({
            "name": hotel.get("name", "Unknown Hotel"),
            "type": hotel.get("type", "Hotel"),
            "description": hotel.get("description", ""),
            "price_per_night": hotel.get("rate_per_night", {}).get("lowest", "N/A"),
            "total_price": hotel.get("total_rate", {}).get("lowest", "N/A"),
            "currency": "USD",
            "rating": hotel.get("overall_rating", 0),
            "reviews_count": hotel.get("reviews", 0),
            "star_rating": hotel.get("hotel_class", ""),
            "location": hotel.get("neighborhood", ""),
            "address": hotel.get("address", ""),
            "amenities": hotel.get("amenities", []),
            "images": hotel.get("images", [])[:3],
            "check_in_time": hotel.get("check_in_time", "15:00"),
            "check_out_time": hotel.get("check_out_time", "11:00"),
            "link": hotel.get("link", ""),
        })

    return {
        "search_metadata": {
            "location": data.get("search_parameters", {}).get("q", ""),
            "check_in": data.get("search_parameters", {}).get("check_in_date", ""),
            "check_out": data.get("search_parameters", {}).get("check_out_date", ""),
        },
        "hotels": hotels,
        "total_results": len(properties),
    }


def _get_mock_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
) -> dict[str, Any]:
    """Return mock hotel data for testing."""
    return {
        "search_metadata": {
            "location": location,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "note": "Mock data - set SERPAPI_API_KEY for real results",
        },
        "hotels": [
            {
                "name": f"Grand {location.split(',')[0]} Hotel",
                "type": "Hotel",
                "description": "Luxury hotel in the heart of the city with stunning views.",
                "price_per_night": "$245",
                "total_price": "$980",
                "currency": "USD",
                "rating": 4.7,
                "reviews_count": 2847,
                "star_rating": "5-star",
                "location": "City Center",
                "address": f"123 Main Street, {location}",
                "amenities": ["Free WiFi", "Pool", "Spa", "Restaurant", "Gym", "Room Service"],
                "images": [],
                "check_in_time": "15:00",
                "check_out_time": "11:00",
            },
            {
                "name": f"{location.split(',')[0]} Boutique Inn",
                "type": "Boutique Hotel",
                "description": "Charming boutique hotel with local character and modern comforts.",
                "price_per_night": "$165",
                "total_price": "$660",
                "currency": "USD",
                "rating": 4.5,
                "reviews_count": 1523,
                "star_rating": "4-star",
                "location": "Historic District",
                "address": f"456 Heritage Lane, {location}",
                "amenities": ["Free WiFi", "Breakfast Included", "Rooftop Bar", "Concierge"],
                "images": [],
                "check_in_time": "14:00",
                "check_out_time": "12:00",
            },
            {
                "name": f"Comfort Suites {location.split(',')[0]}",
                "type": "Hotel",
                "description": "Comfortable and affordable accommodation near transit.",
                "price_per_night": "$95",
                "total_price": "$380",
                "currency": "USD",
                "rating": 4.2,
                "reviews_count": 892,
                "star_rating": "3-star",
                "location": "Near Station",
                "address": f"789 Station Road, {location}",
                "amenities": ["Free WiFi", "Parking", "Breakfast", "Laundry"],
                "images": [],
                "check_in_time": "15:00",
                "check_out_time": "10:00",
            },
        ],
        "total_results": 3,
    }

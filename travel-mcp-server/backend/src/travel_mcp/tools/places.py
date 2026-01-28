"""Places search tools using Google Places API."""

from typing import Any

import structlog

from travel_mcp.config import get_settings
from travel_mcp.services.http_client import get_http_client
from travel_mcp.services.cache import get_cache_service

logger = structlog.get_logger()

GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place"


async def search_attractions(
    location: str,
    categories: list[str] | None = None,
    radius: int = 5000,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Search for tourist attractions and points of interest.

    Args:
        location: City or area to search (e.g., 'Tokyo, Japan')
        categories: List of categories to filter (e.g., ['temple', 'museum', 'park'])
                   Available: temple, museum, park, landmark, shopping, nightlife
        radius: Search radius in meters (default: 5000)
        max_results: Maximum number of results (default: 10)

    Returns:
        Dictionary containing attractions with ratings, descriptions, and opening hours
    """
    settings = get_settings()

    if not settings.google_places_api_key:
        return _get_mock_attractions(location, categories)

    cache_params = {"location": location, "categories": categories, "radius": radius}
    cache = await get_cache_service()
    cached = await cache.get("attractions", cache_params)
    if cached:
        return cached

    http = get_http_client()

    try:
        # First, geocode the location
        geocode_params = {
            "address": location,
            "key": settings.google_places_api_key,
        }
        geo_response = await http.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params=geocode_params,
        )

        if not geo_response.get("results"):
            return {"error": f"Location not found: {location}", "attractions": []}

        lat = geo_response["results"][0]["geometry"]["location"]["lat"]
        lng = geo_response["results"][0]["geometry"]["location"]["lng"]

        # Search for places
        place_types = _map_categories_to_types(categories)
        all_attractions = []

        for place_type in place_types:
            search_params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": settings.google_places_api_key,
            }

            response = await http.get(
                f"{GOOGLE_PLACES_URL}/nearbysearch/json",
                params=search_params,
            )

            places = response.get("results", [])
            for place in places:
                all_attractions.append(_parse_place(place))

        # Remove duplicates and sort by rating
        seen = set()
        unique_attractions = []
        for attr in all_attractions:
            if attr["name"] not in seen:
                seen.add(attr["name"])
                unique_attractions.append(attr)

        unique_attractions.sort(key=lambda x: x.get("rating", 0), reverse=True)
        result = {
            "location": location,
            "attractions": unique_attractions[:max_results],
            "total_found": len(unique_attractions),
        }

        await cache.set("attractions", cache_params, result, ttl=86400)  # 24h cache

        return result

    except Exception as e:
        logger.error("Attractions search failed", error=str(e))
        return {"error": f"Failed to search attractions: {str(e)}", "attractions": []}


async def search_restaurants(
    location: str,
    cuisine: str | None = None,
    price_level: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Search for restaurants in a location.

    Args:
        location: City or area to search (e.g., 'Tokyo, Japan')
        cuisine: Type of cuisine (e.g., 'japanese', 'italian', 'local')
        price_level: Price range - 'budget', 'moderate', 'expensive', 'luxury'
        max_results: Maximum number of results (default: 10)

    Returns:
        Dictionary containing restaurants with ratings, cuisine, and price info
    """
    settings = get_settings()

    if not settings.google_places_api_key:
        return _get_mock_restaurants(location, cuisine)

    cache_params = {"location": location, "cuisine": cuisine, "price": price_level}
    cache = await get_cache_service()
    cached = await cache.get("restaurants", cache_params)
    if cached:
        return cached

    http = get_http_client()

    try:
        # Build search query
        query = f"restaurants in {location}"
        if cuisine:
            query = f"{cuisine} restaurants in {location}"

        search_params = {
            "query": query,
            "type": "restaurant",
            "key": settings.google_places_api_key,
        }

        response = await http.get(
            f"{GOOGLE_PLACES_URL}/textsearch/json",
            params=search_params,
        )

        places = response.get("results", [])
        restaurants = []

        for place in places[:max_results]:
            restaurant = _parse_place(place)
            restaurant["cuisine"] = cuisine or "Various"
            restaurants.append(restaurant)

        # Filter by price level if specified
        if price_level:
            price_map = {"budget": [1], "moderate": [2], "expensive": [3], "luxury": [4]}
            target_levels = price_map.get(price_level.lower(), [1, 2, 3, 4])
            restaurants = [r for r in restaurants if r.get("price_level", 2) in target_levels]

        result = {
            "location": location,
            "restaurants": restaurants[:max_results],
            "cuisine_filter": cuisine,
            "price_filter": price_level,
        }

        await cache.set("restaurants", cache_params, result, ttl=86400)

        return result

    except Exception as e:
        logger.error("Restaurant search failed", error=str(e))
        return {"error": f"Failed to search restaurants: {str(e)}", "restaurants": []}


def _map_categories_to_types(categories: list[str] | None) -> list[str]:
    """Map user-friendly categories to Google Places types."""
    if not categories:
        return ["tourist_attraction", "museum", "park"]

    mapping = {
        "temple": "hindu_temple",
        "shrine": "place_of_worship",
        "museum": "museum",
        "park": "park",
        "landmark": "tourist_attraction",
        "shopping": "shopping_mall",
        "nightlife": "night_club",
        "beach": "natural_feature",
        "market": "market",
    }

    return [mapping.get(c.lower(), "tourist_attraction") for c in categories]


def _parse_place(place: dict[str, Any]) -> dict[str, Any]:
    """Parse Google Places result into clean format."""
    price_symbols = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}

    return {
        "name": place.get("name", "Unknown"),
        "address": place.get("formatted_address", place.get("vicinity", "")),
        "rating": place.get("rating", 0),
        "reviews_count": place.get("user_ratings_total", 0),
        "price_level": place.get("price_level", 2),
        "price_symbol": price_symbols.get(place.get("price_level", 2), "$$"),
        "types": place.get("types", [])[:3],
        "is_open": place.get("opening_hours", {}).get("open_now"),
        "photo_reference": (
            place.get("photos", [{}])[0].get("photo_reference")
            if place.get("photos")
            else None
        ),
        "place_id": place.get("place_id", ""),
    }


def _get_mock_attractions(location: str, categories: list[str] | None) -> dict[str, Any]:
    """Return mock attractions data."""
    city = location.split(",")[0]
    return {
        "location": location,
        "attractions": [
            {
                "name": f"{city} National Museum",
                "address": f"1-1 Museum Street, {city}",
                "rating": 4.7,
                "reviews_count": 12543,
                "types": ["museum", "tourist_attraction"],
                "is_open": True,
                "description": f"Premier museum showcasing {city}'s rich cultural heritage",
            },
            {
                "name": f"{city} Central Park",
                "address": f"Central District, {city}",
                "rating": 4.6,
                "reviews_count": 8921,
                "types": ["park", "tourist_attraction"],
                "is_open": True,
                "description": "Beautiful urban park perfect for walks and picnics",
            },
            {
                "name": f"Historic {city} Temple",
                "address": f"Temple Road, Old Town, {city}",
                "rating": 4.8,
                "reviews_count": 15234,
                "types": ["place_of_worship", "tourist_attraction"],
                "is_open": True,
                "description": "Ancient temple with stunning architecture",
            },
            {
                "name": f"{city} Tower",
                "address": f"Tower Plaza, {city}",
                "rating": 4.5,
                "reviews_count": 23456,
                "types": ["landmark", "tourist_attraction"],
                "is_open": True,
                "description": "Iconic observation tower with panoramic city views",
            },
        ],
        "note": "Mock data - set GOOGLE_PLACES_API_KEY for real results",
    }


def _get_mock_restaurants(location: str, cuisine: str | None) -> dict[str, Any]:
    """Return mock restaurant data."""
    city = location.split(",")[0]
    cuisine_name = cuisine or "Local"
    return {
        "location": location,
        "restaurants": [
            {
                "name": f"{cuisine_name} House",
                "address": f"123 Food Street, {city}",
                "rating": 4.6,
                "reviews_count": 2341,
                "price_level": 2,
                "price_symbol": "$$",
                "cuisine": cuisine_name,
                "is_open": True,
            },
            {
                "name": f"The {city} Kitchen",
                "address": f"456 Dining Avenue, {city}",
                "rating": 4.4,
                "reviews_count": 1876,
                "price_level": 3,
                "price_symbol": "$$$",
                "cuisine": cuisine_name,
                "is_open": True,
            },
            {
                "name": f"Street Food {city}",
                "address": f"Night Market, {city}",
                "rating": 4.7,
                "reviews_count": 3421,
                "price_level": 1,
                "price_symbol": "$",
                "cuisine": "Street Food",
                "is_open": True,
            },
        ],
        "note": "Mock data - set GOOGLE_PLACES_API_KEY for real results",
    }

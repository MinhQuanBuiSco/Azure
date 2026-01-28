"""Flight search tool using SerpAPI Google Flights."""

from datetime import date
from typing import Any

import structlog

from travel_mcp.config import get_settings
from travel_mcp.services.http_client import get_http_client
from travel_mcp.services.cache import get_cache_service

logger = structlog.get_logger()

SERPAPI_BASE_URL = "https://serpapi.com/search"

# Major city to airport code mapping
CITY_TO_AIRPORT = {
    # United States
    "san francisco": "SFO",
    "los angeles": "LAX",
    "new york": "JFK",
    "new york city": "JFK",
    "nyc": "JFK",
    "chicago": "ORD",
    "miami": "MIA",
    "seattle": "SEA",
    "boston": "BOS",
    "las vegas": "LAS",
    "denver": "DEN",
    "atlanta": "ATL",
    "dallas": "DFW",
    "houston": "IAH",
    "phoenix": "PHX",
    "washington": "DCA",
    "washington dc": "DCA",
    "orlando": "MCO",
    "honolulu": "HNL",
    # Asia
    "tokyo": "NRT",
    "osaka": "KIX",
    "seoul": "ICN",
    "beijing": "PEK",
    "shanghai": "PVG",
    "hong kong": "HKG",
    "singapore": "SIN",
    "bangkok": "BKK",
    "hanoi": "HAN",
    "ho chi minh": "SGN",
    "ho chi minh city": "SGN",
    "saigon": "SGN",
    "taipei": "TPE",
    "manila": "MNL",
    "jakarta": "CGK",
    "kuala lumpur": "KUL",
    "mumbai": "BOM",
    "delhi": "DEL",
    "new delhi": "DEL",
    # Europe
    "london": "LHR",
    "paris": "CDG",
    "rome": "FCO",
    "amsterdam": "AMS",
    "frankfurt": "FRA",
    "munich": "MUC",
    "barcelona": "BCN",
    "madrid": "MAD",
    "lisbon": "LIS",
    "dublin": "DUB",
    "zurich": "ZRH",
    "vienna": "VIE",
    "prague": "PRG",
    "athens": "ATH",
    "istanbul": "IST",
    "moscow": "SVO",
    # Australia/Oceania
    "sydney": "SYD",
    "melbourne": "MEL",
    "auckland": "AKL",
    # Middle East
    "dubai": "DXB",
    "doha": "DOH",
    "abu dhabi": "AUH",
    # South America
    "sao paulo": "GRU",
    "rio de janeiro": "GIG",
    "buenos aires": "EZE",
    "lima": "LIM",
    "bogota": "BOG",
    # Canada
    "toronto": "YYZ",
    "vancouver": "YVR",
    "montreal": "YUL",
    # Africa
    "johannesburg": "JNB",
    "cairo": "CAI",
    "cape town": "CPT",
}


def _get_airport_code_sync(location: str) -> str | None:
    """Convert city name to airport code using static mapping."""
    # If already looks like an airport code (3 letters), return as-is
    clean = location.strip()
    if len(clean) == 3 and clean.isalpha():
        return clean.upper()

    # Remove country suffix (e.g., "Tokyo, Japan" -> "Tokyo")
    city = clean.split(",")[0].strip().lower()

    # Check mapping
    if city in CITY_TO_AIRPORT:
        return CITY_TO_AIRPORT[city]

    # Try partial match for common patterns
    for city_name, code in CITY_TO_AIRPORT.items():
        if city_name in city or city in city_name:
            return code

    return None


async def _get_airport_code(location: str) -> str:
    """Convert city name to airport code, using AI as fallback."""
    from travel_mcp.services.llm import get_airport_code as ai_get_airport_code

    # Try static mapping first
    code = _get_airport_code_sync(location)
    if code:
        return code

    # Try AI fallback
    logger.info("Using AI for airport lookup", location=location)
    ai_code = await ai_get_airport_code(location)
    if ai_code:
        return ai_code

    # Last resort: return cleaned location
    logger.warning("Could not resolve airport code", location=location)
    return location.split(",")[0].strip().upper()


async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    passengers: int = 1,
    travel_class: str = "economy",
    max_results: int = 5,
) -> dict[str, Any]:
    """
    Search for available flights between two airports.

    Args:
        origin: Departure airport code (e.g., 'SFO', 'LAX', 'JFK')
        destination: Arrival airport code (e.g., 'TYO', 'CDG', 'LHR')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date for round trips (YYYY-MM-DD)
        passengers: Number of passengers (default: 1)
        travel_class: Class of travel - economy, business, first (default: economy)
        max_results: Maximum number of flight options to return (default: 5)

    Returns:
        Dictionary containing flight options with prices, times, and airline info
    """
    settings = get_settings()

    if not settings.serpapi_api_key:
        return _get_mock_flights(origin, destination, departure_date, return_date)

    # Check cache first
    cache_params = {
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers,
        "travel_class": travel_class,
    }

    cache = await get_cache_service()
    cached = await cache.get("flights", cache_params)
    if cached:
        return cached

    # Convert city names to airport codes
    origin_code = await _get_airport_code(origin)
    destination_code = await _get_airport_code(destination)

    logger.info("Flight search", origin=origin, origin_code=origin_code,
                destination=destination, destination_code=destination_code)

    # Make API request
    http = get_http_client()

    params = {
        "engine": "google_flights",
        "departure_id": origin_code,
        "arrival_id": destination_code,
        "outbound_date": departure_date,
        "currency": "USD",
        "hl": "en",
        "adults": passengers,
        "travel_class": _map_travel_class(travel_class),
        "api_key": settings.serpapi_api_key,
    }

    if return_date:
        params["return_date"] = return_date
        params["type"] = "1"  # Round trip
    else:
        params["type"] = "2"  # One way

    try:
        data = await http.get(SERPAPI_BASE_URL, params=params)
        result = _parse_flight_results(data, max_results)

        # Cache the result
        await cache.set("flights", cache_params, result, ttl=1800)  # 30 min cache

        return result

    except Exception as e:
        logger.error("Flight search failed", error=str(e))
        return {
            "error": f"Failed to search flights: {str(e)}",
            "flights": [],
        }


def _map_travel_class(travel_class: str) -> int:
    """Map travel class string to SerpAPI value."""
    mapping = {
        "economy": 1,
        "premium_economy": 2,
        "business": 3,
        "first": 4,
    }
    return mapping.get(travel_class.lower(), 1)


def _parse_flight_results(data: dict[str, Any], max_results: int) -> dict[str, Any]:
    """Parse SerpAPI flight results into clean format."""
    flights = []

    best_flights = data.get("best_flights", [])
    other_flights = data.get("other_flights", [])

    all_flights = best_flights + other_flights

    for flight in all_flights[:max_results]:
        flight_legs = flight.get("flights", [])
        if not flight_legs:
            continue

        first_leg = flight_legs[0]
        last_leg = flight_legs[-1]

        flights.append({
            "airline": first_leg.get("airline", "Unknown"),
            "airline_logo": first_leg.get("airline_logo", ""),
            "flight_number": first_leg.get("flight_number", ""),
            "price": flight.get("price", 0),
            "currency": "USD",
            "departure_time": first_leg.get("departure_airport", {}).get("time", ""),
            "departure_airport": first_leg.get("departure_airport", {}).get("name", ""),
            "arrival_time": last_leg.get("arrival_airport", {}).get("time", ""),
            "arrival_airport": last_leg.get("arrival_airport", {}).get("name", ""),
            "duration": flight.get("total_duration", 0),
            "stops": len(flight_legs) - 1,
            "layovers": [
                {
                    "airport": leg.get("arrival_airport", {}).get("name", ""),
                    "duration": leg.get("layover_duration", 0),
                }
                for leg in flight_legs[:-1]
            ] if len(flight_legs) > 1 else [],
            "carbon_emissions": flight.get("carbon_emissions", {}).get("this_flight", 0),
        })

    return {
        "search_metadata": {
            "origin": data.get("search_parameters", {}).get("departure_id", ""),
            "destination": data.get("search_parameters", {}).get("arrival_id", ""),
            "date": data.get("search_parameters", {}).get("outbound_date", ""),
        },
        "flights": flights,
        "price_insights": data.get("price_insights", {}),
    }


def _get_mock_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
) -> dict[str, Any]:
    """Return mock flight data for testing without API key."""
    return {
        "search_metadata": {
            "origin": origin,
            "destination": destination,
            "date": departure_date,
            "note": "Mock data - set SERPAPI_API_KEY for real results",
        },
        "flights": [
            {
                "airline": "United Airlines",
                "flight_number": "UA 837",
                "price": 856,
                "currency": "USD",
                "departure_time": "10:30",
                "departure_airport": f"{origin} International",
                "arrival_time": "14:45+1",
                "arrival_airport": f"{destination} International",
                "duration": 780,
                "stops": 0,
                "layovers": [],
                "carbon_emissions": 450,
            },
            {
                "airline": "Delta Airlines",
                "flight_number": "DL 295",
                "price": 742,
                "currency": "USD",
                "departure_time": "14:20",
                "departure_airport": f"{origin} International",
                "arrival_time": "06:30+1",
                "arrival_airport": f"{destination} International",
                "duration": 840,
                "stops": 1,
                "layovers": [{"airport": "Los Angeles (LAX)", "duration": 90}],
                "carbon_emissions": 520,
            },
            {
                "airline": "American Airlines",
                "flight_number": "AA 153",
                "price": 923,
                "currency": "USD",
                "departure_time": "08:15",
                "departure_airport": f"{origin} International",
                "arrival_time": "12:30+1",
                "arrival_airport": f"{destination} International",
                "duration": 750,
                "stops": 0,
                "layovers": [],
                "carbon_emissions": 430,
            },
        ],
        "price_insights": {
            "lowest_price": 742,
            "typical_price_range": [700, 950],
            "price_level": "typical",
        },
    }

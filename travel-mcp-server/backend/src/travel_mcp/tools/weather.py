"""Weather forecast tool using OpenWeather API."""

from datetime import datetime, timedelta
from typing import Any

import structlog

from travel_mcp.config import get_settings
from travel_mcp.services.http_client import get_http_client
from travel_mcp.services.cache import get_cache_service

logger = structlog.get_logger()

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0"


async def get_weather(
    location: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Get weather forecast for a location.

    Args:
        location: City name (e.g., 'Tokyo', 'Paris, France', 'New York, US')
        start_date: Start date for forecast (YYYY-MM-DD), defaults to today
        end_date: End date for forecast (YYYY-MM-DD), defaults to 5 days from start

    Returns:
        Dictionary containing weather forecast with temperature, conditions, and tips
    """
    settings = get_settings()

    if not settings.openweather_api_key:
        return _get_mock_weather(location, start_date, end_date)

    # Check cache
    cache_params = {"location": location, "start": start_date, "end": end_date}
    cache = await get_cache_service()
    cached = await cache.get("weather", cache_params)
    if cached:
        return cached

    http = get_http_client()

    try:
        # First, get coordinates for the location
        geo_params = {
            "q": location,
            "limit": 1,
            "appid": settings.openweather_api_key,
        }
        geo_data = await http.get(f"{OPENWEATHER_GEO_URL}/direct", params=geo_params)

        if not geo_data:
            return {"error": f"Location not found: {location}", "forecast": []}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        location_name = f"{geo_data[0].get('name')}, {geo_data[0].get('country')}"

        # Get forecast
        forecast_params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "appid": settings.openweather_api_key,
        }
        forecast_data = await http.get(
            f"{OPENWEATHER_BASE_URL}/forecast", params=forecast_params
        )

        result = _parse_weather_results(forecast_data, location_name, start_date, end_date)

        await cache.set("weather", cache_params, result, ttl=3600)

        return result

    except Exception as e:
        logger.error("Weather fetch failed", error=str(e))
        return {
            "error": f"Failed to get weather: {str(e)}",
            "forecast": [],
        }


def _parse_weather_results(
    data: dict[str, Any],
    location: str,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    """Parse OpenWeather forecast into daily summaries."""
    forecasts = data.get("list", [])

    # Group by date
    daily_forecasts: dict[str, list[dict]] = {}
    for item in forecasts:
        dt = datetime.fromtimestamp(item["dt"])
        date_str = dt.strftime("%Y-%m-%d")

        if date_str not in daily_forecasts:
            daily_forecasts[date_str] = []
        daily_forecasts[date_str].append(item)

    # Create daily summaries
    daily_summary = []
    for date_str, items in sorted(daily_forecasts.items()):
        temps = [i["main"]["temp"] for i in items]
        feels_like = [i["main"]["feels_like"] for i in items]
        humidity = [i["main"]["humidity"] for i in items]

        # Get most common weather condition
        conditions = [i["weather"][0]["main"] for i in items]
        main_condition = max(set(conditions), key=conditions.count)

        descriptions = [i["weather"][0]["description"] for i in items]
        main_description = max(set(descriptions), key=descriptions.count)

        icons = [i["weather"][0]["icon"] for i in items]
        main_icon = max(set(icons), key=icons.count)

        daily_summary.append({
            "date": date_str,
            "day_of_week": datetime.strptime(date_str, "%Y-%m-%d").strftime("%A"),
            "temperature": {
                "min": round(min(temps), 1),
                "max": round(max(temps), 1),
                "avg": round(sum(temps) / len(temps), 1),
            },
            "feels_like": {
                "min": round(min(feels_like), 1),
                "max": round(max(feels_like), 1),
            },
            "humidity": round(sum(humidity) / len(humidity)),
            "condition": main_condition,
            "description": main_description,
            "icon": f"https://openweathermap.org/img/wn/{main_icon}@2x.png",
        })

    # Filter by date range if provided
    if start_date:
        daily_summary = [d for d in daily_summary if d["date"] >= start_date]
    if end_date:
        daily_summary = [d for d in daily_summary if d["date"] <= end_date]

    # Generate packing tips
    packing_tips = _generate_packing_tips(daily_summary)

    return {
        "location": location,
        "forecast": daily_summary[:7],  # Max 7 days
        "packing_tips": packing_tips,
        "units": "celsius",
    }


def _generate_packing_tips(forecast: list[dict]) -> list[str]:
    """Generate packing tips based on forecast."""
    tips = []

    if not forecast:
        return tips

    temps = [d["temperature"]["avg"] for d in forecast]
    avg_temp = sum(temps) / len(temps)
    conditions = [d["condition"] for d in forecast]

    # Temperature-based tips
    if avg_temp < 5:
        tips.append("Pack heavy winter clothing: warm coat, layers, gloves, and hat")
    elif avg_temp < 15:
        tips.append("Bring layers and a warm jacket for cool weather")
    elif avg_temp < 25:
        tips.append("Light layers recommended - comfortable for most activities")
    else:
        tips.append("Pack light, breathable clothing for warm weather")

    # Condition-based tips
    if "Rain" in conditions or "Drizzle" in conditions:
        tips.append("Bring an umbrella and waterproof jacket - rain expected")
    if "Snow" in conditions:
        tips.append("Waterproof boots and warm accessories recommended")
    if "Clear" in conditions and avg_temp > 20:
        tips.append("Don't forget sunscreen and sunglasses")

    return tips


def _get_mock_weather(
    location: str,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    """Return mock weather data for testing."""
    today = datetime.now()

    forecast = []
    for i in range(7):
        day = today + timedelta(days=i)
        forecast.append({
            "date": day.strftime("%Y-%m-%d"),
            "day_of_week": day.strftime("%A"),
            "temperature": {
                "min": 15 + i % 3,
                "max": 22 + i % 4,
                "avg": 18 + i % 3,
            },
            "feels_like": {"min": 14 + i % 3, "max": 21 + i % 4},
            "humidity": 65 + i % 10,
            "condition": ["Clear", "Clouds", "Rain", "Clear", "Clouds", "Clear", "Clear"][i],
            "description": ["clear sky", "scattered clouds", "light rain", "clear sky",
                          "few clouds", "clear sky", "clear sky"][i],
            "icon": "https://openweathermap.org/img/wn/01d@2x.png",
        })

    return {
        "location": location,
        "forecast": forecast,
        "packing_tips": [
            "Light layers recommended - comfortable for most activities",
            "Bring an umbrella just in case",
            "Don't forget sunscreen and sunglasses",
        ],
        "units": "celsius",
        "note": "Mock data - set OPENWEATHER_API_KEY for real results",
    }

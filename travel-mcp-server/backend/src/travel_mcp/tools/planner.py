"""Trip planning and budget calculation tools."""

from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()


async def plan_itinerary(
    destination: str,
    days: int,
    interests: list[str] | None = None,
    pace: str = "moderate",
) -> dict[str, Any]:
    """
    Generate a day-by-day travel itinerary.

    Args:
        destination: Destination city (e.g., 'Tokyo', 'Paris')
        days: Number of days for the trip
        interests: List of interests (e.g., ['culture', 'food', 'nature', 'shopping', 'nightlife'])
        pace: Travel pace - 'relaxed', 'moderate', 'intensive' (default: moderate)

    Returns:
        Dictionary containing day-by-day itinerary with activities and tips
    """
    interests = interests or ["culture", "food", "sightseeing"]
    city = destination.split(",")[0].strip()

    # Get destination-specific activities
    activities = _get_destination_activities(city, interests)

    # Generate itinerary
    itinerary = []
    activity_index = 0
    activities_per_day = {"relaxed": 2, "moderate": 3, "intensive": 4}.get(pace, 3)

    for day in range(1, days + 1):
        day_activities = []

        for slot in ["morning", "afternoon", "evening"]:
            if len(day_activities) >= activities_per_day:
                break

            if activity_index < len(activities):
                activity = activities[activity_index]
                activity["time_slot"] = slot
                day_activities.append(activity)
                activity_index += 1

        itinerary.append({
            "day": day,
            "theme": _get_day_theme(day, days, interests),
            "activities": day_activities,
            "meals": _get_meal_suggestions(city, day),
            "tips": _get_daily_tips(city, day, days),
        })

    return {
        "destination": destination,
        "duration": f"{days} days",
        "pace": pace,
        "interests": interests,
        "itinerary": itinerary,
        "general_tips": _get_general_tips(city),
    }


async def calculate_budget(
    destination: str,
    days: int,
    travelers: int = 1,
    travel_style: str = "moderate",
    include_flights: bool = True,
    flight_cost: float | None = None,
    hotel_cost_per_night: float | None = None,
) -> dict[str, Any]:
    """
    Calculate estimated trip budget.

    Args:
        destination: Destination city
        days: Number of days
        travelers: Number of travelers (default: 1)
        travel_style: Budget style - 'budget', 'moderate', 'luxury' (default: moderate)
        include_flights: Include flight estimate (default: True)
        flight_cost: Override flight cost per person (optional)
        hotel_cost_per_night: Override hotel cost per night (optional)

    Returns:
        Dictionary containing detailed budget breakdown
    """
    city = destination.split(",")[0].strip()

    # Get cost estimates for destination
    costs = _get_destination_costs(city, travel_style)

    # Calculate each category
    nights = max(days - 1, 1)

    flight_total = 0
    if include_flights:
        flight_per_person = flight_cost or costs["flight_avg"]
        flight_total = flight_per_person * travelers

    hotel_per_night = hotel_cost_per_night or costs["hotel_per_night"]
    hotel_total = hotel_per_night * nights

    food_per_day = costs["food_per_day"] * travelers
    food_total = food_per_day * days

    activities_per_day = costs["activities_per_day"] * travelers
    activities_total = activities_per_day * days

    transport_per_day = costs["local_transport_per_day"] * travelers
    transport_total = transport_per_day * days

    misc_per_day = costs["misc_per_day"] * travelers
    misc_total = misc_per_day * days

    subtotal = hotel_total + food_total + activities_total + transport_total + misc_total
    grand_total = subtotal + flight_total

    return {
        "destination": destination,
        "duration": f"{days} days, {nights} nights",
        "travelers": travelers,
        "travel_style": travel_style,
        "currency": "USD",
        "breakdown": {
            "flights": {
                "per_person": flight_cost or costs["flight_avg"] if include_flights else 0,
                "total": flight_total,
                "included": include_flights,
            },
            "accommodation": {
                "per_night": hotel_per_night,
                "nights": nights,
                "total": hotel_total,
            },
            "food": {
                "per_day": food_per_day,
                "days": days,
                "total": food_total,
            },
            "activities": {
                "per_day": activities_per_day,
                "days": days,
                "total": activities_total,
            },
            "local_transport": {
                "per_day": transport_per_day,
                "days": days,
                "total": transport_total,
            },
            "miscellaneous": {
                "per_day": misc_per_day,
                "days": days,
                "total": misc_total,
            },
        },
        "totals": {
            "excluding_flights": round(subtotal, 2),
            "grand_total": round(grand_total, 2),
            "per_person": round(grand_total / travelers, 2),
            "per_day": round(grand_total / days, 2),
        },
        "tips": _get_budget_tips(travel_style),
    }


def _get_destination_activities(city: str, interests: list[str]) -> list[dict]:
    """Get activities for a destination based on interests."""
    # Activity database by city
    city_activities = {
        "Tokyo": {
            "culture": [
                {"name": "Senso-ji Temple", "duration": "2 hours", "cost": "Free"},
                {"name": "Meiji Shrine", "duration": "1.5 hours", "cost": "Free"},
                {"name": "Tokyo National Museum", "duration": "3 hours", "cost": "$10"},
            ],
            "food": [
                {"name": "Tsukiji Outer Market", "duration": "2 hours", "cost": "$20-50"},
                {"name": "Ramen Street (Tokyo Station)", "duration": "1 hour", "cost": "$15"},
                {"name": "Izakaya experience in Yurakucho", "duration": "2 hours", "cost": "$30-50"},
            ],
            "sightseeing": [
                {"name": "Tokyo Skytree", "duration": "2 hours", "cost": "$20"},
                {"name": "Shibuya Crossing", "duration": "1 hour", "cost": "Free"},
                {"name": "Imperial Palace Gardens", "duration": "1.5 hours", "cost": "Free"},
            ],
            "shopping": [
                {"name": "Harajuku & Takeshita Street", "duration": "3 hours", "cost": "Varies"},
                {"name": "Akihabara Electronics District", "duration": "2 hours", "cost": "Varies"},
                {"name": "Ginza Shopping District", "duration": "3 hours", "cost": "Varies"},
            ],
        },
        "Paris": {
            "culture": [
                {"name": "Louvre Museum", "duration": "4 hours", "cost": "$20"},
                {"name": "Musée d'Orsay", "duration": "3 hours", "cost": "$16"},
                {"name": "Notre-Dame Cathedral (exterior)", "duration": "1 hour", "cost": "Free"},
            ],
            "food": [
                {"name": "Le Marais food tour", "duration": "3 hours", "cost": "$50-100"},
                {"name": "Café de Flore", "duration": "1 hour", "cost": "$20"},
                {"name": "Rue Mouffetard Market", "duration": "2 hours", "cost": "$20-40"},
            ],
            "sightseeing": [
                {"name": "Eiffel Tower", "duration": "2 hours", "cost": "$30"},
                {"name": "Arc de Triomphe", "duration": "1.5 hours", "cost": "$15"},
                {"name": "Seine River Cruise", "duration": "1 hour", "cost": "$18"},
            ],
        },
    }

    # Default activities for unknown cities
    default_activities = {
        "culture": [
            {"name": f"{city} National Museum", "duration": "3 hours", "cost": "$15"},
            {"name": f"Historic {city} Walking Tour", "duration": "2 hours", "cost": "$25"},
        ],
        "food": [
            {"name": f"{city} Food Market", "duration": "2 hours", "cost": "$20-40"},
            {"name": "Local cuisine cooking class", "duration": "3 hours", "cost": "$50"},
        ],
        "sightseeing": [
            {"name": f"{city} City Center", "duration": "2 hours", "cost": "Free"},
            {"name": f"{city} Viewpoint", "duration": "1 hour", "cost": "$10"},
        ],
    }

    activities_db = city_activities.get(city, default_activities)

    # Collect activities based on interests
    all_activities = []
    for interest in interests:
        interest_activities = activities_db.get(interest, [])
        all_activities.extend(interest_activities)

    # Add some default sightseeing if not enough activities
    if len(all_activities) < 5:
        all_activities.extend(activities_db.get("sightseeing", []))

    return all_activities


def _get_day_theme(day: int, total_days: int, interests: list[str]) -> str:
    """Generate a theme for each day."""
    if day == 1:
        return "Arrival & Orientation"
    if day == total_days:
        return "Last Day Highlights & Departure Prep"

    themes = interests * ((total_days // len(interests)) + 1)
    return f"{themes[day - 2].title()} Day"


def _get_meal_suggestions(city: str, day: int) -> dict:
    """Get meal suggestions for a day."""
    return {
        "breakfast": "Local café or hotel breakfast",
        "lunch": f"Try local {city} cuisine at a popular restaurant",
        "dinner": "Explore neighborhood dining options",
    }


def _get_daily_tips(city: str, day: int, total_days: int) -> list[str]:
    """Get tips for a specific day."""
    tips = []
    if day == 1:
        tips.append("Take it easy today to adjust to the time zone")
        tips.append("Exchange some local currency for small purchases")
    if day == total_days:
        tips.append("Leave time for last-minute shopping")
        tips.append("Confirm your airport transport")
    return tips


def _get_general_tips(city: str) -> list[str]:
    """Get general tips for a destination."""
    return [
        "Download offline maps before your trip",
        "Learn a few basic phrases in the local language",
        "Keep copies of important documents",
        "Check if you need any travel adapters",
        "Inform your bank about travel plans",
    ]


def _get_destination_costs(city: str, style: str) -> dict:
    """Get cost estimates for a destination by travel style."""
    # Cost database (daily per person in USD)
    costs_db = {
        "Tokyo": {
            "budget": {"hotel": 60, "food": 30, "activities": 20, "transport": 15, "misc": 10, "flight": 800},
            "moderate": {"hotel": 150, "food": 60, "activities": 40, "transport": 20, "misc": 20, "flight": 1200},
            "luxury": {"hotel": 400, "food": 150, "activities": 100, "transport": 50, "misc": 50, "flight": 3000},
        },
        "Paris": {
            "budget": {"hotel": 80, "food": 35, "activities": 25, "transport": 15, "misc": 15, "flight": 600},
            "moderate": {"hotel": 200, "food": 80, "activities": 50, "transport": 20, "misc": 25, "flight": 1000},
            "luxury": {"hotel": 500, "food": 200, "activities": 150, "transport": 60, "misc": 50, "flight": 4000},
        },
        "default": {
            "budget": {"hotel": 50, "food": 25, "activities": 15, "transport": 10, "misc": 10, "flight": 500},
            "moderate": {"hotel": 120, "food": 50, "activities": 35, "transport": 15, "misc": 20, "flight": 900},
            "luxury": {"hotel": 300, "food": 120, "activities": 80, "transport": 40, "misc": 40, "flight": 2500},
        },
    }

    city_costs = costs_db.get(city, costs_db["default"])
    style_costs = city_costs.get(style, city_costs["moderate"])

    return {
        "hotel_per_night": style_costs["hotel"],
        "food_per_day": style_costs["food"],
        "activities_per_day": style_costs["activities"],
        "local_transport_per_day": style_costs["transport"],
        "misc_per_day": style_costs["misc"],
        "flight_avg": style_costs["flight"],
    }


def _get_budget_tips(style: str) -> list[str]:
    """Get budget tips based on travel style."""
    tips = {
        "budget": [
            "Book accommodations in advance for better rates",
            "Use public transportation instead of taxis",
            "Eat at local markets and street food stalls",
            "Look for free walking tours and museum free days",
            "Consider hostels or Airbnb for cheaper stays",
        ],
        "moderate": [
            "Book flights 6-8 weeks in advance for best prices",
            "Mix splurge meals with casual dining",
            "Get city passes for attractions if visiting many",
            "Use ride-sharing apps for group transport",
        ],
        "luxury": [
            "Consider travel insurance for expensive bookings",
            "Book premium experiences in advance",
            "Look into hotel loyalty programs for upgrades",
            "Hire private guides for personalized experiences",
        ],
    }

    return tips.get(style, tips["moderate"])

"""Destination resources for Travel MCP Server."""

from typing import Any

# Destination database
DESTINATIONS = {
    "Tokyo": {
        "country": "Japan",
        "region": "Asia",
        "timezone": "JST (UTC+9)",
        "language": "Japanese",
        "currency": "Japanese Yen (JPY)",
        "best_time_to_visit": "March-May (cherry blossoms) or October-November (autumn foliage)",
        "climate": "Humid subtropical with four distinct seasons",
        "description": "A vibrant metropolis blending ancient traditions with cutting-edge technology. From serene temples to neon-lit streets, Tokyo offers endless discoveries.",
        "highlights": [
            "Senso-ji Temple in Asakusa",
            "Shibuya Crossing",
            "Meiji Shrine",
            "Tsukiji Outer Market",
            "Tokyo Skytree",
            "Akihabara electronics district",
        ],
        "neighborhoods": {
            "Shinjuku": "Entertainment hub with nightlife and shopping",
            "Shibuya": "Youth culture, fashion, and the famous crossing",
            "Asakusa": "Traditional area with temples and old Tokyo charm",
            "Ginza": "Upscale shopping and dining",
            "Harajuku": "Street fashion and youth culture",
            "Roppongi": "Nightlife and art museums",
        },
        "local_customs": [
            "Remove shoes when entering homes and some restaurants",
            "Bow when greeting people",
            "Don't tip - it can be considered rude",
            "Be quiet on public transport",
            "Queue orderly and wait your turn",
        ],
        "food_must_try": ["Sushi", "Ramen", "Tempura", "Yakitori", "Wagyu beef", "Matcha desserts"],
        "average_daily_cost": {"budget": "$80", "moderate": "$200", "luxury": "$500+"},
    },
    "Paris": {
        "country": "France",
        "region": "Europe",
        "timezone": "CET (UTC+1)",
        "language": "French",
        "currency": "Euro (EUR)",
        "best_time_to_visit": "April-June or September-October",
        "climate": "Oceanic climate with mild winters and warm summers",
        "description": "The City of Light captivates with its iconic landmarks, world-class art, exquisite cuisine, and romantic ambiance.",
        "highlights": [
            "Eiffel Tower",
            "Louvre Museum",
            "Notre-Dame Cathedral",
            "Champs-Élysées",
            "Montmartre",
            "Seine River cruises",
        ],
        "neighborhoods": {
            "Le Marais": "Historic Jewish quarter with trendy boutiques",
            "Saint-Germain-des-Prés": "Literary cafés and art galleries",
            "Montmartre": "Artistic hilltop village with Sacré-Cœur",
            "Latin Quarter": "Student area with bookshops and bistros",
            "Champs-Élysées": "Grand avenue with luxury shopping",
        },
        "local_customs": [
            "Greet with 'Bonjour' when entering shops",
            "Dress smartly - Parisians are fashion-conscious",
            "Lunch is typically 12-2pm, dinner after 8pm",
            "Service charge is usually included (service compris)",
            "Learn basic French phrases - it's appreciated",
        ],
        "food_must_try": ["Croissants", "Coq au vin", "Crêpes", "French onion soup", "Macarons", "Wine and cheese"],
        "average_daily_cost": {"budget": "$100", "moderate": "$250", "luxury": "$600+"},
    },
    "Bangkok": {
        "country": "Thailand",
        "region": "Asia",
        "timezone": "ICT (UTC+7)",
        "language": "Thai",
        "currency": "Thai Baht (THB)",
        "best_time_to_visit": "November-February (cool and dry season)",
        "climate": "Tropical with hot, humid weather year-round",
        "description": "A sensory explosion of ornate temples, bustling markets, vibrant street food, and modern shopping malls.",
        "highlights": [
            "Grand Palace",
            "Wat Pho (Reclining Buddha)",
            "Chatuchak Weekend Market",
            "Khao San Road",
            "Floating markets",
            "Rooftop bars",
        ],
        "neighborhoods": {
            "Sukhumvit": "Modern area with expat scene and nightlife",
            "Silom": "Business district with night markets",
            "Rattanakosin": "Old city with Grand Palace and temples",
            "Khao San": "Backpacker hub with bars and budget stays",
            "Chinatown": "Street food heaven and gold shops",
        },
        "local_customs": [
            "Remove shoes before entering temples and homes",
            "Dress modestly at temples (cover shoulders and knees)",
            "Never touch someone's head",
            "Don't point feet at Buddha images",
            "Respect the royal family",
        ],
        "food_must_try": ["Pad Thai", "Tom Yum Goong", "Green curry", "Mango sticky rice", "Som Tam (papaya salad)"],
        "average_daily_cost": {"budget": "$40", "moderate": "$100", "luxury": "$300+"},
    },
}


def get_destination_overview(city: str) -> dict[str, Any]:
    """Get comprehensive overview of a destination."""
    city_title = city.title()

    if city_title in DESTINATIONS:
        dest = DESTINATIONS[city_title]
        return {
            "city": city_title,
            "country": dest["country"],
            "region": dest["region"],
            "timezone": dest["timezone"],
            "language": dest["language"],
            "currency": dest["currency"],
            "description": dest["description"],
            "best_time_to_visit": dest["best_time_to_visit"],
            "climate": dest["climate"],
            "highlights": dest["highlights"],
            "neighborhoods": dest["neighborhoods"],
            "average_daily_cost": dest["average_daily_cost"],
        }

    return {
        "city": city_title,
        "message": f"Detailed information for {city_title} not in database. Basic info provided.",
        "tip": "Use the search tools to find specific information about this destination.",
    }


def get_destination_tips(city: str) -> dict[str, Any]:
    """Get travel tips and local customs for a destination."""
    city_title = city.title()

    if city_title in DESTINATIONS:
        dest = DESTINATIONS[city_title]
        return {
            "city": city_title,
            "local_customs": dest["local_customs"],
            "food_must_try": dest["food_must_try"],
            "general_tips": [
                "Always carry some local currency for small purchases",
                "Download offline maps and translation apps",
                "Keep copies of important documents",
                "Check visa requirements before booking",
                "Get travel insurance",
            ],
        }

    return {
        "city": city_title,
        "general_tips": [
            "Research local customs before visiting",
            "Learn basic phrases in the local language",
            "Respect local dress codes, especially at religious sites",
            "Be aware of common tourist scams",
            "Keep emergency contacts handy",
        ],
    }


def get_popular_destinations() -> dict[str, Any]:
    """Get list of popular destinations with brief info."""
    destinations = []

    for city, info in DESTINATIONS.items():
        destinations.append({
            "city": city,
            "country": info["country"],
            "region": info["region"],
            "best_time": info["best_time_to_visit"],
            "highlight": info["highlights"][0],
        })

    return {
        "destinations": destinations,
        "regions": ["Asia", "Europe", "Americas", "Africa", "Oceania"],
    }

"""Visa requirements tool with static data."""

from typing import Any

import structlog

logger = structlog.get_logger()

# Visa requirements database (simplified)
# Format: {destination_country: {passport_country: requirement}}
# Requirements: "visa_free", "visa_on_arrival", "e_visa", "visa_required"
VISA_DATABASE: dict[str, dict[str, dict[str, Any]]] = {
    "Japan": {
        "US": {"type": "visa_free", "duration": "90 days", "notes": "Tourist visa waiver"},
        "UK": {"type": "visa_free", "duration": "90 days", "notes": "Tourist visa waiver"},
        "EU": {"type": "visa_free", "duration": "90 days", "notes": "Schengen area citizens"},
        "Australia": {"type": "visa_free", "duration": "90 days", "notes": "Tourist visa waiver"},
        "Canada": {"type": "visa_free", "duration": "90 days", "notes": "Tourist visa waiver"},
        "default": {"type": "visa_required", "duration": "Varies", "notes": "Apply at embassy"},
    },
    "Thailand": {
        "US": {"type": "visa_free", "duration": "30 days", "notes": "Can extend 30 more days"},
        "UK": {"type": "visa_free", "duration": "30 days", "notes": "Can extend 30 more days"},
        "EU": {"type": "visa_free", "duration": "30 days", "notes": "Can extend 30 more days"},
        "Australia": {"type": "visa_free", "duration": "30 days", "notes": "Can extend"},
        "China": {"type": "visa_on_arrival", "duration": "15 days", "notes": "At airport"},
        "India": {"type": "visa_on_arrival", "duration": "15 days", "notes": "At airport"},
        "default": {"type": "visa_on_arrival", "duration": "15 days", "notes": "Check requirements"},
    },
    "France": {
        "US": {"type": "visa_free", "duration": "90 days", "notes": "Schengen area, 90/180 rule"},
        "UK": {"type": "visa_free", "duration": "90 days", "notes": "Post-Brexit, 90/180 rule"},
        "EU": {"type": "visa_free", "duration": "Unlimited", "notes": "EU freedom of movement"},
        "Australia": {"type": "visa_free", "duration": "90 days", "notes": "Schengen area"},
        "Canada": {"type": "visa_free", "duration": "90 days", "notes": "Schengen area"},
        "China": {"type": "visa_required", "duration": "Varies", "notes": "Apply for Schengen visa"},
        "default": {"type": "visa_required", "duration": "Varies", "notes": "Schengen visa required"},
    },
    "United States": {
        "UK": {"type": "e_visa", "duration": "90 days", "notes": "ESTA required ($21)"},
        "EU": {"type": "e_visa", "duration": "90 days", "notes": "ESTA required ($21)"},
        "Australia": {"type": "e_visa", "duration": "90 days", "notes": "ESTA required ($21)"},
        "Japan": {"type": "e_visa", "duration": "90 days", "notes": "ESTA required ($21)"},
        "Canada": {"type": "visa_free", "duration": "180 days", "notes": "B1/B2 not needed"},
        "China": {"type": "visa_required", "duration": "Varies", "notes": "B1/B2 visa required"},
        "India": {"type": "visa_required", "duration": "Varies", "notes": "B1/B2 visa required"},
        "default": {"type": "visa_required", "duration": "Varies", "notes": "Check visa requirements"},
    },
    "Mexico": {
        "US": {"type": "visa_free", "duration": "180 days", "notes": "FMM form required"},
        "UK": {"type": "visa_free", "duration": "180 days", "notes": "FMM form required"},
        "EU": {"type": "visa_free", "duration": "180 days", "notes": "FMM form required"},
        "Canada": {"type": "visa_free", "duration": "180 days", "notes": "FMM form required"},
        "Australia": {"type": "visa_free", "duration": "180 days", "notes": "FMM form required"},
        "default": {"type": "visa_required", "duration": "Varies", "notes": "Check requirements"},
    },
}

# Country code mapping
COUNTRY_CODES = {
    "US": ["US", "USA", "United States", "America"],
    "UK": ["UK", "GB", "United Kingdom", "Britain", "England"],
    "EU": ["EU", "Germany", "France", "Italy", "Spain", "Netherlands", "Belgium"],
    "Australia": ["AU", "Australia"],
    "Canada": ["CA", "Canada"],
    "China": ["CN", "China"],
    "India": ["IN", "India"],
    "Japan": ["JP", "Japan"],
}


async def get_visa_info(
    passport_country: str,
    destination: str,
) -> dict[str, Any]:
    """
    Get visa requirements for traveling to a destination.

    Args:
        passport_country: Country of passport (e.g., 'US', 'UK', 'Germany')
        destination: Destination country (e.g., 'Japan', 'France', 'Thailand')

    Returns:
        Dictionary containing visa type, duration, and application info
    """
    # Normalize inputs
    passport_region = _normalize_country(passport_country)
    dest_country = _find_destination(destination)

    if not dest_country:
        return {
            "passport_country": passport_country,
            "destination": destination,
            "visa_type": "unknown",
            "message": f"Visa information for {destination} not in database. Please check official sources.",
            "recommendation": "Visit the destination country's embassy website for accurate information.",
        }

    # Get visa info
    country_data = VISA_DATABASE.get(dest_country, {})
    visa_info = country_data.get(passport_region, country_data.get("default", {}))

    visa_type = visa_info.get("type", "unknown")
    type_descriptions = {
        "visa_free": "No visa required",
        "visa_on_arrival": "Visa on arrival available",
        "e_visa": "Electronic visa/authorization required",
        "visa_required": "Visa must be obtained before travel",
    }

    return {
        "passport_country": passport_country,
        "destination": destination,
        "visa_type": visa_type,
        "visa_type_description": type_descriptions.get(visa_type, "Check requirements"),
        "allowed_stay": visa_info.get("duration", "Varies"),
        "notes": visa_info.get("notes", ""),
        "recommendations": _get_recommendations(visa_type),
        "disclaimer": "This is general information. Always verify with official embassy sources before travel.",
    }


def _normalize_country(country: str) -> str:
    """Normalize country name to region code."""
    country_upper = country.upper()
    country_title = country.title()

    for region, variants in COUNTRY_CODES.items():
        if country_upper in [v.upper() for v in variants] or country_title in variants:
            return region

    return country_title


def _find_destination(destination: str) -> str | None:
    """Find destination in database."""
    dest_lower = destination.lower()

    for country in VISA_DATABASE:
        if country.lower() == dest_lower or dest_lower in country.lower():
            return country

    return None


def _get_recommendations(visa_type: str) -> list[str]:
    """Get recommendations based on visa type."""
    recommendations = {
        "visa_free": [
            "Ensure passport is valid for at least 6 months beyond travel dates",
            "Have proof of onward travel and accommodation",
            "Carry sufficient funds for your stay",
        ],
        "visa_on_arrival": [
            "Bring passport photos (usually 2)",
            "Have exact fee amount in USD or local currency",
            "Prepare hotel booking confirmation",
            "Allow extra time at immigration",
        ],
        "e_visa": [
            "Apply at least 72 hours before travel",
            "Print confirmation or save to phone",
            "Ensure all information matches passport exactly",
        ],
        "visa_required": [
            "Apply well in advance (4-8 weeks recommended)",
            "Gather required documents: invitation letter, itinerary, bank statements",
            "Book a visa appointment at the embassy",
            "Consider using a visa service for assistance",
        ],
    }

    return recommendations.get(visa_type, ["Check official embassy website for requirements"])

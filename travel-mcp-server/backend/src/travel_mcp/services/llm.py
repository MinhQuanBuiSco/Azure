"""Azure OpenAI integration for AI-powered responses."""

import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class AzureOpenAIClient:
    """Client for Azure OpenAI models."""

    def __init__(self) -> None:
        self.endpoint = os.environ.get("AZURE_AI_ENDPOINT", "")
        self.api_key = os.environ.get("AZURE_AI_KEY", "")
        self.model = os.environ.get("AZURE_AI_MODEL", "gpt-4o-mini")
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.endpoint and self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate a response using Azure OpenAI.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        if not self.is_configured:
            logger.warning("Azure OpenAI not configured, returning fallback")
            return self._fallback_response(prompt)

        client = await self._get_client()

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Azure OpenAI endpoint
        url = f"{self.endpoint}/openai/deployments/{self.model}/chat/completions?api-version=2024-08-01-preview"

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error("Azure OpenAI API error", status=e.response.status_code, detail=e.response.text)
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error("Azure OpenAI error", error=str(e))
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when AI is not available."""
        return (
            "I'm unable to generate an AI-powered response at the moment. "
            "Please check the travel data displayed above for your trip planning needs."
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
_ai_client: AzureOpenAIClient | None = None


def get_ai_client() -> AzureOpenAIClient:
    """Get or create AI client instance."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AzureOpenAIClient()
    return _ai_client


async def generate_trip_plan(
    destination: str,
    days: int,
    travel_data: dict[str, Any],
    preferences: dict[str, Any] | None = None,
) -> str:
    """
    Generate an AI-powered trip plan using Azure OpenAI.

    Args:
        destination: Travel destination
        days: Number of days
        travel_data: Dictionary with flights, hotels, weather, attractions
        preferences: User preferences (interests, budget, style)

    Returns:
        AI-generated trip plan as formatted text
    """
    client = get_ai_client()

    preferences = preferences or {}

    system_prompt = """You are an expert travel planner. Create detailed, practical, and
    personalized travel itineraries. Consider weather conditions when suggesting activities.
    Format your response with clear day-by-day plans, including specific times and locations.
    Be friendly and enthusiastic while remaining practical."""

    prompt = f"""Create a {days}-day travel itinerary for {destination}.

## Available Travel Data:

### Flights
{_format_data(travel_data.get('flights', {}))}

### Hotels
{_format_data(travel_data.get('hotels', {}))}

### Weather Forecast
{_format_data(travel_data.get('weather', {}))}

### Top Attractions
{_format_data(travel_data.get('attractions', {}))}

### Restaurants
{_format_data(travel_data.get('restaurants', {}))}

## User Preferences:
- Interests: {preferences.get('interests', ['general sightseeing'])}
- Budget Style: {preferences.get('travel_style', 'moderate')}
- Pace: {preferences.get('pace', 'moderate')}

## Instructions:
1. Recommend the best flight option based on value
2. Suggest a hotel that matches their style
3. Create a day-by-day itinerary considering the weather
4. Include restaurant recommendations for each day
5. Add practical tips and estimated daily costs
6. Format with emojis for visual appeal

Generate a comprehensive, personalized travel plan:"""

    return await client.generate_response(prompt, system_prompt)


def _format_data(data: Any) -> str:
    """Format data for prompt inclusion."""
    if not data:
        return "Not available"
    if isinstance(data, dict):
        if "error" in data:
            return f"Error: {data['error']}"
        return str(data)[:1500]  # Limit size
    if isinstance(data, list):
        return str(data[:5])[:1500]  # Limit items and size
    return str(data)[:1500]


async def get_airport_code(location: str) -> str | None:
    """
    Use AI to convert a location name to an IATA airport code.

    Args:
        location: City name, airport name, or location description

    Returns:
        IATA airport code (3 letters) or None if not found
    """
    client = get_ai_client()

    if not client.is_configured:
        logger.warning("Azure OpenAI not configured for airport lookup")
        return None

    system_prompt = """You are an airport code lookup assistant. Given a location (city, airport, or region),
    return ONLY the 3-letter IATA airport code for the main international airport serving that location.
    Return ONLY the code, nothing else. If you cannot determine the airport code, return "UNKNOWN"."""

    prompt = f"What is the IATA airport code for: {location}"

    try:
        response = await client.generate_response(prompt, system_prompt, max_tokens=10)
        code = response.strip().upper()

        # Validate it's a proper airport code (3 letters)
        if len(code) == 3 and code.isalpha() and code != "UNK":
            logger.info("AI airport lookup", location=location, code=code)
            return code

        logger.warning("AI returned invalid airport code", location=location, response=response)
        return None

    except Exception as e:
        logger.error("AI airport lookup failed", location=location, error=str(e))
        return None

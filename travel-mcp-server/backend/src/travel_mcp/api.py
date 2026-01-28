"""REST API endpoints for Travel Planner."""

import json
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
from openai import AzureOpenAI

from travel_mcp.tools.flights import search_flights
from travel_mcp.tools.hotels import search_hotels
from travel_mcp.tools.weather import get_weather
from travel_mcp.tools.places import search_attractions, search_restaurants
from travel_mcp.tools.currency import get_exchange_rate
from travel_mcp.tools.planner import plan_itinerary, calculate_budget
from travel_mcp.config import get_settings

logger = structlog.get_logger()

app = FastAPI(
    title="Travel Planner API",
    description="REST API for AI-powered travel planning",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class HotelSearchRequest(BaseModel):
    location: str
    check_in_date: str
    check_out_date: str
    guests: int = 2
    rooms: int = 1
    min_price: int | None = None
    max_price: int | None = None


class AttractionSearchRequest(BaseModel):
    location: str
    categories: list[str] | None = None
    max_results: int = 10


class WeatherRequest(BaseModel):
    location: str
    start_date: str | None = None
    end_date: str | None = None


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: str | None = None
    passengers: int = 1
    travel_class: str = "economy"


class BudgetRequest(BaseModel):
    destination: str
    days: int
    travelers: int = 1
    travel_style: str = "moderate"
    include_flights: bool = True


class TripPlanRequest(BaseModel):
    destination: str
    departure_city: str
    start_date: str
    end_date: str
    travelers: int = 2
    travel_style: str = "moderate"
    interests: list[str] = []


class AIAgentRequest(BaseModel):
    query: str
    conversation_history: list[dict] = []  # List of {"role": "user"|"assistant", "content": str}
    collected_params: dict = {}  # Parameters collected so far


class ExtractedTravelParams(BaseModel):
    destination: str | None = None
    departure_city: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    travelers: int | None = None
    travel_style: str | None = None
    interests: list[str] = []
    confidence: float = 0.0
    raw_interpretation: str = ""


class ConversationResponse(BaseModel):
    message: str  # AI's response message
    collected_params: dict  # All params collected so far
    is_complete: bool  # Whether we have enough info to search
    missing_fields: list[str]  # What's still needed


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "travel-planner-api"}


# Hotels endpoint
@app.post("/api/hotels")
async def api_search_hotels(request: HotelSearchRequest):
    try:
        logger.info("API: Searching hotels", location=request.location)
        result = await search_hotels(
            location=request.location,
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date,
            guests=request.guests,
            rooms=request.rooms,
            min_price=request.min_price,
            max_price=request.max_price,
        )
        return result
    except Exception as e:
        logger.error("API: Hotel search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Attractions endpoint
@app.post("/api/attractions")
async def api_search_attractions(request: AttractionSearchRequest):
    try:
        logger.info("API: Searching attractions", location=request.location)
        result = await search_attractions(
            location=request.location,
            categories=request.categories,
            max_results=request.max_results,
        )
        return result
    except Exception as e:
        logger.error("API: Attraction search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Weather endpoint
@app.post("/api/weather")
async def api_get_weather(request: WeatherRequest):
    try:
        logger.info("API: Getting weather", location=request.location)
        result = await get_weather(
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return result
    except Exception as e:
        logger.error("API: Weather fetch failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Flights endpoint
@app.post("/api/flights")
async def api_search_flights(request: FlightSearchRequest):
    try:
        logger.info("API: Searching flights", origin=request.origin, destination=request.destination)
        result = await search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            passengers=request.passengers,
            travel_class=request.travel_class,
        )
        return result
    except Exception as e:
        logger.error("API: Flight search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Budget endpoint
@app.post("/api/budget")
async def api_calculate_budget(request: BudgetRequest):
    try:
        logger.info("API: Calculating budget", destination=request.destination)
        result = await calculate_budget(
            destination=request.destination,
            days=request.days,
            travelers=request.travelers,
            travel_style=request.travel_style,
            include_flights=request.include_flights,
        )
        return result
    except Exception as e:
        logger.error("API: Budget calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to run task with timeout
async def run_with_timeout(coro, timeout_seconds: float, default_value):
    """Run a coroutine with a timeout, returning default value on timeout/error."""
    import asyncio
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Task timed out after {timeout_seconds}s")
        return default_value
    except Exception as e:
        logger.warning(f"Task failed: {e}")
        return default_value


# Complete trip plan endpoint - fetches all data for a trip
@app.post("/api/trip-plan")
async def api_get_trip_plan(request: TripPlanRequest):
    """Get complete trip plan with hotels, attractions, weather, and budget."""
    import asyncio
    from datetime import datetime

    logger.info("API: Creating trip plan", destination=request.destination)

    # Calculate number of days
    start = datetime.strptime(request.start_date, "%Y-%m-%d")
    end = datetime.strptime(request.end_date, "%Y-%m-%d")
    days = (end - start).days or 1

    # Default empty responses for timeouts
    empty_flights = {"flights": [], "error": "Request timed out"}
    empty_hotels = {"hotels": [], "total_results": 0, "error": "Request timed out"}
    empty_attractions = {"attractions": [], "total_results": 0, "error": "Request timed out"}
    empty_weather = {"forecast": [], "error": "Request timed out"}
    empty_budget = {"budget": None, "error": "Request timed out"}

    # Fetch all data in parallel with 25 second timeout per task
    timeout = 25.0

    flights_task = run_with_timeout(
        search_flights(
            origin=request.departure_city,
            destination=request.destination,
            departure_date=request.start_date,
            return_date=request.end_date,
            passengers=request.travelers,
        ),
        timeout,
        empty_flights,
    )

    hotels_task = run_with_timeout(
        search_hotels(
            location=request.destination,
            check_in_date=request.start_date,
            check_out_date=request.end_date,
            guests=request.travelers,
        ),
        timeout,
        empty_hotels,
    )

    attractions_task = run_with_timeout(
        search_attractions(
            location=request.destination,
            max_results=6,
        ),
        timeout,
        empty_attractions,
    )

    weather_task = run_with_timeout(
        get_weather(
            location=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
        ),
        timeout,
        empty_weather,
    )

    budget_task = run_with_timeout(
        calculate_budget(
            destination=request.destination,
            days=days,
            travelers=request.travelers,
            travel_style=request.travel_style,
        ),
        timeout,
        empty_budget,
    )

    # Execute all tasks concurrently
    flights, hotels, attractions, weather, budget = await asyncio.gather(
        flights_task,
        hotels_task,
        attractions_task,
        weather_task,
        budget_task,
    )

    logger.info("API: Trip plan completed", destination=request.destination)

    return {
        "destination": request.destination,
        "departure_city": request.departure_city,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "travelers": request.travelers,
        "travel_style": request.travel_style,
        "flights": flights,
        "hotels": hotels,
        "attractions": attractions,
        "weather": weather,
        "budget": budget,
    }


async def conversational_ai_agent(
    user_message: str,
    conversation_history: list[dict],
    collected_params: dict
) -> dict:
    """
    Conversational AI agent that asks follow-up questions to gather trip information.
    Returns a response with the AI message, updated params, and completion status.
    """
    settings = get_settings()

    if not settings.azure_ai_endpoint or not settings.azure_ai_key:
        logger.warning("Azure OpenAI not configured")
        return {
            "message": "I'm sorry, the AI service is not configured. Please try again later.",
            "collected_params": collected_params,
            "is_complete": False,
            "missing_fields": ["destination", "departure_city", "start_date", "end_date", "travelers"]
        }

    client = AzureOpenAI(
        azure_endpoint=settings.azure_ai_endpoint,
        api_key=settings.azure_ai_key,
        api_version="2024-02-15-preview"
    )

    today = datetime.now()

    system_prompt = f"""You are a friendly travel planning assistant helping users plan their perfect trip. Your job is to have a natural conversation to gather all the information needed to plan their trip.

Today's date is {today.strftime("%Y-%m-%d")} ({today.strftime("%A")}).

## Required Information to Collect:
1. **destination** - Where they want to go (city/country)
2. **departure_city** - Where they're traveling from
3. **start_date** - When they want to leave (YYYY-MM-DD format)
4. **end_date** - When they want to return (YYYY-MM-DD format)
5. **travelers** - Number of people traveling

## Optional Information:
- **travel_style** - budget, moderate, or luxury (default: moderate)
- **interests** - Culture, Food, Nature, Shopping, Nightlife, Relaxation

## Current Collected Information:
{json.dumps(collected_params, indent=2)}

## Your Task:
1. Extract any NEW information from the user's latest message
2. Update the collected parameters
3. If information is still missing, ask a friendly follow-up question for ONE missing piece at a time
4. When you have all required info (destination, departure_city, start_date, end_date, travelers), confirm the details and indicate completion

## Response Format (JSON only):
{{
    "message": "Your friendly response to the user",
    "updated_params": {{
        "destination": "city name or null",
        "departure_city": "city name or null",
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null",
        "travelers": number or null,
        "travel_style": "budget/moderate/luxury or null",
        "interests": ["array", "of", "interests"]
    }},
    "is_complete": true/false,
    "missing_fields": ["list", "of", "missing", "required", "fields"]
}}

## Guidelines:
- Be warm, enthusiastic, and helpful
- Ask ONE question at a time to avoid overwhelming the user
- For dates: convert natural language ("next week", "March 15th", "in 2 weeks") to YYYY-MM-DD
- For duration: if they say "5 days", calculate end_date from start_date
- Confirm details before marking complete
- Keep responses concise but friendly

Return ONLY valid JSON, no markdown or explanation."""

    # Build messages for the conversation
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add the current user message
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=settings.azure_ai_model,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )

        result_text = response.choices[0].message.content

        if not result_text:
            logger.error("AI returned empty response")
            raise ValueError("Empty response from AI")

        result_text = result_text.strip()
        logger.info("AI raw response", response=result_text[:200])

        # Remove markdown code blocks if present
        if "```json" in result_text:
            start = result_text.find("```json") + 7
            end = result_text.find("```", start)
            if end > start:
                result_text = result_text[start:end]
        elif "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.find("```", start)
            if end > start:
                result_text = result_text[start:end]

        result_text = result_text.strip()
        if result_text.startswith("json"):
            result_text = result_text[4:].strip()

        # Try to find JSON object in the response
        if not result_text.startswith("{"):
            # Try to extract JSON from the text
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result_text = result_text[json_start:json_end]

        result = json.loads(result_text)

        # Merge updated params with existing collected params
        updated_params = result.get("updated_params", {})
        merged_params = {**collected_params}
        for key, value in updated_params.items():
            if value is not None:
                merged_params[key] = value

        return {
            "message": result.get("message", "I'm here to help you plan your trip!"),
            "collected_params": merged_params,
            "is_complete": result.get("is_complete", False),
            "missing_fields": result.get("missing_fields", [])
        }

    except json.JSONDecodeError as e:
        logger.error("AI response JSON parse failed", error=str(e), response=result_text[:500] if result_text else "empty")

        # Try to extract information from the user's simple response
        updated_params = {**collected_params}
        user_input = user_message.strip()

        # Determine what we were asking for and try to extract it
        missing_before = []
        if not collected_params.get("destination"):
            missing_before.append("destination")
        if not collected_params.get("departure_city"):
            missing_before.append("departure_city")
        if not collected_params.get("start_date"):
            missing_before.append("start_date")
        if not collected_params.get("end_date"):
            missing_before.append("end_date")
        if not collected_params.get("travelers"):
            missing_before.append("travelers")

        # Smart extraction based on what's missing (in order of questions)
        if missing_before and len(user_input) > 0:
            first_missing = missing_before[0]

            if first_missing == "destination":
                # User is providing destination
                updated_params["destination"] = user_input
                logger.info("Fallback extracted destination", destination=user_input)

            elif first_missing == "departure_city":
                # User is providing departure city
                updated_params["departure_city"] = user_input
                logger.info("Fallback extracted departure_city", departure_city=user_input)

            elif first_missing in ["start_date", "end_date"]:
                # Try to parse dates from input
                user_lower = user_input.lower()
                today = datetime.now()

                # Month name mapping
                months = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }

                # Pattern 1: "February 10 to February 15" or "Feb 10 - Feb 15"
                range_pattern = r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|-)\s*(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?'
                range_match = re.search(range_pattern, user_input, re.IGNORECASE)
                if range_match:
                    start_month_str, start_day, end_month_str, end_day = range_match.groups()
                    start_month = months.get(start_month_str.lower())
                    end_month = months.get(end_month_str.lower())
                    if start_month and end_month:
                        year = today.year
                        if start_month < today.month:
                            year += 1
                        updated_params["start_date"] = f"{year}-{start_month:02d}-{int(start_day):02d}"
                        end_year = year if end_month >= start_month else year + 1
                        updated_params["end_date"] = f"{end_year}-{end_month:02d}-{int(end_day):02d}"
                        logger.info("Fallback extracted date range", start=updated_params["start_date"], end=updated_params["end_date"])

                # Pattern 2: "next Monday for 5 days" or "next week for 3 days"
                elif 'next' in user_lower:
                    days_match = re.search(r'(\d+)\s*days?', user_lower)
                    duration = int(days_match.group(1)) if days_match else 5

                    if 'monday' in user_lower:
                        days_ahead = (0 - today.weekday()) % 7 or 7
                    elif 'tuesday' in user_lower:
                        days_ahead = (1 - today.weekday()) % 7 or 7
                    elif 'wednesday' in user_lower:
                        days_ahead = (2 - today.weekday()) % 7 or 7
                    elif 'thursday' in user_lower:
                        days_ahead = (3 - today.weekday()) % 7 or 7
                    elif 'friday' in user_lower:
                        days_ahead = (4 - today.weekday()) % 7 or 7
                    elif 'saturday' in user_lower:
                        days_ahead = (5 - today.weekday()) % 7 or 7
                    elif 'sunday' in user_lower:
                        days_ahead = (6 - today.weekday()) % 7 or 7
                    elif 'week' in user_lower:
                        days_ahead = 7
                    elif 'month' in user_lower:
                        # Next month, first day
                        if today.month == 12:
                            start_date = datetime(today.year + 1, 1, 1)
                        else:
                            start_date = datetime(today.year, today.month + 1, 1)
                        updated_params["start_date"] = start_date.strftime("%Y-%m-%d")
                        updated_params["end_date"] = (start_date + timedelta(days=duration)).strftime("%Y-%m-%d")
                        logger.info("Fallback extracted next month", start=updated_params["start_date"])
                        days_ahead = None
                    else:
                        days_ahead = 7  # Default to next week

                    if days_ahead is not None:
                        start_date = today + timedelta(days=days_ahead)
                        updated_params["start_date"] = start_date.strftime("%Y-%m-%d")
                        updated_params["end_date"] = (start_date + timedelta(days=duration)).strftime("%Y-%m-%d")
                        logger.info("Fallback extracted relative date", start=updated_params["start_date"])

                # Pattern 3: Just duration "3 days" or "around 5 days" - use next week as start
                elif re.search(r'(\d+)\s*days?', user_lower):
                    days_match = re.search(r'(\d+)\s*days?', user_lower)
                    duration = int(days_match.group(1))
                    start_date = today + timedelta(days=7)  # Start next week
                    updated_params["start_date"] = start_date.strftime("%Y-%m-%d")
                    updated_params["end_date"] = (start_date + timedelta(days=duration)).strftime("%Y-%m-%d")
                    logger.info("Fallback extracted duration only", days=duration)

                # Check for travelers in the same message
                travelers_match = re.search(r'(\d+)\s*(?:people|persons?|travelers?|pax)', user_lower)
                if travelers_match:
                    updated_params["travelers"] = int(travelers_match.group(1))

            elif first_missing == "travelers":
                # Try to extract number
                num_match = re.search(r'(\d+)', user_input)
                if num_match:
                    updated_params["travelers"] = int(num_match.group(1))
                    logger.info("Fallback extracted travelers", travelers=updated_params["travelers"])

        # Recalculate missing fields
        missing = []
        if not updated_params.get("destination"):
            missing.append("destination")
        if not updated_params.get("departure_city"):
            missing.append("departure_city")
        if not updated_params.get("start_date"):
            missing.append("start_date")
        if not updated_params.get("end_date"):
            missing.append("end_date")
        if not updated_params.get("travelers"):
            missing.append("travelers")

        # Generate a helpful follow-up question
        if "destination" in missing:
            msg = "Where would you like to travel to?"
        elif "departure_city" in missing:
            msg = f"Great! Where will you be departing from?"
        elif "start_date" in missing or "end_date" in missing:
            msg = "When would you like to travel? Please provide dates like 'February 10 to February 15' or 'next Monday for 5 days'."
        elif "travelers" in missing:
            msg = "How many people will be traveling?"
        else:
            msg = f"Perfect! I have all the details for your trip to {updated_params.get('destination')}. Let me search for the best options!"

        return {
            "message": msg,
            "collected_params": updated_params,
            "is_complete": len(missing) == 0,
            "missing_fields": missing
        }

    except Exception as e:
        logger.error("AI conversation failed", error=str(e))
        return {
            "message": "I'm sorry, something went wrong. Could you please rephrase that?",
            "collected_params": collected_params,
            "is_complete": False,
            "missing_fields": ["destination", "departure_city", "start_date", "end_date", "travelers"]
        }


@app.post("/api/ai-agent")
async def process_ai_agent_query(request: AIAgentRequest):
    """
    Conversational AI agent for trip planning.

    Handles multi-turn conversation to gather trip information,
    then returns trip plan when all required info is collected.
    """
    import asyncio

    logger.info("API: Processing AI agent message", query=request.query[:100])

    # Get conversational response from AI
    ai_response = await conversational_ai_agent(
        user_message=request.query,
        conversation_history=request.conversation_history,
        collected_params=request.collected_params
    )

    # If conversation is not complete, return the AI response for more info
    if not ai_response["is_complete"]:
        return {
            "type": "conversation",
            "message": ai_response["message"],
            "collected_params": ai_response["collected_params"],
            "missing_fields": ai_response["missing_fields"],
            "is_complete": False,
            "trip_plan": None
        }

    # Conversation is complete - fetch the trip plan
    params = ai_response["collected_params"]

    # Validate we have all required fields
    destination = params.get("destination")
    departure_city = params.get("departure_city", "New York")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    travelers = params.get("travelers", 2)
    travel_style = params.get("travel_style", "moderate")

    if not destination or not start_date or not end_date:
        return {
            "type": "conversation",
            "message": "I still need a few more details. " + ai_response["message"],
            "collected_params": ai_response["collected_params"],
            "missing_fields": ai_response["missing_fields"],
            "is_complete": False,
            "trip_plan": None
        }

    # Calculate number of days
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end_dt - start_dt).days or 1

    logger.info("API: Fetching trip plan", destination=destination)

    # Default empty responses for timeouts
    empty_flights = {"flights": [], "error": "Request timed out"}
    empty_hotels = {"hotels": [], "total_results": 0, "error": "Request timed out"}
    empty_attractions = {"attractions": [], "total_results": 0, "error": "Request timed out"}
    empty_weather = {"forecast": [], "error": "Request timed out"}
    empty_budget = {"budget": None, "error": "Request timed out"}

    timeout = 25.0

    # Fetch all travel data in parallel
    flights_task = run_with_timeout(
        search_flights(
            origin=departure_city,
            destination=destination,
            departure_date=start_date,
            return_date=end_date,
            passengers=travelers,
        ),
        timeout,
        empty_flights,
    )

    hotels_task = run_with_timeout(
        search_hotels(
            location=destination,
            check_in_date=start_date,
            check_out_date=end_date,
            guests=travelers,
        ),
        timeout,
        empty_hotels,
    )

    attractions_task = run_with_timeout(
        search_attractions(
            location=destination,
            max_results=6,
        ),
        timeout,
        empty_attractions,
    )

    weather_task = run_with_timeout(
        get_weather(
            location=destination,
            start_date=start_date,
            end_date=end_date,
        ),
        timeout,
        empty_weather,
    )

    budget_task = run_with_timeout(
        calculate_budget(
            destination=destination,
            days=days,
            travelers=travelers,
            travel_style=travel_style,
        ),
        timeout,
        empty_budget,
    )

    flights, hotels, attractions, weather, budget = await asyncio.gather(
        flights_task,
        hotels_task,
        attractions_task,
        weather_task,
        budget_task,
    )

    logger.info("API: AI agent trip plan completed", destination=destination)

    return {
        "type": "complete",
        "message": ai_response["message"],
        "collected_params": ai_response["collected_params"],
        "missing_fields": [],
        "is_complete": True,
        "trip_plan": {
            "destination": destination,
            "departure_city": departure_city,
            "start_date": start_date,
            "end_date": end_date,
            "travelers": travelers,
            "travel_style": travel_style,
            "flights": flights,
            "hotels": hotels,
            "attractions": attractions,
            "weather": weather,
            "budget": budget,
        }
    }


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

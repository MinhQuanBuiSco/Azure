# Travel MCP Server

A Travel Planner MCP Server for AI-powered trip planning, built with FastMCP and Azure OpenAI.

## Features

- Flight search via SerpAPI
- Hotel search via SerpAPI
- Weather forecasts via OpenWeather
- Attractions and restaurants via Google Places
- Currency conversion via ExchangeRate API
- AI-powered trip planning with Azure OpenAI (GPT-4o-mini)

## Development

```bash
# Install dependencies
uv sync

# Run locally
uv run travel-mcp
```

## Environment Variables

```env
SERPAPI_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
GOOGLE_PLACES_API_KEY=your_key
EXCHANGERATE_API_KEY=your_key
AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_AI_KEY=your_key
AZURE_AI_MODEL=gpt-4o-mini
REDIS_HOST=localhost
REDIS_PORT=6379
```

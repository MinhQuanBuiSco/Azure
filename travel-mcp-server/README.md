# Travel Planner MCP Server

An AI-powered travel planning assistant built with the Model Context Protocol (MCP). This server enables AI assistants like Claude to search flights, hotels, attractions, and create complete trip itineraries.

## Overview

The Travel MCP Server implements the [Model Context Protocol](https://modelcontextprotocol.io/) - the "USB-C for AI" - providing a standardized way for AI models to access travel planning tools and data.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Assistant (Claude, GPT, etc.)                  │
│                           MCP Client                                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ MCP Protocol (JSON-RPC 2.0)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TRAVEL PLANNER MCP SERVER                         │
│                        (Python + FastMCP)                            │
├─────────────────────────────────────────────────────────────────────┤
│  TOOLS:                           │  RESOURCES:                      │
│  • search_flights                 │  • destination://{city}/overview │
│  • search_hotels                  │  • destination://{city}/tips     │
│  • get_weather                    │  • destinations://popular        │
│  • search_attractions             │                                  │
│  • search_restaurants             │  PROMPTS:                        │
│  • get_exchange_rate              │  • weekend_getaway               │
│  • get_visa_info                  │  • family_vacation               │
│  • plan_itinerary                 │  • budget_backpacker             │
│  • calculate_budget               │  • luxury_escape                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────┐
        ▼                       ▼                   ▼
   ┌─────────┐           ┌─────────┐         ┌─────────┐
   │ SerpAPI │           │OpenWeather│        │  Redis  │
   │(flights)│           │(weather) │        │ (cache) │
   └─────────┘           └─────────┘         └─────────┘
```

## Features

- **9 Travel Tools**: Flight search, hotel booking, weather forecasts, attractions, restaurants, currency exchange, visa info, itinerary planning, and budget calculation
- **3 Resource Types**: Destination overviews, travel tips, and popular destinations
- **5 Prompt Templates**: Weekend getaway, family vacation, budget backpacker, luxury escape, romantic trip
- **Redis Caching**: Fast responses with intelligent caching
- **Azure Deployment**: Full Terraform IaC for Azure Container Apps

## Tech Stack

| Layer | Technology |
|-------|------------|
| MCP Framework | FastMCP 2.0 |
| Backend | Python 3.11+, FastAPI |
| Frontend | React 19, TypeScript, Tailwind CSS v4 |
| APIs | SerpAPI, OpenWeather, Google Places, ExchangeRate |
| Cache | Redis |
| Infrastructure | Azure Container Apps, Terraform |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Azure CLI (for deployment)
- API Keys: SerpAPI, OpenWeather, Google Places, ExchangeRate

### 1. Clone and Setup

```bash
git clone https://github.com/MinhQuanBuiSco/Azure.git
cd Azure/travel-mcp-server
```

### 2. Environment Variables

Create a `.env` file:

```env
# Travel API Keys
SERPAPI_API_KEY=your-serpapi-key
OPENWEATHER_API_KEY=your-openweather-key
GOOGLE_PLACES_API_KEY=your-google-places-key
EXCHANGERATE_API_KEY=your-exchangerate-key

# Redis (local)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Local Development

**Option A: Docker Compose (Recommended)**

```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Option B: Manual Setup**

Backend:
```bash
cd backend
pip install uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
python -m travel_mcp.server
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

### 4. Connect to Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "travel-planner": {
      "command": "python",
      "args": ["-m", "travel_mcp.server"],
      "cwd": "/path/to/travel-mcp-server/backend"
    }
  }
}
```

## MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_flights` | Search for flights | origin, destination, dates, passengers |
| `search_hotels` | Find accommodations | location, dates, guests, price range |
| `get_weather` | Weather forecast | location, date range |
| `search_attractions` | Tourist attractions | location, categories |
| `search_restaurants` | Dining options | location, cuisine, price level |
| `get_exchange_rate` | Currency conversion | from/to currency, amount |
| `get_visa_info` | Visa requirements | passport country, destination |
| `plan_itinerary` | Generate trip plan | destination, days, interests |
| `calculate_budget` | Budget estimate | destination, days, style |

## Usage Examples

### In Claude Desktop

```
User: Plan a 5-day trip to Tokyo in April for 2 people, budget style

Claude: [Automatically uses MCP tools]
  → search_flights("SFO", "TYO", "2026-04-01", ...)
  → search_hotels("Tokyo, Japan", "2026-04-01", ...)
  → get_weather("Tokyo", "2026-04-01", "2026-04-05")
  → search_attractions("Tokyo, Japan", ["culture", "food"])
  → calculate_budget("Tokyo", 5, 2, "budget")

Claude: Here's your complete Tokyo trip plan...
```

## Azure Deployment

### Deploy

```bash
# Set API keys
export SERPAPI_API_KEY="your-key"
export OPENWEATHER_API_KEY="your-key"

# Deploy
./deploy.sh
```

### Cleanup

```bash
./cleanup.sh --azure-only
```

## Project Structure

```
travel-mcp-server/
├── backend/
│   ├── src/travel_mcp/
│   │   ├── tools/           # MCP tool implementations
│   │   ├── resources/       # MCP resources
│   │   ├── prompts/         # MCP prompt templates
│   │   ├── services/        # Cache, HTTP client
│   │   ├── config.py        # Settings
│   │   └── server.py        # Main MCP server
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── cloud_infra/
│   └── terraform/           # Azure IaC
├── docker-compose.yml
├── deploy.sh
└── cleanup.sh
```

## API Keys

| Service | Free Tier | Get Key |
|---------|-----------|---------|
| SerpAPI | 100 searches/month | [serpapi.com](https://serpapi.com) |
| OpenWeather | 1000 calls/day | [openweathermap.org](https://openweathermap.org/api) |
| Google Places | $200 credit/month | [Google Cloud Console](https://console.cloud.google.com) |
| ExchangeRate | 1500 requests/month | [exchangerate-api.com](https://exchangerate-api.com) |

## License

MIT License

## Author

**Dr. Quan** - [GitHub](https://github.com/MinhQuanBuiSco)

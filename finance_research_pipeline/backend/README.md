# Finance Research Pipeline - Backend

Multi-agent research system powered by LangGraph and FastAPI.

## Features

- **Multi-Agent System**: 7 specialized AI agents (Supervisor, Web Research, Financial Data, News Analysis, Analyst, Writer, Reviewer)
- **Real-time Updates**: WebSocket for agent progress, SSE for LLM streaming
- **Research Tools**: Tavily web search, yfinance stock data, NewsAPI news articles
- **PDF Reports**: Automated report generation with WeasyPrint
- **Caching**: Redis for performance optimization
- **Persistence**: Optional Cosmos DB for session storage

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run development server
uvicorn backend.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research/start` | Start research pipeline |
| GET | `/api/v1/research/{id}` | Get research status |
| GET | `/api/v1/research/{id}/report/pdf` | Download PDF report |
| WS | `/api/v1/ws/research/{id}` | Real-time agent progress |
| SSE | `/api/v1/sse/research/{id}/stream` | LLM token streaming |

## Environment Variables

See `.env.example` in the root directory for required configuration.

## License

MIT

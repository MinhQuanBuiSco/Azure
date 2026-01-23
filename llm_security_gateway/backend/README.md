# LLM Security Gateway - Backend

FastAPI-based backend providing security scanning and LLM proxy capabilities.

## Features

- OpenAI-compatible API endpoints
- Prompt injection detection
- Jailbreak detection
- PII detection and masking (Presidio)
- Secret/credential scanning
- Content filtering (Azure Content Safety)
- Rate limiting (Redis)
- Audit logging (Cosmos DB)

## Quick Start

```bash
# Install dependencies
pip install uv
uv sync

# Run development server
uv run uvicorn backend:app --reload
```

## API Endpoints

### Gateway Endpoints

```
POST /v1/chat/completions     # OpenAI-compatible chat
POST /v1/completions          # OpenAI-compatible completions
POST /v1/security/scan        # Standalone security scan
```

### Management Endpoints

```
GET  /api/audit               # List audit logs
GET  /api/audit/summary       # Audit summary
GET  /api/analytics/threats   # Threat analytics
GET  /api/analytics/usage     # Usage analytics
GET  /health                  # Health check
GET  /ready                   # Readiness check
```

## Configuration

Create a `.env` file with:

```bash
# Azure AI Foundry
AZURE_AI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_AI_API_KEY=your-key
AZURE_AI_DEPLOYMENT_NAME=gpt-4o

# Azure Content Safety (optional)
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key

# Redis (optional, defaults to local)
REDIS_URL=redis://localhost:6379

# Cosmos DB (optional)
COSMOS_CONNECTION_STRING=your-connection-string

# Security Settings
ENABLE_PROMPT_INJECTION_DETECTION=true
ENABLE_PII_DETECTION=true
ENABLE_SECRET_SCANNING=true
ENABLE_JAILBREAK_DETECTION=true
PII_ACTION=mask
```

## Testing

```bash
uv run pytest tests/ -v
```

## Docker

```bash
docker build -t llm-gateway-backend .
docker run -p 8000:8000 --env-file .env llm-gateway-backend
```

## Project Structure

```
src/backend/
├── __init__.py           # FastAPI app
├── api/
│   ├── routes/           # API endpoints
│   │   ├── chat.py       # Chat completions
│   │   ├── completions.py
│   │   ├── audit.py
│   │   └── health.py
│   ├── middleware/       # Request middleware
│   └── dependencies.py   # FastAPI dependencies
├── security/
│   ├── scanner.py        # Unified scanner
│   ├── prompt_injection.py
│   ├── jailbreak_detector.py
│   ├── pii_detector.py
│   ├── secret_scanner.py
│   └── content_filter.py
├── providers/
│   ├── azure_ai_foundry.py
│   ├── content_safety.py
│   └── router.py
├── storage/
│   ├── redis.py
│   └── cosmos.py
├── models/
│   ├── requests.py
│   ├── audit.py
│   └── security.py
└── config/
    ├── settings.py
    └── policies.py
```

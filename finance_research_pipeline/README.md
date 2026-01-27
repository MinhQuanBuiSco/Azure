# Finance Research Pipeline

A production-ready multi-agent AI system for automated finance research using LangGraph, FastAPI, React, and Azure.

## Overview

This project implements an intelligent finance research pipeline that orchestrates 7 specialized AI agents to conduct comprehensive company analysis. The system provides real-time progress updates via WebSocket, generates PDF reports, and persists research sessions to Azure Cosmos DB.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                    Real-time WebSocket Updates                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                   WebSocket + REST API                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Research Graph                      │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                  │
│  │ Supervisor│──▶│Web Research│──▶│Financial  │                  │
│  │   Agent   │   │   Agent   │   │Data Agent │                  │
│  └───────────┘   └───────────┘   └───────────┘                  │
│        │              │               │                          │
│        ▼              ▼               ▼                          │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                  │
│  │   News    │──▶│  Analyst  │──▶│  Writer   │                  │
│  │   Agent   │   │   Agent   │   │   Agent   │                  │
│  └───────────┘   └───────────┘   └───────────┘                  │
│                                       │                          │
│                                       ▼                          │
│                              ┌───────────┐                       │
│                              │ Reviewer  │                       │
│                              │   Agent   │                       │
│                              └───────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │  Redis   │   │ Cosmos DB│   │  Azure   │
         │  Cache   │   │          │   │  OpenAI  │
         └──────────┘   └──────────┘   └──────────┘
```

## Features

- **7 Specialized AI Agents**: Supervisor, Web Research, Financial Data, News Analysis, Analyst, Writer, Reviewer
- **Real-time Progress**: WebSocket streaming of agent activities
- **PDF Report Generation**: Professional research reports with WeasyPrint
- **Session Persistence**: Azure Cosmos DB for research history
- **Redis Caching**: Fast state management and caching
- **Azure Integration**: Full Azure deployment with Container Apps

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite, TailwindCSS, TanStack Query |
| Backend | FastAPI, Python 3.11+, WebSocket, SSE |
| AI/ML | LangGraph, LangChain, Azure OpenAI (GPT-4o) |
| Data | Cosmos DB, Redis |
| Tools | Tavily (web search), yfinance, NewsAPI |
| Infrastructure | Azure Container Apps, Terraform |

## Project Structure

```
finance_research_pipeline/
├── backend/
│   ├── src/backend/
│   │   ├── agents/          # AI agent implementations
│   │   │   ├── supervisor.py
│   │   │   ├── web_research.py
│   │   │   ├── financial_data.py
│   │   │   ├── news_analysis.py
│   │   │   ├── analyst.py
│   │   │   ├── writer.py
│   │   │   └── reviewer.py
│   │   ├── api/v1/          # REST & WebSocket endpoints
│   │   ├── graph/           # LangGraph research graph
│   │   ├── services/        # Business logic services
│   │   ├── tools/           # External tool integrations
│   │   └── main.py          # FastAPI application
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks (WebSocket, SSE)
│   │   └── types/           # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── cloud_infra/
│   └── terraform/           # Infrastructure as Code
│       ├── environments/dev/
│       └── modules/
├── deploy.sh                # Azure deployment script
├── cleanup.sh               # Resource cleanup script
├── docker-compose.yml       # Production compose
└── docker-compose.dev.yml   # Development compose
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Azure CLI (for cloud deployment)
- API Keys: Azure OpenAI, Tavily, NewsAPI

### 1. Clone and Setup

```bash
git clone https://github.com/MinhQuanBuiSco/Azure.git
cd Azure/finance_research_pipeline
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# External APIs
TAVILY_API_KEY=your-tavily-key
NEWSAPI_KEY=your-newsapi-key

# Redis (local)
REDIS_URL=redis://localhost:6379

# Cosmos DB (optional for local dev)
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
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
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn backend.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Azure Deployment

### Prerequisites

1. Azure CLI installed and logged in
2. Required API keys set as environment variables

### Deploy

```bash
# Set your API keys
export TAVILY_API_KEY="your-key"
export NEWSAPI_KEY="your-key"

# Run deployment
./deploy.sh
```

This will create:
- Resource Group
- Azure OpenAI with GPT-4o deployment
- Azure Container Registry
- Azure Cache for Redis
- Azure Cosmos DB
- Azure Container Apps (Backend + Frontend)

### Cleanup

```bash
./cleanup.sh --azure-only
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research/start` | Start new research |
| GET | `/api/v1/research/{id}` | Get research status |
| GET | `/api/v1/research/{id}/report` | Download PDF report |
| GET | `/api/v1/research/sessions` | List all sessions |
| WS | `/api/v1/ws/{research_id}` | WebSocket for real-time updates |

### Start Research Request

```json
{
  "company_name": "Microsoft",
  "research_type": "comprehensive",
  "ticker_symbol": "MSFT",
  "additional_context": "Focus on AI initiatives"
}
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | Yes |
| `TAVILY_API_KEY` | Tavily search API key | Yes |
| `NEWSAPI_KEY` | NewsAPI key | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `COSMOS_ENDPOINT` | Cosmos DB endpoint | No* |
| `COSMOS_KEY` | Cosmos DB key | No* |

*Required for session persistence

## Development

### Running Tests

```bash
cd backend
pytest -v --cov=backend
```

### Linting

```bash
cd backend
ruff check .
ruff format .
```

### Type Checking

```bash
cd backend
mypy src/backend
```

## License

MIT License

## Author

**Dr. Quan** - [GitHub](https://github.com/MinhQuanBuiSco)

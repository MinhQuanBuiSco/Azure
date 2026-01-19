# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise-grade Fraud Detection System built for Azure, demonstrating end-to-end ML system design with:
- Real-time fraud scoring (<100ms target latency)
- Pretrained ML models (no training required)
- AKS deployment with cost-optimized configuration
- React frontend with 2025 design trends

## Project Structure

```
fraud_detection/
├── backend/                     # FastAPI backend
│   ├── src/backend/
│   │   ├── api/v1/             # API endpoints
│   │   ├── core/               # Config, database, security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic (rule engine, scoring, etc.)
│   │   ├── utils/              # Utilities
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Test suite
│   ├── pyproject.toml          # Dependencies managed by uv
│   ├── .env.example            # Environment variables template
│   └── README.md               # Backend documentation
├── frontend/                   # React + Tailwind CSS (TBD)
├── cloud_infra/                # Terraform for AKS (TBD)
│   └── terraform/
└── kubernetes/                 # Helm charts (TBD)
```

## Development Commands

### Backend

The backend uses Python 3.12 with `uv` for dependency management.

**Setup:**
```bash
cd backend
uv sync                    # Install all dependencies
cp .env.example .env       # Create environment file
# Edit .env with your configuration
```

**Run the application:**
```bash
cd backend
uv run fraud-api                                      # Run using script entry point
# OR
uv run uvicorn backend.main:app --reload --port 8000  # Run with uvicorn directly
```

**Database migrations:**
```bash
cd backend
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run alembic upgrade head                              # Apply migrations
uv run alembic downgrade -1                              # Rollback last migration
```

**Development tools:**
```bash
cd backend
uv run pytest                    # Run tests
uv run black .                   # Format code
uv run ruff check .              # Lint code
uv run mypy backend              # Type checking
```

**Add dependencies:**
```bash
cd backend
uv add <package-name>            # Add production dependency
uv add --dev <package-name>      # Add development dependency
```

## Architecture Notes

### Backend
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL (via SQLAlchemy + asyncpg) for relational data, Azure Cosmos DB for transactions
- **Caching**: Redis for sub-ms latency fraud scoring
- **Package Manager**: uv (fast, modern Python package manager)
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **Build Backend**: Hatchling

### Fraud Detection Strategy
- **Rule Engine**: 70% of detection (velocity checks, geolocation, amount anomalies, blacklists)
- **Pretrained ML**: 30% of detection (Isolation Forest, Azure Anomaly Detector API)
- **No model training required** - focus on architecture and integration
- **Explanations**: Claude via Azure AI Foundry generates natural language fraud explanations

### Data Flow
1. **Historical Data**: Kaggle dataset → ETL script → Cosmos DB + PostgreSQL
2. **Live Data**: Synthetic generator → Azure Event Hubs → FastAPI → Fraud scoring → Alerts
3. **Caching**: Redis caches risk scores for recent transactions

### Deployment Target
- **Kubernetes**: Azure Kubernetes Service (AKS)
- **VM Size**: B2s instances (cost-optimized for portfolio)
- **Scaling**: 2-4 nodes with HPA for API pods
- **Frontend**: Azure Static Web Apps (free tier)
- **Monitoring**: Prometheus + Grafana in-cluster

## Key Files

- `backend/src/backend/main.py` - FastAPI application entry point
- `backend/src/backend/core/config.py` - Application settings (Pydantic)
- `backend/src/backend/core/database.py` - Database connection setup
- `backend/src/backend/models/` - SQLAlchemy database models
- `backend/src/backend/api/v1/` - API endpoint routers
- `backend/pyproject.toml` - Python dependencies and project metadata
- `backend/alembic/env.py` - Alembic migration configuration

## Environment Variables

See `backend/.env.example` for all configuration options. Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST` - Redis hostname
- `COSMOS_ENDPOINT` / `COSMOS_KEY` - Azure Cosmos DB credentials
- `AZURE_AI_ENDPOINT` / `AZURE_AI_KEY` - Azure AI Foundry credentials for Claude
- `DEBUG` - Enable debug mode (default: true)

## Git Workflow

Main branch: `main`
Recent commits show removal of chatbot/RAG features to focus on fraud detection core functionality.

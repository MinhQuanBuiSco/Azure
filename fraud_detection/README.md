# Enterprise Fraud Detection System

A production-ready fraud detection system built with FastAPI, React, and Azure services. Demonstrates end-to-end ML system design with real-time fraud scoring, pretrained models, and AKS deployment.

## 🎯 Features

- **Real-time Fraud Scoring** - Sub-100ms fraud detection with rule engine + ML models
- **WebSocket Live Updates** - Real-time transaction feed and fraud alerts
- **Pretrained Models** - Isolation Forest + Azure Anomaly Detector (no training required)
- **AI Explanations** - Claude Haiku generates natural language fraud analysis
- **Synthetic Data Generator** - Realistic transaction generator for testing and demos
- **Modern UI** - React + Tailwind CSS with 2025 design trends
- **Production Ready** - Docker, Kubernetes (AKS), CI/CD, monitoring
- **Cost Optimized** - Designed for Azure with B2s instances

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│  Databases  │
│  (React)    │     │  (FastAPI)   │     │ PostgreSQL  │
│  Port 3000  │     │  Port 8000   │     │   Redis     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Azure AI    │
                    │ - Anomaly    │
                    │ - Claude     │
                    └──────────────┘
```

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose
- Git

### First Time Setup

```bash
# Clone repository
git clone <repo-url>
cd fraud_detection

# Initialize project (builds images, starts services, runs migrations)
make init
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Daily Development

```bash
# Start all services
make up

# Start with hot reload (development mode)
make dev

# View logs
make logs

# Stop services
make down
```

### Common Commands

```bash
make help              # Show all available commands
make build             # Rebuild Docker images
make restart           # Restart all services
make test              # Run backend tests
make db-migrate        # Create database migration
make db-upgrade        # Apply migrations
make load-data         # Load Kaggle dataset
make backend-shell     # Open backend container shell
make clean             # Remove all containers and volumes
```

### Loading Kaggle Data

```bash
# 1. Download the dataset from Kaggle
# https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

# 2. Place creditcard.csv in backend/data/
cp ~/Downloads/creditcard.csv backend/data/

# 3. Load data into PostgreSQL
make load-data

# Or load a sample (10k transactions) for testing
make load-data-sample
```

The dataset contains:
- 284,807 transactions
- 492 fraudulent (0.172% fraud rate)
- Realistic transaction amounts and patterns

### Generating Synthetic Transactions

For testing and demos, generate realistic fake transactions:

```bash
# Generate 100 transactions with 10% fraud rate
make generate-txns

# Generate transactions quickly (testing)
make generate-txns-fast

# Generate continuous stream (for WebSocket testing)
make generate-txns-stream
```

**Custom generation:**
```bash
docker-compose exec backend uv run python scripts/generate_transactions.py \
  --count 200 \
  --interval 0.5 \
  --fraud-rate 0.15 \
  --users 100
```

Features:
- Realistic user behavior patterns (favorite merchants, home country)
- Multiple fraud scenarios (high amount, unusual location, velocity abuse, new device)
- Configurable fraud rate and transaction volume
- Sends transactions directly to API for real-time scoring

## 📁 Project Structure

```
fraud_detection/
├── backend/              # FastAPI backend
│   ├── src/backend/
│   │   ├── api/v1/      # API endpoints
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── core/        # Configuration
│   ├── alembic/         # Database migrations
│   ├── Dockerfile       # Production image
│   ├── Dockerfile.dev   # Development image
│   └── pyproject.toml   # Python dependencies (uv)
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Page components
│   │   └── lib/         # API client
│   ├── Dockerfile       # Production image (nginx)
│   ├── Dockerfile.dev   # Development image (Vite)
│   └── package.json     # Node dependencies
├── cloud_infra/         # Terraform (TBD)
│   └── terraform/       # AKS infrastructure
├── kubernetes/          # Helm charts (TBD)
│   └── fraud-detection/
├── docker-compose.yml   # Production compose
├── docker-compose.dev.yml  # Development override
├── Makefile             # Convenience commands
└── README.md            # This file
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI + Python 3.12
- **Package Manager**: uv (modern Python package manager)
- **Database**: PostgreSQL (async with SQLAlchemy + asyncpg)
- **Cache**: Redis
- **ML**: scikit-learn (Isolation Forest), Azure Anomaly Detector
- **AI**: Anthropic Claude (Haiku)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4-ready
- **Components**: shadcn/ui-inspired
- **State**: TanStack Query (React Query)
- **Charts**: Recharts
- **Router**: React Router v6

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Orchestration**: Azure Kubernetes Service (AKS)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana

## 📊 Data Sources

- **Historical Data**: Kaggle Credit Card Fraud Detection dataset (1.85M transactions)
- **Live Data**: Synthetic transaction generator for real-time demo

## 🧪 Development

### Backend Development

```bash
cd backend

# Install dependencies
uv sync

# Run locally (without Docker)
uv run fraud-api

# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
uv run alembic upgrade head

# Run tests
uv run pytest
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run locally (without Docker)
npm run dev

# Build for production
npm run build
```

## 🐳 Docker Details

### Production Build

```bash
# Build production images
docker-compose build

# Start production stack
docker-compose up -d
```

### Development Mode (Hot Reload)

```bash
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use Makefile
make dev
```

### Database Migrations

```bash
# Create new migration
make db-migrate msg="add_new_table"

# Apply migrations
make db-upgrade

# Rollback last migration
make db-downgrade
```

## 🌐 Environment Variables

### Backend (.env)
```env
DEBUG=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fraud_detection
REDIS_HOST=localhost
REDIS_PORT=6379

# Azure Anomaly Detector (optional - falls back to z-score if not configured)
ANOMALY_DETECTOR_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
ANOMALY_DETECTOR_KEY=your_azure_key_here

# Anthropic Claude (for AI-generated explanations)
ANTHROPIC_API_KEY=sk-ant-...
```

**Azure Anomaly Detector Setup** (optional):
1. Create an Azure Anomaly Detector resource in Azure Portal
2. Copy the endpoint URL and API key
3. Add to `.env` file (or leave empty to use fallback z-score detection)
4. The system automatically falls back if Azure is unavailable

**Claude Haiku Setup** (optional):
1. Get API key from https://console.anthropic.com/
2. Add `ANTHROPIC_API_KEY` to `.env`
3. Uses Claude 3 Haiku (cheapest model: ~$0.25/1M input tokens)
4. Falls back to template-based explanations if not configured
5. Endpoints:
   - `/api/v1/transactions/score` - AI-enhanced fraud explanations
   - `/api/v1/analytics/summary` - AI-generated activity summaries

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## 🚢 Deployment

### Azure Kubernetes Service (AKS)

See `cloud_infra/terraform/README.md` for deployment instructions.

**Cost-optimized configuration:**
- VM Size: Standard_B2s (2 vCPU, 4 GB RAM)
- Node count: 2-4 with autoscaling
- Estimated cost: ~$150/month

## 📈 Fraud Detection Strategy

**Multi-Model Ensemble Scoring:**
- **Rule Engine (60%)**: 6 configurable business rules
  - Velocity checks (transaction frequency)
  - High amount detection (>3x user average)
  - Impossible travel (geolocation)
  - Unusual hours (2-5am)
  - New device detection
  - Country blacklist
- **Isolation Forest (25%)**: Unsupervised ML anomaly detection (scikit-learn)
  - 9 features: amount, time patterns, velocity, geolocation
  - Works without training data
- **Azure Anomaly Detector (15%)**: Managed AI service for time-series anomalies
  - No training required
  - Optional (falls back to z-score if not configured)
- **AI-Generated Explanations**: Claude Haiku (Anthropic)
  - Natural language fraud explanations for analysts
  - Dashboard activity summaries
  - Cost-optimized with Haiku (cheapest Claude model)
  - Falls back to template-based explanations if not configured

## 🤝 Contributing

This is a portfolio project. Feel free to fork and adapt for your needs.

## 📝 License

MIT License - see LICENSE file for details

## 🎓 Learning Resources

- Backend: `backend/README.md`
- Frontend: `frontend/README.md`
- Infrastructure: `cloud_infra/README.md`
- Architecture: `CLAUDE.md`

## 💡 Quick Tips

```bash
# View all containers
make ps

# View resource usage
make stats

# Clean everything
make clean

# First time setup
make init

# Show all commands
make help
```

## 🔍 Monitoring

- API Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## 🔴 Real-Time Updates (WebSocket)

The system provides WebSocket endpoints for live updates:

**Endpoints:**
- `ws://localhost:8000/api/v1/ws/transactions` - Real-time transaction scoring results
- `ws://localhost:8000/api/v1/ws/alerts` - High-risk fraud alerts only
- `ws://localhost:8000/api/v1/ws/stats` - Dashboard statistics updates

**Message Types:**
- `connected` - Connection established
- `transaction` - New transaction scored
- `alert` - Fraud alert for high-risk transaction
- `heartbeat` - Keep-alive ping (every 30s)

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/transactions');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New transaction:', data);
};

// Send ping to keep connection alive
setInterval(() => ws.send('ping'), 30000);
```

**Testing:**
```bash
# Generate stream of transactions to see live updates
make generate-txns-stream
```

## 📞 Support

For issues or questions, see the documentation in each component's directory.

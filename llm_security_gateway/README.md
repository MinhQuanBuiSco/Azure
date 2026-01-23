# LLM Security Gateway

A security layer for LLM applications on Azure, providing prompt injection detection, PII masking, rate limiting, and audit logging.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Applications                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Security Gateway                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Auth &    │  │  Security   │  │   Audit     │             │
│  │ Rate Limit  │  │   Scanner   │  │   Logger    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                │                      │
│         │    ┌───────────┴───────────┐    │                     │
│         │    │  - Prompt Injection   │    │                     │
│         │    │  - Jailbreak Detection│    │                     │
│         │    │  - PII Detection      │    │                     │
│         │    │  - Secret Scanning    │    │                     │
│         │    │  - Content Filtering  │    │                     │
│         │    └───────────────────────┘    │                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Azure AI Foundry                              │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │     GPT-4o      │  │   GPT-4o-mini   │                       │
│  └─────────────────┘  └─────────────────┘                       │
│  ┌─────────────────────────────────────────┐                    │
│  │       Azure AI Content Safety           │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Prompt Injection Detection**: Identifies attempts to override system instructions
- **Jailbreak Detection**: Detects known jailbreak patterns (DAN, etc.)
- **PII Detection & Masking**: Scans for and masks personal information using Presidio
- **Secret Scanning**: Identifies API keys, tokens, and credentials
- **Content Filtering**: Enforces content policies with Azure Content Safety
- **Rate Limiting**: Prevents abuse with configurable limits via Redis
- **Audit Logging**: Complete request/response logging in Cosmos DB
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API clients

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + FastAPI |
| Frontend | Next.js + TypeScript + Shadcn/ui + Tailwind CSS |
| Infrastructure | Terraform + Azure |
| Database | Azure Cosmos DB (audit) + Azure Redis Cache (rate limiting) |
| AI Services | Azure AI Foundry (GPT-4o) + Azure AI Content Safety |

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm_security_gateway
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your Azure credentials
   ```

3. **Start with Docker Compose**
   ```bash
   docker compose up -d
   ```

4. **Access the services**
   - Backend API: http://localhost:8000
   - Frontend Dashboard: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

### Without Docker

**Backend:**
```bash
cd backend
pip install uv
uv sync
uv run uvicorn backend:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Gateway Endpoints (OpenAI-Compatible)

```
POST /v1/chat/completions     # Chat completions with security scanning
POST /v1/completions          # Text completions with security scanning
POST /v1/security/scan        # Standalone security scan
```

### Management Endpoints

```
GET  /api/audit               # List audit logs
GET  /api/audit/summary       # Audit summary statistics
GET  /api/analytics/threats   # Threat analytics
GET  /api/analytics/usage     # Usage analytics
GET  /health                  # Health check
GET  /ready                   # Readiness check
```

## Usage Example

```python
import openai

# Point to the Security Gateway instead of OpenAI
client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"  # Optional in dev mode
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)
```

## Security Scanning

The gateway performs the following security checks on all requests:

| Check | Description | Action |
|-------|-------------|--------|
| Prompt Injection | Detects instruction override attempts | Block |
| Jailbreak | Identifies known jailbreak patterns | Block |
| PII Detection | Scans for personal information | Mask |
| Secret Scanning | Finds API keys and credentials | Block |
| Content Filtering | Enforces content policies | Block |

## Configuration

Environment variables for the backend:

```bash
# Azure AI Foundry
AZURE_AI_ENDPOINT=https://your-ai-foundry.openai.azure.com/
AZURE_AI_API_KEY=your-api-key
AZURE_AI_DEPLOYMENT_NAME=gpt-4o

# Azure Content Safety
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-content-safety.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your-key

# Redis (Rate Limiting)
REDIS_URL=redis://localhost:6379

# Cosmos DB (Audit Logs)
COSMOS_CONNECTION_STRING=your-connection-string

# Security Settings
ENABLE_PROMPT_INJECTION_DETECTION=true
ENABLE_PII_DETECTION=true
ENABLE_SECRET_SCANNING=true
ENABLE_JAILBREAK_DETECTION=true
PII_ACTION=mask  # mask, block, or log
```

## Deployment

### Deploy to Azure

1. **Initialize Terraform**
   ```bash
   cd cloud_infra/environments/dev
   terraform init
   ```

2. **Review the plan**
   ```bash
   terraform plan
   ```

3. **Apply the configuration**
   ```bash
   terraform apply
   ```

4. **Get the outputs**
   ```bash
   terraform output
   ```

## Project Structure

```
llm_security_gateway/
├── backend/
│   ├── src/backend/
│   │   ├── api/           # API routes and middleware
│   │   ├── security/      # Security scanning modules
│   │   ├── providers/     # LLM provider clients
│   │   ├── storage/       # Database clients
│   │   ├── models/        # Pydantic models
│   │   └── config/        # Configuration
│   ├── tests/             # Test suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities
│   ├── Dockerfile
│   └── package.json
├── cloud_infra/
│   ├── environments/      # Environment configs
│   └── modules/           # Terraform modules
├── docker-compose.yml
└── README.md
```

## Testing

### Backend Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Security Testing
Use the Security Playground in the frontend dashboard to test various attack vectors with pre-built examples.

## License

MIT License

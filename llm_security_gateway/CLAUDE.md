# LLM Security Gateway - Development Guide

## Project Overview

This is an LLM Security Gateway built on Azure that acts as a security layer between applications and LLM providers. It provides:
- Prompt injection detection
- Jailbreak detection
- PII detection and masking
- Secret/credential scanning
- Content filtering
- Rate limiting
- Audit logging

## Quick Commands

### Start Development Environment
```bash
docker compose up -d
```

### Backend Development
```bash
cd backend
uv sync
uv run uvicorn backend:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Deploy Infrastructure
```bash
cd cloud_infra/environments/dev
terraform init
terraform plan
terraform apply
```

## Project Structure

```
llm_security_gateway/
├── backend/                 # FastAPI backend
│   └── src/backend/
│       ├── api/            # Routes and middleware
│       ├── security/       # Security detection modules
│       ├── providers/      # Azure AI clients
│       ├── storage/        # Redis and Cosmos clients
│       ├── models/         # Pydantic models
│       └── config/         # Settings and policies
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/           # Pages (dashboard, audit, playground, settings)
│       ├── components/    # React components
│       └── lib/           # API client and utilities
└── cloud_infra/           # Terraform infrastructure
    ├── environments/      # Dev/prod configs
    └── modules/           # Azure resource modules
```

## Key Files

### Backend
- `backend/src/backend/__init__.py` - FastAPI app entry
- `backend/src/backend/security/scanner.py` - Unified security scanner
- `backend/src/backend/api/routes/chat.py` - Chat completions endpoint
- `backend/src/backend/config/settings.py` - Configuration

### Frontend
- `frontend/src/app/page.tsx` - Dashboard
- `frontend/src/app/playground/page.tsx` - Security testing playground
- `frontend/src/lib/api.ts` - API client

### Infrastructure
- `cloud_infra/environments/dev/main.tf` - Main Terraform config
- `cloud_infra/modules/` - Reusable Terraform modules

## API Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat with security
- `POST /v1/security/scan` - Standalone security scan
- `GET /api/audit` - Query audit logs
- `GET /health` - Health check

## Environment Variables

Required for backend:
- `AZURE_AI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_AI_API_KEY` - Azure OpenAI API key
- `REDIS_URL` - Redis connection (default: redis://localhost:6379)

Optional:
- `COSMOS_CONNECTION_STRING` - For audit logging
- `AZURE_CONTENT_SAFETY_ENDPOINT` - For content safety checks

## Security Detection

The gateway detects:
1. **Prompt Injection** - Instruction override attempts
2. **Jailbreaks** - DAN, developer mode, etc.
3. **PII** - Names, emails, SSNs, credit cards
4. **Secrets** - API keys, passwords, tokens
5. **Content Violations** - Harmful content requests

Detection is performed by `SecurityScanner` which orchestrates all detectors.

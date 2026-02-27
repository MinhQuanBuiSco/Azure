# Blog 2: Protected API with FastAPI + Azure AD

Build a FastAPI backend that validates Azure AD JWT tokens, and call it from a Next.js frontend.

## What You'll Build

- A FastAPI backend with JWT token validation (JWKS-based)
- Custom API scopes exposed in Azure AD
- Protected CRUD endpoints for task management
- A Next.js frontend that acquires tokens and calls the API

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Azure CLI** (`az`) — [install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Azure subscription** (free tier works)

## Quick Start

### 1. Register the Apps (Azure CLI)

The setup script creates **two** app registrations (API + SPA), exposes a custom scope, and writes both env files.

```bash
az login
./setup.sh                        # defaults: "Blog2-API" + "Blog2-Frontend"
./setup.sh MyAPI MyFrontend       # or pass custom names
```

### 2. Run the Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at [http://localhost:8000](http://localhost:8000).

### 3. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at [http://localhost:3000](http://localhost:3000).

### Cleanup

```bash
./cleanup.sh
```

## Architecture

```
Browser (Next.js + MSAL)
   │
   │  Bearer token (scope: api://<api-id>/access_as_user)
   ▼
FastAPI Backend
   ├── GET  /api/me          → user profile from token claims
   ├── GET  /api/tasks       → list tasks
   ├── POST /api/tasks       → create task
   ├── PATCH /api/tasks/:id  → update task
   └── DELETE /api/tasks/:id → delete task
         │
         │  Validates JWT via Microsoft JWKS
         ▼
   Microsoft Entra ID
```

### Key Patterns

| Pattern | Implementation |
|---|---|
| Token validation | Download JWKS from Microsoft, verify RS256 signature, audience, issuer |
| Custom scope | API exposes `access_as_user` scope, frontend requests it |
| Token acquisition | `acquireTokenSilent` → fallback to `acquireTokenPopup` |
| CORS | FastAPI middleware allows `localhost:3000` |
| Per-user data | Tasks keyed by `oid` claim (user object ID) |

## Tech Stack

- **Next.js 14** (App Router) + **MSAL React**
- **FastAPI** + **python-jose** (JWT validation)
- **Tailwind CSS** + **shadcn/ui**
- **TypeScript** + **Python**

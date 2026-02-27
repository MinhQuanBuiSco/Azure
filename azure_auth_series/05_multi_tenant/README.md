# Blog 5 — Multi-Tenant Auth

Convert the single-tenant RBAC app (Blogs 3-4) into a **multi-tenant** app. Users from any Azure AD organization can sign in, with fully tenant-isolated data.

## What's Different from Blog 4

| Component | Blog 4 (Single-Tenant) | Blog 5 (Multi-Tenant) |
|---|---|---|
| App registration | Single tenant | `AzureADMultipleOrgs` |
| Frontend authority | `login.microsoftonline.com/{tenant-id}` | `login.microsoftonline.com/organizations` |
| JWKS endpoint | Static, one tenant | Dynamic per-token `tid` claim |
| Issuer validation | Hardcoded `sts.windows.net/{tid}/` | Dynamic `sts.windows.net/{tid}/` |
| Tenant gating | N/A | `ALLOWED_TENANT_IDS` env var |
| Task store | `{user_id: [tasks]}` | `{tenant_id: {user_id: [tasks]}}` |
| Admin scope | All tasks globally | All tasks **in their tenant only** |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                         │
│  authority: login.microsoftonline.com/organizations             │
│  → Any Azure AD org can sign in                                 │
└──────────────┬──────────────────────────────────────────────────┘
               │ Bearer token (includes tid claim)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                  │
│  1. Extract tid from unverified claims                           │
│  2. Check tenant allow-list (ALLOWED_TENANT_IDS)                 │
│  3. Fetch JWKS from login.microsoftonline.com/{tid}/...keys      │
│  4. Verify token with dynamic issuer: sts.windows.net/{tid}/     │
│  5. Route to tenant-isolated data store                          │
│                                                                  │
│  tasks_db = { tenant_id: { user_id: [tasks] } }                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Azure CLI (`az login`)
- Python 3.11+
- Node.js 18+

### 1. Create App Registrations

```bash
./setup.sh
```

This creates multi-tenant app registrations (`AzureADMultipleOrgs`), test users, role assignments, and writes `.env` files.

### 2. Start Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and sign in.

## Onboarding Another Tenant

`setup.sh` prints an **admin consent URL** at the end. Share it with an admin from another Azure AD tenant:

```
https://login.microsoftonline.com/organizations/adminconsent?client_id=<API_APP_ID>
```

After they consent:

1. Add their tenant ID to `ALLOWED_TENANT_IDS` in `backend/.env` (comma-separated)
2. Restart the backend
3. Users from that tenant can now sign in

To allow **any** Azure AD tenant without an allow-list:

```bash
ALLOW_ANY_TENANT=true
```

## Key Files

| File | Purpose |
|---|---|
| `backend/auth.py` | **Core teaching point** — dynamic per-tenant JWKS + issuer validation |
| `backend/config.py` | Tenant allow-list (`ALLOWED_TENANT_IDS`) and `ALLOW_ANY_TENANT` flag |
| `backend/main.py` | Tenant-isolated task store: `{tenant_id: {user_id: [tasks]}}` |
| `frontend/src/config/auth-config.ts` | Authority set to `organizations` (any Azure AD org) |

## Cleanup

```bash
./cleanup.sh
```

Deletes app registrations, test users, and local `.env` files. No infrastructure to destroy (this is local-only).

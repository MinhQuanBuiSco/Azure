# Blog 6: Service-to-Service Auth (Client Credentials + OBO)

Real enterprise apps have **multiple backend services** that talk to each other. This blog teaches the two fundamental service-to-service auth patterns in Azure AD:

- **On-Behalf-Of (OBO)** — Task API calls Notification Service *as the user* (user context preserved)
- **Client Credentials** — Task API calls Audit Service *as itself* (no user, app-only identity)

## Architecture

```
┌──────────┐  user token   ┌────────────────┐  OBO token     ┌─────────────────────┐
│ Frontend  │─────────────▶│  Task API       │──────────────▶│  Notification Svc    │
│ :3000     │              │  :8000          │               │  :8001               │
└──────────┘              │                  │               │  Validates OBO token  │
                          │  On task create: │               │  (has user context)   │
                          │  1. OBO → notify │               └─────────────────────┘
                          │  2. CC → audit   │
                          │                  │  client cred   ┌─────────────────────┐
                          │                  │──────────────▶│  Audit Service        │
                          └────────────────┘  (app-only)     │  :8002               │
                                                             │  Validates app token  │
                                                             │  (no user context)    │
                                                             └─────────────────────┘
```

## Quick Start

### 1. Create Azure AD resources

```bash
./setup.sh
```

This creates 4 app registrations, 3 test users, role assignments, permissions, and writes all `.env` files.

### 2. Start the services (3 terminals)

```bash
# Terminal 1 — Task API
cd task-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Notification Service
cd notification-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Terminal 3 — Audit Service
cd audit-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Test it

1. Open http://localhost:3000
2. Sign in as `testuser-admin` (or editor)
3. Create a task
4. Observe in the dashboard: **Notify: sent** and **Audit: logged** badges
5. Check terminal logs:
   - Notification Service shows **user name** (OBO token has user context)
   - Audit Service shows **app ID** (client credential token, no user)

### 5. Cleanup

```bash
./cleanup.sh
```

## OBO vs Client Credentials

| Aspect | On-Behalf-Of (OBO) | Client Credentials |
|---|---|---|
| **Use when** | Downstream service needs to know WHO the user is | Downstream service only cares THAT a trusted app is calling |
| **User context** | Preserved — token has `oid`, `name`, `tid` | None — token has app identity only |
| **Token claim** | `scp` (delegated scopes) | `roles` (application permissions) |
| **Consent** | User consents (or admin on behalf of org) | Admin consents (no user involved) |
| **MSAL method** | `acquire_token_on_behalf_of()` | `acquire_token_for_client()` |
| **Authority** | Tenant-specific (`/{tenant_id}`) | Home tenant (`/{home_tenant_id}`) |
| **Scope format** | `api://{target}/.default` | `api://{target}/.default` |
| **Example** | Personalized notifications | Audit logging, background jobs |

## Key Files

| File | Purpose |
|---|---|
| `task-api/obo_client.py` | OBO token acquisition via MSAL → calls Notification Service |
| `task-api/service_client.py` | Client credentials token via MSAL → calls Audit Service |
| `task-api/auth.py` | Multi-tenant user token validation (same as Blog 5) |
| `notification-service/auth.py` | Validates OBO tokens (delegated, has user claims) |
| `audit-service/auth.py` | Validates app-only tokens (checks `AuditLog.Write` role) |
| `setup.sh` | Creates 4 app registrations + permissions + test users |

## Token Flow

```
User signs in via SPA
  │
  ▼
SPA acquires token for Task API
  │  scope: api://{task-api}/access_as_user
  │  token has: scp="access_as_user", oid, name, tid
  │
  ▼
Task API validates user token (auth.py)
  │
  ├──▶ OBO: acquire_token_on_behalf_of(user_token)
  │     scope: api://{notification-svc}/.default
  │     result: NEW token with oid, name, tid (user context preserved)
  │     → POST /notify to Notification Service
  │
  └──▶ Client Credentials: acquire_token_for_client()
        scope: api://{audit-svc}/.default
        result: token with roles=["AuditLog.Write"] (NO user context)
        → POST /audit to Audit Service
```

## What Changed from Blog 5

| Component | Blog 5 | Blog 6 |
|---|---|---|
| Backend services | 1 (Task API) | 3 (Task API + Notification + Audit) |
| Task API secrets | None (public client) | Client secret (for OBO/client cred) |
| MSAL library | Not used | `msal` for token acquisition |
| App registrations | 2 (API + SPA) | 4 (API + SPA + Notification + Audit) |
| Task create response | Task only | Task + notification_status + audit_status |

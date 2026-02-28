# Blog 7: API Gateway with Azure API Management

Centralized authentication using Azure API Management (APIM) as a gateway in front of three microservices. APIM handles JWT validation, rate limiting, and routing — so backends can focus on business logic.

## Architecture

```
                         ┌──────────────────────────────────────────────┐
                         │        Azure API Management (APIM)           │
                         │        Developer tier                        │
┌──────────┐  Bearer     │  ┌────────────────────────────────────────┐  │
│ Frontend  │────────────▶│  │  validate-jwt policy                   │  │
│ (local    │             │  │  - Verify signature (JWKS)             │  │
│  :3000)   │             │  │  - Check audience + issuer             │  │
└──────────┘             │  │  - Extract claims → headers            │  │
                         │  └──────────────┬─────────────────────────┘  │
                         │                 │ validated                   │
                         │     ┌───────────┼───────────┐               │
                         │     ▼           ▼           ▼               │
                         │  /api/*      /notify     /audit             │
                         └──────┬──────────┬───────────┬───────────────┘
                                │          │           │
                         ┌──────▼──┐  ┌────▼────┐  ┌──▼──────┐
                         │Task API │  │Notif Svc│  │Audit Svc│
                         │Cont.App│  │Cont.App │  │Cont.App │
                         └─────┬──┘  └─────────┘  └─────────┘
                               │ direct (OBO + client cred)
                               ├──────────▶ Notification Svc
                               └──────────▶ Audit Svc
```

**Key pattern:** External traffic goes through APIM. Internal S2S calls (Task API → Notification/Audit) go direct — not through the gateway.

## What Changed from Blog 6

| Component | Blog 6 | Blog 7 |
|---|---|---|
| Infrastructure | Local only | Azure: APIM + 3 Container Apps (Terraform) |
| JWT validation | Each service validates independently | APIM validates at gateway, backends trust headers |
| Rate limiting | None | APIM rate-limit-by-key policy |
| Backend auth | Always validate JWT | Dual mode: JWT validation OR trust APIM headers |
| Frontend API URL | `http://localhost:8000` | APIM gateway URL |
| CORS | FastAPI middleware | APIM policy (+ FastAPI as fallback) |

## Quick Start

### Prerequisites

- Azure CLI (`az login`)
- Terraform >= 1.5
- Docker
- Node.js >= 18

### Deploy

```bash
./setup.sh
```

The script will:
1. Create 4 Azure AD app registrations (same as Blog 6)
2. Create 3 test users with role assignments
3. Deploy infrastructure via Terraform (~30-45 min for APIM)
4. Build and push Docker images to ACR
5. Update Container Apps with real images
6. Write `.env` files for all services + frontend

### Run Frontend

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 → Sign in → Create tasks → Verify Notify + Audit badges.

### Local Development

The services also work locally (Blog 6 mode) with `TRUST_GATEWAY=false`:

```bash
# Terminal 1
cd task-api && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Terminal 2
cd notification-service && pip install -r requirements.txt && uvicorn main:app --reload --port 8001

# Terminal 3
cd audit-service && pip install -r requirements.txt && uvicorn main:app --reload --port 8002
```

### Destroy

```bash
./cleanup.sh
```

## Centralized vs Decentralized Auth

**Blog 6 (Decentralized):** Each service fetches JWKS, validates signatures, checks audiences, and enforces roles independently. Consistent behavior requires duplicating validation logic everywhere.

**Blog 7 (Centralized):** APIM validates the JWT once at the gateway, then forwards validated claims as HTTP headers (`X-User-OID`, `X-User-Name`, `X-Tenant-ID`, `X-User-Roles`). Backends trust these headers when `TRUST_GATEWAY=true`.

**Best practice:** Use APIM as the primary auth gate + keep JWT validation in backends as optional defense-in-depth (toggle with `TRUST_GATEWAY`).

## APIM Policy Breakdown

### JWT Validation (task-api.xml)

```xml
<!-- Validate token using OpenID Connect discovery -->
<validate-jwt header-name="Authorization" require-scheme="Bearer">
  <openid-config url="https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration" />
  <audiences><audience>api://{client_id}</audience></audiences>
  <issuers><issuer>https://sts.windows.net/{tenant}/</issuer></issuers>
</validate-jwt>

<!-- Forward validated claims to backend -->
<set-header name="X-User-OID" exists-action="override">
  <value>@(context.Request.Headers.GetValueOrDefault("Authorization","").AsJwt()?.Claims["oid"]?.FirstOrDefault())</value>
</set-header>
```

### Rate Limiting

```xml
<!-- 100 requests per minute per user (or per IP for unauthenticated) -->
<rate-limit-by-key calls="100" renewal-period="60"
  counter-key="@(context.Request.Headers.GetValueOrDefault("Authorization","").AsJwt()?.Subject ?? context.Request.IpAddress)" />
```

### Audit API — Role Enforcement

```xml
<!-- APIM checks the AuditLog.Write role in the JWT -->
<required-claims>
  <claim name="roles" match="any">
    <value>AuditLog.Write</value>
  </claim>
</required-claims>
```

## Key Files

| File | Purpose |
|---|---|
| `infra/main.tf` | Root Terraform — modules for RG, ACR, Container Apps, APIM |
| `infra/modules/api_management/main.tf` | APIM instance + 3 APIs + operations + policies |
| `infra/modules/api_management/policies/task-api.xml` | JWT validation + rate limit + CORS + claim headers |
| `infra/modules/api_management/policies/audit.xml` | JWT validation + AuditLog.Write role enforcement |
| `infra/modules/container_apps/main.tf` | 3 Container Apps with env vars |
| `task-api/auth.py` | Dual-mode: JWT validation OR trust APIM headers |
| `task-api/config.py` | TRUST_GATEWAY env var |
| `setup.sh` | Full setup: AD + Terraform + Docker + deploy |
| `cleanup.sh` | Full teardown |

## Cost Warning

APIM Developer tier costs ~$50/month. Run `./cleanup.sh` after testing to avoid charges. The `terraform destroy` in cleanup removes all Azure resources.

## Teaching Points

1. **Centralized auth at the gateway** — One policy manages JWT validation for all APIs
2. **validate-jwt policy** — Uses OpenID Connect discovery for automatic JWKS refresh
3. **Claims forwarding** — APIM extracts validated claims and passes them as trusted headers
4. **Per-API policies** — Different JWT audiences per API (user tokens vs app tokens)
5. **Rate limiting** — Per-user throttling via JWT subject claim
6. **Dual-mode backends** — Gateway trust mode for cloud, JWT validation for local dev

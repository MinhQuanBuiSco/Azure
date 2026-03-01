# Blog 8: Production Readiness — Monitoring, Alerts & Security Hardening

Blog 7 deployed 3 microservices behind Azure API Management. Everything works, but it's not production-ready. Blog 8 adds **Application Insights + OpenTelemetry**, **KQL queries**, **alert rules**, and **security hardening** — all using free-tier Azure resources.

## Architecture

```
┌──────────────┐ Bearer ┌────────────────────────────────────────────┐
│ Frontend     │───────▶│  Azure API Management (APIM)                │
│ Container App│        │  + APIM Diagnostics → App Insights          │
│ (port 3000)  │        │  validate-jwt → rate-limit → route          │
└──────────────┘        └──────┬──────────┬───────────┬──────────────┘
                              │          │           │
                       ┌──────▼──┐  ┌────▼────┐  ┌──▼──────┐
                       │Task API │  │Notif Svc│  │Audit Svc│
                       │external │  │INTERNAL │  │INTERNAL │
                       │+ OTel   │  │+ OTel   │  │+ OTel   │
                       │+ health │  │+ health │  │+ health │
                       └────┬────┘  └─────────┘  └─────────┘
                            │ direct S2S (internal network)
                            ├──────▶ Notification (internal)
                            └──────▶ Audit (internal)

                       ┌─────────────────────────────────┐
                       │   Application Insights            │
                       │   - APIM request logs             │
                       │   - FastAPI traces (OTel)         │
                       │   - KQL queries                   │
                       │   - Alert rules → Action Group    │
                       └─────────────────────────────────┘
```

## What's New from Blog 7

| Component | Blog 7 | Blog 8 |
|---|---|---|
| Observability | None | Application Insights + OpenTelemetry |
| Alerting | None | Azure Monitor alert rules + email action group |
| APIM diagnostics | None | Logger + diagnostic linked to App Insights |
| Frontend hosting | `npm run dev` (localhost) | Azure Container App (deployed) |
| Notification/Audit ingress | `external_enabled = true` | `external_enabled = false` (internal only) |
| Health probes | None | Liveness + readiness on `/health` |
| Scaling | min=0, max=1 | min=1, max=3 |
| Python deps | fastapi, jose, httpx | + azure-monitor-opentelemetry |
| Frontend theme | Blue/indigo | Emerald/green (monitoring/health) |
| KQL queries | None | 5 security/ops query files |

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
1. Create 4 Azure AD app registrations
2. Create 3 test users with role assignments
3. Deploy infrastructure via Terraform (~30-45 min for APIM)
4. Build and push Docker images to ACR (3 backends + frontend)
5. Update all 4 Container Apps with real images
6. Update SPA redirect URIs for deployed frontend
7. Write `.env` files for all services + frontend
8. Verify monitoring setup

### Open Frontend

The frontend is deployed as a Container App. After `setup.sh` completes, open the `FRONTEND_URL` printed in the output. Sign in → Create tasks → Verify Notify + Audit badges.

For local development:

```bash
cd frontend && npm install && npm run dev
```

### Destroy

```bash
./cleanup.sh
```

## Application Insights + OpenTelemetry

All three services use `azure-monitor-opentelemetry` which auto-instruments:
- **FastAPI requests** — every HTTP request is traced
- **httpx calls** — S2S dependency calls (OBO, client credentials) are tracked
- **Exceptions** — unhandled errors flow to App Insights

No manual span creation needed. Just set `APPLICATIONINSIGHTS_CONNECTION_STRING` and traces flow automatically.

APIM also sends diagnostics to App Insights via a logger + diagnostic resource, capturing:
- Frontend request/response metadata
- Backend request/response metadata
- Custom headers (X-User-OID, X-Tenant-ID)
- W3C trace correlation

## KQL Query Guide

Five query files in `kql/` for copy-pasting into App Insights → Logs:

| File | Purpose |
|---|---|
| `failed-auth-requests.kql` | 401/403 errors by endpoint — detect brute-force attempts |
| `slow-requests.kql` | P95 latency > 2s — identify slow endpoints |
| `error-rate-by-service.kql` | 5xx rate per cloud role — which service is failing |
| `top-callers.kql` | Most active users by OID — usage patterns |
| `dependency-failures.kql` | Failed S2S calls — OBO/client credentials issues |

## Alert Rules

Two metric alerts configured via Terraform:

| Alert | Condition | Severity | Window |
|---|---|---|---|
| High error rate | >10 failed requests | 2 (Warning) | 5 minutes |
| Slow response | Avg duration >5s | 3 (Informational) | 5 minutes |

Alerts fire to an email action group. Add more receivers (SMS, webhook, Logic App) by modifying `infra/modules/monitoring/main.tf`.

## Security Hardening

### Internal Ingress

Notification and Audit services are now **internal only** (`external_enabled = false`). They're reachable within the Container Apps Environment but not from the internet. Only Task API (which APIM routes to) has external ingress.

### Health Probes

All three services have:
- **Liveness probe**: `/health` every 30s — restarts unhealthy containers
- **Readiness probe**: `/health` every 10s — removes from load balancer if unhealthy

### Auto-Scaling

- **min_replicas = 1** — always at least one instance running (no cold starts)
- **max_replicas = 3** — scales up under load

## Key Files

| File | Description |
|---|---|
| `infra/modules/monitoring/main.tf` | App Insights + action group + alert rules |
| `frontend/Dockerfile` | Multi-stage build for Next.js standalone (NEXT_PUBLIC_* baked at build) |
| `infra/modules/container_apps/main.tf` | 4 Container Apps: task-api, notification, audit, frontend |
| `infra/modules/api_management/main.tf` | APIM identity + logger + diagnostic |
| `infra/modules/api_management/policies/task-api.xml` | JWT validation + rate limit + CORS + claim headers |
| `task-api/main.py` | OTel init + /health endpoint |
| `notification-service/main.py` | OTel init + /health endpoint |
| `audit-service/main.py` | OTel init + /health endpoint |
| `kql/*.kql` | 5 operational KQL queries |
| `setup.sh` | Full deployment with monitoring verification |
| `cleanup.sh` | Full teardown |

## Cost

- **APIM Developer tier**: ~$50/month (same as Blog 7)
- **Application Insights**: Free tier = 5 GB/month ingestion (sufficient for dev/testing)
- **Container Apps**: Consumption plan pricing (minimal for 4 small services)
- **Alert rules**: Free (included with Azure Monitor)

Run `./cleanup.sh` when done to destroy all resources.

## Teaching Points

1. **Application Insights + OTel** — One-line instrumentation for automatic request + dependency tracing
2. **APIM Diagnostics** — Gateway-level telemetry with W3C trace correlation
3. **KQL queries** — Operational queries for security monitoring and performance analysis
4. **Alert rules** — Automated detection of error spikes and latency degradation
5. **Internal ingress** — Lock down services that should only be reachable internally
6. **Health probes** — Let the platform detect and recover from unhealthy instances
7. **Auto-scaling** — Always-on with room to scale under load
8. **Frontend on Container Apps** — Next.js standalone build with NEXT_PUBLIC_* baked at Docker build time

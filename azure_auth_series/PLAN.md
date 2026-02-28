# Implementation Plan — Azure Auth Blog Series

Comprehensive series for solution architects covering every authentication & authorization pattern in Microsoft Entra ID.

---

## Series Overview

| Blog | Title | Status |
|------|-------|--------|
| 01 | Basic Login (MSAL + OpenID Connect) | DONE |
| 02 | Protected API (JWT validation + custom scopes) | DONE |
| 03 | RBAC (App Roles + authorization matrix) | DONE |
| 04 | Managed Identity (Key Vault + secret-less deploy) | DONE |
| 05 | Multi-Tenant (Dynamic JWKS + tenant isolation) | DONE |
| **06** | **Service-to-Service Auth (Client Credentials + OBO)** | TODO |
| **07** | **API Gateway (API Management + JWT policies)** | TODO |
| **08** | **Customer-Facing Auth (Entra External ID + social login)** | TODO |
| **09** | **CI/CD & Workload Identity Federation** | TODO |
| **10** | **Zero Trust Production Hardening** | TODO |

---

## Blog 6: Service-to-Service Auth (Client Credentials + On-Behalf-Of)

### Why This Matters (Solution Architect POV)
Every enterprise has multiple backend services that need to talk to each other. Two patterns dominate:
- **Client Credentials** — service calls service with its own identity (background jobs, event processing, internal APIs)
- **On-Behalf-Of (OBO)** — service calls service on behalf of the logged-in user (preserving user context through a chain)

Clients will ask: "How should my Order Service call my Inventory Service?" This blog answers that.

### Architecture
```
┌─────────────┐     user token     ┌──────────────┐   OBO token    ┌────────────────────┐
│   Frontend   │──────────────────▶│  Task API     │──────────────▶│  Notification Svc  │
│   (SPA)      │                   │  (FastAPI)    │               │  (FastAPI)         │
└─────────────┘                   │               │               │  - Send emails     │
                                  │  Also calls:  │               │  - Push webhooks   │
                                  │               │               └────────────────────┘
                                  │               │  client cred
                                  │               │──────────────▶┌────────────────────┐
                                  │               │               │  Audit Service     │
                                  │               │  (app-only,   │  (FastAPI)         │
                                  └──────────────┘   no user)     │  - Log events      │
                                                                  └────────────────────┘
```

### What's New
| Component | Details |
|---|---|
| Notification Service | New FastAPI service, validates OBO tokens, sends notifications |
| Audit Service | New FastAPI service, validates client credential tokens (no user context) |
| OBO flow in Task API | `ConfidentialClientApplication.acquire_token_on_behalf_of()` |
| Client Credentials | `ConfidentialClientApplication.acquire_token_for_client()` |
| App registration | New app regs for Notification + Audit services with app permissions |

### Azure Setup
1. **Notification Service** app registration
   - Expose API scope: `api://notification-svc/Notify.Send`
   - App role: `Notification.Send` (for client credentials path)
2. **Audit Service** app registration
   - App role: `AuditLog.Write` (application permission only — no user delegation)
3. **Task API** registration updates
   - Add API permission: `Notification.Send` (delegated, for OBO)
   - Add API permission: `AuditLog.Write` (application, for client credentials)
   - Add client secret (needed for OBO + client credentials)

### File Structure
```
06_service_to_service/
├── README.md
├── setup.sh
├── cleanup.sh
├── task-api/                   # Extended from Blog 5 backend
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── obo_client.py           # OBO token acquisition
│   ├── service_client.py       # Client credentials token acquisition
│   ├── requirements.txt        # + msal
│   └── .env.example
├── notification-service/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
├── audit-service/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/                   # Minimal changes from Blog 5
    └── src/app/dashboard/page.tsx
```

### Key Teaching Points
- When to use OBO vs Client Credentials (decision framework)
- Token chain: user token → OBO token → downstream service
- App permissions vs delegated permissions
- Client secret management (sets up why Blog 9's workload identity matters)

---

## Blog 7: API Gateway with Azure API Management

### Why This Matters (Solution Architect POV)
Clients with 5+ microservices always ask: "How do we manage auth centrally instead of each service validating tokens?" API Management (APIM) is the answer — it handles JWT validation, rate limiting, and routing at the gateway level.

### Architecture
```
                         ┌──────────────────────────────────────┐
                         │     Azure API Management (APIM)       │
                         │                                        │
┌──────────┐  Bearer     │  ┌─────────────────────────────────┐  │
│ Frontend  │────────────▶│  │  JWT Validation Policy          │  │
│           │             │  │  - Validate signature (JWKS)     │  │
└──────────┘             │  │  - Check audience                 │  │
                         │  │  - Check issuer                   │  │
                         │  │  - Check roles (optional)         │  │
                         │  └──────────────┬──────────────────┘  │
                         │                 │ validated            │
                         │     ┌───────────┼───────────┐         │
                         │     ▼           ▼           ▼         │
                         │  /tasks      /notify     /audit       │
                         │  Task API    Notif Svc   Audit Svc    │
                         └──────────────────────────────────────┘
```

### What's New
| Component | Details |
|---|---|
| APIM instance | Terraform: `azurerm_api_management` (Developer tier) |
| JWT validation policy | XML inbound policy with `<validate-jwt>` |
| Role-based routing | APIM policy checks `roles` claim |
| Rate limiting | Per-subscription rate limiting policy |
| Backend simplification | Services remove JWT validation, trust APIM headers |

### Terraform Resources
```hcl
azurerm_api_management
azurerm_api_management_api
azurerm_api_management_api_policy   # validate-jwt inbound policies
azurerm_api_management_product
azurerm_api_management_subscription
azurerm_api_management_logger       # Application Insights
```

### File Structure
```
07_api_gateway/
├── README.md
├── setup.sh
├── cleanup.sh
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── policies/
│       ├── jwt-validation.xml
│       └── rate-limit.xml
├── task-api/                   # Simplified — no local JWT validation
├── notification-service/       # Simplified
├── audit-service/              # Simplified
└── frontend/
    └── src/config/auth-config.ts  # Points to APIM URL
```

### Key Teaching Points
- Centralized vs decentralized auth validation (trade-offs)
- APIM JWT policy XML syntax
- When to use APIM (cost vs complexity vs scale)
- Products & subscriptions for API monetization

---

## Blog 8: Customer-Facing Auth (Microsoft Entra External ID)

### Why This Matters (Solution Architect POV)
Blogs 1-7 cover workforce identity (employees, B2B). Consumer-facing apps need: self-service sign-up, social logins (Google/Apple), branded login pages. Azure AD B2C is deprecated for new customers (May 2025) — **Entra External ID** is the replacement.

### Architecture
```
┌──────────────────────────────────────────┐
│            SecureShop (E-Commerce)         │
│                                            │
│  ┌───────────┐    ┌───────────────────┐   │
│  │  Next.js   │    │  FastAPI Backend   │   │
│  │  Frontend  │    │  (Product API)     │   │
│  └─────┬─────┘    └───────────────────┘   │
│        │                                    │
│        ▼                                    │
│  ┌──────────────────────────┐              │
│  │  Entra External ID Tenant │              │
│  │  (*.ciamlogin.com)        │              │
│  │                            │              │
│  │  - Email/password sign-up  │              │
│  │  - Google sign-in          │              │
│  │  - Apple sign-in           │              │
│  │  - Custom branding         │              │
│  │  - Self-service profile    │              │
│  └──────────────────────────┘              │
└──────────────────────────────────────────┘
```

### What's New
| Component | Details |
|---|---|
| External ID tenant | Separate Entra tenant for customer identities |
| Authority | `https://{tenant}.ciamlogin.com` (not login.microsoftonline.com) |
| Social identity providers | Google, Apple |
| User flows | Sign-up/sign-in with custom attributes |
| SecureShop project | New e-commerce app (separate from SecureTask) |

### File Structure
```
08_customer_auth/
├── README.md
├── setup.sh
├── cleanup.sh
├── backend/
│   ├── main.py                 # Product catalog + cart API
│   ├── auth.py                 # Validates External ID tokens
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── config/auth-config.ts  # ciamlogin.com authority
    │   ├── app/
    │   │   ├── page.tsx            # Shop landing page
    │   │   ├── products/page.tsx   # Product catalog
    │   │   ├── cart/page.tsx       # Shopping cart
    │   │   └── profile/page.tsx    # Customer profile
    │   └── components/
    │       ├── auth/
    │       └── shop/
    ├── package.json
    └── .env.local.example
```

### Key Teaching Points
- Entra ID (workforce) vs External ID (customers) — when to use which
- B2C deprecation and migration path
- Social identity provider setup
- Token differences (claims, issuer, scopes)
- Cost model (per monthly active user)

---

## Blog 9: CI/CD & Workload Identity Federation

### Why This Matters (Solution Architect POV)
Every client asks: "How do we deploy securely from GitHub Actions without storing secrets?" Workload Identity Federation removes client secrets for CI/CD pipelines using federated tokens. This is the modern best practice.

### Architecture
```
┌─────────────────────┐           ┌──────────────────────┐
│   GitHub Actions     │           │   Microsoft Entra ID  │
│                      │           │                        │
│  1. GitHub OIDC      │───────▶  │  2. Federated Identity │
│     issues token     │           │     Credential checks  │
│                      │           │     GitHub OIDC issuer │
│  3. az login with    │◀──────── │                        │
│     federated token  │           │  4. Returns Azure      │
│                      │           │     access token       │
│  5. Deploy to Azure  │           │     (no secrets!)      │
└─────────────────────┘           └──────────────────────┘
```

### What's New
| Component | Details |
|---|---|
| Federated Identity Credential | Trust GitHub Actions OIDC issuer |
| GitHub Actions workflow | `azure/login@v2` with OIDC |
| Terraform deployment | Automated infra provisioning in CI |
| Environment protection | GitHub environments with approval gates |
| Multiple environments | dev / staging / prod with separate credentials |

### File Structure
```
09_cicd_workload_identity/
├── README.md
├── setup.sh
├── cleanup.sh
├── infra/
│   ├── main.tf                   # Federated identity credential
│   ├── variables.tf
│   └── outputs.tf
├── .github/
│   └── workflows/
│       ├── deploy-infra.yml      # Terraform plan/apply with OIDC
│       ├── deploy-backend.yml    # Build + deploy API
│       └── deploy-frontend.yml   # Build + deploy SWA
└── docs/
    ├── secret-rotation-comparison.md
    └── multi-env-strategy.md
```

### Key Teaching Points
- Why federated credentials > client secrets > certificates
- GitHub OIDC token structure and claims
- Scoping federated credentials (repo, branch, environment, tag)
- Multi-environment deployment strategy
- Cost: free (no additional Azure cost)

---

## Blog 10: Zero Trust Production Hardening

### Why This Matters (Solution Architect POV)
The "production checklist" that ties everything together. Clients need: Conditional Access, audit logging, token security, monitoring, and compliance before going live.

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    ZERO TRUST ARCHITECTURE                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Conditional   │  │ Identity     │  │ Azure Monitor     │  │
│  │ Access        │  │ Protection   │  │ + Sentinel        │  │
│  │ - MFA admins  │  │ - Risky      │  │ - Sign-in logs    │  │
│  │ - Device      │  │   sign-in    │  │ - KQL queries     │  │
│  │ - Location    │  │ - Block      │  │ - Alert rules     │  │
│  │               │  │   legacy     │  │ - Dashboards      │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Token         │  │ Network      │  │ Compliance        │  │
│  │ Security      │  │ Security     │  │ - Consent         │  │
│  │ - CAE         │  │ - Private    │  │   framework       │  │
│  │ - Short TTL   │  │   endpoint   │  │ - Least privilege │  │
│  │ - Proof-of-   │  │ - VNet       │  │ - NIST/ISO        │  │
│  │   possession  │  │ - WAF        │  │   mapping         │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Terraform Resources
```hcl
azuread_conditional_access_policy       # MFA for admins, block legacy auth
azuread_named_location                  # Trusted locations
azurerm_log_analytics_workspace
azurerm_monitor_diagnostic_setting      # Entra sign-in logs
azurerm_monitor_scheduled_query_rules_alert_v2
azurerm_private_endpoint               # Key Vault private endpoint
azuread_token_lifetime_policy
```

### File Structure
```
10_zero_trust_production/
├── README.md
├── setup.sh
├── cleanup.sh
├── infra/
│   ├── main.tf
│   ├── conditional-access.tf
│   ├── monitoring.tf
│   ├── network.tf
│   ├── variables.tf
│   └── outputs.tf
├── monitoring/
│   ├── queries/
│   │   ├── failed-signins.kql
│   │   ├── risky-signins.kql
│   │   ├── role-changes.kql
│   │   └── consent-grants.kql
│   └── workbooks/
│       └── auth-dashboard.json
├── security-checklist.md
└── docs/
    ├── conditional-access-guide.md
    ├── token-security.md
    └── compliance-mapping.md
```

### Key Teaching Points
- Zero Trust principles applied to identity
- Conditional Access policy design
- KQL queries for security monitoring
- CAE (near-real-time token revocation)
- Production security checklist
- Compliance mapping (NIST/ISO/SOC2)

---

## Solution Architect Use-Case Coverage

| Client Question | Blog |
|---|---|
| "How do I add SSO to my web app?" | 1 |
| "How do I protect my API?" | 2 |
| "How do I implement role-based access?" | 3 |
| "How do I deploy without hardcoding secrets?" | 4 |
| "How do I support multiple organizations?" | 5 |
| "How do my microservices authenticate with each other?" | 6 |
| "How do I centralize auth at the gateway?" | 7 |
| "How do I build customer-facing auth with social logins?" | 8 |
| "How do I deploy from CI/CD without secrets?" | 9 |
| "How do I secure everything for production?" | 10 |
| "How do I implement MFA and Conditional Access?" | 10 |
| "How do I monitor auth events and detect threats?" | 10 |
| "What's the best API security architecture?" | 7 |
| "How do I implement Zero Trust for identity?" | 10 |

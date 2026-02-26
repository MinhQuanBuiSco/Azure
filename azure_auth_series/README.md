# Azure Authentication & Authorization — Blog Series

A hands-on blog series that teaches Azure authentication and authorization by building real applications, progressing from basic login to production-grade zero trust architecture.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | **Next.js 14+ (App Router)** + TypeScript | Modern React framework, great MSAL support |
| UI | **shadcn/ui** + **Tailwind CSS** | Beautiful, accessible, production-grade components |
| Auth Library (Frontend) | **@azure/msal-react** + **@azure/msal-browser** | Official Microsoft auth library for SPAs |
| Backend | **Python FastAPI** | Clean, async, easy to follow in blog format |
| Auth Library (Backend) | **python-jose** + **azure-identity** | JWT validation + Managed Identity |
| IaC | **Terraform** + **azurerm provider** | Infrastructure as Code for all Azure resources |
| Identity Provider | **Microsoft Entra ID** (Azure AD) | Enterprise identity, OAuth 2.0 / OpenID Connect |

## Blog Series Overview

### Blog 1: Basic Login (`01_basic_login/`)
> **Goal:** Get a user signed in with Microsoft Entra ID

- Register an app in Microsoft Entra ID
- Build a Next.js app with MSAL.js
- Implement sign-in / sign-out with popup flow
- Display user profile info from ID token
- Call Microsoft Graph API to fetch user details

**Key Concepts:** App registration, OAuth 2.0 Authorization Code Flow with PKCE, ID tokens, MSAL React hooks (`useMsal`, `AuthenticatedTemplate`)

---

### Blog 2: Protected API (`02_protected_api/`)
> **Goal:** Build a backend API that only authenticated users can access

- Build a FastAPI backend with token validation
- Configure API permissions and scopes in Entra ID
- Frontend acquires access tokens and calls the protected API
- Implement a simple Task CRUD API

**Key Concepts:** Access tokens vs ID tokens, scopes & permissions, Bearer token authentication, token validation (issuer, audience, signature)

---

### Blog 3: Role-Based Access Control (`03_rbac/`)
> **Goal:** Control what each user can do based on their role

- Define App Roles (Admin, Editor, Reader) in app registration
- Assign roles to users/groups in Azure portal
- Backend enforces role-based authorization on endpoints
- Frontend conditionally renders UI based on user roles

**Key Concepts:** App Roles, token claims (`roles`), authorization decorators, role assignment, principle of least privilege

---

### Blog 4: Managed Identity (`04_managed_identity/`)
> **Goal:** Deploy to Azure with zero secrets in code

- Deploy frontend to Azure Static Web Apps
- Deploy backend to Azure App Service
- Use Managed Identity to access Key Vault (secrets), Storage (blobs), and Azure SQL
- Terraform modules for all infrastructure
- Remove all hardcoded secrets from code

**Key Concepts:** System-assigned vs user-assigned Managed Identity, `DefaultAzureCredential`, Azure RBAC for resources, Key Vault references, secret-less architecture

---

### Blog 5: Multi-Tenant App (`05_multi_tenant/`)
> **Goal:** Allow users from any organization to sign in

- Convert app registration to multi-tenant
- Handle admin consent flow for new tenants
- Implement tenant-specific data isolation
- Tenant onboarding and management UI

**Key Concepts:** Multi-tenant app registration, `common` vs `organizations` authority, admin consent, tenant ID filtering, data isolation patterns

---

### Blog 6: Azure AD B2C (`06_b2c/`)
> **Goal:** Build customer-facing auth with social logins

- Set up an Azure AD B2C tenant
- Configure sign-up/sign-in user flows
- Add social identity providers (Google, GitHub)
- Customize the login UI with branding
- Build a simple storefront ("SecureShop")

**Key Concepts:** B2C vs Entra ID (when to use which), user flows vs custom policies, identity providers, custom branding, self-service sign-up

---

### Blog 7: Microservices Auth (`07_microservices/`)
> **Goal:** Authenticate services to each other without user involvement

- Build a notification microservice
- Implement client credentials flow (machine-to-machine)
- Add Azure API Management as gateway with OAuth validation policies
- Service-to-service token exchange

**Key Concepts:** Client credentials grant, daemon/service apps, API Management OAuth policies, on-behalf-of flow, service principals

---

### Blog 8: Production Readiness (`08_production/`)
> **Goal:** Harden everything for production with Zero Trust principles

- Implement Conditional Access policies
- Add token caching and refresh strategies
- Implement proper error handling and retry logic
- Add monitoring with Azure Application Insights
- Security best practices audit

**Key Concepts:** Zero Trust architecture, Conditional Access, token lifecycle management, security monitoring, OWASP identity best practices

---

## Project Architecture

```
Blog 1          Blog 2          Blog 3          Blog 4-5
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐
│  Next.js  │   │  Next.js  │   │  Next.js  │   │     Next.js      │
│  + MSAL   │   │  + MSAL   │   │  + MSAL   │   │  + MSAL + Roles  │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────────────┘
     │              │              │               │
     ▼              ▼              ▼               ▼
 Entra ID      ┌────────┐   ┌────────────┐   ┌────────────┐
               │ FastAPI │   │  FastAPI    │   │  FastAPI    │──▶ Key Vault
               │  + JWT  │   │ + JWT+Roles │   │ + Managed  │──▶ Storage
               └────────┘   └────────────┘   │   Identity  │──▶ Azure SQL
                                              └────────────┘

Blog 7                              Blog 8
┌──────────────────┐               ┌──────────────────────────┐
│     Next.js      │               │        Next.js           │
│  + MSAL + Roles  │               │  + MSAL + Roles + Cache  │
└────┬─────────────┘               └────┬─────────────────────┘
     │                                  │
     ▼                                  ▼
┌──────────────┐                   ┌──────────────┐
│    API Mgmt  │                   │  API Mgmt +  │
│   (Gateway)  │                   │ Cond. Access  │
└──┬───────┬───┘                   └──┬───────┬───┘
   │       │                          │       │
   ▼       ▼                          ▼       ▼
┌──────┐ ┌──────────────┐         ┌──────┐ ┌──────────────┐
│ API  │ │ Notification │         │ API  │ │ Notification │
│      │ │  Service     │         │      │ │  Service     │
└──────┘ └──────────────┘         └──────┘ └──────────────┘
```

## Folder Structure

```
azure_auth_series/
├── README.md                          ← You are here
├── PLAN.md                            ← Detailed implementation plan
│
├── 01_basic_login/
│   ├── frontend/                      # Next.js + MSAL + shadcn/ui
│   └── README.md                      # Blog 1 guide
│
├── 02_protected_api/
│   ├── frontend/                      # Extended from 01
│   ├── backend/                       # FastAPI + JWT validation
│   └── README.md
│
├── 03_rbac/
│   ├── frontend/                      # + Role-based UI
│   ├── backend/                       # + Role enforcement
│   └── README.md
│
├── 04_managed_identity/
│   ├── frontend/
│   ├── backend/                       # + DefaultAzureCredential
│   ├── infra/terraform/               # App Service, Key Vault, SQL
│   └── README.md
│
├── 05_multi_tenant/
│   ├── frontend/                      # + Tenant picker
│   ├── backend/                       # + Tenant isolation
│   ├── infra/terraform/
│   └── README.md
│
├── 06_b2c/
│   ├── frontend/                      # SecureShop storefront
│   ├── backend/
│   ├── infra/terraform/               # B2C tenant setup
│   └── README.md
│
├── 07_microservices/
│   ├── frontend/
│   ├── backend/
│   ├── notification-service/          # New microservice
│   ├── infra/terraform/               # + API Management
│   └── README.md
│
└── 08_production/
    ├── frontend/                      # + Caching, error handling
    ├── backend/                       # + Monitoring, retry logic
    ├── notification-service/
    ├── infra/terraform/               # + Conditional Access, App Insights
    └── README.md
```

## Prerequisites

- **Azure Subscription** (free tier works for most blogs)
- **Microsoft Entra ID** tenant (comes with Azure subscription)
- **Node.js** 18+ and **npm/yarn/pnpm**
- **Python** 3.11+
- **Terraform** 1.5+
- **Azure CLI** (`az`) installed and configured
- **VS Code** (recommended)

## Quick Start

Each blog folder is self-contained. To run any blog's code:

```bash
# Frontend
cd azure_auth_series/01_basic_login/frontend
npm install
npm run dev

# Backend (Blog 2+)
cd azure_auth_series/02_protected_api/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Infrastructure (Blog 4+)
cd azure_auth_series/04_managed_identity/infra/terraform
terraform init
terraform plan
terraform apply
```

## Git Tags

Each blog milestone is tagged for easy navigation:

```bash
git tag blog/auth/01-basic-login       # Blog 1 complete
git tag blog/auth/02-protected-api     # Blog 2 complete
git tag blog/auth/03-rbac              # Blog 3 complete
# ... and so on
```

## License

MIT

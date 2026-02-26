# Implementation Plan — Azure Auth Blog Series

Detailed technical plan for each blog, including Azure configurations, code structure, and key implementation details.

---

## Blog 1: Basic Login

### Azure Setup
1. Go to **Entra ID → App registrations → New registration**
   - Name: `SecureTask-Frontend`
   - Supported account types: **Single tenant** (this org only)
   - Redirect URI: `http://localhost:3000` (SPA)
2. Note down: **Application (client) ID**, **Directory (tenant) ID**
3. Under **Authentication**:
   - Enable **ID tokens** (for OpenID Connect)
   - Add `http://localhost:3000` as redirect URI
4. Under **API permissions**:
   - `Microsoft Graph → User.Read` (delegated) — should be there by default

### Frontend Code Structure
```
01_basic_login/frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout with MsalProvider
│   │   ├── page.tsx                # Landing page
│   │   └── dashboard/
│   │       └── page.tsx            # Protected dashboard
│   ├── components/
│   │   ├── auth/
│   │   │   ├── login-button.tsx    # Sign in button
│   │   │   ├── logout-button.tsx   # Sign out button
│   │   │   ├── user-profile.tsx    # User avatar + info
│   │   │   └── msal-provider.tsx   # MSAL React provider wrapper
│   │   ├── ui/                     # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── navbar.tsx          # Top navigation
│   │   │   ├── sidebar.tsx         # Side navigation
│   │   │   └── footer.tsx
│   │   └── landing/
│   │       ├── hero.tsx            # Landing page hero
│   │       └── features.tsx        # Feature cards
│   ├── config/
│   │   └── auth-config.ts          # MSAL configuration
│   ├── hooks/
│   │   └── use-graph.ts            # Hook to call MS Graph
│   ├── lib/
│   │   ├── graph.ts                # MS Graph API calls
│   │   └── utils.ts                # shadcn/ui utils
│   └── types/
│       └── index.ts                # Type definitions
├── public/
├── tailwind.config.ts
├── next.config.js
├── package.json
├── tsconfig.json
└── .env.local.example              # Template for env vars
```

### Key Files Content

**auth-config.ts** — MSAL Configuration:
```typescript
export const msalConfig = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_AZURE_TENANT_ID}`,
    redirectUri: "http://localhost:3000",
    postLogoutRedirectUri: "http://localhost:3000",
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: ["User.Read"],
};

export const graphConfig = {
  graphMeEndpoint: "https://graph.microsoft.com/v1.0/me",
};
```

### What the User Sees
1. **Landing page** — Beautiful hero section with "Sign in with Microsoft" button
2. **After login** — Dashboard showing user profile (name, email, photo from Graph API)
3. **Nav bar** — Shows user avatar when logged in, sign-in button when not

---

## Blog 2: Protected API

### Azure Setup (additional)
1. Register a **second app**: `SecureTask-API`
   - No redirect URI needed (it's an API)
2. Under **Expose an API**:
   - Set Application ID URI: `api://<client-id>`
   - Add scope: `Tasks.Read`, `Tasks.ReadWrite`
3. In **SecureTask-Frontend** app registration:
   - Under **API permissions → Add permission → My APIs**
   - Select `SecureTask-API` → add `Tasks.Read`, `Tasks.ReadWrite`

### Backend Code Structure
```
02_protected_api/backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, CORS, routes
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── config.py               # Azure AD settings
│   │   ├── token_validator.py      # JWT decode + validate
│   │   └── dependencies.py         # FastAPI Depends() for auth
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── tasks.py                # Task CRUD endpoints
│   │   └── health.py               # Health check
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py                 # Task Pydantic models
│   └── services/
│       ├── __init__.py
│       └── task_service.py         # Business logic (in-memory store)
├── requirements.txt
├── .env.example
└── README.md
```

### Token Validation Flow
```
Frontend                    Backend                     Entra ID
   │                          │                            │
   │── acquireTokenSilent ──▶│                            │
   │   (scope: api://xxx)    │                            │
   │                          │                            │
   │── GET /api/tasks ──────▶│                            │
   │   Authorization: Bearer  │── Fetch JWKS ────────────▶│
   │                          │◀── Public keys ───────────│
   │                          │                            │
   │                          │── Validate JWT:            │
   │                          │   ✓ Signature              │
   │                          │   ✓ Issuer                 │
   │                          │   ✓ Audience               │
   │                          │   ✓ Expiry                 │
   │                          │                            │
   │◀── 200 OK + tasks ──────│                            │
```

---

## Blog 3: RBAC

### Azure Setup (additional)
1. In **SecureTask-API** app registration → **App roles**:
   - `Task.Admin` — "Can manage all tasks and users"
   - `Task.Editor` — "Can create and edit own tasks"
   - `Task.Reader` — "Can view tasks only"
2. In **Enterprise Applications** → Assign users/groups to roles

### Authorization Matrix
| Action | Admin | Editor | Reader |
|---|---|---|---|
| View all tasks | Yes | No (own only) | Yes (read-only) |
| Create task | Yes | Yes | No |
| Edit any task | Yes | No | No |
| Edit own task | Yes | Yes | No |
| Delete task | Yes | No | No |
| Manage users | Yes | No | No |

### Key Implementation
```python
# Backend role decorator
from functools import wraps

def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if not any(role in current_user.roles for role in allowed_roles):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

---

## Blog 4: Managed Identity

### Terraform Resources
```hcl
# Key resources to provision:
azurerm_resource_group
azurerm_service_plan
azurerm_linux_web_app              # Backend API
azurerm_static_web_app             # Frontend (or azurerm_linux_web_app)
azurerm_key_vault                  # Secrets
azurerm_key_vault_access_policy    # Managed Identity access
azurerm_storage_account            # Blob storage for files
azurerm_mssql_server               # Azure SQL
azurerm_mssql_database
azurerm_user_assigned_identity     # Optional: shared identity
```

### Secret-less Architecture
```
Before (Blog 2-3):                After (Blog 4):
┌─────────────┐                   ┌─────────────┐
│   Backend    │                   │   Backend    │
│             │                   │              │
│ DB_PASSWORD  │                   │  Managed ID  │──▶ Key Vault ──▶ DB password
│ API_KEY     │                   │  (no secrets │──▶ Storage   (RBAC)
│ STORAGE_KEY │                   │   in code)   │──▶ Azure SQL (AD auth)
└─────────────┘                   └──────────────┘
```

---

## Blog 5: Multi-Tenant

### Key Changes
- App registration: change to **Accounts in any organizational directory**
- Authority changes from `https://login.microsoftonline.com/{tenant-id}` to `https://login.microsoftonline.com/common`
- Add **admin consent endpoint**: `https://login.microsoftonline.com/common/adminconsent`
- Backend validates `tid` (tenant ID) claim and routes to tenant-specific data

### Data Isolation Strategy
```
┌───────────────────────────────────┐
│           Azure SQL               │
│                                   │
│  ┌─────────┐  ┌─────────┐       │
│  │Tenant A  │  │Tenant B  │  ... │   ← Row-level security
│  │ tasks    │  │ tasks    │       │     filtered by tenant_id
│  └─────────┘  └─────────┘       │
└───────────────────────────────────┘
```

---

## Blog 6: Azure AD B2C (SecureShop)

### B2C Tenant Setup
1. Create a new **Azure AD B2C tenant** (separate from Entra ID)
2. Register app in B2C tenant
3. Create **User flows**:
   - Sign up and sign in (B2C_1_signupsignin)
   - Password reset (B2C_1_passwordreset)
   - Profile editing (B2C_1_profileediting)
4. Add **Identity providers**: Google, GitHub
5. **Customize UI** with company branding

### How B2C Differs from Entra ID
| Feature | Entra ID (Blog 1-5) | Azure AD B2C (Blog 6) |
|---|---|---|
| Target users | Employees / internal | Customers / external |
| Sign-up | Admin creates accounts | Self-service |
| Social login | No (org accounts only) | Yes (Google, FB, GitHub) |
| Customization | Limited | Full UI customization |
| Pricing | Included with Azure | Pay per authentication |

---

## Blog 7: Microservices

### New Service: Notification Service
```
07_microservices/notification-service/
├── app/
│   ├── main.py
│   ├── auth/
│   │   ├── config.py
│   │   └── client_credentials.py   # Validate service tokens
│   ├── routes/
│   │   └── notifications.py
│   └── services/
│       └── email_service.py
├── requirements.txt
└── Dockerfile
```

### Service-to-Service Flow
```
Backend API                          Notification Service
     │                                       │
     │── acquireTokenByClientCredential ──▶ Entra ID
     │◀── Access token (app permission) ──── │
     │                                       │
     │── POST /notify ─────────────────────▶│
     │   Authorization: Bearer <token>       │── Validate token
     │                                       │   (app role, not user)
     │◀── 202 Accepted ─────────────────────│
```

### API Management
```hcl
# Terraform resources
azurerm_api_management
azurerm_api_management_api
azurerm_api_management_api_policy   # JWT validation policy
```

---

## Blog 8: Production Readiness

### Checklist
- [ ] Conditional Access policies (require MFA for admin role)
- [ ] Token caching with Redis (backend)
- [ ] MSAL token cache serialization (frontend)
- [ ] Retry logic with exponential backoff for token acquisition
- [ ] Application Insights integration
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging for auth events
- [ ] Secret rotation strategy via Key Vault
- [ ] Health checks and readiness probes

### Monitoring
```hcl
# Terraform resources
azurerm_application_insights
azurerm_monitor_diagnostic_setting
azurerm_log_analytics_workspace
```

---

## Dependencies Between Blogs

```
Blog 1 (Login)
  └──▶ Blog 2 (API) ── extends frontend, adds backend
         └──▶ Blog 3 (RBAC) ── extends both
                └──▶ Blog 4 (Managed Identity) ── adds infra
                       └──▶ Blog 5 (Multi-tenant) ── extends all
                              └──▶ Blog 7 (Microservices) ── adds service
                                     └──▶ Blog 8 (Production) ── hardens all

Blog 6 (B2C) ── independent, can be done after Blog 2
```

## Estimated Complexity per Blog

| Blog | Frontend | Backend | Infra | Azure Config | Overall |
|---|---|---|---|---|---|
| 01 | Medium | None | None | Easy | Easy |
| 02 | Low | Medium | None | Medium | Medium |
| 03 | Medium | Medium | None | Medium | Medium |
| 04 | Low | Medium | High | Medium | Medium-Hard |
| 05 | Medium | High | Medium | High | Hard |
| 06 | Medium | Medium | Medium | High | Medium-Hard |
| 07 | Low | High | High | High | Hard |
| 08 | Medium | High | Medium | High | Hard |

# Blog 4: Deploy to Azure with Managed Identity + Key Vault

Deploy the RBAC app from Blog 3 to Azure, replacing `.env` files with **Azure Key Vault** + **Managed Identity** for secure config management.

## Architecture

```
┌─────────────────┐     HTTPS      ┌─────────────────────────────┐
│  Static Web App  │ ──────────────▶│  Container Apps (Backend)   │
│  (Next.js SPA)   │                │  FastAPI + System MI        │
└─────────────────┘                └──────────┬──────────────────┘
                                              │ DefaultAzureCredential
                                              ▼
                                   ┌─────────────────────┐
                                   │  Azure Key Vault     │
                                   │  • azure-tenant-id   │
                                   │  • azure-api-client-id│
                                   └─────────────────────┘
```

| Component | Service | SKU / Tier |
|---|---|---|
| Backend | Azure Container Apps | Consumption (scale 0-1) |
| Frontend | Azure Static Web Apps | Free |
| Secrets | Azure Key Vault | Standard |
| Container images | Azure Container Registry | Basic |
| **Estimated cost** | | **~$5/mo** |

## Key Concept: `config.py`

```python
if KEY_VAULT_URL:
    # In Azure: Managed Identity → Key Vault
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    TENANT_ID = client.get_secret("azure-tenant-id").value
else:
    # Local dev: .env file (same as Blog 3)
    TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
```

## Prerequisites

- Azure CLI (`az`) logged in
- Terraform >= 1.5
- Docker
- Node.js >= 18 + npm

## Quick Start

### 1. App Registrations (same as Blog 3)

```bash
./setup.sh
```

Creates API + SPA app registrations, test users, and writes `backend/.env` + `frontend/.env.local`.

### 2. Verify Locally (optional)

```bash
# Terminal 1
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# Terminal 2
cd frontend && npm install && npm run dev
```

### 3. Provision Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set globally unique names for key_vault_name and acr_name

terraform init
terraform plan    # Should show ~8 resources
terraform apply
```

### 4. Deploy

```bash
./deploy.sh
```

This script:
1. Seeds Key Vault with secrets from `backend/.env`
2. Builds and pushes the backend Docker image to ACR
3. Updates the Container App
4. Builds the frontend with production URLs and deploys to Static Web App
5. Adds the SWA URL as a redirect URI

### 5. Verify

```bash
# Health check
curl $(cd infra && terraform output -raw backend_url)/health

# Open frontend
open $(cd infra && terraform output -raw frontend_url)

# View Container App logs
az containerapp logs show \
  -n $(cd infra && terraform output -raw backend_app_name) \
  -g $(cd infra && terraform output -raw resource_group_name) \
  --follow
```

Sign in as Admin/Editor/Reader — same RBAC behavior as Blog 3, now running in Azure.

## Cleanup

```bash
./cleanup.sh
```

Destroys all Terraform infrastructure, deletes app registrations, and removes test users.

## File Structure

```
04_managed_identity/
├── README.md
├── setup.sh              # Azure AD app registrations
├── deploy.sh             # Build, push, deploy orchestration
├── cleanup.sh            # Tear down everything
├── backend/
│   ├── main.py           # FastAPI (Blog 3 + /health + configurable CORS)
│   ├── auth.py           # JWT validation (identical to Blog 3)
│   ├── config.py         # Key Vault via Managed Identity, .env fallback
│   ├── requirements.txt  # + azure-identity, azure-keyvault-secrets
│   ├── Dockerfile
│   └── .env.example
├── frontend/             # Blog 3 frontend + static export
│   ├── next.config.mjs   # + output: "export" for SWA
│   ├── staticwebapp.config.json  # SPA fallback routing
│   └── ...
└── infra/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars.example
    └── modules/
        ├── resource_group/
        ├── key_vault/
        ├── container_registry/
        ├── container_apps/
        └── static_web_app/
```

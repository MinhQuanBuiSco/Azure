# Cloud Infrastructure

Terraform configuration for deploying the LLM Security Gateway to Azure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Resource Group                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Container Apps Environment                      ││
│  │  ┌───────────────────┐  ┌───────────────────┐              ││
│  │  │   Backend App     │  │   Frontend App    │              ││
│  │  │   (FastAPI)       │  │   (Next.js)       │              ││
│  │  └───────────────────┘  └───────────────────┘              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Azure OpenAI   │  │  Redis Cache    │  │   Cosmos DB     │ │
│  │  (GPT-4o)       │  │  (Rate Limit)   │  │  (Audit Logs)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Content Safety  │  │   Key Vault     │  │  Log Analytics  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Azure CLI installed and authenticated
- Terraform >= 1.5.0
- Azure subscription with required resource providers enabled

## Modules

| Module | Description |
|--------|-------------|
| `monitoring` | Log Analytics + Application Insights |
| `key_vault` | Azure Key Vault for secrets |
| `redis_cache` | Azure Cache for Redis |
| `cosmos_db` | Azure Cosmos DB (serverless) |
| `ai_foundry` | Azure OpenAI + Content Safety |
| `container_apps` | Container Apps for backend & frontend |

## Usage

### Development Environment

```bash
cd environments/dev
terraform init
terraform plan
terraform apply
```

### Production Environment

```bash
cd environments/prod
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Outputs

After deployment, you'll get:
- `backend_url` - Backend API URL
- `frontend_url` - Frontend dashboard URL
- `ai_foundry_endpoint` - Azure OpenAI endpoint
- `key_vault_name` - Key Vault for secrets

## Cost Optimization

The dev environment uses:
- Cosmos DB Serverless (pay-per-request)
- Basic Redis Cache (smallest tier)
- Container Apps consumption plan
- Standard OpenAI capacity

## Security

- All secrets stored in Azure Key Vault
- Redis and Cosmos DB use private endpoints (optional)
- Container Apps use managed identity
- TLS enforced on all connections

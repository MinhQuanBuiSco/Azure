# Azure Infrastructure - Terraform

Terraform infrastructure as code for the RAG Application with entity extraction and multi-strategy search.

## Architecture

This Terraform configuration deploys the following Azure resources:

- **Resource Group**: Central container for all resources
- **Storage Account**: Blob storage for PDF files
- **Redis Cache**: Semantic caching (Standard C1)
- **Azure AI Search**: Vector search + BM25 + entity filtering (Standard S1)
- **Azure OpenAI**: GPT-4o-mini + text-embedding-3-small
- **Container Registry**: Store Docker images
- **Container Apps**: Backend FastAPI application (3-50 replicas)
- **Static Web App**: React frontend
- **Application Insights**: Monitoring and logging

## Prerequisites

1. **Azure CLI** installed and authenticated
   ```bash
   az login
   az account set --subscription <subscription-id>
   ```

2. **Terraform** >= 1.5.0 installed
   ```bash
   terraform version
   ```

3. **Docker** for building images
   ```bash
   docker --version
   ```

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update the following **globally unique** names:
- `storage_account_name` (lowercase, alphanumeric, no hyphens)
- `redis_cache_name`
- `search_service_name`
- `openai_name`
- `acr_name` (alphanumeric only)
- `static_web_app_name`

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan
```

Review the planned changes carefully.

### 4. Apply Configuration

```bash
terraform apply tfplan
```

This will take **15-20 minutes** to provision all resources.

### 5. Create AI Search Index

After Terraform completes, create the search index:

```bash
# Get outputs
SEARCH_NAME=$(terraform output -raw search_endpoint | cut -d'/' -f3 | cut -d'.' -f1)
SEARCH_KEY=$(terraform output -raw search_primary_key)

# Create index
cd modules/ai_search
chmod +x create_index.sh
SEARCH_SERVICE_NAME=$SEARCH_NAME SEARCH_ADMIN_KEY=$SEARCH_KEY ./create_index.sh
```

### 6. Build and Push Docker Images

```bash
# Get ACR details
ACR_SERVER=$(terraform output -raw acr_login_server)
ACR_USERNAME=$(terraform output -raw acr_admin_username)
ACR_PASSWORD=$(terraform output -raw acr_admin_password)

# Login to ACR
docker login $ACR_SERVER -u $ACR_USERNAME -p $ACR_PASSWORD

# Build and push backend
cd ../backend
docker build -t $ACR_SERVER/rag-backend:latest .
docker push $ACR_SERVER/rag-backend:latest

# Build and push frontend (optional if using Static Web App deployment)
cd ../frontend
docker build -t $ACR_SERVER/rag-frontend:latest .
docker push $ACR_SERVER/rag-frontend:latest
```

### 7. Deploy Frontend to Static Web App

```bash
# Get deployment token
DEPLOYMENT_TOKEN=$(terraform output -raw frontend_deployment_token)

# Deploy using Azure Static Web Apps CLI
cd ../frontend
npm run build

# Deploy (requires @azure/static-web-apps-cli)
swa deploy ./dist --deployment-token $DEPLOYMENT_TOKEN
```

### 8. Verify Deployment

```bash
# Get URLs
terraform output backend_url
terraform output frontend_url

# Test backend health
curl $(terraform output -raw backend_url)/health

# Open frontend
open https://$(terraform output -raw frontend_url)
```

## Outputs

After successful deployment, Terraform provides these outputs:

```bash
# View all outputs
terraform output

# View specific output
terraform output backend_url
terraform output -raw search_primary_key  # Get sensitive value
```

### Important Outputs

- `backend_url`: Backend API endpoint
- `frontend_url`: Frontend application URL
- `acr_login_server`: Container registry for Docker images
- `backend_env_config`: Environment variables for backend (sensitive)
- `backend_secrets`: Secret values (sensitive)

## Environment Configuration

### Backend .env File

Generate backend `.env` file from Terraform outputs:

```bash
cd ../backend

cat > .env << EOF
# Generated from Terraform outputs
AZURE_STORAGE_ACCOUNT_NAME=$(terraform -chdir=../azure_infra output -json backend_env_config | jq -r '.AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_CONNECTION_STRING=$(terraform -chdir=../azure_infra output -json backend_secrets | jq -r '.AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME=$(terraform -chdir=../azure_infra output -raw blob_container_name)
AZURE_SEARCH_ENDPOINT=$(terraform -chdir=../azure_infra output -raw search_endpoint)
AZURE_SEARCH_API_KEY=$(terraform -chdir=../azure_infra output -raw search_primary_key)
AZURE_SEARCH_INDEX_NAME=$(terraform -chdir=../azure_infra output -raw search_index_name)
AZURE_OPENAI_ENDPOINT=$(terraform -chdir=../azure_infra output -raw openai_endpoint)
AZURE_OPENAI_API_KEY=$(terraform -chdir=../azure_infra output -raw openai_primary_key)
AZURE_OPENAI_CHAT_DEPLOYMENT=$(terraform -chdir=../azure_infra output -raw openai_chat_deployment)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$(terraform -chdir=../azure_infra output -raw openai_embedding_deployment)
REDIS_HOST=$(terraform -chdir=../azure_infra output -raw redis_hostname)
REDIS_PORT=6380
REDIS_PASSWORD=$(terraform -chdir=../azure_infra output -raw redis_primary_key)
REDIS_SSL=true
EOF

echo "Backend .env file created!"
```

## Cost Optimization

### Estimated Monthly Cost (~$1,150)

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| Container Apps | 1vCPU, 2GB | $530 |
| Redis Cache | Standard C1 | $75 |
| Azure OpenAI | GPT-4o-mini | $165 |
| AI Search | Standard S1 | $245 |
| Storage | Standard LRS | $5 |
| Static Web App | Standard | $9 |
| Application Insights | Pay-as-you-go | $20 |
| Container Registry | Standard | $20 |
| **Total** | | **~$1,069** |

### Cost Savings Tips

1. **Use Reserved Instances**
   - 1-year commitment: 30-40% discount on Redis, AI Search

2. **Adjust Scaling**
   - Lower `backend_min_replicas` to 1-2 for dev/test
   - Reduce Redis to Basic tier for non-production

3. **Use Free Tier for Development**
   - Static Web App: Free tier available
   - AI Search: Free tier (limited)

## Cleanup

### Option 1: Automated Cleanup Script (Recommended)

```bash
# Preview what would be deleted (safe - doesn't delete anything)
./cleanup-preview.sh

# Delete all resources (requires confirmation)
./cleanup.sh
```

The script will:
- Ask for double confirmation before deleting
- Destroy all Azure resources
- Clean up local state files
- Remove generated backend .env file

### Option 2: Manual Cleanup

```bash
terraform destroy
```

**Warning**: This will permanently delete all resources and data!

**What gets deleted:**
- All Azure resources (~$1,154/month in costs will stop)
- All data in Storage, Redis, and AI Search
- Docker images in Container Registry
- Terraform state files (local)

## Troubleshooting

### Container App Not Starting

Check logs:
```bash
az containerapp logs show \
  --name $(terraform output -raw backend_app_name) \
  --resource-group $(terraform output -raw resource_group_name) \
  --follow
```

### AI Search Index Issues

Verify index:
```bash
SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
SEARCH_KEY=$(terraform output -raw search_primary_key)

curl "$SEARCH_ENDPOINT/indexes/rag-index?api-version=2023-11-01" \
  -H "api-key: $SEARCH_KEY"
```

### OpenAI Deployment Errors

Check deployment status:
```bash
az cognitiveservices account deployment list \
  --name $(terraform output -raw openai_name) \
  --resource-group $(terraform output -raw resource_group_name)
```

## Security Best Practices

1. **Use Managed Identities** (recommended over access keys)
2. **Enable Private Endpoints** for production
3. **Store tfstate remotely** in Azure Storage with encryption
4. **Use Azure Key Vault** for secrets management
5. **Enable diagnostic logging** for all resources
6. **Implement network security groups**
7. **Use Azure Front Door WAF** for DDoS protection

## Remote State (Production)

For production, use remote state storage:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatexxxxx"
    container_name       = "tfstate"
    key                  = "rag-app.terraform.tfstate"
  }
}
```

Create state storage:
```bash
az group create --name terraform-state-rg --location eastus2
az storage account create --name tfstatexxxxx --resource-group terraform-state-rg --location eastus2 --sku Standard_LRS
az storage container create --name tfstate --account-name tfstatexxxxx
```

## Module Documentation

Each module has its own README:
- `modules/resource_group/` - Resource group
- `modules/storage/` - Blob storage
- `modules/redis/` - Redis cache
- `modules/ai_search/` - Azure AI Search with index schema
- `modules/openai/` - Azure OpenAI with model deployments
- `modules/container_registry/` - ACR
- `modules/container_apps/` - Container Apps environment and backend
- `modules/static_web_app/` - Static Web App for frontend
- `modules/app_insights/` - Application Insights and Log Analytics

## Support

- Azure Documentation: https://docs.microsoft.com/azure
- Terraform Azure Provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- Issues: Open an issue on GitHub

## License

MIT License

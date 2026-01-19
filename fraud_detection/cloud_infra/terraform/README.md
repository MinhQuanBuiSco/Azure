# Terraform Infrastructure

This directory contains Terraform configurations for deploying the fraud detection system to Azure.

## Architecture

- **AKS Cluster**: Kubernetes cluster with B2s nodes (cost-optimized)
- **ACR**: Azure Container Registry (Basic SKU)
- **PostgreSQL**: Flexible Server with B1ms SKU
- **Redis**: Azure Cache for Redis (Basic C0)

## Cost Optimization

This configuration is optimized for development/portfolio use:
- **AKS**: Standard_B2s nodes (2 vCPU, 4 GB RAM) - ~$35/month per node
- **ACR**: Basic SKU - ~$5/month
- **PostgreSQL**: B_Standard_B1ms (1 vCPU, 2 GB RAM) - ~$16/month
- **Redis**: Basic C0 (250 MB) - ~$16/month

**Estimated monthly cost: ~$107 for 2-node cluster**

## Prerequisites

1. **Azure CLI**: Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Terraform**: Install from https://www.terraform.io/downloads
3. **Azure Subscription**: Active Azure subscription

## Setup

### 1. Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### 2. Create terraform.tfvars

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:
- Update `acr_name` to be globally unique (alphanumeric only)
- Set a strong `postgres_admin_password`

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan Infrastructure

```bash
terraform plan
```

### 5. Deploy Infrastructure

```bash
terraform apply
```

This will take 10-15 minutes to complete.

## Post-Deployment

### 1. Configure kubectl

```bash
az aks get-credentials --resource-group fraud-detection-dev-rg --name fraud-detection-aks-dev
kubectl get nodes
```

### 2. Get ACR Credentials

```bash
terraform output -raw acr_admin_username
terraform output -raw acr_admin_password
```

### 3. Login to ACR

```bash
ACR_NAME=$(terraform output -raw acr_name)
az acr login --name $ACR_NAME
```

### 4. Get Database Connection Strings

```bash
# PostgreSQL
terraform output postgres_fqdn
terraform output database_name
terraform output -raw postgres_admin_username

# Redis
terraform output redis_hostname
terraform output redis_port
terraform output -raw redis_connection_string
```

## Destroying Infrastructure

**Warning**: This will delete all resources.

```bash
terraform destroy
```

## Remote State (Optional)

For team collaboration, use Azure Storage for remote state:

1. Create a storage account:

```bash
az group create --name terraform-state-rg --location eastus
az storage account create --name fraudtfstate --resource-group terraform-state-rg --location eastus --sku Standard_LRS
az storage container create --name tfstate --account-name fraudtfstate
```

2. Uncomment the backend configuration in `provider.tf`

3. Reinitialize:

```bash
terraform init -migrate-state
```

## Module Structure

```
terraform/
├── modules/              # Reusable modules
│   ├── aks/             # AKS cluster
│   ├── acr/             # Container Registry
│   └── databases/       # PostgreSQL + Redis
└── environments/        # Environment-specific configs
    └── dev/            # Development environment
```

## Variables

Key variables in `variables.tf`:

- `location`: Azure region (default: eastus)
- `resource_group_name`: Resource group name
- `aks_cluster_name`: AKS cluster name
- `acr_name`: Container registry name (must be unique)
- `postgres_admin_password`: PostgreSQL password (sensitive)

## Outputs

After deployment, Terraform outputs:

- AKS cluster name and kubeconfig
- ACR login server and credentials
- PostgreSQL FQDN and credentials
- Redis hostname and connection string

## Troubleshooting

### ACR name already taken

Update `acr_name` in `terraform.tfvars` to a unique value.

### AKS quota exceeded

Check your subscription quota:
```bash
az vm list-usage --location eastus --output table
```

### PostgreSQL connection issues

Ensure firewall rules allow your IP:
```bash
az postgres flexible-server firewall-rule create \
  --resource-group fraud-detection-dev-rg \
  --name fraud-detection-postgres-dev \
  --rule-name allow-my-ip \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

## Security Notes

- Never commit `terraform.tfvars` to git (it contains secrets)
- Use Azure Key Vault for production secrets
- Enable Azure Policy for governance
- Use managed identities instead of service principals

# GitHub Actions CI/CD Pipelines

This directory contains GitHub Actions workflows for automated testing, building, and deployment of the fraud detection system.

## Workflows

### 1. Backend CI/CD (`backend-cicd.yml`)

Automated testing and deployment for the FastAPI backend.

**Triggers:**
- Push to `main` or `develop` branches (backend changes)
- Pull requests to `main` or `develop` branches (backend changes)

**Jobs:**
- **Test**: Runs linter, tests, and uploads coverage
- **Build and Push**: Builds Docker image and pushes to ACR
- **Deploy Dev**: Deploys to development environment (on `develop` branch)
- **Deploy Prod**: Deploys to production environment (on `main` branch)

### 2. Frontend CI/CD (`frontend-cicd.yml`)

Automated testing and deployment for the React frontend.

**Triggers:**
- Push to `main` or `develop` branches (frontend changes)
- Pull requests to `main` or `develop` branches (frontend changes)

**Jobs:**
- **Test**: Runs linter and builds application
- **Build and Push**: Builds Docker image and pushes to ACR
- **Deploy Dev**: Deploys to development environment (on `develop` branch)
- **Deploy Prod**: Deploys to production environment (on `main` branch)

### 3. Terraform CI/CD (`terraform.yml`)

Infrastructure as Code deployment.

**Triggers:**
- Push to `main` branch (terraform changes)
- Pull requests to `main` branch (terraform changes)

**Jobs:**
- **Validate**: Format check and validation
- **Plan**: Creates terraform plan (on PR)
- **Apply**: Applies infrastructure changes (on push to `main`)

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### Azure Credentials

```bash
# Create Azure Service Principal
az ad sp create-for-rbac --name "github-actions-fraud-detection" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Add output as AZURE_CREDENTIALS secret
```

**Required Secrets:**
- `AZURE_CREDENTIALS`: Azure service principal credentials (JSON format)
- `ARM_CLIENT_ID`: Azure AD service principal client ID
- `ARM_CLIENT_SECRET`: Azure AD service principal client secret
- `ARM_SUBSCRIPTION_ID`: Azure subscription ID
- `ARM_TENANT_ID`: Azure AD tenant ID

### Application Secrets

- `POSTGRES_ADMIN_PASSWORD`: PostgreSQL administrator password

### Optional Secrets

- `CODECOV_TOKEN`: For code coverage reporting (if using Codecov)

## Setup Instructions

### 1. Create Service Principal

```bash
# Login to Azure
az login

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-fraud-detection" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth > azure-credentials.json

# Extract values
CLIENT_ID=$(jq -r '.clientId' azure-credentials.json)
CLIENT_SECRET=$(jq -r '.clientSecret' azure-credentials.json)
TENANT_ID=$(jq -r '.tenantId' azure-credentials.json)
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret:

1. **AZURE_CREDENTIALS**: Paste entire contents of `azure-credentials.json`
2. **ARM_CLIENT_ID**: Paste `$CLIENT_ID`
3. **ARM_CLIENT_SECRET**: Paste `$CLIENT_SECRET`
4. **ARM_SUBSCRIPTION_ID**: Paste `$SUBSCRIPTION_ID`
5. **ARM_TENANT_ID**: Paste `$TENANT_ID`
6. **POSTGRES_ADMIN_PASSWORD**: Create a strong password

### 3. Configure Environments

Create protected environments for deployment gates:

1. Go to Settings → Environments
2. Create `development` environment
3. Create `production` environment (add required reviewers)
4. Create `infrastructure` environment (add required reviewers)

### 4. Update Workflow Variables

Edit the workflows to match your configuration:

**Backend/Frontend workflows:**
```yaml
env:
  ACR_NAME: your-acr-name
  AKS_CLUSTER_NAME: your-aks-cluster
  AKS_RESOURCE_GROUP: your-resource-group
  NAMESPACE: fraud-detection
```

**Terraform workflow:**
```yaml
env:
  WORKING_DIR: './cloud_infra/terraform/environments/dev'
```

## Deployment Flow

### Development Environment

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Push to GitHub: `git push origin feature/my-feature`
4. Create pull request to `develop`
5. CI tests run automatically
6. Merge to `develop` → automatic deployment to dev environment

### Production Environment

1. Create pull request from `develop` to `main`
2. CI tests run automatically
3. Review and approve
4. Merge to `main` → automatic deployment to production

### Infrastructure Changes

1. Modify terraform files
2. Create pull request to `main`
3. Terraform plan runs and comments on PR
4. Review plan carefully
5. Merge to `main` → terraform apply runs with approval gate

## Monitoring Deployments

### View Workflow Runs

Go to Actions tab in GitHub to see all workflow runs.

### Check Deployment Status

```bash
# Get AKS credentials
az aks get-credentials --resource-group <rg-name> --name <aks-name>

# Check pod status
kubectl get pods -n fraud-detection

# Check deployment history
helm history fraud-detection-backend -n fraud-detection
helm history fraud-detection-frontend -n fraud-detection
```

### Rollback Deployment

```bash
# Rollback backend
helm rollback fraud-detection-backend -n fraud-detection

# Rollback frontend
helm rollback fraud-detection-frontend -n fraud-detection
```

## Best Practices

1. **Always use pull requests** - Never push directly to `main` or `develop`
2. **Review terraform plans** - Carefully review infrastructure changes
3. **Test locally first** - Use Docker Compose for local testing
4. **Tag releases** - Use semantic versioning for production releases
5. **Monitor deployments** - Check pod logs after deployment
6. **Use feature flags** - For gradual feature rollout
7. **Rotate secrets** - Regularly rotate service principal credentials

## Troubleshooting

### Build Failures

**Issue**: Docker build fails
```bash
# Check Dockerfile syntax
docker build -t test-build ./backend
```

**Issue**: Tests fail
```bash
# Run tests locally
cd backend
uv run pytest tests/ -v
```

### Deployment Failures

**Issue**: Image pull errors
```bash
# Verify ACR permissions
az aks update -n <aks-name> -g <rg-name> --attach-acr <acr-name>
```

**Issue**: Helm deployment fails
```bash
# Debug helm release
helm status fraud-detection-backend -n fraud-detection
helm get values fraud-detection-backend -n fraud-detection
```

### Authentication Errors

**Issue**: Azure credentials expired
```bash
# Recreate service principal
az ad sp create-for-rbac --name "github-actions-fraud-detection" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [Helm Documentation](https://helm.sh/docs/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

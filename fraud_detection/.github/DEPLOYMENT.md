# Deployment Guide

This guide covers deploying the Fraud Detection System to Azure using GitHub Actions CI/CD.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    AKS Cluster                           │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │  Frontend   │  │  Backend    │  │  Ingress    │      │    │
│  │  │  (nginx)    │  │  (FastAPI)  │  │  Controller │      │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  PostgreSQL   │  │    Redis      │  │     ACR       │        │
│  │  Flexible     │  │    Cache      │  │  (Images)     │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Cost Comparison

| Resource | Dev (~$107/mo) | Prod (~$450/mo) |
|----------|----------------|-----------------|
| AKS Nodes | 2x B2s | 3x D2s_v3 |
| PostgreSQL | B1ms (1 vCPU) | D2s_v3 (2 vCPU, HA) |
| Redis | Basic C0 (250MB) | Standard C1 (1GB) |
| ACR | Basic | Standard |
| Features | - | HA, Backups, Monitoring |

## Prerequisites

### 1. Azure CLI & Terraform

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Login to Azure
az login
az account set --subscription "your-subscription-id"
```

### 2. Create Service Principal for CI/CD

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "fraud-detection-cicd" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Save the JSON output - you'll need it for GitHub secrets
```

### 3. GitHub Secrets

Configure these secrets in your GitHub repository:

#### Common Secrets
| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON (dev) |
| `AZURE_CREDENTIALS_PROD` | Service principal JSON (prod) |
| `ARM_CLIENT_ID` | SP client ID |
| `ARM_CLIENT_SECRET` | SP client secret |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID |
| `ARM_TENANT_ID` | Azure tenant ID |
| `AZURE_AI_ENDPOINT` | Azure AI Foundry endpoint |
| `AZURE_AI_KEY` | Azure AI Foundry API key |
| `AZURE_AI_MODEL_NAME` | Model name (e.g., claude-3-5-sonnet) |

#### Development Secrets
| Secret | Description |
|--------|-------------|
| `DEV_POSTGRES_PASSWORD` | PostgreSQL password |
| `DEV_API_URL` | Backend API URL |
| `DEV_WS_URL` | WebSocket URL |
| `DEV_BACKEND_HOST` | Backend ingress host |
| `DEV_FRONTEND_HOST` | Frontend ingress host |

#### Production Secrets
| Secret | Description |
|--------|-------------|
| `PROD_POSTGRES_PASSWORD` | PostgreSQL password |
| `PROD_DATABASE_URL` | Full PostgreSQL connection string |
| `PROD_REDIS_HOST` | Redis hostname |
| `PROD_REDIS_PORT` | Redis port (6380) |
| `PROD_REDIS_PASSWORD` | Redis access key |
| `PROD_API_URL` | Backend API URL |
| `PROD_WS_URL` | WebSocket URL |
| `PROD_BACKEND_HOST` | Backend ingress host |
| `PROD_FRONTEND_HOST` | Frontend ingress host |

## Deployment Steps

### Step 1: Deploy Infrastructure

```bash
# Option A: Using GitHub Actions (Recommended)
# Go to Actions > Terraform > Run workflow
# Select environment (dev/prod) and action (plan/apply)

# Option B: Manual deployment
cd cloud_infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

### Step 2: Configure kubectl

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group fraud-detection-dev-rg \
  --name fraud-detection-aks-dev

# Verify connection
kubectl get nodes
```

### Step 3: Install Required Components

```bash
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install cert-manager (for TLS)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Step 4: Create Secrets

```bash
# Get values from Terraform output
cd cloud_infra/terraform/environments/dev
POSTGRES_HOST=$(terraform output -raw postgres_fqdn)
REDIS_HOST=$(terraform output -raw redis_hostname)
REDIS_KEY=$(terraform output -raw redis_connection_string | grep -oP 'password=\K[^,]+')

# Create Kubernetes secret
kubectl create namespace fraud-detection

kubectl create secret generic backend-secrets \
  --namespace fraud-detection \
  --from-literal=database-url="postgresql://fraudadmin:YOUR_PASSWORD@${POSTGRES_HOST}:5432/fraud_detection?sslmode=require" \
  --from-literal=redis-host="${REDIS_HOST}" \
  --from-literal=redis-port="6380" \
  --from-literal=redis-password="${REDIS_KEY}" \
  --from-literal=anthropic-api-key="YOUR_ANTHROPIC_KEY"
```

### Step 5: Deploy Application

```bash
# Option A: Using GitHub Actions (Recommended)
# Push to develop branch for dev deployment
git push origin develop

# Create tag for production deployment
git tag v1.0.0
git push origin v1.0.0

# Option B: Manual deployment
cd cloud_infra/helm

# Deploy backend
helm install fraud-detection-backend ./backend \
  --namespace fraud-detection \
  --set image.repository=yourregistry.azurecr.io/fraud-detection-backend \
  --set image.tag=latest

# Deploy frontend
helm install fraud-detection-frontend ./frontend \
  --namespace fraud-detection \
  --set image.repository=yourregistry.azurecr.io/fraud-detection-frontend \
  --set image.tag=latest
```

## CI/CD Workflows

### Workflow Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | PR, push to main/develop | Lint, test, build |
| `cd-dev.yml` | Push to develop | Deploy to dev |
| `cd-prod.yml` | Tag v* | Deploy to production |
| `terraform.yml` | Manual, path changes | Infrastructure changes |

### Branching Strategy

```
main ────────────────────────────────► (stable, releases)
         │
         └── develop ─────────────────► (integration, dev deploys)
                  │
                  ├── feature/xxx ────► (feature development)
                  └── bugfix/xxx ─────► (bug fixes)
```

### Release Process

1. Merge features to `develop` → Auto-deploys to dev
2. Test on dev environment
3. Merge `develop` to `main`
4. Create release tag: `git tag v1.2.3 && git push origin v1.2.3`
5. Production deployment runs automatically

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -f -l app.kubernetes.io/name=fraud-detection-backend -n fraud-detection

# Specific pod
kubectl logs -f <pod-name> -n fraud-detection
```

### Check Status

```bash
# Pods
kubectl get pods -n fraud-detection -w

# Services
kubectl get svc -n fraud-detection

# Ingress
kubectl get ingress -n fraud-detection

# HPA
kubectl get hpa -n fraud-detection
```

### Debugging

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n fraud-detection

# Get shell access
kubectl exec -it <pod-name> -n fraud-detection -- /bin/sh

# Port forward for local testing
kubectl port-forward svc/fraud-detection-backend 8000:8000 -n fraud-detection
```

## Rollback

### Using Helm

```bash
# View history
helm history fraud-detection-backend -n fraud-detection

# Rollback to previous
helm rollback fraud-detection-backend -n fraud-detection

# Rollback to specific revision
helm rollback fraud-detection-backend 2 -n fraud-detection
```

### Using kubectl

```bash
# Rollback deployment
kubectl rollout undo deployment/fraud-detection-backend -n fraud-detection

# Check rollout status
kubectl rollout status deployment/fraud-detection-backend -n fraud-detection
```

## Cleanup

### Development Environment

```bash
# Using GitHub Actions
# Go to Actions > Terraform > Run workflow
# Select: environment=dev, action=destroy

# Manual
cd cloud_infra/terraform/environments/dev
terraform destroy
```

### Production Environment

```bash
# Using GitHub Actions
# Go to Actions > Terraform > Run workflow
# Select: environment=prod, action=destroy

# Manual (requires approval)
cd cloud_infra/terraform/environments/prod
terraform destroy
```

## Troubleshooting

### Common Issues

#### Image Pull Errors
```bash
# Attach ACR to AKS
az aks update -n fraud-detection-aks-dev -g fraud-detection-dev-rg --attach-acr yourregistry
```

#### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs <pod-name> -n fraud-detection --previous

# Check events
kubectl describe pod <pod-name> -n fraud-detection
```

#### Database Connection Failed
```bash
# Verify secret
kubectl get secret backend-secrets -n fraud-detection -o yaml

# Test connection from pod
kubectl exec -it <pod-name> -n fraud-detection -- \
  python -c "import asyncpg; print(asyncpg.connect('...'))"
```

#### Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Check ingress status
kubectl describe ingress -n fraud-detection
```

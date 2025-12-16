# Deployment Guide - Azure Chatbot

Complete step-by-step guide to deploy the chatbot application on Azure using Terraform, Docker, and Kubernetes.

## Prerequisites

Before starting, make sure you have completed the setup in `SETUP.md`:

- ✅ All tools installed (Azure CLI, Terraform, Docker, kubectl, uv, Node.js)
- ✅ Azure account configured and logged in
- ✅ Service principal created for Terraform
- ✅ **Azure OpenAI access approved** (critical!)
- ✅ Environment variables exported

---

## Phase 1: Infrastructure Deployment with Terraform

### Step 1: Configure Terraform Variables

```bash
cd cloud_infra

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and customize:
# - ACR name (must be globally unique!)
# - OpenAI account name (must be globally unique!)
# - Other settings as needed
```

**Important**: Change these values to be unique:
- `acr_name` - e.g., `acrchatbotjohn123`
- `openai_account_name` - e.g., `openai-chatbot-john123`

### Step 2: Initialize Terraform

```bash
terraform init
```

This will download the Azure provider and initialize your Terraform workspace.

### Step 3: Review the Plan

```bash
terraform plan
```

Review the resources that will be created:
- Resource Group
- Virtual Network & Subnet
- Azure Container Registry
- Azure Kubernetes Service (2-node cluster)
- Azure OpenAI Service with model deployment

### Step 4: Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will take **15-20 minutes** to complete.

**What's happening:**
- Creating resource group
- Setting up networking
- Provisioning AKS cluster (longest step)
- Creating Azure OpenAI service and deploying model
- Configuring ACR

### Step 5: Save Terraform Outputs

```bash
# View all outputs
terraform output

# Save important values
terraform output deployment_summary

# Save OpenAI key securely
terraform output -raw openai_primary_key > ../openai-key.txt
chmod 600 ../openai-key.txt
```

---

## Phase 2: Build and Push Docker Images

### Step 1: Login to Azure Container Registry

```bash
# Get ACR name from Terraform
export ACR_NAME=$(terraform output -raw acr_name)

# Login to ACR
az acr login --name $ACR_NAME
```

### Step 2: Build Backend Image

```bash
cd ../backend

# Build the image
docker build -t $ACR_NAME.azurecr.io/chatbot-backend:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/chatbot-backend:latest
```

### Step 3: Build Frontend Image

```bash
cd ../frontend

# Build the image
docker build -t $ACR_NAME.azurecr.io/chatbot-frontend:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/chatbot-frontend:latest
```

### Step 4: Verify Images

```bash
# List images in ACR
az acr repository list --name $ACR_NAME --output table

# You should see:
# chatbot-backend
# chatbot-frontend
```

---

## Phase 3: Configure Kubernetes

### Step 1: Get AKS Credentials

```bash
cd ../cloud_infra

# Get cluster name and resource group
export CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
export RG_NAME=$(terraform output -raw resource_group_name)

# Configure kubectl
az aks get-credentials --resource-group $RG_NAME --name $CLUSTER_NAME

# Verify connection
kubectl get nodes
```

You should see 2 nodes in "Ready" state.

### Step 2: Create Namespace

```bash
cd ../k8s

kubectl apply -f namespace.yaml

# Verify
kubectl get namespace chatbot
```

### Step 3: Create Secrets

```bash
cd ../cloud_infra

# Create Azure OpenAI secret from Terraform outputs
kubectl create secret generic azure-openai-secret \
  --from-literal=AZURE_OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint) \
  --from-literal=AZURE_OPENAI_KEY=$(terraform output -raw openai_primary_key) \
  --from-literal=AZURE_OPENAI_DEPLOYMENT=$(terraform output -raw openai_deployment_name) \
  --from-literal=AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
  --namespace=chatbot

# Verify secret created
kubectl get secrets -n chatbot
```

### Step 4: Update Deployment Manifests

```bash
cd ../k8s

# Get ACR login server
export ACR_LOGIN_SERVER=$(cd ../cloud_infra && terraform output -raw acr_login_server)

# Replace ${ACR_NAME} in deployment files
sed -i '' "s/\${ACR_NAME}/${ACR_LOGIN_SERVER%%.*}/g" backend-deployment.yaml frontend-deployment.yaml

# Or manually edit backend-deployment.yaml and frontend-deployment.yaml
# Replace: ${ACR_NAME}.azurecr.io
# With: your-acr-name.azurecr.io
```

### Step 5: Install Nginx Ingress Controller

```bash
# Install ingress-nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Wait for it to be ready (may take 2-3 minutes)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Verify external IP assigned (may take a few minutes)
kubectl get svc -n ingress-nginx
```

Wait until you see an EXTERNAL-IP (not `<pending>`).

---

## Phase 4: Deploy Application

### Step 1: Deploy Backend

```bash
kubectl apply -f backend-deployment.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=backend -n chatbot --timeout=300s

# Check status
kubectl get pods -n chatbot
kubectl get svc -n chatbot
```

### Step 2: Deploy Frontend

```bash
kubectl apply -f frontend-deployment.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=frontend -n chatbot --timeout=300s

# Check status
kubectl get pods -n chatbot
```

### Step 3: Deploy Ingress

```bash
kubectl apply -f ingress.yaml

# Check ingress
kubectl get ingress -n chatbot
```

### Step 4: Get Application URL

```bash
# Get the external IP from ingress-nginx
export EXTERNAL_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Application URL: http://$EXTERNAL_IP"
echo "API URL: http://$EXTERNAL_IP/api"
```

---

## Phase 5: Verify Deployment

### Test the API

```bash
# Test health endpoint
curl http://$EXTERNAL_IP/api/health

# You should see: {"status":"healthy","service":"chatbot-api"}
```

### Test the Frontend

Open your browser and go to:
```
http://<EXTERNAL-IP>
```

You should see the chatbot interface. Try sending a message!

### View Logs

```bash
# Backend logs
kubectl logs -l app=backend -n chatbot --tail=50

# Frontend logs
kubectl logs -l app=frontend -n chatbot --tail=50
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod for detailed error
kubectl describe pod <pod-name> -n chatbot

# Common issues:
# - Image pull errors: Check ACR integration
# - Secret errors: Verify secrets created correctly
# - Resource limits: Check if nodes have enough capacity
```

### Image Pull Errors

```bash
# Verify AKS can access ACR
kubectl describe pod <pod-name> -n chatbot | grep -A 5 "Failed"

# Check if role assignment exists
az role assignment list --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.ContainerRegistry/registries/<acr-name>
```

### OpenAI API Errors

```bash
# Check if secrets are correct
kubectl get secret azure-openai-secret -n chatbot -o yaml

# Verify OpenAI endpoint and key are valid
# Test manually:
cd ../backend
# Create .env file with secrets
# Run: uv run python -m backend.main
```

### Cannot Access Application

```bash
# Check if ingress has IP
kubectl get svc -n ingress-nginx

# Check ingress rules
kubectl describe ingress chatbot-ingress -n chatbot

# Check if pods are running
kubectl get pods -n chatbot
```

---

## Updating the Application

After making code changes:

### Update Backend

```bash
cd backend

# Rebuild image
docker build -t $ACR_NAME.azurecr.io/chatbot-backend:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/chatbot-backend:latest

# Restart deployment
kubectl rollout restart deployment/backend -n chatbot

# Check rollout status
kubectl rollout status deployment/backend -n chatbot
```

### Update Frontend

```bash
cd frontend

# Rebuild image
docker build -t $ACR_NAME.azurecr.io/chatbot-frontend:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/chatbot-frontend:latest

# Restart deployment
kubectl rollout restart deployment/frontend -n chatbot

# Check rollout status
kubectl rollout status deployment/frontend -n chatbot
```

---

## Cost Management

### Monitor Costs

```bash
# View current costs
az consumption usage list --start-date 2024-12-01 --end-date 2024-12-31

# Set up budget alert
az consumption budget create \
  --budget-name chatbot-budget \
  --amount 200 \
  --time-grain Monthly \
  --category Cost
```

### Stop Resources to Save Costs

```bash
# Stop AKS cluster (saves ~70% of costs)
az aks stop --name $CLUSTER_NAME --resource-group $RG_NAME

# Start when needed
az aks start --name $CLUSTER_NAME --resource-group $RG_NAME
```

---

## Cleanup

When you're done and want to delete everything:

```bash
cd cloud_infra

# Destroy all infrastructure
terraform destroy

# Type 'yes' to confirm

# This will delete:
# - AKS cluster
# - ACR
# - Azure OpenAI
# - Virtual Network
# - Resource Group
```

---

## Next Steps

- Set up custom domain name
- Add SSL/TLS certificate
- Configure autoscaling
- Set up monitoring with Azure Monitor
- Add CI/CD with GitHub Actions
- Implement rate limiting
- Add authentication

Congratulations! Your chatbot is now running on Azure! 🎉

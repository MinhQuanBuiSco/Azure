# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying the chatbot application to AKS.

## Files

- `namespace.yaml` - Creates the chatbot namespace
- `secrets.yaml` - Template for Azure OpenAI secrets (DO NOT commit actual secrets!)
- `backend-deployment.yaml` - Backend API deployment and service
- `frontend-deployment.yaml` - Frontend web deployment and service
- `ingress.yaml` - Ingress controller configuration

## Deployment Steps

### 1. Get AKS Credentials

```bash
# Get credentials from Terraform output or use:
az aks get-credentials --resource-group rg-chatbot-dev --name aks-chatbot
```

### 2. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 3. Create Secrets from Terraform Outputs

```bash
# Navigate to terraform directory
cd ../cloud_infra

# Create secrets using Terraform outputs
kubectl create secret generic azure-openai-secret \
  --from-literal=AZURE_OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint) \
  --from-literal=AZURE_OPENAI_KEY=$(terraform output -raw openai_primary_key) \
  --from-literal=AZURE_OPENAI_DEPLOYMENT=$(terraform output -raw openai_deployment_name) \
  --from-literal=AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
  --namespace=chatbot
```

### 4. Update Image Names

Replace `${ACR_NAME}` in the deployment files with your actual ACR name:

```bash
# Get ACR name from Terraform
cd ../cloud_infra
export ACR_NAME=$(terraform output -raw acr_login_server | cut -d. -f1)

# Update deployment files
cd ../k8s
sed -i '' "s/\${ACR_NAME}/$ACR_NAME/g" backend-deployment.yaml frontend-deployment.yaml
```

Or manually edit the files and replace `${ACR_NAME}.azurecr.io` with your ACR login server.

### 5. Install Nginx Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
```

Wait for the ingress controller to be ready:

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### 6. Deploy Application

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

### 7. Verify Deployment

```bash
# Check pods
kubectl get pods -n chatbot

# Check services
kubectl get svc -n chatbot

# Check ingress
kubectl get ingress -n chatbot

# Get external IP (may take a few minutes)
kubectl get svc -n ingress-nginx
```

### 8. Access the Application

Once the ingress has an external IP, you can access the application at:

```
http://<EXTERNAL-IP>
```

The API will be available at:

```
http://<EXTERNAL-IP>/api
```

## Updating Deployments

After building and pushing new Docker images:

```bash
# Restart deployments to pull new images
kubectl rollout restart deployment/backend -n chatbot
kubectl rollout restart deployment/frontend -n chatbot

# Check rollout status
kubectl rollout status deployment/backend -n chatbot
kubectl rollout status deployment/frontend -n chatbot
```

## Troubleshooting

```bash
# View logs
kubectl logs -l app=backend -n chatbot --tail=100
kubectl logs -l app=frontend -n chatbot --tail=100

# Describe pod for issues
kubectl describe pod <pod-name> -n chatbot

# Check events
kubectl get events -n chatbot --sort-by='.lastTimestamp'
```

## Cleanup

```bash
kubectl delete namespace chatbot
```

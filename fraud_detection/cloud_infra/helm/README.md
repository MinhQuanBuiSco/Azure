# Helm Charts for Fraud Detection System

This directory contains Helm charts for deploying the fraud detection system to Kubernetes/AKS.

## Charts

- **backend**: FastAPI backend service
- **frontend**: React frontend application

## Prerequisites

1. **Helm 3**: Install from https://helm.sh/docs/intro/install/
2. **kubectl**: Configured with AKS cluster access
3. **ACR**: Container images pushed to Azure Container Registry

## Quick Start

### 1. Create Kubernetes Secrets

```bash
# Backend secrets
kubectl create secret generic backend-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/fraud_detection" \
  --from-literal=redis-host="your-redis.redis.cache.windows.net" \
  --from-literal=redis-port="6380" \
  --from-literal=redis-password="your-redis-key" \
  --from-literal=azure-ai-endpoint="https://your-resource.services.ai.azure.com/models" \
  --from-literal=azure-ai-key="your-azure-ai-key" \
  --from-literal=azure-ai-model-name="claude-3-5-sonnet" \
  --from-literal=azure-anomaly-endpoint="your-endpoint" \
  --from-literal=azure-anomaly-key="your-key"
```

### 2. Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
```

### 3. Install cert-manager (Optional, for TLS)

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

### 4. Deploy Backend

```bash
cd backend
helm install fraud-detection-backend . \
  --namespace fraud-detection --create-namespace \
  --set image.repository=frauddetectionacr.azurecr.io/fraud-detection-backend \
  --set image.tag=latest \
  --set ingress.hosts[0].host=api.your-domain.com \
  --set ingress.tls[0].hosts[0]=api.your-domain.com
```

### 5. Deploy Frontend

```bash
cd ../frontend
helm install fraud-detection-frontend . \
  --namespace fraud-detection \
  --set image.repository=frauddetectionacr.azurecr.io/fraud-detection-frontend \
  --set image.tag=latest \
  --set env[0].value=https://api.your-domain.com \
  --set env[1].value=wss://api.your-domain.com/api/v1/ws/transactions \
  --set ingress.hosts[0].host=your-domain.com \
  --set ingress.tls[0].hosts[0]=your-domain.com
```

## Configuration

### Backend Values

Key configuration options in `backend/values.yaml`:

```yaml
replicaCount: 2              # Number of replicas
image:
  repository: <acr>.azurecr.io/fraud-detection-backend
  tag: latest
resources:
  requests:
    cpu: 250m
    memory: 256Mi
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 4
```

### Frontend Values

Key configuration options in `frontend/values.yaml`:

```yaml
replicaCount: 2              # Number of replicas
image:
  repository: <acr>.azurecr.io/fraud-detection-frontend
  tag: latest
env:
  - name: VITE_API_URL
    value: "https://api.your-domain.com"
  - name: VITE_WS_URL
    value: "wss://api.your-domain.com/api/v1/ws/transactions"
```

## Upgrading Deployments

```bash
# Backend
helm upgrade fraud-detection-backend ./backend \
  --namespace fraud-detection \
  --set image.tag=v1.1.0

# Frontend
helm upgrade fraud-detection-frontend ./frontend \
  --namespace fraud-detection \
  --set image.tag=v1.1.0
```

## Rolling Back

```bash
# Backend
helm rollback fraud-detection-backend -n fraud-detection

# Frontend
helm rollback fraud-detection-frontend -n fraud-detection
```

## Uninstalling

```bash
helm uninstall fraud-detection-backend -n fraud-detection
helm uninstall fraud-detection-frontend -n fraud-detection
kubectl delete namespace fraud-detection
```

## Monitoring

### Check Pod Status

```bash
kubectl get pods -n fraud-detection
kubectl logs -f <pod-name> -n fraud-detection
```

### Check Services

```bash
kubectl get services -n fraud-detection
kubectl get ingress -n fraud-detection
```

### View HPA Status

```bash
kubectl get hpa -n fraud-detection
```

## Troubleshooting

### Image Pull Errors

Ensure AKS has permission to pull from ACR:

```bash
az aks update -n <aks-name> -g <rg-name> --attach-acr <acr-name>
```

### Secret Not Found

Verify secrets exist:

```bash
kubectl get secrets -n fraud-detection
kubectl describe secret backend-secrets -n fraud-detection
```

### Pod Crash Loop

Check logs:

```bash
kubectl logs <pod-name> -n fraud-detection --previous
kubectl describe pod <pod-name> -n fraud-detection
```

### Ingress Not Working

Check ingress controller:

```bash
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx <ingress-controller-pod>
```

## Production Recommendations

1. **Use Specific Image Tags**: Never use `latest` in production
2. **Resource Limits**: Set appropriate CPU/memory limits
3. **Secrets Management**: Use Azure Key Vault with CSI driver
4. **TLS Certificates**: Configure cert-manager with Let's Encrypt
5. **Monitoring**: Install Prometheus + Grafana
6. **Backup**: Regular database backups
7. **Scaling**: Tune HPA based on load testing results

## Values Override Example

Create a `values-prod.yaml`:

```yaml
backend:
  replicaCount: 3
  image:
    tag: "v1.2.0"
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  autoscaling:
    minReplicas: 3
    maxReplicas: 10
```

Deploy with:

```bash
helm install fraud-detection-backend ./backend \
  -f values-prod.yaml \
  --namespace fraud-detection
```

## CI/CD Integration

These charts are designed to work with GitHub Actions. See `.github/workflows/` for automated deployment pipelines.

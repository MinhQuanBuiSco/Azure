# 🤖 AI Chatbot - Production-Ready on Azure

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![React](https://img.shields.io/badge/react-18.3-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![Azure](https://img.shields.io/badge/Azure-Cloud-0078d4.svg)
![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-326ce5.svg)

A modern, production-ready AI chatbot with **real-time streaming responses**, built with React, FastAPI, and deployed on Azure Kubernetes Service.

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Deployment](#-deployment) • [Cleanup](#-cleanup--resource-management) • [Documentation](#-documentation)

</div>

---

## ✨ Features

### 🎯 Core Capabilities
- **Real-time Streaming Responses** - See AI responses appear word-by-word as they're generated
- **Modern Dark UI** - Sleek, professional interface with glass-morphism effects
- **Production-Ready** - Multi-stage Docker builds, health checks, auto-scaling
- **Cloud-Native** - Fully containerized and orchestrated with Kubernetes
- **Infrastructure as Code** - Complete Terraform configuration for reproducible deployments

### 🛠 Technical Stack

**Frontend**
- ⚛️ React 18 with modern hooks
- 🎨 Tailwind CSS for styling
- ⚡ Vite for blazing-fast builds
- 🌊 Server-Sent Events (SSE) for streaming
- 📱 Responsive design for all devices

**Backend**
- 🐍 Python 3.12 with FastAPI
- 🤖 OpenAI GPT-4 integration (Azure OpenAI compatible)
- 🔄 Async streaming with event generation
- 📊 Pydantic for data validation
- 🚀 uvicorn with optimized settings

**Infrastructure**
- ☁️ Azure Kubernetes Service (AKS)
- 🐳 Azure Container Registry (ACR)
- 🌐 Nginx Ingress Controller
- 🏗️ Terraform for IaC
- 🔐 Kubernetes Secrets for secure config

**DevOps**
- 🐋 Multi-stage Docker builds
- 🔄 CI/CD ready
- 📈 Health checks and readiness probes
- 📊 Resource limits and auto-scaling
- 🔍 Comprehensive logging

---

## 🎬 Demo

### Real-time Streaming in Action

The chatbot features **true real-time streaming** - responses appear word-by-word as the AI generates them:

```
User: Explain quantum computing

AI: Quantum [streaming...]
AI: Quantum computing is [streaming...]
AI: Quantum computing is a revolutionary [streaming...]
```

### Modern UI Features
- 🌙 Professional dark theme with blue-cyan gradients
- 💬 Integrated typing indicators during streaming
- ✨ Smooth animations and transitions
- 🎯 Suggested prompts for quick starts
- 📱 Mobile-responsive design

---

## 🚀 Quick Start

### Prerequisites

- **Azure Account** with active subscription
- **Docker** (20.10+)
- **kubectl** (1.28+)
- **Terraform** (1.0+)
- **Azure CLI** (2.50+)
- **OpenAI API Key** (or Azure OpenAI access)

### Local Development (5 minutes)

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/chatbot_on_azure.git
cd chatbot_on_azure
```

**2. Set up backend**
```bash
cd backend
uv sync                          # Install dependencies
cp .env.example .env             # Copy environment template
# Edit .env with your OpenAI API key
uv run uvicorn backend.main:app --reload --port 8000
```

**3. Set up frontend** (in new terminal)
```bash
cd frontend
npm install                       # Install dependencies
cp .env.example .env              # Copy environment template
# Edit .env: VITE_API_URL=http://localhost:8000
npm run dev                       # Start dev server
```

**4. Open your browser**
```
http://localhost:5173
```

That's it! Start chatting with the AI 🎉

---

## 🏗 Architecture

> 💡 **New to Azure or Terraform?** Check out the [**Infrastructure Guide (INFRASTRUCTURE.md)**](INFRASTRUCTURE.md) - A comprehensive guide with AWS comparisons, Terraform explanations, and step-by-step walkthroughs!

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Nginx Ingress       │
              │  (Load Balancer)     │
              └──────────┬───────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
    ┌──────────────┐          ┌──────────────┐
    │   Frontend   │          │   Backend    │
    │  (React SPA) │──────────│  (FastAPI)   │
    │   + Nginx    │   API    │  + OpenAI    │
    └──────────────┘          └──────────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
              ┌──────────────────┐
              │      OpenAI      │
              │     (GPT-4)      │
              └──────────────────┘
```

### Streaming Data Flow

```
Frontend (React) ──HTTP POST──> Backend (FastAPI)
                                      │
                                      ▼
                              OpenAI API (streaming)
                                      │
                                      ▼
                              Event Generator
                                      │
                                      ▼
                              SSE Format
                              data: {"content": "word"}
                                      │
                                      ▼
Frontend ←──────chunk by chunk──────┘
   │
   └──> React State Update (incremental)
```

### Project Structure

```
chatbot_on_azure/
├── backend/                     # Python FastAPI backend
│   ├── src/backend/
│   │   ├── config.py           # Environment configuration
│   │   ├── main.py             # FastAPI app with CORS
│   │   ├── routes/
│   │   │   └── chat.py         # Streaming & non-streaming endpoints
│   │   └── services/
│   │       └── openai_service.py  # OpenAI integration
│   ├── Dockerfile              # Multi-stage build
│   ├── pyproject.toml          # uv dependencies
│   └── .env.example
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx     # Message bubble with streaming indicator
│   │   │   └── TypingIndicator.jsx # Animated typing dots
│   │   ├── services/
│   │   │   └── api.js          # SSE streaming client
│   │   └── App.jsx             # Main app with state management
│   ├── Dockerfile              # Build + Nginx
│   ├── nginx.conf              # Production config
│   └── .env.example
│
├── cloud_infra/                 # Terraform IaC
│   ├── modules/
│   │   ├── acr/                # Container registry
│   │   ├── aks/                # Kubernetes cluster
│   │   ├── network/            # VNet & subnets
│   │   └── openai/             # Azure OpenAI (optional)
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
└── k8s/                         # Kubernetes manifests
    ├── namespace.yaml
    ├── backend-deployment.yaml  # 2 replicas with health checks
    ├── frontend-deployment.yaml # 2 replicas with health checks
    ├── ingress.yaml            # SSE-optimized configuration
    └── UPDATE_SECRET.md        # Guide for managing OpenAI secrets
```

---

## 📦 Deployment

### Option 1: Azure Kubernetes Service (Production)

**Step 1: Deploy Infrastructure**
```bash
cd cloud_infra
terraform init
terraform apply -auto-approve

# Get outputs
export ACR_NAME=$(terraform output -raw acr_name)
export AKS_NAME=$(terraform output -raw aks_cluster_name)
export RESOURCE_GROUP=$(terraform output -raw resource_group_name)
```

**Step 2: Build & Push Docker Images**
```bash
# Login to Azure Container Registry
az acr login --name $ACR_NAME

# Build and push backend
cd ../backend
docker build -t $ACR_NAME.azurecr.io/chatbot-backend:latest .
docker push $ACR_NAME.azurecr.io/chatbot-backend:latest

# Build and push frontend
cd ../frontend
docker build -t $ACR_NAME.azurecr.io/chatbot-frontend:latest .
docker push $ACR_NAME.azurecr.io/chatbot-frontend:latest
```

**Step 3: Configure Kubernetes**
```bash
# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME

# Create namespace
kubectl apply -f ../k8s/namespace.yaml

# Create secrets (replace with your actual API key from platform.openai.com)
kubectl create secret generic openai-secret \
  --from-literal=OPENAI_API_KEY='sk-your-openai-api-key' \
  --from-literal=OPENAI_MODEL='gpt-4-turbo-preview' \
  -n chatbot

# 💡 Tip: Need to update your API key later?
# See k8s/UPDATE_SECRET.md for detailed instructions
```

**Step 4: Deploy Application**
```bash
cd ../k8s

# Deploy backend
kubectl apply -f backend-deployment.yaml

# Deploy frontend
kubectl apply -f frontend-deployment.yaml

# Deploy ingress
kubectl apply -f ingress.yaml

# Wait for deployment
kubectl rollout status deployment/backend -n chatbot
kubectl rollout status deployment/frontend -n chatbot
```

**Step 5: Get Application URL**
```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Output shows EXTERNAL-IP
# Access your chatbot at: http://<EXTERNAL-IP>
```

### Option 2: Local Docker Compose (Development)

Coming soon! Simple `docker-compose up` for local testing.

---

## 🔧 Configuration

### Backend Environment Variables

```bash
# OpenAI Configuration (choose one)

# Option 1: Regular OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
USE_AZURE_OPENAI=false

# Option 2: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
USE_AZURE_OPENAI=true

# Application Settings
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
DEBUG=false
```

### Frontend Environment Variables

```bash
# Development
VITE_API_URL=http://localhost:8000

# Production (use empty string for same-origin)
VITE_API_URL=
```

### Streaming Configuration

The application is **pre-configured for optimal streaming**:

**Backend (`backend/Dockerfile`)**
```dockerfile
CMD ["uvicorn", "backend.main:app",
     "--host", "0.0.0.0",
     "--port", "8000",
     "--timeout-keep-alive", "300"]
```

**Ingress (`k8s/ingress.yaml`)**
```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-buffering: "off"
  nginx.ingress.kubernetes.io/proxy-http-version: "1.1"
  nginx.ingress.kubernetes.io/server-snippet: |
    chunked_transfer_encoding on;
    proxy_buffering off;
    proxy_cache off;
```

---

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint - API info |
| `GET` | `/api/health` | Health check for K8s probes |
| `POST` | `/api/chat` | Non-streaming chat (full response) |
| `POST` | `/api/chat/stream` | **Streaming chat (SSE)** |

### Streaming Chat Example

**Request**
```bash
curl -N http://your-domain/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Count to 5"}
    ]
  }'
```

**Response (Server-Sent Events)**
```
data: {"content": "1"}

data: {"content": ", 2"}

data: {"content": ", 3"}

data: {"content": ", 4"}

data: {"content": ", 5"}

data: {"done": true}
```

### Frontend Integration

```javascript
import { sendChatMessageStream } from './services/api';

// Send message with streaming callback
await sendChatMessageStream(messages, (chunk) => {
  // Update UI with each chunk in real-time
  setMessages(prev => {
    const updated = [...prev];
    updated[updated.length - 1].content += chunk;
    return updated;
  });
});
```

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# Backend logs (watch streaming in action)
kubectl logs -f -l app=backend -n chatbot | grep STREAM

# Frontend logs
kubectl logs -f -l app=frontend -n chatbot

# All pods
kubectl logs -f -l app=backend,app=frontend -n chatbot
```

### Check Status

```bash
# Pod status
kubectl get pods -n chatbot

# Service endpoints
kubectl get svc -n chatbot

# Ingress configuration
kubectl describe ingress chatbot-ingress -n chatbot

# Resource usage
kubectl top pods -n chatbot
kubectl top nodes
```

### Debug Streaming Issues

**1. Verify backend is sending chunks**
```bash
kubectl logs -l app=backend -n chatbot | grep "STREAM"
# You should see:
# [STREAM] Starting streaming response
# [STREAM] Chunk 1: 'Hello'
# [STREAM] Chunk 2: ' there'
```

**2. Check ingress buffering settings**
```bash
kubectl describe ingress chatbot-ingress -n chatbot | grep buffering
# Should show: proxy-buffering: off
```

**3. Test backend directly (bypass ingress)**
```bash
kubectl port-forward -n chatbot svc/backend 8080:80
curl -N http://localhost:8080/api/chat/stream -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Hi"}]}'
```

---

## 💰 Cost Estimation

Running on Azure with $200 free credit:

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| **AKS** | 2 × B2s nodes (2 vCPU, 4GB) | $70-100 |
| **ACR** | Basic tier | $5 |
| **OpenAI** | GPT-4 Turbo | $0.01 per 1K input tokens<br>$0.03 per 1K output tokens |
| **Load Balancer** | Standard | $5-10 |
| **Networking** | Egress | $5-10 |
| **Total** | | **~$85-130/month** |

**Cost Optimization Tips:**
- Use B-series VMs for development
- Enable cluster autoscaler
- Use Azure OpenAI consumption tier
- Monitor and set spending alerts
- Shut down dev environments when not in use

Your **$200 Azure credit** should last **~2-3 months** for development/testing.

---

## 🔐 Security Best Practices

### Implemented Security Features

- ✅ **Secrets Management** - Kubernetes secrets (not in code/version control)
- ✅ **Environment Variables** - 12-factor app configuration
- ✅ **CORS Configuration** - Restricted origins
- ✅ **Nginx Security Headers** - X-Frame-Options, CSP, etc.
- ✅ **Azure Managed Identity** - ACR integration without passwords
- ✅ **Health Checks** - Liveness/readiness probes
- ✅ **Resource Limits** - CPU/memory constraints
- ✅ **Multi-stage Builds** - Smaller attack surface

### Additional Recommendations

```bash
# Enable network policies
kubectl apply -f k8s/network-policy.yaml

# Use Azure Key Vault for secrets
# Add pod identity for key vault access

# Enable Azure Policy for AKS
az aks enable-addons --addons azure-policy --name $AKS_NAME --resource-group $RESOURCE_GROUP

# Regular security scans
az acr task create --registry $ACR_NAME --name security-scan --cmd "trivy image {{.Run.Registry}}/chatbot-backend:{{.Run.ID}}"
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Streaming not working (full response appears at once)**

✅ **Solution:**
- Verify ingress annotations: `kubectl describe ingress chatbot-ingress -n chatbot`
- Check backend logs: `kubectl logs -l app=backend -n chatbot | grep STREAM`
- Clear browser cache (Ctrl+Shift+R)
- Test backend directly with port-forward

**2. Image pull errors**

✅ **Solution:**
```bash
# Grant AKS access to ACR
az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
```

**3. Pods crashing / CrashLoopBackOff**

✅ **Solution:**
```bash
# Check logs
kubectl logs <pod-name> -n chatbot

# Verify secrets exist
kubectl get secrets -n chatbot

# Check environment variables
kubectl describe pod <pod-name> -n chatbot
```

**4. OpenAI API errors**

✅ **Solution:**
- Verify API key is correct in secret
- Check quota limits in OpenAI dashboard
- Ensure USE_AZURE_OPENAI flag matches your setup
- Test API key manually with curl

**5. Ingress not getting external IP**

✅ **Solution:**
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# If not installed, install it:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

---

## 🧹 Cleanup & Resource Management

### ⚠️ Important: Avoid Unexpected Costs

Azure resources continue to incur charges even when not in use. **Always clean up when done testing/developing.**

### Quick Cleanup (Delete Everything)

**Option 1: Delete via Terraform (Recommended)**
```bash
cd cloud_infra

# Destroy all infrastructure
terraform destroy -auto-approve

# This will delete:
# - AKS cluster
# - ACR registry (including all images)
# - VNet and networking
# - Resource group (if empty)
```

**Option 2: Delete Resource Group (Fastest)**
```bash
# Get resource group name
az group list --output table

# Delete entire resource group (WARNING: Deletes EVERYTHING in it)
az group delete --name <resource-group-name> --yes --no-wait

# Example:
az group delete --name rg-chatbot-japaneast --yes --no-wait
```

### Selective Cleanup (Keep Infrastructure, Delete Apps)

**Delete Kubernetes Resources Only**
```bash
# Delete all chatbot resources
kubectl delete namespace chatbot

# Delete ingress controller (optional)
kubectl delete namespace ingress-nginx

# This preserves:
# ✓ AKS cluster
# ✓ ACR registry
# ✓ VNet
# You can redeploy apps without rebuilding infrastructure
```

**Delete Container Images Only**
```bash
# List images
az acr repository list --name $ACR_NAME --output table

# Delete specific image
az acr repository delete --name $ACR_NAME --image chatbot-backend:latest --yes
az acr repository delete --name $ACR_NAME --image chatbot-frontend:latest --yes
```

### Verify Cleanup

```bash
# Check if resources are deleted
az group list --output table
az aks list --output table
az acr list --output table

# Check Kubernetes
kubectl get all -n chatbot
kubectl get all -n ingress-nginx
```

### Cost Monitoring

**Set up spending alerts (Recommended)**
```bash
# Set budget alert at $50
az consumption budget create \
  --budget-name chatbot-budget \
  --amount 50 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2025-12-31

# Check current costs
az consumption usage list --output table
```

**View costs in Azure Portal**
```
https://portal.azure.com → Cost Management + Billing → Cost Analysis
```

### Development Workflow Best Practices

**Daily Development:**
```bash
# Morning: Start working
kubectl scale deployment/backend --replicas=2 -n chatbot
kubectl scale deployment/frontend --replicas=2 -n chatbot

# Evening: Stop to save costs (keeps cluster running)
kubectl scale deployment/backend --replicas=0 -n chatbot
kubectl scale deployment/frontend --replicas=0 -n chatbot
```

**Weekend/Extended Breaks:**
```bash
# Stop AKS cluster (saves ~70% of costs)
az aks stop --name $AKS_NAME --resource-group $RESOURCE_GROUP

# Restart when needed
az aks start --name $AKS_NAME --resource-group $RESOURCE_GROUP
```

**Project Completed:**
```bash
# Delete everything via Terraform
cd cloud_infra
terraform destroy -auto-approve
```

### Emergency Stop (Prevent Billing)

If you need to **immediately stop all charges**:

```bash
# 1. Stop AKS cluster
az aks stop --name <aks-name> --resource-group <rg-name> --no-wait

# 2. Or delete resource group entirely
az group delete --name <rg-name> --yes --no-wait

# 3. Verify in portal
# https://portal.azure.com → Resource groups
# Make sure resource group is gone or resources are stopped
```

### Cleanup Checklist

Before ending your session:

- [ ] **Stop AKS cluster** if not using for a few days
- [ ] **Scale down deployments** to 0 replicas if taking a break
- [ ] **Delete resource group** if project is complete
- [ ] **Check Azure portal** for any orphaned resources
- [ ] **Review cost analysis** to ensure no unexpected charges
- [ ] **Remove local credentials** if on shared machine
  ```bash
  kubectl config delete-context aks-chatbot
  az logout
  ```

### Common Cleanup Mistakes

❌ **Don't:**
- Leave AKS cluster running 24/7 during development
- Forget to delete load balancers (they charge even when idle)
- Keep unused container images in ACR
- Leave public IPs allocated

✅ **Do:**
- Use `terraform destroy` when completely done
- Stop AKS cluster during nights/weekends
- Set up budget alerts ($50-100 recommended)
- Regularly check Azure cost analysis

---

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://your-domain/api/health

# Non-streaming chat
curl -X POST http://your-domain/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hi"}]}'

# Streaming chat (watch chunks appear)
curl -N http://your-domain/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Count to 10"}]}'
```

### Load Testing

```bash
# Install hey (HTTP load testing tool)
go install github.com/rakyll/hey@latest

# Test backend performance
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hi"}]}' \
  http://your-domain/api/chat
```

---

## 📈 Performance Optimization

### Implemented Optimizations

**Backend**
- Async/await for non-blocking I/O
- Connection pooling
- uvicorn workers (can be increased)
- Streaming responses (lower latency)

**Frontend**
- React 18 automatic batching
- Code splitting with Vite
- Gzip compression in Nginx
- Asset caching (1 year)
- Lazy loading components

**Infrastructure**
- Horizontal Pod Autoscaler (HPA)
- Resource requests/limits
- Ingress connection pooling
- Container image optimization

### Further Optimizations

```yaml
# Enable HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
5. **Push and create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

### Development Guidelines

- Use conventional commits (feat, fix, docs, etc.)
- Run linters before committing
- Test locally before pushing
- Update README if adding features

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License - You are free to:
✓ Use commercially
✓ Modify
✓ Distribute
✓ Use privately
```

---

## 🙏 Acknowledgments

### Technologies Used
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [OpenAI](https://openai.com/) - GPT-4 API
- [Azure](https://azure.microsoft.com/) - Cloud platform
- [Kubernetes](https://kubernetes.io/) - Container orchestration
- [Terraform](https://www.terraform.io/) - Infrastructure as Code
- [Docker](https://www.docker.com/) - Containerization

### Inspiration
Built for learning modern cloud-native development practices including:
- Microservices architecture
- Container orchestration
- Infrastructure as Code
- Real-time streaming APIs
- Modern DevOps workflows

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

**Built with ❤️ for the developer community**

[Report Bug](https://github.com/yourusername/chatbot_on_azure/issues) · [Request Feature](https://github.com/yourusername/chatbot_on_azure/issues) · [Contribute](https://github.com/yourusername/chatbot_on_azure/pulls)

</div>

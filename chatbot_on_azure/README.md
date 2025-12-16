# Azure Chatbot - Full Stack Application

A production-ready chatbot application deployed on Azure using modern DevOps practices.

## Architecture

- **Frontend**: React + Tailwind CSS + Vite
- **Backend**: Python FastAPI + Azure OpenAI SDK
- **Infrastructure**: Terraform (Infrastructure as Code)
- **Container Registry**: Azure Container Registry (ACR)
- **Orchestration**: Azure Kubernetes Service (AKS)
- **AI**: Azure OpenAI Service (GPT-3.5-turbo or GPT-4)
- **Package Management**: uv (Python), npm (Node.js)

## Project Structure

```
chatbot_on_azure/
├── backend/                 # Python FastAPI backend
│   ├── src/backend/
│   │   ├── config.py       # Configuration management
│   │   ├── main.py         # FastAPI application
│   │   ├── routes/         # API routes
│   │   └── services/       # Azure OpenAI service
│   ├── Dockerfile          # Multi-stage Docker build
│   ├── pyproject.toml      # uv dependencies
│   └── .env.example        # Environment template
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── App.jsx         # Main app
│   ├── Dockerfile          # Multi-stage build with nginx
│   ├── nginx.conf          # Production nginx config
│   └── .env.example        # Environment template
│
├── cloud_infra/            # Terraform IaC
│   ├── modules/
│   │   ├── acr/           # Container Registry module
│   │   ├── aks/           # Kubernetes module
│   │   ├── network/       # VNet module
│   │   └── openai/        # Azure OpenAI module
│   ├── main.tf            # Main terraform config
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Output values
│   └── terraform.tfvars.example
│
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── ingress.yaml
│
├── SETUP.md               # Prerequisites and Azure setup
├── DEPLOYMENT.md          # Complete deployment guide
└── README.md              # This file
```

## Features

- ✅ Production-ready FastAPI backend
- ✅ Modern React frontend with Tailwind CSS
- ✅ Azure OpenAI integration (GPT-3.5-turbo/GPT-4)
- ✅ Complete Infrastructure as Code with Terraform
- ✅ Containerized with Docker (multi-stage builds)
- ✅ Kubernetes orchestration on AKS
- ✅ Auto-scaling and health checks
- ✅ Nginx ingress controller
- ✅ Secure secrets management
- ✅ CORS configuration
- ✅ Comprehensive logging

## Getting Started

### 1. Prerequisites

Follow the instructions in [SETUP.md](SETUP.md) to:
- Install required tools
- Configure Azure CLI
- Create service principal
- Apply for Azure OpenAI access

### 2. Deployment

Follow the step-by-step guide in [DEPLOYMENT.md](DEPLOYMENT.md) to:
- Deploy infrastructure with Terraform
- Build and push Docker images
- Configure Kubernetes
- Deploy the application

### 3. Quick Start (After Setup)

```bash
# 1. Deploy infrastructure
cd cloud_infra
terraform init
terraform apply

# 2. Build and push images
export ACR_NAME=$(terraform output -raw acr_name)
az acr login --name $ACR_NAME

cd ../backend
docker build -t $ACR_NAME.azurecr.io/chatbot-backend:latest .
docker push $ACR_NAME.azurecr.io/chatbot-backend:latest

cd ../frontend
docker build -t $ACR_NAME.azurecr.io/chatbot-frontend:latest .
docker push $ACR_NAME.azurecr.io/chatbot-frontend:latest

# 3. Deploy to Kubernetes
cd ../k8s
kubectl apply -f namespace.yaml
# Create secrets (see DEPLOYMENT.md)
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml

# 4. Get application URL
kubectl get svc -n ingress-nginx
```

## Local Development

### Backend

```bash
cd backend

# Install dependencies with uv
uv sync

# Create .env file (copy from .env.example and fill in values)
cp .env.example .env

# Run development server
uv run uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Run development server
npm run dev
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `POST /api/chat` - Chat endpoint

### Chat API Request

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
```

### Chat API Response

```json
{
  "response": "I'm doing well, thank you! How can I help you today?"
}
```

## Environment Variables

### Backend (.env)

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=True
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
```

## Cost Estimation

Monthly costs with $200 Azure credit:

| Service | Cost/Month |
|---------|------------|
| AKS (2 B2s nodes) | ~$70-100 |
| ACR (Basic) | ~$5 |
| Azure OpenAI | ~$0.002-0.03 per 1K tokens |
| Networking | ~$5-10 |
| **Total** | **~$80-120** |

Your $200 credit should last 2-3 months.

## Security Best Practices

- ✅ Secrets stored in Kubernetes secrets (not in code)
- ✅ Environment variables for configuration
- ✅ CORS properly configured
- ✅ Nginx security headers
- ✅ Azure managed identities for AKS-ACR integration
- ✅ Network policies ready for implementation

## Monitoring

```bash
# View pod logs
kubectl logs -l app=backend -n chatbot

# Check pod status
kubectl get pods -n chatbot

# View resource usage
kubectl top pods -n chatbot
kubectl top nodes
```

## Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting steps.

Common issues:
- Azure OpenAI not approved → Apply for access
- Image pull errors → Check ACR integration
- Pod crashes → Check logs and secrets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use this project for learning and production!

## Support

For issues and questions:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Check [SETUP.md](SETUP.md) for setup issues
- Review Kubernetes logs for runtime errors
- Verify Azure OpenAI access and quotas

## Acknowledgments

- Azure OpenAI Service
- FastAPI framework
- React and Tailwind CSS
- Terraform by HashiCorp
- Kubernetes and AKS

---

Built with ❤️ for learning Azure, Kubernetes, and modern DevOps practices.

# Getting Started Guide

This guide will walk you through setting up and using the fraud detection system from scratch.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Using the Application](#using-the-application)
3. [Testing Fraud Detection](#testing-fraud-detection)
4. [Deploying to Azure](#deploying-to-azure)
5. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

Install these tools before starting:

1. **Docker Desktop** - https://www.docker.com/products/docker-desktop
2. **Git** - https://git-scm.com/downloads
3. **Make** (optional, for convenience commands)
   - macOS: Pre-installed
   - Windows: Install via Chocolatey `choco install make`
   - Linux: `sudo apt-get install build-essential`

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd fraud_detection
```

### Step 2: Start the Application

```bash
# One command to build and start everything
make init
```

This will:
1. Build Docker images for backend and frontend
2. Start PostgreSQL, Redis, backend, and frontend
3. Run database migrations
4. Create initial data

**Wait 2-3 minutes** for all services to start.

### Step 3: Verify Everything is Running

```bash
# Check all containers are running
make ps

# Should show:
# - fraud_detection-backend
# - fraud_detection-frontend
# - fraud_detection-postgres
# - fraud_detection-redis
```

### Step 4: Access the Application

Open your browser:

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

You should see the fraud detection dashboard!

---

## Using the Application

### Dashboard Overview

The application has 4 main pages:

#### 1. **Live Dashboard** (http://localhost:3000)

**What you see:**
- Real-time transaction feed
- Fraud alerts sidebar
- Statistics cards (total transactions, fraud detected, amount blocked)
- Live connection indicator

**How to use:**
```bash
# Generate transactions to see live updates
make generate-txns

# Watch the dashboard update in real-time!
```

#### 2. **Transactions** (http://localhost:3000/transactions)

**What you see:**
- Searchable table of all transactions
- Risk level filter (All, High, Medium, Low)
- Click any row to see full details

**How to use:**
1. Click dropdown to filter by risk level
2. Click any transaction to see detailed breakdown
3. View fraud score, triggered rules, AI explanation

#### 3. **Alerts** (http://localhost:3000/alerts)

**What you see:**
- Queue of fraud alerts requiring investigation
- Filter by status (New, Investigating, Resolved)
- Filter by priority (Critical, High, Medium, Low)

**How to use:**
1. Click alert to expand actions
2. Click "Investigate" to mark as under review
3. Click "Resolve" when investigation complete
4. Click "False Positive" if fraud was incorrectly flagged
5. Click "View Details" to see full transaction info

#### 4. **Analytics** (http://localhost:3000/analytics)

**What you see:**
- Transaction & fraud trends (line chart)
- Risk level distribution (pie chart)
- Fraud by merchant category (bar chart)
- Fraud score distribution (area chart)
- Hourly patterns (area chart)

**How to use:**
- Select time range (7d, 30d, 90d)
- Hover over charts for details
- Analyze fraud patterns

### Dark Mode

Toggle dark/light mode using the button in the sidebar (bottom left).

---

## Testing Fraud Detection

### Method 1: Generate Synthetic Transactions (Recommended)

Generate realistic transactions with configurable fraud:

```bash
# Generate 100 transactions with 10% fraud rate
make generate-txns

# Generate transactions quickly (for testing)
make generate-txns-fast

# Generate continuous stream (watch real-time updates)
make generate-txns-stream
```

**Custom generation:**

```bash
docker-compose exec backend uv run python scripts/generate_transactions.py \
  --count 500 \
  --interval 0.2 \
  --fraud-rate 0.15 \
  --users 50
```

Parameters:
- `--count`: Number of transactions to generate
- `--interval`: Seconds between transactions (0.2 = 5 txns/sec)
- `--fraud-rate`: Percentage of fraudulent transactions (0.15 = 15%)
- `--users`: Number of unique users

**What happens:**
1. Generator creates realistic transactions with user patterns
2. Sends to backend API for fraud scoring
3. Backend scores using rules + ML + Azure AI
4. Results broadcast via WebSocket
5. Dashboard updates in real-time
6. Fraud alerts appear in alerts queue

### Method 2: Use the API Directly

Submit transactions via the REST API:

```bash
# Submit a normal transaction
curl -X POST http://localhost:8000/api/v1/transactions/score \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": 45.99,
    "merchant_name": "Amazon",
    "merchant_category": "E-commerce",
    "transaction_type": "purchase",
    "country": "US",
    "city": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "device_id": "device_abc",
    "ip_address": "192.168.1.1"
  }'

# Submit a fraudulent transaction (high amount + unusual location)
curl -X POST http://localhost:8000/api/v1/transactions/score \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": 9999.99,
    "merchant_name": "Suspicious Shop",
    "merchant_category": "Gaming",
    "transaction_type": "purchase",
    "country": "NG",
    "city": "Lagos",
    "latitude": 6.5244,
    "longitude": 3.3792,
    "device_id": "new_device_xyz",
    "ip_address": "41.203.100.50"
  }'
```

**Response:**
```json
{
  "transaction_id": "abc123...",
  "fraud_score": 85.5,
  "risk_level": "high",
  "is_fraud": true,
  "is_blocked": true,
  "triggered_rules": [
    "high_amount",
    "unusual_location",
    "new_device"
  ],
  "rule_scores": {
    "high_amount": 20,
    "unusual_location": 30,
    "new_device": 15
  },
  "explanation": "This transaction shows multiple fraud indicators...",
  "processing_time_ms": 45.2
}
```

### Method 3: Load Kaggle Dataset

Load real credit card fraud data:

```bash
# 1. Download dataset from Kaggle
# https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

# 2. Place creditcard.csv in backend/data/
cp ~/Downloads/creditcard.csv backend/data/

# 3. Load full dataset (284,807 transactions)
make load-data

# OR load sample (10,000 transactions)
make load-data-sample
```

**What this does:**
- Loads historical fraud data into PostgreSQL
- Enriches with realistic merchant names and locations
- Available for analysis and model validation
- View via `/transactions` page in frontend

### Understanding Fraud Scores

**Score Components:**

1. **Rule Engine (60% weight)**
   - Velocity check: 25 points max
   - High amount: 20 points max
   - Geolocation impossible: 30 points max
   - Unusual time: 10 points max
   - New device: 15 points max
   - Blacklist: 50 points max

2. **Isolation Forest (25% weight)**
   - Unsupervised ML anomaly detection
   - Analyzes 9 features (amount, time, location, velocity)
   - Returns 0-100 score

3. **Azure Anomaly Detector (15% weight)**
   - Time-series anomaly detection
   - Falls back to z-score if not configured
   - Returns 0-100 score

**Risk Levels:**
- **Low** (0-30): Normal transaction
- **Medium** (30-70): Moderate risk
- **High** (70-100): High risk, may be blocked

**Blocking Logic:**
- Score ≥ 80 → Automatically blocked
- Score 70-79 → Flagged for review
- Score < 70 → Approved

---

## Deploying to Azure

### Prerequisites

1. **Azure Account** - https://azure.microsoft.com/free
2. **Azure CLI** - https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
3. **Terraform** - https://www.terraform.io/downloads
4. **kubectl** - https://kubernetes.io/docs/tasks/tools/
5. **Helm** - https://helm.sh/docs/intro/install/

### Step 1: Login to Azure

```bash
az login
az account set --subscription "your-subscription-id"
```

### Step 2: Deploy Infrastructure with Terraform

```bash
cd cloud_infra/terraform/environments/dev

# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
nano terraform.tfvars
```

**Update these values:**
```hcl
acr_name = "frauddetectionacr12345"  # Must be globally unique
postgres_admin_password = "YourStrongPassword123!"
```

**Deploy:**
```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates AKS, ACR, PostgreSQL, Redis)
terraform apply
```

**Wait 10-15 minutes** for infrastructure to be created.

### Step 3: Build and Push Docker Images

```bash
# Login to ACR
az acr login --name frauddetectionacr12345

# Build and push backend
docker build -t frauddetectionacr12345.azurecr.io/fraud-detection-backend:latest ./backend
docker push frauddetectionacr12345.azurecr.io/fraud-detection-backend:latest

# Build and push frontend
docker build -t frauddetectionacr12345.azurecr.io/fraud-detection-frontend:latest ./frontend
docker push frauddetectionacr12345.azurecr.io/fraud-detection-frontend:latest
```

### Step 4: Configure kubectl

```bash
az aks get-credentials \
  --resource-group fraud-detection-dev-rg \
  --name fraud-detection-aks-dev

# Verify connection
kubectl get nodes
```

### Step 5: Create Kubernetes Secrets

```bash
kubectl create namespace fraud-detection

kubectl create secret generic backend-secrets \
  --namespace fraud-detection \
  --from-literal=database-url="postgresql://pgadmin:YourPassword@postgres-host:5432/fraud_detection" \
  --from-literal=redis-host="your-redis.redis.cache.windows.net" \
  --from-literal=redis-port="6380" \
  --from-literal=redis-password="your-redis-key" \
  --from-literal=anthropic-api-key="your-anthropic-key"
```

### Step 6: Deploy with Helm

```bash
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Deploy backend
cd cloud_infra/helm
helm install fraud-detection-backend ./backend \
  --namespace fraud-detection \
  --set image.repository=frauddetectionacr12345.azurecr.io/fraud-detection-backend \
  --set image.tag=latest

# Deploy frontend
helm install fraud-detection-frontend ./frontend \
  --namespace fraud-detection \
  --set image.repository=frauddetectionacr12345.azurecr.io/fraud-detection-frontend \
  --set image.tag=latest
```

### Step 7: Get External IP

```bash
kubectl get service -n ingress-nginx

# Wait for EXTERNAL-IP to be assigned (may take 2-3 minutes)
```

### Step 8: Access Your Application

```bash
# Get the external IP
EXTERNAL_IP=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Frontend: http://$EXTERNAL_IP"
echo "Backend API: http://$EXTERNAL_IP/api"
```

**For production:**
- Configure DNS to point to external IP
- Update Helm values with your domain
- Configure TLS with cert-manager

---

## Troubleshooting

### Local Development Issues

**Problem: Containers won't start**
```bash
# Check logs
make logs

# Restart everything
make restart

# Clean and rebuild
make clean
make init
```

**Problem: Database connection errors**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart just the database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

**Problem: Frontend shows connection error**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

**Problem: WebSocket not connecting**
```bash
# Check backend WebSocket endpoint
curl http://localhost:8000/health

# Check browser console for errors
# Open DevTools → Console

# Verify CORS settings in backend
```

### Deployment Issues

**Problem: Image pull errors in AKS**
```bash
# Verify ACR is attached to AKS
az aks update \
  --resource-group fraud-detection-dev-rg \
  --name fraud-detection-aks-dev \
  --attach-acr frauddetectionacr12345
```

**Problem: Pod crash loop**
```bash
# Check pod logs
kubectl logs -n fraud-detection <pod-name>

# Describe pod for events
kubectl describe pod -n fraud-detection <pod-name>

# Check secrets exist
kubectl get secrets -n fraud-detection
```

**Problem: Ingress not working**
```bash
# Check ingress status
kubectl get ingress -n fraud-detection

# Check ingress controller logs
kubectl logs -n ingress-nginx <controller-pod>

# Verify external IP assigned
kubectl get service -n ingress-nginx
```

### Common Commands

```bash
# View all running containers
make ps

# View resource usage
make stats

# View logs (all services)
make logs

# View logs (specific service)
make logs-backend
make logs-frontend

# Restart all services
make restart

# Clean everything and start fresh
make clean
make init

# Access backend shell
make backend-shell

# Access database
make db-shell

# Run backend tests
make test
```

### Getting Help

1. Check logs first: `make logs`
2. Verify services are running: `make ps`
3. Check API health: http://localhost:8000/health
4. Review documentation in component directories:
   - Backend: `backend/README.md`
   - Frontend: `frontend/README.md`
   - Terraform: `cloud_infra/terraform/README.md`
   - Helm: `cloud_infra/helm/README.md`

---

## Next Steps

Once you have the system running:

1. **Explore the UI**: Navigate through all 4 pages
2. **Generate transactions**: Use `make generate-txns-stream` to see real-time updates
3. **Test fraud scenarios**: Submit high-amount or unusual-location transactions
4. **View analytics**: Check the analytics page for fraud patterns
5. **Load Kaggle data**: Analyze real historical fraud data
6. **Deploy to Azure**: Follow the deployment guide above
7. **Setup CI/CD**: Configure GitHub Actions for automated deployments

## Quick Reference

```bash
# First time setup
make init

# Daily development
make dev              # Start with hot reload
make generate-txns    # Generate test transactions
make logs             # View logs
make down             # Stop everything

# Testing
make test             # Run backend tests
make load-data        # Load Kaggle dataset

# Troubleshooting
make restart          # Restart all services
make clean            # Clean everything
make help             # Show all commands
```

---

**Ready to start? Run `make init` and open http://localhost:3000!**

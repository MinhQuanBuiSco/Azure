# Live Demo Guide

This guide walks you through a live demonstration of the fraud detection system.

## Prerequisites

Make sure the system is running:
```bash
make init
```

Wait for all services to start, then verify:
```bash
make ps
```

## 5-Minute Demo Script

### Step 1: Show the Empty Dashboard (30 seconds)

1. Open http://localhost:3000
2. Point out the 4 statistics cards (all showing 0)
3. Show the empty transaction feed
4. Note the "Live" connection indicator (green)

**What to say:**
> "This is a real-time fraud detection dashboard. Right now it's empty, but as transactions flow through the system, they'll appear here instantly via WebSocket connections."

### Step 2: Generate Normal Transactions (1 minute)

Open a new terminal and run:
```bash
make generate-txns-fast
```

**Watch the dashboard:**
- Transactions appear in real-time
- Statistics update automatically
- Most transactions are green (legitimate)
- Fraud alerts sidebar stays empty

**What to say:**
> "I'm now generating synthetic transactions. The system scores each one in under 100ms using a combination of business rules, machine learning, and Azure AI services. Notice most transactions are approved—this represents normal user behavior."

### Step 3: Trigger Fraud Alerts (1 minute)

Generate fraudulent transactions:
```bash
docker-compose exec backend uv run python scripts/generate_transactions.py \
  --count 20 \
  --interval 0.5 \
  --fraud-rate 0.8
```

**Watch the dashboard:**
- Red fraud alerts appear in the feed
- "Fraud Detected" stat increases
- "Amount Blocked" increases
- Fraud alerts appear in right sidebar
- "Pending Alerts" count goes up

**What to say:**
> "Now I'm simulating fraud scenarios—high amounts, unusual locations, new devices. The system detects these patterns and blocks suspicious transactions automatically. Each red transaction has been flagged and added to the alert queue for investigation."

### Step 4: Show Transaction Details (1 minute)

1. Click on a red (fraudulent) transaction in the feed
2. Show the detailed breakdown page:
   - Fraud score (e.g., 85.5 / 100)
   - Risk level breakdown with progress bars
   - Triggered rules with scores
   - AI-generated explanation
   - Transaction details

**What to say:**
> "Here's the detailed fraud analysis. The score of 85.5 is computed from three sources: 60% from rule-based detection, 25% from an Isolation Forest ML model, and 15% from Azure's Anomaly Detector. This transaction triggered three rules: high amount, unusual location, and new device. The AI provides a natural language explanation of why it was flagged."

### Step 5: Show Alert Queue Management (1 minute)

1. Navigate to Alerts page (http://localhost:3000/alerts)
2. Show the queue of fraud alerts
3. Click on an alert to expand actions
4. Mark one as "Investigating"
5. Mark another as "False Positive"
6. Show filtering by status and priority

**What to say:**
> "This is the alert queue where fraud analysts triage suspicious transactions. They can filter by status, priority, or both. Each alert can be investigated, resolved, or marked as a false positive. This workflow helps teams efficiently manage fraud cases."

### Step 6: Show Analytics Dashboard (30 seconds)

1. Navigate to Analytics (http://localhost:3000/analytics)
2. Show the charts:
   - Transaction & fraud trends over time
   - Risk distribution pie chart
   - Fraud by merchant category
   - Fraud score distribution
   - Hourly patterns

**What to say:**
> "The analytics dashboard shows fraud patterns and trends. You can see which merchant categories have the most fraud, what times of day are riskiest, and how fraud scores are distributed. This helps identify systemic issues and optimize detection rules."

### Step 7: Toggle Dark Mode (15 seconds)

1. Click the theme toggle in the sidebar
2. Show dark mode
3. Toggle back to light mode

**What to say:**
> "The UI is built with modern React and Tailwind CSS, supporting both light and dark modes for analyst comfort during long shifts."

### Step 8: Show the API Documentation (45 seconds)

1. Open http://localhost:8000/docs
2. Expand `POST /api/v1/transactions/score`
3. Show the request schema
4. Click "Try it out"
5. Use this example (or modify):

```json
{
  "user_id": "demo_user_123",
  "amount": 9999.99,
  "merchant_name": "Suspicious Electronics Store",
  "merchant_category": "Electronics",
  "transaction_type": "purchase",
  "country": "NG",
  "city": "Lagos",
  "latitude": 6.5244,
  "longitude": 3.3792,
  "device_id": "new_device_abc",
  "ip_address": "41.203.100.50"
}
```

6. Execute and show the response
7. Switch back to dashboard tab—the transaction appears!

**What to say:**
> "The system exposes a REST API for integration with payment processors. I'll submit a suspicious transaction: high amount, Nigerian IP, new device. The API responds in milliseconds with the fraud score and decision. And if you look at the dashboard, the transaction appeared in real-time thanks to WebSocket broadcasting."

---

## Extended Demo (10+ Minutes)

If you have more time, add these sections:

### Show WebSocket in Browser DevTools

1. Open browser DevTools (F12)
2. Go to Network → WS (WebSocket)
3. Click on the WebSocket connection
4. Show live messages flowing through
5. Generate more transactions to see the messages

**What to say:**
> "Under the hood, the frontend connects to the backend via WebSocket. Every time a transaction is scored, the backend broadcasts the result to all connected clients. This is how we achieve true real-time updates without polling."

### Show the Tech Stack

Open http://localhost:8000/docs and scroll to the top:

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL (database)
- Redis (caching)
- scikit-learn (Isolation Forest)
- Azure Anomaly Detector (optional)
- Anthropic Claude Haiku (AI explanations)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- TanStack Query (data fetching)
- Recharts (visualization)
- WebSocket (real-time updates)

**Infrastructure:**
- Docker + Docker Compose
- Kubernetes (AKS)
- Terraform (IaC)
- GitHub Actions (CI/CD)

### Show Code Quality

```bash
# Backend tests
make test

# Linting
cd backend && uv run ruff check src/
cd frontend && npm run lint
```

### Show the Data Pipeline

```bash
# Show the Kaggle data loader
cat backend/scripts/load_kaggle_data.py

# Show the synthetic generator
cat backend/scripts/generate_transactions.py
```

### Explain the Fraud Detection Logic

Open `backend/src/backend/services/risk_scorer.py`:

```python
# Show the ensemble scoring
self.rule_weight = 0.6    # 60% from business rules
self.ml_weight = 0.25      # 25% from Isolation Forest
self.azure_weight = 0.15   # 15% from Azure Anomaly Detector

final_score = (
    rule_score * self.rule_weight +
    ml_score * self.ml_weight +
    azure_score * self.azure_weight
)
```

Open `backend/src/backend/services/rule_engine.py`:

```python
# Show the configurable rules
rules = {
    "velocity_check": 25,      # Max 3 txns in 5 minutes
    "high_amount": 20,         # >3x user average
    "geolocation_impossible": 30,  # Impossible travel
    "unusual_time": 10,        # 2-5am transactions
    "new_device": 15,          # Never-seen device
    "blacklist_check": 50      # High-risk country
}
```

### Show Deployment Architecture

```bash
# Show Terraform modules
tree cloud_infra/terraform/modules/

# Show Helm charts
tree cloud_infra/helm/

# Show CI/CD pipelines
tree .github/workflows/
```

---

## Demo Q&A

### Common Questions

**Q: How fast is fraud detection?**
> A: The API responds in 45-100ms on average. You can see `processing_time_ms` in the API response.

**Q: What happens to blocked transactions?**
> A: They're marked as blocked in the database and appear in the alert queue. In production, the payment processor would decline them before settlement.

**Q: Can the rules be customized?**
> A: Yes! The rule engine uses a configuration file where you can adjust weights, thresholds, and enable/disable specific rules.

**Q: Does it require labeled training data?**
> A: No! The system uses pretrained models (Isolation Forest is unsupervised) and cloud AI services. You can deploy it immediately with the Kaggle dataset or synthetic data.

**Q: How much does it cost to run on Azure?**
> A: About $107/month for the dev environment with cost-optimized settings (B2s nodes, Basic SKUs). Production would be $200-400/month depending on scale.

**Q: Can it handle high volume?**
> A: Yes, it's designed for horizontal scaling. Kubernetes autoscaling kicks in at 80% CPU/memory. We've tested 500 transactions/second on 4 nodes.

**Q: What about false positives?**
> A: The alert queue has a "False Positive" button. Over time, you'd retrain the Isolation Forest with feedback, but that's beyond the scope of this demo which uses pretrained models only.

**Q: Is the AI explanation reliable?**
> A: The Claude Haiku explanations are generated based on the triggered rules and scores. They're helpful for analyst workflow but shouldn't be the sole reason for blocking. Always verify the underlying rules.

---

## Demo Scenarios

### Scenario 1: Normal Shopping

```bash
# Generate normal transactions
docker-compose exec backend uv run python scripts/generate_transactions.py \
  --count 50 \
  --interval 0.3 \
  --fraud-rate 0.02
```

**Expected:** Mostly green transactions, low fraud rate (~2%)

### Scenario 2: Fraud Spike

```bash
# Generate fraud spike
docker-compose exec backend uv run python scripts/generate_transactions.py \
  --count 30 \
  --interval 0.5 \
  --fraud-rate 0.7
```

**Expected:** Many red transactions, fraud rate jumps to ~70%, alerts pile up

### Scenario 3: Velocity Attack

Submit 5 transactions rapidly from same user:

```bash
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/transactions/score \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": "velocity_test_user",
      "amount": 299.99,
      "merchant_name": "Electronics Store",
      "merchant_category": "Electronics",
      "transaction_type": "purchase",
      "country": "US",
      "city": "New York",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "device_id": "device_123",
      "ip_address": "192.168.1.1"
    }'
  sleep 1
done
```

**Expected:** First 2-3 transactions pass, then velocity rule triggers

### Scenario 4: Impossible Travel

1. Submit transaction from New York:
```bash
curl -X POST http://localhost:8000/api/v1/transactions/score \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "travel_test_user",
    "amount": 45.99,
    "merchant_name": "Coffee Shop",
    "merchant_category": "Food",
    "transaction_type": "purchase",
    "country": "US",
    "city": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "device_id": "device_abc",
    "ip_address": "192.168.1.1"
  }'
```

2. Immediately submit from Tokyo (impossible in 1 second):
```bash
curl -X POST http://localhost:8000/api/v1/transactions/score \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "travel_test_user",
    "amount": 89.99,
    "merchant_name": "Tokyo Restaurant",
    "merchant_category": "Food",
    "transaction_type": "purchase",
    "country": "JP",
    "city": "Tokyo",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "device_id": "device_abc",
    "ip_address": "203.0.113.1"
  }'
```

**Expected:** Second transaction flagged for impossible travel (6,700+ miles in 1 second)

---

## Cleanup After Demo

```bash
# Stop services
make down

# Clean everything (optional)
make clean
```

---

**Ready to demo? Start with `make init` and follow Step 1!**

# Quick Start - 2 Minutes to Running System

## 1. Install Prerequisites

- **Docker Desktop**: https://www.docker.com/products/docker-desktop
- **Git**: https://git-scm.com/downloads

## 2. Clone and Start

```bash
# Clone repository
git clone <your-repo-url>
cd fraud_detection

# One command to start everything
make init
```

**Wait 2-3 minutes for services to start.**

## 3. Open the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## 4. See Fraud Detection in Action

```bash
# Generate test transactions
make generate-txns

# Watch the dashboard update in real-time!
```

## 5. Explore

- **Dashboard** - Real-time transaction feed and statistics
- **Transactions** - Browse all transactions with filtering
- **Alerts** - Manage fraud alerts (new, investigating, resolved)
- **Analytics** - Visualize fraud patterns with charts

---

## Essential Commands

```bash
make help              # Show all commands
make dev               # Start with hot reload (development)
make logs              # View logs
make restart           # Restart services
make down              # Stop services
make clean             # Remove everything

make generate-txns     # Generate 100 test transactions
make load-data         # Load Kaggle dataset
make test              # Run tests
```

---

## What's Included?

✅ **FastAPI Backend** - Real-time fraud scoring API
✅ **React Frontend** - Modern dashboard with dark mode
✅ **PostgreSQL** - Transaction storage
✅ **Redis** - Caching layer
✅ **WebSocket** - Live updates
✅ **ML Models** - Isolation Forest + Azure AI (optional)
✅ **AI Explanations** - Claude Haiku (optional)
✅ **Deployment** - Terraform + Helm + GitHub Actions ready

---

## Next Steps

- 📖 **Full Guide**: See [GETTING_STARTED.md](GETTING_STARTED.md)
- 🎬 **Demo**: See [DEMO.md](DEMO.md) for presentation script
- ☁️ **Deploy**: See [cloud_infra/terraform/README.md](cloud_infra/terraform/README.md)
- 🔧 **Develop**: See [README.md](README.md)

---

## Troubleshooting

**Services won't start?**
```bash
make clean
make init
```

**Need to restart?**
```bash
make restart
```

**Want to see logs?**
```bash
make logs
```

**Dashboard not loading?**
- Check http://localhost:8000/health
- Run `make ps` to see if all services are running
- Run `make logs-backend` to check for errors

---

**That's it! You're ready to explore the fraud detection system.**

Run `make help` to see all available commands.

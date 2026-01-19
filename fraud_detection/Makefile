.PHONY: help build up down logs restart clean test backend-shell frontend-shell db-migrate db-upgrade

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Backend:  http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Docs:     http://localhost:8000/docs"

dev: ## Start services in development mode with hot reload
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes
	docker-compose down -v

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

restart: ## Restart all services
	docker-compose restart

restart-backend: ## Restart backend service
	docker-compose restart backend

restart-frontend: ## Restart frontend service
	docker-compose restart frontend

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

test: ## Run backend tests
	docker-compose exec backend pytest

backend-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

frontend-shell: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d fraud_detection

db-migrate: ## Create new Alembic migration
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Apply database migrations
	docker-compose exec backend alembic upgrade head

db-downgrade: ## Rollback last migration
	docker-compose exec backend alembic downgrade -1

load-data: ## Load Kaggle dataset into database
	docker-compose exec backend python scripts/load_kaggle_data.py --csv-path data/creditcard.csv

load-data-sample: ## Load sample of Kaggle data (10k transactions for testing)
	docker-compose exec backend python scripts/load_kaggle_data.py --csv-path data/creditcard.csv --limit 10000

generate-txns: ## Generate synthetic transactions (100 txns, 10% fraud rate)
	docker-compose exec backend python scripts/generate_transactions.py --count 100 --fraud-rate 0.10

generate-txns-fast: ## Generate transactions quickly (1 per 0.5s)
	docker-compose exec backend python scripts/generate_transactions.py --count 50 --interval 0.5 --fraud-rate 0.15

generate-txns-stream: ## Generate continuous stream (useful for testing WebSocket)
	docker-compose exec backend python scripts/generate_transactions.py --count 1000 --interval 2.0 --fraud-rate 0.10

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats

prune: ## Remove unused Docker resources
	docker system prune -af --volumes

init: ## Initialize the project (first time setup)
	@echo "🚀 Initializing Fraud Detection System..."
	@cp backend/.env.example backend/.env 2>/dev/null || true
	@cp frontend/.env.example frontend/.env 2>/dev/null || true
	@echo "📦 Building Docker images..."
	@docker-compose build
	@echo "🗄️  Starting services..."
	@docker-compose up -d
	@echo "⏳ Waiting for database..."
	@sleep 5
	@echo "🔄 Running database migrations..."
	@docker-compose exec backend alembic upgrade head
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Access the application:"
	@echo "  Backend API:  http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/docs"
	@echo "  Frontend:     http://localhost:3000"

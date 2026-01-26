#!/bin/bash
set -e

# =============================================================================
# Finance Research Pipeline - Local Deployment Script
# =============================================================================
# This script deploys the application locally using Docker Compose
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env exists
if [ ! -f ".env" ]; then
    log_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_warning "Please edit .env with your API keys before running again."
        exit 1
    else
        log_error ".env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check required environment variables
source .env

if [ "$LLM_PROVIDER" = "azure_openai" ]; then
    if [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_API_KEY" ]; then
        log_error "Azure OpenAI credentials not set in .env"
        log_info "Either set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
        log_info "Or change LLM_PROVIDER to 'openai' and set OPENAI_API_KEY"
        exit 1
    fi
elif [ "$LLM_PROVIDER" = "openai" ]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "OPENAI_API_KEY not set in .env"
        exit 1
    fi
elif [ "$LLM_PROVIDER" = "anthropic" ]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log_error "ANTHROPIC_API_KEY not set in .env"
        exit 1
    fi
fi

# Parse arguments
DEV_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --down)
            log_info "Stopping containers..."
            docker-compose down
            exit 0
            ;;
        --logs)
            docker-compose logs -f
            exit 0
            ;;
        *)
            echo "Usage: $0 [--dev] [--down] [--logs]"
            echo "  --dev   Use development mode with hot-reload"
            echo "  --down  Stop all containers"
            echo "  --logs  Follow container logs"
            exit 1
            ;;
    esac
done

# Stop any existing containers
log_info "Stopping any existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Build and start
if [ "$DEV_MODE" = true ]; then
    log_info "Starting in DEVELOPMENT mode (hot-reload enabled)..."
    docker-compose -f docker-compose.dev.yml up --build -d

    echo ""
    log_success "Development environment started!"
    echo ""
    echo -e "${BLUE}Frontend:${NC}  http://localhost:5173"
    echo -e "${BLUE}Backend:${NC}   http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC}  http://localhost:8000/docs"
    echo ""
    log_info "Hot-reload enabled - changes to source files will auto-refresh"
    log_info "Run './local-deploy.sh --logs' to view logs"
else
    log_info "Starting in PRODUCTION mode..."
    docker-compose up --build -d

    echo ""
    log_success "Production environment started!"
    echo ""
    echo -e "${BLUE}Frontend:${NC}  http://localhost"
    echo -e "${BLUE}Backend:${NC}   http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC}  http://localhost:8000/docs"
    echo ""
    log_info "Run './local-deploy.sh --logs' to view logs"
fi

echo ""
log_info "To stop: ./local-deploy.sh --down"

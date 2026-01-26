#!/bin/bash
set -e

# =============================================================================
# Finance Research Pipeline - Full Azure Deployment Script
# =============================================================================
# This script deploys the complete infrastructure and application to Azure:
# - Azure OpenAI (GPT-4o)
# - Azure Container Registry
# - Azure Cache for Redis
# - Azure Cosmos DB
# - Azure Container Apps (Backend + Frontend)
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Edit these as needed
PROJECT_NAME="${PROJECT_NAME:-finance-research}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${PROJECT_NAME}-rg-${ENVIRONMENT}"

# Derived names
OPENAI_NAME="${PROJECT_NAME}-openai-${ENVIRONMENT}"
ACR_NAME="${PROJECT_NAME//-/}acr${ENVIRONMENT}"  # ACR names must be alphanumeric
REDIS_NAME="${PROJECT_NAME}-redis-${ENVIRONMENT}"
COSMOS_NAME="${PROJECT_NAME}-cosmos-${ENVIRONMENT}"
CONTAINER_ENV_NAME="${PROJECT_NAME}-env-${ENVIRONMENT}"
BACKEND_APP_NAME="${PROJECT_NAME}-backend-${ENVIRONMENT}"
FRONTEND_APP_NAME="${PROJECT_NAME}-frontend-${ENVIRONMENT}"

# API Keys (set via environment or .env file)
TAVILY_API_KEY="${TAVILY_API_KEY:-}"
NEWSAPI_KEY="${NEWSAPI_KEY:-}"

# =============================================================================
# Helper Functions
# =============================================================================

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

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is required but not installed."
        exit 1
    fi
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_checks() {
    log_info "Running pre-flight checks..."

    check_command az
    check_command docker

    # Check Azure login
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Run 'az login' first."
        exit 1
    fi

    # Load .env file if exists
    if [ -f ".env" ]; then
        log_info "Loading environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    fi

    # Check required API keys
    if [ -z "$TAVILY_API_KEY" ]; then
        log_warning "TAVILY_API_KEY not set. Web search will not work."
    fi

    if [ -z "$NEWSAPI_KEY" ]; then
        log_warning "NEWSAPI_KEY not set. News search will not work."
    fi

    log_success "Pre-flight checks passed"
}

# =============================================================================
# Resource Group
# =============================================================================

create_resource_group() {
    log_info "Creating resource group: $RESOURCE_GROUP..."

    if az group show --name $RESOURCE_GROUP &> /dev/null; then
        log_info "Resource group already exists"
    else
        az group create \
            --name $RESOURCE_GROUP \
            --location $LOCATION \
            --output none
        log_success "Resource group created"
    fi
}

# =============================================================================
# Azure OpenAI
# =============================================================================

deploy_azure_openai() {
    log_info "Deploying Azure OpenAI: $OPENAI_NAME..."

    # Check if OpenAI resource exists
    if az cognitiveservices account show --name $OPENAI_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        log_info "Azure OpenAI resource already exists"
    else
        az cognitiveservices account create \
            --name $OPENAI_NAME \
            --resource-group $RESOURCE_GROUP \
            --location $LOCATION \
            --kind OpenAI \
            --sku S0 \
            --custom-domain $OPENAI_NAME \
            --output none
        log_success "Azure OpenAI resource created"
    fi

    # Deploy GPT-4o model
    log_info "Deploying GPT-4o model..."
    if az cognitiveservices account deployment show \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --deployment-name gpt-4o &> /dev/null; then
        log_info "GPT-4o deployment already exists"
    else
        az cognitiveservices account deployment create \
            --name $OPENAI_NAME \
            --resource-group $RESOURCE_GROUP \
            --deployment-name gpt-4o \
            --model-name gpt-4o \
            --model-version "2024-08-06" \
            --model-format OpenAI \
            --sku-capacity 10 \
            --sku-name Standard \
            --output none
        log_success "GPT-4o model deployed"
    fi

    # Get credentials
    AZURE_OPENAI_ENDPOINT=$(az cognitiveservices account show \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.endpoint" -o tsv)

    AZURE_OPENAI_API_KEY=$(az cognitiveservices account keys list \
        --name $OPENAI_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "key1" -o tsv)

    log_success "Azure OpenAI deployed: $AZURE_OPENAI_ENDPOINT"
}

# =============================================================================
# Azure Container Registry
# =============================================================================

deploy_acr() {
    log_info "Deploying Azure Container Registry: $ACR_NAME..."

    if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        log_info "ACR already exists"
    else
        az acr create \
            --name $ACR_NAME \
            --resource-group $RESOURCE_GROUP \
            --location $LOCATION \
            --sku Basic \
            --admin-enabled true \
            --output none
        log_success "ACR created"
    fi

    # Get ACR credentials
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query "loginServer" -o tsv)
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

    log_success "ACR deployed: $ACR_LOGIN_SERVER"
}

# =============================================================================
# Azure Cache for Redis
# =============================================================================

deploy_redis() {
    log_info "Deploying Azure Cache for Redis: $REDIS_NAME..."

    if az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        log_info "Redis already exists"
    else
        az redis create \
            --name $REDIS_NAME \
            --resource-group $RESOURCE_GROUP \
            --location $LOCATION \
            --sku Basic \
            --vm-size c0 \
            --output none
        log_success "Redis created (this may take a few minutes to provision)"
    fi

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    while true; do
        STATUS=$(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query "provisioningState" -o tsv)
        if [ "$STATUS" == "Succeeded" ]; then
            break
        fi
        echo -n "."
        sleep 10
    done
    echo ""

    # Get Redis credentials
    REDIS_HOST=$(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query "hostName" -o tsv)
    REDIS_PASSWORD=$(az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query "primaryKey" -o tsv)
    REDIS_PORT="6380"
    REDIS_SSL="true"

    log_success "Redis deployed: $REDIS_HOST"
}

# =============================================================================
# Azure Cosmos DB
# =============================================================================

deploy_cosmos_db() {
    log_info "Deploying Azure Cosmos DB: $COSMOS_NAME..."

    if az cosmosdb show --name $COSMOS_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        log_info "Cosmos DB already exists"
    else
        az cosmosdb create \
            --name $COSMOS_NAME \
            --resource-group $RESOURCE_GROUP \
            --locations regionName=$LOCATION \
            --default-consistency-level Session \
            --output none
        log_success "Cosmos DB account created"
    fi

    # Create database
    log_info "Creating Cosmos DB database..."
    az cosmosdb sql database create \
        --account-name $COSMOS_NAME \
        --resource-group $RESOURCE_GROUP \
        --name finance_research \
        --output none 2>/dev/null || true

    # Create containers
    log_info "Creating Cosmos DB containers..."
    az cosmosdb sql container create \
        --account-name $COSMOS_NAME \
        --resource-group $RESOURCE_GROUP \
        --database-name finance_research \
        --name sessions \
        --partition-key-path "/research_id" \
        --output none 2>/dev/null || true

    az cosmosdb sql container create \
        --account-name $COSMOS_NAME \
        --resource-group $RESOURCE_GROUP \
        --database-name finance_research \
        --name reports \
        --partition-key-path "/research_id" \
        --output none 2>/dev/null || true

    # Get Cosmos DB credentials
    COSMOS_ENDPOINT=$(az cosmosdb show --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query "documentEndpoint" -o tsv)
    COSMOS_KEY=$(az cosmosdb keys list --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query "primaryMasterKey" -o tsv)

    log_success "Cosmos DB deployed: $COSMOS_ENDPOINT"
}

# =============================================================================
# Build and Push Docker Images
# =============================================================================

build_and_push_images() {
    log_info "Building and pushing Docker images..."

    # Login to ACR
    az acr login --name $ACR_NAME

    # Build for linux/amd64 (required for Azure Container Apps)
    # This is needed when building on Apple Silicon Macs
    PLATFORM="linux/amd64"

    # Build and push backend
    log_info "Building backend image for $PLATFORM..."
    docker buildx build --platform $PLATFORM -t $ACR_LOGIN_SERVER/backend:latest --push ./backend
    log_success "Backend image pushed"

    # Build and push frontend
    log_info "Building frontend image for $PLATFORM..."
    docker buildx build --platform $PLATFORM -t $ACR_LOGIN_SERVER/frontend:latest --push ./frontend
    log_success "Frontend image pushed"
}

# =============================================================================
# Azure Container Apps
# =============================================================================

deploy_container_apps() {
    log_info "Deploying Azure Container Apps..."

    # Create Container Apps Environment
    if az containerapp env show --name $CONTAINER_ENV_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        log_info "Container Apps Environment already exists"
    else
        log_info "Creating Container Apps Environment..."
        az containerapp env create \
            --name $CONTAINER_ENV_NAME \
            --resource-group $RESOURCE_GROUP \
            --location $LOCATION \
            --output none
        log_success "Container Apps Environment created"
    fi

    # Deploy Backend
    log_info "Deploying backend container app..."
    az containerapp create \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_ENV_NAME \
        --image $ACR_LOGIN_SERVER/backend:latest \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port 8000 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 1.0 \
        --memory 2.0Gi \
        --env-vars \
            "ENVIRONMENT=production" \
            "DEBUG=false" \
            "LOG_LEVEL=INFO" \
            "LOG_FORMAT=json" \
            "LLM_PROVIDER=azure_openai" \
            "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
            "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY" \
            "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o" \
            "TAVILY_API_KEY=$TAVILY_API_KEY" \
            "NEWSAPI_KEY=$NEWSAPI_KEY" \
            "REDIS_HOST=$REDIS_HOST" \
            "REDIS_PORT=$REDIS_PORT" \
            "REDIS_PASSWORD=$REDIS_PASSWORD" \
            "REDIS_SSL=$REDIS_SSL" \
            "COSMOS_ENDPOINT=$COSMOS_ENDPOINT" \
            "COSMOS_KEY=$COSMOS_KEY" \
        --output none 2>/dev/null || \
    az containerapp update \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_LOGIN_SERVER/backend:latest \
        --set-env-vars \
            "ENVIRONMENT=production" \
            "DEBUG=false" \
            "LOG_LEVEL=INFO" \
            "LOG_FORMAT=json" \
            "LLM_PROVIDER=azure_openai" \
            "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
            "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY" \
            "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o" \
            "TAVILY_API_KEY=$TAVILY_API_KEY" \
            "NEWSAPI_KEY=$NEWSAPI_KEY" \
            "REDIS_HOST=$REDIS_HOST" \
            "REDIS_PORT=$REDIS_PORT" \
            "REDIS_PASSWORD=$REDIS_PASSWORD" \
            "REDIS_SSL=$REDIS_SSL" \
            "COSMOS_ENDPOINT=$COSMOS_ENDPOINT" \
            "COSMOS_KEY=$COSMOS_KEY" \
        --output none

    # Get backend URL
    BACKEND_URL=$(az containerapp show \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.configuration.ingress.fqdn" -o tsv)
    BACKEND_URL="https://$BACKEND_URL"

    log_success "Backend deployed: $BACKEND_URL"

    # Deploy Frontend
    log_info "Deploying frontend container app..."
    az containerapp create \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_ENV_NAME \
        --image $ACR_LOGIN_SERVER/frontend:latest \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port 80 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1.0Gi \
        --env-vars "BACKEND_URL=$BACKEND_URL" \
        --output none 2>/dev/null || \
    az containerapp update \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_LOGIN_SERVER/frontend:latest \
        --set-env-vars "BACKEND_URL=$BACKEND_URL" \
        --output none

    # Get frontend URL
    FRONTEND_URL=$(az containerapp show \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.configuration.ingress.fqdn" -o tsv)
    FRONTEND_URL="https://$FRONTEND_URL"

    log_success "Frontend deployed: $FRONTEND_URL"

    # Update backend CORS with frontend URL
    log_info "Updating backend CORS settings..."
    az containerapp update \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --set-env-vars "CORS_ORIGINS=[\"$FRONTEND_URL\"]" \
        --output none
}

# =============================================================================
# Output Summary
# =============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}=============================================================================${NC}"
    echo -e "${GREEN}                    DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}=============================================================================${NC}"
    echo ""
    echo -e "${BLUE}Frontend URL:${NC}     $FRONTEND_URL"
    echo -e "${BLUE}Backend API:${NC}      $BACKEND_URL"
    echo -e "${BLUE}API Docs:${NC}         $BACKEND_URL/docs"
    echo ""
    echo -e "${YELLOW}Azure Resources:${NC}"
    echo "  - Resource Group:  $RESOURCE_GROUP"
    echo "  - Azure OpenAI:    $OPENAI_NAME"
    echo "  - Container Reg:   $ACR_NAME"
    echo "  - Redis Cache:     $REDIS_NAME"
    echo "  - Cosmos DB:       $COSMOS_NAME"
    echo "  - Container Env:   $CONTAINER_ENV_NAME"
    echo ""
    echo -e "${YELLOW}To update your local .env file:${NC}"
    echo "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT"
    echo "AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY"
    echo "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o"
    echo ""
    echo -e "${GREEN}=============================================================================${NC}"
}

# =============================================================================
# Cleanup Function
# =============================================================================

cleanup() {
    echo ""
    log_warning "To delete all resources, run:"
    echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "       Finance Research Pipeline - Azure Deployment"
    echo "============================================================================="
    echo -e "${NC}"

    preflight_checks
    create_resource_group
    deploy_azure_openai
    deploy_acr
    deploy_redis
    deploy_cosmos_db
    build_and_push_images
    deploy_container_apps
    print_summary
    cleanup
}

# Run main function
main "$@"

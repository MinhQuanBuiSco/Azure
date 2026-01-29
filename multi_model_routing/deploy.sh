#!/bin/bash
set -e

#######################################
# Multi-Model LLM Router - One-Click Deployment
#######################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-eastus2}"
PROJECT_NAME="${PROJECT_NAME:-llm-router}"

# Derived names
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"
ACR_NAME="${PROJECT_NAME//-/}${ENVIRONMENT}acr"
CONTAINER_APP_ENV="${PROJECT_NAME}-${ENVIRONMENT}-cae"
BACKEND_APP="${PROJECT_NAME}-${ENVIRONMENT}-backend"
FRONTEND_APP="${PROJECT_NAME}-${ENVIRONMENT}-frontend"

# Image tag
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
BACKEND_IMAGE="${ACR_NAME}.azurecr.io/llm-router-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${ACR_NAME}.azurecr.io/llm-router-frontend:${IMAGE_TAG}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

#######################################
# Helper functions
#######################################

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_prerequisites() {
    log_info "Checking prerequisites..."

    command -v az &> /dev/null || { log_error "Azure CLI not found"; exit 1; }
    command -v docker &> /dev/null || { log_error "Docker not found"; exit 1; }
    command -v terraform &> /dev/null || { log_error "Terraform not found"; exit 1; }
    az account show &> /dev/null || { log_error "Not logged into Azure. Run: az login"; exit 1; }

    log_success "Prerequisites OK"
}

#######################################
# Main deployment function
#######################################

deploy_all() {
    log_info "========================================="
    log_info "Deploying Multi-Model LLM Router"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Location: ${LOCATION}"
    log_info "========================================="

    # Step 1: Terraform - Deploy all Azure infrastructure
    log_info "[1/6] Deploying infrastructure with Terraform..."
    cd cloud_infra/environments/dev

    # Create tfvars if not exists
    if [[ ! -f terraform.tfvars ]]; then
        SUBSCRIPTION_ID=$(az account show --query id -o tsv)
        cat > terraform.tfvars <<EOF
subscription_id = "${SUBSCRIPTION_ID}"
location        = "${LOCATION}"
environment     = "${ENVIRONMENT}"
project_name    = "${PROJECT_NAME}"
EOF
        log_info "Created terraform.tfvars"
    fi

    terraform init -upgrade
    terraform apply -auto-approve

    # Get outputs
    FOUNDRY_RESOURCE_NAME=$(terraform output -raw foundry_resource_name)
    FOUNDRY_API_KEY=$(terraform output -raw foundry_api_key)
    REDIS_URL=$(terraform output -raw redis_url)
    COSMOS_ENDPOINT=$(terraform output -raw cosmos_endpoint)
    COSMOS_KEY=$(terraform output -raw cosmos_key)

    cd "${SCRIPT_DIR}"
    log_success "Infrastructure deployed"

    # Step 2: Create ACR
    log_info "[2/6] Creating Container Registry..."
    if ! az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
        az acr create \
            --resource-group "${RESOURCE_GROUP}" \
            --name "${ACR_NAME}" \
            --sku Basic \
            --admin-enabled true \
            --output none
    fi
    az acr login --name "${ACR_NAME}"
    log_success "Container Registry ready"

    # Step 3: Build Docker images
    log_info "[3/6] Building Docker images..."
    docker build --platform linux/amd64 -t "${BACKEND_IMAGE}" -f backend/Dockerfile backend/
    docker build --platform linux/amd64 -t "${FRONTEND_IMAGE}" -f frontend/Dockerfile frontend/
    log_success "Images built"

    # Step 4: Push images
    log_info "[4/6] Pushing images to ACR..."
    docker push "${BACKEND_IMAGE}"
    docker push "${FRONTEND_IMAGE}"
    log_success "Images pushed"

    # Step 5: Deploy Backend
    log_info "[5/6] Deploying backend..."
    if ! az containerapp env show --name "${CONTAINER_APP_ENV}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
        az containerapp env create \
            --name "${CONTAINER_APP_ENV}" \
            --resource-group "${RESOURCE_GROUP}" \
            --location "${LOCATION}" \
            --output none
    fi

    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name "${ACR_NAME}" --query "username" -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "${ACR_NAME}" --query "passwords[0].value" -o tsv)

    if az containerapp show --name "${BACKEND_APP}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
        # Ensure registry is configured, then update
        az containerapp registry set \
            --name "${BACKEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --server "${ACR_NAME}.azurecr.io" \
            --username "${ACR_USERNAME}" \
            --password "${ACR_PASSWORD}" \
            --output none
        az containerapp update \
            --name "${BACKEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --image "${BACKEND_IMAGE}" \
            --set-env-vars \
                ENVIRONMENT=production \
                LOG_LEVEL=INFO \
                FOUNDRY_RESOURCE_NAME="${FOUNDRY_RESOURCE_NAME}" \
                FOUNDRY_API_KEY="${FOUNDRY_API_KEY}" \
                REDIS_URL="${REDIS_URL}" \
                COSMOS_ENDPOINT="${COSMOS_ENDPOINT}" \
                COSMOS_KEY="${COSMOS_KEY}" \
            --output none
    else
        az containerapp create \
            --name "${BACKEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --environment "${CONTAINER_APP_ENV}" \
            --image "${BACKEND_IMAGE}" \
            --registry-server "${ACR_NAME}.azurecr.io" \
            --registry-username "${ACR_USERNAME}" \
            --registry-password "${ACR_PASSWORD}" \
            --target-port 8000 \
            --ingress external \
            --min-replicas 1 \
            --max-replicas 10 \
            --cpu 0.5 \
            --memory 1.0Gi \
            --env-vars \
                ENVIRONMENT=production \
                LOG_LEVEL=INFO \
                FOUNDRY_RESOURCE_NAME="${FOUNDRY_RESOURCE_NAME}" \
                FOUNDRY_API_KEY="${FOUNDRY_API_KEY}" \
                REDIS_URL="${REDIS_URL}" \
                COSMOS_ENDPOINT="${COSMOS_ENDPOINT}" \
                COSMOS_KEY="${COSMOS_KEY}" \
            --output none
    fi

    BACKEND_FQDN=$(az containerapp show \
        --name "${BACKEND_APP}" \
        --resource-group "${RESOURCE_GROUP}" \
        --query "properties.configuration.ingress.fqdn" -o tsv)
    log_success "Backend deployed: https://${BACKEND_FQDN}"

    # Step 6: Deploy Frontend
    log_info "[6/6] Deploying frontend..."
    BACKEND_URL="https://${BACKEND_FQDN}"

    if az containerapp show --name "${FRONTEND_APP}" --resource-group "${RESOURCE_GROUP}" &> /dev/null; then
        az containerapp registry set \
            --name "${FRONTEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --server "${ACR_NAME}.azurecr.io" \
            --username "${ACR_USERNAME}" \
            --password "${ACR_PASSWORD}" \
            --output none
        az containerapp update \
            --name "${FRONTEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --image "${FRONTEND_IMAGE}" \
            --set-env-vars BACKEND_URL="${BACKEND_URL}" \
            --output none
    else
        az containerapp create \
            --name "${FRONTEND_APP}" \
            --resource-group "${RESOURCE_GROUP}" \
            --environment "${CONTAINER_APP_ENV}" \
            --image "${FRONTEND_IMAGE}" \
            --registry-server "${ACR_NAME}.azurecr.io" \
            --registry-username "${ACR_USERNAME}" \
            --registry-password "${ACR_PASSWORD}" \
            --target-port 80 \
            --ingress external \
            --min-replicas 1 \
            --max-replicas 5 \
            --cpu 0.25 \
            --memory 0.5Gi \
            --env-vars BACKEND_URL="${BACKEND_URL}" \
            --output none
    fi

    FRONTEND_FQDN=$(az containerapp show \
        --name "${FRONTEND_APP}" \
        --resource-group "${RESOURCE_GROUP}" \
        --query "properties.configuration.ingress.fqdn" -o tsv)
    log_success "Frontend deployed: https://${FRONTEND_FQDN}"

    # Done!
    echo ""
    log_success "========================================="
    log_success "Deployment Complete!"
    log_success "========================================="
    echo ""
    echo -e "Frontend:  ${GREEN}https://${FRONTEND_FQDN}${NC}"
    echo -e "Backend:   ${GREEN}https://${BACKEND_FQDN}${NC}"
    echo -e "API:       ${GREEN}https://${BACKEND_FQDN}/docs${NC}"
    echo ""
}

#######################################
# Other commands
#######################################

show_status() {
    echo ""
    log_info "Deployment Status: ${ENVIRONMENT}"
    echo "─────────────────────────────────────────"

    echo -n "Resource Group:  "
    az group show --name "${RESOURCE_GROUP}" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "Not found"

    echo -n "AI Services:     "
    az cognitiveservices account show --name "${PROJECT_NAME}-${ENVIRONMENT}-ai" --resource-group "${RESOURCE_GROUP}" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "Not found"

    echo -n "Redis:           "
    az redis show --name "${PROJECT_NAME}-${ENVIRONMENT}-redis" --resource-group "${RESOURCE_GROUP}" --query "provisioningState" -o tsv 2>/dev/null || echo "Not found"

    echo -n "Cosmos DB:       "
    az cosmosdb show --name "${PROJECT_NAME}-${ENVIRONMENT}-cosmos" --resource-group "${RESOURCE_GROUP}" --query "provisioningState" -o tsv 2>/dev/null || echo "Not found"

    echo -n "Backend:         "
    BACKEND_FQDN=$(az containerapp show --name "${BACKEND_APP}" --resource-group "${RESOURCE_GROUP}" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null) && echo "https://${BACKEND_FQDN}" || echo "Not found"

    echo -n "Frontend:        "
    FRONTEND_FQDN=$(az containerapp show --name "${FRONTEND_APP}" --resource-group "${RESOURCE_GROUP}" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null) && echo "https://${FRONTEND_FQDN}" || echo "Not found"

    echo ""
}

show_logs() {
    az containerapp logs show \
        --name "${BACKEND_APP}" \
        --resource-group "${RESOURCE_GROUP}" \
        --follow
}

show_help() {
    echo "Multi-Model LLM Router - Deployment"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  deploy    Deploy everything (default) - Terraform + Docker + Container Apps"
    echo "  status    Show deployment status"
    echo "  logs      Stream backend logs"
    echo "  help      Show this help"
    echo ""
    echo "To destroy resources, use: ./cleanup.sh"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT   Environment name (default: dev)"
    echo "  LOCATION      Azure region (default: eastus2)"
    echo "  PROJECT_NAME  Project name (default: llm-router)"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh                        # Deploy everything"
    echo "  ENVIRONMENT=prod ./deploy.sh       # Deploy to production"
}

#######################################
# Main
#######################################

case "${1:-deploy}" in
    deploy|all)
        check_prerequisites
        deploy_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

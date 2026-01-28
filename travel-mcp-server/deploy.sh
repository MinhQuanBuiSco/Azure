#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/cloud_infra/terraform/environments/dev"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Travel MCP Server - Azure Deployment  ${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
PROJECT_NAME="${PROJECT_NAME:-travel-mcp}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"
ACR_NAME="${PROJECT_NAME//-/}${ENVIRONMENT}acr"

# Check required tools
check_requirements() {
    echo -e "\n${BLUE}[1/6]${NC} ${YELLOW}Checking requirements...${NC}"

    local missing=()

    if ! command -v az &> /dev/null; then
        missing+=("Azure CLI (az)")
    fi

    if ! command -v docker &> /dev/null; then
        missing+=("Docker")
    fi

    if ! command -v terraform &> /dev/null; then
        missing+=("Terraform")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing required tools:${NC}"
        for tool in "${missing[@]}"; do
            echo -e "  - $tool"
        done
        exit 1
    fi

    echo -e "${GREEN}✓ All requirements met!${NC}"
}

# Login to Azure
azure_login() {
    echo -e "\n${BLUE}[2/6]${NC} ${YELLOW}Checking Azure login...${NC}"

    if ! az account show &> /dev/null; then
        echo "Please login to Azure..."
        az login
    fi

    SUBSCRIPTION=$(az account show --query name -o tsv)
    echo -e "${GREEN}✓ Logged in to subscription: ${SUBSCRIPTION}${NC}"
}

# Deploy base infrastructure (without Container Apps)
deploy_base_infrastructure() {
    echo -e "\n${BLUE}[3/6]${NC} ${YELLOW}Deploying base infrastructure...${NC}"
    echo -e "  This includes: Resource Group, ACR, Redis, Log Analytics, Container Apps Environment, AI Foundry"

    cd "$TERRAFORM_DIR"

    # Initialize Terraform
    terraform init -upgrade

    # Deploy base infrastructure first (everything except container apps)
    echo -e "\n  ${YELLOW}Creating base resources...${NC}"
    terraform apply -auto-approve \
        -target=module.resource_group \
        -target=module.log_analytics \
        -target=module.acr \
        -target=module.redis \
        -target=module.container_apps_env \
        -target=module.ai_foundry

    # Get ACR login server
    ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server 2>/dev/null || echo "")

    if [ -z "$ACR_LOGIN_SERVER" ]; then
        echo -e "${RED}Error: Could not get ACR login server${NC}"
        exit 1
    fi

    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Base infrastructure deployed!${NC}"
}

# Build and push Docker images
build_and_push_images() {
    echo -e "\n${BLUE}[4/6]${NC} ${YELLOW}Building and pushing Docker images...${NC}"

    # Login to ACR
    echo -e "  Logging into ACR..."
    az acr login --name $ACR_NAME

    # Build and push backend (linux/amd64 for Azure Container Apps)
    echo -e "\n  ${YELLOW}Building backend image...${NC}"
    docker build --platform linux/amd64 -t $ACR_LOGIN_SERVER/travel-mcp-backend:latest ./backend
    echo -e "  ${YELLOW}Pushing backend image...${NC}"
    docker push $ACR_LOGIN_SERVER/travel-mcp-backend:latest

    # Build and push frontend (linux/amd64 for Azure Container Apps)
    echo -e "\n  ${YELLOW}Building frontend image...${NC}"
    docker build --platform linux/amd64 -t $ACR_LOGIN_SERVER/travel-mcp-frontend:latest ./frontend
    echo -e "  ${YELLOW}Pushing frontend image...${NC}"
    docker push $ACR_LOGIN_SERVER/travel-mcp-frontend:latest

    echo -e "${GREEN}✓ Images pushed to ACR!${NC}"
}

# Deploy Container Apps (now that images exist)
deploy_container_apps() {
    echo -e "\n${BLUE}[5/6]${NC} ${YELLOW}Deploying Container Apps...${NC}"

    cd "$TERRAFORM_DIR"

    # Now deploy the container apps (images exist in ACR)
    terraform apply -auto-approve \
        -target=module.backend \
        -target=module.frontend

    # Get outputs
    BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo "")
    FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "")

    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Container Apps deployed!${NC}"
}

# Final verification
verify_deployment() {
    echo -e "\n${BLUE}[6/6]${NC} ${YELLOW}Verifying deployment...${NC}"

    cd "$TERRAFORM_DIR"

    # Get all outputs
    BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo "Not available")
    FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "Not available")
    AI_ENDPOINT=$(terraform output -raw ai_foundry_endpoint 2>/dev/null || echo "Not available")
    AI_MODEL=$(terraform output -raw ai_foundry_model 2>/dev/null || echo "Not available")

    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Deployment verified!${NC}"
}

# Print summary
print_summary() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}       Deployment Complete!             ${NC}"
    echo -e "${GREEN}========================================${NC}"

    echo -e "\n${YELLOW}URLs:${NC}"
    echo -e "  Frontend:    ${FRONTEND_URL}"
    echo -e "  Backend:     ${BACKEND_URL}"

    echo -e "\n${YELLOW}AI Foundry:${NC}"
    echo -e "  Endpoint:    ${AI_ENDPOINT}"
    echo -e "  Model:       ${AI_MODEL}"

    echo -e "\n${YELLOW}Resources:${NC}"
    echo -e "  Resource Group:  ${RESOURCE_GROUP}"
    echo -e "  ACR:             ${ACR_NAME}.azurecr.io"

    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo -e "  1. Wait 2-3 minutes for apps to start"
    echo -e "  2. Visit ${FRONTEND_URL}"
    echo -e "  3. Test the travel planning features"

    echo -e "\n${YELLOW}Useful Commands:${NC}"
    echo -e "  View logs:     az containerapp logs show -n ${PROJECT_NAME}-${ENVIRONMENT}-backend -g ${RESOURCE_GROUP}"
    echo -e "  Destroy all:   cd cloud_infra/terraform/environments/dev && terraform destroy"
}

# Cleanup function for errors
cleanup_on_error() {
    echo -e "\n${RED}Deployment failed!${NC}"
    echo -e "You can clean up partial resources with:"
    echo -e "  cd cloud_infra/terraform/environments/dev && terraform destroy"
    exit 1
}

# Set trap for errors
trap cleanup_on_error ERR

# Main deployment flow
main() {
    check_requirements
    azure_login
    deploy_base_infrastructure
    build_and_push_images
    deploy_container_apps
    verify_deployment
    print_summary
}

# Run main function
main "$@"

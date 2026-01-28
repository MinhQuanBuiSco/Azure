#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}  Travel MCP Server - Cleanup           ${NC}"
echo -e "${RED}========================================${NC}"

# Configuration
PROJECT_NAME="${PROJECT_NAME:-travel-mcp}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"

# Parse arguments
AZURE_ONLY=false
LOCAL_ONLY=false
FORCE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --azure-only) AZURE_ONLY=true ;;
        --local-only) LOCAL_ONLY=true ;;
        --force|-f) FORCE=true ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --azure-only    Only clean up Azure resources"
            echo "  --local-only    Only clean up local Docker resources"
            echo "  --force, -f     Skip confirmation prompts"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Confirmation prompt
confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    read -p "Are you sure you want to proceed? (y/N) " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Clean up Azure resources
cleanup_azure() {
    echo -e "\n${YELLOW}Cleaning up Azure resources...${NC}"

    # Check if resource group exists
    if az group show --name $RESOURCE_GROUP &> /dev/null; then
        echo -e "${YELLOW}Destroying Terraform infrastructure...${NC}"

        cd cloud_infra/terraform/environments/dev

        if [ -f "terraform.tfstate" ]; then
            terraform destroy -auto-approve
        else
            echo "No Terraform state found, deleting resource group directly..."
            az group delete --name $RESOURCE_GROUP --yes --no-wait
        fi

        cd ../../../..

        echo -e "${GREEN}Azure resources cleaned up!${NC}"
    else
        echo -e "${YELLOW}Resource group $RESOURCE_GROUP not found, skipping...${NC}"
    fi
}

# Clean up local Docker resources
cleanup_local() {
    echo -e "\n${YELLOW}Cleaning up local Docker resources...${NC}"

    # Stop and remove containers
    echo "Stopping containers..."
    docker-compose down -v 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true

    # Remove images
    echo "Removing images..."
    docker rmi travel-mcp-server-backend:latest 2>/dev/null || true
    docker rmi travel-mcp-server-frontend:latest 2>/dev/null || true

    # Clean up dangling images
    echo "Cleaning up dangling images..."
    docker image prune -f

    echo -e "${GREEN}Local Docker resources cleaned up!${NC}"
}

# Main cleanup flow
main() {
    echo -e "\n${RED}WARNING: This will delete resources!${NC}"

    if [ "$AZURE_ONLY" = false ] && [ "$LOCAL_ONLY" = false ]; then
        echo "This will clean up both Azure and local resources."
    elif [ "$AZURE_ONLY" = true ]; then
        echo "This will clean up Azure resources only."
    else
        echo "This will clean up local Docker resources only."
    fi

    if ! confirm; then
        echo "Cleanup cancelled."
        exit 0
    fi

    if [ "$LOCAL_ONLY" = false ]; then
        cleanup_azure
    fi

    if [ "$AZURE_ONLY" = false ]; then
        cleanup_local
    fi

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Cleanup Complete!                      ${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main "$@"

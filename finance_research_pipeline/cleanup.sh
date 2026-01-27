#!/bin/bash

# ============================================================================
# Finance Research Pipeline - Cleanup Script
# ============================================================================
# This script removes all Azure resources and local artifacts for the
# Finance Research Pipeline project.
#
# Usage:
#   ./cleanup.sh                    # Interactive mode
#   ./cleanup.sh --all              # Clean everything (Azure + local)
#   ./cleanup.sh --azure-only       # Only destroy Azure resources
#   ./cleanup.sh --local-only       # Only clean local artifacts
#   ./cleanup.sh --force            # Skip confirmations (dangerous!)
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project configuration (same as deploy.sh)
PROJECT_NAME="${PROJECT_NAME:-finance-research}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
RESOURCE_GROUP="${PROJECT_NAME}-rg-${ENVIRONMENT}"
ACR_NAME="${PROJECT_NAME//-/}acr${ENVIRONMENT}"  # ACR names must be alphanumeric (removes hyphens)

# Other resource names (for reference, deleted with resource group)
OPENAI_NAME="${PROJECT_NAME}-openai-${ENVIRONMENT}"
REDIS_NAME="${PROJECT_NAME}-redis-${ENVIRONMENT}"
COSMOS_NAME="${PROJECT_NAME}-cosmos-${ENVIRONMENT}"
CONTAINER_ENV_NAME="${PROJECT_NAME}-env-${ENVIRONMENT}"
BACKEND_APP_NAME="${PROJECT_NAME}-backend-${ENVIRONMENT}"
FRONTEND_APP_NAME="${PROJECT_NAME}-frontend-${ENVIRONMENT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/cloud_infra/terraform/environments/dev"

# Flags
CLEAN_AZURE=false
CLEAN_LOCAL=false
FORCE=false
USE_TERRAFORM=true

# ============================================================================
# Helper Functions
# ============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║         Finance Research Pipeline - Cleanup Script                ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    local message=$1
    echo -e "${YELLOW}"
    read -p "$message [y/N]: " response
    echo -e "${NC}"
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    print_success "Azure CLI is available and logged in"
}

check_terraform() {
    if ! command -v terraform &> /dev/null; then
        print_warning "Terraform is not installed. Will use Azure CLI for cleanup."
        USE_TERRAFORM=false
        return 1
    fi
    print_success "Terraform is available"
    return 0
}

# ============================================================================
# Cleanup Functions
# ============================================================================

destroy_azure_terraform() {
    print_step "Destroying Azure resources with Terraform..."

    if [ ! -d "$TERRAFORM_DIR" ]; then
        print_warning "Terraform directory not found: $TERRAFORM_DIR"
        return 1
    fi

    cd "$TERRAFORM_DIR"

    # Check if terraform is initialized
    if [ ! -d ".terraform" ]; then
        print_warning "Terraform not initialized. Initializing..."
        terraform init
    fi

    # Check if there's state
    if ! terraform state list &> /dev/null; then
        print_warning "No Terraform state found. Resources may have been created manually."
        return 1
    fi

    echo -e "${YELLOW}The following resources will be destroyed:${NC}"
    terraform state list 2>/dev/null || true
    echo ""

    if confirm "Are you sure you want to destroy all Azure resources?"; then
        terraform destroy -auto-approve
        print_success "Azure resources destroyed via Terraform"
    else
        print_warning "Terraform destroy cancelled"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

destroy_azure_cli() {
    print_step "Destroying Azure resources with Azure CLI..."

    # Check if resource group exists
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Resource group '$RESOURCE_GROUP' does not exist"
        return 0
    fi

    echo -e "${YELLOW}Resources in resource group '$RESOURCE_GROUP':${NC}"
    az resource list --resource-group "$RESOURCE_GROUP" --output table 2>/dev/null || true
    echo ""

    if confirm "Are you sure you want to delete the resource group '$RESOURCE_GROUP' and ALL its resources?"; then
        print_step "Deleting resource group (this may take several minutes)..."
        az group delete --name "$RESOURCE_GROUP" --yes --no-wait
        print_success "Resource group deletion initiated (running in background)"

        # Optionally wait for deletion
        if confirm "Do you want to wait for the deletion to complete?"; then
            echo "Waiting for resource group deletion..."
            az group wait --name "$RESOURCE_GROUP" --deleted --timeout 600 2>/dev/null || true
            print_success "Resource group deleted"
        fi
    else
        print_warning "Resource group deletion cancelled"
    fi
}

cleanup_acr_images() {
    print_step "Cleaning up Azure Container Registry images..."

    # Check if ACR exists
    if ! az acr show --name "$ACR_NAME" &> /dev/null 2>&1; then
        print_warning "ACR '$ACR_NAME' does not exist or already deleted"
        return 0
    fi

    echo "Repositories in ACR:"
    az acr repository list --name "$ACR_NAME" --output table 2>/dev/null || true

    if confirm "Do you want to delete all images from ACR before destroying it?"; then
        for repo in $(az acr repository list --name "$ACR_NAME" -o tsv 2>/dev/null); do
            print_step "Deleting repository: $repo"
            az acr repository delete --name "$ACR_NAME" --repository "$repo" --yes 2>/dev/null || true
        done
        print_success "ACR images cleaned up"
    fi
}

cleanup_local_docker() {
    print_step "Cleaning up local Docker artifacts..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_warning "Docker is not running. Skipping Docker cleanup."
        return 0
    fi

    # Find and remove project-related images
    echo "Looking for project-related Docker images..."

    local images_to_remove=()

    # Images from ACR
    while IFS= read -r image; do
        [ -n "$image" ] && images_to_remove+=("$image")
    done < <(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "${ACR_NAME}|finresearch|finance-research" 2>/dev/null || true)

    # Local build images
    while IFS= read -r image; do
        [ -n "$image" ] && images_to_remove+=("$image")
    done < <(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "backend.*latest|frontend.*latest" 2>/dev/null || true)

    if [ ${#images_to_remove[@]} -eq 0 ]; then
        print_success "No project-related Docker images found"
        return 0
    fi

    echo "Found the following images:"
    printf '%s\n' "${images_to_remove[@]}"
    echo ""

    if confirm "Do you want to remove these Docker images?"; then
        for image in "${images_to_remove[@]}"; do
            echo "Removing: $image"
            docker rmi "$image" 2>/dev/null || print_warning "Failed to remove $image"
        done
        print_success "Docker images removed"
    fi

    # Clean up dangling images
    if confirm "Do you want to remove dangling Docker images (docker image prune)?"; then
        docker image prune -f
        print_success "Dangling images removed"
    fi

    # Clean up volumes
    local volumes=$(docker volume ls -q --filter "name=finance" 2>/dev/null || true)
    if [ -n "$volumes" ]; then
        echo "Found project-related volumes:"
        echo "$volumes"
        if confirm "Do you want to remove these Docker volumes?"; then
            echo "$volumes" | xargs -r docker volume rm 2>/dev/null || true
            print_success "Docker volumes removed"
        fi
    fi
}

cleanup_local_files() {
    print_step "Cleaning up local build artifacts..."

    cd "$SCRIPT_DIR"

    # Python artifacts
    if [ -d "backend/.venv" ]; then
        if confirm "Remove backend Python virtual environment (.venv)?"; then
            rm -rf backend/.venv
            print_success "Removed backend/.venv"
        fi
    fi

    if [ -d "backend/__pycache__" ] || find backend -name "__pycache__" -type d 2>/dev/null | grep -q .; then
        if confirm "Remove Python cache files (__pycache__)?"; then
            find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
            find backend -type f -name "*.pyc" -delete 2>/dev/null || true
            print_success "Removed Python cache files"
        fi
    fi

    # Node artifacts
    if [ -d "frontend/node_modules" ]; then
        if confirm "Remove frontend node_modules?"; then
            rm -rf frontend/node_modules
            print_success "Removed frontend/node_modules"
        fi
    fi

    if [ -d "frontend/dist" ]; then
        if confirm "Remove frontend build output (dist)?"; then
            rm -rf frontend/dist
            print_success "Removed frontend/dist"
        fi
    fi

    # Terraform artifacts
    if [ -d "$TERRAFORM_DIR/.terraform" ]; then
        if confirm "Remove Terraform cache (.terraform)?"; then
            rm -rf "$TERRAFORM_DIR/.terraform"
            rm -f "$TERRAFORM_DIR/.terraform.lock.hcl"
            print_success "Removed Terraform cache"
        fi
    fi

    if [ -f "$TERRAFORM_DIR/terraform.tfstate" ] || [ -f "$TERRAFORM_DIR/terraform.tfstate.backup" ]; then
        if confirm "Remove Terraform state files (terraform.tfstate)?"; then
            rm -f "$TERRAFORM_DIR/terraform.tfstate"
            rm -f "$TERRAFORM_DIR/terraform.tfstate.backup"
            print_success "Removed Terraform state files"
        fi
    fi

    # Environment files (be careful!)
    if [ -f ".env" ]; then
        print_warning "Found .env file with potentially sensitive data"
        if confirm "Do you want to remove .env file?"; then
            rm -f .env
            print_success "Removed .env file"
        fi
    fi
}

cleanup_terraform_state() {
    print_step "Cleaning up Terraform state..."

    cd "$TERRAFORM_DIR"

    if [ -f "terraform.tfstate" ]; then
        if confirm "Remove local Terraform state file?"; then
            rm -f terraform.tfstate
            rm -f terraform.tfstate.backup
            print_success "Removed Terraform state files"
        fi
    fi

    if [ -d ".terraform" ]; then
        if confirm "Remove Terraform cache directory?"; then
            rm -rf .terraform
            rm -f .terraform.lock.hcl
            print_success "Removed Terraform cache"
        fi
    fi

    cd "$SCRIPT_DIR"
}

delete_entire_project() {
    print_step "Delete entire project directory..."

    print_warning "This will permanently delete the entire project directory!"
    echo "Directory: $SCRIPT_DIR"

    if confirm "Are you ABSOLUTELY sure you want to delete the entire project?"; then
        if confirm "This cannot be undone. Type 'yes' to confirm"; then
            cd ..
            rm -rf "$SCRIPT_DIR"
            print_success "Project directory deleted"
            exit 0
        fi
    fi

    print_warning "Project directory deletion cancelled"
}

# ============================================================================
# Main Script
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                CLEAN_AZURE=true
                CLEAN_LOCAL=true
                shift
                ;;
            --azure-only)
                CLEAN_AZURE=true
                CLEAN_LOCAL=false
                shift
                ;;
            --local-only)
                CLEAN_AZURE=false
                CLEAN_LOCAL=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --all          Clean everything (Azure + local)"
                echo "  --azure-only   Only destroy Azure resources"
                echo "  --local-only   Only clean local artifacts"
                echo "  --force        Skip confirmations (dangerous!)"
                echo "  --help, -h     Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

interactive_menu() {
    echo ""
    echo "What would you like to clean up?"
    echo ""
    echo "  1) Azure resources only (Terraform destroy)"
    echo "  2) Azure resources only (Direct resource group delete - faster)"
    echo "  3) Local artifacts only (Docker, node_modules, .venv, etc.)"
    echo "  4) Everything (Azure + Local)"
    echo "  5) Delete entire project directory"
    echo "  6) Exit"
    echo ""

    read -p "Enter your choice [1-6]: " choice

    case $choice in
        1)
            CLEAN_AZURE=true
            CLEAN_LOCAL=false
            USE_TERRAFORM=true
            ;;
        2)
            CLEAN_AZURE=true
            CLEAN_LOCAL=false
            USE_TERRAFORM=false
            ;;
        3)
            CLEAN_AZURE=false
            CLEAN_LOCAL=true
            ;;
        4)
            CLEAN_AZURE=true
            CLEAN_LOCAL=true
            ;;
        5)
            check_azure_cli
            destroy_azure_cli
            cleanup_local_docker
            delete_entire_project
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

main() {
    print_banner

    parse_args "$@"

    # If no flags provided, show interactive menu
    if [ "$CLEAN_AZURE" = false ] && [ "$CLEAN_LOCAL" = false ]; then
        interactive_menu
    fi

    # Pre-flight checks
    if [ "$CLEAN_AZURE" = true ]; then
        check_azure_cli
        if [ "$USE_TERRAFORM" = true ]; then
            check_terraform
        fi
    fi

    # Summary
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                         Cleanup Summary                            ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Project:        $PROJECT_NAME"
    echo "Environment:    $ENVIRONMENT"
    echo ""
    echo -e "${YELLOW}Azure Resources to delete:${NC}"
    echo "  - Resource Group:  $RESOURCE_GROUP"
    echo "  - Azure OpenAI:    $OPENAI_NAME"
    echo "  - Container Reg:   $ACR_NAME"
    echo "  - Redis Cache:     $REDIS_NAME"
    echo "  - Cosmos DB:       $COSMOS_NAME"
    echo "  - Container Env:   $CONTAINER_ENV_NAME"
    echo "  - Backend App:     $BACKEND_APP_NAME"
    echo "  - Frontend App:    $FRONTEND_APP_NAME"
    echo ""
    echo "Actions to perform:"
    [ "$CLEAN_AZURE" = true ] && echo "  - Destroy Azure resources"
    [ "$CLEAN_LOCAL" = true ] && echo "  - Clean local artifacts"
    echo ""

    if ! confirm "Proceed with cleanup?"; then
        echo "Cleanup cancelled."
        exit 0
    fi

    # Execute cleanup
    if [ "$CLEAN_AZURE" = true ]; then
        if [ "$USE_TERRAFORM" = true ]; then
            cleanup_acr_images
            destroy_azure_terraform || destroy_azure_cli
        else
            destroy_azure_cli
        fi
    fi

    if [ "$CLEAN_LOCAL" = true ]; then
        cleanup_local_docker
        cleanup_local_files
        cleanup_terraform_state
    fi

    # Final summary
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                       Cleanup Complete!                            ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    if [ "$CLEAN_AZURE" = true ]; then
        echo "Note: Azure resource deletion may take a few minutes to complete."
        echo "You can check status with: az group show --name $RESOURCE_GROUP"
    fi
}

# Run main function
main "$@"

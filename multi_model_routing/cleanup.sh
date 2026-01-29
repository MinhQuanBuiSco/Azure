#!/bin/bash
set -e

#######################################
# Multi-Model LLM Router - Cleanup Script
#######################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="${PROJECT_NAME:-llm-router}"

# Derived names
RESOURCE_GROUP="${PROJECT_NAME}-${ENVIRONMENT}-rg"
ACR_NAME="${PROJECT_NAME//-/}${ENVIRONMENT}acr"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
log_warn "========================================="
log_warn "  CLEANUP: ${PROJECT_NAME}-${ENVIRONMENT}"
log_warn "========================================="
echo ""
log_warn "This will PERMANENTLY DELETE:"
echo "  - Resource Group: ${RESOURCE_GROUP}"
echo "  - All Azure resources (AI Services, Redis, Cosmos DB, etc.)"
echo "  - Container Registry: ${ACR_NAME}"
echo "  - Container Apps (backend, frontend)"
echo "  - All data and configurations"
echo ""

read -p "Type 'yes' to confirm destruction: " CONFIRM

if [[ "${CONFIRM}" != "yes" ]]; then
    log_warn "Cancelled"
    exit 0
fi

echo ""
log_info "Starting cleanup..."

# Step 1: Terraform destroy
if [[ -d "cloud_infra/environments/dev" ]]; then
    log_info "[1/3] Destroying Terraform resources..."
    cd cloud_infra/environments/dev

    if [[ -f "terraform.tfstate" ]] || [[ -d ".terraform" ]]; then
        terraform destroy -auto-approve 2>/dev/null || log_warn "Terraform destroy skipped (no state)"
    fi

    # Clean up local files
    rm -f terraform.tfstate terraform.tfstate.backup tfplan .terraform.lock.hcl 2>/dev/null || true
    rm -rf .terraform 2>/dev/null || true

    cd "${SCRIPT_DIR}"
    log_success "Terraform resources destroyed"
else
    log_warn "[1/3] Terraform directory not found, skipping"
fi

# Step 2: Delete ACR
log_info "[2/3] Deleting Container Registry..."
az acr delete \
    --name "${ACR_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --yes 2>/dev/null || log_warn "ACR not found or already deleted"
log_success "Container Registry deleted"

# Step 3: Delete Resource Group (catches anything remaining)
log_info "[3/3] Deleting Resource Group..."
az group delete \
    --name "${RESOURCE_GROUP}" \
    --yes \
    --no-wait 2>/dev/null || log_warn "Resource group not found or already deleted"
log_success "Resource Group deletion initiated"

# Clean up local files
rm -f .backend_url 2>/dev/null || true

echo ""
log_success "========================================="
log_success "Cleanup Complete!"
log_success "========================================="
echo ""
log_info "Note: Resource group deletion runs in background."
log_info "Run 'az group show -n ${RESOURCE_GROUP}' to check status."
echo ""

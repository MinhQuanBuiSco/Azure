#!/bin/bash

# LLM Security Gateway - Force Cleanup Script
# This script destroys ALL Azure resources without prompts

set -e

echo "============================================"
echo "LLM Security Gateway - Force Cleanup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="cloud_infra/environments/dev"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${RED}FORCE DELETING ALL RESOURCES...${NC}"
echo ""

# Step 1: Get resource group name from Terraform state
echo "============================================"
echo "Step 1: Getting resource group info..."
echo "============================================"

RESOURCE_GROUP=""
if [ -d "$TERRAFORM_DIR/.terraform" ]; then
    cd "$TERRAFORM_DIR"
    RESOURCE_GROUP=$(terraform output -raw resource_group_name 2>/dev/null || echo "")
    cd "$SCRIPT_DIR"
fi

# Fallback: find resource groups matching pattern
if [ -z "$RESOURCE_GROUP" ]; then
    echo "Searching for resource groups..."
    RESOURCE_GROUP=$(az group list --query "[?starts_with(name, 'rg-llm-gateway-dev')].name" -o tsv 2>/dev/null | head -1 || echo "")
fi

if [ -n "$RESOURCE_GROUP" ]; then
    echo -e "Found resource group: ${YELLOW}$RESOURCE_GROUP${NC}"
else
    echo -e "${YELLOW}No resource group found. Checking Terraform state...${NC}"
fi

echo ""

# Step 2: Delete resource group directly (fastest method)
echo "============================================"
echo "Step 2: Deleting Azure resource group..."
echo "============================================"

if [ -n "$RESOURCE_GROUP" ]; then
    echo "Deleting resource group: $RESOURCE_GROUP"
    echo "This will delete ALL resources inside it..."

    az group delete --name "$RESOURCE_GROUP" --yes --no-wait 2>/dev/null && \
        echo -e "${GREEN}✓ Resource group deletion initiated${NC}" || \
        echo -e "${YELLOW}Resource group may already be deleted or not exist${NC}"
else
    # Try terraform destroy as fallback
    echo "No resource group found. Trying terraform destroy..."
    if [ -d "$TERRAFORM_DIR/.terraform" ]; then
        cd "$TERRAFORM_DIR"
        terraform destroy -auto-approve 2>/dev/null || true
        cd "$SCRIPT_DIR"
    fi
fi

echo ""

# Step 3: Clean up any other matching resource groups
echo "============================================"
echo "Step 3: Cleaning up any remaining resources..."
echo "============================================"

ALL_RG=$(az group list --query "[?contains(name, 'llm-gateway')].name" -o tsv 2>/dev/null || echo "")

if [ -n "$ALL_RG" ]; then
    echo "Found additional resource groups:"
    echo "$ALL_RG"
    echo ""
    for RG in $ALL_RG; do
        echo "Deleting: $RG"
        az group delete --name "$RG" --yes --no-wait 2>/dev/null || true
    done
    echo -e "${GREEN}✓ All resource group deletions initiated${NC}"
else
    echo -e "${GREEN}✓ No additional resource groups found${NC}"
fi

echo ""

# Step 4: Clean up local Docker images
echo "============================================"
echo "Step 4: Cleaning up Docker images..."
echo "============================================"

# Remove ACR images
docker images | grep "azurecr.io" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker image prune -f 2>/dev/null || true

echo -e "${GREEN}✓ Docker images cleaned${NC}"

echo ""

# Step 5: Clean up Terraform state
echo "============================================"
echo "Step 5: Cleaning up Terraform state..."
echo "============================================"

if [ -d "$TERRAFORM_DIR" ]; then
    cd "$TERRAFORM_DIR"
    rm -rf .terraform 2>/dev/null || true
    rm -f .terraform.lock.hcl 2>/dev/null || true
    rm -f terraform.tfstate 2>/dev/null || true
    rm -f terraform.tfstate.backup 2>/dev/null || true
    rm -f *.tfplan 2>/dev/null || true
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Terraform state cleaned${NC}"
fi

echo ""

# Step 6: Clean up Playwright artifacts
echo "============================================"
echo "Step 6: Cleaning up other artifacts..."
echo "============================================"

rm -rf .playwright-mcp 2>/dev/null || true
echo -e "${GREEN}✓ Artifacts cleaned${NC}"

echo ""
echo "============================================"
echo -e "${GREEN}CLEANUP COMPLETE!${NC}"
echo "============================================"
echo ""
echo "Resource group deletion runs in background."
echo "Full deletion may take 5-10 minutes."
echo ""
echo "Verify at: https://portal.azure.com"
echo ""

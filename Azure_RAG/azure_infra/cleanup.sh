#!/bin/bash
# Cleanup script for RAG Application Azure infrastructure
set -e

echo "========================================="
echo "RAG Application - Azure Cleanup"
echo "========================================="
echo ""
echo "⚠️  WARNING: This will PERMANENTLY DELETE all Azure resources!"
echo ""
echo "Resources to be deleted:"
echo "  - Resource Group: rg-rag-app-prod"
echo "  - Storage Account with all PDFs"
echo "  - Redis Cache"
echo "  - Azure AI Search (including all indexed data)"
echo "  - Azure OpenAI deployments"
echo "  - Container Registry with Docker images"
echo "  - Container Apps"
echo "  - Static Web App"
echo "  - Application Insights & Log Analytics"
echo ""
echo "This action CANNOT be undone!"
echo ""

read -p "Type 'DELETE' to confirm deletion: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
read -p "Are you absolutely sure? Type 'yes' to proceed: " CONFIRM2

if [ "$CONFIRM2" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Step 1: Destroying all Azure resources..."
echo "This will take 5-10 minutes..."
terraform destroy -auto-approve

echo ""
echo "Step 2: Cleaning up local files..."

# Remove Terraform state and plan files
if [ -f "terraform.tfstate" ]; then
    echo "  - Removing terraform.tfstate"
    rm -f terraform.tfstate
fi

if [ -f "terraform.tfstate.backup" ]; then
    echo "  - Removing terraform.tfstate.backup"
    rm -f terraform.tfstate.backup
fi

if [ -f "tfplan" ]; then
    echo "  - Removing tfplan"
    rm -f tfplan
fi

# Remove backend .env file
if [ -f "../backend/.env" ]; then
    echo "  - Removing backend/.env"
    rm -f ../backend/.env
fi

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "All Azure resources have been deleted."
echo "Local Terraform state files have been removed."
echo ""
echo "Note: The following files were preserved:"
echo "  - terraform.tfvars (your configuration)"
echo "  - .terraform/ directory (provider cache)"
echo "  - .terraform.lock.hcl (provider versions)"
echo ""
echo "To completely reset, run:"
echo "  rm -rf .terraform .terraform.lock.hcl terraform.tfvars"
echo ""

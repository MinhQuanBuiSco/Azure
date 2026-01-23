#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LLM Security Gateway - Azure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Set directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/cloud_infra/environments/dev"

# Step 0: Clean up existing deployment (optional)
echo -e "\n${YELLOW}Step 0: Checking for existing deployment...${NC}"
cd "${TERRAFORM_DIR}"

if [ -f "terraform.tfstate" ]; then
    echo -e "${YELLOW}Found existing Terraform state. Destroying...${NC}"
    terraform init -upgrade
    terraform destroy -auto-approve || true
    echo -e "${GREEN}Cleanup complete.${NC}"
fi

# Step 1: Initialize Terraform
echo -e "\n${YELLOW}Step 1: Initializing Terraform...${NC}"
terraform init -upgrade

# Step 2: Deploy ACR first (needed for pushing images)
echo -e "\n${YELLOW}Step 2: Deploying ACR and base resources...${NC}"
terraform apply -target=random_string.suffix \
                -target=azurerm_resource_group.main \
                -target=module.acr \
                -auto-approve

# Get ACR credentials
ACR_NAME=$(terraform output -raw acr_name)
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)

echo -e "${GREEN}ACR Name: ${ACR_NAME}${NC}"
echo -e "${GREEN}ACR Login Server: ${ACR_LOGIN_SERVER}${NC}"

# Step 3: Login to ACR
echo -e "\n${YELLOW}Step 3: Logging into ACR...${NC}"
az acr login --name "${ACR_NAME}"

# Step 4: Build and push Docker images (linux/amd64 for Azure)
echo -e "\n${YELLOW}Step 4: Building and pushing Docker images...${NC}"
cd "${SCRIPT_DIR}"

# Build backend for linux/amd64 (required by Azure Container Apps)
echo -e "${YELLOW}Building backend image (linux/amd64)...${NC}"
docker build --platform linux/amd64 --no-cache -t "${ACR_LOGIN_SERVER}/backend:latest" ./backend

# Build frontend for linux/amd64 (required by Azure Container Apps)
echo -e "${YELLOW}Building frontend image (linux/amd64)...${NC}"
docker build --platform linux/amd64 --no-cache -t "${ACR_LOGIN_SERVER}/frontend:latest" ./frontend

# Push images to ACR
echo -e "${YELLOW}Pushing backend image...${NC}"
docker push "${ACR_LOGIN_SERVER}/backend:latest"

echo -e "${YELLOW}Pushing frontend image...${NC}"
docker push "${ACR_LOGIN_SERVER}/frontend:latest"

# Step 5: Deploy full infrastructure
echo -e "\n${YELLOW}Step 5: Deploying full infrastructure...${NC}"
cd "${TERRAFORM_DIR}"
terraform apply -auto-approve

# Step 6: Get outputs and display
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "pending...")
BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo "pending...")

echo -e "\n${YELLOW}Application URLs:${NC}"
echo -e "Frontend: ${GREEN}${FRONTEND_URL}${NC}"
echo -e "Backend:  ${GREEN}${BACKEND_URL}${NC}"

echo -e "\n${YELLOW}Test the backend:${NC}"
echo -e "curl ${BACKEND_URL}/health"

echo -e "\n${YELLOW}Resource Group:${NC}"
terraform output -raw resource_group_name

echo -e "\n${YELLOW}ACR:${NC}"
echo -e "Name: ${ACR_NAME}"
echo -e "Server: ${ACR_LOGIN_SERVER}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Your LLM Security Gateway is now live!${NC}"
echo -e "${GREEN}Open ${FRONTEND_URL} in your browser${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 7: Quick health check
echo -e "\n${YELLOW}Running health check...${NC}"
sleep 10  # Wait for container to start

if curl -s "${BACKEND_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy!${NC}"
else
    echo -e "${YELLOW}⚠ Backend might still be starting. Try: curl ${BACKEND_URL}/health${NC}"
fi

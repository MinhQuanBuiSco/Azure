#!/bin/bash
# Fully Automated Deployment Script for RAG Application on Azure
set -e

echo "========================================="
echo "RAG Application - Automated Deployment"
echo "========================================="
echo ""

# Configuration
BACKEND_VERSION="${BACKEND_VERSION:-$(date +%Y%m%d-%H%M%S)}"
echo "Backend version: $BACKEND_VERSION"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI is required but not installed."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed."; exit 1; }

az account show &>/dev/null || { echo "❌ Please login to Azure CLI first: az login"; exit 1; }
echo "✅ All prerequisites met"
echo ""

# Step 1: Initialize Terraform
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Initializing Terraform"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
terraform init -upgrade
echo ""

# Step 2: Plan Infrastructure
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Planning Infrastructure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
terraform plan -out=tfplan
echo ""

# Confirm deployment
read -p "Proceed with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    rm -f tfplan
    exit 0
fi
echo ""

# Step 3: Apply Infrastructure
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Deploying Infrastructure (15-20 min)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
terraform apply tfplan
rm -f tfplan
echo "✅ Infrastructure deployed"
echo ""

# Step 4: Extract Terraform Outputs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Extracting Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ACR_SERVER=$(terraform output -raw acr_login_server)
ACR_USERNAME=$(terraform output -raw acr_admin_username)
ACR_PASSWORD=$(terraform output -raw acr_admin_password)
RG_NAME=$(terraform output -raw resource_group_name)
BACKEND_APP_NAME=$(terraform output -raw backend_app_name 2>/dev/null || echo "ca-rag-backend")
SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
SEARCH_KEY=$(terraform output -raw search_primary_key)
FRONTEND_URL=$(terraform output -raw frontend_url)

echo "  ACR Server: $ACR_SERVER"
echo "  Resource Group: $RG_NAME"
echo "  Backend App: $BACKEND_APP_NAME"
echo "  Frontend URL: https://$FRONTEND_URL"
echo "✅ Configuration extracted"
echo ""

# Step 5: Create AI Search Index
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Creating AI Search Index"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ../backend
if [ -f "create_index.py" ]; then
    # Activate venv if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || true
    fi

    AZURE_SEARCH_API_KEY="$SEARCH_KEY" python create_index.py
    echo "✅ Search index created"
else
    echo "⚠️  create_index.py not found, skipping"
fi
cd ../azure_infra
echo ""

# Step 6: Build and Push Backend Docker Image
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Building Backend ($BACKEND_VERSION)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$ACR_PASSWORD" | docker login $ACR_SERVER -u $ACR_USERNAME --password-stdin

cd ../backend
echo "  Building image (linux/amd64)..."
docker build --platform linux/amd64 \
    -t $ACR_SERVER/rag-backend:$BACKEND_VERSION \
    -t $ACR_SERVER/rag-backend:latest \
    .

echo "  Pushing to ACR..."
docker push $ACR_SERVER/rag-backend:$BACKEND_VERSION
docker push $ACR_SERVER/rag-backend:latest

cd ../azure_infra
echo "✅ Backend image pushed"
echo ""

# Step 7: Update Container App with New Image and Frontend URL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Updating Backend Container App"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Update with new image and add FRONTEND_URL environment variable
az containerapp update \
    --name $BACKEND_APP_NAME \
    --resource-group $RG_NAME \
    --image $ACR_SERVER/rag-backend:$BACKEND_VERSION \
    --set-env-vars FRONTEND_URL="https://$FRONTEND_URL" \
    --output none

echo "✅ Backend updated to version $BACKEND_VERSION"
echo ""

# Step 8: Build and Deploy Frontend
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Building and Deploying Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ../frontend

# Create/update .env file with backend URL
BACKEND_URL=$(cd ../azure_infra && terraform output -raw backend_url)
cat > .env << EOF
VITE_API_BASE_URL=$BACKEND_URL
EOF

echo "  Installing dependencies..."
npm install --silent

echo "  Building..."
npm run build

echo "  Deploying to Static Web App..."
DEPLOY_TOKEN=$(cd ../azure_infra && terraform output -raw frontend_deployment_token)
npx @azure/static-web-apps-cli deploy ./dist \
    --env production \
    --deployment-token "$DEPLOY_TOKEN" \
    --no-use-keychain

cd ../azure_infra
echo "✅ Frontend deployed"
echo ""

# Step 9: Generate Local Configuration Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 9: Generating Local Config Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backend .env
cd ../backend
cat > .env << EOF
# Generated on $(date)
# Backend Configuration
AZURE_STORAGE_ACCOUNT_NAME=$(cd ../azure_infra && terraform output -raw storage_account_name)
AZURE_STORAGE_CONNECTION_STRING=$(cd ../azure_infra && terraform output -raw storage_connection_string)
AZURE_STORAGE_CONTAINER_NAME=$(cd ../azure_infra && terraform output -raw blob_container_name)
AZURE_SEARCH_ENDPOINT=$(cd ../azure_infra && terraform output -raw search_endpoint)
AZURE_SEARCH_API_KEY=$(cd ../azure_infra && terraform output -raw search_primary_key)
AZURE_SEARCH_INDEX_NAME=$(cd ../azure_infra && terraform output -raw search_index_name)
AZURE_OPENAI_ENDPOINT=$(cd ../azure_infra && terraform output -raw openai_endpoint)
AZURE_OPENAI_API_KEY=$(cd ../azure_infra && terraform output -raw openai_primary_key)
AZURE_OPENAI_CHAT_DEPLOYMENT=$(cd ../azure_infra && terraform output -raw openai_chat_deployment)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$(cd ../azure_infra && terraform output -raw openai_embedding_deployment)
REDIS_HOST=$(cd ../azure_infra && terraform output -raw redis_hostname)
REDIS_PORT=6380
REDIS_PASSWORD=$(cd ../azure_infra && terraform output -raw redis_primary_key)
REDIS_SSL=true
FRONTEND_URL=https://$FRONTEND_URL
EOF

cd ../azure_infra
echo "  ✓ backend/.env"
echo "  ✓ frontend/.env"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Application URLs:"
echo "  Frontend:  https://$FRONTEND_URL"
echo "  Backend:   $BACKEND_URL"
echo "  API Docs:  $BACKEND_URL/docs"
echo ""
echo "🔧 Backend Version: $BACKEND_VERSION"
echo ""
echo "📋 Next Steps:"
echo "  1. Test backend health:"
echo "     curl $BACKEND_URL/health"
echo ""
echo "  2. Monitor backend logs:"
echo "     az containerapp logs show \\"
echo "       --name $BACKEND_APP_NAME \\"
echo "       --resource-group $RG_NAME \\"
echo "       --follow"
echo ""
echo "  3. Access frontend:"
echo "     open https://$FRONTEND_URL"
echo ""
echo "📁 Configuration Files:"
echo "  • backend/.env (local development)"
echo "  • frontend/.env (local development)"
echo ""

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
# Clean up any cached state
if [ -f ".terraform.lock.hcl" ]; then
    echo "  Removing cached lock file..."
    rm -f .terraform.lock.hcl
fi
terraform init -upgrade -reconfigure
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
BACKEND_APP_NAME=$(terraform output -raw backend_app_name)
SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
SEARCH_KEY=$(terraform output -raw search_primary_key)
SEARCH_INDEX_NAME=$(terraform output -raw search_index_name)
SEARCH_NAME=$(echo "$SEARCH_ENDPOINT" | sed 's|https://||' | sed 's|\.search\.windows\.net||')
STORAGE_NAME=$(terraform output -raw storage_account_name)
STORAGE_CONN_STR=$(terraform output -raw storage_connection_string)
BLOB_CONTAINER=$(terraform output -raw blob_container_name)
REDIS_HOSTNAME=$(terraform output -raw redis_hostname)
REDIS_NAME=$(echo "$REDIS_HOSTNAME" | cut -d. -f1)
REDIS_KEY=$(terraform output -raw redis_primary_key)
OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint)
OPENAI_KEY=$(terraform output -raw openai_primary_key)
OPENAI_CHAT_DEPLOY=$(terraform output -raw openai_chat_deployment)
OPENAI_EMBED_DEPLOY=$(terraform output -raw openai_embedding_deployment)
FRONTEND_URL=$(terraform output -raw frontend_url)
BACKEND_URL=$(terraform output -raw backend_url)

echo "  Resource Group: $RG_NAME"
echo "  Storage Account: $STORAGE_NAME"
echo "  Search Service: $SEARCH_NAME"
echo "  Redis Cache: $REDIS_NAME"
echo "  ACR: $ACR_SERVER"
echo "  Backend App: $BACKEND_APP_NAME"
echo "  Frontend URL: https://$FRONTEND_URL"
echo "✅ Configuration extracted - All resource names from terraform"
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

    # Retry logic for DNS propagation
    SEARCH_HOSTNAME=$(echo "$SEARCH_ENDPOINT" | sed 's|https://||' | sed 's|/||')
    MAX_RETRIES=10
    RETRY_COUNT=0

    echo "  Waiting for DNS propagation for $SEARCH_HOSTNAME..."

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        # Check DNS resolution first
        if nslookup "$SEARCH_HOSTNAME" &>/dev/null || host "$SEARCH_HOSTNAME" &>/dev/null; then
            echo "  ✓ DNS resolved successfully"

            # Try to create index
            if AZURE_SEARCH_ENDPOINT="$SEARCH_ENDPOINT" AZURE_SEARCH_API_KEY="$SEARCH_KEY" python create_index.py 2>&1; then
                echo "✅ Search index created"
                break
            else
                RETRY_COUNT=$((RETRY_COUNT + 1))
                if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                    echo "  ⚠️  Index creation failed, retrying in 60s... ($RETRY_COUNT/$MAX_RETRIES)"
                    sleep 60
                fi
            fi
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "  ⏳ DNS not ready, waiting 60s... ($RETRY_COUNT/$MAX_RETRIES)"
                sleep 60
            fi
        fi
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "  ❌ Failed to create index after $MAX_RETRIES attempts (10 minutes)"
        echo "  The search service may need more time for DNS propagation."
        echo "  You can manually create it later by running:"
        echo "  cd backend && AZURE_SEARCH_ENDPOINT=\"$SEARCH_ENDPOINT\" AZURE_SEARCH_API_KEY=\"$SEARCH_KEY\" python create_index.py"
    fi
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

# Step 7: Deploy Backend (initial deployment without FRONTEND_URL)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Deploying Backend Container App"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

az containerapp update \
    --name $BACKEND_APP_NAME \
    --resource-group $RG_NAME \
    --image $ACR_SERVER/rag-backend:$BACKEND_VERSION \
    --output none

echo "✅ Backend deployed (version $BACKEND_VERSION)"
echo ""

# Step 8: Build and Deploy Frontend
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Building and Deploying Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ../frontend

# Get stable backend URL (not revision-specific)
BACKEND_STABLE_FQDN=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RG_NAME --query "properties.configuration.ingress.fqdn" -o tsv)
BACKEND_URL="https://$BACKEND_STABLE_FQDN"

echo "  Using stable backend URL: $BACKEND_URL"

# Create/update .env file with backend URL
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
echo "✅ Frontend deployed to https://$FRONTEND_URL"
echo ""

# Step 9: Update Backend Secrets and CORS
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 9: Updating Backend Secrets and CORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  Updating backend secrets..."
az containerapp secret set \
    --name $BACKEND_APP_NAME \
    --resource-group $RG_NAME \
    --secrets \
        azure-storage-key="$STORAGE_CONN_STR" \
        azure-search-key="$SEARCH_KEY" \
        azure-openai-key="$OPENAI_KEY" \
        redis-password="$REDIS_KEY" \
    --output none

echo "  Setting FRONTEND_URL=https://$FRONTEND_URL for CORS..."
az containerapp update \
    --name $BACKEND_APP_NAME \
    --resource-group $RG_NAME \
    --set-env-vars FRONTEND_URL="https://$FRONTEND_URL" \
    --output none

echo "  Restarting backend to apply changes..."
az containerapp revision restart \
    --name $BACKEND_APP_NAME \
    --resource-group $RG_NAME \
    --revision $(az containerapp revision list --name $BACKEND_APP_NAME --resource-group $RG_NAME --query "[?properties.active==\`true\`].name" -o tsv) \
    --output none 2>/dev/null || true

echo "  Waiting for backend to restart..."
sleep 20

echo "✅ Backend configured with all secrets and CORS for https://$FRONTEND_URL"
echo ""

# Step 10: Generate Local Configuration Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 10: Generating Local Config Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backend .env
cd ../backend
cat > .env << EOF
# Generated on $(date)
# Backend Configuration
AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME
AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONN_STR
AZURE_STORAGE_CONTAINER_NAME=$BLOB_CONTAINER
AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
AZURE_SEARCH_API_KEY=$SEARCH_KEY
AZURE_SEARCH_INDEX_NAME=$SEARCH_INDEX_NAME
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_CHAT_DEPLOYMENT=$OPENAI_CHAT_DEPLOY
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$OPENAI_EMBED_DEPLOY
REDIS_HOST=$REDIS_HOSTNAME
REDIS_PORT=6380
REDIS_PASSWORD=$REDIS_KEY
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

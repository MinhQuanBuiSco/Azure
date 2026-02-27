#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 4 — Deploy: Seed Key Vault, push Docker image, deploy frontend
#
# Prerequisites:
#   1. setup.sh has been run (backend/.env + frontend/.env.local exist)
#   2. terraform apply has been run (infra exists)
#   3. Docker is running
#   4. npm is available (for swa-cli)
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"

# ── Preflight checks ────────────────────────────────

if [[ ! -f "$SCRIPT_DIR/backend/.env" ]]; then
  echo "ERROR: backend/.env not found. Run ./setup.sh first." >&2
  exit 1
fi

if [[ ! -d "$INFRA_DIR/.terraform" ]]; then
  echo "ERROR: Terraform not initialized. Run: cd infra && terraform init && terraform apply" >&2
  exit 1
fi

# ── Read Terraform outputs ──────────────────────────

echo "==> Reading Terraform outputs..."
cd "$INFRA_DIR"

BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || true)
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || true)
KEY_VAULT_NAME=$(terraform output -raw key_vault_name 2>/dev/null || true)
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server 2>/dev/null || true)
SWA_TOKEN=$(terraform output -raw swa_deployment_token 2>/dev/null || true)
RG_NAME=$(terraform output -raw resource_group_name 2>/dev/null || true)
BACKEND_APP_NAME=$(terraform output -raw backend_app_name 2>/dev/null || true)

cd "$SCRIPT_DIR"

# Validate outputs are not empty
if [[ -z "$BACKEND_URL" || -z "$KEY_VAULT_NAME" || -z "$ACR_LOGIN_SERVER" ]]; then
  echo "ERROR: Terraform outputs are empty. Run: cd infra && terraform apply" >&2
  echo "       Make sure terraform.tfvars is configured and apply completed successfully." >&2
  exit 1
fi

echo "   Backend URL:    $BACKEND_URL"
echo "   Frontend URL:   $FRONTEND_URL"
echo "   Key Vault:      $KEY_VAULT_NAME"
echo "   ACR:            $ACR_LOGIN_SERVER"

# ── 1. Seed Key Vault secrets from backend/.env ─────

echo ""
echo "==> Seeding Key Vault secrets from backend/.env..."

# Read values from the .env file that setup.sh created
TENANT_ID=$(grep AZURE_TENANT_ID "$SCRIPT_DIR/backend/.env" | cut -d= -f2)
API_CLIENT_ID=$(grep AZURE_API_CLIENT_ID "$SCRIPT_DIR/backend/.env" | cut -d= -f2)

az keyvault secret set --vault-name "$KEY_VAULT_NAME" \
  --name "azure-tenant-id" --value "$TENANT_ID" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" \
  --name "azure-api-client-id" --value "$API_CLIENT_ID" --output none

echo "   Seeded: azure-tenant-id, azure-api-client-id"

# ── 2. Build + push Docker image ────────────────────

echo ""
echo "==> Logging in to ACR: $ACR_LOGIN_SERVER..."
az acr login --name "${ACR_LOGIN_SERVER%%.*}"

IMAGE_TAG="$ACR_LOGIN_SERVER/blog4-backend:latest"

echo "==> Building Docker image (linux/amd64)..."
docker build --platform linux/amd64 -t "$IMAGE_TAG" "$SCRIPT_DIR/backend"

echo "==> Pushing Docker image..."
docker push "$IMAGE_TAG"

# ── 3. Update Container App with new image ──────────

echo ""
echo "==> Updating Container App..."
az containerapp update \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RG_NAME" \
  --image "$IMAGE_TAG" \
  --output none

echo "   Backend deployed: $BACKEND_URL"

# ── 4. Build + deploy frontend to Static Web App ───

echo ""
echo "==> Building frontend for production..."

# Read frontend env values
SPA_APP_ID=$(grep NEXT_PUBLIC_AZURE_CLIENT_ID "$SCRIPT_DIR/frontend/.env.local" | cut -d= -f2)
SPA_TENANT_ID=$(grep NEXT_PUBLIC_AZURE_TENANT_ID "$SCRIPT_DIR/frontend/.env.local" | cut -d= -f2)
API_SCOPE=$(grep NEXT_PUBLIC_API_SCOPE "$SCRIPT_DIR/frontend/.env.local" | cut -d= -f2)

cd "$SCRIPT_DIR/frontend"
npm install

# Build with production API URL (the Container Apps backend URL)
NEXT_PUBLIC_AZURE_CLIENT_ID="$SPA_APP_ID" \
NEXT_PUBLIC_AZURE_TENANT_ID="$SPA_TENANT_ID" \
NEXT_PUBLIC_API_SCOPE="$API_SCOPE" \
NEXT_PUBLIC_API_URL="$BACKEND_URL" \
npm run build

echo "==> Deploying to Static Web App..."
npx @azure/static-web-apps-cli deploy ./out \
  --deployment-token "$SWA_TOKEN" \
  --env production

cd "$SCRIPT_DIR"

echo "   Frontend deployed: $FRONTEND_URL"

# ── 5. Add SWA URL as redirect URI ─────────────────

echo ""
echo "==> Adding $FRONTEND_URL as SPA redirect URI..."

SPA_APP_ID_VALUE="$SPA_APP_ID"
SPA_OBJ_ID=$(az ad app show --id "$SPA_APP_ID_VALUE" --query id --output tsv)

# Get current redirect URIs and add the new one
CURRENT_URIS=$(az ad app show --id "$SPA_APP_ID_VALUE" \
  --query "spa.redirectUris" --output tsv 2>/dev/null || echo "")

# Build the new array
URIS_JSON="[\"http://localhost:3000\",\"$FRONTEND_URL\"]"

az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$SPA_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"spa\":{\"redirectUris\":$URIS_JSON}}" \
  --output none

echo "   Added redirect URI: $FRONTEND_URL"

# ── Done ────────────────────────────────────────────

echo ""
echo "=========================================="
echo "  Deployment complete!"
echo "=========================================="
echo ""
echo "  Backend:   $BACKEND_URL"
echo "  Frontend:  $FRONTEND_URL"
echo "  Key Vault: $KEY_VAULT_NAME"
echo ""
echo "  Verify:"
echo "    curl $BACKEND_URL/health"
echo "    Open $FRONTEND_URL in your browser"
echo ""
echo "  View logs:"
echo "    az containerapp logs show -n $BACKEND_APP_NAME -g $RG_NAME --follow"

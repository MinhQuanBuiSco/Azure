#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# Blog 1 — Azure AD App Registration Setup
# Creates a SPA app registration for local dev
# ──────────────────────────────────────────────

APP_NAME="${1:-Blog1-BasicLogin}"
REDIRECT_URI="http://localhost:3000"
GRAPH_API="00000003-0000-0000-c000-000000000000"  # Microsoft Graph
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"  # User.Read permission ID

echo "==> Creating app registration: $APP_NAME"
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --required-resource-accesses "[{
    \"resourceAppId\": \"$GRAPH_API\",
    \"resourceAccess\": [{
      \"id\": \"$USER_READ\",
      \"type\": \"Scope\"
    }]
  }]" \
  --query appId \
  --output tsv)

OBJ_ID=$(az ad app show --id "$APP_ID" --query id --output tsv)

echo "==> Setting SPA redirect URI: $REDIRECT_URI"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"spa\":{\"redirectUris\":[\"$REDIRECT_URI\"]}}"

TENANT_ID=$(az account show --query tenantId --output tsv)

echo ""
echo "==> Done! App registered successfully."
echo ""
echo "   Client ID:  $APP_ID"
echo "   Tenant ID:  $TENANT_ID"
echo ""
echo "==> Writing frontend/.env.local ..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cat > "$SCRIPT_DIR/frontend/.env.local" <<EOF
# Azure AD / Microsoft Entra ID configuration
NEXT_PUBLIC_AZURE_CLIENT_ID=$APP_ID
NEXT_PUBLIC_AZURE_TENANT_ID=$TENANT_ID
EOF

echo "   Written to frontend/.env.local"
echo ""
echo "==> Next steps:"
echo "   cd frontend && npm run dev"

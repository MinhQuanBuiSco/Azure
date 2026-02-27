#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 2 — Protected API: Azure AD Setup
# Creates TWO app registrations:
#   1. API backend  (exposes a custom scope)
#   2. SPA frontend (requests that scope)
# ──────────────────────────────────────────────────────

API_APP_NAME="${1:-Blog2-API}"
SPA_APP_NAME="${2:-Blog2-Frontend}"
REDIRECT_URI="http://localhost:3000"
SCOPE_NAME="access_as_user"
GRAPH_API="00000003-0000-0000-c000-000000000000"
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

TENANT_ID=$(az account show --query tenantId --output tsv)

# ── 1. API app registration ─────────────────────────

echo "==> Creating API app registration: $API_APP_NAME"
API_APP_ID=$(az ad app create \
  --display-name "$API_APP_NAME" \
  --query appId \
  --output tsv)

API_OBJ_ID=$(az ad app show --id "$API_APP_ID" --query id --output tsv)

echo "==> Creating service principal for API app"
az ad sp create --id "$API_APP_ID" --output none

echo "==> Setting identifier URI: api://$API_APP_ID"
az ad app update --id "$API_APP_ID" \
  --identifier-uris "api://$API_APP_ID"

# Generate a UUID for the scope
SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "==> Exposing scope: $SCOPE_NAME"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$API_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"oauth2PermissionScopes\": [{
        \"adminConsentDescription\": \"Allow the app to access the API on behalf of the signed-in user\",
        \"adminConsentDisplayName\": \"Access API as user\",
        \"id\": \"$SCOPE_ID\",
        \"isEnabled\": true,
        \"type\": \"User\",
        \"userConsentDescription\": \"Allow the app to access the API on your behalf\",
        \"userConsentDisplayName\": \"Access API as user\",
        \"value\": \"$SCOPE_NAME\"
      }]
    }
  }"

# ── 2. SPA frontend app registration ────────────────

echo "==> Creating SPA app registration: $SPA_APP_NAME"
SPA_APP_ID=$(az ad app create \
  --display-name "$SPA_APP_NAME" \
  --required-resource-accesses "[
    {
      \"resourceAppId\": \"$GRAPH_API\",
      \"resourceAccess\": [{
        \"id\": \"$USER_READ\",
        \"type\": \"Scope\"
      }]
    },
    {
      \"resourceAppId\": \"$API_APP_ID\",
      \"resourceAccess\": [{
        \"id\": \"$SCOPE_ID\",
        \"type\": \"Scope\"
      }]
    }
  ]" \
  --query appId \
  --output tsv)

SPA_OBJ_ID=$(az ad app show --id "$SPA_APP_ID" --query id --output tsv)

echo "==> Creating service principal for SPA app"
az ad sp create --id "$SPA_APP_ID" --output none

echo "==> Setting SPA redirect URI: $REDIRECT_URI"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$SPA_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"spa\":{\"redirectUris\":[\"$REDIRECT_URI\"]}}"

# ── 3. Write env files ──────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Writing backend/.env"
cat > "$SCRIPT_DIR/backend/.env" <<EOF
AZURE_TENANT_ID=$TENANT_ID
AZURE_API_CLIENT_ID=$API_APP_ID
EOF

echo "==> Writing frontend/.env.local"
cat > "$SCRIPT_DIR/frontend/.env.local" <<EOF
# Azure AD / Microsoft Entra ID configuration
NEXT_PUBLIC_AZURE_CLIENT_ID=$SPA_APP_ID
NEXT_PUBLIC_AZURE_TENANT_ID=$TENANT_ID
NEXT_PUBLIC_API_SCOPE=api://$API_APP_ID/$SCOPE_NAME
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# ── Done ────────────────────────────────────────────

echo ""
echo "==> Done! Both apps registered successfully."
echo ""
echo "   API App:      $API_APP_ID"
echo "   SPA App:      $SPA_APP_ID"
echo "   Tenant:       $TENANT_ID"
echo "   API Scope:    api://$API_APP_ID/$SCOPE_NAME"
echo ""
echo "==> Next steps:"
echo "   1. cd backend  && pip install -r requirements.txt && uvicorn main:app --reload"
echo "   2. cd frontend && npm install && npm run dev"

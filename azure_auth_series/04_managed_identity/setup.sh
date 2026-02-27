#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 4 — Managed Identity: Azure AD Setup
# (Same as Blog 3 — creates app registrations + test users)
#
# Creates:
#   1. API app with 3 App Roles (Admin/Editor/Reader)
#   2. SPA frontend app
#   3. Two test users (editor + reader)
#   4. Role assignments for all 3 users
#   5. Writes .env files for local dev
# ──────────────────────────────────────────────────────

API_APP_NAME="${1:-Blog4-API}"
SPA_APP_NAME="${2:-Blog4-Frontend}"
REDIRECT_URI="http://localhost:3000"
SCOPE_NAME="access_as_user"
GRAPH_API="00000003-0000-0000-c000-000000000000"
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

TENANT_ID=$(az account show --query tenantId --output tsv)
DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv)

# Role IDs (fixed UUIDs for consistency)
ADMIN_ROLE_ID="a1b2c3d4-0001-0001-0001-000000000001"
EDITOR_ROLE_ID="a1b2c3d4-0001-0001-0001-000000000002"
READER_ROLE_ID="a1b2c3d4-0001-0001-0001-000000000003"

# ── 1. API app registration ─────────────────────────

echo "==> Creating API app registration: $API_APP_NAME"
API_APP_ID=$(az ad app create \
  --display-name "$API_APP_NAME" \
  --query appId \
  --output tsv)

API_OBJ_ID=$(az ad app show --id "$API_APP_ID" --query id --output tsv)

echo "==> Creating service principal for API app"
API_SP_ID=$(az ad sp create --id "$API_APP_ID" --query id --output tsv 2>/dev/null) || \
API_SP_ID=$(az ad sp show --id "$API_APP_ID" --query id --output tsv)

echo "==> Setting identifier URI: api://$API_APP_ID"
az ad app update --id "$API_APP_ID" \
  --identifier-uris "api://$API_APP_ID"

# Generate a UUID for the scope
SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "==> Exposing scope + defining App Roles"
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
    },
    \"appRoles\": [
      {
        \"allowedMemberTypes\": [\"User\"],
        \"description\": \"Full access: manage all tasks and users\",
        \"displayName\": \"Admin\",
        \"id\": \"$ADMIN_ROLE_ID\",
        \"isEnabled\": true,
        \"value\": \"Admin\"
      },
      {
        \"allowedMemberTypes\": [\"User\"],
        \"description\": \"Create, read, and update own tasks\",
        \"displayName\": \"Editor\",
        \"id\": \"$EDITOR_ROLE_ID\",
        \"isEnabled\": true,
        \"value\": \"Editor\"
      },
      {
        \"allowedMemberTypes\": [\"User\"],
        \"description\": \"Read-only access to own tasks\",
        \"displayName\": \"Reader\",
        \"id\": \"$READER_ROLE_ID\",
        \"isEnabled\": true,
        \"value\": \"Reader\"
      }
    ]
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
az ad sp create --id "$SPA_APP_ID" --output none 2>/dev/null || true

echo "==> Setting SPA redirect URI: $REDIRECT_URI"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$SPA_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"spa\":{\"redirectUris\":[\"$REDIRECT_URI\"]}}"

# ── 3. Create test users ────────────────────────────

EDITOR_UPN="testuser-editor@${DOMAIN}"
READER_UPN="testuser-reader@${DOMAIN}"
TEMP_PASSWORD="SecureP@ss123!"

echo "==> Creating test user: $EDITOR_UPN"
EDITOR_OBJ_ID=$(az ad user create \
  --display-name "Test Editor" \
  --user-principal-name "$EDITOR_UPN" \
  --password "$TEMP_PASSWORD" \
  --force-change-password-next-sign-in false \
  --query id --output tsv 2>/dev/null) || \
EDITOR_OBJ_ID=$(az ad user show --id "$EDITOR_UPN" --query id --output tsv)

echo "==> Creating test user: $READER_UPN"
READER_OBJ_ID=$(az ad user create \
  --display-name "Test Reader" \
  --user-principal-name "$READER_UPN" \
  --password "$TEMP_PASSWORD" \
  --force-change-password-next-sign-in false \
  --query id --output tsv 2>/dev/null) || \
READER_OBJ_ID=$(az ad user show --id "$READER_UPN" --query id --output tsv)

# Get current user's object ID for Admin role
MY_OBJ_ID=$(az ad signed-in-user show --query id --output tsv)

# ── 4. Assign roles ─────────────────────────────────

echo "==> Assigning Admin role to your account"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$MY_OBJ_ID\",
    \"resourceId\": \"$API_SP_ID\",
    \"appRoleId\": \"$ADMIN_ROLE_ID\"
  }" --output none 2>/dev/null || echo "   (Admin role may already be assigned)"

echo "==> Assigning Editor role to $EDITOR_UPN"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$EDITOR_OBJ_ID\",
    \"resourceId\": \"$API_SP_ID\",
    \"appRoleId\": \"$EDITOR_ROLE_ID\"
  }" --output none 2>/dev/null || echo "   (Editor role may already be assigned)"

echo "==> Assigning Reader role to $READER_UPN"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$READER_OBJ_ID\",
    \"resourceId\": \"$API_SP_ID\",
    \"appRoleId\": \"$READER_ROLE_ID\"
  }" --output none 2>/dev/null || echo "   (Reader role may already be assigned)"

# ── 5. Write env files ──────────────────────────────

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
echo "==> Done! App registrations created."
echo ""
echo "   API App:      $API_APP_ID"
echo "   SPA App:      $SPA_APP_ID"
echo "   Tenant:       $TENANT_ID"
echo "   API Scope:    api://$API_APP_ID/$SCOPE_NAME"
echo ""
echo "   Test accounts:"
echo "   ┌──────────────────────────────────────────────┐"
echo "   │ Role    │ Username              │ Password    │"
echo "   ├──────────────────────────────────────────────┤"
echo "   │ Admin   │ (your account)        │ (yours)     │"
echo "   │ Editor  │ $EDITOR_UPN           │ $TEMP_PASSWORD │"
echo "   │ Reader  │ $READER_UPN           │ $TEMP_PASSWORD │"
echo "   └──────────────────────────────────────────────┘"
echo ""
echo "==> Next steps:"
echo "   1. Local dev:  cd backend && pip install -r requirements.txt && uvicorn main:app --reload"
echo "   2. Local dev:  cd frontend && npm install && npm run dev"
echo "   3. Deploy:     cd infra && terraform init && terraform apply"
echo "   4. Deploy:     ./deploy.sh"

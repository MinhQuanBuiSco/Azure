#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 5 — Multi-Tenant: Azure AD Setup
#
# Creates:
#   1. API app with 3 App Roles (Admin/Editor/Reader)
#      → signInAudience = AzureADMultipleOrgs
#   2. SPA frontend app (also multi-tenant)
#   3. Two test users (editor + reader) in your home tenant
#   4. Role assignments for all 3 users
#   5. Writes .env files for local dev
#   6. Prints admin consent URL for onboarding other tenants
# ──────────────────────────────────────────────────────

API_APP_NAME="${1:-Blog5-MT-API}"
SPA_APP_NAME="${2:-Blog5-MT-Frontend}"
REDIRECT_URI="http://localhost:3000"
SCOPE_NAME="access_as_user"
GRAPH_API="00000003-0000-0000-c000-000000000000"
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

TENANT_ID=$(az account show --query tenantId --output tsv)
DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv)

# Role IDs (fixed UUIDs for consistency)
ADMIN_ROLE_ID="a1b2c3d4-0005-0005-0005-000000000001"
EDITOR_ROLE_ID="a1b2c3d4-0005-0005-0005-000000000002"
READER_ROLE_ID="a1b2c3d4-0005-0005-0005-000000000003"

# ── 1. API app registration (multi-tenant) ──────────

echo "==> Creating multi-tenant API app: $API_APP_NAME"
API_APP_ID=$(az ad app create \
  --display-name "$API_APP_NAME" \
  --sign-in-audience AzureADMultipleOrgs \
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
        \"description\": \"Full access: manage all tasks in the tenant\",
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

# ── 2. SPA frontend app registration (multi-tenant) ─

echo "==> Creating multi-tenant SPA app: $SPA_APP_NAME"
SPA_APP_ID=$(az ad app create \
  --display-name "$SPA_APP_NAME" \
  --sign-in-audience AzureADMultipleOrgs \
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

# ── 3. Create test users (home tenant) ──────────────
# All three roles get proper organizational accounts so App Roles work.

ADMIN_UPN="testuser-admin@${DOMAIN}"
EDITOR_UPN="testuser-editor@${DOMAIN}"
READER_UPN="testuser-reader@${DOMAIN}"
TEMP_PASSWORD="SecureP@ss123!"

echo "==> Creating test user: $ADMIN_UPN"
ADMIN_OBJ_ID=$(az ad user create \
  --display-name "Test Admin" \
  --user-principal-name "$ADMIN_UPN" \
  --password "$TEMP_PASSWORD" \
  --force-change-password-next-sign-in false \
  --query id --output tsv 2>/dev/null) || \
ADMIN_OBJ_ID=$(az ad user show --id "$ADMIN_UPN" --query id --output tsv)

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

# ── 4. Assign roles ─────────────────────────────────

echo "==> Assigning Admin role to $ADMIN_UPN"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$ADMIN_OBJ_ID\",
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
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_API_CLIENT_ID=$API_APP_ID
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
EOF

echo "==> Writing frontend/.env.local"
cat > "$SCRIPT_DIR/frontend/.env.local" <<EOF
# Multi-tenant — authority is "organizations" (set in auth-config.ts)
NEXT_PUBLIC_AZURE_CLIENT_ID=$SPA_APP_ID
NEXT_PUBLIC_API_SCOPE=api://$API_APP_ID/$SCOPE_NAME
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# ── Done ────────────────────────────────────────────

CONSENT_URL="https://login.microsoftonline.com/organizations/adminconsent?client_id=$API_APP_ID"

echo ""
echo "==> Done! Multi-tenant app registrations created."
echo ""
echo "   API App:      $API_APP_ID  (signInAudience: AzureADMultipleOrgs)"
echo "   SPA App:      $SPA_APP_ID  (signInAudience: AzureADMultipleOrgs)"
echo "   Home Tenant:  $TENANT_ID"
echo "   API Scope:    api://$API_APP_ID/$SCOPE_NAME"
echo ""
echo "   Test accounts (home tenant):"
echo "   ┌──────────────────────────────────────────────┐"
echo "   │ Role    │ Username              │ Password    │"
echo "   ├──────────────────────────────────────────────┤"
echo "   │ Admin   │ $ADMIN_UPN            │ $TEMP_PASSWORD │"
echo "   │ Editor  │ $EDITOR_UPN           │ $TEMP_PASSWORD │"
echo "   │ Reader  │ $READER_UPN           │ $TEMP_PASSWORD │"
echo "   └──────────────────────────────────────────────┘"
echo ""
echo "   Admin consent URL (for onboarding other tenants):"
echo "   $CONSENT_URL"
echo ""
echo "==> Next steps:"
echo "   1. cd backend  && pip install -r requirements.txt && uvicorn main:app --reload"
echo "   2. cd frontend && npm install && npm run dev"
echo "   3. To onboard another tenant, share the admin consent URL above."
echo "      Then add their tenant ID to ALLOWED_TENANT_IDS in backend/.env."

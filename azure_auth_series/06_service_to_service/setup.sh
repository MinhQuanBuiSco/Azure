#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 6 — Service-to-Service: Azure AD Setup
#
# Creates:
#   1. Task API app (multi-tenant, with client secret)
#   2. SPA Frontend app (multi-tenant)
#   3. Notification Service app (single-tenant, OBO target)
#   4. Audit Service app (single-tenant, client cred target)
#   5. API permissions + admin consent
#   6. Three test users with role assignments
#   7. Writes .env files for all services + frontend
# ──────────────────────────────────────────────────────

API_APP_NAME="${1:-Blog6-S2S-API}"
SPA_APP_NAME="${2:-Blog6-S2S-Frontend}"
NOTIFY_APP_NAME="${3:-Blog6-S2S-Notification}"
AUDIT_APP_NAME="${4:-Blog6-S2S-Audit}"
REDIRECT_URI="http://localhost:3000"
SCOPE_NAME="access_as_user"
GRAPH_API="00000003-0000-0000-c000-000000000000"
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

TENANT_ID=$(az account show --query tenantId --output tsv)
DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv)

# Fixed UUIDs for consistency
ADMIN_ROLE_ID="a1b2c3d4-0006-0006-0006-000000000001"
EDITOR_ROLE_ID="a1b2c3d4-0006-0006-0006-000000000002"
READER_ROLE_ID="a1b2c3d4-0006-0006-0006-000000000003"
AUDIT_WRITE_ROLE_ID="a1b2c3d4-0006-0006-0006-000000000010"

# ── 1. Notification Service app (single-tenant) ──────
# Must be created first so Task API can reference its scope.

echo "==> Creating Notification Service app: $NOTIFY_APP_NAME"
NOTIFY_APP_ID=$(az ad app create \
  --display-name "$NOTIFY_APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --query appId \
  --output tsv)

NOTIFY_OBJ_ID=$(az ad app show --id "$NOTIFY_APP_ID" --query id --output tsv)

echo "==> Creating service principal for Notification app"
NOTIFY_SP_ID=$(az ad sp create --id "$NOTIFY_APP_ID" --query id --output tsv 2>/dev/null) || \
NOTIFY_SP_ID=$(az ad sp show --id "$NOTIFY_APP_ID" --query id --output tsv)

echo "==> Setting identifier URI: api://$NOTIFY_APP_ID"
az ad app update --id "$NOTIFY_APP_ID" \
  --identifier-uris "api://$NOTIFY_APP_ID"

NOTIFY_SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "==> Exposing Notification delegated scope: Notify.Send"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$NOTIFY_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"oauth2PermissionScopes\": [{
        \"adminConsentDescription\": \"Send notifications on behalf of the user\",
        \"adminConsentDisplayName\": \"Send Notifications\",
        \"id\": \"$NOTIFY_SCOPE_ID\",
        \"isEnabled\": true,
        \"type\": \"User\",
        \"userConsentDescription\": \"Allow sending notifications on your behalf\",
        \"userConsentDisplayName\": \"Send Notifications\",
        \"value\": \"Notify.Send\"
      }]
    }
  }"

# ── 2. Audit Service app (single-tenant) ─────────────
# App role only (no delegated scopes) — for client credentials.

echo "==> Creating Audit Service app: $AUDIT_APP_NAME"
AUDIT_APP_ID=$(az ad app create \
  --display-name "$AUDIT_APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --query appId \
  --output tsv)

AUDIT_OBJ_ID=$(az ad app show --id "$AUDIT_APP_ID" --query id --output tsv)

echo "==> Creating service principal for Audit app"
AUDIT_SP_ID=$(az ad sp create --id "$AUDIT_APP_ID" --query id --output tsv 2>/dev/null) || \
AUDIT_SP_ID=$(az ad sp show --id "$AUDIT_APP_ID" --query id --output tsv)

echo "==> Setting identifier URI: api://$AUDIT_APP_ID"
az ad app update --id "$AUDIT_APP_ID" \
  --identifier-uris "api://$AUDIT_APP_ID"

echo "==> Defining AuditLog.Write app role"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$AUDIT_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"appRoles\": [{
      \"allowedMemberTypes\": [\"Application\"],
      \"description\": \"Write audit log entries\",
      \"displayName\": \"AuditLog.Write\",
      \"id\": \"$AUDIT_WRITE_ROLE_ID\",
      \"isEnabled\": true,
      \"value\": \"AuditLog.Write\"
    }]
  }"

# ── 3. Task API app (multi-tenant, with secret) ──────

echo "==> Creating multi-tenant Task API app: $API_APP_NAME"
API_APP_ID=$(az ad app create \
  --display-name "$API_APP_NAME" \
  --sign-in-audience AzureADMultipleOrgs \
  --query appId \
  --output tsv)

API_OBJ_ID=$(az ad app show --id "$API_APP_ID" --query id --output tsv)

echo "==> Creating service principal for Task API"
API_SP_ID=$(az ad sp create --id "$API_APP_ID" --query id --output tsv 2>/dev/null) || \
API_SP_ID=$(az ad sp show --id "$API_APP_ID" --query id --output tsv)

echo "==> Setting identifier URI: api://$API_APP_ID"
az ad app update --id "$API_APP_ID" \
  --identifier-uris "api://$API_APP_ID"

API_SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "==> Exposing scope + defining App Roles for Task API"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$API_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"oauth2PermissionScopes\": [{
        \"adminConsentDescription\": \"Allow the app to access the API on behalf of the signed-in user\",
        \"adminConsentDisplayName\": \"Access API as user\",
        \"id\": \"$API_SCOPE_ID\",
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

echo "==> Adding client secret for Task API (needed for OBO + client cred)"
API_SECRET=$(az ad app credential reset \
  --id "$API_APP_ID" \
  --display-name "blog6-secret" \
  --years 1 \
  --query password \
  --output tsv)

# Add knownClientApplications to Notification Service (enables combined consent)
echo "==> Setting knownClientApplications on Notification Service"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$NOTIFY_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"knownClientApplications\": [\"$API_APP_ID\"],
      \"oauth2PermissionScopes\": [{
        \"adminConsentDescription\": \"Send notifications on behalf of the user\",
        \"adminConsentDisplayName\": \"Send Notifications\",
        \"id\": \"$NOTIFY_SCOPE_ID\",
        \"isEnabled\": true,
        \"type\": \"User\",
        \"userConsentDescription\": \"Allow sending notifications on your behalf\",
        \"userConsentDisplayName\": \"Send Notifications\",
        \"value\": \"Notify.Send\"
      }]
    }
  }"

# ── Add API permissions to Task API ───────────────────

echo "==> Adding API permissions to Task API"
az ad app update --id "$API_APP_ID" \
  --required-resource-accesses "[
    {
      \"resourceAppId\": \"$GRAPH_API\",
      \"resourceAccess\": [{
        \"id\": \"$USER_READ\",
        \"type\": \"Scope\"
      }]
    },
    {
      \"resourceAppId\": \"$NOTIFY_APP_ID\",
      \"resourceAccess\": [{
        \"id\": \"$NOTIFY_SCOPE_ID\",
        \"type\": \"Scope\"
      }]
    },
    {
      \"resourceAppId\": \"$AUDIT_APP_ID\",
      \"resourceAccess\": [{
        \"id\": \"$AUDIT_WRITE_ROLE_ID\",
        \"type\": \"Role\"
      }]
    }
  ]"

# ── 4. SPA Frontend app (multi-tenant) ───────────────

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
        \"id\": \"$API_SCOPE_ID\",
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

# ── 5. Grant admin consent for Task API → Audit Service ─

echo "==> Granting admin consent: Task API → Audit Service (AuditLog.Write)"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$API_SP_ID\",
    \"resourceId\": \"$AUDIT_SP_ID\",
    \"appRoleId\": \"$AUDIT_WRITE_ROLE_ID\"
  }" --output none 2>/dev/null || echo "   (App role may already be assigned)"

echo "==> Granting admin consent: Task API → Notification Service (Notify.Send delegated)"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/oauth2PermissionGrants" \
  --headers "Content-Type=application/json" \
  --body "{
    \"clientId\": \"$API_SP_ID\",
    \"consentType\": \"AllPrincipals\",
    \"resourceId\": \"$NOTIFY_SP_ID\",
    \"scope\": \"Notify.Send\"
  }" --output none 2>/dev/null || echo "   (Delegated consent may already be granted)"

# ── 6. Create test users ─────────────────────────────

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

# ── 7. Assign roles ──────────────────────────────────

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

# ── 8. Write env files ────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Writing task-api/.env"
cat > "$SCRIPT_DIR/task-api/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_API_CLIENT_ID=$API_APP_ID
AZURE_API_CLIENT_SECRET=$API_SECRET
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false

# Downstream services
AZURE_NOTIFICATION_CLIENT_ID=$NOTIFY_APP_ID
NOTIFICATION_URL=http://localhost:8001
AZURE_AUDIT_CLIENT_ID=$AUDIT_APP_ID
AUDIT_URL=http://localhost:8002
EOF

echo "==> Writing notification-service/.env"
cat > "$SCRIPT_DIR/notification-service/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_NOTIFICATION_CLIENT_ID=$NOTIFY_APP_ID
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
EOF

echo "==> Writing audit-service/.env"
cat > "$SCRIPT_DIR/audit-service/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_AUDIT_CLIENT_ID=$AUDIT_APP_ID
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
EOF

echo "==> Writing frontend/.env.local"
cat > "$SCRIPT_DIR/frontend/.env.local" <<EOF
NEXT_PUBLIC_AZURE_CLIENT_ID=$SPA_APP_ID
NEXT_PUBLIC_API_SCOPE=api://$API_APP_ID/$SCOPE_NAME
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# ── Done ──────────────────────────────────────────────

echo ""
echo "==> Done! Blog 6 app registrations created."
echo ""
echo "   Task API:             $API_APP_ID  (multi-tenant + client secret)"
echo "   SPA Frontend:         $SPA_APP_ID  (multi-tenant)"
echo "   Notification Service: $NOTIFY_APP_ID  (single-tenant, OBO target)"
echo "   Audit Service:        $AUDIT_APP_ID  (single-tenant, app role)"
echo "   Home Tenant:          $TENANT_ID"
echo ""
echo "   Test accounts:"
echo "   ┌────────────────────────────────────────────────────┐"
echo "   │ Role    │ Username               │ Password         │"
echo "   ├────────────────────────────────────────────────────┤"
echo "   │ Admin   │ $ADMIN_UPN             │ $TEMP_PASSWORD   │"
echo "   │ Editor  │ $EDITOR_UPN            │ $TEMP_PASSWORD   │"
echo "   │ Reader  │ $READER_UPN            │ $TEMP_PASSWORD   │"
echo "   └────────────────────────────────────────────────────┘"
echo ""
echo "==> Next steps:"
echo "   1. cd task-api             && pip install -r requirements.txt && uvicorn main:app --reload --port 8000"
echo "   2. cd notification-service && pip install -r requirements.txt && uvicorn main:app --reload --port 8001"
echo "   3. cd audit-service        && pip install -r requirements.txt && uvicorn main:app --reload --port 8002"
echo "   4. cd frontend             && npm install && npm run dev"
echo "   5. Sign in → create a task → check service logs for OBO + client cred calls"

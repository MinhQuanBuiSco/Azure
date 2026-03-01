#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 8 — Production Readiness: Full Setup
#
# Creates:
#   1. Same 4 AD app registrations as Blog 7
#   2. Same 3 test users with role assignments
#   3. Terraform: RG + ACR + 4 Container Apps + APIM + App Insights + Alerts
#   4. Docker build + push to ACR
#   5. Update Container Apps with real images
#   6. Write .env files (services + frontend)
#   7. Verify monitoring setup
#
# Requires:
#   - az CLI (logged in)
#   - terraform
#   - docker
#   - Unique names for ACR and APIM (set below)
# ──────────────────────────────────────────────────────

API_APP_NAME="${1:-Blog8-Prod-API}"
SPA_APP_NAME="${2:-Blog8-Prod-Frontend}"
NOTIFY_APP_NAME="${3:-Blog8-Prod-Notification}"
AUDIT_APP_NAME="${4:-Blog8-Prod-Audit}"
REDIRECT_URI="http://localhost:3000"
SCOPE_NAME="access_as_user"
GRAPH_API="00000003-0000-0000-c000-000000000000"
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Prompt for globally unique names ──────────────────

echo ""
echo "==> Blog 8: Production Readiness Setup"
echo ""

# ACR name (alphanumeric only, globally unique)
if [[ -z "${ACR_NAME:-}" ]]; then
  read -rp "   ACR name (alphanumeric, globally unique, e.g. blog08acr): " ACR_NAME
fi
# APIM name (globally unique)
if [[ -z "${APIM_NAME:-}" ]]; then
  read -rp "   APIM name (globally unique, e.g. blog08-apim): " APIM_NAME
fi
# Publisher email
if [[ -z "${PUBLISHER_EMAIL:-}" ]]; then
  read -rp "   Publisher email (for APIM): " PUBLISHER_EMAIL
fi
# Alert email
if [[ -z "${ALERT_EMAIL:-}" ]]; then
  read -rp "   Alert email (for Azure Monitor alerts): " ALERT_EMAIL
fi

TENANT_ID=$(az account show --query tenantId --output tsv)
DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv)

# Fixed UUIDs for consistency
ADMIN_ROLE_ID="a1b2c3d4-0008-0008-0008-000000000001"
EDITOR_ROLE_ID="a1b2c3d4-0008-0008-0008-000000000002"
READER_ROLE_ID="a1b2c3d4-0008-0008-0008-000000000003"
AUDIT_WRITE_ROLE_ID="a1b2c3d4-0008-0008-0008-000000000010"

# ════════════════════════════════════════════════════════
# PHASE 1: Azure AD Setup
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 1: Azure AD app registrations ==="
echo ""

# ── 1. Notification Service app (single-tenant) ──────

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

NOTIFY_SCOPE_ID=$(az ad app show --id "$NOTIFY_APP_ID" \
  --query "api.oauth2PermissionScopes[?value=='Notify.Send'].id | [0]" --output tsv)

if [[ -z "$NOTIFY_SCOPE_ID" || "$NOTIFY_SCOPE_ID" == "None" ]]; then
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
else
  echo "==> Notification scope Notify.Send already exists (id: $NOTIFY_SCOPE_ID), skipping"
fi

# ── 2. Audit Service app (single-tenant) ─────────────

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

API_SCOPE_ID=$(az ad app show --id "$API_APP_ID" \
  --query "api.oauth2PermissionScopes[?value=='$SCOPE_NAME'].id | [0]" --output tsv)

if [[ -z "$API_SCOPE_ID" || "$API_SCOPE_ID" == "None" ]]; then
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
else
  echo "==> Task API scope $SCOPE_NAME already exists (id: $API_SCOPE_ID), skipping"
fi

echo "==> Adding client secret for Task API"
API_SECRET=$(az ad app credential reset \
  --id "$API_APP_ID" \
  --display-name "blog8-secret" \
  --years 1 \
  --query password \
  --output tsv)

# knownClientApplications for combined consent
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

# ── 5. Grant admin consent ────────────────────────────

echo "==> Granting admin consent: Task API → Audit Service (AuditLog.Write)"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$API_SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$API_SP_ID\",
    \"resourceId\": \"$AUDIT_SP_ID\",
    \"appRoleId\": \"$AUDIT_WRITE_ROLE_ID\"
  }" --output none 2>/dev/null || echo "   (App role may already be assigned)"

echo "==> Granting admin consent: Task API → Notification Service (Notify.Send)"
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

# ════════════════════════════════════════════════════════
# PHASE 2: Terraform Infrastructure
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 2: Terraform infrastructure ==="
echo ""

cd "$SCRIPT_DIR/infra"

echo "==> Writing terraform.tfvars"
cat > terraform.tfvars <<EOF
project_name        = "blog08-prod"
resource_group_name = "rg-blog08-production"
location            = "australiaeast"
acr_name            = "$ACR_NAME"
apim_name           = "$APIM_NAME"
publisher_email     = "$PUBLISHER_EMAIL"
tenant_id              = "$TENANT_ID"
task_api_client_id     = "$API_APP_ID"
task_api_client_secret = "$API_SECRET"
notification_client_id = "$NOTIFY_APP_ID"
audit_client_id        = "$AUDIT_APP_ID"
allowed_origins        = "http://localhost:3000"
alert_email            = "$ALERT_EMAIL"
EOF

echo "==> terraform init"
terraform init

echo "==> terraform apply (this will take 30-45 minutes due to APIM Developer tier)"
terraform apply -auto-approve

# Capture outputs
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
APIM_GATEWAY_URL=$(terraform output -raw apim_gateway_url)
TASK_API_URL=$(terraform output -raw task_api_url)
NOTIFICATION_URL=$(terraform output -raw notification_url)
AUDIT_URL=$(terraform output -raw audit_url)
FRONTEND_URL=$(terraform output -raw frontend_url)
APPINSIGHTS_NAME=$(terraform output -raw app_insights_name)

cd "$SCRIPT_DIR"

# ════════════════════════════════════════════════════════
# PHASE 3: Docker Build + Push
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 3: Docker build + push ==="
echo ""

echo "==> Logging in to ACR: $ACR_LOGIN_SERVER"
az acr login --name "$ACR_NAME"

echo "==> Building and pushing task-api"
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/task-api:latest" "$SCRIPT_DIR/task-api"
docker push "$ACR_LOGIN_SERVER/task-api:latest"

echo "==> Building and pushing notification-service"
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/notification-service:latest" "$SCRIPT_DIR/notification-service"
docker push "$ACR_LOGIN_SERVER/notification-service:latest"

echo "==> Building and pushing audit-service"
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/audit-service:latest" "$SCRIPT_DIR/audit-service"
docker push "$ACR_LOGIN_SERVER/audit-service:latest"

echo "==> Building and pushing frontend (baking NEXT_PUBLIC_* env vars)"
docker build --platform linux/amd64 \
  --build-arg "NEXT_PUBLIC_AZURE_CLIENT_ID=$SPA_APP_ID" \
  --build-arg "NEXT_PUBLIC_API_SCOPE=api://$API_APP_ID/$SCOPE_NAME" \
  --build-arg "NEXT_PUBLIC_API_URL=$APIM_GATEWAY_URL" \
  -t "$ACR_LOGIN_SERVER/frontend:latest" \
  "$SCRIPT_DIR/frontend"
docker push "$ACR_LOGIN_SERVER/frontend:latest"

# ════════════════════════════════════════════════════════
# PHASE 4: Update Container Apps with real images
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 4: Updating Container Apps ==="
echo ""

RG_NAME="rg-blog08-production"

echo "==> Updating task-api container app"
az containerapp update \
  --name task-api \
  --resource-group "$RG_NAME" \
  --image "$ACR_LOGIN_SERVER/task-api:latest" \
  --output none

echo "==> Updating notification-svc container app"
az containerapp update \
  --name notification-svc \
  --resource-group "$RG_NAME" \
  --image "$ACR_LOGIN_SERVER/notification-service:latest" \
  --output none

echo "==> Updating audit-svc container app"
az containerapp update \
  --name audit-svc \
  --resource-group "$RG_NAME" \
  --image "$ACR_LOGIN_SERVER/audit-service:latest" \
  --output none

echo "==> Updating frontend container app"
az containerapp update \
  --name frontend \
  --resource-group "$RG_NAME" \
  --image "$ACR_LOGIN_SERVER/frontend:latest" \
  --output none

# ── Update SPA redirect URIs to include deployed frontend ──

echo "==> Updating SPA redirect URIs (localhost + deployed)"
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$SPA_OBJ_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"spa\":{\"redirectUris\":[\"$REDIRECT_URI\",\"$FRONTEND_URL\"]}}"

# ════════════════════════════════════════════════════════
# PHASE 5: Write .env files
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 5: Writing .env files ==="
echo ""

echo "==> Writing task-api/.env (for local dev)"
cat > "$SCRIPT_DIR/task-api/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_API_CLIENT_ID=$API_APP_ID
AZURE_API_CLIENT_SECRET=$API_SECRET
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
TRUST_GATEWAY=false

# Downstream services (local dev — direct URLs)
AZURE_NOTIFICATION_CLIENT_ID=$NOTIFY_APP_ID
NOTIFICATION_URL=http://localhost:8001
AZURE_AUDIT_CLIENT_ID=$AUDIT_APP_ID
AUDIT_URL=http://localhost:8002

# Application Insights (leave empty for local dev, set for cloud testing)
# APPLICATIONINSIGHTS_CONNECTION_STRING=
EOF

echo "==> Writing notification-service/.env (for local dev)"
cat > "$SCRIPT_DIR/notification-service/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_NOTIFICATION_CLIENT_ID=$NOTIFY_APP_ID
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
TRUST_GATEWAY=false

# Application Insights (leave empty for local dev)
# APPLICATIONINSIGHTS_CONNECTION_STRING=
EOF

echo "==> Writing audit-service/.env (for local dev)"
cat > "$SCRIPT_DIR/audit-service/.env" <<EOF
AZURE_HOME_TENANT_ID=$TENANT_ID
AZURE_AUDIT_CLIENT_ID=$AUDIT_APP_ID
ALLOWED_TENANT_IDS=$TENANT_ID
# ALLOW_ANY_TENANT=false
TRUST_GATEWAY=false

# Application Insights (leave empty for local dev)
# APPLICATIONINSIGHTS_CONNECTION_STRING=
EOF

echo "==> Writing frontend/.env.local (points to APIM gateway)"
cat > "$SCRIPT_DIR/frontend/.env.local" <<EOF
NEXT_PUBLIC_AZURE_CLIENT_ID=$SPA_APP_ID
NEXT_PUBLIC_API_SCOPE=api://$API_APP_ID/$SCOPE_NAME
NEXT_PUBLIC_API_URL=$APIM_GATEWAY_URL
EOF

# ════════════════════════════════════════════════════════
# PHASE 6: Verify Monitoring
# ════════════════════════════════════════════════════════

echo ""
echo "=== Phase 6: Verifying monitoring ==="
echo ""

echo "==> Application Insights: $APPINSIGHTS_NAME"
echo "    View in Azure Portal:"
echo "    https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/microsoft.insights%2Fcomponents"
echo ""
echo "==> Alert rules configured:"
echo "    - High error rate: >10 failed requests in 5 minutes (Severity 2)"
echo "    - Slow response: avg >5s over 5 minutes (Severity 3)"
echo "    - Alerts sent to: $ALERT_EMAIL"
echo ""
echo "==> Security hardening:"
echo "    - notification-svc: internal ingress only (not publicly reachable)"
echo "    - audit-svc: internal ingress only (not publicly reachable)"
echo "    - frontend: external ingress (Azure-hosted Next.js)"
echo "    - All services: health probes (liveness + readiness)"
echo "    - All services: auto-scaling min=1, max=3"

# ── Done ──────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Blog 8: Production Readiness — Setup Complete!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Azure AD:"
echo "    Task API:             $API_APP_ID"
echo "    SPA Frontend:         $SPA_APP_ID"
echo "    Notification Service: $NOTIFY_APP_ID"
echo "    Audit Service:        $AUDIT_APP_ID"
echo ""
echo "  Infrastructure:"
echo "    Frontend URL:         $FRONTEND_URL"
echo "    APIM Gateway URL:     $APIM_GATEWAY_URL"
echo "    Task API URL:         $TASK_API_URL"
echo "    Notification URL:     $NOTIFICATION_URL (internal only)"
echo "    Audit URL:            $AUDIT_URL (internal only)"
echo "    ACR:                  $ACR_LOGIN_SERVER"
echo "    App Insights:         $APPINSIGHTS_NAME"
echo ""
echo "  Test accounts:"
echo "    ┌──────────────────────────────────────────────┐"
echo "    │ Role    │ Username               │ Password  │"
echo "    ├──────────────────────────────────────────────┤"
echo "    │ Admin   │ $ADMIN_UPN"
echo "    │ Editor  │ $EDITOR_UPN"
echo "    │ Reader  │ $READER_UPN"
echo "    │ Password: $TEMP_PASSWORD"
echo "    └──────────────────────────────────────────────┘"
echo ""
echo "  Next steps:"
echo "    1. Open $FRONTEND_URL"
echo "    2. Sign in → create tasks → verify Notify + Audit"
echo "    3. Check App Insights → Live Metrics → see requests flowing"
echo "    4. Check App Insights → Logs → run KQL queries from kql/"
echo "    5. Verify internal services are not publicly reachable"
echo ""
echo "  Cost warning:"
echo "    APIM Developer tier ~\$50/month. Run cleanup.sh when done!"
echo "    App Insights free tier = 5 GB/month ingestion."
echo ""

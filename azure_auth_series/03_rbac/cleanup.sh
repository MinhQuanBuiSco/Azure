#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 3 — RBAC: Cleanup
# Deletes app registrations, test users, and env files
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_ENV="$SCRIPT_DIR/backend/.env"
FRONTEND_ENV="$SCRIPT_DIR/frontend/.env.local"

# Read API client ID from backend .env
if [[ ! -f "$BACKEND_ENV" ]]; then
  echo "ERROR: $BACKEND_ENV not found. Nothing to clean up."
  exit 1
fi
API_APP_ID=$(grep AZURE_API_CLIENT_ID "$BACKEND_ENV" | cut -d'=' -f2)

# Read SPA client ID from frontend .env.local
if [[ ! -f "$FRONTEND_ENV" ]]; then
  echo "ERROR: $FRONTEND_ENV not found."
  exit 1
fi
SPA_APP_ID=$(grep NEXT_PUBLIC_AZURE_CLIENT_ID "$FRONTEND_ENV" | cut -d'=' -f2)

# Get tenant domain for test user UPNs
DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv)

echo "==> Deleting test user: testuser-editor@${DOMAIN}"
az ad user delete --id "testuser-editor@${DOMAIN}" 2>/dev/null || echo "   (user not found)"

echo "==> Deleting test user: testuser-reader@${DOMAIN}"
az ad user delete --id "testuser-reader@${DOMAIN}" 2>/dev/null || echo "   (user not found)"

echo "==> Deleting API app registration: $API_APP_ID"
az ad app delete --id "$API_APP_ID"

echo "==> Deleting SPA app registration: $SPA_APP_ID"
az ad app delete --id "$SPA_APP_ID"

echo "==> Removing env files"
rm -f "$BACKEND_ENV" "$FRONTEND_ENV"

echo ""
echo "==> Done! App registrations and test users deleted."

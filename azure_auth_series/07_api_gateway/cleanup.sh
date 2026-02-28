#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 7 — Cleanup: Destroy all resources
#
# 1. Terraform destroy (RG + ACR + Container Apps + APIM)
# 2. Delete 4 app registrations
# 3. Delete 3 test users
# 4. Remove local .env files
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

API_APP_NAME="${1:-Blog7-APIGW-API}"
SPA_APP_NAME="${2:-Blog7-APIGW-Frontend}"
NOTIFY_APP_NAME="${3:-Blog7-APIGW-Notification}"
AUDIT_APP_NAME="${4:-Blog7-APIGW-Audit}"

echo ""
echo "==> This will DESTROY all Blog 7 resources:"
echo "    - Terraform infrastructure (RG, ACR, Container Apps, APIM)"
echo "    - App registrations ($API_APP_NAME, $SPA_APP_NAME, $NOTIFY_APP_NAME, $AUDIT_APP_NAME)"
echo "    - Test users (testuser-admin, testuser-editor, testuser-reader)"
echo ""
read -rp "    Continue? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "    Aborted."
  exit 0
fi

# ── 1. Terraform destroy ──────────────────────────────

if [[ -d "$SCRIPT_DIR/infra" ]] && [[ -f "$SCRIPT_DIR/infra/terraform.tfvars" ]]; then
  echo ""
  echo "==> Destroying Terraform infrastructure..."
  cd "$SCRIPT_DIR/infra"
  terraform destroy -auto-approve
  cd "$SCRIPT_DIR"
else
  echo ""
  echo "==> No terraform.tfvars found — skipping terraform destroy"
fi

# ── 2. Delete app registrations ──────────────────────

echo ""
echo "==> Deleting app registrations..."

for APP_NAME in "$API_APP_NAME" "$SPA_APP_NAME" "$NOTIFY_APP_NAME" "$AUDIT_APP_NAME"; do
  echo "    Deleting: $APP_NAME"
  APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" --output tsv 2>/dev/null || true)
  if [[ -n "$APP_ID" ]]; then
    az ad app delete --id "$APP_ID"
    echo "    Deleted: $APP_ID"
  else
    echo "    (Not found — skipping)"
  fi
done

# ── 3. Delete test users ─────────────────────────────

DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv 2>/dev/null || true)

if [[ -n "$DOMAIN" ]]; then
  echo ""
  echo "==> Deleting test users..."
  for UPN in "testuser-admin@${DOMAIN}" "testuser-editor@${DOMAIN}" "testuser-reader@${DOMAIN}"; do
    echo "    Deleting: $UPN"
    az ad user delete --id "$UPN" 2>/dev/null || echo "    (Not found — skipping)"
  done
fi

# ── 4. Clean up local files ──────────────────────────

echo ""
echo "==> Cleaning up local files..."
rm -f "$SCRIPT_DIR/task-api/.env"
rm -f "$SCRIPT_DIR/notification-service/.env"
rm -f "$SCRIPT_DIR/audit-service/.env"
rm -f "$SCRIPT_DIR/frontend/.env.local"
rm -f "$SCRIPT_DIR/infra/terraform.tfvars"

echo ""
echo "==> Cleanup complete! All Blog 7 resources destroyed."

#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 6 — Cleanup: Delete all AD objects
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

API_APP_NAME="${1:-Blog6-S2S-API}"
SPA_APP_NAME="${2:-Blog6-S2S-Frontend}"
NOTIFY_APP_NAME="${3:-Blog6-S2S-Notification}"
AUDIT_APP_NAME="${4:-Blog6-S2S-Audit}"

echo "==> This will delete Blog 6 Azure AD resources."
echo "    - App registrations ($API_APP_NAME, $SPA_APP_NAME, $NOTIFY_APP_NAME, $AUDIT_APP_NAME)"
echo "    - Test users (testuser-admin, testuser-editor, testuser-reader)"
echo ""
read -rp "    Continue? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "    Aborted."
  exit 0
fi

# ── 1. Delete app registrations ──────────────────────

for APP_NAME in "$API_APP_NAME" "$SPA_APP_NAME" "$NOTIFY_APP_NAME" "$AUDIT_APP_NAME"; do
  echo ""
  echo "==> Deleting app registration: $APP_NAME"
  APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" --output tsv 2>/dev/null || true)
  if [[ -n "$APP_ID" ]]; then
    az ad app delete --id "$APP_ID"
    echo "   Deleted: $APP_ID"
  else
    echo "   (Not found — skipping)"
  fi
done

# ── 2. Delete test users ─────────────────────────────

DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv 2>/dev/null || true)

if [[ -n "$DOMAIN" ]]; then
  for UPN in "testuser-admin@${DOMAIN}" "testuser-editor@${DOMAIN}" "testuser-reader@${DOMAIN}"; do
    echo "==> Deleting test user: $UPN"
    az ad user delete --id "$UPN" 2>/dev/null || echo "   (Not found — skipping)"
  done
fi

# ── 3. Clean up local files ──────────────────────────

echo ""
echo "==> Cleaning up local env files..."
rm -f "$SCRIPT_DIR/task-api/.env"
rm -f "$SCRIPT_DIR/notification-service/.env"
rm -f "$SCRIPT_DIR/audit-service/.env"
rm -f "$SCRIPT_DIR/frontend/.env.local"

echo ""
echo "==> Cleanup complete!"

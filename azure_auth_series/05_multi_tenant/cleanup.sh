#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────
# Blog 5 — Cleanup: Delete AD objects (no infra to destroy)
# ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

API_APP_NAME="${1:-Blog5-MT-API}"
SPA_APP_NAME="${2:-Blog5-MT-Frontend}"

echo "==> This will delete Blog 5 Azure AD resources."
echo "    - App registrations ($API_APP_NAME, $SPA_APP_NAME)"
echo "    - Test users (testuser-admin, testuser-editor, testuser-reader)"
echo ""
read -rp "    Continue? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "    Aborted."
  exit 0
fi

# ── 1. Delete app registrations ─────────────────────

echo ""
echo "==> Deleting app registration: $API_APP_NAME"
API_APP_ID=$(az ad app list --display-name "$API_APP_NAME" --query "[0].appId" --output tsv 2>/dev/null || true)
if [[ -n "$API_APP_ID" ]]; then
  az ad app delete --id "$API_APP_ID"
  echo "   Deleted: $API_APP_ID"
else
  echo "   (Not found — skipping)"
fi

echo "==> Deleting app registration: $SPA_APP_NAME"
SPA_APP_ID=$(az ad app list --display-name "$SPA_APP_NAME" --query "[0].appId" --output tsv 2>/dev/null || true)
if [[ -n "$SPA_APP_ID" ]]; then
  az ad app delete --id "$SPA_APP_ID"
  echo "   Deleted: $SPA_APP_ID"
else
  echo "   (Not found — skipping)"
fi

# ── 2. Delete test users ────────────────────────────

DOMAIN=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/domains" \
  --query "value[?isDefault].id" --output tsv 2>/dev/null || true)

if [[ -n "$DOMAIN" ]]; then
  for UPN in "testuser-admin@${DOMAIN}" "testuser-editor@${DOMAIN}" "testuser-reader@${DOMAIN}"; do
    echo "==> Deleting test user: $UPN"
    az ad user delete --id "$UPN" 2>/dev/null || echo "   (Not found — skipping)"
  done
fi

# ── 3. Clean up local files ─────────────────────────

echo ""
echo "==> Cleaning up local env files..."
rm -f "$SCRIPT_DIR/backend/.env"
rm -f "$SCRIPT_DIR/frontend/.env.local"

echo ""
echo "==> Cleanup complete!"

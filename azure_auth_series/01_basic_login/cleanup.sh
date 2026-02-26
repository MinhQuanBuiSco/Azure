#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# Blog 1 — Azure AD App Registration Cleanup
# Deletes the app registration and removes .env.local
# ──────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/frontend/.env.local"

# Read client ID from .env.local
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Nothing to clean up."
  exit 1
fi

APP_ID=$(grep NEXT_PUBLIC_AZURE_CLIENT_ID "$ENV_FILE" | cut -d'=' -f2)

if [[ -z "$APP_ID" ]]; then
  echo "ERROR: Could not read CLIENT_ID from $ENV_FILE"
  exit 1
fi

echo "==> Deleting app registration: $APP_ID"
az ad app delete --id "$APP_ID"

echo "==> Removing frontend/.env.local"
rm -f "$ENV_FILE"

echo ""
echo "==> Done! App registration deleted and .env.local removed."

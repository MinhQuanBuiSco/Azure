import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Multi-Tenant Configuration ───────────────────────

# Home tenant (your own Azure AD tenant — used for setup reference only)
HOME_TENANT_ID = os.getenv("AZURE_HOME_TENANT_ID", "")

# API app registration (same client ID works for all tenants)
API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "")
AUDIENCE = f"api://{API_CLIENT_ID}"

# ── Tenant Allow-List ────────────────────────────────
# Comma-separated list of tenant IDs that are allowed to use this app.
# Set ALLOW_ANY_TENANT=true to skip the check (open to all Azure AD orgs).

ALLOW_ANY_TENANT = os.getenv("ALLOW_ANY_TENANT", "false").lower() == "true"

_raw_tenants = os.getenv("ALLOWED_TENANT_IDS", HOME_TENANT_ID)
ALLOWED_TENANT_IDS: set[str] = {
    t.strip() for t in _raw_tenants.split(",") if t.strip()
}

if ALLOW_ANY_TENANT:
    logger.info("ALLOW_ANY_TENANT=true — accepting tokens from any Azure AD tenant")
else:
    logger.info("Allowed tenants: %s", ALLOWED_TENANT_IDS)

# ── CORS ─────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

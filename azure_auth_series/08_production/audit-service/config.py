import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Audit Service Configuration ───────────────────────

HOME_TENANT_ID = os.getenv("AZURE_HOME_TENANT_ID", "")

# This service's own app registration
AUDIT_CLIENT_ID = os.getenv("AZURE_AUDIT_CLIENT_ID", "")
AUDIENCE = f"api://{AUDIT_CLIENT_ID}"

# ── Tenant Allow-List ─────────────────────────────────

ALLOW_ANY_TENANT = os.getenv("ALLOW_ANY_TENANT", "false").lower() == "true"

_raw_tenants = os.getenv("ALLOWED_TENANT_IDS", HOME_TENANT_ID)
ALLOWED_TENANT_IDS: set[str] = {
    t.strip() for t in _raw_tenants.split(",") if t.strip()
}

if ALLOW_ANY_TENANT:
    logger.info("ALLOW_ANY_TENANT=true — accepting tokens from any Azure AD tenant")
else:
    logger.info("Allowed tenants: %s", ALLOWED_TENANT_IDS)

# ── NEW in Blog 7: Gateway Trust Mode ──────────────────

TRUST_GATEWAY = os.getenv("TRUST_GATEWAY", "false").lower() == "true"

if TRUST_GATEWAY:
    logger.info("TRUST_GATEWAY=true — accepting claims from APIM headers")
else:
    logger.info("TRUST_GATEWAY=false — validating JWT tokens locally")

# ── NEW in Blog 8: Application Insights ──────────────────

APPINSIGHTS_CONN_STR = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Multi-Tenant Configuration (same as Blog 5/6) ──────

HOME_TENANT_ID = os.getenv("AZURE_HOME_TENANT_ID", "")
API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "")
AUDIENCE = f"api://{API_CLIENT_ID}"

ALLOW_ANY_TENANT = os.getenv("ALLOW_ANY_TENANT", "false").lower() == "true"

_raw_tenants = os.getenv("ALLOWED_TENANT_IDS", HOME_TENANT_ID)
ALLOWED_TENANT_IDS: set[str] = {
    t.strip() for t in _raw_tenants.split(",") if t.strip()
}

if ALLOW_ANY_TENANT:
    logger.info("ALLOW_ANY_TENANT=true — accepting tokens from any Azure AD tenant")
else:
    logger.info("Allowed tenants: %s", ALLOWED_TENANT_IDS)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

# ── Service-to-Service Config (same as Blog 6) ─────────

# Client secret — required for OBO and client credentials flows
API_CLIENT_SECRET = os.getenv("AZURE_API_CLIENT_SECRET", "")

# Notification Service (OBO target)
NOTIFICATION_CLIENT_ID = os.getenv("AZURE_NOTIFICATION_CLIENT_ID", "")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://localhost:8001")

# Audit Service (client credentials target)
AUDIT_CLIENT_ID = os.getenv("AZURE_AUDIT_CLIENT_ID", "")
AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:8002")

# ── NEW in Blog 7: Gateway Trust Mode ──────────────────

TRUST_GATEWAY = os.getenv("TRUST_GATEWAY", "false").lower() == "true"

if TRUST_GATEWAY:
    logger.info("TRUST_GATEWAY=true — accepting claims from APIM headers (skip JWT validation)")
else:
    logger.info("TRUST_GATEWAY=false — validating JWT tokens locally")

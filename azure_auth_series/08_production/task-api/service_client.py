"""
Client Credentials token acquisition.

Acquires a token for the Audit Service as the application itself (no user).
The resulting token has NO user context — only app identity and `roles` claim.

Key concepts:
  - Uses MSAL ConfidentialClientApplication (same class as OBO)
  - Authority is always the home tenant (app-to-app, no user involved)
  - Scope format: api://{target_client_id}/.default
  - Token has `roles` claim (e.g., AuditLog.Write), not `scp`
"""

import logging
import httpx
from msal import ConfidentialClientApplication

from config import (
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    HOME_TENANT_ID,
    AUDIT_CLIENT_ID,
    AUDIT_URL,
)

logger = logging.getLogger(__name__)

# Reuse a single confidential client for client credentials
_cc_app: ConfidentialClientApplication | None = None


def _get_cc_app() -> ConfidentialClientApplication:
    """Get or create the MSAL confidential client for client credentials."""
    global _cc_app
    if _cc_app is None:
        _cc_app = ConfidentialClientApplication(
            client_id=API_CLIENT_ID,
            client_credential=API_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{HOME_TENANT_ID}",
        )
    return _cc_app


async def audit_log(
    action: str, resource_id: int, actor: str, tenant_id: str
) -> dict:
    """
    Acquire a client credentials token and call the Audit Service.
    Graceful failure — logs warning but doesn't block.
    """
    try:
        app = _get_cc_app()
        result = app.acquire_token_for_client(
            scopes=[f"api://{AUDIT_CLIENT_ID}/.default"],
        )

        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "unknown"))
            logger.warning("Client credentials token acquisition failed: %s", error)
            return {"status": "failed", "error": error}

        cc_token = result["access_token"]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{AUDIT_URL}/audit",
                json={
                    "action": action,
                    "resource_id": resource_id,
                    "actor": actor,
                    "tenant_id": tenant_id,
                },
                headers={"Authorization": f"Bearer {cc_token}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    except Exception as e:
        logger.warning("Audit logging failed (non-blocking): %s", str(e))
        return {"status": "failed", "error": str(e)}

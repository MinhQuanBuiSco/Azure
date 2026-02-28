"""
On-Behalf-Of (OBO) token acquisition.

Acquires a token for the Notification Service on behalf of the signed-in user.
The resulting token preserves user context (oid, name, tid) so the downstream
service knows WHO the user is.

Key concepts:
  - Uses MSAL ConfidentialClientApplication (requires client secret)
  - Authority must be tenant-specific (not /common or /organizations)
  - The user_assertion is the incoming access token from the SPA
  - Scope format: api://{target_client_id}/.default
"""

import logging
import httpx
from msal import ConfidentialClientApplication

from config import (
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    NOTIFICATION_CLIENT_ID,
    NOTIFICATION_URL,
)

logger = logging.getLogger(__name__)


def _get_obo_app(tenant_id: str) -> ConfidentialClientApplication:
    """Create an MSAL confidential client for OBO in the user's tenant."""
    return ConfidentialClientApplication(
        client_id=API_CLIENT_ID,
        client_credential=API_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )


async def notify_task_created(
    incoming_token: str, tenant_id: str, task: dict
) -> dict:
    """
    Acquire an OBO token and call the Notification Service.
    Graceful failure — logs warning but doesn't block task creation.
    """
    try:
        app = _get_obo_app(tenant_id)
        result = app.acquire_token_on_behalf_of(
            user_assertion=incoming_token,
            scopes=[f"api://{NOTIFICATION_CLIENT_ID}/.default"],
        )

        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "unknown"))
            logger.warning("OBO token acquisition failed: %s", error)
            return {"status": "failed", "error": error}

        obo_token = result["access_token"]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{NOTIFICATION_URL}/notify",
                json={
                    "event": "task_created",
                    "task_title": task.get("title", ""),
                },
                headers={"Authorization": f"Bearer {obo_token}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    except Exception as e:
        logger.warning("Notification failed (non-blocking): %s", str(e))
        return {"status": "failed", "error": str(e)}

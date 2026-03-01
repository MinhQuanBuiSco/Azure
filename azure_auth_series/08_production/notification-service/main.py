import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends

from config import APPINSIGHTS_CONN_STR

# ── OpenTelemetry instrumentation (auto-instruments FastAPI) ──
if APPINSIGHTS_CONN_STR:
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=APPINSIGHTS_CONN_STR)

from auth import validate_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog 8 — Notification Service (Production Ready)")

# In-memory notification log
notifications: list[dict] = []


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification"}


@app.post("/notify")
async def notify(body: dict, claims: dict = Depends(validate_token)):
    """
    Receive a notification triggered via OBO flow.
    The token contains user context (oid, name, tid) because it was
    acquired on-behalf-of the signed-in user.
    """
    user_name = claims.get("name", "Unknown User")
    user_email = claims.get("preferred_username", "")
    user_oid = claims.get("oid", "")
    tenant_id = claims.get("tid", "")

    event = body.get("event", "unknown")
    task_title = body.get("task_title", "")

    notification = {
        "id": len(notifications) + 1,
        "event": event,
        "task_title": task_title,
        "to": user_name,
        "email": user_email,
        "user_oid": user_oid,
        "tenant_id": tenant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    notifications.append(notification)

    logger.info(
        "Notification sent — event=%s, to=%s (%s), tenant=%s",
        event, user_name, user_email, tenant_id,
    )

    return {
        "status": "sent",
        "to": user_name,
        "event": event,
        "task_title": task_title,
    }


@app.get("/notifications")
async def list_notifications(claims: dict = Depends(validate_token)):
    """List recent notifications (authenticated, user context from OBO)."""
    return notifications[-50:]

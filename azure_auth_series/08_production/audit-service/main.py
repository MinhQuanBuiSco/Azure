import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends

from config import APPINSIGHTS_CONN_STR

# ── OpenTelemetry instrumentation (auto-instruments FastAPI) ──
if APPINSIGHTS_CONN_STR:
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=APPINSIGHTS_CONN_STR)

from auth import validate_app_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog 8 — Audit Service (Production Ready)")

# In-memory audit log
audit_log: list[dict] = []


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "audit"}


@app.post("/audit")
async def create_audit_entry(body: dict, claims: dict = Depends(validate_app_token)):
    """
    Record an audit event. Called via client credentials flow.
    The token is app-only — no user context, just the calling app's identity.
    """
    # App-only tokens have oid = the service principal of the calling app
    caller_app_id = claims.get("azp", claims.get("appid", "unknown"))
    caller_tenant = claims.get("tid", "")

    entry = {
        "id": len(audit_log) + 1,
        "action": body.get("action", "unknown"),
        "resource_id": body.get("resource_id"),
        "actor": body.get("actor", "system"),
        "tenant_id": body.get("tenant_id", caller_tenant),
        "caller_app_id": caller_app_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    audit_log.append(entry)

    logger.info(
        "Audit logged — action=%s, resource=%s, actor=%s, caller_app=%s",
        entry["action"], entry["resource_id"], entry["actor"], caller_app_id,
    )

    return {"status": "logged", "audit_id": entry["id"]}


@app.get("/audit")
async def list_audit_entries(claims: dict = Depends(validate_app_token)):
    """List recent audit events (authenticated, app-only)."""
    return audit_log[-50:]

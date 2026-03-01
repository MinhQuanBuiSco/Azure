import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, APPINSIGHTS_CONN_STR

# ── OpenTelemetry instrumentation (auto-instruments FastAPI + httpx) ──
if APPINSIGHTS_CONN_STR:
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=APPINSIGHTS_CONN_STR)

from auth import validate_token, require_role, get_user_roles
from obo_client import notify_task_created
from service_client import audit_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog 8 — Task API (Production Ready)")

origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check (unauthenticated) ──────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "task-api"}


# ── Tenant-isolated task store ──────────────────────

tasks_db: dict[str, dict[str, list[dict]]] = {}
_task_counter = 0


def _next_id() -> int:
    global _task_counter
    _task_counter += 1
    return _task_counter


def _get_tenant_store(tenant_id: str) -> dict[str, list[dict]]:
    if tenant_id not in tasks_db:
        tasks_db[tenant_id] = {}
    return tasks_db[tenant_id]


def _extract_raw_token(request: Request) -> str:
    """Extract the raw Bearer token from the Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return ""


# ── Public (authenticated) endpoints ────────────────

@app.get("/api/me")
async def get_me(request: Request):
    claims = await validate_token(request)
    return {
        "id": claims.get("oid", ""),
        "name": claims.get("name", ""),
        "email": claims.get("preferred_username", ""),
        "tenant_id": claims.get("tid", ""),
        "roles": get_user_roles(claims),
        "scopes": claims.get("scp", ""),
    }


# ── Reader+ endpoints ──────────────────────────────

@app.get("/api/tasks")
async def get_tasks(
    claims: dict = Depends(require_role("Admin", "Editor", "Reader")),
):
    tenant_id = claims.get("tid", "")
    user_id = claims.get("oid", "")
    roles = get_user_roles(claims)

    tenant_store = _get_tenant_store(tenant_id)

    if "Admin" in roles:
        all_tasks = []
        for owner_id, user_tasks in tenant_store.items():
            for task in user_tasks:
                all_tasks.append({**task, "owner_id": owner_id})
        return all_tasks

    return tenant_store.get(user_id, [])


# ── Editor+ endpoints ──────────────────────────────

@app.post("/api/tasks")
async def create_task(
    task: dict,
    request: Request,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    """
    Create a new task, then:
    1. OBO → Notification Service (user context preserved)
    2. Client Credentials → Audit Service (app identity only)

    S2S calls go DIRECT to Container Apps — not through APIM.
    """
    tenant_id = claims.get("tid", "")
    user_id = claims.get("oid", "")
    user_name = claims.get("name", "Unknown")

    tenant_store = _get_tenant_store(tenant_id)
    if user_id not in tenant_store:
        tenant_store[user_id] = []

    new_task = {
        "id": _next_id(),
        "title": task.get("title", ""),
        "completed": False,
        "owner_name": user_name,
        "tenant_id": tenant_id,
    }
    tenant_store[user_id].append(new_task)

    # ── Service-to-Service calls (non-blocking, direct) ────

    raw_token = _extract_raw_token(request)

    # 1. OBO → Notification Service (preserves user context)
    notification_result = await notify_task_created(raw_token, tenant_id, new_task)

    # 2. Client Credentials → Audit Service (app identity only)
    audit_result = await audit_log(
        action="task_created",
        resource_id=new_task["id"],
        actor=user_name,
        tenant_id=tenant_id,
    )

    return {
        **new_task,
        "notification_status": notification_result.get("status", "unknown"),
        "audit_status": audit_result.get("status", "unknown"),
    }


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    updates: dict,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    tenant_id = claims.get("tid", "")
    user_id = claims.get("oid", "")
    roles = get_user_roles(claims)

    tenant_store = _get_tenant_store(tenant_id)

    if "Admin" in roles:
        for user_tasks in tenant_store.values():
            for task in user_tasks:
                if task["id"] == task_id:
                    if "completed" in updates:
                        task["completed"] = updates["completed"]
                    if "title" in updates:
                        task["title"] = updates["title"]
                    return task
    else:
        user_tasks = tenant_store.get(user_id, [])
        for task in user_tasks:
            if task["id"] == task_id:
                if "completed" in updates:
                    task["completed"] = updates["completed"]
                if "title" in updates:
                    task["title"] = updates["title"]
                return task

    return {"error": "Task not found"}


# ── Admin-only endpoints ────────────────────────────

@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: int,
    request: Request,
    claims: dict = Depends(require_role("Admin")),
):
    """Delete a task and log to audit service."""
    tenant_id = claims.get("tid", "")
    user_name = claims.get("name", "Unknown")
    tenant_store = _get_tenant_store(tenant_id)

    for user_id, user_tasks in tenant_store.items():
        tenant_store[user_id] = [t for t in user_tasks if t["id"] != task_id]

    # Audit the deletion (client credentials — app identity)
    audit_result = await audit_log(
        action="task_deleted",
        resource_id=task_id,
        actor=user_name,
        tenant_id=tenant_id,
    )

    return {
        "status": "deleted",
        "audit_status": audit_result.get("status", "unknown"),
    }

import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from auth import validate_token, require_role, get_user_roles
from config import ALLOWED_ORIGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog 5 — Multi-Tenant Auth API")

# Configurable CORS: reads ALLOWED_ORIGINS from config (comma-separated)
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
    return {"status": "healthy"}


# ── Tenant-isolated task store ──────────────────────
# Structure: { tenant_id: { user_id: [tasks] } }

tasks_db: dict[str, dict[str, list[dict]]] = {}
_task_counter = 0


def _next_id() -> int:
    global _task_counter
    _task_counter += 1
    return _task_counter


def _get_tenant_store(tenant_id: str) -> dict[str, list[dict]]:
    """Get or create the task store for a specific tenant."""
    if tenant_id not in tasks_db:
        tasks_db[tenant_id] = {}
    return tasks_db[tenant_id]


# ── Public (authenticated) endpoints ────────────────

@app.get("/api/me")
async def get_me(claims: dict = Depends(validate_token)):
    """Return the authenticated user's profile + roles from token claims."""
    return {
        "id": claims.get("oid", ""),
        "name": claims.get("name", ""),
        "email": claims.get("preferred_username", ""),
        "tenant_id": claims.get("tid", ""),
        "roles": get_user_roles(claims),
        "scopes": claims.get("scp", ""),
    }


# ── Reader+ endpoints (Reader, Editor, Admin) ──────

@app.get("/api/tasks")
async def get_tasks(
    claims: dict = Depends(require_role("Admin", "Editor", "Reader")),
):
    """Get tasks. Admin sees all in their tenant, others see only their own."""
    tenant_id = claims.get("tid", "")
    user_id = claims.get("oid", "")
    roles = get_user_roles(claims)

    tenant_store = _get_tenant_store(tenant_id)

    if "Admin" in roles:
        # Admin sees all tasks — but only within their tenant
        all_tasks = []
        for owner_id, user_tasks in tenant_store.items():
            for task in user_tasks:
                all_tasks.append({**task, "owner_id": owner_id})
        return all_tasks

    return tenant_store.get(user_id, [])


# ── Editor+ endpoints (Editor, Admin) ──────────────

@app.post("/api/tasks")
async def create_task(
    task: dict,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    """Create a new task. Editor+ only."""
    tenant_id = claims.get("tid", "")
    user_id = claims.get("oid", "")

    tenant_store = _get_tenant_store(tenant_id)
    if user_id not in tenant_store:
        tenant_store[user_id] = []

    new_task = {
        "id": _next_id(),
        "title": task.get("title", ""),
        "completed": False,
        "owner_name": claims.get("name", "Unknown"),
        "tenant_id": tenant_id,
    }
    tenant_store[user_id].append(new_task)
    return new_task


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    updates: dict,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    """Update a task. Editor can update own, Admin can update any in tenant."""
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
    claims: dict = Depends(require_role("Admin")),
):
    """Delete any task within the admin's tenant."""
    tenant_id = claims.get("tid", "")
    tenant_store = _get_tenant_store(tenant_id)

    for user_id, user_tasks in tenant_store.items():
        tenant_store[user_id] = [t for t in user_tasks if t["id"] != task_id]
    return {"status": "deleted"}

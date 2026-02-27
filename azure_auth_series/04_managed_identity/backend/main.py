import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from auth import validate_token, require_role, get_user_roles
from config import ALLOWED_ORIGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog 4 — Managed Identity + Key Vault API")

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


# ── In-memory task store ────────────────────────────

tasks_db: dict[str, list[dict]] = {}
_task_counter = 0


def _next_id() -> int:
    global _task_counter
    _task_counter += 1
    return _task_counter


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
    """Get tasks. Admin sees all, others see only their own."""
    user_id = claims.get("oid", "")
    roles = get_user_roles(claims)

    if "Admin" in roles:
        all_tasks = []
        for owner_id, user_tasks in tasks_db.items():
            for task in user_tasks:
                all_tasks.append({**task, "owner_id": owner_id})
        return all_tasks

    return tasks_db.get(user_id, [])


# ── Editor+ endpoints (Editor, Admin) ──────────────

@app.post("/api/tasks")
async def create_task(
    task: dict,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    """Create a new task. Editor+ only."""
    user_id = claims.get("oid", "")
    if user_id not in tasks_db:
        tasks_db[user_id] = []

    new_task = {
        "id": _next_id(),
        "title": task.get("title", ""),
        "completed": False,
        "owner_name": claims.get("name", "Unknown"),
    }
    tasks_db[user_id].append(new_task)
    return new_task


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    updates: dict,
    claims: dict = Depends(require_role("Admin", "Editor")),
):
    """Update a task. Editor can update own, Admin can update any."""
    user_id = claims.get("oid", "")
    roles = get_user_roles(claims)

    if "Admin" in roles:
        for user_tasks in tasks_db.values():
            for task in user_tasks:
                if task["id"] == task_id:
                    if "completed" in updates:
                        task["completed"] = updates["completed"]
                    if "title" in updates:
                        task["title"] = updates["title"]
                    return task
    else:
        user_tasks = tasks_db.get(user_id, [])
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
    """Delete any task. Admin only."""
    for user_id, user_tasks in tasks_db.items():
        tasks_db[user_id] = [t for t in user_tasks if t["id"] != task_id]
    return {"status": "deleted"}

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from auth import validate_token

app = FastAPI(title="Blog 2 — Protected API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store (keyed by user ID)
tasks_db: dict[str, list[dict]] = {}


@app.get("/api/me")
async def get_me(claims: dict = Depends(validate_token)):
    """Return the authenticated user's profile from token claims."""
    return {
        "id": claims.get("oid", ""),
        "name": claims.get("name", ""),
        "email": claims.get("preferred_username", ""),
        "tenant_id": claims.get("tid", ""),
        "scopes": claims.get("scp", ""),
    }


@app.get("/api/tasks")
async def get_tasks(claims: dict = Depends(validate_token)):
    """Get all tasks for the authenticated user."""
    user_id = claims.get("oid", "")
    return tasks_db.get(user_id, [])


@app.post("/api/tasks")
async def create_task(task: dict, claims: dict = Depends(validate_token)):
    """Create a new task for the authenticated user."""
    user_id = claims.get("oid", "")
    if user_id not in tasks_db:
        tasks_db[user_id] = []

    new_task = {
        "id": len(tasks_db[user_id]) + 1,
        "title": task.get("title", ""),
        "completed": False,
    }
    tasks_db[user_id].append(new_task)
    return new_task


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int, updates: dict, claims: dict = Depends(validate_token)
):
    """Toggle or update a task for the authenticated user."""
    user_id = claims.get("oid", "")
    user_tasks = tasks_db.get(user_id, [])

    for task in user_tasks:
        if task["id"] == task_id:
            if "completed" in updates:
                task["completed"] = updates["completed"]
            if "title" in updates:
                task["title"] = updates["title"]
            return task

    return {"error": "Task not found"}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, claims: dict = Depends(validate_token)):
    """Delete a task for the authenticated user."""
    user_id = claims.get("oid", "")
    user_tasks = tasks_db.get(user_id, [])
    tasks_db[user_id] = [t for t in user_tasks if t["id"] != task_id]
    return {"status": "deleted"}

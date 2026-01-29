"""API route modules."""

from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.budget import router as budget_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.health import router as health_router

__all__ = [
    "analytics_router",
    "budget_router",
    "chat_router",
    "health_router",
]

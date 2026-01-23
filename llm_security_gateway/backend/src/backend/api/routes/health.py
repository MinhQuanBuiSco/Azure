"""Health check endpoints."""

from fastapi import APIRouter, Response, status

from backend.config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "llm-security-gateway",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """
    Readiness check endpoint.
    Verifies all required services are available.
    """
    settings = get_settings()
    checks = {
        "azure_ai_configured": bool(settings.azure_ai_endpoint),
        "content_safety_configured": bool(settings.azure_content_safety_endpoint),
    }

    all_ready = all(checks.values()) or settings.environment == "development"

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "environment": settings.environment,
    }


@router.get("/live")
async def liveness_check(response: Response) -> dict:
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}

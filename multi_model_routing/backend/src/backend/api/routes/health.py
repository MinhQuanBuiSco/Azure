"""Health check endpoints."""

from fastapi import APIRouter, Depends

from backend.config import Settings, get_settings
from backend.models import HealthResponse
from backend.storage import get_redis_client, get_cosmos_client

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Readiness check that verifies all dependencies.

    Returns degraded status if some services are unavailable.
    """
    services: dict[str, bool] = {}

    # Check Redis
    try:
        redis_client = get_redis_client(settings)
        services["redis"] = await redis_client.health_check()
    except Exception:
        services["redis"] = False

    # Check Cosmos DB
    try:
        cosmos_client = get_cosmos_client(settings)
        services["cosmos"] = await cosmos_client.health_check()
    except Exception:
        services["cosmos"] = False

    # Determine overall status
    all_healthy = all(services.values())
    any_healthy = any(services.values())

    if all_healthy:
        status = "healthy"
    elif any_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        version=settings.app_version,
        environment=settings.environment,
        services=services,
    )


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "alive"}

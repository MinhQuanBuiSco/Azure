"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from backend.config.settings import get_settings, Settings
from backend.providers.azure_ai_foundry import AzureAIFoundryClient, get_azure_ai_client
from backend.providers.content_safety import AzureContentSafetyClient, get_content_safety_client
from backend.security.scanner import SecurityScanner, get_security_scanner
from backend.storage.redis import RedisClient, get_redis_client
from backend.storage.cosmos import CosmosClient, get_cosmos_client


def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


def get_ai_client() -> AzureAIFoundryClient:
    """Get Azure AI Foundry client."""
    return get_azure_ai_client()


def get_safety_client() -> AzureContentSafetyClient:
    """Get Azure Content Safety client."""
    return get_content_safety_client()


def get_scanner() -> SecurityScanner:
    """Get security scanner."""
    return get_security_scanner()


def get_redis() -> RedisClient:
    """Get Redis client."""
    return get_redis_client()


def get_cosmos() -> CosmosClient:
    """Get Cosmos DB client."""
    return get_cosmos_client()


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Verify API key from headers.

    Accepts either X-API-Key header or Authorization: Bearer token.

    Returns:
        The API key if provided, None otherwise (for development)
    """
    settings = get_settings()

    # In development, allow requests without API key
    if settings.environment in ("dev", "development"):
        return x_api_key or (authorization.replace("Bearer ", "") if authorization else None)

    # Extract API key
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header or Authorization: Bearer token.",
        )

    # TODO: Validate API key against a database or key vault
    # For now, just check it's not empty
    return api_key


async def check_rate_limit(
    request: Request,
    redis_client: Annotated[RedisClient, Depends(get_redis)],
    api_key: Annotated[str | None, Depends(verify_api_key)],
) -> None:
    """
    Check rate limit for the request.

    Raises HTTPException if rate limit exceeded.
    """
    settings = get_settings()

    # Build rate limit key
    key_parts = []
    if api_key:
        key_parts.append(f"api:{api_key[:8]}")
    else:
        # Use client IP for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        key_parts.append(f"ip:{client_ip}")

    rate_key = ":".join(key_parts)

    # Check rate limit
    allowed, remaining, reset_time = await redis_client.check_rate_limit(rate_key)

    # Add rate limit headers
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_time

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {reset_time} seconds.",
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time),
            },
        )


# Type aliases for cleaner dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
AIClientDep = Annotated[AzureAIFoundryClient, Depends(get_ai_client)]
SafetyClientDep = Annotated[AzureContentSafetyClient, Depends(get_safety_client)]
ScannerDep = Annotated[SecurityScanner, Depends(get_scanner)]
RedisDep = Annotated[RedisClient, Depends(get_redis)]
CosmosDep = Annotated[CosmosClient, Depends(get_cosmos)]
APIKeyDep = Annotated[str | None, Depends(verify_api_key)]
RateLimitDep = Annotated[None, Depends(check_rate_limit)]

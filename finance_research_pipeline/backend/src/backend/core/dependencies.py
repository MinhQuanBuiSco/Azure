"""FastAPI dependency injection container."""

from functools import lru_cache
from typing import Annotated, AsyncGenerator

from fastapi import Depends
import redis.asyncio as redis

from backend.core.config import Settings, get_settings
from backend.services.cache import CacheService
from backend.services.cosmos_db import CosmosDBService
from backend.services.llm_factory import LLMFactory
from backend.services.websocket_manager import WebSocketManager


# Global instances
_websocket_manager: WebSocketManager | None = None
_redis_client: redis.Redis | None = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


async def get_redis_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[redis.Redis, None]:
    """Get Redis client with connection pooling."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    yield _redis_client


async def get_cache_service(
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CacheService:
    """Get cache service instance."""
    return CacheService(redis_client, settings.cache_ttl_seconds)


@lru_cache
def get_llm_factory() -> LLMFactory:
    """Get LLM factory instance."""
    settings = get_settings()
    return LLMFactory(settings)


async def get_cosmos_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[CosmosDBService | None, None]:
    """Get Cosmos DB service instance."""
    if settings.cosmos_endpoint and settings.cosmos_key:
        service = CosmosDBService(settings)
        await service.initialize()
        yield service
    else:
        yield None


# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
WebSocketManagerDep = Annotated[WebSocketManager, Depends(get_websocket_manager)]
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
LLMFactoryDep = Annotated[LLMFactory, Depends(get_llm_factory)]
CosmosServiceDep = Annotated[CosmosDBService | None, Depends(get_cosmos_service)]

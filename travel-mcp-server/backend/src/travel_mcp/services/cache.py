"""Redis caching service for Travel MCP Server."""

import json
import hashlib
from functools import lru_cache
from typing import Any

import redis.asyncio as redis
import structlog

from travel_mcp.config import get_settings

logger = structlog.get_logger()


class CacheService:
    """Redis-based caching service for API responses."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self.settings = get_settings()

    @staticmethod
    def _generate_key(prefix: str, params: dict[str, Any]) -> str:
        """Generate a cache key from prefix and parameters."""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        return f"travel:{prefix}:{params_hash}"

    async def get(self, prefix: str, params: dict[str, Any]) -> Any | None:
        """Get cached value if exists."""
        key = self._generate_key(prefix, params)
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug("Cache hit", key=key)
                return json.loads(value)
            logger.debug("Cache miss", key=key)
            return None
        except Exception as e:
            logger.warning("Cache get error", error=str(e), key=key)
            return None

    async def set(
        self,
        prefix: str,
        params: dict[str, Any],
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set cached value with TTL."""
        key = self._generate_key(prefix, params)
        ttl = ttl or self.settings.cache_ttl_seconds
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
            logger.debug("Cache set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.warning("Cache set error", error=str(e), key=key)
            return False

    async def delete(self, prefix: str, params: dict[str, Any]) -> bool:
        """Delete cached value."""
        key = self._generate_key(prefix, params)
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning("Cache delete error", error=str(e), key=key)
            return False

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


_cache_service: CacheService | None = None


async def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        settings = get_settings()
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=3.0,  # 3 second timeout for operations
            socket_connect_timeout=3.0,  # 3 second connection timeout
        )
        _cache_service = CacheService(client)
    return _cache_service

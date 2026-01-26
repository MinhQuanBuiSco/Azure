"""Redis caching service."""

import json
from typing import Any

import redis.asyncio as redis

from backend.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Service for caching data in Redis."""

    def __init__(self, client: redis.Redis, default_ttl: int = 3600) -> None:
        """
        Initialize cache service.

        Args:
            client: Redis client instance
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.client = client
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: TTL in seconds (optional, uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)
            await self.client.set(
                key,
                serialized,
                ex=ttl or self.default_ttl,
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def get_research_state(self, research_id: str) -> dict[str, Any] | None:
        """Get cached research state."""
        return await self.get(f"research:{research_id}:state")

    async def set_research_state(
        self,
        research_id: str,
        state: dict[str, Any],
        ttl: int = 7200,  # 2 hours
    ) -> bool:
        """Cache research state."""
        return await self.set(f"research:{research_id}:state", state, ttl)

    async def get_financial_data(
        self,
        ticker: str,
        data_type: str,
    ) -> dict[str, Any] | None:
        """Get cached financial data."""
        return await self.get(f"finance:{ticker}:{data_type}")

    async def set_financial_data(
        self,
        ticker: str,
        data_type: str,
        data: dict[str, Any],
        ttl: int = 900,  # 15 minutes
    ) -> bool:
        """Cache financial data."""
        return await self.set(f"finance:{ticker}:{data_type}", data, ttl)

    async def invalidate_research(self, research_id: str) -> None:
        """Invalidate all cache entries for a research session."""
        try:
            pattern = f"research:{research_id}:*"
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidation error for research {research_id}: {e}")

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

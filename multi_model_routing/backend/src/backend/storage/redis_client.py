"""Redis client for caching and real-time budget tracking."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import redis.asyncio as redis

from backend.config import Settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching and budget tracking."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Redis client."""
        self._settings = settings
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        """Get or create the Redis connection."""
        if self._client is None:
            url = self._settings.redis_url
            # rediss:// URL already contains password and implies SSL
            # Just pass the URL directly and let redis-py parse it
            self._client = redis.from_url(
                url,
                decode_responses=True,
                ssl_cert_reqs=None,  # Azure Redis uses Microsoft-managed certs
            )
        return self._client

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    # Budget tracking methods
    async def get_budget_spend(
        self, user_id: str, period: str = "daily"
    ) -> float:
        """Get current spend for a budget period."""
        client = await self._get_client()
        key = f"budget:{user_id}:{period}"
        value = await client.get(key)
        return float(value) if value else 0.0

    async def increment_spend(
        self, user_id: str, amount: float, period: str = "daily"
    ) -> float:
        """Increment spend and return new total."""
        client = await self._get_client()
        key = f"budget:{user_id}:{period}"

        # Use INCRBYFLOAT for atomic increment
        new_value = await client.incrbyfloat(key, amount)

        # Set expiry based on period if not set
        ttl = await client.ttl(key)
        if ttl == -1:  # No expiry set
            if period == "daily":
                # Expire at end of day
                now = datetime.utcnow()
                end_of_day = now.replace(hour=23, minute=59, second=59)
                seconds = int((end_of_day - now).total_seconds()) + 1
            elif period == "weekly":
                seconds = 7 * 24 * 60 * 60
            elif period == "monthly":
                seconds = 30 * 24 * 60 * 60
            else:
                seconds = 24 * 60 * 60

            await client.expire(key, seconds)

        return float(new_value)

    async def reset_budget(self, user_id: str, period: str = "daily") -> None:
        """Reset budget for a period."""
        client = await self._get_client()
        key = f"budget:{user_id}:{period}"
        await client.delete(key)

    # Routing cache methods
    async def get_routing_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get cached routing decision."""
        client = await self._get_client()
        key = f"routing_cache:{cache_key}"
        value = await client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_routing_cache(
        self, cache_key: str, decision: dict[str, Any], ttl: int = 300
    ) -> None:
        """Cache a routing decision."""
        client = await self._get_client()
        key = f"routing_cache:{cache_key}"
        await client.setex(key, ttl, json.dumps(decision))

    # Statistics methods
    async def increment_counter(self, name: str, amount: int = 1) -> int:
        """Increment a global counter."""
        client = await self._get_client()
        key = f"stats:global:{name}"
        return await client.incrby(key, amount)

    async def get_counter(self, name: str) -> int:
        """Get a global counter value."""
        client = await self._get_client()
        key = f"stats:global:{name}"
        value = await client.get(key)
        return int(value) if value else 0

    async def record_request(
        self,
        user_id: str,
        model: str,
        tier: str,
        cost: float,
        latency_ms: int,
    ) -> None:
        """Record request metrics for real-time stats."""
        client = await self._get_client()
        timestamp = datetime.utcnow().isoformat()

        # Increment counters
        await self.increment_counter("total_requests")
        await self.increment_counter(f"requests:{tier}")
        await self.increment_counter(f"requests:model:{model}")

        # Add to recent requests list (keep last 1000)
        request_data = json.dumps(
            {
                "user_id": user_id,
                "model": model,
                "tier": tier,
                "cost": cost,
                "latency_ms": latency_ms,
                "timestamp": timestamp,
            }
        )
        await client.lpush("stats:recent_requests", request_data)
        await client.ltrim("stats:recent_requests", 0, 999)

    async def get_recent_requests(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent requests for real-time dashboard."""
        client = await self._get_client()
        requests = await client.lrange("stats:recent_requests", 0, limit - 1)
        return [json.loads(r) for r in requests]

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global instance
_redis_client: RedisClient | None = None


def get_redis_client(settings: Settings) -> RedisClient:
    """Get or create the global Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(settings)
    return _redis_client

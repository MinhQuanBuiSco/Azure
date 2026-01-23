"""Redis client for rate limiting and caching."""

import time
from typing import Any

import redis.asyncio as redis

from backend.config.settings import get_settings


class RedisClient:
    """Async Redis client for rate limiting and caching."""

    def __init__(self):
        self.settings = get_settings()
        self._client: redis.Redis | None = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if self._connected:
            return True

        try:
            self._client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            print(f"Connected to Redis at {self.settings.redis_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False

    @property
    def connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ) -> tuple[bool, int, int]:
        """
        Check and update rate limit for a key.

        Args:
            key: The rate limit key (e.g., "rate_limit:user:123")
            max_requests: Maximum requests allowed (default from settings)
            window_seconds: Time window in seconds (default from settings)

        Returns:
            Tuple of (allowed, remaining_requests, reset_time_seconds)
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            # If Redis is unavailable, allow the request
            return True, -1, 0

        max_requests = max_requests or self.settings.rate_limit_requests
        window_seconds = window_seconds or self.settings.rate_limit_window_seconds

        try:
            now = int(time.time())
            window_start = now - window_seconds

            # Use a sorted set with timestamps as scores
            rate_key = f"rate_limit:{key}"

            # Remove old entries
            await self._client.zremrangebyscore(rate_key, 0, window_start)

            # Count current requests
            current_count = await self._client.zcard(rate_key)

            if current_count >= max_requests:
                # Get oldest entry to calculate reset time
                oldest = await self._client.zrange(rate_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + window_seconds - now
                else:
                    reset_time = window_seconds
                return False, 0, reset_time

            # Add new request
            await self._client.zadd(rate_key, {str(now): now})
            await self._client.expire(rate_key, window_seconds + 1)

            remaining = max_requests - current_count - 1
            return True, remaining, window_seconds

        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True, -1, 0

    async def increment_counter(self, key: str, ttl_seconds: int | None = None) -> int:
        """
        Increment a counter.

        Args:
            key: The counter key
            ttl_seconds: Optional TTL for the counter

        Returns:
            The new counter value
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            return 0

        try:
            value = await self._client.incr(key)
            if ttl_seconds and value == 1:
                await self._client.expire(key, ttl_seconds)
            return value
        except Exception as e:
            print(f"Counter increment error: {e}")
            return 0

    async def get_counter(self, key: str) -> int:
        """Get a counter value."""
        if not self._connected:
            await self.connect()

        if not self._connected:
            return 0

        try:
            value = await self._client.get(key)
            return int(value) if value else 0
        except Exception as e:
            print(f"Counter get error: {e}")
            return 0

    async def cache_set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        """Set a cache value."""
        if not self._connected:
            await self.connect()

        if not self._connected:
            return False

        try:
            await self._client.setex(key, ttl_seconds, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def cache_get(self, key: str) -> str | None:
        """Get a cache value."""
        if not self._connected:
            await self.connect()

        if not self._connected:
            return None

        try:
            return await self._client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None


# Global instance
_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """Get or create the Redis client."""
    global _client
    if _client is None:
        _client = RedisClient()
    return _client

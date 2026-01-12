import logging
import json
import hashlib
from typing import Optional, Any
import redis.asyncio as redis
from ..config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for semantic caching and session management."""

    def __init__(self):
        """Initialize Redis client."""
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                ssl=settings.redis_ssl,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    def _generate_cache_key(self, query: str, strategy: str, filters: Optional[dict] = None) -> str:
        """
        Generate a cache key from query parameters.

        Args:
            query: Search query
            strategy: Search strategy
            filters: Optional entity filters

        Returns:
            Cache key hash
        """
        cache_data = {
            "query": query.lower().strip(),
            "strategy": strategy,
            "filters": filters or {}
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()[:16]
        return f"query_cache:{cache_hash}"

    async def get_cached_results(
        self,
        query: str,
        strategy: str,
        filters: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Get cached search results.

        Args:
            query: Search query
            strategy: Search strategy
            filters: Optional entity filters

        Returns:
            Cached results dict or None
        """
        try:
            cache_key = self._generate_cache_key(query, strategy, filters)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return json.loads(cached_data)

            logger.debug(f"Cache MISS for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Cache read error: {str(e)}")
            return None

    async def cache_results(
        self,
        query: str,
        strategy: str,
        results: dict,
        filters: Optional[dict] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache search results.

        Args:
            query: Search query
            strategy: Search strategy
            results: Results to cache
            filters: Optional entity filters
            ttl: Time-to-live in seconds (default from settings)
        """
        try:
            cache_key = self._generate_cache_key(query, strategy, filters)
            cache_data = json.dumps(results)
            ttl = ttl or settings.cache_ttl

            await self.redis_client.setex(
                cache_key,
                ttl,
                cache_data
            )

            logger.debug(f"Cached results for query: {query[:50]}...")

        except Exception as e:
            logger.error(f"Cache write error: {str(e)}")

    async def get_indexing_status(self, document_id: str) -> Optional[dict]:
        """Get document indexing status from cache."""
        try:
            key = f"indexing_status:{document_id}"
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get indexing status: {str(e)}")
            return None

    async def set_indexing_status(
        self,
        document_id: str,
        status: dict,
        ttl: int = 86400  # 24 hours
    ):
        """Set document indexing status in cache."""
        try:
            key = f"indexing_status:{document_id}"
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(status)
            )
        except Exception as e:
            logger.error(f"Failed to set indexing status: {str(e)}")

    async def invalidate_cache(self, pattern: str = "query_cache:*"):
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Redis key pattern (default: all query caches)
        """
        try:
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    await self.redis_client.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted_count} cache entries")

        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}


# Global cache instance
cache_service = CacheService()

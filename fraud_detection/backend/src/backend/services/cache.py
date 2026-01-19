"""
Redis caching service for fraud detection system.

Caches:
- User transaction history (frequently accessed)
- Fraud scores
- User statistics
- Rule engine results
"""
import json
from typing import Optional, Dict, List, Any
from datetime import timedelta
import redis.asyncio as redis

from backend.core.config import get_settings


class CacheService:
    """Redis-based caching service."""

    def __init__(self):
        """Initialize Redis connection."""
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None

        # Cache TTLs (time to live)
        self.TTL_USER_HISTORY = 300  # 5 minutes
        self.TTL_FRAUD_SCORE = 3600  # 1 hour
        self.TTL_USER_STATS = 600    # 10 minutes
        self.TTL_RULE_RESULT = 1800  # 30 minutes

    async def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                f"redis://{self.settings.redis_host}:{self.settings.redis_port}",
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            print(f"✅ Connected to Redis at {self.settings.redis_host}:{self.settings.redis_port}")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            print("👋 Disconnected from Redis")

    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            if not self.redis_client:
                await self.connect()
            await self.redis_client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis ping failed: {e}")
            return False

    # User History Cache
    async def get_user_history(self, user_id: str) -> Optional[List[Dict]]:
        """Get cached user transaction history."""
        try:
            key = f"user_history:{user_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error (user_history): {e}")
            return None

    async def set_user_history(
        self,
        user_id: str,
        history: List[Dict],
        ttl: int = None
    ):
        """Cache user transaction history."""
        try:
            key = f"user_history:{user_id}"
            ttl = ttl or self.TTL_USER_HISTORY

            # Convert datetime objects to ISO format for JSON serialization
            serializable_history = []
            for txn in history:
                txn_copy = txn.copy()
                if 'transaction_time' in txn_copy and hasattr(txn_copy['transaction_time'], 'isoformat'):
                    txn_copy['transaction_time'] = txn_copy['transaction_time'].isoformat()
                serializable_history.append(txn_copy)

            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(serializable_history)
            )
        except Exception as e:
            print(f"Cache set error (user_history): {e}")

    async def invalidate_user_history(self, user_id: str):
        """Invalidate user history cache (call after new transaction)."""
        try:
            key = f"user_history:{user_id}"
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache invalidate error (user_history): {e}")

    # Fraud Score Cache
    async def get_fraud_score(self, transaction_id: str) -> Optional[Dict]:
        """Get cached fraud score for a transaction."""
        try:
            key = f"fraud_score:{transaction_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error (fraud_score): {e}")
            return None

    async def set_fraud_score(
        self,
        transaction_id: str,
        score_data: Dict,
        ttl: int = None
    ):
        """Cache fraud score result."""
        try:
            key = f"fraud_score:{transaction_id}"
            ttl = ttl or self.TTL_FRAUD_SCORE
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(score_data)
            )
        except Exception as e:
            print(f"Cache set error (fraud_score): {e}")

    # User Statistics Cache
    async def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get cached user statistics."""
        try:
            key = f"user_stats:{user_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error (user_stats): {e}")
            return None

    async def set_user_stats(
        self,
        user_id: str,
        stats: Dict,
        ttl: int = None
    ):
        """Cache user statistics."""
        try:
            key = f"user_stats:{user_id}"
            ttl = ttl or self.TTL_USER_STATS
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(stats)
            )
        except Exception as e:
            print(f"Cache set error (user_stats): {e}")

    # Rule Results Cache
    async def get_rule_result(self, rule_key: str) -> Optional[Any]:
        """Get cached rule evaluation result."""
        try:
            key = f"rule_result:{rule_key}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error (rule_result): {e}")
            return None

    async def set_rule_result(
        self,
        rule_key: str,
        result: Any,
        ttl: int = None
    ):
        """Cache rule evaluation result."""
        try:
            key = f"rule_result:{rule_key}"
            ttl = ttl or self.TTL_RULE_RESULT
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(result)
            )
        except Exception as e:
            print(f"Cache set error (rule_result): {e}")

    # Generic Cache Operations
    async def get(self, key: str) -> Optional[str]:
        """Generic cache get."""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300):
        """Generic cache set with TTL."""
        try:
            await self.redis_client.setex(key, ttl, value)
        except Exception as e:
            print(f"Cache set error: {e}")

    async def delete(self, key: str):
        """Delete a cache key."""
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching a pattern."""
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            print(f"Cache clear pattern error: {e}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error: {e}")
            return 0

    async def get_stats(self) -> Dict:
        """Get Redis statistics."""
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


async def init_cache():
    """Initialize cache connection."""
    cache = get_cache()
    await cache.connect()
    return cache


async def close_cache():
    """Close cache connection."""
    cache = get_cache()
    await cache.disconnect()

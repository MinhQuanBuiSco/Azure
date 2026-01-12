import logging
from fastapi import APIRouter, HTTPException
from ...services import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.delete("/clear")
async def clear_cache():
    """
    Clear all cached query results.

    This does not clear indexing status.

    Returns:
        Success message with count of cleared keys
    """
    try:
        # Get all query cache keys
        keys = await cache_service.redis_client.keys("query_cache:*")

        if keys:
            # Delete all query cache keys
            await cache_service.redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cached queries")
            return {
                "message": "Cache cleared successfully",
                "cleared_keys": len(keys)
            }
        else:
            return {
                "message": "Cache is already empty",
                "cleared_keys": 0
            }

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics.

    Returns:
        Cache statistics including total keys and query cache count
    """
    try:
        all_keys = await cache_service.redis_client.keys("*")
        query_keys = await cache_service.redis_client.keys("query_cache:*")

        return {
            "total_keys": len(all_keys),
            "query_cache_keys": len(query_keys),
            "indexing_status_keys": len(all_keys) - len(query_keys)
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

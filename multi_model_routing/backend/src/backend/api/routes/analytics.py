"""Analytics endpoints for cost and savings tracking."""

import logging
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request

from backend.config import Settings, get_settings
from backend.models import CostAnalytics, SavingsAnalytics
from backend.storage import get_cosmos_client, get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _parse_period(
    period: str,
) -> tuple[datetime, datetime]:
    """Parse period string to date range."""
    now = datetime.utcnow()

    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "weekly":
        start = now - timedelta(days=7)
        end = now
    elif period == "monthly":
        start = now - timedelta(days=30)
        end = now
    else:
        # Default to last 30 days
        start = now - timedelta(days=30)
        end = now

    return start, end


@router.get("/costs", response_model=CostAnalytics)
async def get_cost_analytics(
    request: Request,
    period: Literal["daily", "weekly", "monthly"] = Query(default="monthly"),
    settings: Settings = Depends(get_settings),
) -> CostAnalytics:
    """
    Get cost breakdown by tier and model.

    Returns aggregated cost data for the specified period.
    """
    user_id = request.headers.get("X-User-ID")
    start_date, end_date = _parse_period(period)

    cosmos = get_cosmos_client(settings)
    analytics = await cosmos.get_cost_analytics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    return CostAnalytics(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_cost=analytics["total_cost"],
        total_requests=analytics["total_requests"],
        cost_by_tier=analytics["cost_by_tier"],
        cost_by_model=analytics["cost_by_model"],
        average_cost_per_request=analytics["average_cost_per_request"],
    )


@router.get("/savings", response_model=SavingsAnalytics)
async def get_savings_analytics(
    request: Request,
    period: Literal["daily", "weekly", "monthly"] = Query(default="monthly"),
    settings: Settings = Depends(get_settings),
) -> SavingsAnalytics:
    """
    Calculate savings compared to always using frontier models.

    Shows how much money was saved by intelligent routing.
    """
    user_id = request.headers.get("X-User-ID")
    start_date, end_date = _parse_period(period)

    cosmos = get_cosmos_client(settings)
    savings = await cosmos.calculate_savings(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    return SavingsAnalytics(
        period=period,
        start_date=start_date,
        end_date=end_date,
        actual_cost=savings["actual_cost"],
        frontier_cost=savings["frontier_cost"],
        savings=savings["savings"],
        savings_percentage=savings["savings_percentage"],
        requests_routed_to_lower_tiers=savings["requests_routed_to_lower_tiers"],
        total_requests=savings["total_requests"],
    )


@router.get("/realtime")
async def get_realtime_stats(
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Get real-time statistics from Redis.

    Returns recent request counts and current activity.
    """
    redis = get_redis_client(settings)

    # Get counters
    total_requests = await redis.get_counter("total_requests")
    frontier_requests = await redis.get_counter("requests:frontier")
    standard_requests = await redis.get_counter("requests:standard")
    fast_requests = await redis.get_counter("requests:fast")

    # Get recent requests
    recent = await redis.get_recent_requests(limit=10)

    # Calculate recent stats
    recent_costs = [r.get("cost", 0) for r in recent]
    recent_latencies = [r.get("latency_ms", 0) for r in recent]

    return {
        "total_requests": total_requests,
        "requests_by_tier": {
            "frontier": frontier_requests,
            "standard": standard_requests,
            "fast": fast_requests,
        },
        "recent_requests": recent,
        "recent_avg_cost": sum(recent_costs) / len(recent_costs) if recent_costs else 0,
        "recent_avg_latency_ms": sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0,
    }


@router.get("/models")
async def get_model_stats(
    request: Request,
    period: Literal["daily", "weekly", "monthly"] = Query(default="monthly"),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Get statistics broken down by model.

    Shows usage patterns for each model.
    """
    user_id = request.headers.get("X-User-ID")
    start_date, end_date = _parse_period(period)

    cosmos = get_cosmos_client(settings)
    analytics = await cosmos.get_cost_analytics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Format model stats
    model_stats = {}
    for model, cost in analytics["cost_by_model"].items():
        model_stats[model] = {
            "total_cost": round(cost, 4),
            "percentage_of_total": round(
                cost / analytics["total_cost"] * 100, 2
            ) if analytics["total_cost"] > 0 else 0,
        }

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "models": model_stats,
        "total_cost": analytics["total_cost"],
    }

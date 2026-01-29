"""Budget management endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, Request

from backend.config import Settings, get_settings
from backend.models import BudgetStatus, BudgetUpdateRequest
from backend.budget import BudgetController
from backend.storage import get_redis_client, get_cosmos_client

router = APIRouter(prefix="/api/budget", tags=["budget"])


def get_budget_controller(settings: Settings = Depends(get_settings)) -> BudgetController:
    """Get budget controller instance."""
    redis = get_redis_client(settings)
    cosmos = get_cosmos_client(settings)
    return BudgetController(settings, redis, cosmos)


@router.get("", response_model=BudgetStatus)
async def get_budget_status(
    request: Request,
    budget_controller: BudgetController = Depends(get_budget_controller),
) -> BudgetStatus:
    """
    Get current budget status.

    Returns current spend, limits, and any active alerts.
    """
    user_id = request.headers.get("X-User-ID", "default")
    return await budget_controller.get_status(user_id)


@router.put("", response_model=BudgetStatus)
async def update_budget(
    request: Request,
    budget_update: BudgetUpdateRequest,
    budget_controller: BudgetController = Depends(get_budget_controller),
) -> BudgetStatus:
    """
    Update budget configuration.

    Allows setting daily, weekly, and monthly limits, as well as alert thresholds.
    """
    user_id = request.headers.get("X-User-ID", "default")

    return await budget_controller.update_config(
        user_id=user_id,
        daily_limit=budget_update.daily_limit,
        weekly_limit=budget_update.weekly_limit,
        monthly_limit=budget_update.monthly_limit,
        alert_thresholds=budget_update.alert_thresholds,
        hard_limit=budget_update.hard_limit,
    )


@router.post("/reset", response_model=BudgetStatus)
async def reset_budget(
    request: Request,
    period: Literal["daily", "weekly", "monthly", "all"] = "all",
    budget_controller: BudgetController = Depends(get_budget_controller),
) -> BudgetStatus:
    """
    Reset budget spend counters.

    Use this to manually reset spend tracking for a specific period or all periods.
    """
    user_id = request.headers.get("X-User-ID", "default")
    return await budget_controller.reset_spend(user_id, period)


@router.get("/alerts")
async def get_budget_alerts(
    request: Request,
    budget_controller: BudgetController = Depends(get_budget_controller),
) -> dict:
    """
    Get active budget alerts.

    Returns a list of any threshold warnings or limit exceeded alerts.
    """
    user_id = request.headers.get("X-User-ID", "default")
    status = await budget_controller.get_status(user_id)

    return {
        "user_id": user_id,
        "alerts": status.alerts,
        "is_limited": status.is_limited,
        "utilization": {
            "daily": round(status.daily_spent / status.daily_limit * 100, 2)
            if status.daily_limit > 0 else 0,
            "weekly": round(status.weekly_spent / status.weekly_limit * 100, 2)
            if status.weekly_limit > 0 else 0,
            "monthly": round(status.monthly_spent / status.monthly_limit * 100, 2)
            if status.monthly_limit > 0 else 0,
        },
    }

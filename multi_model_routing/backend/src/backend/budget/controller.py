"""Budget controller for cost management."""

import logging
from dataclasses import dataclass
from typing import Literal

from backend.config import Settings
from backend.models import BudgetStatus
from backend.storage import RedisClient, CosmosDBClient

logger = logging.getLogger(__name__)


@dataclass
class BudgetCheckResult:
    """Result of a budget check."""

    allowed: bool
    reason: str | None = None
    alerts: list[str] | None = None
    remaining_daily: float = 0.0
    remaining_weekly: float = 0.0
    remaining_monthly: float = 0.0


class BudgetController:
    """Manages budget limits and tracking."""

    def __init__(
        self,
        settings: Settings,
        redis_client: RedisClient,
        cosmos_client: CosmosDBClient,
    ) -> None:
        """Initialize the budget controller."""
        self._settings = settings
        self._redis = redis_client
        self._cosmos = cosmos_client

    async def check_budget(
        self,
        user_id: str,
        estimated_cost: float,
    ) -> BudgetCheckResult:
        """
        Check if a request is within budget.

        Args:
            user_id: User identifier
            estimated_cost: Estimated cost of the request

        Returns:
            BudgetCheckResult indicating if request is allowed
        """
        # Get budget config
        config = await self._cosmos.get_budget_config(user_id)

        if not config:
            # Use defaults
            daily_limit = self._settings.default_daily_budget
            weekly_limit = self._settings.default_weekly_budget
            monthly_limit = self._settings.default_monthly_budget
            alert_thresholds = [0.5, 0.75, 0.9]
            hard_limit = True
        else:
            daily_limit = config.get("daily_limit", self._settings.default_daily_budget)
            weekly_limit = config.get("weekly_limit", self._settings.default_weekly_budget)
            monthly_limit = config.get("monthly_limit", self._settings.default_monthly_budget)
            alert_thresholds = config.get("alert_thresholds", [0.5, 0.75, 0.9])
            hard_limit = config.get("hard_limit", True)

        # Get current spend
        daily_spent = await self._redis.get_budget_spend(user_id, "daily")
        weekly_spent = await self._redis.get_budget_spend(user_id, "weekly")
        monthly_spent = await self._redis.get_budget_spend(user_id, "monthly")

        # Calculate remaining
        daily_remaining = daily_limit - daily_spent
        weekly_remaining = weekly_limit - weekly_spent
        monthly_remaining = monthly_limit - monthly_spent

        # Check alerts
        alerts = []
        for threshold in sorted(alert_thresholds):
            if daily_spent >= daily_limit * threshold:
                alerts.append(f"Daily budget at {int(threshold * 100)}% (${daily_spent:.2f}/${daily_limit:.2f})")
            if weekly_spent >= weekly_limit * threshold:
                alerts.append(f"Weekly budget at {int(threshold * 100)}% (${weekly_spent:.2f}/${weekly_limit:.2f})")
            if monthly_spent >= monthly_limit * threshold:
                alerts.append(f"Monthly budget at {int(threshold * 100)}% (${monthly_spent:.2f}/${monthly_limit:.2f})")

        # Check if request is allowed
        if hard_limit:
            if daily_spent + estimated_cost > daily_limit:
                return BudgetCheckResult(
                    allowed=False,
                    reason=f"Daily budget exceeded (${daily_spent:.2f}/${daily_limit:.2f})",
                    alerts=alerts,
                    remaining_daily=max(0, daily_remaining),
                    remaining_weekly=max(0, weekly_remaining),
                    remaining_monthly=max(0, monthly_remaining),
                )

            if weekly_spent + estimated_cost > weekly_limit:
                return BudgetCheckResult(
                    allowed=False,
                    reason=f"Weekly budget exceeded (${weekly_spent:.2f}/${weekly_limit:.2f})",
                    alerts=alerts,
                    remaining_daily=max(0, daily_remaining),
                    remaining_weekly=max(0, weekly_remaining),
                    remaining_monthly=max(0, monthly_remaining),
                )

            if monthly_spent + estimated_cost > monthly_limit:
                return BudgetCheckResult(
                    allowed=False,
                    reason=f"Monthly budget exceeded (${monthly_spent:.2f}/${monthly_limit:.2f})",
                    alerts=alerts,
                    remaining_daily=max(0, daily_remaining),
                    remaining_weekly=max(0, weekly_remaining),
                    remaining_monthly=max(0, monthly_remaining),
                )

        return BudgetCheckResult(
            allowed=True,
            alerts=alerts if alerts else None,
            remaining_daily=max(0, daily_remaining - estimated_cost),
            remaining_weekly=max(0, weekly_remaining - estimated_cost),
            remaining_monthly=max(0, monthly_remaining - estimated_cost),
        )

    async def record_spend(
        self,
        user_id: str,
        cost: float,
    ) -> None:
        """Record spend after a request completes."""
        await self._redis.increment_spend(user_id, cost, "daily")
        await self._redis.increment_spend(user_id, cost, "weekly")
        await self._redis.increment_spend(user_id, cost, "monthly")

    async def get_status(self, user_id: str) -> BudgetStatus:
        """Get current budget status for a user."""
        # Get config
        config = await self._cosmos.get_budget_config(user_id)

        if not config:
            daily_limit = self._settings.default_daily_budget
            weekly_limit = self._settings.default_weekly_budget
            monthly_limit = self._settings.default_monthly_budget
        else:
            daily_limit = config.get("daily_limit", self._settings.default_daily_budget)
            weekly_limit = config.get("weekly_limit", self._settings.default_weekly_budget)
            monthly_limit = config.get("monthly_limit", self._settings.default_monthly_budget)

        # Get current spend
        daily_spent = await self._redis.get_budget_spend(user_id, "daily")
        weekly_spent = await self._redis.get_budget_spend(user_id, "weekly")
        monthly_spent = await self._redis.get_budget_spend(user_id, "monthly")

        # Check for alerts
        alerts = []
        is_limited = False

        if daily_spent >= daily_limit:
            alerts.append("Daily budget limit reached")
            is_limited = True
        elif daily_spent >= daily_limit * 0.9:
            alerts.append("Daily budget at 90%")
        elif daily_spent >= daily_limit * 0.75:
            alerts.append("Daily budget at 75%")

        if weekly_spent >= weekly_limit:
            alerts.append("Weekly budget limit reached")
            is_limited = True
        elif weekly_spent >= weekly_limit * 0.9:
            alerts.append("Weekly budget at 90%")

        if monthly_spent >= monthly_limit:
            alerts.append("Monthly budget limit reached")
            is_limited = True
        elif monthly_spent >= monthly_limit * 0.9:
            alerts.append("Monthly budget at 90%")

        return BudgetStatus(
            user_id=user_id,
            daily_limit=daily_limit,
            daily_spent=round(daily_spent, 4),
            daily_remaining=round(max(0, daily_limit - daily_spent), 4),
            weekly_limit=weekly_limit,
            weekly_spent=round(weekly_spent, 4),
            weekly_remaining=round(max(0, weekly_limit - weekly_spent), 4),
            monthly_limit=monthly_limit,
            monthly_spent=round(monthly_spent, 4),
            monthly_remaining=round(max(0, monthly_limit - monthly_spent), 4),
            alerts=alerts,
            is_limited=is_limited,
        )

    async def update_config(
        self,
        user_id: str,
        daily_limit: float | None = None,
        weekly_limit: float | None = None,
        monthly_limit: float | None = None,
        alert_thresholds: list[float] | None = None,
        hard_limit: bool | None = None,
    ) -> BudgetStatus:
        """Update budget configuration."""
        # Get existing config
        existing = await self._cosmos.get_budget_config(user_id)

        # Merge with new values
        new_daily = daily_limit if daily_limit is not None else (
            existing.get("daily_limit") if existing else self._settings.default_daily_budget
        )
        new_weekly = weekly_limit if weekly_limit is not None else (
            existing.get("weekly_limit") if existing else self._settings.default_weekly_budget
        )
        new_monthly = monthly_limit if monthly_limit is not None else (
            existing.get("monthly_limit") if existing else self._settings.default_monthly_budget
        )
        new_thresholds = alert_thresholds if alert_thresholds is not None else (
            existing.get("alert_thresholds") if existing else [0.5, 0.75, 0.9]
        )
        new_hard_limit = hard_limit if hard_limit is not None else (
            existing.get("hard_limit") if existing else True
        )

        # Save to Cosmos
        await self._cosmos.upsert_budget_config(
            user_id=user_id,
            daily_limit=new_daily,
            weekly_limit=new_weekly,
            monthly_limit=new_monthly,
            alert_thresholds=new_thresholds,
            hard_limit=new_hard_limit,
        )

        # Return updated status
        return await self.get_status(user_id)

    async def reset_spend(
        self,
        user_id: str,
        period: Literal["daily", "weekly", "monthly", "all"] = "all",
    ) -> BudgetStatus:
        """Reset spend counters."""
        if period == "all":
            await self._redis.reset_budget(user_id, "daily")
            await self._redis.reset_budget(user_id, "weekly")
            await self._redis.reset_budget(user_id, "monthly")
        else:
            await self._redis.reset_budget(user_id, period)

        return await self.get_status(user_id)

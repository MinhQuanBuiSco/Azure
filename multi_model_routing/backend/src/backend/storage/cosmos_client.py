"""Cosmos DB client for persistent storage."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient, ContainerProxy

from backend.config import Settings

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """Cosmos DB client for routing logs and analytics."""

    ROUTING_LOGS_CONTAINER = "routing_logs"
    BUDGETS_CONTAINER = "budgets"
    ANALYTICS_CONTAINER = "analytics_aggregates"

    def __init__(self, settings: Settings) -> None:
        """Initialize the Cosmos DB client."""
        self._settings = settings
        self._client: CosmosClient | None = None
        self._database = None
        self._containers: dict[str, ContainerProxy] = {}

    async def _get_client(self) -> CosmosClient:
        """Get or create the Cosmos DB client."""
        if self._client is None:
            self._client = CosmosClient(
                self._settings.cosmos_endpoint,
                credential=self._settings.cosmos_key.get_secret_value(),
            )
        return self._client

    async def _get_database(self):
        """Get or create the database."""
        if self._database is None:
            client = await self._get_client()
            self._database = client.get_database_client(self._settings.cosmos_database)
        return self._database

    async def _get_container(self, container_name: str) -> ContainerProxy:
        """Get or create a container."""
        if container_name not in self._containers:
            database = await self._get_database()
            self._containers[container_name] = database.get_container_client(container_name)
        return self._containers[container_name]

    async def initialize_containers(self) -> None:
        """Create containers if they don't exist."""
        try:
            client = await self._get_client()
            database = client.get_database_client(self._settings.cosmos_database)

            # Create database if not exists
            try:
                await client.create_database(self._settings.cosmos_database)
            except Exception:
                pass  # Database already exists

            # Define containers
            containers = [
                (self.ROUTING_LOGS_CONTAINER, "/user_id"),
                (self.BUDGETS_CONTAINER, "/user_id"),
                (self.ANALYTICS_CONTAINER, "/date"),
            ]

            for container_name, partition_key in containers:
                try:
                    await database.create_container(
                        id=container_name,
                        partition_key=PartitionKey(path=partition_key),
                    )
                    logger.info(f"Created container: {container_name}")
                except Exception:
                    pass  # Container already exists

        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB containers: {e}")
            raise

    async def health_check(self) -> bool:
        """Check Cosmos DB connectivity."""
        try:
            client = await self._get_client()
            # Try to read database properties
            database = client.get_database_client(self._settings.cosmos_database)
            await database.read()
            return True
        except Exception as e:
            logger.warning(f"Cosmos DB health check failed: {e}")
            return False

    # Routing log methods
    async def log_routing_decision(
        self,
        user_id: str,
        request_id: str,
        model: str,
        tier: str,
        complexity_score: int,
        category: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        routing_reason: str,
    ) -> str:
        """Log a routing decision."""
        container = await self._get_container(self.ROUTING_LOGS_CONTAINER)

        doc_id = str(uuid4())
        document = {
            "id": doc_id,
            "user_id": user_id,
            "request_id": request_id,
            "model": model,
            "tier": tier,
            "complexity_score": complexity_score,
            "category": category,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "latency_ms": latency_ms,
            "routing_reason": routing_reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await container.create_item(body=document)
        return doc_id

    async def get_routing_logs(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get routing logs for a user."""
        container = await self._get_container(self.ROUTING_LOGS_CONTAINER)

        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]

        if start_date:
            query += " AND c.timestamp >= @start_date"
            params.append({"name": "@start_date", "value": start_date.isoformat()})

        if end_date:
            query += " AND c.timestamp <= @end_date"
            params.append({"name": "@end_date", "value": end_date.isoformat()})

        query += " ORDER BY c.timestamp DESC"

        results = []
        async for item in container.query_items(
            query=query,
            parameters=params,
            max_item_count=limit,
        ):
            results.append(item)
            if len(results) >= limit:
                break

        return results

    # Budget methods
    async def get_budget_config(self, user_id: str) -> dict[str, Any] | None:
        """Get budget configuration for a user."""
        container = await self._get_container(self.BUDGETS_CONTAINER)

        try:
            item = await container.read_item(item=user_id, partition_key=user_id)
            return item
        except Exception:
            return None

    async def upsert_budget_config(
        self,
        user_id: str,
        daily_limit: float,
        weekly_limit: float,
        monthly_limit: float,
        alert_thresholds: list[float] | None = None,
        hard_limit: bool = True,
    ) -> dict[str, Any]:
        """Create or update budget configuration."""
        container = await self._get_container(self.BUDGETS_CONTAINER)

        document = {
            "id": user_id,
            "user_id": user_id,
            "daily_limit": daily_limit,
            "weekly_limit": weekly_limit,
            "monthly_limit": monthly_limit,
            "alert_thresholds": alert_thresholds or [0.5, 0.75, 0.9],
            "hard_limit": hard_limit,
            "updated_at": datetime.utcnow().isoformat(),
        }

        await container.upsert_item(body=document)
        return document

    # Analytics methods
    async def _query_routing_logs(
        self,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Query routing logs from Cosmos DB. Single shared query for all analytics."""
        container = await self._get_container(self.ROUTING_LOGS_CONTAINER)

        # Default to last 30 days
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        query = """
            SELECT
                c.cost,
                c.tier,
                c.model,
                c.input_tokens,
                c.output_tokens
            FROM c
            WHERE c.timestamp >= @start_date
              AND c.timestamp <= @end_date
        """
        params: list[dict[str, Any]] = [
            {"name": "@start_date", "value": start_date.isoformat()},
            {"name": "@end_date", "value": end_date.isoformat()},
        ]

        if user_id:
            query += " AND c.user_id = @user_id"
            params.append({"name": "@user_id", "value": user_id})

        results: list[dict[str, Any]] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results

    async def get_cost_analytics(
        self,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated cost analytics."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        results = await self._query_routing_logs(user_id, start_date, end_date)

        total_cost = 0.0
        total_requests = 0
        cost_by_tier: dict[str, float] = {}
        cost_by_model: dict[str, float] = {}

        for item in results:
            cost = item.get("cost", 0) or 0
            tier = item.get("tier", "unknown")
            model = item.get("model", "unknown")

            total_cost += cost
            total_requests += 1
            cost_by_tier[tier] = cost_by_tier.get(tier, 0) + cost
            cost_by_model[model] = cost_by_model.get(model, 0) + cost

        return {
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "average_cost_per_request": (
                round(total_cost / total_requests, 6) if total_requests > 0 else 0
            ),
            "cost_by_tier": cost_by_tier,
            "cost_by_model": cost_by_model,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    async def calculate_savings(
        self,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Calculate savings compared to always using frontier tier."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        results = await self._query_routing_logs(user_id, start_date, end_date)

        # Frontier pricing (GPT-4o)
        FRONTIER_INPUT_COST = 5.0 / 1_000_000
        FRONTIER_OUTPUT_COST = 15.0 / 1_000_000

        actual_cost = 0.0
        frontier_cost = 0.0
        total_requests = 0
        lower_tier_requests = 0

        for item in results:
            input_tokens = item.get("input_tokens", 0) or 0
            output_tokens = item.get("output_tokens", 0) or 0
            cost = item.get("cost", 0) or 0
            tier = item.get("tier", "")

            actual_cost += cost
            frontier_cost += (
                input_tokens * FRONTIER_INPUT_COST + output_tokens * FRONTIER_OUTPUT_COST
            )
            total_requests += 1

            if tier in ["fast", "standard"]:
                lower_tier_requests += 1

        savings = frontier_cost - actual_cost
        savings_pct = (savings / frontier_cost * 100) if frontier_cost > 0 else 0

        return {
            "actual_cost": round(actual_cost, 4),
            "frontier_cost": round(frontier_cost, 4),
            "savings": round(savings, 4),
            "savings_percentage": round(savings_pct, 2),
            "total_requests": total_requests,
            "requests_routed_to_lower_tiers": lower_tier_requests,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    async def close(self) -> None:
        """Close the Cosmos DB client."""
        if self._client:
            await self._client.close()
            self._client = None


# Global instance
_cosmos_client: CosmosDBClient | None = None


def get_cosmos_client(settings: Settings) -> CosmosDBClient:
    """Get or create the global Cosmos DB client."""
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosDBClient(settings)
    return _cosmos_client

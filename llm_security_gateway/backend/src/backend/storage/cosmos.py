"""Cosmos DB client for audit logs."""

import uuid
from datetime import datetime
from typing import Any

from azure.cosmos import CosmosClient as AzureCosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from backend.config.settings import get_settings
from backend.models.audit import AuditLog, AuditLogCreate, AuditLogQuery, AuditLogSummary


class CosmosClient:
    """Async client for Azure Cosmos DB audit logs."""

    def __init__(self):
        self.settings = get_settings()
        self._client: AzureCosmosClient | None = None
        self._database = None
        self._container = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Cosmos DB."""
        if self._connected:
            return True

        if not self.settings.cosmos_connection_string:
            print("Cosmos DB connection string not configured")
            return False

        try:
            self._client = AzureCosmosClient.from_connection_string(
                self.settings.cosmos_connection_string
            )

            # Get or create database
            self._database = self._client.create_database_if_not_exists(
                id=self.settings.cosmos_database_name
            )

            # Get or create container
            self._container = self._database.create_container_if_not_exists(
                id=self.settings.cosmos_container_name,
                partition_key=PartitionKey(path="/request_id"),
                offer_throughput=400,  # Minimum RUs
            )

            self._connected = True
            print(f"Connected to Cosmos DB database: {self.settings.cosmos_database_name}")
            return True

        except Exception as e:
            print(f"Failed to connect to Cosmos DB: {e}")
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        """Check if connected to Cosmos DB."""
        return self._connected

    async def create_audit_log(self, log: AuditLogCreate) -> AuditLog | None:
        """
        Create a new audit log entry.

        Args:
            log: The audit log data

        Returns:
            The created AuditLog with ID, or None if failed
        """
        if not self._connected:
            self.connect()

        if not self._connected:
            return None

        try:
            log_id = str(uuid.uuid4())
            item = {
                "id": log_id,
                **log.model_dump(mode="json"),
            }

            # Ensure timestamp is serialized properly
            if isinstance(item.get("timestamp"), datetime):
                item["timestamp"] = item["timestamp"].isoformat()

            self._container.create_item(body=item)

            return AuditLog(id=log_id, **log.model_dump())

        except Exception as e:
            print(f"Failed to create audit log: {e}")
            return None

    async def get_audit_log(self, log_id: str, request_id: str) -> AuditLog | None:
        """
        Get an audit log by ID.

        Args:
            log_id: The audit log ID
            request_id: The request ID (partition key)

        Returns:
            The AuditLog or None if not found
        """
        if not self._connected:
            self.connect()

        if not self._connected:
            return None

        try:
            item = self._container.read_item(item=log_id, partition_key=request_id)
            return AuditLog(**item)

        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            print(f"Failed to get audit log: {e}")
            return None

    async def query_audit_logs(self, query: AuditLogQuery) -> list[AuditLog]:
        """
        Query audit logs with filters.

        Args:
            query: Query parameters

        Returns:
            List of matching AuditLog entries
        """
        if not self._connected:
            self.connect()

        if not self._connected:
            return []

        try:
            # Build query
            conditions = []
            parameters = []

            if query.start_date:
                conditions.append("c.timestamp >= @start_date")
                parameters.append({"name": "@start_date", "value": query.start_date.isoformat()})

            if query.end_date:
                conditions.append("c.timestamp <= @end_date")
                parameters.append({"name": "@end_date", "value": query.end_date.isoformat()})

            if query.status:
                conditions.append("c.status = @status")
                parameters.append({"name": "@status", "value": query.status})

            if query.user_id:
                conditions.append("c.user_id = @user_id")
                parameters.append({"name": "@user_id", "value": query.user_id})

            if query.model:
                conditions.append("c.model = @model")
                parameters.append({"name": "@model", "value": query.model})

            if query.has_threats:
                conditions.append("ARRAY_LENGTH(c.threats_detected) > 0")

            if query.has_pii:
                conditions.append("ARRAY_LENGTH(c.pii_detected) > 0")

            # Build full query
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            order_clause = f"c.{query.sort_by} {query.sort_order.upper()}"

            query_text = f"""
                SELECT * FROM c
                WHERE {where_clause}
                ORDER BY {order_clause}
                OFFSET {query.offset} LIMIT {query.limit}
            """

            items = list(self._container.query_items(
                query=query_text,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))

            return [AuditLog(**item) for item in items]

        except Exception as e:
            print(f"Failed to query audit logs: {e}")
            return []

    async def get_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AuditLogSummary:
        """
        Get summary statistics for audit logs.

        Args:
            start_date: Start of time range
            end_date: End of time range

        Returns:
            AuditLogSummary with statistics
        """
        if not self._connected:
            self.connect()

        if not self._connected:
            return AuditLogSummary()

        try:
            # Build date filter
            conditions = []
            parameters = []

            if start_date:
                conditions.append("c.timestamp >= @start_date")
                parameters.append({"name": "@start_date", "value": start_date.isoformat()})

            if end_date:
                conditions.append("c.timestamp <= @end_date")
                parameters.append({"name": "@end_date", "value": end_date.isoformat()})

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Query for counts
            query_text = f"""
                SELECT
                    COUNT(1) as total_requests,
                    SUM(CASE WHEN c.status = 'allowed' THEN 1 ELSE 0 END) as allowed_requests,
                    SUM(CASE WHEN c.status = 'blocked' THEN 1 ELSE 0 END) as blocked_requests,
                    SUM(CASE WHEN c.status = 'filtered' THEN 1 ELSE 0 END) as filtered_requests,
                    SUM(CASE WHEN c.status = 'error' THEN 1 ELSE 0 END) as error_requests,
                    SUM(c.total_tokens) as total_tokens,
                    SUM(c.prompt_tokens) as prompt_tokens,
                    SUM(c.completion_tokens) as completion_tokens,
                    AVG(c.response_time_ms) as avg_response_time_ms
                FROM c
                WHERE {where_clause}
            """

            items = list(self._container.query_items(
                query=query_text,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))

            if items:
                item = items[0]
                return AuditLogSummary(
                    total_requests=item.get("total_requests", 0) or 0,
                    allowed_requests=item.get("allowed_requests", 0) or 0,
                    blocked_requests=item.get("blocked_requests", 0) or 0,
                    filtered_requests=item.get("filtered_requests", 0) or 0,
                    error_requests=item.get("error_requests", 0) or 0,
                    total_tokens=item.get("total_tokens", 0) or 0,
                    prompt_tokens=item.get("prompt_tokens", 0) or 0,
                    completion_tokens=item.get("completion_tokens", 0) or 0,
                    avg_response_time_ms=item.get("avg_response_time_ms", 0) or 0,
                    start_date=start_date,
                    end_date=end_date,
                )

            return AuditLogSummary(start_date=start_date, end_date=end_date)

        except Exception as e:
            print(f"Failed to get summary: {e}")
            return AuditLogSummary()


# Global instance
_client: CosmosClient | None = None


def get_cosmos_client() -> CosmosClient:
    """Get or create the Cosmos DB client."""
    global _client
    if _client is None:
        _client = CosmosClient()
    return _client

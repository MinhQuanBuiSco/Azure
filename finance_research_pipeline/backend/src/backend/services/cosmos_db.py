"""Cosmos DB service for session persistence."""

from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.schemas.research import ResearchStatus, ResearchType

logger = get_logger(__name__)


class CosmosDBService:
    """Service for persisting research sessions and reports to Cosmos DB."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize Cosmos DB service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client: CosmosClient | None = None
        self.database = None
        self.sessions_container = None
        self.reports_container = None

    async def initialize(self) -> None:
        """Initialize Cosmos DB client and containers."""
        if not self.settings.cosmos_endpoint or not self.settings.cosmos_key:
            logger.warning("Cosmos DB not configured")
            return

        try:
            self.client = CosmosClient(
                url=self.settings.cosmos_endpoint,
                credential=self.settings.cosmos_key.get_secret_value(),
            )

            # Get or create database
            self.database = self.client.create_database_if_not_exists(
                id=self.settings.cosmos_database
            )

            # Get or create sessions container
            self.sessions_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_container_sessions,
                partition_key=PartitionKey(path="/research_id"),
                offer_throughput=400,
            )

            # Get or create reports container
            self.reports_container = self.database.create_container_if_not_exists(
                id=self.settings.cosmos_container_reports,
                partition_key=PartitionKey(path="/research_id"),
                offer_throughput=400,
            )

            logger.info("Cosmos DB initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

    async def create_session(
        self,
        research_id: str,
        company_name: str,
        research_type: ResearchType,
        ticker_symbol: str | None = None,
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new research session.

        Args:
            research_id: Unique research session ID
            company_name: Company to research
            research_type: Type of research
            ticker_symbol: Optional ticker symbol
            additional_context: Optional additional context

        Returns:
            Created session document
        """
        if not self.sessions_container:
            raise RuntimeError("Cosmos DB not initialized")

        now = datetime.now(UTC).isoformat()

        session = {
            "id": research_id,
            "research_id": research_id,
            "company_name": company_name,
            "ticker_symbol": ticker_symbol,
            "research_type": research_type.value,
            "additional_context": additional_context,
            "status": ResearchStatus.PENDING.value,
            "progress": 0.0,
            "current_agent": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error_message": None,
            "agent_outputs": {},
        }

        self.sessions_container.create_item(body=session)
        logger.info(f"Created research session: {research_id}")
        return session

    async def get_session(self, research_id: str) -> dict[str, Any] | None:
        """
        Get a research session by ID.

        Args:
            research_id: Session ID

        Returns:
            Session document or None
        """
        if not self.sessions_container:
            return None

        try:
            return self.sessions_container.read_item(
                item=research_id,
                partition_key=research_id,
            )
        except CosmosResourceNotFoundError:
            return None

    async def update_session(
        self,
        research_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Update a research session.

        Args:
            research_id: Session ID
            updates: Fields to update

        Returns:
            Updated session document or None
        """
        if not self.sessions_container:
            return None

        try:
            session = await self.get_session(research_id)
            if not session:
                return None

            session.update(updates)
            session["updated_at"] = datetime.now(UTC).isoformat()

            return self.sessions_container.replace_item(
                item=research_id,
                body=session,
            )
        except Exception as e:
            logger.error(f"Failed to update session {research_id}: {e}")
            return None

    async def save_report(
        self,
        research_id: str,
        report_content: str,
        report_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Save a research report.

        Args:
            research_id: Associated session ID
            report_content: Full report content (markdown/HTML)
            report_data: Structured report data

        Returns:
            Created report document
        """
        if not self.reports_container:
            raise RuntimeError("Cosmos DB not initialized")

        report_id = str(uuid4())
        now = datetime.now(UTC).isoformat()

        report = {
            "id": report_id,
            "research_id": research_id,
            "content": report_content,
            "data": report_data,
            "created_at": now,
        }

        self.reports_container.create_item(body=report)
        logger.info(f"Saved report {report_id} for session {research_id}")
        return report

    async def get_report(self, research_id: str) -> dict[str, Any] | None:
        """
        Get a report by research session ID.

        Args:
            research_id: Session ID

        Returns:
            Report document or None
        """
        if not self.reports_container:
            return None

        try:
            query = "SELECT * FROM c WHERE c.research_id = @research_id"
            items = list(
                self.reports_container.query_items(
                    query=query,
                    parameters=[{"name": "@research_id", "value": research_id}],
                    enable_cross_partition_query=True,
                )
            )
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to get report for {research_id}: {e}")
            return None

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: ResearchStatus | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List research sessions with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            status: Optional status filter

        Returns:
            Tuple of (sessions list, total count)
        """
        if not self.sessions_container:
            return [], 0

        try:
            # Build query
            query = "SELECT * FROM c"
            parameters = []

            if status:
                query += " WHERE c.status = @status"
                parameters.append({"name": "@status", "value": status.value})

            query += " ORDER BY c.created_at DESC"

            # Get all items (for count and pagination)
            items = list(
                self.sessions_container.query_items(
                    query=query,
                    parameters=parameters if parameters else None,
                    enable_cross_partition_query=True,
                )
            )

            total = len(items)
            start = (page - 1) * page_size
            end = start + page_size

            return items[start:end], total

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return [], 0

    async def delete_session(self, research_id: str) -> bool:
        """
        Delete a research session and its report.

        Args:
            research_id: Session ID

        Returns:
            True if deleted, False otherwise
        """
        if not self.sessions_container or not self.reports_container:
            return False

        try:
            # Delete session
            self.sessions_container.delete_item(
                item=research_id,
                partition_key=research_id,
            )

            # Delete associated report
            report = await self.get_report(research_id)
            if report:
                self.reports_container.delete_item(
                    item=report["id"],
                    partition_key=research_id,
                )

            logger.info(f"Deleted session and report: {research_id}")
            return True

        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {research_id}: {e}")
            return False

"""WebSocket connection manager for real-time updates."""

import asyncio
import json
from datetime import datetime, UTC
from typing import Any

from fastapi import WebSocket

from backend.core.logging import get_logger
from backend.schemas.agent import AgentProgress, AgentType, PipelineProgress

logger = get_logger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections and broadcasting."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        # research_id -> list of connected WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, research_id: str) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            research_id: Research session ID
        """
        await websocket.accept()

        async with self._lock:
            if research_id not in self.active_connections:
                self.active_connections[research_id] = []
            self.active_connections[research_id].append(websocket)

        logger.info(f"WebSocket connected for research: {research_id}")

    async def disconnect(self, websocket: WebSocket, research_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            research_id: Research session ID
        """
        async with self._lock:
            if research_id in self.active_connections:
                if websocket in self.active_connections[research_id]:
                    self.active_connections[research_id].remove(websocket)
                if not self.active_connections[research_id]:
                    del self.active_connections[research_id]

        logger.info(f"WebSocket disconnected for research: {research_id}")

    async def send_message(
        self,
        research_id: str,
        message_type: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Send a message to all connections for a research session.

        Args:
            research_id: Research session ID
            message_type: Type of message (progress, error, complete, etc.)
            payload: Message payload
        """
        message = {
            "type": message_type,
            "research_id": research_id,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        async with self._lock:
            connections = self.active_connections.get(research_id, []).copy()

        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket, research_id)

    async def send_agent_progress(
        self,
        research_id: str,
        agent_type: AgentType,
        progress: AgentProgress,
    ) -> None:
        """
        Send agent progress update.

        Args:
            research_id: Research session ID
            agent_type: Type of agent
            progress: Agent progress data
        """
        await self.send_message(
            research_id,
            "agent_progress",
            {
                "agent_type": agent_type.value,
                "progress": progress.model_dump(mode='json'),
            },
        )

    async def send_pipeline_progress(
        self,
        research_id: str,
        progress: PipelineProgress,
    ) -> None:
        """
        Send overall pipeline progress update.

        Args:
            research_id: Research session ID
            progress: Pipeline progress data
        """
        await self.send_message(
            research_id,
            "pipeline_progress",
            progress.model_dump(mode='json'),
        )

    async def send_error(
        self,
        research_id: str,
        error_message: str,
        agent_type: AgentType | None = None,
    ) -> None:
        """
        Send error message.

        Args:
            research_id: Research session ID
            error_message: Error description
            agent_type: Optional agent that caused the error
        """
        await self.send_message(
            research_id,
            "error",
            {
                "error": error_message,
                "agent_type": agent_type.value if agent_type else None,
            },
        )

    async def send_completion(
        self,
        research_id: str,
        summary: str | None = None,
    ) -> None:
        """
        Send completion message.

        Args:
            research_id: Research session ID
            summary: Optional completion summary
        """
        await self.send_message(
            research_id,
            "complete",
            {
                "summary": summary,
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )

    async def broadcast_to_all(
        self,
        message_type: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message_type: Type of message
            payload: Message payload
        """
        async with self._lock:
            all_connections = [
                (rid, ws)
                for rid, connections in self.active_connections.items()
                for ws in connections
            ]

        for research_id, websocket in all_connections:
            try:
                await websocket.send_json({
                    "type": message_type,
                    "research_id": research_id,
                    "payload": payload,
                    "timestamp": datetime.now(UTC).isoformat(),
                })
            except Exception:
                pass

    def get_connection_count(self, research_id: str | None = None) -> int:
        """
        Get the number of active connections.

        Args:
            research_id: Optional specific research session

        Returns:
            Number of connections
        """
        if research_id:
            return len(self.active_connections.get(research_id, []))
        return sum(len(conns) for conns in self.active_connections.values())

    def is_connected(self, research_id: str) -> bool:
        """Check if there are active connections for a research session."""
        return research_id in self.active_connections and len(
            self.active_connections[research_id]
        ) > 0

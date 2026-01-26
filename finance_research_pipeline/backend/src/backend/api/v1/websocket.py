"""WebSocket endpoint for real-time agent progress updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.dependencies import get_websocket_manager
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/research/{research_id}")
async def research_progress_websocket(
    websocket: WebSocket,
    research_id: str,
) -> None:
    """
    WebSocket endpoint for receiving real-time research progress updates.

    Clients connect to this endpoint to receive:
    - Agent progress updates
    - Overall pipeline progress
    - Completion/error notifications

    Message format:
    {
        "type": "agent_progress" | "pipeline_progress" | "complete" | "error",
        "research_id": "uuid",
        "payload": { ... },
        "timestamp": "ISO timestamp"
    }
    """
    ws_manager = get_websocket_manager()

    try:
        # Accept and register connection
        await ws_manager.connect(websocket, research_id)
        logger.info(f"WebSocket connected for research: {research_id}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "research_id": research_id,
            "message": "Connected to research progress stream",
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, etc.)
                data = await websocket.receive_json()

                # Handle ping messages
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "research_id": research_id,
                    })

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for research: {research_id}")

    except Exception as e:
        logger.error(f"WebSocket error for research {research_id}: {e}")

    finally:
        # Clean up connection
        await ws_manager.disconnect(websocket, research_id)
        logger.info(f"WebSocket cleaned up for research: {research_id}")


@router.get("/connections")
async def get_active_connections() -> dict[str, int]:
    """Get count of active WebSocket connections."""
    ws_manager = get_websocket_manager()
    return {
        "total_connections": ws_manager.get_connection_count(),
    }

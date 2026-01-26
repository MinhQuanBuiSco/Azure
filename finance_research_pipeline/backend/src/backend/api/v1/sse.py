"""Server-Sent Events endpoint for LLM token streaming."""

import asyncio
import json
from datetime import datetime, UTC
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.core.dependencies import CacheServiceDep, LLMFactoryDep, SettingsDep
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/sse", tags=["sse"])

# In-memory stream state (for tracking active streams)
_active_streams: dict[str, bool] = {}


@router.get("/research/{research_id}/stream")
async def stream_research_output(
    research_id: str,
    cache_service: CacheServiceDep,
    llm_factory: LLMFactoryDep,
) -> EventSourceResponse:
    """
    Server-Sent Events endpoint for streaming LLM output.

    This endpoint provides real-time streaming of LLM-generated content
    during the research process.

    Event format:
    - event: token | agent_update | complete | error
    - data: JSON payload

    Example events:
    - Token: {"token": "text", "agent": "writer"}
    - Agent update: {"agent": "analyst", "status": "running"}
    - Complete: {"message": "Research complete"}
    - Error: {"error": "Error message"}
    """
    # Check if research exists
    session = await cache_service.get_research_state(research_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {research_id} not found",
        )

    # Mark stream as active
    _active_streams[research_id] = True

    async def generate_events() -> AsyncGenerator[dict, None]:
        """Generate SSE events for the research session."""
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "research_id": research_id,
                    "message": "Connected to research stream",
                    "timestamp": datetime.now(UTC).isoformat(),
                }),
            }

            # Monitor research progress and stream updates
            last_status = None
            last_agent = None

            while _active_streams.get(research_id, False):
                # Get current state
                current_session = await cache_service.get_research_state(research_id)

                if not current_session:
                    await asyncio.sleep(1)
                    continue

                current_status = current_session.get("status")
                current_agent = current_session.get("current_agent")

                # Send agent update if changed
                if current_agent != last_agent:
                    yield {
                        "event": "agent_update",
                        "data": json.dumps({
                            "agent": current_agent,
                            "status": "running",
                            "progress": current_session.get("progress", 0),
                            "timestamp": datetime.now(UTC).isoformat(),
                        }),
                    }
                    last_agent = current_agent

                # Check for status changes
                if current_status != last_status:
                    if current_status == "completed":
                        # Send completion event
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "research_id": research_id,
                                "message": "Research completed successfully",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }),
                        }
                        break

                    elif current_status == "failed":
                        # Send error event
                        yield {
                            "event": "error",
                            "data": json.dumps({
                                "research_id": research_id,
                                "error": current_session.get("error_message", "Unknown error"),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }),
                        }
                        break

                    last_status = current_status

                # Send progress heartbeat
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "progress": current_session.get("progress", 0),
                        "agent": current_agent,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }),
                }

                # Wait before next check
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for research: {research_id}")
        except Exception as e:
            logger.error(f"SSE stream error for research {research_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                }),
            }
        finally:
            # Clean up
            _active_streams.pop(research_id, None)

    return EventSourceResponse(
        generate_events(),
        media_type="text/event-stream",
    )


@router.delete("/research/{research_id}/stream")
async def stop_stream(research_id: str) -> dict[str, str]:
    """Stop an active SSE stream."""
    if research_id in _active_streams:
        _active_streams[research_id] = False
        return {"message": f"Stream stopped for research {research_id}"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No active stream for research {research_id}",
    )


@router.get("/streams/active")
async def get_active_streams() -> dict[str, list[str]]:
    """Get list of active SSE streams."""
    return {
        "active_streams": [
            rid for rid, active in _active_streams.items() if active
        ],
    }

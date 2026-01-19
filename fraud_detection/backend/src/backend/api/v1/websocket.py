"""
WebSocket endpoints for real-time fraud detection updates.

Provides live streaming of:
- Transaction scoring results
- Fraud alerts
- Dashboard statistics
"""
import asyncio
import json
from typing import Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self.transaction_subscribers: Set[WebSocket] = set()
        self.alert_subscribers: Set[WebSocket] = set()
        self.stats_subscribers: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, channel: str = "transactions"):
        """
        Connect a WebSocket client.

        Args:
            websocket: WebSocket connection
            channel: Channel to subscribe to (transactions, alerts, stats)
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        if channel == "transactions":
            self.transaction_subscribers.add(websocket)
        elif channel == "alerts":
            self.alert_subscribers.add(websocket)
        elif channel == "stats":
            self.stats_subscribers.add(websocket)

        print(f"✅ WebSocket connected: {channel} (Total connections: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.active_connections.discard(websocket)
        self.transaction_subscribers.discard(websocket)
        self.alert_subscribers.discard(websocket)
        self.stats_subscribers.discard(websocket)
        print(f"👋 WebSocket disconnected (Total connections: {len(self.active_connections)})")

    async def broadcast_transaction(self, transaction_data: dict):
        """
        Broadcast transaction result to all subscribers.

        Args:
            transaction_data: Transaction scoring result
        """
        message = {
            "type": "transaction",
            "timestamp": datetime.utcnow().isoformat(),
            "data": transaction_data
        }
        await self._broadcast(self.transaction_subscribers, message)

    async def broadcast_alert(self, alert_data: dict):
        """
        Broadcast fraud alert to all subscribers.

        Args:
            alert_data: Fraud alert details
        """
        message = {
            "type": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        await self._broadcast(self.alert_subscribers, message)

    async def broadcast_stats(self, stats_data: dict):
        """
        Broadcast dashboard statistics to all subscribers.

        Args:
            stats_data: Dashboard statistics
        """
        message = {
            "type": "stats",
            "timestamp": datetime.utcnow().isoformat(),
            "data": stats_data
        }
        await self._broadcast(self.stats_subscribers, message)

    async def _broadcast(self, subscribers: Set[WebSocket], message: dict):
        """
        Broadcast message to specific subscribers.

        Args:
            subscribers: Set of WebSocket connections
            message: Message to broadcast
        """
        disconnected = set()

        for websocket in subscribers:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.add(websocket)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_heartbeat(self):
        """Send periodic heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(30)  # Every 30 seconds

            message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "connections": len(self.active_connections)
            }

            disconnected = set()
            for websocket in self.active_connections.copy():
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(message)
                    else:
                        disconnected.add(websocket)
                except Exception:
                    disconnected.add(websocket)

            for websocket in disconnected:
                self.disconnect(websocket)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/transactions")
async def websocket_transactions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transaction updates.

    Streams fraud scoring results as transactions are processed.
    """
    await manager.connect(websocket, channel="transactions")

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "channel": "transactions",
            "message": "Connected to transaction feed",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and listen for client messages
        while True:
            # Receive messages from client (optional)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Client can send ping/pong or subscription updates
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except asyncio.TimeoutError:
                # No message received, continue
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time fraud alerts.

    Streams high-risk fraud alerts.
    """
    await manager.connect(websocket, channel="alerts")

    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "alerts",
            "message": "Connected to fraud alerts feed",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard statistics.

    Streams aggregated fraud detection metrics.
    """
    await manager.connect(websocket, channel="stats")

    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "stats",
            "message": "Connected to statistics feed",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def get_websocket_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager

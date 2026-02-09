"""WebSocket manager — broadcasts events to connected frontend clients.

Replaces legacy tkinter.after() polling with real-time push.
Maps legacy event types to typed WebSocket messages.
"""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket client connected ({len(self.active_connections)} total)"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket client disconnected ({len(self.active_connections)} total)"
        )

    async def broadcast(self, event: str, data: dict):
        """Broadcast an event to all connected clients."""
        message = json.dumps({"event": event, "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)


# Singleton
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler."""
    await manager.connect(websocket)
    try:
        while True:
            # Listen for client messages (e.g., subscription filters)
            data = await websocket.receive_text()
            # TODO: Handle client subscription messages
            # e.g., {"subscribe": ["finding", "stats_update", "high_score"]}
    except WebSocketDisconnect:
        manager.disconnect(websocket)

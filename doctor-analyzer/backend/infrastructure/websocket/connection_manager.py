"""WebSocket connection management for real-time streaming."""

from typing import Dict, Set, List
from fastapi import WebSocket
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for analysis streaming."""

    def __init__(self):
        # session_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = set()
            self._connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")

    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)
                if not self._connections[session_id]:
                    del self._connections[session_id]
        logger.info(f"WebSocket disconnected for session {session_id}")

    async def broadcast_to_session(self, session_id: str, message: dict) -> None:
        """Broadcast message to all connections for a session."""
        async with self._lock:
            connections = self._connections.get(session_id, set()).copy()

        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected
        for ws in disconnected:
            await self.disconnect(ws, session_id)

    async def send_emotion_update(
        self,
        session_id: str,
        timestamp_ms: int,
        emotions: List[dict],
        bounding_box: dict,
    ) -> None:
        """Send real-time emotion detection update."""
        await self.broadcast_to_session(session_id, {
            "type": "emotion_update",
            "timestamp_ms": timestamp_ms,
            "emotions": emotions,
            "bounding_box": bounding_box,
        })

    async def send_status_update(
        self,
        session_id: str,
        status: str,
        progress: float = None,
        message: str = None,
    ) -> None:
        """Send analysis status update."""
        payload = {"type": "status_update", "status": status}
        if progress is not None:
            payload["progress"] = progress
        if message is not None:
            payload["message"] = message
        await self.broadcast_to_session(session_id, payload)

    async def send_transcription_update(
        self,
        session_id: str,
        text: str,
        start_time: float,
        end_time: float,
    ) -> None:
        """Send transcription segment update."""
        await self.broadcast_to_session(session_id, {
            "type": "transcription_update",
            "text": text,
            "start_time": start_time,
            "end_time": end_time,
        })

    async def send_complete(self, session_id: str, results: dict) -> None:
        """Send analysis completion message."""
        await self.broadcast_to_session(session_id, {
            "type": "complete",
            "results": results,
        })

    async def send_error(self, session_id: str, message: str) -> None:
        """Send error message."""
        await self.broadcast_to_session(session_id, {
            "type": "error",
            "message": message,
        })

    def get_connection_count(self, session_id: str) -> int:
        """Get number of connections for a session."""
        return len(self._connections.get(session_id, set()))

    def has_connections(self, session_id: str) -> bool:
        """Check if session has any active connections."""
        return session_id in self._connections and len(self._connections[session_id]) > 0

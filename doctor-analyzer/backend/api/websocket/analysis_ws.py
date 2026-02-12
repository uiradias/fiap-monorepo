"""WebSocket endpoint for real-time analysis streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from infrastructure.websocket.connection_manager import ConnectionManager
from domain.session import SessionStore
from api.dependencies import get_connection_manager, get_session_store

router = APIRouter()


@router.websocket("/ws/analysis/{session_id}")
async def analysis_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time analysis streaming.

    Client connects with session_id and receives:
    - status_update: Analysis pipeline status changes
    - emotion_update: Real-time emotion detections with timestamps
    - transcription_update: Transcription segments as processed
    - complete: Final aggregated results
    - error: Error messages

    Client can send:
    - {"action": "get_status"}: Request current status
    """
    ws_manager = get_connection_manager()
    session_store = get_session_store()

    await ws_manager.connect(websocket, session_id)

    try:
        # Send initial status
        session = await session_store.get(session_id)
        if session:
            await websocket.send_json({
                "type": "status_update",
                "status": session.status.value,
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Session {session_id} not found",
            })
            return

        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_json()
                action = data.get("action")

                if action == "get_status":
                    session = await session_store.get(session_id)
                    if session:
                        await websocket.send_json({
                            "type": "status_update",
                            "status": session.status.value,
                        })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

            except ValueError:
                # Invalid JSON received
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message",
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)

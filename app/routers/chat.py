from __future__ import annotations

import logging
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.telemetry import add_log
from services.ai_agent import stream_ai_response

logger = logging.getLogger(__name__)
router = APIRouter()

_ACTIVE_CONNECTIONS: dict[str, list[WebSocket]] = {}
LIVE_CHAT_OVERRIDE = False


@router.post("/chat/override")
async def toggle_override(override: bool):
    global LIVE_CHAT_OVERRIDE
    LIVE_CHAT_OVERRIDE = override
    add_log("System", "pink", f"Live Chat Override toggled {'ON' if override else 'OFF'}")
    return {"status": "success", "override": LIVE_CHAT_OVERRIDE}


def _is_valid_key(api_key: str) -> bool:
    return api_key == os.getenv("SAAS_API_KEY", "demo-tenant-key-123")


@router.websocket("/ws/chat/{api_key}")
async def websocket_chat(websocket: WebSocket, api_key: str) -> None:
    if not _is_valid_key(api_key):
        await websocket.close(code=4403)
        logger.warning("WebSocket rejected for invalid API key: %s", api_key)
        return

    await websocket.accept()
    _ACTIVE_CONNECTIONS.setdefault(api_key, []).append(websocket)
    try:
        while True:
            user_message = await websocket.receive_text()
            if LIVE_CHAT_OVERRIDE:
                await websocket.send_text("Live Support Agent: How can I help you today?")
            else:
                async for chunk in stream_ai_response(user_message):
                    await websocket.send_text(chunk)
            await websocket.send_text("__END__")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for key: %s", api_key)
    finally:
        if websocket in _ACTIVE_CONNECTIONS.get(api_key, []):
            _ACTIVE_CONNECTIONS[api_key].remove(websocket)


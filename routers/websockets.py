# routers/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List
import json
from jose import jwt, JWTError
from dependencies import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["Real-Time Logic"])

class ConnectionManager:
    def __init__(self):
        # Maps booking_id to a list of connected sockets (User & Provider)
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_rooms:
            self.active_rooms[room_id].remove(websocket)
            if len(self.active_rooms[room_id]) == 0:
                del self.active_rooms[room_id] # Clean up empty rooms

    async def broadcast(self, room_id: str, message: dict, sender: WebSocket):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                if connection != sender:
                    await connection.send_text(json.dumps(message))

manager = ConnectionManager()

def verify_ws_token(token: str):
    """Manually verify token for WebSockets since Headers aren't easily supported."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return False
        return True
    except JWTError:
        return False

@router.websocket("/ws/{feature}/{booking_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    feature: str, 
    booking_id: str, 
    token: str = Query(None) # 🚨 SECURED: Require token in URL
):
    """
    Handles both Tracking and Video.
    feature: 'tracking' or 'video'
    """
    if not token or not verify_ws_token(token):
        await websocket.close(code=1008, reason="Unauthorized connection.")
        return

    await manager.connect(booking_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Forward data (GPS coords or Video Signals) to the other person
            await manager.broadcast(booking_id, json.loads(data), sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(booking_id, websocket)
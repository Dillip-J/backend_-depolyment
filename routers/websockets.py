# routers/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

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

    async def broadcast(self, room_id: str, message: dict, sender: WebSocket):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                if connection != sender:
                    await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws/{feature}/{booking_id}")
async def websocket_endpoint(websocket: WebSocket, feature: str, booking_id: str):
    """
    Handles both Tracking and Video.
    feature: 'tracking' or 'video'
    """
    await manager.connect(booking_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Forward data (GPS coords or Video Signals) to the other person
            await manager.broadcast(booking_id, json.loads(data), sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(booking_id, websocket)
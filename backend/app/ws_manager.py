import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self._client_connections: Dict[str, WebSocket] = {}
        self._frontend_connections: Set[WebSocket] = set()
        self._client_info: Dict[str, dict] = {}

    async def connect_client(self, websocket: WebSocket, client_id: str, info: dict = None):
        await websocket.accept()
        self._client_connections[client_id] = websocket
        if info:
            self._client_info[client_id] = info
        await self.broadcast_to_frontends({
            "type": "client_connected",
            "client_id": client_id,
            "info": info or {}
        })

    async def disconnect_client(self, client_id: str):
        self._client_connections.pop(client_id, None)
        self._client_info.pop(client_id, None)
        await self.broadcast_to_frontends({
            "type": "client_disconnected",
            "client_id": client_id
        })

    async def connect_frontend(self, websocket: WebSocket):
        await websocket.accept()
        self._frontend_connections.add(websocket)
        # Send current client list to newly connected frontend
        await websocket.send_json({
            "type": "client_list",
            "clients": [
                {"client_id": cid, "is_online": True, **info}
                for cid, info in self._client_info.items()
            ]
        })

    async def disconnect_frontend(self, websocket: WebSocket):
        self._frontend_connections.discard(websocket)

    async def send_to_client(self, client_id: str, message: dict) -> bool:
        ws = self._client_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception:
                await self.disconnect_client(client_id)
        return False

    async def broadcast_to_frontends(self, message: dict):
        disconnected = []
        for ws in self._frontend_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self._frontend_connections.discard(ws)

    async def broadcast_scan_result(self, scan_id: str, client_id: str, data: dict):
        await self.broadcast_to_frontends({
            "type": "scan_progress",
            "scan_id": scan_id,
            "client_id": client_id,
            "data": data
        })

    def get_online_clients(self) -> list:
        return [
            {"client_id": cid, **info}
            for cid, info in self._client_info.items()
        ]

    def is_client_online(self, client_id: str) -> bool:
        return client_id in self._client_connections

manager = ConnectionManager()

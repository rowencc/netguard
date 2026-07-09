"""
WebSocket Client

通过 WebSocket 连接到后端，接收扫描指令并上报结果
"""

import json
import asyncio
import ssl
import traceback
from typing import Callable, Optional


class WSClient:
    def __init__(self, ws_url: str, client_id: str, api_key: str):
        self.ws_url = ws_url
        self.client_id = client_id
        self.api_key = api_key
        self.ws = None
        self.connected = False
        self._on_scan_command: Optional[Callable] = None
    
    def set_scan_handler(self, handler: Callable):
        self._on_scan_command = handler
    
    async def connect(self):
        try:
            import websockets
        except ImportError:
            print("[WS] websockets library not installed. Run: pip install websockets")
            return False
        
        url = f"{self.ws_url}/ws/client/{self.client_id}"
        print(f"[WS] Connecting to {url}...")
        
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        try:
            if self.ws_url.startswith("wss://"):
                self.ws = await websockets.connect(url, ssl=ssl_ctx, ping_interval=30, ping_timeout=10)
            else:
                self.ws = await websockets.connect(url, ping_interval=30, ping_timeout=10)
            
            self.connected = True
            print(f"[WS] Connected as {self.client_id}")
            return True
        except Exception as e:
            print(f"[WS] Connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        self.connected = False
    
    async def send_json(self, data: dict):
        if self.ws and self.connected:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                print(f"[WS] Send error: {e}")
                self.connected = False
    
    async def send_heartbeat(self, device_count: int = 0, online_count: int = 0, version: str = "0.4.0"):
        await self.send_json({
            "type": "heartbeat",
            "device_count": device_count,
            "online_count": online_count,
            "version": version,
        })
    
    async def send_scan_result(self, scan_id: str, device: dict):
        await self.send_json({
            "type": "scan_result",
            "scan_id": scan_id,
            "device": device,
        })
    
    async def send_scan_complete(self, scan_id: str, device_count: int = 0, new_device_count: int = 0):
        await self.send_json({
            "type": "scan_complete",
            "scan_id": scan_id,
            "device_count": device_count,
            "new_device_count": new_device_count,
        })
    
    async def listen(self):
        if not self.ws or not self.connected:
            return
        
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "scan_command":
                        print(f"[WS] Received scan command: {data.get('scan_id')}")
                        if self._on_scan_command:
                            asyncio.create_task(self._on_scan_command(data))
                    
                    elif msg_type == "heartbeat_ack":
                        pass
                    
                except json.JSONDecodeError:
                    print(f"[WS] Invalid JSON: {message}")
        except Exception as e:
            print(f"[WS] Listen error: {e}")
        finally:
            self.connected = False
            print("[WS] Disconnected")

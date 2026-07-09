"""
NetGuard Client Agent

部署在桌面电脑或 ARM 硬件上，负责：
- 本地网络扫描
- 设备发现与识别
- 数据上报到云端服务器
- 心跳保活
- WebSocket 实时通信
"""

import sys
import os
import json
import time
import socket
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import ClientConfig
from scanner import LocalScanner
from reporter import ServerReporter
from ws_client import WSClient


class NetGuardClient:
    def __init__(self, config_path: str = None):
        self.config = ClientConfig(config_path)
        self.scanner = LocalScanner()
        self.reporter = ServerReporter(
            server_url=self.config.server_url,
            api_key=self.config.api_key,
            client_id=self.config.client_id
        )
        self.ws_client = WSClient(
            ws_url=self.config.ws_url,
            client_id=self.config.client_id,
            api_key=self.config.api_key,
        )
        self.ws_client.set_scan_handler(self._handle_ws_scan)
        
        self.running = False
        self._last_scan_devices = []
        self._ws_loop = None
        
    def start(self):
        print(f"[NetGuard Client] Starting...")
        print(f"  Client ID: {self.config.client_id}")
        print(f"  Server: {self.config.server_url}")
        print(f"  WebSocket: {self.config.ws_url}")
        print(f"  Scan Interval: {self.config.scan_interval}s")
        print(f"  Use WebSocket: {self.config.use_websocket}")
        
        self.running = True
        
        self._send_heartbeat()
        
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        scan_thread.start()
        
        if self.config.use_websocket:
            ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
            ws_thread.start()
        
        print("[NetGuard Client] Running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        print("\n[NetGuard Client] Stopping...")
        self.running = False
        if self._ws_loop:
            asyncio.run_coroutine_threadsafe(
                self.ws_client.disconnect(),
                self._ws_loop
            )
        print("[NetGuard Client] Stopped.")
    
    def _run_ws_loop(self):
        self._ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._ws_loop)
        self._ws_loop.run_until_complete(self._ws_connect_and_listen())
    
    async def _ws_connect_and_listen(self):
        while self.running:
            try:
                connected = await self.ws_client.connect()
                if connected:
                    await self.ws_client.listen()
                else:
                    print("[WS] Reconnecting in 5s...")
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"[WS] Error: {e}")
                await asyncio.sleep(5)
    
    async def _handle_ws_scan(self, command: dict):
        scan_id = command.get("scan_id")
        subnets = command.get("subnets", [])
        
        print(f"[WS Scan] Starting scan {scan_id}...")
        
        device_count = 0
        new_device_count = 0
        
        for device in self.scanner.scan_network_stream(subnets):
            device_count += 1
            await self.ws_client.send_scan_result(scan_id, device)
            print(f"[WS Scan] Found: {device['ip_address']} ({device['mac_address']})")
        
        await self.ws_client.send_scan_complete(scan_id, device_count, new_device_count)
        print(f"[WS Scan] Complete: {device_count} devices found")
    
    def _heartbeat_loop(self):
        while self.running:
            try:
                self._send_heartbeat()
                if self.ws_client.connected:
                    online_count = sum(1 for d in self._last_scan_devices if d.get("is_online"))
                    asyncio.run_coroutine_threadsafe(
                        self.ws_client.send_heartbeat(
                            device_count=len(self._last_scan_devices),
                            online_count=online_count,
                            version="0.4.0"
                        ),
                        self._ws_loop
                    ) if self._ws_loop else None
            except Exception as e:
                print(f"[Heartbeat Error] {e}")
            time.sleep(60)
    
    def _send_heartbeat(self):
        try:
            online_count = sum(1 for d in self._last_scan_devices if d.get("is_online"))
            self.reporter.send_heartbeat(
                hostname=socket.gethostname(),
                ip_address=self._get_local_ip(),
                platform=sys.platform,
                version="0.4.0",
                device_count=len(self._last_scan_devices),
                online_count=online_count
            )
        except Exception as e:
            print(f"[Heartbeat] Failed: {e}")
    
    def _scan_loop(self):
        while self.running:
            try:
                self._perform_scan()
            except Exception as e:
                print(f"[Scan Error] {e}")
            time.sleep(self.config.scan_interval)
    
    def _perform_scan(self):
        print(f"[Scan] Starting scan...")
        
        devices = self.scanner.scan_network()
        
        for device in devices:
            device["is_online"] = self.scanner.ping_host(device["ip_address"])
        
        self._last_scan_devices = devices
        
        print(f"[Scan] Found {len(devices)} devices, {sum(1 for d in devices if d['is_online'])} online")
        
        if devices:
            try:
                result = self.reporter.report_devices(devices)
                print(f"[Report] Sent {len(devices)} devices: {result}")
            except Exception as e:
                print(f"[Report] Failed: {e}")
    
    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NetGuard Client Agent")
    parser.add_argument("-c", "--config", help="Config file path")
    parser.add_argument("--server", help="Server URL")
    parser.add_argument("--scan-once", action="store_true", help="Scan once and exit")
    parser.add_argument("--no-ws", action="store_true", help="Disable WebSocket")
    args = parser.parse_args()
    
    client = NetGuardClient(args.config)
    
    if args.server:
        client.config.server_url = args.server
        client.ws_client.ws_url = client.config.ws_url
    
    if args.no_ws:
        client.config.use_websocket = False
    
    if args.scan_once:
        client._perform_scan()
        return
    
    client.start()


if __name__ == "__main__":
    main()

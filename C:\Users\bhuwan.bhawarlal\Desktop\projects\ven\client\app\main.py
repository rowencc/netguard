"""
NetGuard Client Agent

部署在桌面电脑或 ARM 硬件上，负责：
- 本地网络扫描
- 设备发现与识别
- 数据上报到云端服务器
- 心跳保活
"""

import sys
import os
import json
import time
import socket
import hashlib
import platform
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config import ClientConfig
from scanner import LocalScanner
from reporter import ServerReporter


class NetGuardClient:
    def __init__(self, config_path: str = None):
        self.config = ClientConfig(config_path)
        self.scanner = LocalScanner()
        self.reporter = ServerReporter(
            server_url=self.config.server_url,
            api_key=self.config.api_key,
            client_id=self.config.client_id
        )
        self.running = False
        self._last_scan_devices = []
        
    def start(self):
        print(f"[NetGuard Client] Starting...")
        print(f"  Client ID: {self.config.client_id}")
        print(f"  Server: {self.config.server_url}")
        print(f"  Scan Interval: {self.config.scan_interval}s")
        
        self.running = True
        
        self._send_heartbeat()
        
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        scan_thread.start()
        
        print("[NetGuard Client] Running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        print("\n[NetGuard Client] Stopping...")
        self.running = False
        print("[NetGuard Client] Stopped.")
    
    def _heartbeat_loop(self):
        while self.running:
            try:
                self._send_heartbeat()
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
                version="0.2.1",
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
    args = parser.parse_args()
    
    client = NetGuardClient(args.config)
    
    if args.server:
        client.config.server_url = args.server
    
    if args.scan_once:
        client._perform_scan()
        return
    
    client.start()


if __name__ == "__main__":
    main()

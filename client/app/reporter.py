"""
Server Reporter

负责向云端服务器上报数据
"""

import json
import urllib.request
import ssl
from typing import Dict, List, Optional
from datetime import datetime


class ServerReporter:
    def __init__(self, server_url: str, api_key: str, client_id: str):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id
        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
    
    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.server_url}{path}"
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        
        body = json.dumps(data).encode("utf-8") if data else None
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            response = urllib.request.urlopen(req, timeout=10, context=self.ctx)
            return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.read() else ""
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"Request failed: {e}")
    
    def send_heartbeat(
        self,
        hostname: str,
        ip_address: str,
        platform: str,
        version: str,
        device_count: int = 0,
        online_count: int = 0
    ) -> dict:
        return self._request("POST", "/api/sync/heartbeat", {
            "client_id": self.client_id,
            "hostname": hostname,
            "ip_address": ip_address,
            "platform": platform,
            "version": version,
            "device_count": device_count,
            "online_count": online_count,
        })
    
    def report_devices(self, devices: List[Dict]) -> dict:
        report = []
        for dev in devices:
            report.append({
                "client_id": self.client_id,
                "ip_address": dev.get("ip_address", ""),
                "mac_address": dev.get("mac_address", ""),
                "hostname": dev.get("hostname", ""),
                "vendor": dev.get("vendor", ""),
                "device_type": dev.get("device_type", ""),
                "risk_level": dev.get("risk_level", "LOW"),
                "is_online": dev.get("is_online", False),
                "ssid": dev.get("ssid", ""),
                "open_ports": dev.get("open_ports", {}),
                "os_info": dev.get("os_info", ""),
            })
        
        return self._request("POST", "/api/sync/report-devices", report)
    
    def get_commands(self) -> dict:
        return self._request("GET", f"/api/sync/commands/{self.client_id}")
    
    def test_connection(self) -> bool:
        try:
            result = self._request("GET", "/api/health")
            return result.get("status") == "healthy"
        except Exception:
            return False

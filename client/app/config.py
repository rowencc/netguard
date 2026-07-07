"""
Client Configuration
"""

import os
import json
import socket
from pathlib import Path


class ClientConfig:
    def __init__(self, config_path: str = None):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_file = config_path or str(self.config_dir / "client.json")
        
        self.server_url = os.getenv("NETGUARD_SERVER_URL", "http://localhost:8089")
        self.api_key = os.getenv("NETGUARD_API_KEY", "netguard-sync-key-2024")
        self.client_id = os.getenv("NETGUARD_CLIENT_ID", self._generate_client_id())
        
        self.scan_interval = int(os.getenv("NETGUARD_SCAN_INTERVAL", "300"))
        self.scan_subnets = os.getenv("NETGUARD_SCAN_SUBNETS", "").split(",") if os.getenv("NETGUARD_SCAN_SUBNETS") else []
        self.use_websocket = os.getenv("NETGUARD_USE_WEBSOCKET", "true").lower() == "true"
        
        self._load_config()
    
    def _generate_client_id(self) -> str:
        hostname = socket.gethostname()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            mac = hex(hash(s.getsockname()[0]))[2:10]
            s.close()
        except Exception:
            mac = "00000000"
        return f"client-{hostname}-{mac}"
    
    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                self.server_url = data.get("server_url", self.server_url)
                self.api_key = data.get("api_key", self.api_key)
                self.client_id = data.get("client_id", self.client_id)
                self.scan_interval = data.get("scan_interval", self.scan_interval)
                self.scan_subnets = data.get("scan_subnets", self.scan_subnets)
                self.use_websocket = data.get("use_websocket", self.use_websocket)
            except Exception:
                pass
    
    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump({
                "server_url": self.server_url,
                "api_key": self.api_key,
                "client_id": self.client_id,
                "scan_interval": self.scan_interval,
                "scan_subnets": self.scan_subnets,
                "use_websocket": self.use_websocket,
            }, f, indent=2)
    
    @property
    def ws_url(self) -> str:
        url = self.server_url.rstrip("/")
        if url.startswith("https://"):
            return "wss://" + url[8:]
        elif url.startswith("http://"):
            return "ws://" + url[5:]
        else:
            return "ws://" + url

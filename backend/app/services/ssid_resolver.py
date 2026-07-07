"""
WiFi SSID Resolver

Discovers WiFi SSID information through multiple methods:
1. Router DHCP/ARP table correlation
2. WiFi scan (airport command on macOS, nmcli on Linux)
3. SNMP query to router
4. UPnP/SSDP device discovery
5. HTTP API to router management interface

Note: SSID is the WiFi network name, not a device identifier.
A device's SSID is determined by which WiFi network it's connected to.
"""

import subprocess
import json
import re
from typing import Dict, Optional, List
from pathlib import Path
from app.services.platform_compat import (
    get_wifi_ssid, scan_wifi_networks, is_macos, get_default_interface
)


class SSIDResolver:
    def __init__(self):
        self._wifi_networks: Dict[str, Dict] = {}
        self._device_ssid_cache: Dict[str, str] = {}

    def scan_wifi_networks(self) -> List[Dict]:
        return scan_wifi_networks()

    def get_current_wifi(self) -> Dict:
        ssid = get_wifi_ssid()
        if ssid:
            return {"ssid": ssid, "bssid": ""}
        return {}

    def get_ssid_for_device(self, mac_address: str, ip_address: str) -> Optional[str]:
        if mac_address in self._device_ssid_cache:
            return self._device_ssid_cache[mac_address]

        ssid = self._try_router_client_list(mac_address, ip_address)
        if ssid:
            self._device_ssid_cache[mac_address] = ssid
            return ssid

        ssid = self._try_dhcp_lease(mac_address, ip_address)
        if ssid:
            self._device_ssid_cache[mac_address] = ssid
            return ssid

        ssid = self._try_arp_correlation(ip_address)
        if ssid:
            self._device_ssid_cache[mac_address] = ssid
            return ssid

        return None

    def _try_dhcp_lease(self, mac_address: str, ip_address: str) -> Optional[str]:
        current_wifi = self.get_current_wifi()
        if not current_wifi.get("ssid"):
            return None

        try:
            if is_macos():
                output = subprocess.check_output(
                    ["arp", "-a", ip_address],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
            else:
                output = subprocess.check_output(
                    ["arp", "-an"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
            if ip_address in output and mac_address.lower() in output.lower():
                return current_wifi["ssid"]
        except Exception:
            pass

        return None

    def _try_router_client_list(self, mac_address: str, ip_address: str) -> Optional[str]:
        router_ips = ["192.168.100.1", "192.168.1.1", "192.168.0.1"]
        mac_normalized = mac_address.upper().replace("-", ":")

        for router_ip in router_ips:
            try:
                import urllib.request
                import ssl

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                for path in ["/cgi-bin/luci/api/clients", "/api/clients", "/client-list", "/dhcp"]:
                    try:
                        url = f"http://{router_ip}{path}"
                        req = urllib.request.Request(url, method='GET')
                        req.add_header('User-Agent', 'NetGuard/1.0')
                        response = urllib.request.urlopen(req, timeout=3, context=ctx)
                        data = json.loads(response.read().decode('utf-8'))

                        if isinstance(data, list):
                            for client in data:
                                client_mac = client.get("mac", "").upper().replace("-", ":")
                                if mac_normalized == client_mac:
                                    return client.get("ssid") or client.get("network") or client.get("hostname")
                        elif isinstance(data, dict):
                            for key, client in data.items():
                                if isinstance(client, dict):
                                    client_mac = client.get("mac", "").upper().replace("-", ":")
                                    if mac_normalized == client_mac:
                                        return client.get("ssid") or client.get("network") or client.get("hostname")
                    except Exception:
                        continue
            except Exception:
                continue

        return None

    def get_all_wifi_clients(self) -> List[Dict]:
        clients = []
        router_ips = ["192.168.100.1", "192.168.1.1", "192.168.0.1"]

        for router_ip in router_ips:
            try:
                import urllib.request
                import ssl

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                for path in ["/cgi-bin/luci/api/clients", "/api/clients", "/client-list", "/dhcp"]:
                    try:
                        url = f"http://{router_ip}{path}"
                        req = urllib.request.Request(url, method='GET')
                        req.add_header('User-Agent', 'NetGuard/1.0')
                        response = urllib.request.urlopen(req, timeout=3, context=ctx)
                        data = json.loads(response.read().decode('utf-8'))

                        if isinstance(data, list):
                            for client in data:
                                clients.append({
                                    "mac": client.get("mac", ""),
                                    "ip": client.get("ip", ""),
                                    "ssid": client.get("ssid", ""),
                                    "hostname": client.get("hostname", ""),
                                    "signal": client.get("signal", 0),
                                })
                        elif isinstance(data, dict):
                            for key, client in data.items():
                                if isinstance(client, dict):
                                    clients.append({
                                        "mac": client.get("mac", ""),
                                        "ip": client.get("ip", ""),
                                        "ssid": client.get("ssid", ""),
                                        "hostname": client.get("hostname", ""),
                                        "signal": client.get("signal", 0),
                                    })
                        if clients:
                            return clients
                    except Exception:
                        continue
            except Exception:
                continue

        return clients

    def _try_arp_correlation(self, ip_address: str) -> Optional[str]:
        current_wifi = self.get_current_wifi()
        if not current_wifi.get("ssid"):
            return None

        try:
            if is_macos():
                output = subprocess.check_output(
                    ["arp", "-a", "-i", "en0"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
            else:
                output = subprocess.check_output(
                    ["arp", "-an"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5
                )
            for line in output.splitlines():
                if ip_address in line:
                    return current_wifi["ssid"]
        except Exception:
            pass

        return None

    def get_network_info(self) -> Dict:
        current = self.get_current_wifi()
        networks = self.scan_wifi_networks()

        return {
            "current_ssid": current.get("ssid", ""),
            "current_bssid": current.get("bssid", ""),
            "available_networks": networks,
            "network_count": len(networks),
        }


def add_ssid_column():
    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            database='netguard'
        )
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM devices LIKE 'ssid'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE devices ADD COLUMN ssid VARCHAR(100) AFTER hostname_source")
            conn.commit()
            print("Column 'ssid' added successfully")
        else:
            print("Column 'ssid' already exists")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    add_ssid_column()
    resolver = SSIDResolver()
    print(json.dumps(resolver.get_network_info(), indent=2, ensure_ascii=False))

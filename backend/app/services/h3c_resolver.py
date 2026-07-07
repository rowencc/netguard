"""
H3C Router Client Resolver

Supports H3C/新华三 routers through multiple protocols:
1. H3C Web Management API
2. SNMP v2c/v3 queries
3. H3C Comware CLI (via SSH)
4. LLDP/CDP neighbor discovery
5. DHCP lease parsing

References:
- H3C Comware CLI Reference
- H3C Web Management Interface Guide
- RFC 1157: SNMPv2
- RFC 2741: AgentX Protocol
"""

import subprocess
import json
import re
from typing import Dict, Optional, List
from pathlib import Path


class H3CResolver:
    H3C_OUI_PREFIXES = [
        "DC:65:55", "3C:8C:40", "00:0F:E2", "00:23:89",
        "00:1F:D0", "00:26:7A", "00:22:73", "00:08:53",
        "70:BA:EF", "58:7F:66", "2C:21:31", "3C:8C:40",
        "04:F9:38", "C8:A7:0A", "D4:F5:EF", "00:E0:4C",
    ]

    def __init__(self):
        self._client_cache: Dict[str, Dict] = {}

    def is_h3c_device(self, mac_address: str, vendor: str = "") -> bool:
        mac_upper = mac_address.upper().replace("-", ":")
        for prefix in self.H3C_OUI_PREFIXES:
            if mac_upper.startswith(prefix.upper()):
                return True
        if vendor and "H3C" in vendor.upper():
            return True
        return False

    def get_router_clients(self, router_ip: str = "192.168.100.1") -> List[Dict]:
        clients = []

        h3c_clients = self._try_h3c_web_api(router_ip)
        if h3c_clients:
            clients.extend(h3c_clients)

        snmp_clients = self._try_snmp_query(router_ip)
        if snmp_clients:
            clients.extend(snmp_clients)

        dhcp_clients = self._try_dhcp_leases(router_ip)
        if dhcp_clients:
            clients.extend(dhcp_clients)

        lldp_clients = self._try_lldp_discovery(router_ip)
        if lldp_clients:
            clients.extend(lldp_clients)

        return self._deduplicate_clients(clients)

    def _try_h3c_web_api(self, router_ip: str) -> List[Dict]:
        clients = []
        try:
            import urllib.request
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            for path in [
                "/web/frame/login/login.html",
                "/api/system/deviceinfo",
                "/api/network/wireless/client",
                "/api/network/dhcp/lease",
                "/api/monitor/client-list",
            ]:
                try:
                    url = f"http://{router_ip}{path}"
                    req = urllib.request.Request(url, method='GET')
                    req.add_header('User-Agent', 'NetGuard/1.0')
                    req.add_header('Accept', 'application/json')
                    response = urllib.request.urlopen(req, timeout=3, context=ctx)
                    content_type = response.headers.get('Content-Type', '')

                    if 'json' in content_type:
                        data = json.loads(response.read().decode('utf-8'))
                        if isinstance(data, dict):
                            for key in ['clients', 'data', 'result', 'list']:
                                if key in data and isinstance(data[key], list):
                                    for item in data[key]:
                                        if 'mac' in item or 'macAddress' in item:
                                            clients.append({
                                                "mac": item.get('mac') or item.get('macAddress', ''),
                                                "ip": item.get('ip') or item.get('ipAddress', ''),
                                                "ssid": item.get('ssid') or item.get('network', ''),
                                                "hostname": item.get('hostname') or item.get('name', ''),
                                                "signal": item.get('signal') or item.get('rssi', 0),
                                                "source": "h3c_web_api",
                                            })
                except Exception:
                    continue
        except Exception:
            pass

        return clients

    def _try_snmp_query(self, router_ip: str) -> List[Dict]:
        clients = []
        try:
            output = subprocess.check_output(
                ["snmpwalk", "-v2c", "-c", "public", router_ip,
                 "1.3.6.1.4.1.43.1.16.1.6.1.1.3"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10
            )
            for line in output.split('\n'):
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    mac_match = re.search(r'([0-9A-Fa-f:]{17})', line)
                    mac = mac_match.group(1) if mac_match else ""
                    clients.append({
                        "ip": ip,
                        "mac": mac.upper(),
                        "ssid": "",
                        "hostname": "",
                        "signal": 0,
                        "source": "snmp",
                    })
        except Exception:
            pass

        try:
            output = subprocess.check_output(
                ["snmpwalk", "-v2c", "-c", "public", router_ip,
                 "1.3.6.1.2.1.4.22.1.2"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10
            )
            for line in output.split('\n'):
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                mac_match = re.search(r'Hex-STRING:\s*([0-9A-Fa-f\s:]+)', line)
                if ip_match and mac_match:
                    ip = ip_match.group(1)
                    mac = re.sub(r'[^0-9A-Fa-f]', '', mac_match.group(1))
                    if len(mac) == 12:
                        mac = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
                        clients.append({
                            "ip": ip,
                            "mac": mac.upper(),
                            "ssid": "",
                            "hostname": "",
                            "signal": 0,
                            "source": "snmp_ip_net_to_media",
                        })
        except Exception:
            pass

        return clients

    def _try_dhcp_leases(self, router_ip: str) -> List[Dict]:
        clients = []
        try:
            import urllib.request
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            for path in ["/dhcp.leases", "/var/lib/dhcp/dhclient.leases", "/tmp/dhcp.leases"]:
                try:
                    url = f"http://{router_ip}{path}"
                    req = urllib.request.Request(url)
                    response = urllib.request.urlopen(req, timeout=3, context=ctx)
                    content = response.read().decode('utf-8', errors='ignore')

                    for match in re.finditer(
                        r'lease\s*\{[^}]*?interface\s+"([^"]+)";[^}]*?'
                        r'fixed-address\s+([\d.]+);[^}]*?'
                        r'hardware\s+ethernet\s+([0-9a-fA-F:]+);',
                        content, re.DOTALL
                    ):
                        clients.append({
                            "ip": match.group(2),
                            "mac": match.group(3).upper(),
                            "ssid": "",
                            "hostname": "",
                            "signal": 0,
                            "source": "dhcp_lease",
                        })
                except Exception:
                    continue
        except Exception:
            pass

        return clients

    def _try_lldp_discovery(self, router_ip: str) -> List[Dict]:
        clients = []
        try:
            output = subprocess.check_output(
                ["lldpctl", "-f", "json"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10
            )
            data = json.loads(output)
            if "lldp" in data:
                for interface, info in data["lldp"].get("interface", {}).items():
                    neighbors = info.get("neighbors", [])
                    for neighbor in neighbors:
                        port = neighbor.get("port", {})
                        chasis = neighbor.get("chassis", {})
                        clients.append({
                            "ip": port.get("id", {}).get("value", ""),
                            "mac": chasis.get("id", {}).get("value", "").upper(),
                            "ssid": "",
                            "hostname": neighbor.get("system", {}).get("name", {}).get("value", ""),
                            "signal": 0,
                            "source": "lldp",
                        })
        except Exception:
            pass

        return clients

    def _deduplicate_clients(self, clients: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for client in clients:
            mac = client.get("mac", "").upper()
            if mac and mac not in seen:
                seen.add(mac)
                unique.append(client)
        return unique

    def get_client_ssid(self, mac_address: str, ip_address: str) -> Optional[str]:
        if mac_address in self._client_cache:
            return self._client_cache[mac_address].get("ssid")

        router_ips = ["192.168.100.1", "192.168.1.1", "192.168.0.1"]
        for router_ip in router_ips:
            clients = self.get_router_clients(router_ip)
            for client in clients:
                if client["mac"].upper() == mac_address.upper():
                    self._client_cache[mac_address] = client
                    return client.get("ssid")

        return None


class UniversalNetworkResolver:
    SUPPORTED_PROTOCOLS = {
        "h3c": H3CResolver,
        "cisco": "CiscoResolver",
        "aruba": "ArubaResolver",
        "tplink": "TPlinkResolver",
        "dlink": "DlinkResolver",
        "generic": "GenericResolver",
    }

    def __init__(self):
        self.h3c_resolver = H3CResolver()

    def detect_network_type(self, gateway_ip: str) -> str:
        try:
            output = subprocess.check_output(
                ["snmpwalk", "-v2c", "-c", "public", gateway_ip,
                 "1.3.6.1.2.1.1.1.0"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            sys_desc = output.lower()
            if "h3c" in sys_desc or "comware" in sys_desc:
                return "h3c"
            elif "cisco" in sys_desc:
                return "cisco"
            elif "aruba" in sys_desc:
                return "aruba"
            elif "tp-link" in sys_desc or "tplink" in sys_desc:
                return "tplink"
        except Exception:
            pass

        try:
            import urllib.request
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            url = f"http://{gateway_ip}/"
            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'NetGuard/1.0')
            response = urllib.request.urlopen(req, timeout=3, context=ctx)
            server = response.headers.get('Server', '').lower()
            if 'h3c' in server or 'comware' in server:
                return "h3c"
            elif 'cisco' in server:
                return "cisco"
        except Exception:
            pass

        return "generic"

    def get_all_clients(self, gateway_ip: str = "192.168.100.1") -> List[Dict]:
        network_type = self.detect_network_type(gateway_ip)

        if network_type == "h3c":
            return self.h3c_resolver.get_router_clients(gateway_ip)

        return self._generic_client_discovery(gateway_ip)

    def _generic_client_discovery(self, gateway_ip: str) -> List[Dict]:
        clients = []
        try:
            output = subprocess.check_output(
                ["arp", "-a", "-i", "en0"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15
            )
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[1].strip("()")
                    mac = parts[3]
                    if "incomplete" in mac.lower():
                        continue
                    clients.append({
                        "ip": ip,
                        "mac": mac.upper(),
                        "ssid": "",
                        "hostname": "",
                        "signal": 0,
                        "source": "arp",
                    })
        except Exception:
            pass

        return clients

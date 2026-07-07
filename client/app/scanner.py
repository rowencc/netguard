"""
Local Network Scanner

本地网络扫描器，用于发现网络设备
支持 macOS 和 Linux
"""

import subprocess
import sys
import socket
from typing import List, Dict, Generator


class LocalScanner:
    def __init__(self):
        self.platform = sys.platform
    
    def scan_network(self, subnets: List[str] = None) -> List[Dict]:
        devices = []
        seen = set()
        
        arp_devices = self._arp_scan()
        for d in arp_devices:
            if d["ip_address"] not in seen:
                seen.add(d["ip_address"])
                devices.append(d)
        
        return devices
    
    def scan_network_stream(self, subnets: List[str] = None) -> Generator[Dict, None, None]:
        seen = set()
        
        arp_devices = self._arp_scan()
        for d in arp_devices:
            if d["ip_address"] not in seen:
                seen.add(d["ip_address"])
                d["is_online"] = self.ping_host(d["ip_address"])
                yield d
    
    def _arp_scan(self) -> List[Dict]:
        devices = []
        
        if self.platform == "darwin":
            for iface in ["en0", "en1"]:
                try:
                    proc = subprocess.Popen(
                        ["arp", "-a", "-i", iface],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                    output, _ = proc.communicate(timeout=10)
                    for line in output.splitlines():
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[1].strip("()")
                            mac = parts[3]
                            if "incomplete" in mac.lower() or mac == "ff:ff:ff:ff:ff:ff":
                                continue
                            devices.append({
                                "ip_address": ip,
                                "mac_address": mac.upper(),
                                "hostname": self._reverse_dns(ip),
                                "vendor": "",
                                "device_type": ""
                            })
                except Exception:
                    continue
        else:
            try:
                result = subprocess.run(
                    ["arp", "-an"],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 4:
                        ip = parts[1].strip("()")
                        mac = parts[3]
                        if "incomplete" in mac.lower() or mac == "ff:ff:ff:ff:ff:ff":
                            continue
                        devices.append({
                            "ip_address": ip,
                            "mac_address": mac.upper(),
                            "hostname": self._reverse_dns(ip),
                            "vendor": "",
                            "device_type": ""
                        })
            except Exception:
                pass
        
        return devices
    
    def ping_host(self, ip: str, timeout: int = 2) -> bool:
        try:
            if self.platform == "darwin":
                result = subprocess.run(
                    ["ping", "-c", "1", "-t", str(timeout), ip],
                    capture_output=True, timeout=timeout + 1
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", str(timeout), ip],
                    capture_output=True, timeout=timeout + 1
                )
            return result.returncode == 0
        except Exception:
            return False
    
    def _reverse_dns(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""
    
    def deep_scan(self, ip: str) -> Dict:
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(hosts=ip, arguments="-sV --open --host-timeout 10s")
            
            if ip not in nm.all_hosts():
                return {}
            
            host_data = nm[ip]
            open_ports = {}
            if "tcp" in host_data:
                for port, info in host_data["tcp"].items():
                    open_ports[port] = info.get("name", "") + "/" + info.get("product", "")
            
            return {
                "ip_address": ip,
                "mac_address": host_data.get("addresses", {}).get("mac", ""),
                "hostname": host_data.hostname(),
                "os_matches": host_data.get("osmatch", []),
                "open_ports": open_ports,
                "vendor": host_data.get("vendor", {}).get("mac", "")
            }
        except Exception:
            return {}

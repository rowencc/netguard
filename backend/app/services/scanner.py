import subprocess
import socket
import nmap
from typing import List, Dict, Optional
from app.config import config
from app.services.vendor_lookup import VendorLookup
from app.services.hostname_resolver import HostnameResolver
from app.services.platform_compat import get_arp_table, get_all_interfaces, is_linux


class NetworkScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.config = config["scanner"]
        self.vendor_lookup = VendorLookup()
        self.hostname_resolver = HostnameResolver()

    @staticmethod
    def normalize_mac(mac: str) -> str:
        parts = mac.replace("-", ":").split(":")
        return ":".join(p.zfill(2).upper() for p in parts)

    def scan_network(self, network: Optional[str] = None) -> List[Dict]:
        arp_devices = self._arp_table(network)
        devices = []
        for d in arp_devices:
            hostname_result = self.hostname_resolver.resolve(d["ip_address"])
            vendor = self.vendor_lookup.lookup(d["mac_address"])
            device_type = self.vendor_lookup.get_device_type_from_mac(d["mac_address"])
            devices.append({
                "ip_address": d["ip_address"],
                "mac_address": d["mac_address"],
                "hostname": hostname_result.get("hostname", ""),
                "hostname_source": hostname_result.get("source", ""),
                "vendor": vendor,
                "device_type_hint": device_type
            })
        return devices

    def _arp_table(self, network: Optional[str] = None) -> List[Dict]:
        devices = []
        seen = set()

        # If a specific network is provided, scan it
        if network:
            try:
                from scapy.all import ARP, Ether, srp
                arp_results = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=network)
                answered, _ = srp(arp_results, timeout=2, verbose=False)
                for sent, received in answered:
                    ip = received.psrc
                    mac = self.normalize_mac(received.hwsrc)
                    if ip not in seen:
                        seen.add(ip)
                        devices.append({"ip_address": ip, "mac_address": mac})
            except Exception:
                pass
            
            if devices:
                return devices

        # Default: scan hardcoded subnets
        try:
            from scapy.all import ARP, Ether, srp
            arp_results = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.100.0/24")
            answered, _ = srp(arp_results, timeout=2, verbose=False)
            for sent, received in answered:
                ip = received.psrc
                mac = self.normalize_mac(received.hwsrc)
                if ip not in seen:
                    seen.add(ip)
                    devices.append({"ip_address": ip, "mac_address": mac})
        except Exception:
            pass

        try:
            from scapy.all import ARP, Ether, srp
            arp_results = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.101.0/24")
            answered, _ = srp(arp_results, timeout=2, verbose=False)
            for sent, received in answered:
                ip = received.psrc
                mac = self.normalize_mac(received.hwsrc)
                if ip not in seen:
                    seen.add(ip)
                    devices.append({"ip_address": ip, "mac_address": mac})
        except Exception:
            pass

        if devices:
            return devices

        arp_table = get_arp_table()
        for entry in arp_table:
            ip = entry["ip_address"]
            mac = self.normalize_mac(entry["mac_address"])
            if ip not in seen:
                seen.add(ip)
                devices.append({"ip_address": ip, "mac_address": mac})

        return devices

    def _reverse_dns(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def deep_scan(self, ip: str) -> Dict:
        self.nm.scan(hosts=ip, arguments="-sV --open --host-timeout 10s")
        if ip not in self.nm.all_hosts():
            return {}
        host_data = self.nm[ip]
        open_ports = {}
        if "tcp" in host_data:
            for port, info in host_data["tcp"].items():
                open_ports[port] = info.get("name", "") + "/" + info.get("product", "")
        raw_mac = host_data.get("addresses", {}).get("mac", "")

        hostname = host_data.hostname()
        if not hostname:
            hostname_result = self.hostname_resolver.resolve(ip)
            hostname = hostname_result.get("hostname", "")

        return {
            "ip_address": ip,
            "mac_address": self.normalize_mac(raw_mac) if raw_mac else "",
            "hostname": hostname,
            "os_matches": host_data.get("osmatch", []),
            "open_ports": open_ports,
            "vendor": host_data.get("vendor", {}).get("mac", "")
        }

    def quick_port_scan(self, ip: str) -> Dict:
        self.nm.scan(hosts=ip, arguments="-F --host-timeout 5s")
        if ip not in self.nm.all_hosts():
            return {}
        host_data = self.nm[ip]
        open_ports = {}
        if "tcp" in host_data:
            for port, info in host_data["tcp"].items():
                open_ports[port] = info.get("name", "")
        return {
            "open_ports": open_ports,
            "vendor": host_data.get("vendor", {}).get("mac", "")
        }

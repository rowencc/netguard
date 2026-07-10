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
        # Step 1: Ping sweep to populate ARP table
        self._ping_sweep(network)
        
        arp_devices = self._arp_table(network)
        devices = []
        for d in arp_devices:
            # Skip slow hostname resolution for speed
            vendor = self.vendor_lookup.lookup(d["mac_address"])
            device_type = self.vendor_lookup.get_device_type_from_mac(d["mac_address"])
            devices.append({
                "ip_address": d["ip_address"],
                "mac_address": d["mac_address"],
                "hostname": "",
                "hostname_source": "",
                "vendor": vendor,
                "device_type_hint": device_type
            })
        return devices

    def _ping_sweep(self, network: Optional[str] = None):
        """Ping sweep to populate ARP table before reading it"""
        from app.services.platform_compat import get_network_info
        import concurrent.futures
        
        # Determine which subnets to scan
        subnets = []
        if network:
            subnets = [network]
        else:
            # Only scan the local subnet for speed
            try:
                info = get_network_info()
                local_ip = info.get("local_ip", "")
                if local_ip and local_ip != "127.0.0.1":
                    parts = local_ip.split(".")
                    if len(parts) == 4:
                        local_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                        subnets.append(local_subnet)
            except Exception:
                pass
            # Fallback to common subnets
            if not subnets:
                subnets = ["192.168.103.0/24"]
        
        def ping_host(ip):
            try:
                subprocess.run(
                    ["ping", "-c", "1", "-W", "0.2", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=0.5
                )
            except Exception:
                pass
        
        # Generate all IPs to ping
        all_ips = []
        for subnet in subnets:
            parts = subnet.replace("/24", "").split(".")
            if len(parts) == 4:
                prefix = f"{parts[0]}.{parts[1]}.{parts[2]}"
                for i in range(1, 255):
                    all_ips.append(f"{prefix}.{i}")
        
        # Ping in parallel (100 concurrent for speed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(ping_host, all_ips)

    def _arp_table(self, network: Optional[str] = None) -> List[Dict]:
        devices = []
        seen = set()

        # Skip scapy (requires root) - use system ARP table directly
        # The ping sweep has already populated the ARP table
        
        arp_table = get_arp_table()
        for entry in arp_table:
            ip = entry["ip_address"]
            mac = self.normalize_mac(entry["mac_address"])
            if ip not in seen and not ip.startswith("127."):
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

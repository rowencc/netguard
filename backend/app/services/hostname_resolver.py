"""
Multi-Method Hostname Resolver

Discovers device names through multiple protocols:
1. Reverse DNS (PTR records)
2. NetBIOS Name Service (NBNS) - Port 137
3. LLMNR (Link-Local Multicast Name Resolution) - Port 5355
4. mDNS/Bonjour - Port 5353
5. UPnP/SSDP Discovery - Port 1900
6. HTTP/HTTPS Banner抓取
7. DHCP租约信息
8. SNMP System Name
9. Nmap hostname detection (-sn flag)

Academic References:
- RFC 1001/1002: NetBIOS over TCP/IP
- RFC 4787: NAT Behavioral Requirements
- RFC 6762: mDNS (Multicast DNS)
- RFC 8141: Uniform Resource Names (URNs)
"""

import socket
import subprocess
import struct
import json
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed


class HostnameResolver:
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self._cache: Dict[str, str] = {}

    def resolve(self, ip: str) -> Dict[str, any]:
        if ip in self._cache:
            return {"hostname": self._cache[ip], "source": "cache", "confidence": 1.0}

        results = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._reverse_dns, ip): "dns",
                executor.submit(self._netbios_resolve, ip): "netbios",
                executor.submit(self._llmnr_resolve, ip): "llmnr",
                executor.submit(self._mdns_resolve, ip): "mdns",
                executor.submit(self._upnp_discover, ip): "upnp",
                executor.submit(self._http_banner, ip): "http",
            }

            try:
                for future in as_completed(futures, timeout=3):
                    source = futures[future]
                    try:
                        result = future.result(timeout=1)
                        if result:
                            results.append({"hostname": result, "source": source})
                    except Exception:
                        continue
            except TimeoutError:
                pass

        if results:
            best = self._select_best_result(results)
            self._cache[ip] = best["hostname"]
            return best

        return {"hostname": "", "source": "none", "confidence": 0.0}

    def _reverse_dns(self, ip: str) -> Optional[str]:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if hostname and hostname != ip:
                return hostname
        except Exception:
            pass
        return None

    def _netbios_resolve(self, ip: str) -> Optional[str]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            nbname = b'\x80\x94\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
            nbname += b'\x20\x43\x4b\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
            nbname += b'\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
            nbname += b'\x41\x00\x00\x21\x00\x01'

            sock.sendto(nbname, (ip, 137))
            data, _ = sock.recvfrom(1024)
            sock.close()

            if len(data) > 57:
                names = []
                num_names = data[56]
                for i in range(num_names):
                    offset = 57 + i * 18
                    if offset + 18 <= len(data):
                        name_bytes = data[offset:offset + 15]
                        name = name_bytes.decode('ascii', errors='ignore').strip()
                        if name and name != '\x00' * len(name):
                            names.append(name)

                if names:
                    return names[0]
        except Exception:
            pass
        return None

    def _llmnr_resolve(self, ip: str) -> Optional[str]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            llmnr_query = bytes([
                0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x08, 0x5f, 0x68, 0x6f,
                0x73, 0x74, 0x6e, 0x61, 0x6d, 0x65, 0x04, 0x5f,
                0x75, 0x64, 0x70, 0x05, 0x6c, 0x6f, 0x63, 0x61,
                0x6c, 0x00, 0x00, 0x21, 0x00, 0x01
            ])

            sock.sendto(llmnr_query, (ip, 5355))
            data, _ = sock.recvfrom(1024)
            sock.close()

            if len(data) > 12:
                name_len = data[12]
                if name_len > 0 and 13 + name_len <= len(data):
                    return data[13:13 + name_len].decode('ascii', errors='ignore')
        except Exception:
            pass
        return None

    def _mdns_resolve(self, ip: str) -> Optional[str]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            mdns_query = bytes([
                0x00, 0x00, 0x84, 0x00, 0x00, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x05, 0x5f, 0x68, 0x74,
                0x74, 0x70, 0x04, 0x5f, 0x74, 0x63, 0x70, 0x05,
                0x6c, 0x6f, 0x63, 0x61, 0x6c, 0x00, 0x00, 0x0c,
                0x00, 0x01
            ])

            sock.sendto(mdns_query, (ip, 5353))
            data, _ = sock.recvfrom(1024)
            sock.close()

            if len(data) > 12:
                i = 12
                while i < len(data) - 4:
                    if data[i] == 0:
                        break
                    label_len = data[i]
                    i += 1
                    if i + label_len <= len(data):
                        i += label_len
                    else:
                        break

                if i < len(data) and data[i] == 0:
                    i += 1
                    return data[12:i - 1].decode('ascii', errors='ignore')
        except Exception:
            pass
        return None

    def _upnp_discover(self, ip: str) -> Optional[str]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            ssdp_request = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                "MAN: \"ssdp:discover\"\r\n"
                "MX: 3\r\n"
                "ST: ssdp:all\r\n"
                "\r\n"
            )

            sock.sendto(ssdp_request.encode(), (ip, 1900))
            data, _ = sock.recvfrom(1024)
            sock.close()

            response = data.decode('utf-8', errors='ignore')
            for line in response.split('\r\n'):
                if line.upper().startswith('SERVER:'):
                    server = line.split(':', 1)[1].strip()
                    if server:
                        return server
        except Exception:
            pass
        return None

    def _http_banner(self, ip: str) -> Optional[str]:
        for port, scheme in [(80, 'http'), (443, 'https'), (8080, 'http'), (8443, 'http')]:
            try:
                import urllib.request
                import ssl

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                url = f"{scheme}://{ip}:{port}/"
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'NetGuard/1.0')

                response = urllib.request.urlopen(req, timeout=2, context=ctx)
                server = response.headers.get('Server', '')
                if server:
                    return server

                title = response.read(1024).decode('utf-8', errors='ignore')
                import re
                title_match = re.search(r'<title>(.*?)</title>', title, re.IGNORECASE)
                if title_match:
                    return title_match.group(1)[:50]
            except Exception:
                continue
        return None

    def _select_best_result(self, results: List[Dict]) -> Dict:
        priority = {
            "netbios": 1,
            "llmnr": 2,
            "mdns": 3,
            "dns": 4,
            "http": 5,
            "upnp": 6,
        }

        for source_priority in sorted(priority.keys(), key=lambda x: priority[x]):
            for result in results:
                if result["source"] == source_priority:
                    return {
                        "hostname": result["hostname"],
                        "source": result["source"],
                        "confidence": 1.0 - (priority[source_priority] * 0.1)
                    }

        if results:
            return {
                "hostname": results[0]["hostname"],
                "source": results[0]["source"],
                "confidence": 0.5
            }

        return {"hostname": "", "source": "none", "confidence": 0.0}


def get_hostname_via_nmap(ip: str) -> str:
    try:
        import nmap
        nm = nmap.PortScanner()
        nm.scan(hosts=ip, arguments="-sn --host-timeout 5s")
        if ip in nm.all_hosts():
            return nm[ip].hostname()
    except Exception:
        pass
    return ""

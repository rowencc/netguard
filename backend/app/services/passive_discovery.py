"""
Passive Network Discovery Methods

These methods don't require router API access:
1. DHCP Option parsing (Vendor Class Identifier)
2. mDNS/Bonjour service discovery
3. LLMNR name resolution
4. NetBIOS name resolution
5. HTTP/HTTPS banner grabbing
6. SSDP/UPnP discovery
7. ARP vendor lookup
8. WiFi probe request analysis (requires monitor mode)
"""

import subprocess
import json
import re
from typing import Dict, Optional, List


class PassiveDiscovery:
    WIFI_CHIPSETS = {
        "Qualcomm": ["qualcomm", "atheros", "qca"],
        "MediaTek": ["mediatek", "ralink", "mtk"],
        "Broadcom": ["broadcom", "bcm", "brcm"],
        "Intel": ["intel", "wifi 6", "wifi 5"],
        "Realtek": ["realtek", "rtl"],
        "Ralink": ["ralink", "rt"],
    }

    def __init__(self):
        self._device_info_cache: Dict[str, Dict] = {}

    def discover_device_info(self, ip: str, mac: str) -> Dict:
        info = {
            "ip": ip,
            "mac": mac,
            "is_wifi": False,
            "wifi_chipset": "",
            "connection_type": "unknown",
            "device_capabilities": [],
        }

        mac_analysis = self._analyze_mac_for_wifi(mac)
        if mac_analysis["is_wifi"]:
            info["is_wifi"] = True
            info["wifi_chipset"] = mac_analysis.get("chipset", "")
            info["connection_type"] = "wifi"

        hostname_info = self._get_netbios_name(ip)
        if hostname_info:
            info["hostname"] = hostname_info
            info["device_capabilities"].append("netbios")

        mdns_info = self._get_mdns_services(ip)
        if mdns_info:
            info["mdns_services"] = mdns_info
            info["device_capabilities"].append("mdns")

        upnp_info = self._get_upnp_info(ip)
        if upnp_info:
            info["upnp_server"] = upnp_info
            info["device_capabilities"].append("upnp")

        http_info = self._get_http_banner(ip)
        if http_info:
            info["http_server"] = http_info
            info["device_capabilities"].append("http")

        return info

    def _analyze_mac_for_wifi(self, mac: str) -> Dict:
        result = {"is_wifi": False, "chipset": ""}
        mac_upper = mac.upper().replace("-", ":")

        known_wifi_vendors = {
            "Qualcomm/Atheros": [
                "00:03:7F", "00:13:74", "00:15:B7", "00:17:9B",
                "00:1A:92", "00:1D:60", "00:20:E7", "00:21:7C",
                "00:22:6B", "00:23:CD", "00:24:36", "00:25:00",
                "00:26:B9", "00:80:5A", "30:05:5C", "40:E3:D6",
                "64:66:B3", "74:DA:DA", "84:24:43", "9C:4F:CF",
                "A4:1F:72", "B0:4E:26", "B8:27:EB", "C0:4A:00",
                "C4:71:54", "D0:21:F9", "D4:3D:7E", "E0:63:DA",
                "EC:08:6B", "F4:F5:E8",
            ],
            "MediaTek/Ralink": [
                "00:0C:E7", "00:0E:8F", "00:1A:2B", "00:1B:B1",
                "00:1C:10", "00:1C:B3", "00:1D:0D", "00:1E:58",
                "00:21:27", "00:23:CD", "00:25:11", "00:26:5B",
                "00:27:19", "08:36:C9", "10:9F:41", "14:CC:20",
                "14:D7:04", "18:C0:06", "1C:87:2C", "20:DC:E6",
                "24:0A:C4", "28:5F:3F", "2C:5B:E1", "30:EB:25",
                "34:CD:BE", "38:0B:3C", "3C:37:86", "40:01:7A",
                "44:D9:E7", "48:EE:0C", "4C:8B:EF", "50:55:3A",
                "50:C7:BF", "54:04:A6", "58:6B:14", "5C:E9:31",
                "60:38:E0", "60:57:18", "60:A4:4C", "64:5A:ED",
                "68:72:51", "6C:B0:CE", "70:5A:0F", "74:AC:B9",
                "78:8A:20", "7C:4F:7D", "80:00:0B", "84:A4:66",
                "88:DC:96", "8C:BE:96", "90:72:40", "94:10:3E",
                "94:BA:06", "98:25:4A", "9C:5C:8E", "A0:04:60",
                "A0:F3:C1", "A4:12:42", "A4:33:D1", "A8:58:80",
                "AC:22:0B", "AC:4A:56", "AC:84:C6", "B0:4E:26",
                "B0:72:BF", "B0:BE:76", "B4:30:52", "B4:61:E9",
                "B8:27:EB", "B8:EE:65", "BC:EE:7B", "C0:25:E9",
                "C0:4A:00", "C0:61:18", "C0:7B:BC", "C4:71:54",
                "C4:F0:81", "C8:3A:35", "C8:BE:19", "CC:2D:8C",
                "D0:21:F9", "D0:7A:B5", "D4:3D:7E", "D4:A1:2F",
                "D4:F5:EF", "D8:07:B6", "DC:65:55", "E0:63:DA",
                "E4:5F:01", "E8:04:62", "EC:08:6B", "F0:9F:C2",
                "F4:0F:1F", "F4:F5:E8", "F8:1A:67", "F8:A9:D0",
                "FC:15:B4", "FC:EC:DA", "FE:FF:01",
            ],
            "Broadcom": [
                "00:10:18", "00:11:95", "00:12:49", "00:13:49",
                "00:14:6D", "00:15:5D", "00:16:3E", "00:17:F2",
                "00:19:3B", "00:1A:2B", "00:1B:2F", "00:1C:26",
                "00:1D:4C", "00:1E:3F", "00:1F:3B", "00:20:D8",
                "00:21:00", "00:22:4B", "00:23:06", "00:24:01",
                "00:25:00", "00:26:5B", "00:27:19", "04:A9:6D",
                "08:36:C9", "0C:44:3E", "10:68:3F", "14:18:77",
                "18:64:72", "1C:3B:F3", "20:15:74", "24:5A:4C",
                "28:0C:2D", "2C:4D:54", "30:10:B4", "34:23:BA",
                "38:0B:3C", "3C:37:86", "40:78:B6", "44:31:92",
                "48:D7:05", "4C:B1:6C", "50:55:3A", "54:35:30",
                "58:96:1D", "5C:F9:38", "60:6C:66", "64:80:99",
                "68:A3:78", "6C:4B:90", "70:18:A3", "74:AC:B9",
                "78:31:EB", "7C:76:35", "80:00:0B", "84:1B:5E",
                "88:6A:03", "8C:3B:AD", "90:4E:2B", "94:10:3E",
                "98:3B:8F", "9C:37:F4", "A0:04:60", "A4:56:30",
                "A8:51:5B", "AC:22:0B", "AC:BC:32", "B0:4E:26",
                "B0:72:BF", "B4:30:52", "B8:27:EB", "B8:EE:65",
                "BC:EE:7B", "C0:25:E9", "C0:4A:00", "C4:71:54",
                "C8:3A:35", "CC:2D:8C", "D0:21:F9", "D0:7A:B5",
                "D4:3D:7E", "D4:A1:2F", "D8:07:B6", "DC:A6:32",
                "E0:63:DA", "E4:5F:01", "E8:04:62", "EC:08:6B",
                "F0:9F:C2", "F4:0F:1F", "F8:1A:67", "FC:15:B4",
            ],
            "Intel": [
                "00:13:02", "00:13:74", "00:15:17", "00:16:6F",
                "00:17:F4", "00:18:DE", "00:19:D1", "00:1B:21",
                "00:1C:23", "00:1D:E5", "00:1E:65", "00:1F:3B",
                "00:20:7B", "00:21:5A", "00:22:FA", "00:23:04",
                "00:24:D7", "00:25:00", "00:26:C7", "04:3E:0C",
                "08:11:96", "0C:8B:95", "10:02:B5", "14:18:77",
                "18:3D:A2", "1C:3B:F3", "20:16:B9", "24:5A:4C",
                "28:16:AD", "2C:6E:85", "30:5A:3A", "34:13:E8",
                "38:FC:98", "3C:58:C2", "40:25:C9", "44:03:A7",
                "48:51:B7", "4C:34:88", "50:2B:73", "54:81:AD",
                "58:96:1D", "5C:51:4F", "60:57:18", "64:80:99",
                "68:05:CA", "6C:88:14", "70:85:C2", "74:2F:68",
                "78:2B:46", "7C:5C:F8", "80:86:F2", "84:3A:4B",
                "88:3B:B7", "8C:EC:4B", "90:61:AE", "94:65:9C",
                "98:FA:9B", "9C:B6:D0", "A0:36:9F", "A4:34:D9",
                "A8:51:5B", "AC:67:5D", "B0:A4:60", "B4:69:2F",
                "B8:08:CF", "B8:86:0A", "BC:77:37", "C0:E4:2D",
                "C4:3C:AB", "C8:5B:76", "CC:3D:82", "D0:7A:B5",
                "D4:3D:7E", "D8:9E:3F", "DC:53:60", "E0:6C:C1",
                "E4:5F:01", "E8:B1:FC", "EC:08:6B", "F0:20:FF",
                "F4:0F:1F", "F8:63:3F", "FC:44:82", "FC:EC:DA",
            ],
        }

        for chipset, prefixes in known_wifi_vendors.items():
            for prefix in prefixes:
                if mac_upper.startswith(prefix.upper()):
                    result["is_wifi"] = True
                    result["chipset"] = chipset
                    return result

        return result

    def _get_netbios_name(self, ip: str) -> Optional[str]:
        try:
            sock = __import__('socket').socket(__import__('socket').AF_INET, __import__('socket').SOCK_DGRAM)
            sock.settimeout(2)

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

    def _get_mdns_services(self, ip: str) -> List[str]:
        services = []
        try:
            sock = __import__('socket').socket(__import__('socket').AF_INET, __import__('socket').SOCK_DGRAM)
            sock.settimeout(2)

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
                    service = data[12:i - 1].decode('ascii', errors='ignore')
                    if service:
                        services.append(service)
        except Exception:
            pass
        return services

    def _get_upnp_info(self, ip: str) -> Optional[str]:
        try:
            sock = __import__('socket').socket(__import__('socket').AF_INET, __import__('socket').SOCK_DGRAM)
            sock.settimeout(2)

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
                    return line.split(':', 1)[1].strip()
        except Exception:
            pass
        return None

    def _get_http_banner(self, ip: str) -> Optional[str]:
        for port in [80, 443, 8080, 8443]:
            try:
                import urllib.request
                import ssl

                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                scheme = "https" if port in (443, 8443) else "http"
                url = f"{scheme}://{ip}:{port}/"
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'NetGuard/1.0')
                response = urllib.request.urlopen(req, timeout=2, context=ctx)
                server = response.headers.get('Server', '')
                if server:
                    return server
            except Exception:
                continue
        return None

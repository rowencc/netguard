"""
Multi-Signal Device Identifier

Cross-validates multiple identification sources:
1. MAC Address Analysis (IEEE 802 standards)
2. OUI Vendor Lookup (multi-source: IEEE + Wireshark + Nmap)
3. Hostname Pattern Matching
4. DHCP Fingerprinting (Option 55: Parameter Request List)
5. mDNS/DNS-SD Service Discovery
6. Open Port Signature Analysis
7. OS Fingerprinting (TCP/IP stack analysis)
8. NetBIOS/LLMNR Name Resolution
9. Cisco/Aruba Device Specific Identification
10. Manufacturer-Specific OUI Database

Academic References:
- IEEE 802-2014: MAC Address Structure and Assignment
- RFC 2131: DHCP (Dynamic Host Configuration Protocol)
- RFC 3118: DHCP Authentication
- RFC 6762: mDNS (Multicast DNS)
- RFC 6763: DNS-SD (DNS Service Discovery)
- RFC 1001/1002: NetBIOS over TCP/IP
- RFC 4787: NAT Behavioral Requirements

Confidence Scoring (weighted fusion):
- MAC OUI vendor match:      weight=0.25
- Hostname pattern match:    weight=0.20
- Port signature match:      weight=0.20
- DHCP fingerprint match:    weight=0.15
- mDNS service match:        weight=0.10
- OS fingerprint match:      weight=0.10
"""

from typing import Dict, Optional, List, Any, Tuple
from app.services.vendor_lookup import VendorLookup
from app.services.mac_analyzer import MACAnalyzer

KNOWN_CAMERA_VENDORS = [
    "HIKVISION", "DAHUA", "UNIVIEW", "TIANDY", "KEDACOM",
    "HONEYWELL", "AXIS", "BOSCH", "SONY", "SAMSUNG",
    "AVIGILON", "MILESTONE", "VIVOTEK", "DINVOTEK", "CP PLUS",
    "EZVIV", "REOLINK", "AMCREST", "WANSVIEW", "ZOSI",
    "FUNGLUE", "YI", "FOSCAM", "INSTAR", "MOBOTIX", "VADDIO",
    "HANWHA", "PELCO", "VERKADA", "ARLO",
]

KNOWN_ROUTER_VENDORS = [
    "TP-LINK", "D-LINK", "NETGEAR", "UBIQUITI", "ASUSTEK",
    "CISCO", "LINKSYS", "HUAWEI", "ZTE", "TENDA",
    "MERCURY", "FAST", "RUIJIE", "H3C", "TOTOLINK",
    "PHICOMM", "EDIMAX", "ENGENIUS", "MIKROTIK",
    "JUNIPER", "EXTREME", "FORTINET", "PALO ALTO", "CHECK POINT",
    "BARRACUDA", "SOPHOS", "WATCHGUARD", "SONICWALL", "ZIMAX",
]

KNOWN_IOT_VENDORS = [
    "BROADLINK", "YEELIGHT", "AQARA",
    "TUYA", "SONOFF", "MAGICHOME",
    "SONOS", "AMAZON", "GOOGLE", "APPLE",
    "EVE", "NANOLEAF", "WIZ", "MERROSS", "SHelly",
]

KNOWN_PHONE_VENDORS = [
    "APPLE", "SAMSUNG", "HUAWEI", "XIAOMI", "OPPO",
    "VIVO", "ONEPLUS", "REALME", "HONOR", "GOOGLE",
    "MOTOROLA", "NOKIA", "SONY", "LG", "ZTE",
    "MEIZU", "ASUS", "RAZER", "BLACKSHARK", "IQOO",
]

KNOWN_COMPUTER_VENDORS = [
    "APPLE", "DELL", "HP", "LENOVO", "ASUSTEK",
    "ACER", "MSI", "RAZER", "SAMSUNG", "MICROSOFT",
    "TOSHIBA", "FUJITSU", "SONY", "PANASONIC", "LG",
]

KNOWN_PRINTER_VENDORS = [
    "HEWLETT-PACKARD", "HP", "CANON", "EPSON", "BROTHER",
    "LEXMARK", "XEROX", "RICOH", "SAMSUNG", "KYOCERA",
    "OKI", "SHARP", "KONICA",
]

KNOWN_SERVER_VENDORS = [
    "DELL", "HP", "LENOVO", "IBM", "SUPERMICRO",
    "SYNOLOGY", "QNAP", "NETAPP", "EMC",
]

KNOWN_NETWORK_DEVICE_VENDORS = [
    "CISCO", "ARUBA", "JUNIPER", "EXTREME", "FORTINET",
    "PALO ALTO", "CHECK POINT", "BARRACUDA", "SOPHOS", "WATCHGUARD",
    "SONICWALL", "ZIMAX", "H3C", "RUIJIE",
    "UBIQUITI", "MIKROTIK", "MERAKI", "MERU",
    "BROADCOM", "QUALCOMM", "INTEL", "AZUREWAVE", "FN-LINK",
    "REALTEK", "MEDIATEK", "Ralink", "Atheros",
]

DHCP_FINGERPRINTS = {
    "camera": {
        "option55_patterns": [
            [1, 3, 6, 12, 15, 43, 51, 53, 54, 255],
            [1, 3, 6, 12, 15, 43, 51, 53, 54],
            [1, 12, 3, 6, 15, 43, 51, 54],
            [1, 3, 6, 12, 15, 43, 51],
        ],
        "vendor_classes": ["hikvision", "dahua", "uniview", "ipcamera", "camera", "nvr", "dvr"],
    },
    "router": {
        "option55_patterns": [
            [1, 3, 6, 12, 15, 43, 51, 53, 54, 58, 59, 255],
            [1, 3, 6, 12, 15, 255],
            [1, 3, 6, 12, 15, 43, 51, 54],
            [1, 3, 6, 12, 15, 43, 51, 53, 54],
        ],
        "vendor_classes": ["android-dhcn", "udhcp", "dnsmasq", "dibbler", "kea"],
    },
    "phone": {
        "option55_patterns": [
            [1, 3, 6, 12, 15, 28, 51, 53, 54],
            [1, 3, 6, 12, 15, 28, 51, 53, 54, 43],
            [1, 3, 6, 12, 15, 28, 51, 53],
        ],
        "vendor_classes": ["android", "iphone", "ios", "windows phone", "huawei", "samsung"],
    },
    "computer": {
        "option55_patterns": [
            [1, 3, 4, 6, 12, 15, 17, 26, 28, 31, 33, 43, 44, 46, 47, 51, 52, 53, 54, 58, 59, 60, 61, 255],
            [1, 3, 4, 6, 12, 15, 17, 26, 28, 31, 33, 43, 44, 46, 47, 51, 52, 53, 54, 58, 59, 60, 61],
        ],
        "vendor_classes": ["msft 10.0", "msft 5.0", "msft 6.0", "msft 9.0", "dhcpcd"],
    },
    "network_device": {
        "option55_patterns": [
            [1, 3, 6, 12, 15, 28, 43, 51, 53, 54, 255],
            [1, 3, 6, 12, 15, 43, 51, 54, 58, 59],
        ],
        "vendor_classes": ["cisco", "aruba", "juniper", "fortinet"],
    },
    "printer": {
        "option55_patterns": [
            [1, 3, 6, 12, 15, 43, 44, 46, 47, 51, 52, 53, 54, 58, 59, 60, 61],
        ],
        "vendor_classes": ["hp", "canon", "epson", "brother", "lexmark"],
    },
}

MDNS_DEVICE_SIGNATURES = {
    "camera": [
        "_rtsp._tcp", "_onvif._tcp", "_ipcam._tcp",
        "_hikvision._tcp", "_dahua._tcp",
    ],
    "router": [
        "_http._tcp", "_ssh._tcp", "_telnet._tcp",
        "_netconfig._udp", "_router._udp",
    ],
    "printer": [
        "_ipp._tcp", "_ipps._tcp", "_printer._tcp",
        "_uscanner._tcp",
    ],
    "media": [
        "_airplay._tcp", "_raop._tcp", "_chromecast._tcp",
        "_dlna._tcp", "_mediareceiver._tcp",
    ],
    "computer": [
        "_smb._tcp", "_afp._tcp", "_ssh._tcp",
        "_rdp._tcp", "_vnc._tcp",
    ],
    "iot": [
        "_hap._tcp", "_coap._udp", "_mqtt._tcp",
        "_homekit._tcp", "_googlecast._tcp",
    ],
    "network_device": [
        "_cisco-vpnc._udp", "_cisco-awdl._tcp",
        "_meraki._tcp", "_aruba._tcp",
    ],
    "phone": [
        "_apple-mobdev2._tcp", "_airdrop._tcp",
        "_companion-link._tcp",
    ],
}

PORT_DEVICE_SIGNATURES = {
    "camera": {
        "ports": [554, 8554, 37777, 8000, 8080, 8081, 80, 443],
        "min_match": 2,
        "port_weights": {554: 0.3, 8554: 0.3, 37777: 0.4, 8081: 0.2},
    },
    "router": {
        "ports": [80, 443, 22, 23, 8080, 8443, 161, 162],
        "min_match": 2,
        "port_weights": {23: 0.3, 161: 0.4, 8080: 0.2},
    },
    "printer": {
        "ports": [631, 9100, 515, 631, 80, 443],
        "min_match": 2,
        "port_weights": {9100: 0.4, 631: 0.3, 515: 0.4},
    },
    "nas": {
        "ports": [5000, 5001, 8080, 139, 445, 22, 21],
        "min_match": 2,
        "port_weights": {5000: 0.4, 5001: 0.4, 139: 0.3, 445: 0.3},
    },
    "phone": {
        "ports": [62078, 49152, 49153, 49154],
        "min_match": 1,
        "port_weights": {62078: 0.5},
    },
    "network_device": {
        "ports": [161, 162, 22, 23, 443, 80, 8080, 8443, 23, 1723, 5060, 5061],
        "min_match": 2,
        "port_weights": {161: 0.4, 162: 0.3, 1723: 0.3, 5060: 0.2, 5061: 0.2},
    },
}


class DeviceIdentifier:
    def __init__(self):
        self.vendor_lookup = VendorLookup()
        self.mac_analyzer = MACAnalyzer()

    def identify_device(self, scan_result: Dict) -> Dict:
        mac_address = scan_result.get("mac_address", "")
        hostname = scan_result.get("hostname", "")
        open_ports = scan_result.get("open_ports", {})
        mdns_services = scan_result.get("mdns_services", [])
        dhcp_options = scan_result.get("dhcp_options", {})
        vendor = scan_result.get("vendor") or self.vendor_lookup.lookup(mac_address)

        mac_analysis = MACAnalyzer.analyze(mac_address)
        is_randomized = MACAnalyzer.is_randomized_mac(mac_address, vendor)

        scores = self._calculate_weighted_scores(
            scan_result, vendor, hostname, open_ports,
            mdns_services, dhcp_options, mac_analysis
        )

        device_type, confidence = self._fuse_scores(scores)

        device_model = self._determine_device_model(vendor, hostname, device_type)
        risk_level = self._assess_risk(scan_result, vendor, device_type, mac_analysis)

        vendor_validation = None
        if vendor and mac_address:
            vendor_validation = self.vendor_lookup.cross_validate(mac_address, vendor)

        return {
            **scan_result,
            "vendor": vendor,
            "device_type": device_type,
            "device_model": device_model,
            "confidence": confidence,
            "risk_level": risk_level,
            "mac_info": MACAnalyzer.get_mac_info(mac_address),
            "is_randomized_mac": is_randomized,
            "identification_scores": scores,
            "vendor_validation": vendor_validation,
        }

    def _calculate_weighted_scores(
        self,
        scan_result: Dict,
        vendor: Optional[str],
        hostname: str,
        open_ports: Dict,
        mdns_services: List[str],
        dhcp_options: Dict,
        mac_analysis,
    ) -> Dict[str, Dict[str, float]]:
        scores = {
            "camera": 0.0, "router": 0.0, "phone": 0.0,
            "computer": 0.0, "iot": 0.0, "printer": 0.0,
            "server": 0.0, "network_device": 0.0, "unknown": 0.0,
        }

        vendor_score = self._score_vendor(vendor, mac_analysis)
        for dt, score in vendor_score.items():
            scores[dt] += score * 0.25

        hostname_score = self._score_hostname(hostname)
        for dt, score in hostname_score.items():
            scores[dt] += score * 0.20

        port_score = self._score_ports(open_ports)
        for dt, score in port_score.items():
            scores[dt] += score * 0.20

        dhcp_score = self._score_dhcp(dhcp_options)
        for dt, score in dhcp_score.items():
            scores[dt] += score * 0.15

        mdns_score = self._score_mdns(mdns_services)
        for dt, score in mdns_score.items():
            scores[dt] += score * 0.10

        os_score = self._score_os(scan_result.get("os_matches", []))
        for dt, score in os_score.items():
            scores[dt] += score * 0.10

        return scores

    def _score_vendor(self, vendor: Optional[str], mac_analysis) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not vendor:
            return scores

        vu = vendor.upper()

        vendor_map = {
            "camera": KNOWN_CAMERA_VENDORS,
            "router": KNOWN_ROUTER_VENDORS,
            "phone": KNOWN_PHONE_VENDORS,
            "computer": KNOWN_COMPUTER_VENDORS,
            "printer": KNOWN_PRINTER_VENDORS,
            "server": KNOWN_SERVER_VENDORS,
            "network_device": KNOWN_NETWORK_DEVICE_VENDORS,
        }

        for device_type, vendors in vendor_map.items():
            for v in vendors:
                if v.upper() in vu or vu in v.upper():
                    scores[device_type] = 1.0
                    break

        if any(k in vu for k in KNOWN_IOT_VENDORS):
            scores["iot"] = max(scores.get("iot", 0), 0.5)

        if mac_analysis and mac_analysis.is_locally_administered:
            for dt in scores:
                scores[dt] *= 0.7

        return scores

    def _score_hostname(self, hostname: str) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not hostname:
            return scores

        hl = hostname.lower()

        hostname_signatures = {
            "camera": [
                "camera", "ipc", "nvr", "dvr", "cam", "hikvision",
                "dahua", "uniview", "reolink", "foscam",
            ],
            "router": [
                "router", "ap", "wifi", "gateway", "switch", "rt",
                "openwrt", "ddwrt", "asus", "netgear",
            ],
            "phone": [
                "iphone", "galaxy", "pixel", "redmi", "oppo", "vivo",
                "android", "ios", "mobile", "phone",
            ],
            "computer": [
                "desktop", "laptop", "pc", "macbook", "imac",
                "windows", "linux", "ubuntu", "debian",
            ],
            "printer": [
                "printer", "print", "laserjet", "inkjet", "mfp",
                "hp-print", "canon", "epson",
            ],
            "nas": [
                "nas", "synology", "qnap", "diskstation",
                "ds-", "ts-",
            ],
            "network_device": [
                "switch", "firewall", "access-point", "ap", "wlan",
                "cisco", "aruba", "juniper", "fortinet", "paloalto",
                "meraki", "extreme", "h3c", "ruijie",
            ],
        }

        for device_type, keywords in hostname_signatures.items():
            for kw in keywords:
                if kw in hl:
                    scores[device_type] = 1.0
                    break

        return scores

    def _score_ports(self, open_ports: Dict) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not open_ports:
            return scores

        port_ints = set()
        for p in open_ports.keys():
            try:
                port_ints.add(int(p))
            except (ValueError, TypeError):
                continue

        for device_type, sig in PORT_DEVICE_SIGNATURES.items():
            sig_ports = set(sig["ports"])
            matched = sig_ports & port_ints
            if len(matched) >= sig["min_match"]:
                weighted = sum(
                    sig["port_weights"].get(p, 0.1) for p in matched
                )
                scores[device_type] = min(weighted, 1.0)

        return scores

    def _score_dhcp(self, dhcp_options: Dict) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not dhcp_options:
            return scores

        option55 = dhcp_options.get("parameter_request_list", [])
        vendor_class = dhcp_options.get("vendor_class_identifier", "").lower()

        for device_type, sig in DHCP_FINGERPRINTS.items():
            if option55 in sig.get("option55_patterns", []):
                scores[device_type] = 1.0

            for vc in sig.get("vendor_classes", []):
                if vc in vendor_class:
                    scores[device_type] = max(scores[device_type], 0.9)

        return scores

    def _score_mdns(self, mdns_services: List[str]) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not mdns_services:
            return scores

        for device_type, sig_services in MDNS_DEVICE_SIGNATURES.items():
            matched = set(sig_services) & set(mdns_services)
            if matched:
                scores[device_type] = min(len(matched) * 0.4, 1.0)

        return scores

    def _score_os(self, os_matches: List[Dict]) -> Dict[str, float]:
        scores = {dt: 0.0 for dt in ["camera", "router", "phone", "computer", "iot", "printer", "server", "network_device"]}
        if not os_matches:
            return scores

        os_signatures = {
            "camera": ["linux", "embedded", "rtsp"],
            "router": ["linux", "embedded", "openwrt", "ddwrt"],
            "phone": ["android", "ios", "windows mobile"],
            "computer": ["windows", "linux", "macos", "mac os", "ubuntu", "debian"],
            "printer": ["embedded", "linux"],
            "network_device": ["ios", "cisco", "aruba", "juniper", "fortinet"],
        }

        for match in os_matches:
            name = match.get("name", "").lower()
            for device_type, keywords in os_signatures.items():
                for kw in keywords:
                    if kw in name:
                        scores[device_type] = max(scores[device_type], 0.6)
                        break

        return scores

    def _fuse_scores(self, scores: Dict[str, float]) -> Tuple[str, float]:
        valid_scores = {dt: s for dt, s in scores.items() if s > 0}

        if not valid_scores:
            return "unknown", 0.0

        best_type = max(valid_scores, key=valid_scores.get)
        best_score = valid_scores[best_type]

        sorted_scores = sorted(valid_scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            margin = sorted_scores[0] - sorted_scores[1]
            if margin < 0.1:
                confidence = best_score * 0.7
            else:
                confidence = best_score
        else:
            confidence = best_score

        if best_score < 0.15:
            return "unknown", best_score

        return best_type, min(confidence, 1.0)

    def _determine_device_model(self, vendor: Optional[str], hostname: str, device_type: str) -> str:
        if not vendor and not hostname:
            return ""
        parts = []
        if vendor:
            parts.append(vendor)
        if hostname:
            parts.append(f"({hostname})")
        return " ".join(parts)

    def _assess_risk(self, scan_result: Dict, vendor: Optional[str],
                     device_type: str, mac_analysis) -> str:
        risk_score = 0

        if device_type in ("camera",):
            risk_score += 3
        if device_type == "unknown":
            risk_score += 1
        if device_type == "network_device":
            risk_score += 2

        if vendor and vendor.upper() in [v.upper() for v in KNOWN_CAMERA_VENDORS]:
            risk_score += 2

        if mac_analysis and mac_analysis.is_locally_administered:
            risk_score += 1

        open_ports = scan_result.get("open_ports", {})
        dangerous_ports = {23, 21, 3389, 5900, 445, 135, 139}
        exposed = set(open_ports.keys()) & dangerous_ports
        if exposed:
            risk_score += len(exposed)

        if risk_score >= 4:
            return "CRITICAL"
        elif risk_score >= 3:
            return "HIGH"
        elif risk_score >= 1:
            return "MEDIUM"
        return "LOW"

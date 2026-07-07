"""
MAC Address Analyzer - IEEE 802 Standard Compliance

References:
- IEEE 802-2014: IEEE Standard for Local and Metropolitan Area Networks
- IEEE OUI Registry: https://standards-oui.ieee.org/
- RFC 7042: IANA Considerations for the IANA Ethernet Address Block

MAC Address Structure (48-bit):
- Bits 0 (LSB of first octet): Unicast(0) / Multicast(1)
- Bits 1 (2nd LSB of first octet): Globally Unique(0) / Locally Administered(1)
- Bits 2-47: Vendor-assigned portion

Extended MAC (EUI-48 vs. other):
- OUI (3 bytes / 6 hex): Standard vendor identification
- MA-M (3.5 bytes / 7 hex): Medium-size assignments
- MA-L (3 bytes / 6 hex): Large (legacy OUI) assignments
- MA-S (4 bytes / 8 hex): Small / sub-vendor identification
"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple


@dataclass
class MACAnalysis:
    mac_address: str
    normalized: str
    is_valid: bool
    is_multicast: bool
    is_locally_administered: bool
    is_burned_in: bool
    oui: str
    nic_specific: str
    mac_type: str
    bit_summary: str
    broadcast: bool
    reserved: bool
    local_range: bool
    global_range: bool


class MACAnalyzer:
    MAC_REGEX = re.compile(r'^([0-9A-Fa-f]{2}[:-]?){5}[0-9A-Fa-f]{2}$')

    IEEE_MULTICAST_PREFIXES = {
        "01:00:5E": "IPv4 Multicast (IANA)",
        "33:33": "IPv6 Multicast",
        "01:80:C2": "Spanning Tree Protocol (BPDU)",
        "01:80:C2:00:00": "STP Protocol",
        "01:80:C2:00:00:01": "MAC Pause",
        "01:80:C2:00:00:02": "LACP",
        "01:80:C2:00:00:03": "LACP Marker",
        "01:80:C2:00:00:0E": "LLDP",
        "01:1B:19": "Precision Time Protocol (PTP)",
        "01:0C:CC": "CDP/VTP (Cisco)",
        "01:E0:2B": "IEEE 802.1Q Spanning Tree",
        "FF:FF:FF": "Broadcast",
    }

    LOCALLY_ADMINISTERED_INDICATORS = [
        "randomized", "privacy", "virtual", "docker", "vmware",
        "virtualbox", "hyper-v", "container", "sandbox",
    ]

    DEVICE_TYPE_SIGNATURES = {
        "router": {
            "keywords": ["router", "gateway", "ap", "wifi", "wireless", "switch", "modem"],
            "vendors": [
                "TP-LINK", "D-LINK", "NETGEAR", "UBIQUITI", "CISCO", "LINKSYS",
                "HUAWEI", "ZTE", "TENDA", "MERCURY", "FAST", "RUIJIE", "H3C",
                "TOTOLINK", "PHICOMM", "EDIMAX", "ENGENIUS", "MIKROTIK", "ARUBA",
                "BROADCOM", "QUALCOMM", "INTEL", "AZUREWAVE", "FN-LINK", "HUALAI",
                "HIGH-FLYING", "BILIAN", "AI-LINK", "CLOUD NETWORK",
            ],
            "oui_prefixes": [
                "00:1A:2B", "00:26:F2", "00:1E:58", "00:25:11",
                "B0:BE:76", "C0:25:E9", "3C:37:86", "D8:07:B6",
                "F8:1A:67", "AC:CF:5C", "14:CF:92", "50:C7:BF",
                "08:36:C9", "44:D9:E7", "6C:B0:CE", "78:8A:20",
                "74:AC:B9", "94:10:3E", "B8:27:EB", "DC:A6:32",
            ],
            "port_signatures": [80, 443, 22, 23, 8080, 8443],
            "mdns_services": ["_http._tcp", "_ssh._tcp", "_netconfig._udp"],
        },
        "camera": {
            "keywords": [
                "camera", "webcam", "ip camera", "nvr", "dvr", "cctv",
                "surveillance", "hikvision", "dahua", "uniview",
            ],
            "vendors": [
                "HIKVISION", "DAHUA", "UNIVIEW", "TIANDY", "KEDACOM",
                "HONEYWELL", "AXIS", "BOSCH", "SONY", "SAMSUNG",
                "AVIGILON", "MILESTONE", "VIVOTEK", "DINVOTEK", "CP PLUS",
                "EZVIV", "REOLINK", "AMCREST", "WANSVIEW", "ZOSI",
                "FUNGLUE", "YI", "XIAOMI", "TP-LINK", "TUYA",
                "FOSCAM", "INSTAR", "MOBOTIX", "VADDIO", "PANASONIC",
                "HANWHA", "HANWHA TECHWIN", "PELCO", "VERKADA", "ARLO",
            ],
            "port_signatures": [554, 8554, 80, 443, 37777, 8080, 8000, 8081],
            "mdns_services": ["_rtsp._tcp", "_onvif._tcp", "_http._tcp"],
        },
        "phone": {
            "keywords": [
                "phone", "mobile", "android", "ios", "iphone", "galaxy",
                "pixel", "redmi", "oppo", "vivo",
            ],
            "vendors": [
                "APPLE", "SAMSUNG", "HUAWEI", "XIAOMI", "OPPO",
                "VIVO", "ONEPLUS", "REALME", "HONOR", "GOOGLE",
                "MOTOROLA", "NOKIA", "SONY", "LG", "ZTE",
                "MEIZU", "ASUS", "RAZER", "BLACKSHARK", "IQOO",
                "REDMI", "POCO", "INFINIX", "TECNO", "ITEL",
            ],
        },
        "computer": {
            "keywords": [
                "windows", "linux", "macos", "mac os", "desktop", "laptop",
                "ubuntu", "debian", "centos", "fedora", "microsoft",
            ],
            "vendors": [
                "APPLE", "DELL", "HP", "LENOVO", "ASUSTEK",
                "ACER", "MSI", "RAZER", "SAMSUNG", "MICROSOFT",
                "TOSHIBA", "FUJITSU", "SONY", "PANASONIC", "LG",
                "THINKPAD", "SURFACE",
            ],
        },
        "iot": {
            "keywords": [
                "iot", "smart", "sensor", "thermostat", "bulb", "plug",
                "switch", "camera", "speaker", "hub", "gateway",
            ],
            "vendors": [
                "XIAOMI", "HUAWEI", "BROADLINK", "YEELIGHT", "AQARA",
                "SONY", "PHILIPS", "TUYA", "SONOFF", "MAGICHOME",
                "TP-LINK", "SONOS", "AMAZON", "GOOGLE", "APPLE",
                "EVE", "NANOLEAF", "WIZ", "MERROSS", "SHelly",
                "TASMOTA", "ESPHOME",
            ],
        },
        "printer": {
            "keywords": ["printer", "print", "laserjet", "inkjet", "mfp"],
            "vendors": [
                "HEWLETT-PACKARD", "HP", "CANON", "EPSON", "BROTHER",
                "LEXMARK", "XEROX", "RICOH", "SAMSUNG", "KYOCERA",
                "OKI", "SHARP", "KONICA", "DELL", "LEXMARK",
            ],
        },
        "server": {
            "keywords": ["server", "nas", "san", "rack", "blade"],
            "vendors": [
                "DELL", "HP", "LENOVO", "IBM", "SUPERMICRO",
                "SYNOLOGY", "QNAP", "NETAPP", "EMC", "ASUSTEK",
            ],
        },
    }

    @staticmethod
    def normalize_mac(mac: str) -> str:
        raw = mac.upper().strip()
        raw = re.sub(r'[^0-9A-F]', '', raw)
        if len(raw) != 12:
            return ""
        return ":".join(raw[i:i + 2] for i in range(0, 12, 2))

    @classmethod
    def validate_mac(cls, mac: str) -> bool:
        normalized = cls.normalize_mac(mac)
        return bool(normalized)

    @classmethod
    def analyze(cls, mac_address: str) -> MACAnalysis:
        normalized = cls.normalize_mac(mac_address)
        is_valid = bool(normalized)

        if not is_valid:
            return MACAnalysis(
                mac_address=mac_address,
                normalized="",
                is_valid=False,
                is_multicast=False,
                is_locally_administered=False,
                is_burned_in=False,
                oui="",
                nic_specific="",
                mac_type="invalid",
                bit_summary="Invalid MAC address format",
                broadcast=False,
                reserved=False,
                local_range=False,
                global_range=False,
            )

        octets = [int(h, 16) for h in normalized.split(":")]
        first_octet = octets[0]

        is_multicast = bool(first_octet & 0x01)
        is_locally_administered = bool(first_octet & 0x02)
        is_burned_in = not is_locally_administered
        broadcast = normalized == "FF:FF:FF:FF:FF:FF"

        oui = ":".join(normalized.split(":")[:3])
        nic_specific = ":".join(normalized.split(":")[3:])

        mac_type = cls._determine_type(
            normalized, is_multicast, is_locally_administered,
            broadcast, first_octet
        )

        bit_summary = cls._describe_bits(first_octet, is_multicast, is_locally_administered)

        reserved = is_multicast and not broadcast
        local_range = is_locally_administered
        global_range = not is_locally_administered

        return MACAnalysis(
            mac_address=mac_address,
            normalized=normalized,
            is_valid=True,
            is_multicast=is_multicast,
            is_locally_administered=is_locally_administered,
            is_burned_in=is_burned_in,
            oui=oui,
            nic_specific=nic_specific,
            mac_type=mac_type,
            bit_summary=bit_summary,
            broadcast=broadcast,
            reserved=reserved,
            local_range=local_range,
            global_range=global_range,
        )

    @classmethod
    def _determine_type(
        cls, normalized: str, is_multicast: bool,
        is_locally_administered: bool, broadcast: bool,
        first_octet: int
    ) -> str:
        if broadcast:
            return "broadcast"
        if is_multicast:
            prefix_6 = normalized[:8]
            prefix_8 = normalized[:11]
            if prefix_6 in cls.IEEE_MULTICAST_PREFIXES:
                return f"multicast ({cls.IEEE_MULTICAST_PREFIXES[prefix_6]})"
            if prefix_8 in cls.IEEE_MULTICAST_PREFIXES:
                return f"multicast ({cls.IEEE_MULTICAST_PREFIXES[prefix_8]})"
            return "multicast (IEEE reserved)"
        if is_locally_administered:
            return "locally administered (virtual/randomized)"
        return "globally unique (IEEE assigned)"

    @classmethod
    def _describe_bits(cls, first_octet: int, is_multicast: bool, is_local: bool) -> str:
        bits = format(first_octet, '08b')
        return (
            f"Byte1={bits} | "
            f"b0(unicast/multicast)={bits[7]}({('multicast' if is_multicast else 'unicast')}) | "
            f"b1(global/local)={bits[6]}({('local' if is_local else 'global')})"
        )

    @classmethod
    def identify_device_type(cls, mac: str, vendor: str = "",
                             hostname: str = "", mdns_services: list = None,
                             open_ports: dict = None) -> Dict[str, any]:
        normalized = cls.normalize_mac(mac)
        analysis = cls.analyze(mac)

        vendor_upper = vendor.upper() if vendor else ""
        hostname_lower = hostname.lower()
        results = {}

        for device_type, signatures in cls.DEVICE_TYPE_SIGNATURES.items():
            score = 0.0
            reasons = []

            for v in signatures.get("vendors", []):
                if v.upper() in vendor_upper or vendor_upper in v.upper():
                    score += 0.4
                    reasons.append(f"vendor_match:{v}")
                    break

            for kw in signatures.get("keywords", []):
                if kw in hostname_lower:
                    score += 0.3
                    reasons.append(f"hostname_match:{kw}")
                    break

            if open_ports:
                sig_ports = set(signatures.get("port_signatures", []))
                matched_ports = sig_ports & set(open_ports.keys())
                if matched_ports:
                    score += 0.2
                    reasons.append(f"port_match:{matched_ports}")

            if mdns_services:
                sig_mdns = set(signatures.get("mdns_services", []))
                matched_mdns = sig_mdns & set(mdns_services)
                if matched_mdns:
                    score += 0.15
                    reasons.append(f"mdns_match:{matched_mdns}")

            if score > 0:
                results[device_type] = {
                    "score": min(score, 1.0),
                    "reasons": reasons,
                }

        if not results:
            return {"device_type": "unknown", "score": 0.0, "reasons": []}

        best = max(results.items(), key=lambda x: x[1]["score"])
        return {
            "device_type": best[0],
            "score": best[1]["score"],
            "reasons": best[1]["reasons"],
        }

    @classmethod
    def get_mac_info(cls, mac: str) -> Dict[str, any]:
        analysis = cls.analyze(mac)
        return {
            "mac_address": analysis.mac_address,
            "normalized": analysis.normalized,
            "is_valid": analysis.is_valid,
            "oui": analysis.oui,
            "nic_specific": analysis.nic_specific,
            "is_multicast": analysis.is_multicast,
            "is_locally_administered": analysis.is_locally_administered,
            "is_burned_in_address": analysis.is_burned_in,
            "mac_type": analysis.mac_type,
            "broadcast": analysis.broadcast,
            "bit_summary": analysis.bit_summary,
            "global_range": analysis.global_range,
            "local_range": analysis.local_range,
        }

    @classmethod
    def is_randomized_mac(cls, mac: str, vendor: str = "") -> bool:
        analysis = cls.analyze(mac)
        if analysis.is_locally_administered:
            return True
        vendor_upper = vendor.upper() if vendor else ""
        for indicator in cls.LOCALLY_ADMINISTERED_INDICATORS:
            if indicator in vendor_upper:
                return True
        return False

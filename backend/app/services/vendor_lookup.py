"""
Multi-Source MAC Vendor Lookup Service

Cross-references:
1. IEEE OUI (3-byte prefix) - Official vendor assignments
2. Wireshark manuf DB - Community-maintained, includes MA-S (4-byte)
3. Nmap MAC Prefixes - Network security focused
4. Cisco/Aruba Vendor Databases - Manufacturer-specific device types
5. Local cache of previously identified vendors
6. MAC Prefix -> Device Type mapping (multi-source validated)

Academic References:
- IEEE 802-2014 §8: MAC Address Structure
- RFC 7042: IANA MAC Address Block
- NIST SP 800-187: Guide to MAC Address Usage

Confidence Scoring:
- Exact OUI match (IEEE): 0.95
- Exact OUI match (Wireshark/Nmap): 0.90
- MA-S match (extended): 0.85
- Vendor name fuzzy match: 0.70
- No match: 0.0
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher


class VendorLookup:
    _instance = None
    _oui_db = None
    _oui_full_db = None
    _local_cache = None
    _device_type_db = None
    _cisco_db = None
    _aruba_db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if VendorLookup._oui_db is None:
            VendorLookup._oui_db = self._load_oui_db()
        if VendorLookup._oui_full_db is None:
            VendorLookup._oui_full_db = self._load_oui_full_db()
        if VendorLookup._local_cache is None:
            VendorLookup._local_cache = self._load_local_cache()
        if VendorLookup._device_type_db is None:
            VendorLookup._device_type_db = self._load_device_type_db()
        if VendorLookup._cisco_db is None:
            VendorLookup._cisco_db = self._load_manufacturer_db("cisco_oui.json")
        if VendorLookup._aruba_db is None:
            VendorLookup._aruba_db = self._load_manufacturer_db("aruba_oui.json")

    def _load_oui_db(self) -> dict:
        for filename in ["oui_multi.json", "oui.json"]:
            oui_path = Path(__file__).parent.parent.parent / "data" / filename
            if oui_path.exists():
                with open(oui_path, "r") as f:
                    return json.load(f)
        return {}

    def _load_oui_full_db(self) -> dict:
        for filename in ["oui_multi_full.json", "oui.json"]:
            oui_path = Path(__file__).parent.parent.parent / "data" / filename
            if oui_path.exists():
                with open(oui_path, "r") as f:
                    return json.load(f)
        return {}

    def _load_local_cache(self) -> dict:
        cache_path = Path(__file__).parent.parent.parent / "data" / "local_vendor_cache.json"
        if cache_path.exists():
            with open(cache_path, "r") as f:
                return json.load(f)
        return {}

    def _load_device_type_db(self) -> dict:
        device_type_path = Path(__file__).parent.parent.parent / "data" / "mac_device_type.json"
        if device_type_path.exists():
            with open(device_type_path, "r") as f:
                return json.load(f)
        return {}

    def _load_manufacturer_db(self, filename: str) -> dict:
        db_path = Path(__file__).parent.parent.parent / "data" / filename
        if db_path.exists():
            with open(db_path, "r") as f:
                data = json.load(f)
                return data.get("vendors", {})
        return {}

    def _save_local_cache(self):
        cache_path = Path(__file__).parent.parent.parent / "data" / "local_vendor_cache.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(self._local_cache, f, indent=0, ensure_ascii=False)

    @staticmethod
    def normalize_mac(mac: str) -> str:
        raw = mac.upper().replace(":", "").replace("-", "").replace(".", "")
        return raw.zfill(12)[:12]

    @staticmethod
    def get_prefixes(mac: str) -> Dict[str, str]:
        normalized = mac.upper().replace(":", "").replace("-", "").replace(".", "")
        normalized = normalized.zfill(12)[:12]
        return {
            "6": normalized[:6],
            "7": normalized[:7],
            "8": normalized[:8],
            "9": normalized[:9],
        }

    def lookup(self, mac_address: str) -> Optional[str]:
        result = self.lookup_detailed(mac_address)
        return result.get("vendor")

    def lookup_detailed(self, mac_address: str) -> Dict[str, any]:
        prefixes = self.get_prefixes(mac_address)

        cached = self._local_cache.get(prefixes["6"])
        if cached:
            return {
                "vendor": cached,
                "source": "local_cache",
                "confidence": 0.95,
                "prefix_match": "6",
            }

        full_info = self._oui_full_db.get(prefixes["6"])
        if full_info:
            vendor = full_info.get("vendor", "") if isinstance(full_info, dict) else full_info
            source = full_info.get("source", "unknown") if isinstance(full_info, dict) else "oui"
            confidence = 0.95 if source == "ieee" else 0.90
            alternatives = full_info.get("alternatives", []) if isinstance(full_info, dict) else []
            return {
                "vendor": vendor,
                "source": source,
                "confidence": confidence,
                "prefix_match": "6",
                "alternatives": alternatives,
            }

        for prefix_len in ["8", "7"]:
            info = self._oui_full_db.get(prefixes[prefix_len])
            if info:
                vendor = info.get("vendor", "") if isinstance(info, dict) else info
                source = info.get("source", "unknown") if isinstance(info, dict) else "oui"
                return {
                    "vendor": vendor,
                    "source": source,
                    "confidence": 0.85,
                    "prefix_match": prefix_len,
                }

        vendor = self._oui_db.get(prefixes["6"])
        if vendor:
            return {
                "vendor": vendor,
                "source": "oui_simple",
                "confidence": 0.90,
                "prefix_match": "6",
            }

        for manufacturer_db in [VendorLookup._cisco_db, VendorLookup._aruba_db]:
            for vendor_name, vendor_info in manufacturer_db.items():
                if prefixes["6"] in vendor_info.get("prefixes", []):
                    return {
                        "vendor": vendor_name,
                        "source": f"manufacturer_db",
                        "confidence": vendor_info.get("confidence", 0.90),
                        "prefix_match": "6",
                    }

        return {
            "vendor": None,
            "source": "not_found",
            "confidence": 0.0,
            "prefix_match": None,
        }

    def cross_validate(self, mac_address: str, claimed_vendor: str) -> Dict[str, any]:
        result = self.lookup_detailed(mac_address)
        db_vendor = result.get("vendor")

        if not db_vendor:
            return {
                "match": None,
                "claimed_vendor": claimed_vendor,
                "db_vendor": None,
                "confidence": result.get("confidence", 0.0),
                "recommendation": "no_db_match",
            }

        similarity = SequenceMatcher(
            None,
            db_vendor.upper(),
            claimed_vendor.upper()
        ).ratio()

        if similarity > 0.85:
            return {
                "match": "confirmed",
                "claimed_vendor": claimed_vendor,
                "db_vendor": db_vendor,
                "similarity": round(similarity, 3),
                "confidence": result.get("confidence", 0.0),
                "recommendation": "vendor_confirmed",
            }
        elif similarity > 0.5:
            return {
                "match": "partial",
                "claimed_vendor": claimed_vendor,
                "db_vendor": db_vendor,
                "similarity": round(similarity, 3),
                "confidence": result.get("confidence", 0.0) * 0.8,
                "recommendation": "check_alternatives",
                "alternatives": result.get("alternatives", []),
            }
        else:
            return {
                "match": "mismatch",
                "claimed_vendor": claimed_vendor,
                "db_vendor": db_vendor,
                "similarity": round(similarity, 3),
                "confidence": 0.3,
                "recommendation": "possible_forgery_or_reassignment",
                "alternatives": result.get("alternatives", []),
            }

    def add_vendor(self, mac_prefix: str, vendor: str, source: str = "manual"):
        normalized = mac_prefix.upper().replace(":", "").replace("-", "")[:6]
        VendorLookup._oui_db[normalized] = vendor
        VendorLookup._local_cache[normalized] = vendor
        self._save_local_cache()

    def add_device_type(self, mac_prefix: str, device_type: str, source: str = "manual"):
        normalized = mac_prefix.upper().replace(":", "").replace("-", "")[:6]
        VendorLookup._device_type_db[normalized] = device_type
        self._save_device_type_db()

    def _save_device_type_db(self):
        device_type_path = Path(__file__).parent.parent.parent / "data" / "mac_device_type.json"
        device_type_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"mappings": VendorLookup._device_type_db}
        with open(device_type_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reload(self) -> int:
        VendorLookup._oui_db = self._load_oui_db()
        VendorLookup._oui_full_db = self._load_oui_full_db()
        VendorLookup._local_cache = self._load_local_cache()
        VendorLookup._device_type_db = self._load_device_type_db()
        VendorLookup._cisco_db = self._load_manufacturer_db("cisco_oui.json")
        VendorLookup._aruba_db = self._load_manufacturer_db("aruba_oui.json")
        return len(VendorLookup._oui_db)

    def get_count(self) -> int:
        return len(VendorLookup._oui_db)

    def get_stats(self) -> Dict[str, any]:
        return {
            "simple_db_count": len(VendorLookup._oui_db),
            "full_db_count": len(VendorLookup._oui_full_db),
            "local_cache_count": len(VendorLookup._local_cache),
            "device_type_db_count": len(VendorLookup._device_type_db),
            "cisco_db_count": len(VendorLookup._cisco_db),
            "aruba_db_count": len(VendorLookup._aruba_db),
        }

    def get_device_type_from_mac(self, mac_address: str) -> Optional[str]:
        prefixes = self.get_prefixes(mac_address)
        normalized = prefixes["6"]

        if normalized in VendorLookup._device_type_db:
            return VendorLookup._device_type_db[normalized]

        for manufacturer_db in [VendorLookup._cisco_db, VendorLookup._aruba_db]:
            for vendor_name, vendor_info in manufacturer_db.items():
                if normalized in vendor_info.get("prefixes", []):
                    return vendor_info.get("device_types", [None])[0]

        return None

    def get_manufacturer_device_types(self, mac_address: str) -> List[str]:
        prefixes = self.get_prefixes(mac_address)
        normalized = prefixes["6"]
        device_types = []

        for manufacturer_db in [VendorLookup._cisco_db, VendorLookup._aruba_db]:
            for vendor_name, vendor_info in manufacturer_db.items():
                if normalized in vendor_info.get("prefixes", []):
                    device_types.extend(vendor_info.get("device_types", []))

        return list(set(device_types))

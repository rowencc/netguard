#!/usr/bin/env python3
"""
Multi-Source MAC Vendor Database Updater

Combines data from:
1. IEEE OUI (Official) - https://standards-oui.ieee.org/oui/oui.txt
2. Wireshark manuf DB - https://gitlab.com/wireshark/wireshark/-/raw/master/manuf
3. Nmap MAC Prefixes - https://raw.githubusercontent.com/wireshark/wireshark/master/manuf

Academic References:
- IEEE 802-2014: Local and Metropolitan Area Networks
- IEEE OUI Registry: https://standards-oui.ieee.org/
- RFC 7042: IANA Considerations for the IANA Ethernet Address Block

Data Sources:
1. IEEE OUI: ~35,000 entries, official vendor assignments
2. Wireshark manuf: ~40,000+ entries, community-maintained, includes OUI-I and IAB
3. Nmap: ~30,000+ entries, network security focused
"""

import json
import re
import sys
import ssl
import time
from pathlib import Path
from urllib.request import urlopen, Request
from datetime import datetime
from typing import Dict, Tuple, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
OUI_FILE = DATA_DIR / "oui_multi.json"
OUI_IEEE_FILE = DATA_DIR / "oui_ieee.json"
OUI_WIRESHARK_FILE = DATA_DIR / "oui_wireshark.json"
OUI_NMAP_FILE = DATA_DIR / "oui_nmap.json"
OUI_BACKUP = DATA_DIR / "oui_multi.json.bak"
OUI_LOG = DATA_DIR / "oui_update.log"
OUI_HISTORY = DATA_DIR / "oui_update_history.json"

URLS = {
    "ieee": "https://standards-oui.ieee.org/oui/oui.txt",
    "nmap": "https://raw.githubusercontent.com/nmap/nmap/master/nmap-mac-prefixes",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def download_url(url: str, source: str) -> str:
    print(f"  [{source}] Downloading from {url}...")
    req = Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(req, timeout=60, context=ctx) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
        print(f"  [{source}] Downloaded {len(data):,} bytes")
        return data
    except Exception as e:
        print(f"  [{source}] Download failed: {e}")
        return ""


def parse_ieee_oui(text: str) -> Dict[str, dict]:
    oui_db = {}
    pattern = re.compile(
        r"^\s*([0-9A-Fa-f]{6})\s+\(base\s+16\)\s+(.+)$",
        re.MULTILINE
    )
    for match in pattern.finditer(text):
        prefix = match.group(1).upper()
        vendor = match.group(2).strip()
        if vendor and prefix not in oui_db:
            oui_db[prefix] = {
                "vendor": vendor,
                "source": "ieee",
                "type": "OUI",
            }
    return oui_db


def parse_wireshark_manuf(text: str) -> Dict[str, dict]:
    oui_db = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r'\s{2,}', line)
        if len(parts) < 2:
            continue
        prefix_raw = parts[0].strip()
        vendor = parts[1].strip()
        if not prefix_raw or not vendor:
            continue
        prefix_clean = re.sub(r'[:\-]', '', prefix_raw).upper()
        if len(prefix_clean) < 6:
            continue
        prefix_6 = prefix_clean[:6]
        if prefix_6 not in oui_db:
            oui_db[prefix_6] = {
                "vendor": vendor,
                "source": "wireshark",
                "type": "OUI",
            }
        if len(prefix_clean) >= 8:
            prefix_8 = prefix_clean[:8]
            if prefix_8 not in oui_db:
                oui_db[prefix_8] = {
                    "vendor": vendor,
                    "source": "wireshark",
                    "type": "MA-S" if len(prefix_clean) >= 8 else "OUI",
                }
    return oui_db


def parse_nmap_mac(text: str) -> Dict[str, dict]:
    oui_db = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        prefix_clean = re.sub(r'[:\-]', '', parts[0]).upper()
        vendor = parts[1].strip()
        if len(prefix_clean) < 6 or not vendor:
            continue
        prefix_6 = prefix_clean[:6]
        if prefix_6 not in oui_db:
            oui_db[prefix_6] = {
                "vendor": vendor,
                "source": "nmap",
                "type": "OUI",
            }
    return oui_db


def merge_databases(
    ieee_db: Dict[str, dict],
    nmap_db: Dict[str, dict]
) -> Dict[str, dict]:
    merged = {}
    stats = {"ieee": 0, "nmap": 0, "total": 0}

    for prefix, info in ieee_db.items():
        merged[prefix] = info
        merged[prefix]["source"] = "ieee"
        stats["ieee"] += 1

    for prefix, info in nmap_db.items():
        if prefix not in merged:
            merged[prefix] = info
            merged[prefix]["source"] = "nmap"
            stats["nmap"] += 1
        else:
            existing_vendor = merged[prefix]["vendor"].upper()
            new_vendor = info["vendor"].upper()
            if existing_vendor != new_vendor:
                merged[prefix]["alternatives"] = merged[prefix].get("alternatives", [])
                merged[prefix]["alternatives"].append(info["vendor"])

    stats["total"] = len(merged)
    return merged, stats


def create_simple_db(merged: Dict[str, dict]) -> Dict[str, str]:
    return {prefix: info["vendor"] for prefix, info in merged.items()}


def save_source_db(db: Dict[str, dict], filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(db, f, indent=0, ensure_ascii=False)


def update_all_sources() -> dict:
    print("=" * 60)
    print("Multi-Source MAC Vendor Database Updater")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {"timestamp": timestamp, "sources": {}, "merged": {}}

    ieee_raw = download_url(URLS["ieee"], "IEEE")
    nmap_raw = download_url(URLS["nmap"], "Nmap")

    ieee_db = parse_ieee_oui(ieee_raw) if ieee_raw else {}
    nmap_db = parse_nmap_mac(nmap_raw) if nmap_raw else {}

    results["sources"]["ieee"] = {"count": len(ieee_db)}
    results["sources"]["nmap"] = {"count": len(nmap_db)}

    print(f"\nSource counts:")
    print(f"  IEEE OUI:      {len(ieee_db):>8,} entries")
    print(f"  Nmap:          {len(nmap_db):>8,} entries")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    save_source_db(ieee_db, OUI_IEEE_FILE)
    save_source_db(nmap_db, OUI_NMAP_FILE)

    merged, merge_stats = merge_databases(ieee_db, nmap_db)
    results["merged"] = merge_stats

    if OUI_FILE.exists():
        OUI_FILE.rename(OUI_BACKUP)

    simple_db = create_simple_db(merged)
    with open(OUI_FILE, "w") as f:
        json.dump(simple_db, f, indent=0, ensure_ascii=False)

    with open(OUI_FILE.parent / "oui_multi_full.json", "w") as f:
        json.dump(merged, f, indent=0, ensure_ascii=False)

    print(f"\nMerged database:")
    print(f"  Total unique prefixes:  {merge_stats['total']:>8,}")
    print(f"  From IEEE:               {merge_stats['ieee']:>8,}")
    print(f"  From Nmap:               {merge_stats['nmap']:>8,}")

    log_msg = (
        f"[{timestamp}] Multi-source update: "
        f"IEEE={len(ieee_db)}, "
        f"Nmap={len(nmap_db)} -> Merged={merge_stats['total']}\n"
    )
    with open(OUI_LOG, "a") as f:
        f.write(log_msg)

    history_entry = {
        "timestamp": timestamp,
        "ieee": len(ieee_db),
        "nmap": len(nmap_db),
        "merged_total": merge_stats["total"],
    }
    history = []
    if OUI_HISTORY.exists():
        with open(OUI_HISTORY, "r") as f:
            history = json.load(f)
    history.append(history_entry)
    if len(history) > 50:
        history = history[-50:]
    with open(OUI_HISTORY, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  {OUI_FILE}")
    print(f"  {OUI_FILE.parent / 'oui_multi_full.json'}")
    print(f"  {OUI_IEEE_FILE}")
    print(f"  {OUI_NMAP_FILE}")

    print("\n" + "=" * 60)
    print("Update complete!")
    print("=" * 60)

    return results


def get_status() -> dict:
    status = {"exists": OUI_FILE.exists()}
    if not OUI_FILE.exists():
        status["count"] = 0
        return status

    with open(OUI_FILE, "r") as f:
        db = json.load(f)
    mtime = datetime.fromtimestamp(OUI_FILE.stat().st_mtime)

    status.update({
        "count": len(db),
        "last_modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size_kb": round(OUI_FILE.stat().st_size / 1024, 1),
    })

    source_stats = {}
    for source_name, source_file in [
        ("ieee", OUI_IEEE_FILE),
        ("nmap", OUI_NMAP_FILE),
    ]:
        if source_file.exists():
            with open(source_file, "r") as f:
                source_db = json.load(f)
            source_stats[source_name] = {
                "count": len(source_db),
                "last_modified": datetime.fromtimestamp(
                    source_file.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            source_stats[source_name] = {"count": 0}

    status["sources"] = source_stats

    if OUI_HISTORY.exists():
        with open(OUI_HISTORY, "r") as f:
            history = json.load(f)
        if history:
            status["last_update"] = history[-1]

    return status


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = get_status()
        print(json.dumps(status, indent=2))
    else:
        update_all_sources()

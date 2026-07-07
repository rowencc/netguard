#!/usr/bin/env python3
"""OUI database updater - fetches latest IEEE OUI data"""

import json
import re
import sys
import ssl
from pathlib import Path
from urllib.request import urlopen, Request
from datetime import datetime

OUI_URL = "https://standards-oui.ieee.org/oui/oui.txt"
DATA_DIR = Path(__file__).parent / "data"
OUI_FILE = DATA_DIR / "oui.json"
OUI_BACKUP = DATA_DIR / "oui.json.bak"
OUI_LOG = DATA_DIR / "oui_update.log"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def download_oui() -> str:
    print(f"Downloading OUI data from IEEE...")
    req = Request(OUI_URL, headers=HEADERS)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urlopen(req, timeout=30, context=ctx) as resp:
        data = resp.read().decode("utf-8", errors="ignore")
    print(f"Downloaded {len(data)} bytes")
    return data


def parse_oui(text: str) -> dict:
    oui_db = {}
    pattern = re.compile(r"^([0-9A-Fa-f]{6})\s+\(base\s+16\)\s+(.+)$", re.MULTILINE)
    for match in pattern.finditer(text):
        prefix = match.group(1).upper()
        vendor = match.group(2).strip()
        if vendor and prefix not in oui_db:
            oui_db[prefix] = vendor
    return oui_db


def update_oui():
    old_count = 0
    if OUI_FILE.exists():
        with open(OUI_FILE, "r") as f:
            old_db = json.load(f)
        old_count = len(old_db)
        OUI_FILE.rename(OUI_BACKUP)

    raw = download_oui()
    new_db = parse_oui(raw)
    new_count = len(new_db)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUI_FILE, "w") as f:
        json.dump(new_db, f, indent=0, ensure_ascii=False)

    added = new_count - old_count
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] Updated: {old_count} -> {new_count} entries (+{added})\n"
    
    with open(OUI_LOG, "a") as f:
        f.write(log_msg)

    print(f"OUI database updated: {old_count} -> {new_count} entries")
    print(f"Added {added} new entries")
    
    return {"old_count": old_count, "new_count": new_count, "added": added}


def get_status() -> dict:
    if not OUI_FILE.exists():
        return {"exists": False, "count": 0}
    with open(OUI_FILE, "r") as f:
        db = json.load(f)
    mtime = datetime.fromtimestamp(OUI_FILE.stat().st_mtime)
    return {
        "exists": True,
        "count": len(db),
        "last_modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size_kb": round(OUI_FILE.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = get_status()
        print(json.dumps(status, indent=2))
    else:
        update_oui()

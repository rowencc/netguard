from fastapi import APIRouter
from pathlib import Path
import json
import subprocess
import sys
from datetime import datetime

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
BACKEND_DIR = Path(__file__).parent.parent.parent


def _get_file_info(filepath: Path) -> dict:
    if not filepath.exists():
        return {"exists": False, "size": 0, "modified": None, "entries": 0}
    stat = filepath.stat()
    entries = 0
    if filepath.suffix == ".json":
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    entries = len(data)
                elif isinstance(data, list):
                    entries = len(data)
        except Exception:
            pass
    return {
        "exists": True,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "entries": entries,
    }


def _get_update_history() -> list:
    history_path = DATA_DIR / "oui_update_history.json"
    if history_path.exists():
        try:
            with open(history_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


@router.get("/status")
def get_libraries_status():
    history = _get_update_history()
    last_update = history[-1] if history else None

    ieee_info = _get_file_info(DATA_DIR / "oui_ieee.json")
    nmap_info = _get_file_info(DATA_DIR / "oui_nmap.json")
    multi_info = _get_file_info(DATA_DIR / "oui_multi.json")
    multi_full_info = _get_file_info(DATA_DIR / "oui_multi_full.json")

    cisco_info = _get_file_info(BACKEND_DIR / "data" / "cisco_oui.json")
    aruba_info = _get_file_info(BACKEND_DIR / "data" / "aruba_oui.json")
    device_type_info = _get_file_info(BACKEND_DIR / "data" / "mac_device_type.json")

    return {
        "libraries": [
            {
                "id": "oui_ieee",
                "name": "IEEE OUI",
                "description": "IEEE Organizationally Unique Identifier 数据库",
                "source": "https://standards-oui.ieee.org/",
                "type": "oui",
                "status": "active" if ieee_info["exists"] else "missing",
                "entries": last_update.get("ieee", ieee_info["entries"]) if last_update else ieee_info["entries"],
                "lastUpdate": ieee_info["modified"],
                "size": ieee_info["size"],
                "autoUpdate": True,
            },
            {
                "id": "oui_nmap",
                "name": "Nmap MAC Prefixes",
                "description": "Nmap 网络安全扫描工具的 MAC 前缀数据库",
                "source": "https://github.com/nmap/nmap",
                "type": "oui",
                "status": "active" if nmap_info["exists"] else "missing",
                "entries": last_update.get("nmap", nmap_info["entries"]) if last_update else nmap_info["entries"],
                "lastUpdate": nmap_info["modified"],
                "size": nmap_info["size"],
                "autoUpdate": True,
            },
            {
                "id": "oui_merged",
                "name": "合并库 (OUI Multi)",
                "description": "多源合并的 OUI 数据库，用于快速查询",
                "source": "本地合并",
                "type": "merged",
                "status": "active" if multi_info["exists"] else "missing",
                "entries": last_update.get("merged_total", multi_info["entries"]) if last_update else multi_info["entries"],
                "lastUpdate": multi_info["modified"],
                "size": multi_info["size"],
                "autoUpdate": False,
            },
            {
                "id": "oui_merged_full",
                "name": "合并库 (完整版)",
                "description": "包含详细信息的多源合并 OUI 数据库",
                "source": "本地合并",
                "type": "merged",
                "status": "active" if multi_full_info["exists"] else "missing",
                "entries": multi_full_info["entries"],
                "lastUpdate": multi_full_info["modified"],
                "size": multi_full_info["size"],
                "autoUpdate": False,
            },
            {
                "id": "cisco_oui",
                "name": "Cisco OUI",
                "description": "Cisco 设备 MAC 前缀数据库",
                "source": "Cisco",
                "type": "vendor",
                "status": "active" if cisco_info["exists"] else "missing",
                "entries": cisco_info["entries"],
                "lastUpdate": cisco_info["modified"],
                "size": cisco_info["size"],
                "autoUpdate": False,
            },
            {
                "id": "aruba_oui",
                "name": "Aruba OUI",
                "description": "Aruba 设备 MAC 前缀数据库",
                "source": "Aruba",
                "type": "vendor",
                "status": "active" if aruba_info["exists"] else "missing",
                "entries": aruba_info["entries"],
                "lastUpdate": aruba_info["modified"],
                "size": aruba_info["size"],
                "autoUpdate": False,
            },
            {
                "id": "mac_device_type",
                "name": "设备类型映射",
                "description": "MAC 前缀到设备类型的映射数据库",
                "source": "本地维护",
                "type": "mapping",
                "status": "active" if device_type_info["exists"] else "missing",
                "entries": device_type_info["entries"],
                "lastUpdate": device_type_info["modified"],
                "size": device_type_info["size"],
                "autoUpdate": False,
            },
        ],
        "lastFullUpdate": last_update.get("timestamp") if last_update else None,
        "totalEntries": last_update.get("merged_total", 0) if last_update else 0,
    }


@router.post("/update/{library_id}")
def update_library(library_id: str):
    if library_id == "oui_all":
        return _update_oui_all()
    elif library_id in ("oui_ieee", "oui_wireshark", "oui_nmap", "oui_merged", "oui_merged_full"):
        return _update_oui_all()
    else:
        return {"success": False, "error": f"Library '{library_id}' does not support online update. Only OUI databases can be updated."}


def _update_oui_all():
    script = BACKEND_DIR / "update_oui_multi.py"
    if not script.exists():
        script = BACKEND_DIR / "update_oui.py"
    if not script.exists():
        return {"success": False, "error": "Update script not found"}

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            _reload_vendor_lookup()
            return {"success": True, "message": result.stdout.strip() or "Update completed"}
        else:
            return {"success": False, "error": result.stderr or "Update failed"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Update timed out (180s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _reload_vendor_lookup():
    try:
        from app.services.vendor_lookup import VendorLookup
        VendorLookup().reload()
    except Exception:
        pass
